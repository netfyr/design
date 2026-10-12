"""Deterministic expansion of authored paths into editable font outlines.

FreeType's vector stroker expands authored centerlines; no font is loaded.
The stroker uses 1/64 design-unit coordinates. Outline formats are compiled
separately so the source remains independent of a rasterizer or font format.
"""
import ctypes as C
import ctypes.util
from copy import deepcopy
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path

def clean_contours(registry,resolver):
    from curve_boolean import batch, ENGINE_INFO
    originals={cp:resolver.cache[cp] for cp in registry if resolver.cache[cp].value}
    cleaned=batch(originals);report=[]
    for cp,r in cleaned.items():
        original=originals[cp]
        if not r.value:raise ValueError(f"Empty after curve union: {cp!r}")
        before=bounds(original);after=bounds(r)
        report.append({"glyph":str(cp),"bounds_shift":max(abs(a-b) for a,b in zip(before,after)),
                       "before_contours":len(split_contours(original)),"after_contours":len(split_contours(r))})
        resolver.cache[cp]=r;registry[cp]["bounds"]=list(after)
    return {"engine":dict(ENGINE_INFO),"glyphs":report}

class Vector(C.Structure):
    _fields_=[('x',C.c_long),('y',C.c_long)]

class Outline(C.Structure):
    _fields_=[('n_contours',C.c_short),('n_points',C.c_short),('points',C.POINTER(Vector)),('tags',C.POINTER(C.c_byte)),('contours',C.POINTER(C.c_short)),('flags',C.c_int)]

MoveFn=C.CFUNCTYPE(C.c_int,C.POINTER(Vector),C.c_void_p)
LineFn=MoveFn
ConicFn=C.CFUNCTYPE(C.c_int,C.POINTER(Vector),C.POINTER(Vector),C.c_void_p)
CubicFn=C.CFUNCTYPE(C.c_int,C.POINTER(Vector),C.POINTER(Vector),C.POINTER(Vector),C.c_void_p)
class OutlineFuncs(C.Structure):
    _fields_=[('move_to',MoveFn),('line_to',LineFn),('conic_to',ConicFn),('cubic_to',CubicFn),('shift',C.c_int),('delta',C.c_long)]

FT=C.CDLL(ctypes.util.find_library('freetype'))
def bind(name,args,ret=C.c_int):
    f=getattr(FT,name);f.argtypes=args;f.restype=ret;return f
init=bind('FT_Init_FreeType',[C.POINTER(C.c_void_p)])
new=bind('FT_Stroker_New',[C.c_void_p,C.POINTER(C.c_void_p)])
setting=bind('FT_Stroker_Set',[C.c_void_p,C.c_long,C.c_int,C.c_int,C.c_long],None)
begin=bind('FT_Stroker_BeginSubPath',[C.c_void_p,C.POINTER(Vector),C.c_ubyte])
line=bind('FT_Stroker_LineTo',[C.c_void_p,C.POINTER(Vector)])
quad=bind('FT_Stroker_ConicTo',[C.c_void_p,C.POINTER(Vector),C.POINTER(Vector)])
cubic=bind('FT_Stroker_CubicTo',[C.c_void_p,C.POINTER(Vector),C.POINTER(Vector),C.POINTER(Vector)])
end=bind('FT_Stroker_EndSubPath',[C.c_void_p])
counts=bind('FT_Stroker_GetCounts',[C.c_void_p,C.POINTER(C.c_uint),C.POINTER(C.c_uint)])
export=bind('FT_Stroker_Export',[C.c_void_p,C.POINTER(Outline)],None)
done=bind('FT_Stroker_Done',[C.c_void_p],None)
decompose=bind('FT_Outline_Decompose',[C.POINTER(Outline),C.POINTER(OutlineFuncs),C.c_void_p])
library=C.c_void_p()
assert init(C.byref(library))==0

def path_recording(d):
    p=RecordingPen();parse_path(d,p);return p

def split_contours(recording):
    contours=[];part=RecordingPen()
    for name,args in recording.value:
        if name=='moveTo' and part.value:
            part.closePath();contours.append(part);part=RecordingPen()
        getattr(part,name)(*args)
        if name in ('closePath','endPath'):
            contours.append(part);part=RecordingPen()
    if part.value:part.closePath();contours.append(part)
    return contours

def orient(recording):
    """Make the largest contour clockwise, retaining authored hole winding."""
    areas=[]
    for part in split_contours(recording):
        a=AreaPen(None);part.replay(a);areas.append(a.value)
    if areas and max(areas,key=abs)>0:
        out=RecordingPen();recording.replay(ReverseContourPen(out));return out
    return recording

def transformed(recording,matrix):
    out=RecordingPen();recording.replay(TransformPen(out,matrix))
    if matrix[0]*matrix[3]-matrix[1]*matrix[2]<0:
        normal=RecordingPen();out.replay(ReverseContourPen(normal));return normal
    return out

def bounds(recording):
    p=BoundsPen(None);recording.replay(p);return p.bounds

def expand_stroke(d,width,cap='butt',join='round',optical=True):
    source=path_recording(d);stroker=C.c_void_p()
    assert new(library,C.byref(stroker))==0
    yscale=.9 if optical else 1
    setting(stroker,round(width*32),{'butt':0,'round':1,'square':2}[cap],{'round':0,'bevel':1,'miter':2}[join],4*65536)
    def vec(p):return Vector(round(p[0]*64),round(p[1]*64/yscale))
    try:
        for contour in split_contours(source):
            closed=contour.value[-1][0]=='closePath'
            for command,args in contour.value:
                if command=='moveTo':
                    v=vec(args[0]);assert begin(stroker,C.byref(v),not closed)==0
                elif command=='lineTo':
                    v=vec(args[0]);assert line(stroker,C.byref(v))==0
                elif command=='curveTo':
                    if len(args)!=3:raise ValueError('Cubic requires three coordinates')
                    a,b,c=map(vec,args);assert cubic(stroker,C.byref(a),C.byref(b),C.byref(c))==0
                elif command=='qCurveTo':
                    if len(args)!=2:raise ValueError('Quadratic requires two coordinates')
                    a,b=map(vec,args);assert quad(stroker,C.byref(a),C.byref(b))==0
                elif command in ('endPath','closePath'):
                    assert end(stroker)==0
        np=C.c_uint();nc=C.c_uint();assert counts(stroker,C.byref(np),C.byref(nc))==0
        if np.value==0:return RecordingPen()
        points=(Vector*np.value)();tags=(C.c_byte*np.value)();ends=(C.c_short*nc.value)()
        outline=Outline(0,0,points,tags,ends,0);export(stroker,C.byref(outline))
        out=RecordingPen();open_contour=[False]
        def point(p):return (p.contents.x/64,p.contents.y/64*yscale)
        def moveto(p,_):
            if open_contour[0]:out.closePath()
            out.moveTo(point(p));open_contour[0]=True;return 0
        def lineto(p,_):out.lineTo(point(p));return 0
        def conicto(a,b,_):out.qCurveTo(point(a),point(b));return 0
        def cubicto(a,b,c,_):out.curveTo(point(a),point(b),point(c));return 0
        callbacks=OutlineFuncs(MoveFn(moveto),LineFn(lineto),ConicFn(conicto),CubicFn(cubicto),0,0)
        assert decompose(C.byref(outline),C.byref(callbacks),None)==0
        if open_contour[0]:out.closePath()
        return orient(out)
    finally:done(stroker)

class Resolver:
    def __init__(self,registry,weight):
        self.registry=registry;self.weight=weight;self.cache={};self.resolving=set()

    def _ops(self,ops):
        out=RecordingPen()
        for op in ops:
            kind=op['kind']
            if kind=='fill':part=orient(path_recording(op['d']))
            elif kind=='stroke':part=expand_stroke(op['d'],self.weight*op.get('width',1),op.get('cap','butt'),op.get('join','round'),op.get('optical',True))
            elif kind=='component':
                part=transformed(self.resolve(op['glyph']),op['transform'])
            elif kind=='group':part=transformed(self._ops(op['ops']),op['transform'])
            else:raise ValueError(f'Unknown outline operation: {kind}')
            part.replay(out)
        return out

    def flatten(self,cp):
        g=self.registry[cp]
        if g.get('decomposition'):
            seq=[]
            for part in g['decomposition']:seq.extend(self.flatten(part))
            return seq
        return [cp]

    def resolve(self,cp):
        if cp in self.cache:return self.cache[cp]
        if cp in self.resolving:raise ValueError(f'Circular component: {cp!r}')
        if cp not in self.registry:raise KeyError(f'Missing component {cp!r}')
        self.resolving.add(cp);g=self.registry[cp]
        if g.get('decomposition'):
            seq=self.flatten(cp)
            base=seq[0];marks=seq[1:]
            if base in (ord('i'),ord('j')) and any(self.registry[m].get('mark')=='above' for m in marks):
                base={ord('i'):0x0131,ord('j'):0x0237}[base]
            out=RecordingPen();self.resolve(base).replay(out)
            bg=self.registry[base]
            top=list(bg.get('top') or (320,755 if str(chr(base)).isupper() else 575))
            tone=list(bg.get('tone') or top)
            bottom=list(bg.get('bottom') or (320,-45))
            right=list(bg.get('right') or (510,510))
            ogonek=list(bg.get('ogonek') or bottom)
            dotbelow=list(bg.get('dotbelow') or bottom)
            below_placed=False
            for mark in marks:
                if base in (0x131,0x237) and self.registry[mark].get('narrow_alternate'):
                    mark=self.registry[mark]['narrow_alternate']
                if base in (ord('i'),ord('j'),ord('l'),0x131,0x237) and self.registry[mark].get('narrow_below_alternate'):
                    mark=self.registry[mark]['narrow_below_alternate']
                if mark==0x030C and base in (ord('d'),ord('l'),ord('t'),ord('L')) and 'caron.side' in self.registry:
                    mark='caron.side'
                if mark==0x0327 and base==ord('g') and 'cedilla.g' in self.registry:
                    mark='cedilla.g'
                elif mark==0x0327 and base in map(ord,'GKkLlNnRr') and 'cedilla.comma' in self.registry:
                    mark='cedilla.comma'
                mg=self.registry[mark];shape=self.resolve(mark);kind=mg.get('mark')
                anchor=ogonek if mg.get('attachment')=='ogonek' else (bottom if below_placed else dotbelow) if mg.get('attachment')=='dotbelow' else (tone if mg.get('use_stack_right') else top) if kind=='above' else bottom if kind=='below' else right if kind=='right' else [320,260]
                transformed(shape,[1,0,0,1,*anchor]).replay(out)
                if kind=='above':
                    cont=mg.get('top') or (0,(bounds(shape) or (0,0,0,90))[3]+35)
                    top=[anchor[0]+cont[0],anchor[1]+cont[1]]
                    off=mg.get('stack_right')
                    tone=[anchor[0]+off[0],anchor[1]+off[1]] if off else list(top)
                elif kind=='below':
                    cont=mg.get('bottom') or (0,(bounds(shape) or (0,-90,0,0))[1]-35)
                    bottom=[anchor[0]+cont[0],anchor[1]+cont[1]]
                    below_placed=True
            g['top']=tuple(top);g['bottom']=tuple(bottom);g['right']=tuple(right);g['ogonek']=tuple(ogonek);g['dotbelow']=tuple(bottom if below_placed else dotbelow)
            g['tone']=tuple(tone)
        else:out=self._ops(g.get('ops',[]))
        self.resolving.remove(cp);self.cache[cp]=out
        bb=bounds(out);g['bounds']=list(bb) if bb else None
        if g.get('top') is None and not g.get('mark'):
            g['top']=(320,(bb[3]+45 if bb else 575))
        if g.get('bottom') is None and not g.get('mark'):
            g['bottom']=(320,(bb[1]-45 if bb else -45))
        return out
