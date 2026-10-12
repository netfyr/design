import { createServer } from 'node:http';
import { watch } from 'node:fs';
import { readFile, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.pdf': 'application/pdf', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.zip': 'application/zip', '.csv': 'text/csv' };
const clients = new Set();
let reloadTimer;
for (const directory of ['src', 'public']) {
  watch(path.join(root, directory), { recursive: true }, () => {
    clearTimeout(reloadTimer);
    reloadTimer = setTimeout(() => {
      for (const client of clients) client.write('data: reload\n\n');
    }, 200);
  });
}
const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url, 'http://localhost');
    if (url.pathname === '/__reload') {
      response.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive' });
      response.write(': connected\n\n');
      clients.add(response);
      request.on('close', () => clients.delete(response));
      return;
    }
    const relative = decodeURIComponent(url.pathname).replace(/^\/+/, '') || 'index.html';
    if (relative.split('/').some(part => part === '..')) throw new Error('Invalid path');
    let file;
    for (const directory of ['src', 'public']) {
      const candidate = path.join(root, directory, relative);
      try {
        if ((await stat(candidate)).isFile()) { file = candidate; break; }
      } catch {}
    }
    if (!file) { response.writeHead(404); response.end('Not found'); return; }
    response.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    const content = await readFile(file);
    response.end(path.extname(file) === '.html'
      ? content.toString().replace('</body>', '<script>new EventSource("/__reload").onmessage = () => location.reload();</script></body>')
      : content);
  } catch {
    response.writeHead(400); response.end('Bad request');
  }
});
server.listen(Number(process.env.PORT || 4173), '127.0.0.1', () => {
  console.log(`Local: http://localhost:${server.address().port}`);
});
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => {
  for (const client of clients) client.end();
  server.close(() => process.exit(0));
});
