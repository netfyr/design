#!/usr/bin/env python3
"""Generate traceable, individual font comparison evidence without fallback."""
import argparse
import hashlib
import json
import sys
import unicodedata as ud
from functools import lru_cache
from pathlib import Path

import cairo
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.cairoPen import CairoPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'sources/validation'))
from shaping import Shaper

REFERENCES = [
    ('Noto Sans', '/usr/share/fonts/noto/NotoSans-Regular.ttf'),
    ('Noto Serif', '/usr/share/fonts/noto/NotoSerif-Regular.ttf'),
    ('DejaVu Sans', '/usr/share/fonts/TTF/DejaVuSans.ttf'),
    ('Noto Mono', '/usr/share/fonts/noto/NotoSansMono-Regular.ttf'),
    ('Noto Math', '/usr/share/fonts/noto/NotoSansMath-Regular.ttf'),
    ('Noto Symbols 2', '/usr/share/fonts/noto/NotoSansSymbols2-Regular.ttf'),
    ('Noto Symbols', '/usr/share/fonts/noto/NotoSansSymbols-Regular.ttf'),
    ('Libertinus Math', '/usr/share/fonts/libertinus/LibertinusMath-Regular.otf'),
]
WEIGHTS = [(300, 'Light'), (400, 'Regular'), (500, 'Medium'), (600, 'SemiBold'),
           (700, 'Bold'), (800, 'ExtraBold'), (900, 'Black')]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@lru_cache(None)
def font(path):
    result = TTFont(path)
    result._review_cmap = result.getBestCmap()
    result._review_glyphs = result.getGlyphSet()
    return result


@lru_cache(None)
def shaper(path):
    return Shaper(path)


def partition(cp):
    if cp < 0x250 or 0x1E00 <= cp <= 0x1EFF or 0xFB00 <= cp <= 0xFB06:
        return 'latin'
    if 0x250 <= cp <= 0x3FF:
        return 'language'
    return 'symbols'


EXTRA_CONTEXTS_ENABLED = False
EXTRA_CONTEXTS = {
    0x025A: ['ɚa', 'ɚɚ', 'aɚ'],
    0x025D: ['ɝa', 'ɝɝ', 'aɝ'],
    0x02AE: ['HʮH', 'ʮa', 'aʮ', 'ʮʮ'],
    0x02AF: ['HʯH', 'ʯa', 'aʯ', 'ʯʯ'],
    0x0307: ['ſ\u034f\u0307', 'ẛ'],
    0x030A: ['A\u034f\u030A', 'U\u034f\u030A', 'u\u034f\u030A', 'w\u034f\u030A', 'y\u034f\u030A', 'Å', 'å', 'Ů', 'ů', 'ẘ', 'ẙ', 'Å'],
    0x030C: ['d\u034f\u030C', 't\u034f\u030C', 'L\u034f\u030C', 'l\u034f\u030C', 'Ʒ\u034f\u030C', 'ʒ\u034f\u030C', 'Ǯ', 'ǯ'],
    0x0327: ['H\u034f\u0327', 'h\u034f\u0327', 'Ḩ', 'ḩ'],
    0x010F: ['d\u034f\u030C'],
    0x0123: ['g\u034f\u0327'],
    0x00C5: ['A\u034f\u030A', 'Å'],
    0x00E5: ['a\u034f\u030A'],
    0x0165: ['t\u034f\u030C'],
    0x016E: ['U\u034f\u030A'],
    0x016F: ['u\u034f\u030A'],
    0x013D: ['L\u034f\u030C'],
    0x013E: ['l\u034f\u030C'],
    0x01EE: ['Ʒ\u034f\u030C'],
    0x01EF: ['ʒ\u034f\u030C'],
    0x1E28: ['H\u034f\u0327'],
    0x1E29: ['h\u034f\u0327'],
    0x1E9B: ['ſ\u034f\u0307'],
    0x1E98: ['w\u034f\u030A'],
    0x1E99: ['y\u034f\u030A', 'ẙ', 'y\u030A'],
    0x212B: ['Å', 'A\u034f\u030A'],
}


def base_contexts(cp):
    ch = chr(cp)
    if ud.category(ch).startswith('M'):
        if 0x35C <= cp <= 0x362:
            return ['a' + ch + 'a', 'i' + ch + 'o', 'i\u034f' + ch + 'o']
        return ['a' + ch, 'i' + ch, 'o' + ch, 'i\u034f' + ch, 'α' + ch]
    if ud.category(ch) in ('Cf', 'Zs', 'Zl', 'Zp'):
        return ['H' + ch + 'H']
    if 0xFB00 <= cp <= 0xFB06:
        return [ch, ['ff', 'fi', 'fl', 'ffi', 'ffl', 'st', 'st'][cp - 0xFB00]]
    if 0x2500 <= cp <= 0x259F:
        return [ch * 3, '│' + ch + '│']
    return ['H' + ch + 'H']


def contexts(cp):
    result = base_contexts(cp)
    if EXTRA_CONTEXTS_ENABLED:
        result += EXTRA_CONTEXTS.get(cp, [])
    return result


def draw_run(ctx, path, text, x, baseline, size, width):
    f = font(path)
    run = shaper(path).shape(text)
    scale = size / 1000
    advance = sum(item['advance'] for item in run)
    x += (width - advance * scale) / 2
    ctx.save()
    ctx.rectangle(x - 30, baseline - size * 1.7, width + 60, size * 2.3)
    ctx.clip()
    ctx.translate(x, baseline)
    ctx.scale(scale, -scale)
    pos = 0
    for item in run:
        ctx.save()
        ctx.translate(pos + item['x'], item['y'])
        ctx.scale(1000 / f['head'].unitsPerEm, 1000 / f['head'].unitsPerEm)
        f._review_glyphs[item['glyph']].draw(CairoPen(f._review_glyphs, ctx))
        ctx.fill()
        ctx.restore()
        pos += item['advance']
    ctx.restore()


def draw_direct(ctx, path, cp, x, baseline, size, width):
    f = font(path)
    name = f._review_cmap[cp]
    scale = size / f['head'].unitsPerEm
    advance = f['hmtx'][name][0]
    ctx.save()
    ctx.translate(x + (width - advance * scale) / 2, baseline)
    ctx.scale(scale, -scale)
    f._review_glyphs[name].draw(CairoPen(f._review_glyphs, ctx))
    ctx.fill()
    ctx.restore()


def details(path, cp):
    f = font(path)
    name = f._review_cmap[cp]
    pen = BoundsPen(f._review_glyphs)
    f._review_glyphs[name].draw(pen)
    return {'font': Path(path).name, 'glyph': name, 'advance': f['hmtx'][name][0],
            'upem': f['head'].unitsPerEm, 'bounds': pen.bounds,
            'contexts': [{'text': text, 'run': shaper(path).shape(text)} for text in contexts(cp)]}


def render(cp, fonts, refs, output, context_index=None, baseline_labels=False):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1120, 1280)
    ctx = cairo.Context(surface)
    ctx.set_source_rgb(1, 1, 1)
    ctx.paint()
    ctx.set_source_rgb(.12, .12, .12)
    labels = [(20, 12, f'U+{cp:04X}  {ud.name(chr(cp), "PROJECT PRIVATE USE")}', 19),
              (20, 43, f'Category {ud.category(chr(cp))} | common em scale | direct outline + shaped/native-size context', 14)]
    if not baseline_labels:
        labels[1] = (20, 43, f'Category {ud.category(chr(cp))} | netfyr 64 px/em | direct outline + shaped/native-size context', 14)
    if context_index is not None:
        labels[1] = (20, 43, f'Shaped context {context_index + 1}: {contexts(cp)[context_index]!r} | netfyr 64 px/em', 14)
    for column, title in enumerate(['Sans upright', 'Sans italic', 'Mono upright', 'Mono italic']):
        labels.append((110 + 250 * column, 75, title, 15))
    cases = []
    for row, (weight, _) in enumerate(WEIGHTS):
        top = 100 + row * 128
        labels.append((15, top + 32, str(weight), 17))
        for column in range(4):
            path = fonts[row * 4 + column]
            left = 95 + column * 250
            ctx.save()
            ctx.set_source_rgb(.9, .9, .9)
            ctx.move_to(left, top + 82)
            ctx.line_to(left + 240, top + 82)
            ctx.stroke()
            ctx.restore()
            if context_index is None:
                draw_direct(ctx, path, cp, left, top + 82, 64, 225)
            else:
                draw_run(ctx, path, contexts(cp)[context_index], left, top + 82, 64, 225)
            text = contexts(cp)[0 if context_index is None or baseline_labels else context_index]
            draw_run(ctx, path, text, left, top + 117, 20, 225)
            cases.append(details(path, cp))
    labels.append((20, 1004, 'References: 76 px/em; netfyr: 64 px/em; independent widths; actual cmap, no fallback', 14))
    if baseline_labels and context_index is None:
        labels[-1] = (20, 1004, 'Reference outlines at the same em scale; independent widths; no fallback or copied reference paths', 14)
    for i, (name, path) in enumerate(refs):
        left = 20 + i * 365
        labels.append((left, 1035, name, 16))
        if context_index is None:
            draw_direct(ctx, path, cp, left, 1140, 76, 340)
        else:
            draw_run(ctx, path, contexts(cp)[context_index], left, 1140, 76, 340)
        draw_run(ctx, path, contexts(cp)[0 if context_index is None or baseline_labels else context_index], left, 1182, 22, 340)
    if not refs:
        labels.append((20, 1050, 'Project symbol: compare with flame SVG or documented Powerline geometry, not arbitrary PUA fonts.', 14))
    labels.append((20, 1222, 'For marks, review additional a/i/o contexts in metadata; spanning marks use two letters.', 14))
    labels.append((20, 1247, 'Blank controls and Braille U+2800 require semantic/advance checks. A blank is not automatically a defect.', 14))
    suffix = '' if context_index is None else f'-context-{context_index + 1}'
    path = output / 'proofs' / f'U{cp:04X}{suffix}.png'
    surface.write_to_png(str(path))
    im = Image.open(path).convert('RGB')
    draw = ImageDraw.Draw(im)
    for x, y, text, size in labels:
        label_font = ImageFont.truetype('/usr/share/fonts/noto/NotoSans-Regular.ttf', size)
        draw.text((x, y), text, font=label_font, fill='#333333')
    im.save(path)
    return cases


def main():
    global EXTRA_CONTEXTS_ENABLED
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonts', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--partition', choices=['latin', 'language', 'symbols'])
    parser.add_argument('--codepoints', help='Comma-separated hexadecimal code points')
    parser.add_argument('--contexts-only', action='store_true', help='Add contextual proofs without changing existing individual evidence')
    parser.add_argument('--extra-contexts', action='store_true', help='Include repaired side attachments and adjoining rhotic letters')
    parser.add_argument('--baseline-evidence-labels', action='store_true', help='Reproduce the documented labels and small-context errata in original 0.506 evidence')
    args = parser.parse_args()
    EXTRA_CONTEXTS_ENABLED = args.extra_contexts
    output = args.output.resolve()
    (output / 'proofs').mkdir(parents=True, exist_ok=True)
    (output / 'cases').mkdir(exist_ok=True)
    paths = []
    for weight, style in WEIGHTS:
        for family, italic in [('sans', False), ('sans', True), ('mono', False), ('mono', True)]:
            name = ('Italic' if weight == 400 else style + 'Italic') if italic else style
            paths.append(str((args.fonts / f'netfyr{family}-{name}.ttf').resolve()))
    cmap = set(font(paths[0])._review_cmap)
    if any(set(font(path)._review_cmap) != cmap for path in paths):
        raise ValueError('Style coverage differs')
    wanted = set(int(v, 16) for v in args.codepoints.split(',')) if args.codepoints else cmap
    cps = sorted(cp for cp in wanted if not args.partition or partition(cp) == args.partition)
    identity = {'fonts': {Path(path).name: sha(path) for path in paths},
                'references': {name: {'path': path, 'sha256': sha(path), 'version': font(path)['name'].getDebugName(5)} for name, path in REFERENCES}}
    (output / 'inputs.json').write_text(json.dumps(identity, indent=2) + '\n')
    for index, cp in enumerate(cps, 1):
        candidates = REFERENCES
        if cp >= 0x2100:
            candidates = [REFERENCES[i] for i in [4, 2, 3, 5, 7, 0, 1, 6]]
        refs = [(name, path) for name, path in candidates if cp in font(path)._review_cmap][:3]
        if args.contexts_only:
            if not ud.category(chr(cp)).startswith('M') and not (args.extra_contexts and cp in EXTRA_CONTEXTS):
                continue
            record_path = output / 'cases' / f'U{cp:04X}.json'
            record = json.loads(record_path.read_text())
            record['context_proofs'] = []
            record['cases'] = [details(path, cp) for path in paths]
            for context_index in range(len(contexts(cp))):
                render(cp, paths, refs, output, context_index, args.baseline_evidence_labels)
                relative = f'proofs/U{cp:04X}-context-{context_index + 1}.png'
                record['context_proofs'].append({'text': contexts(cp)[context_index], 'proof': relative, 'sha256': sha(output / relative)})
            record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
            continue
        cases = render(cp, paths, refs, output, baseline_labels=args.baseline_evidence_labels)
        record = {'codepoint': cp, 'code': f'U+{cp:04X}', 'name': ud.name(chr(cp), 'PROJECT PRIVATE USE'),
                  'category': ud.category(chr(cp)), 'partition': partition(cp),
                  'references': [name for name, _ in refs], 'proof': f'proofs/U{cp:04X}.png',
                  'proof_sha256': sha(output / 'proofs' / f'U{cp:04X}.png'),
                  'rendered_styles': len(cases), 'cases': cases, 'visual_review': 'pending'}
        (output / 'cases' / f'U{cp:04X}.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        if index % 50 == 0:
            print(f'Rendered {index}/{len(cps)} {args.partition or "characters"}', flush=True)
    print(f'Complete: {len(cps)} individual proofs at {output}', flush=True)


if __name__ == '__main__':
    main()
