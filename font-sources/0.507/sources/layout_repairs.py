"""Move explicitly reviewed right-side marks without rebuilding other features."""
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib.tables import otTables

RIGHT_MARKS = (0x0315, 0x031A, 0x0358)
EXTRA_REPAIRS = []


def register_layout_repair(callback):
    EXTRA_REPAIRS.append(callback)
    return callback


def apply(font):
    cmap = font.getBestCmap()
    targets = {cmap[cp] for cp in RIGHT_MARKS}
    above = cmap[0x0300]
    horn = cmap[0x031B]
    changes = []
    for coverage in font['GDEF'].table.MarkGlyphSetsDef.Coverage:
        if above in coverage.glyphs and horn not in coverage.glyphs:
            removed = targets.intersection(coverage.glyphs)
            if removed:
                coverage.glyphs = [name for name in coverage.glyphs if name not in targets]
                changes.append({'table': 'GDEF', 'operation': 'remove right marks from above-mark filtering', 'glyphs': sorted(removed)})
    for lookup in font['GSUB'].table.LookupList.Lookup:
        if lookup.LookupType != 6:
            continue
        for subtable in lookup.SubTable:
            for key in ('BacktrackClassDef', 'InputClassDef', 'LookAheadClassDef'):
                classes = getattr(subtable, key, None)
                if classes is not None and above in classes.classDefs:
                    for target in targets:
                        if classes.classDefs.get(target) == classes.classDefs[above]:
                            del classes.classDefs[target]
                            changes.append({'table': 'GSUB', 'operation': 'exclude right mark from above-accent context', 'glyph': target, 'class_definition': key})
    glyphs = font.getGlyphSet()
    target_lows = []
    for name in targets:
        pen = BoundsPen(glyphs)
        glyphs[name].draw(pen)
        target_lows.append(pen.bounds[1])
    mark_low = min(target_lows)
    for lookup in font['GPOS'].table.LookupList.Lookup:
        for subtable in lookup.SubTable:
            if lookup.LookupType == 4 and targets.intersection(subtable.MarkCoverage.glyphs):
                new_class = subtable.ClassCount
                subtable.ClassCount += 1
                for name, base in zip(subtable.BaseCoverage.glyphs, subtable.BaseArray.BaseRecord):
                    pen = BoundsPen(glyphs)
                    glyphs[name].draw(pen)
                    if pen.bounds is None:
                        base.BaseAnchor.append(None)
                        continue
                    _, _, xmax, ymax = pen.bounds
                    anchor = otTables.Anchor()
                    anchor.Format = 1
                    anchor.XCoordinate = round(xmax + max(14, font['OS/2'].usWeightClass / 25))
                    anchor.YCoordinate = round(ymax + max(28, font['OS/2'].usWeightClass / 20) - mark_low)
                    base.BaseAnchor.append(anchor)
                for name, mark in zip(subtable.MarkCoverage.glyphs, subtable.MarkArray.MarkRecord):
                    if name in targets:
                        mark.Class = new_class
                changes.append({'table': 'GPOS', 'operation': 'new dedicated right-side mark class', 'glyphs': sorted(targets), 'class': new_class})
            elif lookup.LookupType == 6:
                for coverage_key, array_key, record_key, count_key in [
                    ('Mark1Coverage', 'Mark1Array', 'MarkRecord', 'MarkCount'),
                    ('Mark2Coverage', 'Mark2Array', 'Mark2Record', 'Mark2Count')]:
                    coverage = getattr(subtable, coverage_key, None)
                    if coverage is None or not targets.intersection(coverage.glyphs):
                        continue
                    array = getattr(subtable, array_key)
                    keep = [(name, record) for name, record in zip(coverage.glyphs, getattr(array, record_key)) if name not in targets]
                    coverage.glyphs = [name for name, _ in keep]
                    setattr(array, record_key, [record for _, record in keep])
                    setattr(array, count_key, len(keep))
                    changes.append({'table': 'GPOS', 'operation': 'remove right marks from vertical stacking', 'coverage': coverage_key})
    if not changes:
        raise ValueError('Right-side mark layout repair did not apply')
    codes = {f'U+{cp:04X}' for cp in RIGHT_MARKS}
    for callback in EXTRA_REPAIRS:
        result = callback(font)
        if not isinstance(result, dict) or not {'codepoints', 'changes'} <= result.keys():
            raise ValueError('A layout repair must declare its character targets and operations')
        codes.update(result['codepoints'])
        changes.extend(result['changes'])
    return {'codepoints': sorted(codes), 'changes': changes}
