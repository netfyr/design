#!/usr/bin/env python3
"""Apply an authorized OFL notice without changing reviewed font tables."""
import argparse
import hashlib
import json
import struct
from io import BytesIO
from pathlib import Path

from fontTools.ttLib import TTFont

LICENSE_URL = 'https://openfontlicense.org'
NAME_IDS = {0, 13, 14}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def tables(data):
    count = struct.unpack_from('>H', data, 4)[0]
    result = {}
    for index in range(count):
        tag, _, offset, length = struct.unpack_from('>4sIII', data, 12 + index * 16)
        tag = tag.decode('ascii')
        if tag in result or offset + length > len(data):
            raise ValueError('Invalid SFNT directory')
        result[tag] = data[offset:offset + length]
    return result


def normalized_head(data):
    return data[:8] + bytes(4) + data[12:]


def checksum(data):
    padded = data + bytes((-len(data)) % 4)
    return sum(struct.unpack('>' + 'I' * (len(padded) // 4), padded)) & 0xffffffff


def replace_name(original, replacement):
    source = tables(original)
    source['name'] = replacement
    source['head'] = normalized_head(source['head'])
    count = len(source)
    offset = 12 + count * 16
    directory = []
    payload = bytearray()
    head_offset = None
    for tag, content in source.items():
        directory.append(struct.pack('>4sIII', tag.encode('ascii'), checksum(content), offset, len(content)))
        if tag == 'head':
            head_offset = offset
        padded = content + bytes((-len(content)) % 4)
        payload.extend(padded)
        offset += len(padded)
    result = bytearray(original[:12] + b''.join(directory) + payload)
    struct.pack_into('>I', result, head_offset + 8, (0xB1B0AFBA - checksum(result)) & 0xffffffff)
    if checksum(result) != 0xB1B0AFBA:
        raise ValueError('SFNT master checksum failed')
    return bytes(result)


def unrelated_names(font):
    return sorted([record.platformID, record.platEncID, record.langID, record.nameID,
                   bytes(record.string).hex()] for record in font['name'].names
                  if record.nameID not in NAME_IDS)


def amend(original, copyright_notice, license_text):
    font = TTFont(BytesIO(original), lazy=True)
    previous_names = unrelated_names(font)
    for name_id in NAME_IDS:
        font['name'].removeNames(nameID=name_id)
    for name_id, text in [(0, copyright_notice), (13, license_text), (14, LICENSE_URL)]:
        for platform, encoding, language in [(3, 1, 0x409), (0, 3, 0)]:
            font['name'].setName(text, name_id, platform, encoding, language)
    output = replace_name(original, font['name'].compile(font))
    before, after = tables(original), tables(output)
    if set(before) != set(after):
        raise ValueError('Font table inventory changed')
    for tag in before:
        if tag == 'name':
            continue
        left = normalized_head(before[tag]) if tag == 'head' else before[tag]
        right = normalized_head(after[tag]) if tag == 'head' else after[tag]
        if left != right:
            raise ValueError('Unapproved font table change: ' + tag)
    amended = TTFont(BytesIO(output), lazy=True)
    if unrelated_names(amended) != previous_names or amended['OS/2'].fsType != 0:
        raise ValueError('Unrelated names or embedding permission changed')
    for name_id, text in [(0, copyright_notice), (13, license_text), (14, LICENSE_URL)]:
        if {r.toUnicode() for r in amended['name'].names if r.nameID == name_id} != {text}:
            raise ValueError('License name records disagree')
    invariant = {tag: digest(normalized_head(value) if tag == 'head' else value)
                 for tag, value in before.items() if tag != 'name'}
    return output, invariant, previous_names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--copyright-holder', required=True)
    parser.add_argument('--copyright-year', required=True)
    parser.add_argument('--license-file', required=True, type=Path)
    parser.add_argument('--input-fonts', required=True, type=Path)
    parser.add_argument('--output-fonts', required=True, type=Path)
    parser.add_argument('--review', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    holder = args.copyright_holder.strip()
    if not holder or any(value in holder for value in ('<', '>', '\n', '\r')):
        parser.error('An explicit copyright holder is required')
    notice = f'Copyright (c) {args.copyright_year}, {holder}'
    license_bytes = args.license_file.read_bytes()
    license_text = license_bytes.decode('utf-8')
    if notice not in license_text or 'SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007' not in license_text:
        parser.error('OFL.txt must contain the authorized copyright notice and official OFL1.1 text')
    review_bytes = args.review.read_bytes()
    review = json.loads(review_bytes)
    expected = review['font_hashes']
    if not review.get('complete') or len(expected) != 28 or review.get('version') != '0.507':
        parser.error('A complete canonical 28-style 0.507 review is required')
    if args.input_fonts.resolve() == args.output_fonts.resolve() or args.output_fonts.exists() or args.report.exists():
        parser.error('Choose fresh output paths; reviewed input fonts are immutable')
    prepared = []
    for name, old_sha in sorted(expected.items()):
        if Path(name).name != name or not name.endswith('.ttf'):
            raise ValueError('Invalid reviewed font filename')
        original = (args.input_fonts / name).read_bytes()
        if digest(original) != old_sha:
            raise ValueError('Input differs from the canonical review: ' + name)
        output, invariant, previous_names = amend(original, notice, license_text)
        prepared.append((name, output, {'file': name, 'reviewed_sha256': old_sha,
                         'published_sha256': digest(output), 'unchanged_tables': invariant,
                         'unrelated_name_records': previous_names}))
    args.output_fonts.mkdir(parents=True)
    for name, output, _ in prepared:
        (args.output_fonts / name).write_bytes(output)
    report = {'schema': 'netfyr-font-license-amendment/v1', 'version': '0.507',
              'kind': 'metadata-only', 'license': 'OFL-1.1',
              'copyright_holder': holder, 'copyright_year': args.copyright_year,
              'copyright_notice': notice, 'license_url': LICENSE_URL,
              'license_sha256': digest(license_bytes),
              'canonical_review_sha256': digest(review_bytes),
              'amendment_source_sha256': digest(Path(__file__).read_bytes()),
              'allowed_changed_name_ids': sorted(NAME_IDS),
              'reviewed_font_hashes': expected,
              'published_font_hashes': {name: digest(output) for name, output, _ in prepared},
              'files': [row for _, _, row in prepared],
              'scope': 'OFL metadata amendment only; all raw font tables other than name and the head checksum are unchanged. Existing glyph review remains bound to its original fonts; visual review was not repeated.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print('Amended 28 fonts; reviewed glyph tables, layout, metrics and unrelated names are unchanged')


if __name__ == '__main__':
    main()
