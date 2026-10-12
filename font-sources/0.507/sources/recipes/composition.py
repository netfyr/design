"""Glyph composition for the family's authored mathematical negations.

Unicode normalization may leave base + U+0338 decomposed when U+034F is
present. CGJ must not itself change the chosen visual form. This lookup
selects the existing symbol without altering text, metrics, or outlines.
Every visible mark, including internal alternates, remains a lookup blocker.
"""
import unicodedata as ud


def math_negation_lookups(registry, glyph_name):
    visible_marks = [glyph_name(cp) for cp, glyph in registry.items()
                     if glyph.get('mark') and cp != 0x034F]
    pairs = []
    for cp in sorted(c for c in registry if isinstance(c, int)):
        decomposition = ud.decomposition(chr(cp)).split()
        if len(decomposition) != 2 or decomposition[0].startswith('<'):
            continue
        base, mark = (int(value, 16) for value in decomposition)
        if mark == 0x0338 and base in registry and mark in registry:
            pairs.append((base, cp))
    if not pairs:
        return []
    lines = ['  @MATH_VISIBLE_MARKS = ['+' '.join(visible_marks)+'];',
             '  lookup MATH_NEGATION {',
             '    lookupflag UseMarkFilteringSet @MATH_VISIBLE_MARKS;']
    lines.extend(f'    sub {glyph_name(base)} uni0338 by {glyph_name(cp)};'
                 for base, cp in pairs)
    return lines+['  } MATH_NEGATION;']
