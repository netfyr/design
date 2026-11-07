import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

function dimensions(bytes) {
  assert.equal(bytes.readUInt16BE(0), 0xffd8, 'Expected JPEG');
  let offset = 2;
  while (offset + 9 < bytes.length) {
    assert.equal(bytes[offset], 0xff, 'Invalid JPEG marker');
    const marker = bytes[offset + 1];
    if ([0xc0, 0xc2].includes(marker)) return [bytes.readUInt16BE(offset + 7), bytes.readUInt16BE(offset + 5)];
    const length = bytes.readUInt16BE(offset + 2);
    assert.ok(length >= 2, 'Invalid JPEG segment');
    offset += length + 2;
  }
  throw new Error('JPEG dimensions not found');
}

export async function checkBackgrounds(root) {
  const base = new URL('public/assets/backgrounds/', root);
  const catalog = JSON.parse(await readFile(new URL('catalog.json', base), 'utf8'));
  const index = await readFile(new URL('downloads.html', base), 'utf8');
  assert.equal(catalog.version, 1);
  assert.equal(catalog.defaultFormat, 'desktop-fhd');
  assert.deepEqual(catalog.formats.map(format => [format.id, format.width, format.height]), [
    ['desktop-fhd', 1920, 1080], ['desktop-qhd', 2560, 1440], ['desktop-4k', 3840, 2160],
    ['mobile-fhd', 1080, 1920], ['mobile-qhd', 1440, 2560], ['social-header', 1500, 500], ['link-preview', 1200, 630],
  ]);
  assert.equal(catalog.artworks.length, 8);
  assert.equal(new Set(catalog.artworks.map(artwork => artwork.id)).size, 8);
  const checked = new Map();
  async function image(file, width, height) {
    assert.match(file, /^(downloads|previews)\/[a-z0-9-]+\.jpg$/);
    if (!checked.has(file)) checked.set(file, await readFile(new URL(file, base)));
    const bytes = checked.get(file);
    assert.deepEqual(dimensions(bytes), [width, height], `Wrong dimensions: ${file}`);
    return bytes.length;
  }
  for (const artwork of catalog.artworks) {
    assert.ok(artwork.title && artwork.alt);
    assert.deepEqual(Object.keys(artwork.variants), catalog.formats.map(format => format.id));
    for (const format of catalog.formats) {
      assert.ok(format.note && format.label && format.group && format.layout);
      const variant = artwork.variants[format.id];
      assert.equal(await image(variant.file, format.width, format.height), variant.bytes, `Wrong file size: ${variant.file}`);
      if (format.id === 'social-header') assert.ok(variant.bytes <= 1000000, 'Header exceeds 1 MB');
      const preview = variant.preview;
      assert.equal(preview.width * format.height, preview.height * format.width, 'Preview aspect ratio differs from download');
      assert.ok(await image(preview.file, preview.width, preview.height) < 150000, `Preview too large: ${preview.file}`);
      assert.ok(index.includes(`href="${variant.file}" download`), 'Static index missing download');
    }
  }
}
