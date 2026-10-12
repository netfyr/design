#!/usr/bin/env python3
"""Require a complete initial review and verified final after-proofs."""
import argparse
import hashlib
import json
from pathlib import Path
import unicodedata
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', required=True, type=Path)
    parser.add_argument('--initial-coverage', required=True, type=Path)
    parser.add_argument('--after-evidence', required=True, type=Path)
    args = parser.parse_args()
    build = args.build.resolve()
    coverage = json.loads(args.initial_coverage.read_text())
    if not coverage['initial_review_complete']:
        raise ValueError('Initial individual review is incomplete')
    repair_report = json.loads((build / 'repair-report.json').read_text())
    build_report = json.loads((build / 'build-report.json').read_text())
    required_sources = {'compiled_repairs.py', 'repair_geometry.py', 'layout_repairs.py',
                        'latin_repairs.py', 'language_repairs.py', 'symbol_repairs.py'}
    source_hashes = repair_report.get('source_sha256', {})
    if set(source_hashes) != required_sources or any(
            digest(ROOT / 'sources' / name) != expected
            for name, expected in source_hashes.items()):
        raise ValueError('Release source differs from the compiled repair source')
    actual = {path.name: digest(path) for path in (build / 'fonts').glob('*.ttf')}
    inputs = json.loads((args.after_evidence / 'inputs.json').read_text())
    if len(actual) != 28 or actual != inputs['fonts'] or actual != build_report['hashes']:
        raise ValueError('After-evidence and build must cover the exact same complete fonts')
    changed_codes = set()
    changed_unencoded = set()
    for row in repair_report['files']:
        changed_codes.update(row.get('layout_repairs', {}).get('codepoints', []))
        changed_codes.update(item['codepoint'] for item in row.get('contextual_repairs', []))
        with TTFont(build / 'fonts' / row['file']) as font:
            cmap = font.getBestCmap()
            changed = set(row['changed_glyphs']) | set(row.get('metric_changes', {}))
            changed_codes.update(f'U+{cp:04X}' for cp, name in cmap.items() if name in changed)
            changed_unencoded.update(changed - set(cmap.values()))
    if set(coverage['repairs']) - changed_codes:
        raise ValueError('Confirmed repairs remain unimplemented: ' + str(set(coverage['repairs']) - changed_codes))
    after_entries = []
    for partition in ('latin', 'language', 'symbols'):
        path = ROOT / 'review' / (partition + '-after.jsonl')
        if path.exists():
            after_entries.extend(json.loads(line) for line in path.read_text().splitlines() if line.strip())
    reviewed_codes = set()
    reviewed_unencoded = set()
    for entry in after_entries:
        if entry['verdict'] != 'pass' or entry['inspected_styles'] != 28:
            continue
        code = entry['code']
        proof = args.after_evidence / 'proofs' / (code.replace('+', '') + '.png')
        if not proof.exists() or digest(proof) != entry['proof_sha256']:
            raise ValueError('After-proof does not match the reviewed final evidence: ' + code)
        case = json.loads((args.after_evidence / 'cases' / (code.replace('+', '') + '.json')).read_text())
        native_glyphs = {glyph['glyph'] for face in case['cases']
                         for context in face['contexts'] for glyph in context['run']}
        if set(entry.get('unencoded_glyphs', [])) - native_glyphs:
            raise ValueError('Claimed internal glyph is absent from the reviewed shaped runs: ' + code)
        contexts = case.get('context_proofs', [])
        if unicodedata.category(chr(int(code[2:], 16))).startswith('M') or contexts:
            if not contexts or entry.get('context_proofs') != contexts:
                raise ValueError('Final contexts lack individual after-review evidence: ' + code)
            for context in contexts:
                if digest(args.after_evidence / context['proof']) != context['sha256']:
                    raise ValueError('Final combining context proof changed: ' + code)
        reviewed_codes.add(code)
        reviewed_unencoded.update(entry.get('unencoded_glyphs', []))
    missing = sorted(changed_codes - reviewed_codes)
    missing_unencoded = sorted(changed_unencoded - reviewed_unencoded)
    if missing or missing_unencoded:
        raise ValueError(f'Final after-review is incomplete: {missing}; internal glyphs: {missing_unencoded}')
    tracks = {track: json.loads((build / 'validation' / (track + '.json')).read_text())
              for track in ('metadata', 'shaping', 'geometry', 'cells', 'layout-changes')}
    for track, report in tracks.items():
        if not report['passed'] or len(report['files']) != 28:
            raise ValueError('Validation failed: ' + track)
        if {row['file']: row['sha256'] for row in report['files']} != actual:
            raise ValueError('Validation covers different fonts: ' + track)
    result = {'complete': True, 'version': '0.507', 'baseline': '0.506',
              'encoded_characters': coverage['encoded_characters'], 'styles': 28,
              'initial_review': coverage['verdicts'], 'repaired_characters': sorted(changed_codes),
              'repaired_internal_glyphs': sorted(changed_unencoded), 'font_hashes': actual,
              'source_sha256': source_hashes,
              'software_checks': {track: True for track in tracks},
              'scope': 'Individual subagent visual comparisons and local software checks; no native-reader certification, vendor acceptance or licensing change.'}
    (ROOT / 'review/final-verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'complete': True, 'reviewed': coverage['encoded_characters'], 'repaired': len(changed_codes)}))


if __name__ == '__main__':
    main()
