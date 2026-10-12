#!/usr/bin/env python3
"""Export character metrics from the actual completed fonts."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import unicodedata

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('family', 'style', 'weight', 'italic', 'codepoint', 'character',
          'unicode_name', 'glyph', 'advance', 'lsb', 'xMin', 'yMin', 'xMax',
          'yMax', 'contours')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    args = parser.parse_args()
    build = args.build.resolve()
    report = json.loads((build / 'build-report.json').read_text())
    styles = json.loads((ROOT / 'styles.json').read_text())['styles']
    output = build / 'documents' / 'character-inventory.csv'
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    with output.open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(FIELDS)
        for style in sorted(styles, key=lambda item: item['ttf']):
            path = build / 'fonts' / style['ttf']
            if hashlib.sha256(path.read_bytes()).hexdigest() != report['hashes'][path.name]:
                raise ValueError('Inventory input differs from the verified build: ' + path.name)
            with TTFont(path) as font:
                cmap = font.getBestCmap()
                if len(cmap) != 2225:
                    raise ValueError('Incomplete character inventory: ' + path.name)
                for cp, name in sorted(cmap.items()):
                    glyph = font['glyf'][name]
                    glyph.recalcBounds(font['glyf'])
                    box = [getattr(glyph, field, '') for field in FIELDS[10:14]] if glyph.numberOfContours else ['', '', '', '']
                    writer.writerow([style['family'], style['style'], style['weight'],
                                     style['css_style'] == 'italic', f'U+{cp:04X}', chr(cp),
                                     unicodedata.name(chr(cp), ''), name,
                                     *font['hmtx'][name], *box, glyph.numberOfContours])
                    rows += 1
    if rows != 62300:
        raise ValueError('Incomplete style inventory')
    print(json.dumps({'file': str(output), 'rows': rows, 'version': report['version']}))


if __name__ == '__main__':
    main()
