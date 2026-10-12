"""0.504: paired bowl contours, not teardrop holes in unrelated envelopes.

Original netfyr geometry. The control references are this family's o/b/d/e.
Four on-curve extrema and aligned tangents define every oval; a short flat
and two vertical segments intentionally square the Mono o counter. This is
local optical compensation for crowded glyphs, not uniform emboldening.
"""
from model import stroke
from outlines import Resolver
from .common import compound


def oval(cx,cy,rx,ry,k=.56):
    """Four cubic quarters with shared extrema and optical handle proportion."""
    return (f'M{cx} {cy+ry}C{cx+rx*k} {cy+ry} {cx+rx} {cy+ry*k} {cx+rx} {cy}'
        f'C{cx+rx} {cy-ry*k} {cx+rx*k} {cy-ry} {cx} {cy-ry}'
        f'C{cx-rx*k} {cy-ry} {cx-rx} {cy-ry*k} {cx-rx} {cy}'
        f'C{cx-rx} {cy+ry*k} {cx-rx*k} {cy+ry} {cx} {cy+ry}Z')


def gamma(stem,top,cross,bottom,cx,left,right):
    """An oval counter, balanced lower band, and optically relieved crossing.

    The actual four cap endpoints are retained. The pointed internal valley
    belongs between the arms, not inside the closed loop. At the loop the
    upright cardinal bands are v on the sides, .82v below, and 1.05v above.
    These are authored optical choices; no claim of constant radial distance
    or of monolinear strokes at the crossing is made.
    """
    arms=Resolver({},stem)._ops([stroke(f'M{left} {top}L{cx} {cross}L{right} {top}')])
    pts=sorted({p for cmd,ps in arms.value if cmd in ('moveTo','lineTo')
                for p in ps if p[1]>top-stem})
    lp=[p for p in pts if p[0]<cx];rp=[p for p in pts if p[0]>cx]
    if len(lp)!=2 or len(rp)!=2:raise ValueError('Unexpected gamma cap geometry')
    Lout,Lin=lp;Rin,Rout=rp
    ml=(cx-left)/(top-cross);mr=(right-cx)/(top-cross)
    q=max(0.,min(1.,(stem-90)/64))
    radius=139+15*q;cy=bottom+122+7*q
    v=71+13*q;h=.82*v
    innerx=radius-v;innery=cy-bottom-h
    waist=cross+20;neck=49+19*q
    valley=cy+innery+1.05*v
    # Match the incoming arm's direction, turn through a finite waist, and
    # enter an oval lower quadrant with a vertical tangent at its extremum.
    py=waist+100
    pr=(Rout[0]+mr*(py-Rout[1]),py)
    pl=(Lout[0]-ml*(py-Lout[1]),py)
    cr=(pr[0]-45*mr,py-45);cl=(pl[0]+45*ml,py-45)
    outer=(f'M{Lout[0]} {Lout[1]}L{Lin[0]} {Lin[1]}L{cx} {valley}'
        f'L{Rin[0]} {Rin[1]}L{Rout[0]} {Rout[1]}L{pr[0]} {pr[1]}'
        f'C{cr[0]} {cr[1]} {cx+neck} {waist+36} {cx+neck} {waist}'
        f'C{cx+neck} {waist-40} {cx+radius} {cy+53} {cx+radius} {cy}'
        f'C{cx+radius} {cy-(cy-bottom)*.56} {cx+radius*.56} {bottom} {cx} {bottom}'
        f'C{cx-radius*.56} {bottom} {cx-radius} {cy-(cy-bottom)*.56} {cx-radius} {cy}'
        f'C{cx-radius} {cy+53} {cx-neck} {waist-40} {cx-neck} {waist}'
        f'C{cx-neck} {waist+36} {cl[0]} {cl[1]} {pl[0]} {pl[1]}'
        f'L{Lout[0]} {Lout[1]}Z')
    return compound(outer,[oval(cx,cy,innerx,innery)])


def mono_pair(stem,kind):
    """Two distinct, centred counters in the established 640-unit Mono cell.

    The a counter keeps its straight shared stem; the o counter uses the
    short flats and vertical middle found in netfyr's bowl letters. The e
    eye has a centred roof and matching quarter curves. Horizontal contrast
    is .84 of the local side band. The shared stem, local vertical strokes,
    and lower-left bowl use the same v; they are not different accidental
    widths. Both ligatures retain two counters and their open e mouth.
    """
    if kind not in ('ae','oe'):raise ValueError(kind)
    q=max(0.,min(1.,(stem-90)/64));v=90+.35*(stem-90);h=.84*v
    left,right,shared=32.,608.,316.
    sl=shared-v/2;sr=shared+v/2;il=left+v;ir=right-v
    roof=528-h;floor=-8+h;bar=322+24*q;lo=bar-h
    oc=(il+sl)/2;ec=(sr+ir)/2;orx=oc-left;erx=right-ec
    # Symmetric four-corner o counter: no off-centre lower controls.
    k=.56;xa=oc-15;xb=oc+15;bot=200.;top=320.
    oh=(f'M{xa} {roof}H{xb}C{xb+k*(sl-xb)} {roof} {sl} {top+k*(roof-top)} {sl} {top}'
        f'V{bot}C{sl} {bot-k*(bot-floor)} {xb+k*(sl-xb)} {floor} {xb} {floor}'
        f'H{xa}C{xa-k*(xa-il)} {floor} {il} {bot-k*(bot-floor)} {il} {bot}'
        f'V{top}C{il} {top+k*(roof-top)} {xa-k*(xa-il)} {roof} {xa} {roof}Z')
    # The e's flat bar, short flat roof, and paired corners are intentional.
    H=roof-bar;xl=ec-12;xr=ec+12
    eh=(f'M{sr} {bar}H{ir}C{ir} {bar+k*H} {xr+k*(ir-xr)} {roof} {xr} {roof}'
        f'H{xl}C{xl-k*(xl-sr)} {roof} {sr} {bar+k*H} {sr} {bar}Z')
    iy=floor+32;ey=iy-.98*h
    epart=(f'C352 496 {ec-53} 528 {ec} 528'
        f'C{ec+.56*erx} 528 608 {lo+.56*(528-lo)} 608 {lo+17}'
        f'Q608 {lo} 591 {lo}H{sr}'
        f'C{sr} {lo-.56*(lo-floor)} {ec-.56*(ec-sr)} {floor} {ec} {floor}'
        f'C{ec+52} {floor} 555 {floor+15} 592 {iy}'
        f'L592 {ey}C545 10 {ec+56} -8 {ec} -8'
        f'C{ec-56} -8 351 35 316 85')
    if kind=='oe':
        outer=(f'M316 445'+epart+
            f'C280 25 {oc+55} -8 {oc} -8'
            f'C{oc-.56*orx} -8 32 {260-.56*268} 32 260'
            f'C32 {260+.56*268} {oc-.56*orx} 528 {oc} 528'
            f'C{oc+55} 528 282 496 316 445Z')
        holes=[oh,eh]
    else:
        ac=oc-5;acy=(floor+lo)/2
        ah=(f'M{sl} {lo}H{ac}'
            f'C{ac-.56*(ac-il)} {lo} {il} {acy+.56*(lo-acy)} {il} {acy}'
            f'C{il} {acy-.56*(acy-floor)} {ac-.56*(ac-il)} {floor} {ac} {floor}'
            f'C{ac+.56*(sl-ac)} {floor} {sl} {acy-.56*(acy-floor)} {sl} {acy}V{lo}Z')
        outer=(f'M106 390L42 440C80 497 {ac-59} 528 {ac} 528'
            f'C{ac+69} 528 287 484 316 430'+epart+
            f'C279 20 {ac+59} -8 {ac} -8'
            f'C{ac-.56*(ac-left)} -8 32 {acy-.56*(acy+8)} 32 {acy}'
            f'C32 {acy+.56*(bar-acy)} {ac-.56*(ac-left)} {bar} {ac} {bar}'
            f'H{sl}V333C{sl} 400 {ac+42} {roof} {ac} {roof}'
            f'C{ac-41} {roof} 123 426 106 390Z')
        holes=[ah,eh]
    return compound(outer,holes)
