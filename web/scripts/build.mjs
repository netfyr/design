import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { copyFile, lstat, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const root = fileURLToPath(new URL('../', import.meta.url));
export const output = path.join(root, 'dist');
export const archive = 'netfyr-web-components-0.1.0.tgz';
export const vendorFiles = [
  'src/vendor/highlightjs/core.min.js',
  ...['xml', 'css', 'javascript', 'typescript', 'json', 'bash', 'rust']
    .map(language => `src/vendor/highlightjs/languages/${language}.min.js`),
  'src/vendor/highlightjs/LICENSE', 'src/vendor/highlightjs/README.md',
];
export const sources = [
  'index.html', 'gallery.css', 'gallery.js', 'gallery-shell.js',
  'tui/index.html', 'tui/gallery.js', 'tui/previews.js', 'tui/previews.json', 'tui/recordings.js',
  ...['choice', 'interfaces', 'empty', 'loading', 'failed']
    .map(state => `tui/screenshots/dropdown-${state}.png`),
  ...['dropdown-choice', 'dropdown-interfaces', 'dropdown-empty', 'dropdown-loading', 'dropdown-failed', 'settings']
    .map(id => `tui/screenshots/${id}.gif`),
  'tui/screenshots/settings.png',
  'src/components.css', 'src/components.js', 'src/code.js', 'src/theme.js', 'src/theme.css',
  'README.md', 'LICENSE', ...vendorFiles,
];
export const packageFiles = [
  'package.json', 'README.md', 'LICENSE',
  'src/components.css', 'src/components.js', 'src/code.js', 'src/theme.js', 'src/theme.css', ...vendorFiles,
];
export const fonts = [
  'netfyrsans-Regular.woff2', 'netfyrsans-SemiBold.woff2',
  'netfyrmono-Regular.woff2', 'netfyrmono-SemiBold.woff2', 'OFL.txt',
];
export const assets = new Map([
  ...fonts.map(file => [`assets/fonts/${file}`, `fonts/${file}`]),
  ['assets/fonts/netfyrsymbols-Regular.woff2', 'fonts/symbols/netfyrsymbols-Regular.woff2'],
  ['assets/fonts/symbols-NOTICE.txt', 'fonts/symbols/NOTICE.txt'],
  ['downloads/netfyr-symbols.zip', 'fonts/symbols/netfyr-symbols.zip'],
  ['assets/netfyr-mark-orange.svg', 'assets/netfyr-mark-orange.svg'],
]);
export const artifactFiles = [
  ...sources, ...assets.keys(), 'LICENSES.md', `downloads/${archive}`,
];
const publicRoot = path.resolve(root, '../public');

export async function regularFile(directory, relative) {
  assert.ok(relative && !path.isAbsolute(relative) && !relative.split(/[\\/]/).includes('..'));
  const base = await lstat(directory);
  assert.ok(base.isDirectory() && !base.isSymbolicLink(), `Invalid asset directory: ${directory}`);
  let current = directory;
  const parts = relative.split('/');
  for (const [index, part] of parts.entries()) {
    current = path.join(current, part);
    const info = await lstat(current);
    assert.ok(!info.isSymbolicLink(), `Symlink is not a published asset: ${relative}`);
    assert.ok(index === parts.length - 1 ? info.isFile() : info.isDirectory(), `Invalid asset: ${relative}`);
  }
  return current;
}

export async function sourcePath(relative) {
  return assets.has(relative)
    ? regularFile(publicRoot, assets.get(relative))
    : regularFile(root, relative);
}

export async function build() {
  const manifest = JSON.parse(await readFile(path.join(root, 'package.json'), 'utf8'));
  assert.equal(manifest.name, '@netfyr/web-components');
  assert.equal(manifest.version, '0.1.0');
  for (const file of new Set([...sources, ...packageFiles])) await regularFile(root, file);
  for (const file of assets.keys()) await sourcePath(file);
  const previous = await lstat(output).catch(error => {
    if (error.code !== 'ENOENT') throw error;
  });
  assert.ok(!previous?.isSymbolicLink(), 'Refusing to replace a linked output directory');
  await rm(output, { recursive: true, force: true });
  for (const file of [...sources, ...assets.keys()]) {
    const destination = path.join(output, file);
    await mkdir(path.dirname(destination), { recursive: true });
    await copyFile(await sourcePath(file), destination);
  }
  await writeFile(path.join(output, 'LICENSES.md'),
    'Web component and gallery code: MIT; see LICENSE.\n' +
    'Vendored Highlight.js: BSD-3-Clause; see src/vendor/highlightjs/LICENSE.\n' +
    'netfyr Sans, Mono and Symbols fonts, including all glyphs: SIL OFL 1.1; see assets/fonts/OFL.txt and assets/fonts/symbols-NOTICE.txt.\n' +
    'Standalone netfyr flame, logo and wordmark artwork is all rights reserved. Font and code licenses do not grant trademark permission to use the marks as another project\'s identity.\n');
  const downloads = path.join(output, 'downloads');
  await mkdir(downloads, { recursive: true });
  const [packed] = JSON.parse(execFileSync('npm', [
    'pack', '--ignore-scripts', '--json', '--pack-destination', downloads,
  ], { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 30000 }));
  assert.equal(packed.filename, archive);
  assert.deepEqual(packed.files.map(file => file.path).sort(), [...packageFiles].sort(),
    'The package must contain only its public implementation, README and license');
  console.log('Built web and TUI component galleries in web/dist/');
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) await build();
