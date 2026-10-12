#!/usr/bin/env python3
"""Reproduce the baseline, apply declared repairs, and validate the new revision."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from compiled_repairs import apply, digest, ROOT


def run(arguments, log):
    with log.open('w') as output:
        subprocess.run([sys.executable, *map(str, arguments)], stdout=output,
                       stderr=subprocess.STDOUT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline-build', type=Path, help='Reuse an exact checksum-verified 0.506 build')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--documents', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error('Use a fresh output directory')
    output.mkdir(parents=True)
    logs = output / 'logs'
    logs.mkdir()
    if args.baseline_build:
        baseline = args.baseline_build.resolve()
        expected = json.loads((ROOT / 'baseline-font-hashes.json').read_text())
        if {path.name: digest(path) for path in (baseline / 'fonts').glob('*.ttf')} != expected:
            raise ValueError('Baseline build hashes differ')
        for directory in ('fonts', 'reports'):
            shutil.copytree(baseline / directory, output / directory)
        from build_all import reference as check_reference
        reference = check_reference(args.reference.resolve(), output, False)
    else:
        run([ROOT / 'sources/build_all.py', '--reference', args.reference.resolve(),
             '--output', output, '--jobs', args.jobs, '--boolean', 'inkscape'], logs / 'baseline.log')
        reference = Path(json.loads((output / 'build-report.json').read_text())['reference'])
    shutil.copytree(output / 'fonts', output / 'baseline-fonts')
    repair_report = apply(output / 'fonts')
    baseline_reports = output / 'reports/baseline'
    baseline_reports.mkdir()
    for row in repair_report['files']:
        path = output / 'reports' / (Path(row['file']).stem + '.json')
        shutil.copy2(path, baseline_reports / path.name)
        report = json.loads(path.read_text())
        report.update(version='0.507', sha256=row['sha256'],
                      bytes=(output / 'fonts' / row['file']).stat().st_size,
                      baseline_sha256=row['baseline_sha256'],
                      repair_report='../repair-report.json',
                      changed_glyphs=row['changed_glyphs'])
        if 'protected_reference' in report:
            report['baseline_reference'] = report.pop('protected_reference')
        path.write_text(json.dumps(report, indent=2) + '\n')
    tasks = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for track in ('metadata', 'shaping', 'geometry', 'cells'):
            command = [ROOT / 'sources/validation/validate.py', '--track', track,
                       '--fonts', output / 'fonts', '--reference', reference,
                       '--repairs', output / 'repair-report.json',
                       '--output', output / 'validation' / (track + '.json')]
            tasks.append(pool.submit(run, command, logs / (track + '.log')))
        for task in tasks:
            task.result()
    if not all(json.loads(path.read_text())['passed'] for path in (output / 'validation').glob('*.json')):
        raise ValueError('Validation failed; inspect output reports')
    run([ROOT / 'sources/validation/check_layout_changes.py', '--before', output / 'baseline-fonts',
         '--after', output / 'fonts', '--repairs', output / 'repair-report.json',
         '--output', output / 'validation/layout-changes.json'], logs / 'layout-changes.log')
    hashes = {path.name: digest(path) for path in sorted((output / 'fonts').glob('*.ttf'))}
    (output / 'build-report.json').write_text(json.dumps({
        'version': '0.507', 'styles': 28, 'hashes': hashes, 'reference': str(reference),
        'identical_to_recorded_environment': False,
        'baseline_reproduced': True, 'declared_repairs_verified': repair_report['passed'],
        'scope': 'Fresh revision with explicit glyph repairs; no baseline hash equivalence asserted.'
    }, indent=2) + '\n')
    if args.documents:
        documents = output / 'documents'
        documents.mkdir()
        run([ROOT / 'sources/export_inventory.py', '--build', output], logs / 'inventory.log')
        os.environ.update(NETFYR_BUILD=str(output), NETFYR_DELIVERY=str(documents))
        for script in ('build_brand.py', 'build_specimen.py', 'build_type_guide.py'):
            run([ROOT / 'sources/documents' / script], logs / (script + '.log'))
    print(f'Validated 28 corrected styles in {output}', flush=True)


if __name__ == '__main__':
    main()
