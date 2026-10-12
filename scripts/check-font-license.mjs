import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const same = (left, right) => JSON.stringify(left) === JSON.stringify(right);
const sortedMap = value => Object.entries(value).sort(([a], [b]) => a.localeCompare(b));

function sfntTables(bytes) {
  if (bytes.length < 12 || bytes.readUInt32BE(0) !== 0x00010000) throw new Error('Expected a TrueType SFNT');
  const count = bytes.readUInt16BE(4);
  if (12 + count * 16 > bytes.length) throw new Error('Truncated SFNT directory');
  const tables = new Map();
  for (let index = 0; index < count; index++) {
    const pos = 12 + index * 16;
    const tag = bytes.toString('ascii', pos, pos + 4);
    const offset = bytes.readUInt32BE(pos + 8);
    const length = bytes.readUInt32BE(pos + 12);
    if (tables.has(tag) || offset + length > bytes.length) throw new Error('Invalid SFNT table');
    tables.set(tag, bytes.subarray(offset, offset + length));
  }
  return tables;
}

function nameRecords(bytes) {
  const count = bytes.readUInt16BE(2);
  const strings = bytes.readUInt16BE(4);
  const records = [];
  for (let index = 0; index < count; index++) {
    const pos = 6 + index * 12;
    if (pos + 12 > bytes.length) throw new Error('Truncated name table');
    const fields = [0, 2, 4, 6].map(offset => bytes.readUInt16BE(pos + offset));
    const length = bytes.readUInt16BE(pos + 8);
    const start = strings + bytes.readUInt16BE(pos + 10);
    if (start + length > bytes.length) throw new Error('Invalid name string');
    records.push([...fields, bytes.subarray(start, start + length).toString('hex')]);
  }
  return records;
}

function nameText(record) {
  if (![0, 3].includes(record[0])) throw new Error('Unexpected license name encoding');
  const bytes = Buffer.from(record[4], 'hex');
  if (bytes.length % 2) throw new Error('Invalid UTF-16 name');
  return bytes.swap16().toString('utf16le');
}

function recordOrder(a, b) {
  for (let index = 0; index < 4; index++) if (a[index] !== b[index]) return a[index] - b[index];
  return a[4].localeCompare(b[4]);
}

export function fontFaceMetadata(bytes) {
  const tables = sfntTables(bytes);
  const names = nameRecords(tables.get('name'));
  const name = id => {
    const values = new Set(names.filter(record => [0, 3].includes(record[0]) && record[3] === id).map(nameText));
    if (values.size !== 1) throw new Error(`Font name${id} is missing or inconsistent`);
    return [...values][0];
  };
  const os2 = tables.get('OS/2');
  const head = tables.get('head');
  const italic = Boolean(os2.readUInt16BE(62) & 1);
  if (italic !== Boolean(head.readUInt16BE(44) & 2)) throw new Error('Font italic flags disagree');
  return {
    family: name(16), style: name(17).replaceAll(' ', ''),
    weight: os2.readUInt16BE(4), italic, variable: tables.has('fvar'),
    version: Math.round(head.readInt32BE(4) / 65536 * 1000) / 1000,
  };
}

export async function checkFontLicense(root, verification, review, exports) {
  if (verification.license_amendment !== 'license-amendment.json') throw new Error('Unknown font license amendment');
  const reportBytes = await readFile(new URL('public/fonts/license-amendment.json', root));
  if (sha(reportBytes) !== verification.license_amendment_sha256) throw new Error('Font license amendment hash mismatch');
  const report = JSON.parse(reportBytes);
  const licenseBytes = await readFile(new URL('public/fonts/OFL.txt', root));
  const licenseText = licenseBytes.toString('utf8');
  for (const path of ['OFL.txt', 'font-sources/0.507/OFL.txt']) {
    if (!(await readFile(new URL(path, root))).equals(licenseBytes)) throw new Error(`Font license differs: ${path}`);
  }
  const reviewBytes = await readFile(new URL(`public/fonts/${verification.individual_review}`, root));
  if (report.schema !== 'netfyr-font-license-amendment/v1' || report.kind !== 'metadata-only' ||
      report.version !== '0.507' || report.license !== 'OFL-1.1' || report.files.length !== 28 ||
      report.license_url !== 'https://openfontlicense.org' ||
      !same(report.allowed_changed_name_ids, [0, 13, 14]) ||
      sha(licenseBytes) !== report.license_sha256 || sha(reviewBytes) !== report.canonical_review_sha256 ||
      !licenseText.includes(report.copyright_notice) ||
      !licenseText.includes('SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007') ||
      !same(sortedMap(report.reviewed_font_hashes), sortedMap(review.font_hashes)) ||
      !same(sortedMap(report.published_font_hashes), sortedMap(verification.ttf_sha256))) {
    throw new Error('Invalid OFL amendment provenance');
  }
  const source = await readFile(new URL('font-sources/0.507/sources/license_fonts.py', root));
  if (sha(source) !== report.amendment_source_sha256) throw new Error('Font amendment source changed');
  const seen = new Set();
  for (const row of report.files) {
    if (seen.has(row.file) || !/^netfyr(?:sans|mono)-[A-Za-z]+\.ttf$/.test(row.file)) throw new Error('Invalid amended font inventory');
    seen.add(row.file);
    const bytes = await readFile(new URL(`public/fonts/${row.file}`, root));
    if (sha(bytes) !== row.published_sha256 || row.published_sha256 !== verification.ttf_sha256[row.file] ||
        row.reviewed_sha256 !== review.font_hashes[row.file]) throw new Error(`Amended font hash mismatch: ${row.file}`);
    const tables = sfntTables(bytes);
    const invariantTags = [...tables.keys()].filter(tag => tag !== 'name').sort();
    if (!same(invariantTags, Object.keys(row.unchanged_tables).sort())) throw new Error('Amended font table inventory changed');
    for (const tag of invariantTags) {
      const table = Buffer.from(tables.get(tag));
      if (tag === 'head') table.writeUInt32BE(0, 8);
      if (sha(table) !== row.unchanged_tables[tag]) throw new Error(`Unreviewed table change: ${row.file}/${tag}`);
    }
    if (tables.get('OS/2').readUInt16BE(8) !== 0) throw new Error('OFL embedding restriction');
    const names = nameRecords(tables.get('name'));
    const unrelated = names.filter(record => ![0, 13, 14].includes(record[3])).sort(recordOrder);
    if (!same(unrelated, row.unrelated_name_records)) throw new Error('Unrelated font names changed');
    for (const [id, expected] of [[0, report.copyright_notice], [13, licenseText], [14, report.license_url]]) {
      const selected = names.filter(record => record[3] === id);
      if (selected.length !== 2 || selected.some(record => nameText(record) !== expected)) throw new Error(`Font license name${id} mismatch`);
    }
    const web = exports.files.find(file => file.source === row.file);
    if (!web || web.source_sha256 !== row.published_sha256 || !web.all_outlines_preserved || !web.cmap_metrics_and_layout_preserved) {
      throw new Error('OFL WOFF2 export covers different font');
    }
  }
  if (seen.size !== 28 || Object.keys(review.font_hashes).some(name => !seen.has(name))) throw new Error('Incomplete OFL amendment');
  return report;
}
