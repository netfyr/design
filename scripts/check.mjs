import { access, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { checkFontLicense, fontFaceMetadata } from './check-font-license.mjs';

const root = new URL('../', import.meta.url);
if (await access(new URL('.git', root)).then(() => true, () => false)) {
  const tracked = execFileSync('git', ['ls-files', '-z'], { cwd: root, encoding: 'utf8' }).split('\0');
  const pdfs = tracked.filter(file => /\.pdf$/i.test(file));
  if (pdfs.length) throw new Error(`PDFs must not be published in this repository: ${pdfs.join(', ')}`);
}
const manifest = JSON.parse(await readFile(new URL('public/fonts/font-manifest.json', root), 'utf8'));
if (manifest.style_count !== 28 || manifest.styles.length !== 28 || !['0.506', '0.507'].includes(manifest.version)) throw new Error('Incorrect font release declaration');
const canonical = JSON.parse(await readFile(new URL(`font-sources/${manifest.version}/styles.json`, root), 'utf8'));
const canonicalStyles = new Map(canonical.styles.map(style => [style.ttf, style]));
if (canonical.version !== manifest.version || canonical.style_count !== 28 || canonical.styles.length !== 28 || canonicalStyles.size !== 28) {
  throw new Error('Incomplete canonical style manifest');
}
const required = [
  'src/index.html', 'src/app.js', 'src/flame.js', 'src/flame-shape.js', 'src/flame-blur.js', 'src/styles.css',
  'public/vendor/svg.js', 'public/vendor/svg-filter.js',
  'public/assets/netfyr-mark-orange.svg', 'public/fonts/netfyr.css',
  'public/assets/netfyr-logo-ink.svg', 'public/assets/netfyr-logo-paper.svg',
  'public/assets/netfyr-logo-ink.png', 'public/assets/netfyr-logo-paper.png',
  'public/fonts/font-manifest.json', 'public/fonts/verification.json',
  `public/fonts/netfyr-fonts-${manifest.version}.zip`, 'public/assets/glyphs.json',
];
for (const file of required) await access(new URL(file, root));
const html = await readFile(new URL('src/index.html', root), 'utf8');
if (!html.includes('lang="en"') || !html.includes('name="viewport"')) throw new Error('Missing document accessibility metadata');
const references = [...html.matchAll(/(?:href|src)="([^"#][^"]*)"/g)].map(match => match[1]);
for (const reference of new Set(references)) {
  if (/^(?:https?:|data:)/.test(reference)) continue;
  const asset = reference.split(/[?#]/)[0];
  const available = await Promise.allSettled(['src/', 'public/'].map(directory => access(new URL(directory + asset, root))));
  if (available.every(result => result.status === 'rejected')) throw new Error(`Missing linked asset: ${reference}`);
}
const verification = JSON.parse(await readFile(new URL('public/fonts/verification.json', root), 'utf8'));
if (verification.version !== manifest.version) throw new Error('Verification covers a different revision');
const release = JSON.parse(await readFile(new URL('font-sources/0.507/RELEASE.json', root), 'utf8'));
if (release.font_download?.file !== `netfyr-fonts-${manifest.version}.zip`) throw new Error('Missing font download verification');
const archive = await readFile(new URL(`public/fonts/${release.font_download.file}`, root));
if (archive.length !== release.font_download.bytes || createHash('sha256').update(archive).digest('hex') !== release.font_download.sha256) {
  throw new Error('Font download archive differs from the published release');
}
const css = await readFile(new URL('public/fonts/netfyr.css', root), 'utf8');
const faces = [...css.matchAll(/@font-face\s*\{([^}]+)\}/g)].map(match => {
  const declarations = Object.fromEntries([...match[1].matchAll(/([\w-]+)\s*:\s*([^;]+);/g)]
    .map(([, name, value]) => [name, value.trim()]));
  const source = declarations.src?.match(/^url\((["'])(.*?)\1\)\s+format\((["'])woff2\3\)$/);
  if (!source) throw new Error('Expected a local WOFF2 font face');
  return { ...declarations, source: source[2] };
});
const cssFaces = new Map(faces.map(face => [face.source, face]));
if (faces.length !== 28 || cssFaces.size !== 28) throw new Error('Expected 28 distinct CSS font faces');
const logos = JSON.parse(await readFile(new URL('public/assets/netfyr-logo-assets.json', root), 'utf8'));
if (logos.font_sha256 !== verification.ttf_sha256[logos.font]) throw new Error('Logo source font differs from the published release');
for (const [name, expected] of Object.entries(logos.files)) {
  const bytes = await readFile(new URL(`public/assets/${name}`, root));
  if (createHash('sha256').update(bytes).digest('hex') !== expected) throw new Error(`Logo asset hash mismatch: ${name}`);
}
const exports = JSON.parse(await readFile(new URL('public/fonts/export-report.json', root), 'utf8'));
const webHashes = new Map(exports.files.map(file => [file.output, file.output_sha256]));
const combinations = new Set();
for (const style of manifest.styles) {
  const expectedStyle = canonicalStyles.get(style.ttf);
  if (!expectedStyle || Object.entries(expectedStyle).some(([key, value]) => style[key] !== value) ||
      style.italic !== (style.css_style === 'italic') || style.characters !== 2225) {
    throw new Error(`Font manifest differs from the canonical style: ${style.ttf}`);
  }
  const face = cssFaces.get(`./${style.woff2}?v=${manifest.version}`);
  if (!face || face['font-family']?.replace(/^(["'])(.*)\1$/, '$2') !== style.family ||
      Number(face['font-weight']) !== style.weight || face['font-style'] !== style.css_style) {
    throw new Error(`CSS descriptors differ from the font manifest: ${style.woff2}`);
  }
  combinations.add(`${style.family}/${style.weight}/${style.css_style}`);
  for (const format of ['ttf', 'woff2']) {
    const name = style[format];
    const bytes = await readFile(new URL(`public/fonts/${name}`, root));
    const expected = format === 'ttf' ? verification.ttf_sha256[name] : webHashes.get(name);
    if (createHash('sha256').update(bytes).digest('hex') !== expected) throw new Error(`Font hash mismatch: ${name}`);
    if (format === 'ttf') {
      const actual = fontFaceMetadata(bytes);
      if (['family', 'style', 'weight', 'italic', 'variable'].some(key => actual[key] !== style[key]) ||
          actual.version !== Number(manifest.version)) throw new Error(`Font metadata differs from the manifest: ${name}`);
    }
  }
}
if (combinations.size !== 28 || (manifest.version === '0.506' && !verification.byte_identical_to_recorded_build) ||
    Object.values(verification.validation).some(track => !track.passed)) throw new Error('Incomplete verified family');
if (manifest.version === '0.507') {
  const review = JSON.parse(await readFile(new URL(`public/fonts/${verification.individual_review}`, root), 'utf8'));
  if (!verification.license_amendment) throw new Error('Apply the OFL metadata amendment before publishing the font release');
  const reviewedHashes = (await checkFontLicense(root, verification, review, exports)).reviewed_font_hashes;
  if (!verification.validated_release || !review.complete || review.styles !== 28 || review.encoded_characters !== 2225 ||
      Object.keys(review.font_hashes).length !== 28 ||
      Object.entries(reviewedHashes).some(([name, hash]) => review.font_hashes[name] !== hash) ||
      exports.files.some(file => !file.all_outlines_preserved)) throw new Error('Incomplete individual glyph review');
  await access(new URL('public/documents/character-inventory.csv', root));
}
console.log(`Checked source syntax and ${required.length} required files in ${fileURLToPath(root)}`);
