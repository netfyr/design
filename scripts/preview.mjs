import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import path from 'node:path';

const { values } = parseArgs({ options: {
  port: { type: 'string', default: '4174' },
  'base-path': { type: 'string', default: '/' },
} });
const root = fileURLToPath(new URL('../dist/', import.meta.url));
const base = values['base-path'];
if (!/^\/(?:[a-zA-Z0-9_-]+\/)*$/.test(base)) throw new Error('Use a base path such as /design/');
const port = Number(values.port);
if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('Port must be between 0 and 65535');
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.pdf': 'application/pdf', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.zip': 'application/zip', '.csv': 'text/csv', '.txt': 'text/plain; charset=utf-8' };
const server = createServer(async (request, response) => {
  try {
    if (!['GET', 'HEAD'].includes(request.method)) { response.writeHead(405, { Allow: 'GET, HEAD' }); response.end(); return; }
    const url = new URL(request.url, 'http://localhost');
    if (!url.pathname.startsWith(base)) { response.writeHead(404); response.end(); return; }
    const relative = decodeURIComponent(url.pathname.slice(base.length)) || 'index.html';
    if (relative.split('/').some(part => part === '..') || relative.includes('\\')) throw new Error('Invalid path');
    const file = path.resolve(root, relative);
    if (!file.startsWith(root)) { response.writeHead(404); response.end(); return; }
    const info = await stat(file);
    if (!info.isFile()) { response.writeHead(404); response.end(); return; }
    response.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream', 'Content-Length': info.size, 'Cache-Control': 'no-store' });
    response.end(request.method === 'HEAD' ? undefined : await readFile(file));
  } catch (error) {
    response.writeHead(error.code === 'ENOENT' ? 404 : 400); response.end();
  }
});
server.listen(port, '127.0.0.1', () => console.log(`Preview: http://127.0.0.1:${server.address().port}${base}`));
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => { server.closeAllConnections(); server.close(() => process.exit(0)); });
