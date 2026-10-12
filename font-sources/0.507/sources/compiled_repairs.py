"""Apply reviewed, authored corrections to the actual compiled baseline.

Using the compiled outlines preserves the four original upright controls and
their layout anchors. Only explicitly registered glyphs may change.
"""
from pathlib import Path
import copy
import hashlib
import importlib
from io import BytesIO
import json
import sys

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'sources/recipes'))
from outlines import bounds, transformed, expand_stroke, split_contours, path_recording
from curve_boolean import batch, ENGINE_INFO
from repair_geometry import native_boolean, clip_rectangle, bounds_in_x_range
from expansion_design import WEIGHTS, SHEAR, PIVOT
import layout_repairs

REPAIRS = {}
REPAIR_OPTIONS = {}
CONTEXT_DEPENDENCIES = {
    0x0308: ('mark.0308.narrow',),
    0x0311: ('mark.0311.narrow',),
    0x0344: ('mark.0308.narrow',),
}
sys.modules.setdefault('compiled_repairs', sys.modules[__name__])


def repair(cp, *, weights=None, preserve_contours=False):
    def register(function):
        REPAIRS[cp] = function
        REPAIR_OPTIONS[cp] = {'weights': None if weights is None else frozenset(weights),
                              'preserve_contours': preserve_contours}
        return function
    return register


def eligible(font, key):
    weights = REPAIR_OPTIONS[key]['weights']
    return weights is None or font['OS/2'].usWeightClass in weights


def glyph_name(font, key):
    return font.getBestCmap()[key] if isinstance(key, int) else key


def slant_matrix(font, key, inverse=False):
    if not font['post'].italicAngle:
        return None
    name = glyph_name(font, key)
    codes = [cp for cp, mapped in font.getBestCmap().items() if mapped == name]
    if any(0x2500 <= cp <= 0x259F or 0x2800 <= cp <= 0x28FF
           or 0xE0A0 <= cp <= 0xE0D7 or cp in (0xE000, 0xF8FF) for cp in codes):
        return None
    pivot = 0 if font['hmtx'][name][0] == 0 else PIVOT
    shear = -SHEAR if inverse else SHEAR
    return (1, 0, shear, 1, -shear * pivot, 0)


def record(font, cp, upright=True):
    pen = RecordingPen()
    font.getGlyphSet()[glyph_name(font, cp)].draw(pen)
    matrix = slant_matrix(font, cp, inverse=True) if upright else None
    if matrix:
        pen = transformed(pen, matrix)
    return pen


def authored_result(font, key, stem):
    cache = getattr(font, '_repair_results', None)
    if cache is None:
        font._repair_results = cache = {}
        font._repair_stack = set()
    if key not in cache:
        if key in font._repair_stack:
            raise ValueError('Circular repair dependency: ' + str(key))
        font._repair_stack.add(key)
        cache[key] = REPAIRS[key](font, stem)
        font._repair_stack.remove(key)
    return cache[key]


def corrected_record(font, key, stem):
    """Resolve declared parent corrections when composing dependent glyphs."""
    if key not in REPAIRS:
        name = glyph_name(font, key)
        aliases = [candidate for candidate in REPAIRS
                   if eligible(font, candidate) and glyph_name(font, candidate) == name]
        if not aliases:
            return record(font, key)
        key = aliases[0]
    if not eligible(font, key):
        return record(font, key)
    result = authored_result(font, key, stem)
    return result[0] if isinstance(result, tuple) else result


def combine(*parts):
    pen = RecordingPen()
    for part in parts:
        part.replay(pen)
    return pen


def composition_run(font, text):
    """Shape canonical components using the same declared final layout edits."""
    shaper = getattr(font, '_composition_run_shaper', None)
    if shaper is None:
        sys.path.insert(0, str(ROOT / 'sources/validation'))
        from shaping import Shaper
        planned = copy.deepcopy(font)
        layout_repairs.apply(planned)
        data = BytesIO()
        planned.recalcTimestamp = False
        planned.save(data)
        font._composition_run_shaper = shaper = Shaper(data.getvalue())
    return shaper.shape(text)


def stem_edges(pen):
    """Find a straight right stem's two edges at the baseline."""
    points = [point for command, args in pen.value for point in args
              if point is not None and abs(point[1]) < 1.1]
    xs = sorted(set(round(point[0], 3) for point in points))
    if len(xs) < 2:
        raise ValueError('No baseline stem edges')
    return xs[-2:]


@repair(0x0267)
def heng_hook(font, stem):
    base = record(font, 0x0266)
    left, right = stem_edges(base)
    center = (left + right) / 2
    width = right - left
    hook = expand_stroke(
        f'M{center} 165V-60Q{center} -205 {center-125} -185', width)
    return combine(base, hook)


@repair(0x0268)
def dotted_stroked_i(font, stem):
    original = record(font, 0x0268)
    dotted = record(font, ord('i'))
    dot = max(split_contours(dotted), key=lambda part: bounds(part)[3])
    existing = record(font, 0x0131)
    dx = (bounds(existing)[0] + bounds(existing)[2] - bounds(dotted)[0] - bounds(dotted)[2]) / 2
    return combine(original, transformed(dot, (1, 0, 0, 1, dx, 0)))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def update_clipping_extents(paths, results):
    rows = {row['file']: row for row in results}
    for family in ('netfyrsans-', 'netfyrmono-'):
        members = [path for path in paths if path.name.startswith(family)]
        fonts = {path: TTFont(path) for path in members}
        ascent = max(max(font['OS/2'].usWinAscent, font['head'].yMax) for font in fonts.values())
        descent = max(max(font['OS/2'].usWinDescent, -font['head'].yMin) for font in fonts.values())
        for path, font in fonts.items():
            changes = {}
            for attribute, value in (('usWinAscent', ascent), ('usWinDescent', descent)):
                old = getattr(font['OS/2'], attribute)
                if value != old:
                    changes['OS/2.' + attribute] = {'before': old, 'after': value}
                    setattr(font['OS/2'], attribute, value)
            if changes:
                font.recalcTimestamp = False
                font.save(path)
                rows[path.name]['sha256'] = digest(path)
            rows[path.name]['metadata_changes'] = changes
            font.close()


def apply(folder):
    source_hashes = {path.name: digest(path) for name in (
        'compiled_repairs.py', 'repair_geometry.py', 'layout_repairs.py',
        'language_repairs.py', 'latin_repairs.py', 'symbol_repairs.py')
        if (path := Path(__file__).parent / name).exists()}
    for module in ('language_repairs', 'latin_repairs', 'symbol_repairs'):
        if (Path(__file__).parent / (module + '.py')).exists():
            importlib.import_module(module)
    expected = json.loads((ROOT / 'baseline-font-hashes.json').read_text())
    paths = sorted(Path(folder).glob('*.ttf'))
    if {path.name: digest(path) for path in paths} != expected:
        raise ValueError('Repair inputs must reproduce the complete 0.506 baseline exactly')
    results = []
    for path in paths:
        font = TTFont(path)
        font.recalcTimestamp = False
        before = {name: font['glyf'][name].compile(font['glyf']) for name in font.getGlyphOrder()}
        old_metrics = dict(font['hmtx'].metrics)
        layout = {tag: font[tag].compile(font) for tag in ('cmap', 'GSUB', 'GPOS', 'GDEF') if tag in font}
        stem = WEIGHTS[font['OS/2'].usWeightClass]
        authored = {}
        preserved = set()
        native = set()
        approved_advances = {}
        for cp, function in REPAIRS.items():
            if not eligible(font, cp):
                continue
            outline = authored_result(font, cp, stem)
            if isinstance(outline, tuple):
                outline, advance = outline
                approved_advances[glyph_name(font, cp)] = advance
            matrix = slant_matrix(font, cp)
            if matrix:
                outline = transformed(outline, matrix)
            name = glyph_name(font, cp)
            if name in authored and authored[name].value != outline.value:
                raise ValueError('Conflicting repairs for cmap aliases: ' + name)
            authored[name] = outline
            (preserved if REPAIR_OPTIONS[cp]['preserve_contours'] else native).add(name)
        if preserved & native:
            raise ValueError('Conflicting contour handling for cmap aliases')
        compiled = batch({name: outline for name, outline in authored.items() if name in native})
        compiled.update({name: authored[name] for name in preserved})
        for name, outline in compiled.items():
            pen = TTGlyphPen(None)
            outline.replay(Cu2QuPen(pen, max_err=.35, reverse_direction=False))
            glyph = pen.glyph()
            glyph.recalcBounds(font['glyf'])
            if glyph.numberOfContours:
                glyph.flags[0] |= 0x40
            font['glyf'][name] = glyph
            font['hmtx'][name] = (approved_advances.get(name, old_metrics[name][0]), glyph.xMin if glyph.numberOfContours else 0)
        for item in font['name'].names:
            if item.nameID in (3, 5):
                font['name'].setName(item.toUnicode().replace('0.506', '0.507'),
                                     item.nameID, item.platformID, item.platEncID, item.langID)
        font['head'].fontRevision = .507
        changed = [name for name in before if before[name] != font['glyf'][name].compile(font['glyf'])]
        if set(changed) - set(authored):
            raise ValueError(f'Unexpected outline changes: {path.name}')
        if any(font['hmtx'][name] != metric for name, metric in old_metrics.items() if name not in authored):
            raise ValueError('Unexpected metric changes')
        if any(font[tag].compile(font) != data for tag, data in layout.items()):
            raise ValueError('Encoding or layout changed')
        layout_changes = layout_repairs.apply(font)
        font.save(path)
        with TTFont(path) as saved:
            if saved.getGlyphOrder() != list(before):
                raise ValueError('Glyph order changed')
            for name in before:
                if name not in authored and saved['glyf'][name].compile(saved['glyf']) != before[name]:
                    raise ValueError('Unexpected serialized outline change: ' + name)
        contextual = []
        if any(set(names) & set(changed) for names in CONTEXT_DEPENDENCIES.values()):
            sys.path.insert(0, str(ROOT / 'sources/validation'))
            from shaping import Shaper
            context_shaper = Shaper(path)
            for cp, names in CONTEXT_DEPENDENCIES.items():
                affected = sorted(set(names) & set(changed))
                if not affected:
                    continue
                ch = chr(cp)
                texts = ['a' + ch, 'i' + ch, 'i\u034f' + ch, 'o' + ch, 'α' + ch]
                used = [text for text in texts if set(g['glyph'] for g in context_shaper.shape(text)) & set(affected)]
                if not used:
                    raise ValueError('Declared contextual repair is not used in actual shaping: ' + hex(cp))
                contextual.append({'codepoint': f'U+{cp:04X}', 'changed_glyphs': affected,
                                   'verified_contexts': used})
            context_shaper.close()
        results.append({'file': path.name, 'baseline_sha256': expected[path.name],
                        'sha256': digest(path), 'changed_glyphs': changed,
                        'approved_glyphs': sorted(authored),
                        'preserved_contour_glyphs': sorted(preserved),
                        'metric_changes': {name: {'before': old_metrics[name], 'after': font['hmtx'][name]}
                                           for name in old_metrics if old_metrics[name] != font['hmtx'][name]},
                        'codepoints': [f'U+{cp:04X}' for cp, name in font.getBestCmap().items() if name in authored],
                        'unencoded_glyphs': [name for name in authored if name not in font.getBestCmap().values()],
                        'layout_repairs': layout_changes,
                        'contextual_repairs': contextual,
                        'encoding_and_other_glyphs_preserved': True})
        if getattr(font, '_composition_run_shaper', None) is not None:
            font._composition_run_shaper.close()
    update_clipping_extents(paths, results)
    report = {'version': '0.507', 'baseline': '0.506', 'passed': True,
              'native_boolean_engine': dict(ENGINE_INFO),
              'source_sha256': source_hashes, 'files': results}
    (Path(folder).parent / 'repair-report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonts', required=True, type=Path)
    apply(parser.parse_args().fonts)
