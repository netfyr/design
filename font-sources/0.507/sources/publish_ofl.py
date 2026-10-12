#!/usr/bin/env python3
"""Stage an OFL publication from the immutable, reviewed 0.507 font build.

The output is a fresh directory, never the live website. Copy its public/fonts
contents and RELEASE.json into the website only after reviewing the results.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

SOURCES = Path(__file__).resolve().parent
RELEASE = SOURCES.parent
WEBSITE = SOURCES.parents[2]
TRACKS = ('metadata', 'shaping', 'geometry', 'cells', 'layout-changes')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def checked_rows(rows, expected, label):
    if len(rows) != len(expected) or {row['file'] for row in rows} != set(expected):
        raise ValueError(f'{label}: expected all 28 reviewed fonts exactly once')
    for row in rows:
        if row['sha256'] != expected[row['file']]:
            raise ValueError(f'{label}: different reviewed font {row["file"]}')


def check_inputs(build, release):
    review = read_json(release / 'review/final-verification.json')
    report = read_json(build / 'build-report.json')
    repairs = read_json(build / 'repair-report.json')
    manifest = read_json(release / 'styles.json')
    release_info = read_json(release / 'RELEASE.json')
    expected = review['font_hashes']
    if (review.get('version') != '0.507' or not review.get('complete')
            or review.get('styles') != 28 or review.get('encoded_characters') != 2225
            or len(expected) != 28 or report.get('version') != '0.507'
            or report.get('hashes') != expected or not report.get('baseline_reproduced')
            or not report.get('declared_repairs_verified') or not repairs.get('passed')):
        raise ValueError('A complete canonical 28-style 0.507 review and build are required')
    if release_info.get('font_hashes') != expected:
        raise ValueError('RELEASE.json covers a different canonical build')
    if (manifest.get('version') != '0.507' or len(manifest['styles']) != 28
            or {style['ttf'] for style in manifest['styles']} != set(expected)):
        raise ValueError('Style manifest covers a different family')
    if not review.get('source_sha256') or review['source_sha256'] != repairs.get('source_sha256'):
        raise ValueError('Repair source provenance is incomplete')
    for name, sha in review['source_sha256'].items():
        if Path(name).name != name or digest(release / 'sources' / name) != sha:
            raise ValueError('Repair source differs from individual review: ' + name)
    for name, sha in expected.items():
        if not re.fullmatch(r'netfyr(?:sans|mono)-[A-Za-z]+\.ttf', name):
            raise ValueError('Invalid reviewed filename: ' + name)
        if digest(build / 'fonts' / name) != sha:
            raise ValueError('Canonical font differs from individual review: ' + name)
    checked_rows(repairs['files'], expected, 'Declared repairs')
    for track in TRACKS:
        validation = read_json(build / 'validation' / (track + '.json'))
        if not validation.get('passed'):
            raise ValueError('Canonical validation failed: ' + track)
        checked_rows(validation['files'], expected, track)
    return review, report, manifest, release_info


def copy_review(source, destination):
    destination.mkdir()
    for path in sorted(source.rglob('*')):
        if '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        if path.is_symlink():
            raise ValueError('Review evidence must not contain symlinks')
        if path.is_file():
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)


def make_archive(fonts):
    archive = fonts / 'netfyr-fonts-0.507.zip'
    files = sorted(path for path in fonts.rglob('*') if path.is_file() and path != archive)
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in files:
            name = 'netfyr-fonts-0.507/' + path.relative_to(fonts).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, path.read_bytes(), compresslevel=9)
    with zipfile.ZipFile(archive) as check:
        if check.testzip() is not None or len(check.namelist()) != len(files):
            raise ValueError('Font download archive failed its integrity check')
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', required=True, type=Path, help='Canonical reviewed build directory')
    parser.add_argument('--release', type=Path, default=RELEASE, help='Reviewed font source release')
    parser.add_argument('--output', type=Path, help='Fresh publication directory')
    parser.add_argument('--copyright-holder')
    parser.add_argument('--copyright-year')
    parser.add_argument('--license-file', type=Path)
    parser.add_argument('--notice-file', type=Path, default=WEBSITE / 'public/documents/NOTICE.txt')
    parser.add_argument('--check-inputs', action='store_true', help='Verify canonical inputs without applying a license')
    args = parser.parse_args()
    build, release = args.build.resolve(), args.release.resolve()
    review, report, manifest, release_info = check_inputs(build, release)
    if args.check_inputs:
        print('Verified 28 canonical font hashes, individual review, repair sources and all five validation tracks')
        return
    for name in ('output', 'copyright_holder', 'copyright_year', 'license_file'):
        if not getattr(args, name):
            parser.error('--' + name.replace('_', '-') + ' is required for publication')
    if not re.fullmatch(r'\d{4}(?:-\d{4})?', args.copyright_year):
        parser.error('--copyright-year must be a year or a year range')
    output = args.output.resolve()
    if (output.exists() or output.is_relative_to(build) or build.is_relative_to(output)
            or output.is_relative_to(release) or release.is_relative_to(output)):
        parser.error('Publication output must be a fresh directory outside the canonical build and source release')
    notice = args.notice_file.read_text()
    if ('SIL Open Font License 1.1' not in notice or 'all rights reserved' not in notice
            or 'No public font license' in notice):
        parser.error('NOTICE.txt must describe OFL fonts and reserved standalone marks')
    license_bytes = args.license_file.read_bytes()
    notice_text = f'Copyright (c) {args.copyright_year}, {args.copyright_holder.strip()}'
    if (notice_text.encode() not in license_bytes
            or b'SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007' not in license_bytes):
        parser.error('License file does not contain the requested copyright notice and OFL 1.1 text')
    output.mkdir(parents=True)
    amendment_file = output / 'license-amendment.json'
    subprocess.run([sys.executable, str(SOURCES / 'license_fonts.py'),
                    '--copyright-holder', args.copyright_holder,
                    '--copyright-year', args.copyright_year,
                    '--license-file', str(args.license_file.resolve()),
                    '--input-fonts', str(build / 'fonts'),
                    '--output-fonts', str(output / 'fonts'),
                    '--review', str(release / 'review/final-verification.json'),
                    '--report', str(amendment_file)], check=True)
    amendment = read_json(amendment_file)
    published = amendment['published_font_hashes']
    shutil.copyfile(build / 'build-report.json', output / 'canonical-build-report.json')
    shutil.copyfile(build / 'repair-report.json', output / 'repair-report.json')
    staged_report = {
        'version': '0.507', 'styles': 28, 'kind': 'metadata-only-publication',
        'hashes': published, 'canonical_hashes': report['hashes'],
        'canonical_build_report': 'canonical-build-report.json',
        'canonical_build_report_sha256': digest(build / 'build-report.json'),
        'license_amendment': 'license-amendment.json',
        'license_amendment_sha256': digest(amendment_file),
        'baseline_reproduced': True, 'declared_repairs_verified': True,
        'scope': 'Canonical build and repair checks refer to canonical_hashes. Published fonts '
                 'differ only in name records 0, 13 and 14 and the head checksum, as verified '
                 'by license-amendment.json. Individual glyph review was not repeated.',
    }
    write_json(output / 'build-report.json', staged_report)
    subprocess.run([sys.executable, str(SOURCES / 'export_web.py'), '--build', str(output)], check=True)
    fonts = output / 'public/fonts'
    fonts.mkdir(parents=True)
    for style in manifest['styles']:
        shutil.copyfile(output / 'fonts' / style['ttf'], fonts / style['ttf'])
        shutil.copyfile(output / 'web' / style['woff2'], fonts / style['woff2'])
        style.update(italic=style['css_style'] == 'italic', characters=2225)
    for name in ('netfyr.css', 'export-report.json'):
        shutil.copyfile(output / 'web' / name, fonts / name)
    for name in ('license-amendment.json', 'canonical-build-report.json', 'build-report.json', 'repair-report.json'):
        shutil.copyfile(output / name, fonts / name)
    (fonts / 'validation').mkdir()
    for track in TRACKS:
        shutil.copyfile(build / 'validation' / (track + '.json'), fonts / 'validation' / (track + '.json'))
    copy_review(release / 'review', fonts / 'review')
    (fonts / 'OFL.txt').write_bytes(license_bytes)
    shutil.copyfile(args.notice_file, fonts / 'NOTICE.txt')
    manifest.update(verification='verification.json', license='OFL-1.1', license_file='OFL.txt')
    write_json(fonts / 'font-manifest.json', manifest)
    verification = {
        'version': '0.507', 'styles': 28, 'ttf_sha256': published,
        'reviewed_ttf_sha256': review['font_hashes'],
        'byte_identical_to_recorded_build': False, 'validated_release': True,
        'font_license': 'OFL-1.1', 'license_file': 'OFL.txt',
        'license_amendment': 'license-amendment.json',
        'license_amendment_sha256': digest(amendment_file),
        'validation': {name: {'passed': True, 'report': f'validation/{name}.json',
                              'font_hashes': 'reviewed_ttf_sha256'} for name in TRACKS},
        'web_export': 'export-report.json',
        'individual_review': 'review/final-verification.json',
        'declared_repairs': 'repair-report.json',
        'scope': 'Individual agent glyph comparisons and five local validation tracks cover '
                 'the canonical reviewed hashes. The OFL metadata amendment preserves every '
                 'other raw font table and unrelated name record. WOFF2 conversions were '
                 'verified against the published TTFs. Static, unhinted fonts; no native-reader '
                 'certification or vendor acceptance.',
    }
    write_json(fonts / 'verification.json', verification)
    (fonts / 'README.txt').write_text(
        'netfyr 0.507: 28 static TTF and WOFF2 styles.\n'
        'The font software is licensed under the SIL Open Font License 1.1. See OFL.txt.\n'
        'Standalone logos and wordmark artwork remain all rights reserved. See NOTICE.txt.\n'
        'Keep netfyr.css beside the WOFF2 files. Set font-synthesis: none.\n'
        'verification.json links the original glyph review to the published files through\n'
        'a verified metadata-only license amendment. Original review reports retain their hashes.\n')
    release_info.update(
        published_font_hashes=published, font_license='OFL-1.1',
        license_file='OFL.txt', license_amendment='../../public/fonts/license-amendment.json',
        license_amendment_sha256=digest(amendment_file),
        publication_scope='Canonical font_hashes and review_scope retain their original meaning. '
                          'Published fonts have OFL metadata; license-amendment.json verifies '
                          'unchanged glyphs, metrics, layout and unrelated metadata.')
    (output / 'OFL.txt').write_bytes(license_bytes)
    archive = make_archive(fonts)
    release_info['font_download'] = {'file': archive.name, 'sha256': digest(archive),
                                     'bytes': archive.stat().st_size}
    write_json(output / 'RELEASE.json', release_info)
    print(json.dumps({'output': str(output), 'fonts': str(fonts), 'styles': 28,
                      'archive_sha256': digest(archive), 'passed': True}, indent=2))


if __name__ == '__main__':
    main()
