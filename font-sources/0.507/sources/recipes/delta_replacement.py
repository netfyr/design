"""Original, hand-authored delta / increment / partial outlines for netfyr.

Only the formulae and cubic control points below determine the outlines.
No font outlines or dimensions were imported from the research references.
"""
from math import sqrt
from model import fill


def _f(v):
    return format(v, '.6f').rstrip('0').rstrip('.')


def delta_capital_ops(stem, height=708):
    """A deliberately bounded triangular capital with an optical apex.

    The two diagonal counter edges are parallel offsets from the outer
    diagonals. Their normal thickness is 0.9 of the upright stem; the bottom
    horizontal has the same optical thickness. A 20-unit flat at the apex
    avoids a rounded stroker cap without creating an infinitely sharp spike.
    """
    left, right = 58., 582.
    top_left, top_right = 310., 330.
    thick = .9*stem
    slope = (top_left-left)/height
    normal = thick*sqrt(1+slope*slope)
    inner_left = left+slope*thick+normal
    inner_right = 640-inner_left
    inner_top = (320-left-normal)/slope
    outer = f'M{_f(left)} 0L{_f(top_left)} {height}H{_f(top_right)}L{_f(right)} 0Z'
    # Counter winding is opposite to the outer outline.
    counter = (f'M{_f(inner_left)} {_f(thick)}H{_f(inner_right)}'
               f'L320 {_f(inner_top)}Z')
    return [fill(outer+' '+counter)]


def delta_lower_ops(stem):
    """Downstroke-led Greek delta with one exterior and one closed counter.

    The bowl is slightly shorter than omicron, which keeps the descending
    movement of the upper stroke legible. The counter is independently drawn;
    no finite stroke cap ends inside it. Round baseline and ascender heights
    are fixed across the two weights.
    """
    growth=(stem-72)/2
    left,right=90-growth,550+growth
    hook_left=203-growth
    hook_inner=hook_left+stem
    inner_left,inner_right=left+stem,right-stem
    bottom=-10+.9*stem
    top=509-.9*stem
    hook_floor=730-.9*stem
    terminal_lower=(488-.195*stem,715-.878*stem)
    outer=(
        'M488 715C451 725 402 730 356 730'
        f'C262 730 {_f(hook_left)} 703 {_f(hook_left)} 646'
        f'C{_f(hook_left)} 594 255 549 313 509'
        f'C181 509 {_f(left)} 400 {_f(left)} 250'
        f'C{_f(left)} 86 176 -10 313 -10'
        f'C457 -10 {_f(right)} 92 {_f(right)} 250'
        f'C{_f(right)} 383 482 467 392 539'
        f'C326 591.8 {_f(hook_inner)} 620 {_f(hook_inner)} 644'
        f'C{_f(hook_inner)} {_f(hook_floor)} 310 {_f(hook_floor)} 356 {_f(hook_floor)}'
        f'C396 {_f(hook_floor)} 439 {_f(hook_floor-5)} {_f(terminal_lower[0])} {_f(terminal_lower[1])}Z'
    )
    counter=(
        f'M320 {_f(top)}'
        f'C417 {_f(top)} {_f(inner_right)} 367 {_f(inner_right)} 250'
        f'C{_f(inner_right)} 134 417 {_f(bottom)} 316 {_f(bottom)}'
        f'C218 {_f(bottom)} {_f(inner_left)} 134 {_f(inner_left)} 250'
        f'C{_f(inner_left)} 373 225 {_f(top)} 320 {_f(top)}Z'
    )
    return [fill(outer+' '+counter)]


def partial_ops(stem):
    """A separate mathematical partial derivative, not a delta alias.

    Its open top arch and clockwise bowl remain recognisably distinct from
    Greek delta's upper loop. The independent counter removes the same old
    butt-cap incursion found in the delta.
    """
    growth=(stem-72)/2
    left,right=101-growth,552+growth
    inner_left,inner_right=left+stem,right-stem
    bottom=-10+.9*stem
    top=487-.9*stem
    dh=.9*(stem-72)
    terminal=(154+stem/sqrt(2),645-stem/sqrt(2))
    outer=(
        'M154 645C206 699 262 730 320 730'
        f'C465 730 {_f(right)} 515 {_f(right)} 279'
        f'C{_f(right)} 102 457 -10 321 -10'
        f'C186 -10 {_f(left)} 74 {_f(left)} 237'
        f'C{_f(left)} 401 197 487 309 487'
        f'C370 487 421 467 {_f(468-growth)} {_f(426-dh/2)}'
        f'C{_f(448-growth)} {_f(556-dh)} 396 {_f(640-dh)} 350 {_f(660-dh)}'
        f'C302 {_f(660+48*20/46-dh)} {_f(251+growth)} {_f(653-dh)} {_f(terminal[0])} {_f(terminal[1])}Z'
    )
    counter=(
        f'M317 {_f(top)}'
        f'C230 {_f(top)} {_f(inner_left)} 348 {_f(inner_left)} 236'
        f'C{_f(inner_left)} 127 235 {_f(bottom)} 319 {_f(bottom)}'
        f'C414 {_f(bottom)} {_f(inner_right)} 140 {_f(inner_right)} 275'
        f'C{_f(inner_right)} 367 401 {_f(top)} 317 {_f(top)}Z'
    )
    return [fill(outer+' '+counter)]
