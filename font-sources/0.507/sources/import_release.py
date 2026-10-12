#!/usr/bin/env python3
"""Import a verified complete font revision into the local design library."""
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', required=True, type=Path)
    parser.add_argument('--build', required=True, type=Path)
    args = parser.parse_args()
    release, build = args.release.resolve(), args.build.resolve()
    manifest = json.loads((release / 'styles.json').read_text())
    report = json.loads((build / 'build-report.json').read_text())
    version = manifest['version']
    if version == '0.506':
        expected = json.loads((release / 'validation/final-font-hashes.json').read_text())
        if not report['identical_to_recorded_environment'] or report['hashes'] != expected:
            raise ValueError('The TTF build must match the recorded release')
        review = None
    elif version == '0.507':
        expected = report['hashes']
        review = json.loads((release / 'review/final-verification.json').read_text())
        if not report.get('baseline_reproduced') or not report.get('declared_repairs_verified') or not review['complete']:
            raise ValueError('The baseline, repairs and complete individual review must be verified')
        if review['font_hashes'] != expected:
            raise ValueError('The final review covers different fonts')
        repairs = json.loads((build / 'repair-report.json').read_text())
        if not review.get('source_sha256') or review['source_sha256'] != repairs.get('source_sha256'):
            raise ValueError('The final review must verify the compiled repair source')
        if any(digest(release / 'sources' / name) != sha
               for name, sha in review['source_sha256'].items()):
            raise ValueError('Release source differs from the reviewed build')
    else:
        raise ValueError('Unknown font release')
    exports = json.loads((build / 'web/export-report.json').read_text())
    track_names = ('metadata', 'shaping', 'geometry', 'cells') + (('layout-changes',) if review else ())
    tracks = {track: json.loads((build / f'validation/{track}.json').read_text()) for track in track_names}
    if len(manifest['styles']) != 28 or len(expected) != 28:
        raise ValueError('Expected the complete 28-style family')
    if not all(track['passed'] for track in tracks.values()):
        raise ValueError('Every local validation track must pass')
    for track in tracks.values():
        if len(track['files']) != 28:
            raise ValueError('Every validation track must cover all 28 styles')
        for row in track['files']:
            if row['sha256'] != expected[row['file']]:
                raise ValueError(f"Validation covers a different font: {row['file']}")
    exported = {item['source']: item for item in exports['files']}
    if len(exported) != 28:
        raise ValueError('Expected 28 verified web exports')
    for name in ('netfyr-identity.pdf', 'netfyr-font-guide.pdf', 'netfyr-complete-specimen.pdf'):
        if not (build / 'documents' / name).is_file():
            raise ValueError(f'Missing regenerated document: {name}; build with --documents')
    if review and not (build / 'documents/character-inventory.csv').is_file():
        raise ValueError('Missing character inventory from the corrected fonts')
    for style in manifest['styles']:
        ttf, woff = build / 'fonts' / style['ttf'], build / 'web' / style['woff2']
        item = exported[style['ttf']]
        if digest(ttf) != expected[ttf.name] or digest(woff) != item['output_sha256']:
            raise ValueError(f'Changed font: {ttf.name}')
        if item['source_sha256'] != expected[ttf.name] or not item['cmap_metrics_and_layout_preserved']:
            raise ValueError(f'Unverified conversion: {woff.name}')
        if review and not item.get('all_outlines_preserved'):
            raise ValueError(f'Web export changed reviewed outlines: {woff.name}')
        style.update(italic=style['css_style'] == 'italic', characters=2225)
    manifest['verification'] = 'verification.json'
    destination = ROOT / 'public/fonts'
    destination.mkdir(parents=True, exist_ok=True)
    for style in manifest['styles']:
        shutil.copy2(build / 'fonts' / style['ttf'], destination / style['ttf'])
        shutil.copy2(build / 'web' / style['woff2'], destination / style['woff2'])
    shutil.copy2(build / 'web/netfyr.css', destination / 'netfyr.css')
    shutil.copy2(build / 'web/export-report.json', destination / 'export-report.json')
    validation = destination / 'validation'
    validation.mkdir(exist_ok=True)
    for track in tracks:
        shutil.copy2(build / f'validation/{track}.json', validation / f'{track}.json')
    verification = {
        'version': version, 'styles': 28, 'ttf_sha256': expected,
        'byte_identical_to_recorded_build': version == '0.506',
        'validated_release': True,
        'validation': {name: {'passed': value['passed'], 'report': f'validation/{name}.json'}
                       for name, value in tracks.items()},
        'web_export': 'export-report.json',
        'scope': 'Local software checks and exact release hashes. Static, unhinted fonts. '
                 'No independent typography review, vendor acceptance, or public font license is asserted.',
    }
    if review:
        verification.update(individual_review='review/final-verification.json',
                            declared_repairs='repair-report.json',
                            scope='Individual agent glyph comparisons and local software checks. '
                                  'Static, unhinted fonts. No native-reader certification, vendor acceptance or licensing change.')
        shutil.copy2(build / 'repair-report.json', destination / 'repair-report.json')
        shutil.copytree(release / 'review', destination / 'review', dirs_exist_ok=True)
    for name, value in [('font-manifest.json', manifest), ('verification.json', verification)]:
        (destination / name).write_text(json.dumps(value, indent=2) + '\n')
    documents = ROOT / 'public/documents'
    for document in (build / 'documents').glob('*.pdf'):
        shutil.copy2(document, documents / document.name)
    if review:
        shutil.copy2(build / 'documents/character-inventory.csv', documents / 'character-inventory.csv')
    archive = destination / f'netfyr-fonts-{version}.zip'
    names = ['netfyr.css', 'font-manifest.json', 'verification.json', 'export-report.json']
    names += [style[format] for style in manifest['styles'] for format in ('ttf', 'woff2')]
    names += [f'validation/{track}.json' for track in tracks]
    if review:
        names += ['repair-report.json']
        names += [str(path.relative_to(destination)) for path in (destination / 'review').rglob('*') if path.is_file()]
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as output:
        for name in names:
            output.write(destination / name, f'netfyr-fonts-{version}/{name}')
        output.write(documents / 'NOTICE.txt', f'netfyr-fonts-{version}/NOTICE.txt')
        output.writestr(f'netfyr-fonts-{version}/README.txt',
                        f'netfyr {version}: 28 static TTF and WOFF2 styles.\n'
                        'Keep netfyr.css beside the WOFF2 files. Font synthesis must be disabled.\n'
                        'See verification.json for exact build hashes, checks and review scope.\n'
                        'No public font license is assigned. Read NOTICE.txt.\n')
    print(f'Imported 28 verified styles and generated documents; download: {archive}')


if __name__ == '__main__':
    main()
