"""Raster profiles of the actual compiled outlines, without font substitution.

Cairo rasterizes the TTF quadratic paths at 500 pixels/em. Profiles sample ink
at 2 design-unit intervals and alpha >= 128. The test is a collision screen,
not an assertion of optical quality. Bounds and metrics come from the font.
"""
from pathlib import Path
import argparse,ctypes as C,ctypes.util,json,struct,unicodedata as ud,hashlib
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.recordingPen import RecordingPen

CA=C.CDLL(ctypes.util.find_library('cairo'))
def bind(n,args,ret=None):
    f=getattr(CA,n);f.argtypes=args;f.restype=ret;return f
surf=bind('cairo_image_surface_create',[C.c_int,C.c_int,C.c_int],C.c_void_p)
ctx=bind('cairo_create',[C.c_void_p],C.c_void_p)
destroy=bind('cairo_destroy',[C.c_void_p]);sdestroy=bind('cairo_surface_destroy',[C.c_void_p])
flush=bind('cairo_surface_flush',[C.c_void_p]);data=bind('cairo_image_surface_get_data',[C.c_void_p],C.POINTER(C.c_ubyte))
stride=bind('cairo_image_surface_get_stride',[C.c_void_p],C.c_int)
move=bind('cairo_move_to',[C.c_void_p,C.c_double,C.c_double]);line=bind('cairo_line_to',[C.c_void_p,C.c_double,C.c_double])
curve=bind('cairo_curve_to',[C.c_void_p]+[C.c_double]*6)
close=bind('cairo_close_path',[C.c_void_p]);fill=bind('cairo_fill',[C.c_void_p])
translate=bind('cairo_translate',[C.c_void_p,C.c_double,C.c_double]);scale=bind('cairo_scale',[C.c_void_p,C.c_double,C.c_double])
source=bind('cairo_set_source_rgba',[C.c_void_p]+[C.c_double]*4)
class CairoPen(BasePen):
    def __init__(self,gs,c):super().__init__(gs);self.c=c
    def _moveTo(self,p):move(self.c,*p)
    def _lineTo(self,p):line(self.c,*p)
    def _curveToOne(self,a,b,c):curve(self.c,*a,*b,*c)
    def _closePath(self):close(self.c)
    def _endPath(self):close(self.c)

YTOP=1800;YBOTTOM=-700;STEP=2;ROWS=(YTOP-YBOTTOM)//STEP
SENTINEL=30000
def render(gs,gn,bb):
    if bb is None:return None
    x0=int(np.floor(bb[0]/2))-2;y0=int(np.ceil(bb[3]/2))+2
    w=int(np.ceil(bb[2]/2))-x0+2;h=y0-int(np.floor(bb[1]/2))+2
    s=surf(2,w,h);c=ctx(s)
    translate(c,-x0,y0);scale(c,.5,-.5);source(c,1,1,1,1)
    gs[gn].draw(CairoPen(gs,c));fill(c);flush(s)
    a=np.ctypeslib.as_array(data(s),shape=(h*stride(s),)).reshape(h,stride(s))[:,:w].copy()
    destroy(c);sdestroy(s)
    return a,x0,y0

def char_flags(cp):
    cat=ud.category(chr(cp));flags=0
    if cat.startswith('M'):flags|=1
    if cat.startswith('Z') or cat=='Cf' or cp in (0x34F,0x2800):flags|=2
    if 0x2500<=cp<=0x259F or 0x2800<=cp<=0x28FF or 0xE0A0<=cp<=0xE0D7:flags|=4
    if cp in (0xF8FF,0xE000):flags|=8
    if ud.normalize('NFD',chr(cp))!=chr(cp):flags|=16
    return flags

def run(fontpath,out):
    out.mkdir(parents=True,exist_ok=True)
    tt=TTFont(fontpath);gs=tt.getGlyphSet();order=tt.getGlyphOrder();cmap=tt.getBestCmap()
    left=np.full((len(order),ROWS),SENTINEL,dtype='<i2')
    right=np.full((len(order),ROWS),-SENTINEL,dtype='<i2')
    bounds=np.zeros((len(order),4),dtype='<i2');adv=np.zeros(len(order),dtype='<i2');records=[]
    for gid,gn in enumerate(order):
        g=tt['glyf'][gn];adv[gid]=tt['hmtx'][gn][0]
        bb=[g.xMin,g.yMin,g.xMax,g.yMax] if g.numberOfContours else None
        if bb:bounds[gid]=bb
        image=render(gs,gn,bb)
        ink=0
        if image:
            a,x0,y0=image;mask=a>=128;valid=mask.any(axis=1);indices=np.flatnonzero(valid)
            target=YTOP//2-y0+indices
            if len(target) and (target[0]<0 or target[-1]>=ROWS):raise ValueError(('outside declared profile range',gn,bb))
            l=mask.argmax(axis=1);r=mask.shape[1]-mask[:,::-1].argmax(axis=1)
            left[gid,target]=2*(x0+l[indices]);right[gid,target]=2*(x0+r[indices])
            ink=int(mask.sum())
        rp=RecordingPen();gs[gn].draw(rp);areas=[];ap=AreaPen(gs)
        for op,args in rp.value:
            getattr(ap,op)(*args)
            if op=='closePath':areas.append(round(ap.value-sum(areas),4))
        records.append(dict(gid=gid,glyph=gn,advance=int(adv[gid]),bounds=bb,
                            contours=g.numberOfContours,ink_pixels=ink,contour_areas=areas,
                            tiny_contours=sum(abs(v)<1 for v in areas)))
    cps=sorted(cmap);ids={gn:i for i,gn in enumerate(order)}
    with (out/'profiles.bin').open('wb') as f:
        f.write(struct.pack('<6i',len(order),len(cps),ROWS,YTOP,YBOTTOM,STEP))
        f.write(np.array(cps,dtype='<u4').tobytes())
        f.write(np.array([char_flags(cp) for cp in cps],dtype='<u2').tobytes())
        f.write(np.array([ids[cmap[cp]] for cp in cps],dtype='<u2').tobytes())
        f.write(adv.tobytes());f.write(bounds.tobytes());f.write(left.tobytes());f.write(right.tobytes())
    char_records=[]
    for cp in cps:
        rec=dict(records[ids[cmap[cp]]]);rec.update(codepoint=f'U+{cp:04X}',decimal=cp,
            character=chr(cp),name=ud.name(chr(cp),'PRIVATE USE'),category=ud.category(chr(cp)),flags=char_flags(cp))
        char_records.append(rec)
    report=dict(font=str(fontpath),sha256=hashlib.sha256(fontpath.read_bytes()).hexdigest(),
                method='Cairo actual TTF outlines; 500 px/em; alpha threshold 128; 2-unit sample grid',
                glyphs=records,characters=char_records)
    (out/'individual-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(dict(font=fontpath.name,characters=len(cps),glyphs=len(order),
                          tiny_contours=[r['glyph'] for r in records if r['tiny_contours']])))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('font',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();run(a.font,a.out)
