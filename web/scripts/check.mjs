import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { artifactFiles, assets, build, output, packageFiles, regularFile, root, sourcePath, sources } from './build.mjs';
import { checkSymbols } from '../../scripts/check-symbols.mjs';

await checkSymbols(new URL('../../', import.meta.url));

for (const file of [...sources.filter(file => file.endsWith('.js')), 'scripts/build.mjs', 'scripts/serve.mjs', 'scripts/check.mjs', 'scripts/check-browser.mjs']) {
  execFileSync(process.execPath, ['--check', await regularFile(root, file)], { stdio: 'pipe' });
}
const manifest = JSON.parse(await readFile(path.join(root, 'package.json'), 'utf8'));
assert.equal(manifest.type, 'module');
assert.equal(manifest.license, 'MIT');
assert.deepEqual(manifest.exports, {
  '.': './src/components.js', './styles.css': './src/components.css',
  './theme.js': './src/theme.js', './theme.css': './src/theme.css',
});
assert.equal(Object.keys(manifest.dependencies || {}).length, 0);
for (const file of packageFiles) await regularFile(root, file);
const { enhance } = await import('../src/components.js');
assert.equal(typeof enhance, 'function', 'The module must export enhance without accessing a browser on import');
const { mountTheme } = await import('../src/theme.js');
assert.equal(typeof mountTheme, 'function', 'The theme module must import without accessing a browser');
const previewSource = await readFile(path.join(root, 'tui/previews.json'), 'utf8');
assert.ok(Buffer.byteLength(previewSource) < 1024 * 1024, 'TUI preview export unexpectedly exceeds 1 MiB');
const previews = JSON.parse(previewSource);
assert.equal(previews.version, 1);
assert.deepEqual(previews.previews.map(preview => preview.id).sort(),
  ['activity', 'flame', 'footer', 'glyphs', 'replay', 'settings', 'traffic']);
for (const style of previews.styles) {
  assert.match(style.fg, /^#[0-9a-f]{6}$/i);
  assert.match(style.bg, /^#[0-9a-f]{6}$/i);
  assert.equal(typeof style.bold, 'boolean');
  assert.equal(typeof style.underline, 'boolean');
}
for (const preview of previews.previews) {
  assert.ok(Number.isInteger(preview.columns) && preview.columns > 0 && preview.columns <= 100);
  assert.ok(Number.isInteger(preview.rows) && preview.rows > 0 && preview.rows <= 32);
  assert.ok(Number.isFinite(preview.intervalMs) && preview.intervalMs >= 50 && preview.intervalMs <= 1000);
  if (preview.id === 'glyphs') assert.ok(Array.isArray(preview.fallback), 'Glyphs need a standard-character fallback frame');
  else assert.equal(preview.fallback, undefined, 'Unexpected fallback frame: ' + preview.id);
  for (const frame of [preview.still, ...preview.frames, ...(preview.fallback ? [preview.fallback] : [])]) {
    assert.ok(frame.length > 0);
    for (const [x, y, style, text, width] of frame) {
      assert.ok([x, y, style, width].every(Number.isInteger));
      assert.ok(x >= 0 && y >= 0 && y < preview.rows && width > 0 && x + width <= preview.columns);
      assert.ok(style >= 0 && style < previews.styles.length);
      assert.equal(typeof text, 'string');
      assert.ok(!/[\u0000-\u001f\u007f]/.test(text), 'Control character in terminal preview');
    }
  }
  assert.equal(preview.frames.length > 0, !['footer', 'glyphs', 'settings'].includes(preview.id));
  if (preview.frames.length) {
    assert.ok(new Set(preview.frames.map(frame => JSON.stringify(frame))).size > 1,
      `Animation never changes: ${preview.id}`);
  }
}
await build();

async function filesAt(directory, prefix = '') {
  const found = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    assert.ok(!entry.isSymbolicLink(), `Symlink in gallery output: ${entry.name}`);
    const relative = `${prefix}${entry.name}`;
    if (entry.isDirectory()) found.push(...await filesAt(path.join(directory, entry.name), `${relative}/`));
    else found.push(relative);
  }
  return found;
}
assert.deepEqual((await filesAt(output)).sort(), [...artifactFiles].sort(), 'Unexpected gallery artifact files');
for (const file of [...sources, ...assets.keys()]) {
  assert.deepEqual(await readFile(path.join(output, file)), await readFile(await sourcePath(file)), `Changed asset: ${file}`);
}
const allowed = new Set(artifactFiles);
const base = new URL('https://gallery.invalid/components/');
const designPages = new Set(['overview', 'typography', 'colors', 'spacing', 'brand', 'resources']);
for (const file of sources.filter(file => file.endsWith('.html'))) {
  const html = await readFile(path.join(output, file), 'utf8');
  const ids = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]));
  assert.ok(html.includes('lang="en"') && html.includes('name="viewport"'), `Missing page metadata: ${file}`);
  assert.ok(!html.includes('__reload'), `Development reload code reached the production gallery: ${file}`);
  for (const [, tag, attributes] of html.matchAll(/<([a-z][\w-]*)\b([^>]*)>/gi)) {
    const designPage = attributes.match(/data-design-page="([^"]+)"/)?.[1];
    if (designPage) {
      assert.equal(tag, 'a', 'Only navigation links may target the parent design pages');
      assert.ok(designPages.has(designPage), `Unknown design page: ${designPage}`);
      assert.ok(attributes.includes('href="'), `Missing design page link: ${designPage}`);
    }
    for (const [, attribute, value] of attributes.matchAll(/\b(href|src)="([^"]+)"/g)) {
      if (designPage) {
        assert.equal(attribute, 'href', 'Design page navigation cannot contain asset references');
        const home = file === 'index.html' ? '../' : '../../';
        assert.equal(value, `${home}#${designPage}`, `Incorrect design page link: ${file}`);
        continue;
      }
      if (value.startsWith('#')) {
        if (tag === 'use') assert.ok(ids.has(value.slice(1)), `Missing SVG symbol: ${file}: ${value}`);
        continue;
      }
      if (/^(?:https?:|mailto:|data:)/.test(value)) continue;
      assert.ok(!value.startsWith('/'), `Gallery link must be relative: ${file}: ${value}`);
      const link = new URL(value, new URL(file, base));
      assert.ok(link.origin === base.origin && link.pathname.startsWith(base.pathname),
        `Gallery link escapes its base path: ${file}: ${value}`);
      let target = decodeURIComponent(link.pathname.slice(base.pathname.length));
      if (!target || target.endsWith('/')) target += 'index.html';
      else if (allowed.has(`${target}/index.html`)) target += '/index.html';
      assert.ok(allowed.has(target), `Gallery link is missing: ${file}: ${value}`);
    }
  }
}
for (const file of ['gallery.css', 'src/components.css', 'src/theme.css']) {
  const css = await readFile(path.join(output, file), 'utf8');
  for (const [, value] of css.matchAll(/url\(\s*["']?([^\s"')]+)["']?\s*\)/g)) {
    if (value.startsWith('data:')) continue;
    assert.ok(!value.startsWith('/') && !/^https?:/.test(value), `CSS asset must be local and relative: ${value}`);
    const target = path.posix.normalize(path.posix.join(path.posix.dirname(file), value.split(/[?#]/)[0]));
    assert.ok(allowed.has(target), `Missing CSS asset: ${target}`);
  }
}
console.log('Checked web component exports, package contents, local assets and both catalogue pages.');
