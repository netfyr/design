"""Authored monospace variants and deterministic fitting to a 640-unit cell.

M/m/W/w and the narrow coding letters have separate drawings. Broad extended
ligatures and digraphs are condensed only where needed, with horizontal stem
restoration. This operation runs before canonical mark composition, so a
precomposed letter and its live base/mark sequence use the same construction.
No pair kerning is applied to the mono family. Marks/controls remain zero width.
"""
import ctypes as C
import unicodedata as ud
from fontTools.pens.recordingPen import RecordingPen
from model import stroke,fill,component,ellipse,transform_ops
from refined_glyphs import w_ops,W_ops
from mono_u_horn import prepare_mono_u_horn
from outlines import Resolver,bounds,transformed,split_contours,orient,FT,Vector,Outline,OutlineFuncs,MoveFn,LineFn,ConicFn,CubicFn,decompose

CELL=640
INK_WIDTH=576
ANCHORS=('top','bottom','right','ogonek','dotbelow','overlay','tone')

def prepare_ascii(r,stem):
    h=.45*stem;top=520-h
    r[ord(' ')]['note']='Fixed 640-unit text space in the mono family.'
    def setops(c,ops):r[ord(c)]['ops']=ops
    setops('w',w_ops(stem,mono=True));setops('W',W_ops(stem,mono=True))
    # Hyphen-minus shares the coding operator axis of +, =, < and >.
    setops('-',[stroke('M205 300H435',.78)])
    # Three equal full-weight uprights and two independently drawn shoulders.
    setops('m',[stroke('M100 0V520'),
        stroke(f'M100 337C100 443 144 {top+7} 210 {top+7}C276 {top+7} 320 443 320 335V0'),
        stroke(f'M320 337C320 443 364 {top+7} 430 {top+7}C496 {top+7} 540 443 540 335V0')])
    setops('M',[stroke(f'M100 0V{700-h}L320 360L540 {700-h}V0',.98)])
    # A straight foot gives i a useful horizontal presence in a full cell.
    # The dotless base is replaced after extended-Latin registration below.
    setops('i',[component(0x131),ellipse(320,658,stem*.53)])
    setops('j',[component(0x237),ellipse(348,658,stem*.53)])
    setops('l',[stroke(f'M184 {720-h}H294V116C294 54 337 {h} 411 {h}H461')])
    setops('f',[stroke(f'M302 0V553C302 659 349 {720-h} 431 {720-h}H488'),
                stroke(f'M143 {top}H485')])
    setops('t',[stroke(f'M281 656V133C281 64 321 {h} 392 {h}H474'),
                stroke(f'M137 {top}H479')])
    # An open shoulder, with a broad enough reach for the fixed-width rhythm.
    left=136-stem/2;right=136+stem/2;it=528-.9*stem
    setops('r',[fill(f'M{left} 0V520H{right}V429'
        f'C238 501 311 528 396 528C444 528 484 518 518 496V{496-.9*stem}'
        f'C480 {it-14} 439 {it} 396 {it}C265 {it} {right} 389 {right} 274V0Z')])

def prepare_extended(r,stem):
    h=.45*stem
    prepare_mono_u_horn(r,stem)
    r[0x131]['ops']=[stroke(f'M198 {520-h}H320V{h}'),stroke(f'M179 {h}H461')]
    # Centre the hook before adding the dot. Fitting the component and then
    # adding a dot in its old coordinates would shift the dot off the stem.
    jdx=320-(175+348+stem/2)/2
    r[0x237]['ops']=transform_ops([stroke(f'M213 {520-h}H348V-75C348 -166 304 {-220+h} 221 {-220+h}H175')],dx=jdx)
    r[ord('j')]['ops']=[component(0x237),ellipse(348+jdx,658,stem*.53)]
    for cp in [ord('i'),0x131]:
        r[cp]['top']=(320,740 if cp==ord('i') else 550)
        r[cp]['bottom']=(320,-45);r[cp]['dotbelow']=(320,-35)
        r[cp]['ogonek']=(434,0)
    for cp in [ord('j'),0x237]:
        r[cp]['top']=(348+jdx,740 if cp==ord('j') else 550)
        r[cp]['bottom']=(270+jdx,-270);r[cp]['dotbelow']=(270+jdx,-255)
    r[ord('l')]['top']=(294,775);r[ord('l')]['bottom']=(320,-35)
    r[ord('l')]['dotbelow']=(320,-35)

def is_cell(cp):
    return isinstance(cp,int) and (0x2500<=cp<=0x259f or 0x2800<=cp<=0x28ff
             or 0xe0a0<=cp<=0xe0d7 or cp in (0xf8ff,0xe000))

def _normalise(p):
    from curve_boolean import one
    return one(p)

def _embolden_x(recording,strength):
    """Restore horizontal stem weight with FreeType's vector-only XY offset."""
    points=[];tags=[];ends=[]
    for contour in split_contours(recording):
        for command,args in contour.value:
            if command in ('moveTo','lineTo'):
                points.append(args[0]);tags.append(1)
            elif command=='curveTo':
                assert len(args)==3
                points.extend(args);tags.extend((2,2,1))
            elif command=='qCurveTo':
                assert len(args)==2 and args[-1] is not None
                points.extend(args);tags.extend((0,1))
        ends.append(len(points)-1)
    if not points:return recording
    pp=(Vector*len(points))(*(Vector(round(x*64),round(y*64)) for x,y in points))
    tt=(C.c_byte*len(tags))(*tags);ee=(C.c_short*len(ends))(*ends)
    outline=Outline(len(ends),len(points),pp,tt,ee,0)
    fn=FT.FT_Outline_EmboldenXY;fn.argtypes=[C.POINTER(Outline),C.c_long,C.c_long];fn.restype=C.c_int
    err=fn(C.byref(outline),round(strength*64),0)
    if err:raise ValueError(f'Horizontal stem restoration failed: {err}')
    out=RecordingPen();active=[False]
    def pt(p):return (p.contents.x/64,p.contents.y/64)
    def move(p,_):
        if active[0]:out.closePath()
        out.moveTo(pt(p));active[0]=True;return 0
    def line(p,_):out.lineTo(pt(p));return 0
    def conic(a,b,_):out.qCurveTo(pt(a),pt(b));return 0
    def cubic(a,b,c,_):out.curveTo(pt(a),pt(b),pt(c));return 0
    funcs=OutlineFuncs(MoveFn(move),LineFn(line),ConicFn(conic),CubicFn(cubic),0,0)
    if decompose(C.byref(outline),C.byref(funcs),None):raise ValueError('Offset outline could not be decomposed')
    if active[0]:out.closePath()
    return _normalise(orient(out))

class MonoResolver(Resolver):
    def __init__(self,registry,weight):
        super().__init__(registry,weight);self.fitted=set();self.mono_records=[]
    def resolve(self,cp):
        if cp in self.fitted:return self.cache[cp]
        out=super().resolve(cp);g=self.registry[cp]
        if g.get('mark') or g['width']==0:
            g['width']=0;self.fitted.add(cp);return out
        g['width']=CELL;g['fit_key']=None
        if g.get('decomposition') or is_cell(cp) or not out.value:
            self.fitted.add(cp);return out
        old=bounds(out);width=old[2]-old[0];sx=1.;strength=0.
        if width>600:
            # The equation sx*width + (1-sx)*stem = target keeps a vertical
            # stem at its original weight while fitting a broad form.
            sx=(INK_WIDTH-self.weight)/(width-self.weight)
            strength=(1-sx)*self.weight
            out=_embolden_x(transformed(_normalise(out),[sx,0,0,1,0,0]),strength)
        new=bounds(out)
        bias=4 if cp in [ord(c) for c in 'bhnp'] else -4 if cp in [ord('d'),ord('q')] else 0
        dx=320-(new[0]+new[2])/2+bias
        out=transformed(out,[1,0,0,1,dx,0])
        g.setdefault('overlay',(320,260))
        for anchor in ANCHORS:
            if g.get(anchor):g[anchor]=(g[anchor][0]*sx+strength/2+dx,g[anchor][1])
        g['bounds']=list(bounds(out));g['mono_scale_x']=sx;g['mono_restore_x']=strength
        g['mono_translation']=dx;self.cache[cp]=out;self.fitted.add(cp)
        self.mono_records.append({'glyph':str(cp),'source_bounds':old,'bounds':g['bounds'],
                 'x_scale':sx,'horizontal_stem_restoration':strength,'translation':dx})
        return out
