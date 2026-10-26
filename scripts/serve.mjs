import { createServer } from 'node:http';
import { watch } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import path from 'node:path';
import { artifactFiles, assets, build, output, regularFile, sourcePath, sources } from '../web/scripts/build.mjs';

const { values } = parseArgs({ options: {
  port: { type: 'string', default: process.env.PORT || '4173' },
} });
const port = Number(values.port);
if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('Port must be between 0 and 65535');
const root = fileURLToPath(new URL('../', import.meta.url));
const types = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.json': 'application/json',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.gif': 'image/gif',
  '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.zip': 'application/zip',
  '.tgz': 'application/gzip', '.csv': 'text/csv', '.pdf': 'application/pdf',
  '.txt': 'text/plain; charset=utf-8', '.md': 'text/plain; charset=utf-8',
};
const allowed = new Set(artifactFiles.map(file => `components/${file}`));
const directories = new Map([
  ['', 'index.html'],
  ...artifactFiles.filter(file => file === 'index.html' || file.endsWith('/index.html'))
    .map(file => [`components/${file.slice(0, -'index.html'.length)}`, `components/${file}`]),
]);
const editable = new Set([...sources, ...assets.keys()]);
await build();
const clients = new Set();
let reloadTimer;
function reload() {
  clearTimeout(reloadTimer);
  reloadTimer = setTimeout(() => {
    for (const client of clients) client.write('data: reload\n\n');
  }, 200);
}
const watchers = ['src', 'public'].map(directory => watch(path.join(root, directory), { recursive: true }, reload));
const watchedFiles = new Set(await Promise.all(sources.map(sourcePath)));
for (const directory of new Set([...watchedFiles].map(file => path.dirname(file)))) {
  watchers.push(watch(directory, (_event, file) => {
    if (file && watchedFiles.has(path.join(directory, file))) reload();
  }));
}
const server = createServer(async (request, response) => {
  try {
    if (!['GET', 'HEAD'].includes(request.method)) {
      response.writeHead(405, { Allow: 'GET, HEAD' }); response.end(); return;
    }
    const requestPath = decodeURIComponent(request.url.split(/[?#]/)[0]);
    if (requestPath.split('/').includes('..') || requestPath.includes('\\') || requestPath.includes('\0')) {
      throw new URIError('Invalid path');
    }
    const url = new URL(request.url, 'http://localhost');
    let relative = decodeURIComponent(url.pathname.slice(1));
    if (relative.startsWith('/') || relative.split('/').some(part => part === '..')
      || relative.includes('\\') || relative.includes('\0')) throw new URIError('Invalid path');
    if (relative === '__reload' && request.method === 'GET') {
      response.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive' });
      response.write(': connected\n\n');
      clients.add(response);
      response.on('close', () => clients.delete(response));
      return;
    }
    if (relative && !relative.endsWith('/') && directories.has(`${relative}/`)) {
      response.writeHead(308, { Location: `${url.pathname}/${url.search}` }); response.end(); return;
    }
    relative = directories.get(relative) || relative;
    let file;
    if (relative.startsWith('components/')) {
      if (!allowed.has(relative)) { response.writeHead(404); response.end('Not found'); return; }
      const component = relative.slice('components/'.length);
      file = editable.has(component) ? await sourcePath(component) : await regularFile(output, component);
    } else {
      for (const directory of ['src', 'public']) {
        try { file = await regularFile(path.join(root, directory), relative); break; }
        catch (error) { if (!['ENOENT', 'ENOTDIR', 'ERR_ASSERTION'].includes(error.code)) throw error; }
      }
    }
    if (!file) { response.writeHead(404); response.end('Not found'); return; }
    let content = await readFile(file);
    if (path.extname(file) === '.html') {
      content = Buffer.from(content.toString().replace('</body>', '<script>new EventSource("/__reload").onmessage = () => location.reload();</script></body>'));
    }
    response.writeHead(200, {
      'Content-Type': types[path.extname(file)] || 'application/octet-stream',
      'Content-Length': content.length, 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
    });
    response.end(request.method === 'HEAD' ? undefined : content);
  } catch (error) {
    response.writeHead(error instanceof URIError ? 400 : ['ENOENT', 'ENOTDIR', 'ERR_ASSERTION'].includes(error.code) ? 404 : 500);
    response.end();
  }
});
function close() {
  clearTimeout(reloadTimer);
  for (const watcher of watchers) watcher.close();
  for (const client of clients) client.end();
  server.closeAllConnections();
  server.close();
}
server.on('error', error => { console.error(error.message); process.exitCode = 1; close(); });
for (const watcher of watchers) watcher.on('error', error => { console.error(error.message); process.exitCode = 1; close(); });
server.listen(port, '127.0.0.1', () => console.log(`Local: http://localhost:${server.address().port}`));
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, close);
