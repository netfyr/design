"""Individually proofed, original netfyr control glyph outlines.

These recipes are hand-authored; no external font supplies geometry.
"""
from model import fill, stroke

def d_ops(stem):
    left = 116 - stem / 2
    right = 524 + stem / 2
    inner_left = 116 + stem / 2
    inner_right = 524 - stem / 2
    bottom = -10 + stem * .9
    top = 530 - stem * .9
    # These are two separately authored contours. Inner/right is a 120-unit
    # vertical segment (200..320); tangent controls continue the direction at
    # both ends. Vertical weight follows stem, horizontal weight is 0.9 stem.
    outer = (
        f'M{inner_right} 720H{right}V0H{inner_right}V66'
        f'C448 14 390 -10 311 -10'
        f'C164 -10 {left} 93 {left} 259'
        f'C{left} 425 167 530 314 530'
        f'C391 530 449 504 {inner_right} 452V720Z'
    )
    counter = (
        f'M{inner_right} 320'
        f'C{inner_right} 413 411 {top} 319 {top}'
        f'C227 {top} {inner_left} 373 {inner_left} 260'
        f'C{inner_left} 147 227 {bottom} 319 {bottom}'
        f'C411 {bottom} {inner_right} 107 {inner_right} 200V320Z'
    )
    return [fill(outer + ' ' + counter)]



def y_recipe(stem):
    t=max(-1.12,min(2.15,(stem-72)/18))
    # Horizontal width of slanted strips; the normal stroke is about .97 stem.
    left_outer=74.0
    left_inner=151.0+20*t
    right_inner=490.0-20*t
    right_outer=566.0
    left_slope=.425
    right_slope=.420
    def intersect(left):
        y=(left+left_slope*520-right_inner+right_slope*520)/(left_slope+right_slope)
        return (left+left_slope*(520-y),y)
    inner=intersect(left_inner)
    branch=intersect(left_outer)
    outer_end=(right_outer+right_slope*(-92-520),-92)
    inner_end_y=-80+4*t
    inner_end=(right_inner+right_slope*(inner_end_y-520),inner_end_y)
    tail_top=-155+16*t
    # Both final/initial tail handles are horizontal. The handles beside the
    # diagonal use exactly the .420 dx/dy slope, giving C1 direction continuity.
    outer_c1=(outer_end[0]-68*right_slope,outer_end[1]-68)
    inner_c2=(inner_end[0]-48*right_slope,inner_end[1]-48)
    def f(n):return format(n,'.6f').rstrip('0').rstrip('.')
    d=(f'M{f(left_outer)} 520H{f(left_inner)}'
       f'L{f(inner[0])} {f(inner[1])}L{f(right_inner)} 520H{f(right_outer)}'
       f'L{f(outer_end[0])} {f(outer_end[1])}'
       f'C{f(outer_c1[0])} {f(outer_c1[1])} 228 -220 134 -220'
       f'H80V{f(tail_top)}H134'
       f'C{f(181-8*t)} {f(tail_top)} {f(inner_c2[0])} {f(inner_c2[1])} {f(inner_end[0])} {f(inner_end[1])}'
       f'L{f(branch[0])} {f(branch[1])}Z')
    return [fill(d)]

# Integration:
# lower('y', y_recipe(w), bottom=(240,-270))
# Source geometry has ink bounds x=74..566, y=-220..520 in both masters.
# Existing y bearings yield advance536, LSB22/RSB22 (Regular),
# and advance524, LSB16/RSB16 (Semibold). See review for optical fitting option.


def s_ops(stem):
    top=528-stem*.45
    bottom=-8+stem*.45
    d=(f'M471 431C428 474 379 {top} 308 {top}'
       f'C212 {top} 148 450 148 379'
       f'C148 308 212 {2028/7} 309 262'
       f'C409 {1634/7} 489 {1474/7} 489 132'
       f'C489 60 422 {bottom} 315 {bottom}'
       f'C236 {bottom} 175 58 132 101')
    return [stroke(d)]


def a_ops(stem, crossbar=None):
    if crossbar is None:
        crossbar=292+(stem-72)*10/18
    left=112-stem/2
    right=514+stem/2
    inner_left=112+stem/2
    inner_right=514-stem/2
    bottom=-8+.9*stem
    top=528-.9*stem
    counter_top=crossbar-.9*stem
    terminal_inner_x=111+stem*.73
    terminal_inner_y=440-stem*.53
    # Clockwise outer outline. Upper and lower curves are authored separately
    # from the counter so equal stem weight does not force bulbous joins.
    outer=(
        f'M{right} 0H{inner_right}V84'
        f'C431 25 389 -8 284 -8'
        f'C150 -8 {left} 46 {left} 140'
        f'C{left} 239 166 {crossbar} 312 {crossbar}'
        f'H{inner_right}V333'
        f'C{inner_right} 419 422 {top} 323 {top}'
        f'C248 {top} 192 440 {terminal_inner_x} {terminal_inner_y}'
        f'L111 440'
        f'C156 495 232 528 325 528'
        f'C468 528 {right} 451 {right} 327V0Z'
    )
    counter=(
        f'M{inner_right} {counter_top}'
        f'H313'
        f'C210 {counter_top} {inner_left} 190 {inner_left} 140'
        f'C{inner_left} 88 202 {bottom} 284 {bottom}'
        f'C393 {bottom} {inner_right} 109 {inner_right} 174'
        f'V{counter_top}Z'
    )
    return [fill(outer+' '+counter)]


def b_ops(stem):
    left = 116 - stem / 2
    right = 524 + stem / 2
    inner_left = 116 + stem / 2
    inner_right = 524 - stem / 2
    bottom = -10 + stem * .9
    top = 530 - stem * .9
    outer = (
        f'M{left} 0V720H{inner_left}V450'
        f'C194 504 253 530 327 530'
        f'C474 530 {right} 424 {right} 263'
        f'C{right} 98 477 -10 329 -10'
        f'C251 -10 193 14 {inner_left} 64V0Z'
    )
    counter = (
        f'M{inner_left} 320V200'
        f'C{inner_left} 107 233 {bottom} 326 {bottom}'
        f'C417 {bottom} {inner_right} 148 {inner_right} 260'
        f'C{inner_right} 371 413 {top} 322 {top}'
        f'C230 {top} {inner_left} 413 {inner_left} 320Z'
    )
    return [fill(outer + ' ' + counter)]


def r_recipe(stem):
    t=max(-1.12,min(2.15,(stem-72)/18))
    left=212-stem/2
    right=212+stem/2
    inner_top=528-stem*.9
    outer_peak=378
    # G2 at outer maximum: endpoint handles 58 and 25 units long.
    outer_control_y=528-24*(25/58)**2
    # G2 at inner maximum: endpoint handles 25 and (80-9t) units long.
    inner_handle=80-9*t
    inner_control_y=inner_top-5*(inner_handle/25)**2
    def f(value):return format(value,'.6f').rstrip('0').rstrip('.')
    path=(f'M{f(left)} 0V520H{f(right)}V{f(451-13*t)}'
          f'C{f(277+4*t)} 504 320 528 {outer_peak} 528'
          f'C403 528 425 {f(outer_control_y)} 449 516'
          f'V{f(449-stem*.9+64.8)}'
          f'C429 {f(inner_top-5)} 406 {f(inner_top)} 381 {f(inner_top)}'
          f'C{f(381-inner_handle)} {f(inner_top)} {f(right)} {f(inner_control_y)} {f(right)} 329V0Z')
    return [fill(path)]


def p_ops(stem):
    left = 116 - stem / 2
    right = 524 + stem / 2
    inner_left = 116 + stem / 2
    inner_right = 524 - stem / 2
    bottom = -10 + stem * .9
    top = 530 - stem * .9
    outer = (
        f'M{left} -220V520H{inner_left}V452'
        f'C195 504 254 530 328 530'
        f'C475 530 {right} 424 {right} 263'
        f'C{right} 99 477 -10 328 -10'
        f'C252 -10 194 14 {inner_left} 66V-220Z'
    )
    counter = (
        f'M{inner_left} 320V200'
        f'C{inner_left} 107 232 {bottom} 324 {bottom}'
        f'C416 {bottom} {inner_right} 148 {inner_right} 260'
        f'C{inner_right} 372 415 {top} 324 {top}'
        f'C232 {top} {inner_left} 413 {inner_left} 320Z'
    )
    return [fill(outer + ' ' + counter)]


def q_ops(stem):
    left = 116 - stem / 2
    right = 524 + stem / 2
    inner_left = 116 + stem / 2
    inner_right = 524 - stem / 2
    bottom = -10 + stem * .9
    top = 530 - stem * .9
    outer = (
        f'M{inner_right} 520H{right}V-220H{inner_right}V66'
        f'C448 14 390 -10 311 -10'
        f'C164 -10 {left} 93 {left} 259'
        f'C{left} 425 167 530 314 530'
        f'C391 530 449 504 {inner_right} 452V520Z'
    )
    counter = (
        f'M{inner_right} 320'
        f'C{inner_right} 413 411 {top} 319 {top}'
        f'C227 {top} {inner_left} 373 {inner_left} 260'
        f'C{inner_left} 147 227 {bottom} 319 {bottom}'
        f'C411 {bottom} {inner_right} 107 {inner_right} 200V320Z'
    )
    return [fill(outer + ' ' + counter)]


def g_ops(stem):
    left = 116 - stem / 2
    right = 524 + stem / 2
    inner_left = 116 + stem / 2
    inner_right = 524 - stem / 2
    bottom = -10 + stem * .9
    top = 530 - stem * .9
    tail_inner = -220 + stem * .9
    t = max(-1.12,min(2.15,(stem - 72) / 18))
    # The low extremum is fixed at -220; the inner extremum follows the
    # optical horizontal stroke weight. Tail sides join the vertical stem
    # with vertical Bézier tangents, not overlapping stroke end caps.
    outer = (
        f'M{inner_right} 520H{right}V-27'
        f'C{right} -151 460 -220 320 -220'
        f'C224 -220 150 -187 90 -135'
        f'L{142 + 13*t} {-83 + 11*t}'
        f'C{188 + 5*t} {-124 + 10*t} 247 {tail_inner} 320 {tail_inner}'
        f'C426 {tail_inner} {inner_right} -105 {inner_right} -27'
        f'V66C448 14 390 -10 311 -10'
        f'C164 -10 {left} 93 {left} 259'
        f'C{left} 425 167 530 314 530'
        f'C391 530 449 504 {inner_right} 452V520Z'
    )
    counter = (
        f'M{inner_right} 320'
        f'C{inner_right} 413 411 {top} 319 {top}'
        f'C227 {top} {inner_left} 373 {inner_left} 260'
        f'C{inner_left} 147 227 {bottom} 319 {bottom}'
        f'C411 {bottom} {inner_right} 107 {inner_right} 200V320Z'
    )
    return [fill(outer + ' ' + counter)]


def sharp_s_ops(stem):
    """One open-counter contour; its long stem terminates on the baseline."""
    t=max(-1.12,min(2.15,(stem-72)/18))
    left=135-stem/2
    inner_left=135+stem/2
    upper_right=526+9*t
    upper_inner=454-9*t
    lower_right=557+9*t
    lower_inner=485-9*t
    crest_inner=728-.9*stem
    floor_inner=-8+.9*stem
    neck_outer=378+9*t
    neck_inner=307-9*t
    d=(f'M{left} 0V486'
       f'C{left} 638 178 728 313 728'
       f'C451 728 {upper_right} 650 {upper_right} 537'
       f'C{upper_right} 463 {489+9*t} 420 {421+9*t} 379'
       f'C{391+9*t} {379-30*41/68} {neck_outer} 349 {neck_outer} 337'
       f'C{neck_outer} 316 {418+9*t} 304 {459+9*t} 279'
       f'C{523+9*t} {279-64*25/41} {lower_right} 191 {lower_right} 120'
       f'C{lower_right} 39 487 -8 362 -8H309V{floor_inner}H359'
       f'C443 {floor_inner} {lower_inner} 85 {lower_inner} 132'
       f'C{lower_inner} 175 {459-9*t} 203 {419-9*t} 229'
       f'C{355-9*t} 270.6 {neck_inner} 292 {neck_inner} 340'
       f'C{neck_inner} 382 {340-9*t} 412 {389-9*t} 443'
       f'C{431-9*t} {443+42*31/49} {upper_inner} 500 {upper_inner} 539'
       f'C{upper_inner} 615 408 {crest_inner} 314 {crest_inner}'
       f'C222 {crest_inner} {inner_left} 601 {inner_left} 480V0Z')
    return [fill(d)]

# Integration: put(0xDF, sharp_s_ops(weight),720,top=(313,775),bottom=(320,-45))
# Add 'ß':(62,42) to spacing.BEARINGS. Weight reduction is applied by spacing.fit.


def ae_ops(stem):
    t=max(-1.12,min(2.15,(stem-72)/18))
    left=112-stem/2-194
    a_inner_left=112+stem/2-194
    shared_left=320-stem/2
    shared_right=320+stem/2
    right=736+stem/2
    right_inner=736-stem/2
    top=528-.9*stem
    bottom=-8+.9*stem
    bar_top=292+10*t
    bar_bottom=bar_top-.9*stem
    bar_center=bar_top-.45*stem
    k=.5522847498307936
    e_terminal_inner=(726-.3755*stem,106+.297*stem)
    e_terminal_outer=(726+.3755*stem,106-.297*stem)
    terminal_inner_x=111+stem*.73-194
    terminal_inner_y=440-stem*.53
    outer=(
      f'M{terminal_inner_x} {terminal_inner_y}L-83 440'
      f'C-38 495 38 528 131 528'
      f'C236 528 286 486 320 431'
      f'C365 494 435 528 530 528'
      f'C682 528 {right} 428 {right} {bar_center}'
      f'C{right} {bar_center-k*.45*stem} {right-(1-k)*stem/2} {bar_bottom} {right-stem/2} {bar_bottom}'
      f'H{shared_right}'
      f'C{shared_right+8} 117 429 {bottom} 531 {bottom}'
      f'C615 {bottom} {e_terminal_inner[0]-42} {e_terminal_inner[1]-43} {e_terminal_inner[0]} {e_terminal_inner[1]}'
      f'L{e_terminal_outer[0]} {e_terminal_outer[1]}'
      f'C{e_terminal_outer[0]-42} {e_terminal_outer[1]-43} 625 -8 531 -8'
      f'C429 -8 361 25 320 85'
      f'C272 23 206 -8 90 -8'
      f'C-44 -8 {left} 46 {left} 140'
      f'C{left} 239 -28 {bar_top} 118 {bar_top}'
      f'H{shared_left}V333'
      f'C{shared_left} 419 228 {top} 129 {top}'
      f'C54 {top} -2 440 {terminal_inner_x} {terminal_inner_y}Z'
    )
    a_counter=(
      f'M{shared_left} {bar_bottom}H119'
      f'C16 {bar_bottom} {a_inner_left} 190 {a_inner_left} 140'
      f'C{a_inner_left} 88 8 {bottom} 90 {bottom}'
      f'C199 {bottom} {shared_left} 109 {shared_left} 174'
      f'V{bar_bottom}Z'
    )
    e_counter=(
      f'M{shared_right+3} {bar_top}'
      f'H{right_inner}'
      f'C{right_inner-8} 406 632 {top} 530 {top}'
      f'C428 {top} {shared_right+12} 406 {shared_right+3} {bar_top}Z'
    )
    return [fill(outer+' '+a_counter+' '+e_counter)]


def capital_sharp_s_ops(stem):
    t=max(-1.12,min(2.15,(stem-72)/18))
    left=135-stem/2
    inner_left=135+stem/2
    upper_right=605+9*t
    upper_inner=533-9*t
    lower_right=639+9*t
    lower_inner=567-9*t
    roof_inner=700-.9*stem
    floor_inner=-8+.9*stem
    neck_outer=436+9*t
    neck_inner=365-9*t
    d=(f'M{left} 0V700H361'
       f'C511 700 {upper_right} 641 {upper_right} 538'
       f'C{upper_right} 470 {559+9*t} 430 {497+9*t} 390'
       f'C{464+9*t} {390-33*40/62} {neck_outer} 354 {neck_outer} 337'
       f'C{neck_outer} 317 {469+9*t} 304 {511+9*t} 279'
       f'C{577+9*t} {279-66*25/42} {lower_right} 194 {lower_right} 123'
       f'C{lower_right} 38 499 -8 370 -8H309V{floor_inner}H368'
       f'C472 {floor_inner} {lower_inner} 96 {lower_inner} 135'
       f'C{lower_inner} 179 {537-9*t} 211 {482-9*t} 241'
       f'C{413-9*t} {241+69*30/55} {neck_inner} 298 {neck_inner} 339'
       f'C{neck_inner} 382 {405-9*t} 414 {453-9*t} 447'
       f'C{495-9*t} {447+42*33/48} {upper_inner} 503 {upper_inner} 540'
       f'C{upper_inner} 600 468 {roof_inner} 359 {roof_inner}'
       f'H{inner_left}V0Z')
    return [fill(d)]

# Integration: put(0x1E9E,capital_sharp_s_ops(weight),700,top=(361,735),bottom=(350,-35))
# Add 'ẞ':(62,42) to spacing.BEARINGS. Weight reduction stays automatic.

# Set reg[0x1E9E]['dotbelow']=(350,-10) after the put call.


from math import atan2, cos, sin, tan, pi
from model import fill, stroke


def eth_ops(stem):
    cx,cy=320.,260.
    rx,ry=206+stem/2,270.
    left,right=cx-rx,cx+rx
    inner_rx,inner_ry=206-stem/2,270-stem*.9
    # The cut terminal is perpendicular to the opening ascender tangent.
    # Both weights finish at y720; the inner boundary absorbs weight growth.
    p0=(237-stem*108/(193**2+108**2)**.5,
        720-stem*193/(193**2+108**2)**.5)
    p1=(430-stem*108/(193**2+108**2)**.5,
        612-stem*193/(193**2+108**2)**.5)
    p2=(right-stem,450.)
    p3=(right-stem,260.)
    def lerp(a,b,t):return tuple(a[i]+(b[i]-a[i])*t for i in (0,1))
    def split(t):
        a,b,c=lerp(p0,p1,t),lerp(p1,p2,t),lerp(p2,p3,t)
        d,e=lerp(a,b,t),lerp(b,c,t)
        return a,d,lerp(d,e,t)
    lo,hi=0.,1.
    for _ in range(64):
        mid=(lo+hi)/2; _,_,p=split(mid)
        if ((p[0]-cx)/rx)**2+((p[1]-cy)/ry)**2>1:lo=mid
        else:hi=mid
    a,d,join=split((lo+hi)/2)
    theta=atan2((join[1]-cy)/ry,(join[0]-cx)/rx)
    k=4/3*tan((theta-pi/2)/4)
    arc1=(cx-k*rx,cy+ry)
    arc2=(join[0]+k*rx*sin(theta),join[1]-k*ry*cos(theta))
    q=.5522847498307936
    def f(n):return format(n,'.6f').rstrip('0').rstrip('.')
    def xy(p):return ' '.join(f(v) for v in p)
    outer=(f'M237 720C430 612 {f(right)} 450 {f(right)} 260'
      f'C{f(right)} {f(cy-q*ry)} {f(cx+q*rx)} -10 320 -10'
      f'C{f(cx-q*rx)} -10 {f(left)} {f(cy-q*ry)} {f(left)} 260'
      f'C{f(left)} {f(cy+q*ry)} {f(cx-q*rx)} 530 320 530'
      f'C{xy(arc1)} {xy(arc2)} {xy(join)}'
      f'C{xy(d)} {xy(a)} {xy(p0)}Z')
    il,ir=cx-inner_rx,cx+inner_rx;bottom,top=cy-inner_ry,cy+inner_ry
    counter=(f'M{f(ir)} 260C{f(ir)} {f(cy+q*inner_ry)} {f(cx+q*inner_rx)} {f(top)} 320 {f(top)}'
      f'C{f(cx-q*inner_rx)} {f(top)} {f(il)} {f(cy+q*inner_ry)} {f(il)} 260'
      f'C{f(il)} {f(cy-q*inner_ry)} {f(cx-q*inner_rx)} {f(bottom)} 320 {f(bottom)}'
      f'C{f(cx+q*inner_rx)} {f(bottom)} {f(ir)} {f(cy-q*inner_ry)} {f(ir)} 260Z')
    # The crossbar is visibly subordinate to the body and clears the bowl.
    return [fill(outer+' '+counter),stroke('M202 583L432 688',.74)]


def section_ops(stem):
    t=max(-1.12,min(2.15,(stem-72)/18))
    def v(a,b):return a+(b-a)*t
    def p(*pairs):return ' '.join(f'{v(a,b):g}' for a,b in pairs)
    # The top and bottom overshoots stay fixed while interior clearance and
    # side curves are redrawn for the heavier master.
    d='M'+p((492,501),(604,604))
    d+='L'+p((429,423),(572,565))
    d+='C'+p((405,400),(620,615),(366,363),(643,627),(311,311),(643,627))
    d+='C'+p((237,243),(643,627),(212,221),(607,601),(212,221),(560,560))
    d+='C'+p((212,221),(522,528),(247,253),(512,517),(334,339),(468,473))
    d+='C'+p((438,445),(415,420),(493,502),(374,377),(493,502),(307,307))
    d+='C'+p((493,502),(263,263),(472,482),(233,233),(435,445),(211,211))
    d+='C'+p((473,481),(183,183),(493,502),(152,151),(493,502),(103,103))
    d+='C'+p((493,502),(36,28),(421,424),(-8,-8),(316,316),(-8,-8))
    d+='C'+p((214,208),(-8,-8),(140,132),(37,31),(117,108),(110,111))
    d+='L'+p((183,188),(144,154))
    d+='C'+p((208,212),(83,99),(251,255),(57,73),(317,317),(57,73))
    d+='C'+p((380,377),(57,73),(421,412),(75,86),(421,412),(115,115))
    d+='C'+p((421,412),(152,146),(384,379),(168,165),(309,304),(206,203))
    d+='C'+p((204,197),(260,257),(137,128),(300,297),(137,128),(366,366))
    d+='C'+p((137,128),(413,414),(162,153),(447,447),(197,187),(470,470))
    d+='C'+p((161,153),(498,498),(140,131),(532,532),(140,131),(575,575))
    d+='C'+p((140,131),(655,663),(206,202),(708,708),(314,314),(708,708))
    d+='C'+p((401,407),(708,708),(461,470),(674,676),(492,501),(604,604))+'Z'
    # Counter: a rounded diagonal loop, deliberately drawn independently from
    # the outer contour to keep the waist clear at Semibold text sizes.
    d+='M'+p((260,266),(431,417))
    d+='C'+p((228,238),(412,400),(209,218),(393,387),(209,218),(370,370))
    d+='C'+p((209,218),(332,338),(246,254),(315,321),(345,341),(267,281))
    d+='C'+p((389,380),(285,297),(421,412),(297,305),(421,412),(316,316))
    d+='C'+p((421,412),(350,342),(383,375),(368,359),(305,300),(409,398))
    d+='C'+p((287,286),(419,406),(272,276),(426,412),(260,266),(431,417))+'Z'
    return [fill(d)]


from math import sqrt

def _double_diagonal(stem, height, peak, left, foot_left, foot_ratio=1.0):
    center = 320.0
    normal = .96 * stem
    peak_half = .5 * stem
    foot_right = foot_left + foot_ratio * stem
    outer_slope = (foot_left-left) / height
    outer_band = normal * sqrt(1+outer_slope**2)
    # Solve peak*s - normal*sqrt(1+s*s) = A. This gives parallel
    # inside/outside edges of the central diagonal at the desired weight.
    a = center-peak_half-foot_right
    slope = (a*peak + normal*sqrt(peak*peak+a*a-normal*normal)) / (peak*peak-normal*normal)
    inner_band = normal * sqrt(1+slope*slope)
    join_y = (foot_left+outer_band-foot_right+inner_band) / (outer_slope+slope)
    join_x = foot_left + outer_band - outer_slope*join_y
    notch_y = peak + (peak_half-inner_band)/slope
    points = [
        (left,height),(left+outer_band,height),(join_x,join_y),
        (center-peak_half,peak),(center+peak_half,peak),
        (2*center-join_x,join_y),(2*center-left-outer_band,height),
        (2*center-left,height),(2*center-foot_left,0),
        (2*center-foot_right,0),(center,notch_y),(foot_right,0),
        (foot_left,0),
    ]
    def fmt(x):
        return f'{x:.6f}'.rstrip('0').rstrip('.')
    path='M'+'L'.join(f'{fmt(x)} {fmt(y)}' for x,y in points)+'Z'
    return [fill(path)]


def w_ops(stem, mono=False):
    """Lowercase: 520 top, 407 central crest, 0 baseline, center x=320."""
    return _double_diagonal(stem,520,407,34 if mono else -20,130 if mono else 116)


def W_ops(stem, mono=False):
    """Uppercase: 700 top, 500 central crest, 0 baseline, center x=320."""
    return _double_diagonal(stem,700,500,34 if mono else -40,132 if mono else 110)
