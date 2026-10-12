"""Individually reviewed Latin corrections using this family's own outlines."""
import unicodedata as ud

from compiled_repairs import (
    repair, record, corrected_record, combine, glyph_name, slant_matrix,
    bounds, transformed, expand_stroke,
    composition_run, bounds_in_x_range, path_recording, clip_rectangle,
)
from layout_repairs import register_layout_repair
from fontTools.ttLib.tables import otTables
from fontTools.pens.svgPathPen import SVGPathPen

def canonical(font, cp, stem):
    sequence = ud.normalize('NFD', chr(cp))
    run = composition_run(font, sequence[0] + '\u034f' + sequence[1:])
    parts = []
    cursor = 0
    for item in run:
        name = item['glyph']
        outline = corrected_record(font, name, stem)
        matrix = slant_matrix(font, name)
        if matrix:
            outline = transformed(outline, matrix)
        parts.append(transformed(outline, (1, 0, 0, 1, cursor + item['x'], item['y'])))
        cursor += item['advance']
    result = combine(*parts)
    matrix = slant_matrix(font, cp, inverse=True)
    return transformed(result, matrix) if matrix else result


CANONICAL_REPAIRS = (
    0x00EF, 0x010F, 0x0123, 0x013D, 0x013E, 0x0150, 0x0151,
    0x0165, 0x0170, 0x0171, 0x01EE, 0x01EF, 0x01FA, 0x01FB,
    0x0200, 0x0201, 0x0204, 0x0205, 0x0208, 0x0209, 0x020B,
    0x020C, 0x020D, 0x0210, 0x0211, 0x0214, 0x0215,
    0x1E05, 0x1E0D, 0x1E28, 0x1E29, 0x1E2F, 0x1E37, 0x1E39,
    0x1E3D, 0x1E4E, 0x1E4F, 0x1E62, 0x1E64, 0x1E65, 0x1E68,
    0x1E7E, 0x1E7F, 0x1E9B, 0x1EA1, 0x1EA2, 0x1EA3,
    0x1EA4, 0x1EA5, 0x1EA6, 0x1EA7, 0x1EA8, 0x1EA9,
    0x1EAA, 0x1EAB, 0x1EAD, 0x1EAE, 0x1EAF, 0x1EB0,
    0x1EB1, 0x1EB2, 0x1EB3, 0x1EB7, 0x1EB9, 0x1EBA,
    0x1EBB, 0x1EBE, 0x1EBF, 0x1EC0, 0x1EC1, 0x1EC2,
    0x1EC3, 0x1EC4, 0x1EC5, 0x1EC7, 0x1EC8, 0x1EC9,
    0x1ECC, 0x1ECD, 0x1ECE, 0x1ECF, 0x1ED0, 0x1ED1,
    0x1ED2, 0x1ED3, 0x1ED4, 0x1ED5, 0x1ED6, 0x1ED7,
    0x1ED8, 0x1ED9, 0x1EDE, 0x1EDF, 0x1EE2, 0x1EE3,
    0x1EE4, 0x1EE5, 0x1EE6, 0x1EE7, 0x1EEC, 0x1EED,
    0x1EF0, 0x1EF1, 0x1EF6, 0x1EF7,
)
for _cp in CANONICAL_REPAIRS:
    repair(_cp)(lambda font, stem, cp=_cp: canonical(font, cp, stem))


@repair('caron.side')
def side_caron(font, stem):
    # Separate the two diagonals at the heavy end without narrowing their gap.
    width = min(stem * .58, 48)
    return expand_stroke('M38 157L4 29', width)


@repair('cedilla.g')
def g_comma_above(font, stem):
    return transformed(record(font, 'cedilla.g'), (1, 0, 0, 1, 0, max(0, stem - 90) * .48))


@repair('mark.032D.narrow')
def narrow_below_circumflex(font, stem):
    return expand_stroke('M-93 -142L0 -38L93 -142', min(stem * .78, 82))


def original_base(font, cp, base, stem):
    outline = corrected_record(font, base, stem)
    old = bounds(record(font, cp))
    bb = bounds(outline)
    dx = (old[0] + old[2] - bb[0] - bb[2]) / 2
    return transformed(outline, (1, 0, 0, 1, dx, 0))


def bar_across(font, cp, base, stem, y, slope=0, left=24, right=24, factor=.8):
    outline = original_base(font, cp, base, stem)
    x0, _, x1, _ = bounds(outline)
    bar = expand_stroke(f'M{x0-left} {y-slope/2}L{x1+right} {y+slope/2}', stem * factor)
    return combine(outline, bar)


BAR_REPAIRS = {
    0x0141: ('L', 365, 205), 0x0180: ('b', 600, 0),
    0x01E4: ('G', 270, 0), 0x01E5: ('g', -55, 0),
    0x023A: ('A', 350, 260), 0x023B: ('C', 380, 240),
    0x023C: ('c', 280, 230), 0x023D: ('L', 365, 0),
    0x023E: ('T', 375, 250), 0x0243: ('B', 365, 0),
    0x0244: ('U', 365, 0), 0x0246: ('E', 350, 240),
    0x0247: ('e', 265, 230), 0x0248: ('J', 365, 0),
    0x024C: ('R', 360, 0), 0x024E: ('Y', 515, 0),
    0x024F: ('y', 365, 0), 0x1E9C: (0x017F, 350, 250),
    0x1E9D: (0x017F, 540, 0),
}
for _cp, (_base, _y, _slope) in BAR_REPAIRS.items():
    if isinstance(_base, str):
        _base = ord(_base)
    repair(_cp)(lambda font, stem, cp=_cp, base=_base, y=_y, slope=_slope:
                bar_across(font, cp, base, stem, y, slope))


def full_height_slash(font, cp, base, stem):
    outline = original_base(font, cp, ord(base), stem)
    x0, y0, x1, y1 = bounds(outline)
    inset = (x1 - x0) * .1
    slash = expand_stroke(f'M{x0+inset} {y0-40}L{x1-inset} {y1+40}', min(stem * .68, 112))
    return combine(outline, slash)


for _cp, _base in [(0x023A, 'A'), (0x023B, 'C'), (0x023C, 'c'),
                   (0x023E, 'T'), (0x0246, 'E'), (0x0247, 'e')]:
    repair(_cp)(lambda font, stem, cp=_cp, base=_base: full_height_slash(font, cp, base, stem))


@repair(0x0243)
def b_lower_stroke(font, stem):
    outline = original_base(font, 0x0243, ord('B'), stem)
    bb = bounds(outline)
    stroke = expand_stroke(f'M{bb[0]-55} 220H{bb[0]+stem+120}', stem * .72)
    return combine(outline, stroke)


def attachment_anchor(font, key, x, y):
    matrix = slant_matrix(font, key)
    if matrix:
        x = matrix[0] * x + matrix[2] * y + matrix[4]
    anchor = otTables.Anchor()
    anchor.Format = 1
    anchor.XCoordinate = round(x)
    anchor.YCoordinate = round(y)
    return anchor


@register_layout_repair
def latin_attachment_repairs(font):
    from compiled_repairs import WEIGHTS
    stem = WEIGHTS[font['OS/2'].usWeightClass]
    cmap = font.getBestCmap()
    changes = []
    affected_mark_names = {cmap[0x0327]}
    stacking = {cmap[cp] for cp in (0x0301, 0x0302, 0x0303, 0x0306, 0x030A)}
    for lookup in font['GPOS'].table.LookupList.Lookup:
        for subtable in lookup.SubTable:
            if lookup.LookupType == 6 and stacking.intersection(subtable.Mark2Coverage.glyphs):
                incoming = {}
                for name, item in zip(subtable.Mark1Coverage.glyphs, subtable.Mark1Array.MarkRecord):
                    incoming.setdefault(item.Class, []).append(name)
                for name, item in zip(subtable.Mark2Coverage.glyphs, subtable.Mark2Array.Mark2Record):
                    if name not in stacking:
                        continue
                    parent = corrected_record(font, name, stem)
                    for klass, old in enumerate(item.Mark2Anchor):
                        if old is None:
                            continue
                        matrix = slant_matrix(font, name, inverse=True)
                        x, y = old.XCoordinate, old.YCoordinate
                        if matrix:
                            x += matrix[2] * y + matrix[4]
                        required = y
                        for child_name in incoming[klass]:
                            child = corrected_record(font, child_name, stem)
                            bb = bounds(child)
                            if bb is None:
                                continue
                            rb = bounds_in_x_range(parent, x + bb[0] - 12, x + bb[2] + 12)
                            if rb:
                                required = max(required, rb[3] - bb[1] + 16)
                        if required > y + .5:
                            affected_mark_names.update(incoming[klass])
                            item.Mark2Anchor[klass] = attachment_anchor(font, name, x, required)
                            changes.append({'mark': name, 'class': klass, 'before': [old.XCoordinate, old.YCoordinate],
                                            'after': [item.Mark2Anchor[klass].XCoordinate, item.Mark2Anchor[klass].YCoordinate]})
            elif lookup.LookupType == 4 and cmap[0x0327] in subtable.MarkCoverage.glyphs:
                mark_index = subtable.MarkCoverage.glyphs.index(cmap[0x0327])
                klass = subtable.MarkArray.MarkRecord[mark_index].Class
                # Split only cedilla attachment; other below signs keep their class.
                new_class = subtable.ClassCount
                subtable.ClassCount += 1
                subtable.MarkArray.MarkRecord[mark_index].Class = new_class
                for name, item in zip(subtable.BaseCoverage.glyphs, subtable.BaseArray.BaseRecord):
                    old = item.BaseAnchor[klass]
                    anchor = old
                    if name in (cmap[ord('H')], cmap[ord('h')]):
                        base = record(font, name)
                        edges = sorted({point[0] for _, args in base.value for point in args
                                        if point is not None and abs(point[1]) < 1.1})
                        if len(edges) < 2:
                            raise ValueError('Missing H/h left baseline stem edges')
                        x = (edges[0] + edges[1]) / 2
                        y = old.YCoordinate
                        anchor = attachment_anchor(font, name, x, y)
                        changes.append({'base': name, 'mark': cmap[0x0327], 'before': [old.XCoordinate, old.YCoordinate],
                                        'after': [anchor.XCoordinate, anchor.YCoordinate]})
                    item.BaseAnchor.append(anchor)
                caron_name = cmap[0x030C]
                if caron_name in subtable.MarkCoverage.glyphs:
                    mark_index = subtable.MarkCoverage.glyphs.index(caron_name)
                    klass = subtable.MarkArray.MarkRecord[mark_index].Class
                    new_class = subtable.ClassCount
                    subtable.ClassCount += 1
                    subtable.MarkArray.MarkRecord[mark_index].Class = new_class
                    caron = corrected_record(font, caron_name, stem)
                    minimum = bounds(caron)[1]
                    for name, item in zip(subtable.BaseCoverage.glyphs, subtable.BaseArray.BaseRecord):
                        old = item.BaseAnchor[klass]
                        anchor = old
                        if name in (cmap[0x01B7], cmap[0x0292]):
                            bb = bounds(corrected_record(font, name, stem))
                            y = max(old.YCoordinate, bb[3] - minimum + 16)
                            x = old.XCoordinate
                            matrix = slant_matrix(font, name, inverse=True)
                            if matrix:
                                x += matrix[2] * old.YCoordinate + matrix[4]
                            anchor = attachment_anchor(font, name, x, y)
                            if anchor.YCoordinate != old.YCoordinate:
                                affected_mark_names.add(caron_name)
                                changes.append({'base': name, 'mark': caron_name,
                                                'before': [old.XCoordinate, old.YCoordinate],
                                                'after': [anchor.XCoordinate, anchor.YCoordinate]})
                        item.BaseAnchor.append(anchor)
                dot_name = cmap[0x0307]
                if dot_name in subtable.MarkCoverage.glyphs:
                    mark_index = subtable.MarkCoverage.glyphs.index(dot_name)
                    klass = subtable.MarkArray.MarkRecord[mark_index].Class
                    new_class = subtable.ClassCount
                    subtable.ClassCount += 1
                    subtable.MarkArray.MarkRecord[mark_index].Class = new_class
                    minimum = bounds(corrected_record(font, dot_name, stem))[1]
                    for name, item in zip(subtable.BaseCoverage.glyphs, subtable.BaseArray.BaseRecord):
                        old = item.BaseAnchor[klass]
                        anchor = old
                        if name == cmap[0x017F]:
                            bb = bounds(corrected_record(font, name, stem))
                            y = max(old.YCoordinate, bb[3] - minimum + 16)
                            x = old.XCoordinate
                            matrix = slant_matrix(font, name, inverse=True)
                            if matrix:
                                x += matrix[2] * old.YCoordinate + matrix[4]
                            anchor = attachment_anchor(font, name, x, y)
                            if anchor.YCoordinate != old.YCoordinate:
                                affected_mark_names.add(dot_name)
                                changes.append({'base': name, 'mark': dot_name,
                                                'before': [old.XCoordinate, old.YCoordinate],
                                                'after': [anchor.XCoordinate, anchor.YCoordinate]})
                        item.BaseAnchor.append(anchor)
                side_name = 'caron.side'
                if side_name in subtable.MarkCoverage.glyphs:
                    mark_index = subtable.MarkCoverage.glyphs.index(side_name)
                    klass = subtable.MarkArray.MarkRecord[mark_index].Class
                    new_class = subtable.ClassCount
                    subtable.ClassCount += 1
                    subtable.MarkArray.MarkRecord[mark_index].Class = new_class
                    side = corrected_record(font, side_name, stem)
                    side_bounds = bounds(side)
                    for name, item in zip(subtable.BaseCoverage.glyphs, subtable.BaseArray.BaseRecord):
                        old = item.BaseAnchor[klass]
                        anchor = old
                        if name in {cmap[ord(c)] for c in 'dltL'}:
                            base = record(font, name)
                            x, y = old.XCoordinate, old.YCoordinate
                            matrix = slant_matrix(font, name, inverse=True)
                            if matrix:
                                x += matrix[2] * y + matrix[4]
                            swapped = transformed(base, (0, 1, 1, 0, 0, 0))
                            region = bounds_in_x_range(swapped, y + side_bounds[1] - 8, y + side_bounds[3] + 8)
                            if region:
                                x = max(x, region[3] - side_bounds[0] + 16)
                                anchor = attachment_anchor(font, name, x, y)
                                if anchor.XCoordinate != old.XCoordinate:
                                    affected_mark_names.add(cmap[0x030C])
                                    changes.append({'base': name, 'mark': side_name,
                                                    'before': [old.XCoordinate, old.YCoordinate],
                                                    'after': [anchor.XCoordinate, anchor.YCoordinate]})
                        item.BaseAnchor.append(anchor)
    affected = set(CANONICAL_REPAIRS) | {cp for cp, name in cmap.items() if name in affected_mark_names}
    return {'codepoints': [f'U+{cp:04X}' for cp in sorted(affected)], 'changes': changes}


def authored_path(font, cp, stem, drawing):
    return authored_strokes(font, cp, stem, [(drawing, stem)])


def authored_strokes(font, cp, stem, drawings):
    centers = [(path_recording(drawing), width) for drawing, width in drawings]
    bb = bounds(combine(*(outline for outline, _ in centers)))
    target = bounds(record(font, cp))
    sx = (target[2] - target[0] - stem) / (bb[2] - bb[0])
    matrix = (sx, 0, 0, 1, target[0] + stem/2 - bb[0] * sx, 0)
    parts = []
    for outline, width in centers:
        pen = SVGPathPen(None)
        transformed(outline, matrix).replay(pen)
        parts.append(expand_stroke(pen.getCommands(), width))
    return combine(*parts)


# Shared rounded anatomies are assembled before fitting the final glyph width.
PATH_REPAIRS = {
    0x0195: 'M100 0V700M100 320C100 590 320 570 320 330V140C320 -35 555 -35 555 140V410',
    0x01F6: 'M100 0V700M100 360H320M320 700V140C320 -35 555 -35 555 140V410',
    0x019B: 'M125 690C275 700 280 540 325 440L520 35M325 440L100 35M160 575L375 690',
    0x01A6: 'M130 0V700M130 430C130 605 485 610 485 430C485 250 230 285 230 285L525 0',
    0x01A7: 'M140 640C355 795 555 670 490 495C465 425 420 390 320 350C55 240 125 -95 485 85',
    0x01AA: 'M460 -155C335 -225 265 -115 265 70V460C265 705 145 780 45 660M265 565C115 470 80 675 265 650',
    0x01B1: 'M95 665H140C-70 420 130 0 320 0C510 0 710 420 500 665H545',
    0x01BA: 'M135 485H510L300 260C580 290 610 -175 300 -175C185 -175 125 -225 155 -280C180 -335 260 -310 275 -270',
    0x0220: 'M135 0V700M135 430C135 735 500 735 500 430V-220',
    0x0238: 'M320 700V0M320 430C10 650 10 -125 320 90M320 430C630 650 630 -125 320 90',
    0x0239: 'M320 520V-220M320 440C10 650 10 -125 320 85M320 440C630 650 630 -125 320 85',
    0x024A: 'M495 665V-80Q495 -230 610 -140M495 545C440 695 135 740 105 400C75 30 420 -90 495 190',
    0x1E9F: 'M455 660C370 780 170 745 245 615C300 520 535 435 515 230C490 -60 110 -60 105 230C100 380 260 500 405 425',
    0x1EFC: 'M415 655C230 570 100 450 115 245C130 -55 505 -50 515 220C520 390 365 470 240 415',
    0x1EFD: 'M415 485C230 430 100 340 115 180C130 -40 505 -38 515 165C520 290 365 345 240 307',
    0x1EFE: 'M105 665L320 290L535 665M535 665L290 140C175 -90 70 15 135 130C180 210 255 215 330 215',
    0x1EFF: 'M105 485L320 110L535 485M535 485L290 -40C175 -270 70 -165 135 -50C180 30 255 35 330 35',
}
for _cp, _drawing in PATH_REPAIRS.items():
    repair(_cp)(lambda font, stem, cp=_cp, drawing=_drawing: authored_path(font, cp, stem, drawing))


@repair(0x01AA)
def reversed_esh_loop(font, stem):
    main = path_recording('M450 -155C335 -225 265 -115 265 70V650')
    loop = path_recording('M265 650C265 790 45 790 45 650C45 510 265 510 265 650Z')
    bb = bounds(combine(main, loop))
    target = bounds(record(font, 0x01AA))
    sx = (target[2] - target[0] - stem) / (bb[2] - bb[0])
    matrix = (sx, 0, 0, 1, target[0] + stem / 2 - bb[0] * sx, 0)
    parts = []
    for outline, width in [(main, stem), (loop, min(stem * .72, 96))]:
        pen = SVGPathPen(None)
        transformed(outline, matrix).replay(pen)
        parts.append(expand_stroke(pen.getCommands(), width))
    return combine(*parts)


@repair(0x01BA)
def ezh_curled_tail(font, stem):
    main = path_recording('M135 485H510L300 260C580 290 610 -135 300 -135')
    tail = path_recording('M300 -135C100 -135 110 -340 275 -340C380 -340 415 -260 355 -250')
    bb = bounds(combine(main, tail))
    target = bounds(record(font, 0x01BA))
    sx = (target[2] - target[0] - stem) / (bb[2] - bb[0])
    matrix = (sx, 0, 0, 1, target[0] + stem / 2 - bb[0] * sx, 0)
    parts = []
    for outline, width in [(main, stem), (tail, min(stem * .7, 80))]:
        pen = SVGPathPen(None)
        transformed(outline, matrix).replay(pen)
        parts.append(expand_stroke(pen.getCommands(), width))
    return combine(*parts)


def y_lower_loop(font, cp, stem, height):
    shift = height - 665
    return authored_strokes(font, cp, stem, [
        (f'M105 {height}L320 {290+shift}L535 {height}M535 {height}L225 {40+shift}', stem),
        (f'M225 {40+shift}C20 {-210+shift} -100 {20+shift} 35 {75+shift}C95 {120+shift} 170 {65+shift} 225 {40+shift}Z', min(stem*.45, 52)),
    ])


@repair(0x1EFE)
def capital_y_loop(font, stem):
    return y_lower_loop(font, 0x1EFE, stem, 665)


@repair(0x1EFF)
def small_y_loop(font, stem):
    return y_lower_loop(font, 0x1EFF, stem, 485)


@repair(0x01A8)
def small_tone_two(font, stem):
    return fit_to_original_width(font, 0x01A8, transformed(corrected_record(font, 0x01A7, stem), (1, 0, 0, 520/700, 0, 0)))


def fit_to_original_width(font, cp, outline):
    bb = bounds(outline)
    original = bounds(record(font, cp))
    sx = (original[2] - original[0]) / (bb[2] - bb[0])
    return transformed(outline, (sx, 0, 0, 1, original[0] - sx * bb[0], 0))


@repair(0x0184)
def capital_tone_six(font, stem):
    return fit_to_original_width(font, 0x0184, record(font, ord('b')))


@repair(0x0185)
def small_tone_six(font, stem):
    return fit_to_original_width(font, 0x0185, record(font, ord('b')))


@repair(0x018D)
def turned_delta(font, stem):
    return fit_to_original_width(font, 0x018D, transformed(corrected_record(font, 0x1E9F, stem), (-1, 0, 0, -1, 640, 520)))


@repair(0x019C)
def rounded_turned_m(font, stem):
    return authored_path(font, 0x019C, stem,
                         'M110 700V205C110 -40 325 -40 325 205V700M325 205C325 -40 540 -40 540 205V700')


@repair(0x01BE)
def inverted_glottal_stroke(font, stem):
    return bar_across(font, 0x01BE, 0x0296, stem, 470, 0, left=15, right=15)


def hooked_capital(font, cp, base, stem):
    outline = original_base(font, cp, ord(base), stem)
    bb = bounds(outline)
    width = min(stem * .85, 104)
    x = bb[0] + stem / 2
    hook = expand_stroke(f'M{x} {bb[3]-65}V{bb[3]+10}C{x} {bb[3]+140} {x-150} {bb[3]+140} {x-150} {bb[3]+20}', width)
    return combine(outline, hook)


for _cp, _base in [(0x0181, 'B'), (0x018A, 'D'), (0x01A4, 'P')]:
    repair(_cp)(lambda font, stem, cp=_cp, base=_base: hooked_capital(font, cp, base, stem))


def hooked_terminal(font, cp, base, stem, attachment='right-top'):
    outline = original_base(font, cp, ord(base), stem)
    x0, y0, x1, y1 = bounds(outline)
    width = min(stem * .82, 96)
    x = x1 - stem * .42
    if attachment == 'right-top':
        drawing = f'M{x-35} {y1-60}C{x+135} {y1+10} {x+155} {y1+160} {x+25} {y1+160}'
    elif attachment == 'right-down':
        drawing = f'M{x-25} {y1-10}C{x+145} {y1+20} {x+150} {y1-120} {x+100} {y1-150}'
    elif attachment == 'left-down':
        x = x0 + stem * .4
        drawing = f'M{x+50} {y1-35}C{x-140} {y1+70} {x-160} {y1-100} {x-115} {y1-145}'
    return combine(outline, expand_stroke(drawing, width))


for _cp, _base, _attachment in [
    (0x0187, 'C', 'right-top'), (0x0188, 'c', 'right-top'),
    (0x0193, 'G', 'right-top'), (0x0198, 'K', 'right-down'),
    (0x01AC, 'T', 'left-down'),
    (0x01B3, 'Y', 'right-down'), (0x01B4, 'y', 'right-down'),
]:
    repair(_cp)(lambda font, stem, cp=_cp, base=_base, attachment=_attachment:
                hooked_terminal(font, cp, base, stem, attachment))


@repair(0x0199)
def small_k_hook(font, stem):
    base = original_base(font, 0x0199, ord('k'), stem)
    bb = bounds(base)
    x = bb[0] + stem / 2
    hook = expand_stroke(f'M{x} {bb[3]-70}V{bb[3]-10}C{x} {bb[3]+130} {x+185} {bb[3]+130} {x+185} {bb[3]+10}', min(stem*.82, 96))
    return combine(base, hook)


@repair(0x01A5)
def small_p_hook(font, stem):
    base = original_base(font, 0x01A5, ord('p'), stem)
    x0, _, _, _ = bounds(base)
    x = x0 + stem / 2
    hook = expand_stroke(f'M{x} 430V625C{x} 780 {x+160} 775 {x+160} 650', min(stem, 110))
    return combine(base, hook)


@repair(0x01AD)
def small_t_hook(font, stem):
    base = original_base(font, 0x01AD, ord('t'), stem)
    bb = bounds(base)
    x = (bb[0] + bb[2]) / 2 - stem * .25
    hook = expand_stroke(f'M{x} 580V650C{x} 825 {x+180} 825 {x+180} 680', min(stem*.82, 90))
    return combine(base, hook)


def curled_foot(font, cp, base, stem, loop=False, direction=1, at_right=True):
    outline = original_base(font, cp, ord(base), stem)
    bb = bounds(outline)
    if cp == 0x0240:
        cut_y = 150
        outline = clip_rectangle(outline, bb[0] - 100, cut_y, bb[2] + 100, bb[3] + 100)
        section = bounds_in_x_range(transformed(outline, (0, 1, 1, 0, 0, 0)), cut_y, cut_y + 20)
        x = (section[1] + section[3]) / 2
        swash = expand_stroke(f'M{x} {cut_y+20}V-65Q{x} -230 {x+150} -185', min(stem * .87, 108))
        return combine(outline, swash)
    x = bb[2] - stem * .4 if at_right else bb[0] + stem * .4
    width = min(stem * .87, 108)
    if loop:
        drawing = f'M{x} 65C{x+direction*225} 75 {x+direction*225} -170 {x} -170C{x-direction*65} -170 {x-direction*40} -45 {x} 65Z'
    else:
        drawing = f'M{x} 100V-65Q{x} -230 {x+direction*150} -185'
    return combine(outline, expand_stroke(drawing, width))


for _cp, _base, _loop, _direction, _right in [
    (0x01AB, 't', False, -1, True), (0x0221, 'd', True, 1, True),
    (0x0224, 'Z', False, -1, True), (0x0225, 'z', False, -1, True),
    (0x0234, 'l', True, 1, True), (0x0235, 'n', True, 1, True),
    (0x0236, 't', True, 1, True), (0x023F, 's', False, 1, False),
    (0x0240, 'z', False, 1, False),
]:
    repair(_cp)(lambda font, stem, cp=_cp, base=_base, loop=_loop, direction=_direction, right=_right:
                curled_foot(font, cp, base, stem, loop, direction, right))


def oi(font, cp, stem, capital):
    height = 700 if capital else 520
    base = record(font, ord('O' if capital else 'o'))
    bb = bounds(base)
    compressed = transformed(base, (.66, 0, 0, 1, 0, 0))
    x = bb[2] * .66 - stem * .42
    width = min(stem, 112)
    arch = expand_stroke(f'M{x} 40V{height-95}C{x} {height+90} {x+230} {height+90} {x+230} {height-95}V0', width)
    return fit_to_original_width(font, cp, combine(compressed, arch))


for _cp, _capital in [(0x01A2, True), (0x01A3, False)]:
    repair(_cp)(lambda font, stem, cp=_cp, capital=_capital: oi(font, cp, stem, capital))


@repair(0x1E9A)
def a_right_half_ring(font, stem):
    base = original_base(font, 0x1E9A, ord('a'), stem)
    bb = bounds(base)
    x = bb[2] + 30
    return combine(base, expand_stroke(f'M{x} 600C{x+145} 600 {x+145} 840 {x} 840', min(stem*.65, 72)))


@repair(0x1EFB)
def welsh_double_l(font, stem):
    original = record(font, 0x1EFB)
    bb = bounds(original)
    crossbar = expand_stroke(f'M{bb[0]-14} 615H{bb[2]+14}', stem * .72)
    return combine(original, crossbar)


def spaced_pair(font, cp, left, right, stem):
    left = corrected_record(font, left, stem)
    right = corrected_record(font, right, stem)
    lb, rb = bounds(left), bounds(right)
    advance = font['hmtx'][glyph_name(font, cp)][0]
    margin = 26
    gap = max(22, stem * .20)
    natural = lb[2] - lb[0] + rb[2] - rb[0]
    sx = min(1, (advance - 2 * margin - gap) / natural)
    first_width = (lb[2] - lb[0]) * sx
    left = transformed(left, (sx, 0, 0, 1, margin - sx*lb[0], 0))
    right = transformed(right, (sx, 0, 0, 1, margin + first_width + gap - sx*rb[0], 0))
    return combine(left, right)


PAIR_REPAIRS = {
    0x01C4: (ord('D'), 0x017D), 0x01C5: (ord('D'), 0x017E),
    0x01C6: (ord('d'), 0x017E), 0x01C7: (ord('L'), ord('J')),
    0x01CA: (ord('N'), ord('J')), 0x01CB: (ord('N'), ord('j')),
    0x01CC: (ord('n'), ord('j')), 0x01F1: (ord('D'), ord('Z')),
    0x01F2: (ord('D'), ord('z')), 0x01F3: (ord('d'), ord('z')),
}
for _cp, (_left, _right) in PAIR_REPAIRS.items():
    repair(_cp)(lambda font, stem, cp=_cp, left=_left, right=_right:
                spaced_pair(font, cp, left, right, stem))


# Every canonical alias affected by a shared mark or changed attachment gets
# the same positioned components as native decomposed input.
SHARED_MARK_CLOSURE = {0x0308, 0x0309, 0x030A, 0x030B, 0x030F, 0x0311, 0x0323, 0x0325, 0x0327, 0x032D}
STACKED_MARKS = {0x0301, 0x0302, 0x0303, 0x0306, 0x030A}
BLACK_ONLY_RING_CLOSURE = {0x00C5, 0x00E5, 0x016E, 0x016F, 0x1E98, 0x1E99}
for _cp in list(range(0x00C0, 0x0250)) + list(range(0x1E00, 0x1F00)):
    _sequence = ud.normalize('NFD', chr(_cp))
    if _sequence == chr(_cp):
        continue
    _marks = set(map(ord, _sequence[1:]))
    if _marks.intersection(SHARED_MARK_CLOSURE) or (len(_sequence) > 2 and _marks.intersection(STACKED_MARKS)):
        _weights = {900} if _cp in BLACK_ONLY_RING_CLOSURE else None
        repair(_cp, weights=_weights)(lambda font, stem, cp=_cp: canonical(font, cp, stem))

repair(0x212B, weights={900})(lambda font, stem: canonical(font, 0x212B, stem))
