import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { fontFaceMetadata } from './check-font-license.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');

export async function checkSymbols(root) {
  const directory = new URL('public/fonts/symbols/', root);
  const manifest = JSON.parse(await readFile(new URL('symbols-manifest.json', directory), 'utf8'));
  assert.equal(manifest.schema, 'netfyr-symbols/v1');
  assert.equal(manifest.family, 'netfyr symbols');
  assert.equal(manifest.version, '1.000');
  assert.equal(manifest.license, 'OFL-1.1');
  assert.deepEqual(manifest.source, {
    file: 'netfyrmono-Regular.ttf', version: '0.507',
    sha256: sha(await readFile(new URL('public/fonts/netfyrmono-Regular.ttf', root))),
  });
  assert.equal(manifest.generator_sha256, sha(await readFile(new URL('font-sources/symbols/build.py', root))));
  assert.deepEqual(manifest.glyphs.map(({ codepoint, source_codepoint, advance }) => [codepoint, source_codepoint, advance]), [
    ['U+100000', 'U+E000', 640], ['U+100001', 'U+E0B0', 640],
    ['U+100002', 'U+E0B1', 640], ['U+100003', 'U+E0B2', 640], ['U+100004', 'U+E0B3', 640],
  ]);
  assert.deepEqual(Object.keys(manifest.files).sort(), [
    'NOTICE.txt', 'OFL.txt', 'README.txt', 'netfyr-symbols.zip',
    'netfyrsymbols-Regular.ttf', 'netfyrsymbols-Regular.woff2',
  ].sort());
  for (const [name, expected] of Object.entries(manifest.files)) {
    const bytes = await readFile(new URL(name, directory));
    assert.equal(bytes.length, expected.bytes, `Symbols asset length mismatch: ${name}`);
    assert.equal(sha(bytes), expected.sha256, `Symbols asset hash mismatch: ${name}`);
  }
  assert.deepEqual(await readFile(new URL('OFL.txt', directory)), await readFile(new URL('OFL.txt', root)));
  assert.deepEqual(fontFaceMetadata(await readFile(new URL('netfyrsymbols-Regular.ttf', directory))), {
    family: 'netfyr symbols', style: 'Regular', weight: 400,
    italic: false, variable: false, version: 1,
  });
}
