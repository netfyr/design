
"""Original expansion drawings and explicit optical controls.

The existing Regular/SemiBold uprights remain immutable reference styles.
This module supplies actual drawing changes, not synthetic font emboldening.
All weights are statically evaluated; no variable-font compatibility is claimed.
"""
from math import sqrt,tan,radians
from model import fill,stroke,ellipse,component
from outlines import bounds,transformed
import refined_glyphs
from mono import is_cell

WEIGHTS={300:52,400:72,500:81,600:90,700:110,800:132,900:154}
WEIGHT_NAMES={300:'Light',400:'Regular',500:'Medium',600:'SemiBold',
              700:'Bold',800:'ExtraBold',900:'Black'}
ANGLE=10.0
SHEAR=tan(radians(ANGLE))
PIVOT=260.0
ANCHORS=('top','bottom','right','ogonek','dotbelow','overlay','tone','stack_right')

def progress(stem):
    """Nonlinear local contrast control, independently bounded from stem width."""
    return max(0.,min(1.,(stem-90)/64))

def setops(r,c,ops,**anchors):
    cp=ord(c) if isinstance(c,str) and len(c)==1 else c
    r[cp]['ops']=ops
    r[cp].update(anchors)

def poly(points):
    return fill('M'+'L'.join(f'{x:.6f} {y:.6f}' for x,y in points)+'Z')

def diagonal_w(stem,capital=False,mono=False):
    """Planar feet, relieved inner joins, locally lighter diagonal stress."""
    height=700 if capital else 520
    q=progress(stem)
    left=(36 if mono else -38 if capital else -15)
    foot=(132 if mono else 110 if capital else 116)
    # Black's central apex is lower and its converging strokes are relieved.
    peak=(500 if capital else 407)-q*(38 if capital else 40)
    effective=stem*(1-.17*q)
    normal=effective*.96
    half=effective*.5
    outer_slope=(foot-left)/height
    outer_band=normal*sqrt(1+outer_slope**2)
    foot_right=foot+effective
    a=320-half-foot_right
    disc=peak*peak+a*a-normal*normal
    if disc<=0:raise ValueError('Invalid W contour')
    inner_slope=(a*peak+normal*sqrt(disc))/(peak*peak-normal*normal)
    inner_band=normal*sqrt(1+inner_slope**2)
    jy=(foot+outer_band-foot_right+inner_band)/(outer_slope+inner_slope)
    jx=foot+outer_band-outer_slope*jy
    notch=peak+(half-inner_band)/inner_slope
    points=[(left,height),(left+outer_band,height),(jx,jy),
            (320-half,peak),(320+half,peak),(640-jx,jy),
            (640-left-outer_band,height),(640-left,height),
            (640-foot,0),(640-foot_right,0),(320,notch),(foot_right,0),(foot,0)]
    return [poly(points)]


def heavy_a(stem):
    q=progress(stem)
    left=112-stem/2;right=514+stem/2;il=112+stem/2;ir=514-stem/2
    crossbar=302+38*q
    top=528-(.9-.16*q)*stem
    floor=-8+(.9-.10*q)*stem
    innerbar=crossbar-(.9-.16*q)*stem
    tipx=111+stem*(.60-.12*q);tipy=440-stem*(.47-.04*q)
    outer=(f'M{right} 0H{ir}V70C432 19 389 -8 291 -8'
      f'C153 -8 {left} 45 {left} 146C{left} 247 167 {crossbar} 311 {crossbar}'
      f'H{ir}V334C{ir} 392 400 {top} 324 {top}'
      f'C249 {top} 211 {top-17} {tipx} {tipy}L111 440'
      f'C158 497 231 528 325 528C470 528 {right} 451 {right} 327V0Z')
    counter=(f'M{ir} {innerbar}H313'
      f'C230 {innerbar} {il} {innerbar-25} {il} {(floor+innerbar)/2}'
      f'C{il} {floor+17} 229 {floor} 289 {floor}'
      f'C376 {floor} {ir} {floor+30} {ir} {innerbar-17}V{innerbar}Z')
    return [fill(outer+' '+counter)]

def italic_a(stem):
    """A separately drawn single-storey italic; a stable straight right counter."""
    q=progress(stem)
    x0=110-stem/2;x1=512+stem/2;il=110+stem/2;ir=512-stem/2
    top=530-(.86-.06*q)*stem;bot=-9+(.86-.06*q)*stem
    outer=(f'M{ir} 520H{x1}V{stem*.45}H{x1+31}V0H{ir}V70'
      f'C425 13 373 -9 305 -9C153 -9 {x0} 91 {x0} 257'
      f'C{x0} 423 165 530 310 530C391 530 449 503 {ir} 450V520Z')
    counter=(f'M{ir} 320C{ir} 409 409 {top} 318 {top}'
      f'C226 {top} {il} 371 {il} 258C{il} 145 226 {bot} 317 {bot}'
      f'C408 {bot} {ir} 108 {ir} 199V320Z')
    return [fill(outer+' '+counter)]

def italic_r(stem,mono=False):
    """An angled terminal and a lean shoulder, with relieved heavy join."""
    q=progress(stem)
    x=150 if mono else 184
    l=x-stem/2;rr=x+stem/2;end=512 if mono else 450
    top=529;inner=top-(.84-.07*q)*stem
    d=(f'M{l} 0V520H{rr}V{441-25*q}'
       f'C{x+71} 502 {end-115} {top} {end-57} {top}'
       f'C{end-31} {top} {end-7} 525 {end+5} 516'
       f'L{end-12} {inner-11}'
       f'C{end-32} {inner-2} {end-50} {inner} {end-69} {inner}'
       f'C{x+71} {inner} {rr} 374 {rr} 284V0Z')
    return [fill(d)]

def italic_f(stem,mono=False):
    """Long italic f, a curved descending exit rather than a sheared upright."""
    h=.43*stem;x=310 if mono else 286
    return [stroke(f'M{x-150} {-220+h}H{x-121}C{x-40} {-220+h} {x} -143 {x} -48V561'
        f'C{x} 663 {x+56} {727-h} {x+130} {727-h}H{x+175}'),
        stroke(f'M{x-142} {520-h}H{x+139}',.83)]

def italic_t(stem,mono=False):
    h=.44*stem;x=288 if mono else 272
    return [stroke(f'M{x} 655V136C{x} 70 {x+43} {h-4} {x+117} {h-4}'
        f'C{x+159} {h-4} {x+179} {h+12} {x+192} {h+25}'),
        stroke(f'M{x-141} {520-h}H{x+154}',.82)]

def italic_l(stem,mono=False):
    h=.45*stem;x=290 if mono else 282
    return [stroke(f'M{x-82} {720-h}H{x}V121C{x} 59 {x+38} {h} {x+99} {h}H{x+143}')]

def heavy_controls(r,stem,family):
    """Explicit Black-end contour/space controls; no global stroke dilation."""
    q=progress(stem);mono=family=='mono'
    # The lower a counter cannot follow unbounded crossbar extrapolation.
    setops(r,'a',heavy_a(stem) if stem>90 else refined_glyphs.a_ops(stem,crossbar=292+10*min(1,(stem-72)/18)))
    if q:
        setops(r,'w',diagonal_w(stem,mono=mono))
        setops(r,'W',diagonal_w(stem,capital=True,mono=mono))
        # Relieve the spine at heavy weights without thinning vertical stems.
        setops(r,'s',refined_glyphs.s_ops(stem*(1-.10*q)),top=(312,575))
        # Preserve m's apertures: narrower joins than uprights.
        centers=(102,320,538) if mono else (112,430,748)
        x,y,z=centers;h=.42*stem;top=530-h
        setops(r,'m',[stroke(f'M{x} 0V520'),
            stroke(f'M{x} 323C{x} 435 {x+71} {top} {(x+y)/2+4} {top}'
                   f'C{y-37} {top} {y} 420 {y} 318V0',1-.09*q),
            stroke(f'M{y} 329C{y} 433 {y+75} {top} {(y+z)/2+5} {top}'
                   f'C{z-35} {top} {z} 420 {z} 315V0',1-.09*q)])
    # Controlled y strips maintain diagonal stress over the whole range.
    if stem not in (72,90):
        lo=74;ro=566;slope=.42;band=stem*sqrt(1+slope*slope)*(.97-.07*q)
        li=lo+band;ri=ro-band
        ly=(li+.425*520-ri+.420*520)/(.425+.420)
        lx=li+.425*(520-ly)
        by=(lo+.425*520-ri+.420*520)/(.425+.420)
        bx=lo+.425*(520-by)
        oy=-100;ox=ro+slope*(oy-520);iy=-78;ix=ri+slope*(iy-520)
        tail=-220+stem*.82
        d=(f'M{lo} 520H{li}L{lx} {ly}L{ri} 520H{ro}L{ox} {oy}'
           f'C{ox-68*slope} {oy-68} 222 -220 132 -220H77V{tail}H132'
           f'C190 {tail} {ix-48*slope} {iy-48} {ix} {iy}L{bx} {by}Z')
        setops(r,'y',[fill(d)],bottom=(240,-270))

def prepare_ascii(r,stem,family,italic):
    heavy_controls(r,stem,family)
    if not italic:return
    mono=family=='mono'
    setops(r,'a',italic_a(stem),top=(323,575),bottom=(312,-45))
    setops(r,'r',italic_r(stem,mono),top=(310,575),bottom=(260,-45))
    setops(r,'f',italic_f(stem,mono),top=(376,780),bottom=(204,-265),dotbelow=(204,-257))
    setops(r,'t',italic_t(stem,mono),top=(293,706),bottom=(343,-45))
    setops(r,'l',italic_l(stem,mono),top=(283,775),bottom=(365,-45))
    # An independently drawn italic e: forward open terminal and lifted eye.
    q=progress(stem);h=stem*.44
    setops(r,'e',[stroke(
        f'M520 132C478 70 409 {h-8} 321 {h-8}'
        f'C180 {h-8} 113 115 113 261C113 418 194 {530-h} 329 {530-h}'
        f'C459 {530-h} 517 405 517 {287+h/2}H139',1-.03*q)],
        top=(330,575))
    # Build subsequent accented components from these actual italic bases.

def prepare_extended(r,stem,family,italic):
    if not italic:return
    # Marked i/j must use these same dotless sources. Only the italic i grows
    # a modest exit; the existing j hook already has a designed text rhythm.
    h=.45*stem
    if family=='sans':
        r[0x131]['ops']=[stroke(f'M285 520V104C285 57 311 {h} 355 {h}H395')]
        r[0x131]['top']=(285,550);r[0x131]['bottom']=(322,-45)
        r[ord('i')]['ops']=[component(0x131),ellipse(285,658,stem*.53)]
        r[ord('i')]['top']=(285,740)
    # Every standalone mark has origin-based shear; base anchors include pivot.
    for cp,g in r.items():
        if g.get('mark') and g.get('top') is None and g.get('mark')=='above':
            g['top']=(0,175)

def slant(r,resolver):
    for cp,g in r.items():
        if is_cell(cp):continue
        mark=bool(g.get('mark') or g.get('width')==0)
        shift=0 if mark else -SHEAR*PIVOT
        matrix=[1,0,SHEAR,1,shift,0]
        resolver.cache[cp]=transformed(resolver.cache[cp],matrix)
        for k in ANCHORS:
            if g.get(k):
                x,y=g[k];g[k]=(x+SHEAR*y+shift,y)
        g['bounds']=list(bounds(resolver.cache[cp])) if g.get('bounds') else None

def configure_spacing(spacing,stem,italic):
    # Bounded sidebearing reduction: Black apertures do not justify erasing
    # exterior whitespace. Italic has its own classes after base fitting.
    old_fit=spacing.fit
    def fit(r,resolver,s):
        optical=72+min(30,max(-15,(s-72)*.45))
        return old_fit(r,resolver,optical)
    spacing.fit=fit
    if italic:
        spacing.BEARINGS['a']=(40,48)
        spacing.BEARINGS['f']=(28,26)
        spacing.BEARINGS['r']=(56,30)
        spacing.BEARINGS['t']=(35,35)
        spacing.BEARINGS['e']=(39,38)
        # Upright collision exceptions do not transfer to a new slant design.
        spacing.EXCEPTIONS={}
        for key,value in list(spacing.KERN.items()):
            spacing.KERN[key]=round(value*.55)
        spacing.KERN[('f',')')]=28
        spacing.KERN[('r','.')]=-30
