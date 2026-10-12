#!/usr/bin/env python3
"""Check individual review coverage and the exact evidence behind decisions."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-fonts', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    cmap = TTFont(args.baseline_fonts / 'netfyrsans-Regular.ttf').getBestCmap()
    expected = {f'U+{cp:04X}' for cp in cmap}
    entries = []
    for partition in ('latin', 'language', 'symbols'):
        ledger = ROOT / 'review' / (partition + '.jsonl')
        if ledger.exists():
            entries.extend(json.loads(line) for line in ledger.read_text().splitlines() if line.strip())
    counts = Counter(entry['code'] for entry in entries)
    issues = []
    for code, count in counts.items():
        if count != 1:
            issues.append({'code': code, 'issue': 'duplicate decisions'})
        if code not in expected:
            issues.append({'code': code, 'issue': 'not in baseline cmap'})
    for entry in entries:
        proof = args.evidence / 'proofs' / (entry['code'].replace('+', '') + '.png')
        if not proof.exists() or hashlib.sha256(proof.read_bytes()).hexdigest() != entry['proof_sha256']:
            issues.append({'code': entry['code'], 'issue': 'evidence hash mismatch'})
        if entry['inspected_styles'] != 28:
            issues.append({'code': entry['code'], 'issue': 'not all styles inspected'})
        if entry['verdict'] not in ('pass', 'repair', 'needs-context'):
            issues.append({'code': entry['code'], 'issue': 'unknown verdict'})
    missing = sorted(expected - set(counts))
    unresolved = [entry['code'] for entry in entries if entry['verdict'] == 'needs-context']
    repair_codes = sorted(entry['code'] for entry in entries if entry['verdict'] == 'repair')
    result = {
        'baseline': '0.506', 'working_revision': '0.507', 'encoded_characters': len(expected),
        'styles': 28, 'expected_character_style_cases': len(expected) * 28,
        'reviewed_characters': len(set(counts)), 'reviewed_character_style_cases': len(set(counts)) * 28,
        'verdicts': dict(Counter(entry['verdict'] for entry in entries)),
        'missing': missing, 'unresolved': unresolved, 'repairs': repair_codes, 'issues': issues,
        'initial_review_complete': not missing and not unresolved and not issues,
        'scope': 'Individual agent decisions with hashed visual evidence. Not native-reader certification.'
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('reviewed_characters', 'encoded_characters', 'verdicts', 'initial_review_complete')}))
    if issues or (args.require_complete and not result['initial_review_complete']):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
