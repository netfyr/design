import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import path from 'node:path';
import { artifactFiles, regularFile } from '../web/scripts/build.mjs';

const { values } = parseArgs({ options: {
  port: { type: 'string', default: '4174' },
  'base-path': { type: 'string', default: '/' },
} });
const root = fileURLToPath(new URL('../dist/', import.meta.url));
const base = values['base-path'];
if (!/^\/(?:[a-zA-Z0-9_-]+\/)*$/.test(base)) throw new Error('Use a base path such as /design/');
const port = Number(values.port);
if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('Port must be between 0 and 65535');
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.gif': 'image/gif', '.pdf': 'application/pdf', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.zip': 'application/zip', '.tgz': 'application/gzip', '.csv': 'text/csv', '.txt': 'text/plain; charset=utf-8', '.md': 'text/plain; charset=utf-8' };
const allowed = new Set(artifactFiles.map(file => `components/${file}`));
const directories = new Map([
  ['', 'index.html'],
  ...artifactFiles.filter(file => file === 'index.html' || file.endsWith('/index.html'))
    .map(file => [`components/${file.slice(0, -'index.html'.length)}`, `components/${file}`]),
]);
const server = createServer(async (request, response) => {
  try {
    if (!['GET', 'HEAD'].includes(request.method)) { response.writeHead(405, { Allow: 'GET, HEAD' }); response.end(); return; }
    const requestPath = decodeURIComponent(request.url.split(/[?#]/)[0]);
    if (requestPath.split('/').includes('..') || requestPath.includes('\\') || requestPath.includes('\0')) {
      throw new URIError('Invalid path');
    }
    const url = new URL(request.url, 'http://localhost');
    if (!url.pathname.startsWith(base)) { response.writeHead(404); response.end(); return; }
    let relative = decodeURIComponent(url.pathname.slice(base.length));
    if (relative.startsWith('/') || relative.split('/').some(part => part === '..')
      || relative.includes('\\') || relative.includes('\0')) throw new URIError('Invalid path');
    if (relative && !relative.endsWith('/') && directories.has(`${relative}/`)) {
      response.writeHead(308, { Location: `${url.pathname}/${url.search}` }); response.end(); return;
    }
    relative = directories.get(relative) || relative;
    if (relative.startsWith('components/') && !allowed.has(relative)) {
      response.writeHead(404); response.end(); return;
    }
    const file = await regularFile(root, relative);
    const info = await stat(file);
    if (!info.isFile()) { response.writeHead(404); response.end(); return; }
    response.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream', 'Content-Length': info.size, 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' });
    response.end(request.method === 'HEAD' ? undefined : await readFile(file));
  } catch (error) {
    response.writeHead(error instanceof URIError ? 400 : ['ENOENT', 'ENOTDIR', 'ERR_ASSERTION'].includes(error.code) ? 404 : 500); response.end();
  }
});
server.listen(port, '127.0.0.1', () => console.log(`Preview: http://127.0.0.1:${server.address().port}${base}`));
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => { server.closeAllConnections(); server.close(() => process.exit(0)); });
