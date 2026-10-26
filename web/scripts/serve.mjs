import { createServer } from 'node:http';
import { watch } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { parseArgs } from 'node:util';
import path from 'node:path';
import { artifactFiles, build, output, regularFile, root, sourcePath, sources, assets } from './build.mjs';

const { values } = parseArgs({ options: {
  production: { type: 'boolean', default: false },
  port: { type: 'string', default: '4175' },
  'base-path': { type: 'string', default: '/' },
} });
const port = Number(values.port);
if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('Port must be between 0 and 65535');
const base = values['base-path'];
if (!/^\/(?:[a-zA-Z0-9_-]+\/)*$/.test(base)) throw new Error('Use a base path such as /components/');
if (values.production) await regularFile(output, 'index.html');
else await build();

const types = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.json': 'application/json; charset=utf-8',
  '.gif': 'image/gif',
  '.woff2': 'font/woff2', '.txt': 'text/plain; charset=utf-8', '.md': 'text/plain; charset=utf-8', '.tgz': 'application/gzip',
};
const allowed = new Set(artifactFiles);
const directories = new Map(artifactFiles.filter(file => file === 'index.html' || file.endsWith('/index.html'))
  .map(file => [file.slice(0, -'index.html'.length), file]));
const editable = new Set([...sources, ...assets.keys()]);
const clients = new Set();
let reloadTimer;
const watchedFiles = values.production ? [] : await Promise.all([...editable].map(sourcePath));
const watchedPaths = new Set(watchedFiles);
const watchers = [...new Set(watchedFiles.map(file => path.dirname(file)))].map(directory =>
  watch(directory, (_event, file) => {
    if (!file || !watchedPaths.has(path.join(directory, file))) return;
    clearTimeout(reloadTimer);
    reloadTimer = setTimeout(() => {
      for (const client of clients) client.write('data: reload\n\n');
    }, 150);
  }));
const server = createServer(async (request, response) => {
  try {
    if (!['GET', 'HEAD'].includes(request.method)) {
      response.writeHead(405, { Allow: 'GET, HEAD' }); response.end(); return;
    }
    const url = new URL(request.url, 'http://localhost');
    if (!url.pathname.startsWith(base)) { response.writeHead(404); response.end(); return; }
    let relative = decodeURIComponent(url.pathname.slice(base.length));
    if (relative && !relative.endsWith('/') && directories.has(`${relative}/`)) {
      response.writeHead(308, { Location: `${url.pathname}/${url.search}` }); response.end(); return;
    }
    relative = directories.get(relative) || relative;
    if (!values.production && relative === '__reload' && request.method === 'GET') {
      response.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store' });
      response.write(': connected\n\n');
      clients.add(response);
      response.on('close', () => clients.delete(response));
      return;
    }
    if (!allowed.has(relative)) { response.writeHead(404); response.end(); return; }
    const file = !values.production && editable.has(relative)
      ? await sourcePath(relative) : await regularFile(output, relative);
    let content = await readFile(file);
    if (!values.production && relative.endsWith('.html')) {
      const reload = `<script>new EventSource(${JSON.stringify(`${base}__reload`)}).onmessage = () => location.reload();</script>`;
      content = Buffer.from(content.toString().replace('</body>', `${reload}</body>`));
    }
    response.writeHead(200, {
      'Content-Type': types[path.extname(relative)] || 'text/plain; charset=utf-8',
      'Content-Length': content.length, 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
    });
    response.end(request.method === 'HEAD' ? undefined : content);
  } catch (error) {
    response.writeHead(error.code === 'ENOENT' ? 404 : error instanceof URIError ? 400 : 500);
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
server.listen(port, '127.0.0.1', () => console.log(`Preview: http://127.0.0.1:${server.address().port}${base}`));
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, close);
