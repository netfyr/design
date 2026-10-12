#!/usr/bin/env python3
"""Compare actual HarfBuzz runs for every character outside declared layout changes."""
import argparse
import hashlib
import json
from pathlib import Path
import unicodedata as ud
from fontTools.pens.boundsPen import BoundsPen
from shaping import Shaper


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_right_marks(shaper):
    glyphs = shaper.tt.getGlyphSet()
    results = []
    for cp in (0x0315, 0x031A, 0x0358):
        mark_name = shaper.cmap[cp]
        for text in ('a' + chr(cp), 'i' + chr(cp), 'i\u034f' + chr(cp),
                     'o' + chr(cp), 'α' + chr(cp)):
            run = shaper.shape(text)
            boxes = []
            pos = 0
            for item in run:
                pen = BoundsPen(glyphs)
                glyphs[item['glyph']].draw(pen)
                if pen.bounds is not None:
                    x0, y0, x1, y1 = pen.bounds
                    boxes.append((item['glyph'], x0 + pos + item['x'], y0 + item['y'],
                                  x1 + pos + item['x'], y1 + item['y']))
                pos += item['advance']
            base = next(box for box in boxes if box[0] != mark_name)
            mark = next(box for box in boxes if box[0] == mark_name)
            gap = mark[2] - base[4]
            valid = (gap >= 20 and (mark[1] + mark[3]) > (base[1] + base[3])
                     and all(item['advance'] == 0 for item in run if item['glyph'] == mark_name)
                     and (text[0] != 'i' or run[0]['glyph'] == shaper.cmap[ord('i')]))
            results.append({'code': f'U+{cp:04X}', 'text': text,
                            'above_ink_gap': gap, 'passed': valid})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--repairs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repair_rows = json.loads(args.repairs.read_text())['files']
    files = []
    issues = []
    for row in repair_rows:
        before_path = args.before / row['file']
        after_path = args.after / row['file']
        if digest(before_path) != row['baseline_sha256'] or digest(after_path) != row['sha256']:
            raise ValueError('Layout comparison inputs differ from repair report')
        before, after = Shaper(before_path), Shaper(after_path)
        allowed = {int(code[2:], 16) for code in row.get('layout_repairs', {}).get('codepoints', [])}
        metric_names = {name for name, change in row.get('metric_changes', {}).items() if change['before'][0] != change['after'][0]}
        allowed.update(cp for cp, name in before.cmap.items() if name in metric_names)
        checked = 0
        changes = []
        for cp in sorted(before.cmap):
            if cp in allowed:
                continue
            ch = chr(cp)
            texts = ['H' + ch + 'H']
            if ud.category(ch).startswith('M'):
                texts += ['a' + ch, 'i' + ch, 'i\u034f' + ch, 'o' + ch, 'α' + ch]
            for text in texts:
                checked += 1
                old, new = before.shape(text), after.shape(text)
                if old != new:
                    changes.append({'code': f'U+{cp:04X}', 'text': text, 'before': old, 'after': new})
        right_marks = check_right_marks(after)
        files.append({'file': row['file'], 'sha256': row['sha256'], 'checked_runs': checked,
                      'declared_layout_or_advance_codepoints': [f'U+{cp:04X}' for cp in sorted(allowed)],
                      'right_mark_positioning': right_marks,
                      'unexpected_changes': changes})
        if changes or any(not result['passed'] for result in right_marks):
            issues.append(row['file'])
        before.close()
        after.close()
    report = {'passed': not issues, 'files': files, 'issues': issues,
              'scope': 'Actual HarfBuzz glyph IDs, advances and offsets for every encoded character, plus combining contexts, excluding only declared layout/advance targets.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'styles': len(files), 'checked_runs': sum(row['checked_runs'] for row in files)}))
    if issues:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
