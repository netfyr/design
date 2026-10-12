"""Targeted counter corrections following the 0.500 optical audit.

Only weights above SemiBold are changed. No universal counter-area target is
imposed. The main b/d/p/q/o drawings, nominal metrics and cell graphics stay
untouched. The original Bézier exterior contours are retained; selected inner
contours are redrawn or enlarged, before component and mark composition.

This is a scoped counter correction, NOT a claim that the full extended
symbol repertoire passes optical review. See the accompanying issue ledger.
"""
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from outlines import Resolver,split_contours,bounds,transformed,path_recording
from model import fill,ellipse
from curve_boolean import one


def area(c):
    p=AreaPen(None);c.replay(p);return p.value

def parts(ops,stem):
    return split_contours(one(Resolver({},stem)._ops(ops)))

def holes(ops,stem):
    return [c for c in parts(ops,stem) if area(c)>.25]

def positive(c):
    if area(c)<0:
        p=RecordingPen();c.replay(ReverseContourPen(p));return p
    return c

def replace(ops,stem,newholes):
    # Keep the authored outer paths. Each retained inner is explicitly supplied,
    # so no overlapping positive hole is accidentally turned into ink.
    outer=[c for c in parts(ops,stem) if area(c)<-.25]
    p=SVGPathPen(None,ntos=lambda x:format(x,'.10g'))
    for c in outer:c.replay(p)
    for c in newholes:positive(c).replay(p)
    return [fill(p.getCommands())]

def vertical(c,lo,hi):
    bb=bounds(c);scale=(hi-lo)/(bb[3]-bb[1])
    return transformed(c,[1,0,0,scale,0,lo-scale*bb[1]])

def apply_ascii(r,stem,family,italic):
    if stem<=90:return
    q=min(1.,(stem-90)/64);delta=stem-90
    # A: coordinate the inner legs, crossbar and apex as one drawing.
    # The former isolated hole enlargement retained an almost vertical lower
    # opening at Black. The new recipe keeps the exterior design envelope.
    from capital_a_refinement import capital_a_ops
    r[ord('A')]['ops']=capital_a_ops(stem)
    # 8: the top bowl remains smaller. Only horizontal interior growth differs.
    orig=r[ord('8')]['ops'];out=[]
    for h in holes(orig,stem):
        bb=bounds(h);cy=(bb[1]+bb[3])/2;extra=.18*q*stem
        out.append(vertical(h,bb[1]-extra,bb[3]+extra))
    r[ord('8')]['ops']=replace(orig,stem,out)
    # e: three horizontal zones need separate contrast at the heavy end.
    orig=r[ord('e')]['ops'];h=holes(orig,stem)[0];bb=bounds(h)
    if italic:
        lo=bb[1]-.92*delta;hi=bb[3]+.27*delta
        left=113+stem/2+8;right=517-stem/2;mid=329
        d=(f'M{left} {lo}H{right}'
           f'C{right} {hi-30} 394 {hi} {mid} {hi}'
           f'C264 {hi} {left+17} {hi-25} {left} {lo}Z')
        h=positive(path_recording(d))
    else:h=vertical(h,bb[1]-.35*delta,bb[3]+.35*delta)
    r[ord('e')]['ops']=replace(orig,stem,[h])

def apply_extended(r,stem,family,italic):
    if stem<=90:return
    delta=stem-90
    # Ash: its left counter tracks the standalone double-storey a, not an
    # obsolete extrapolation. The independent right eye keeps its ligature width.
    orig=r[0xE6]['ops'];hs=sorted(holes(orig,stem),key=lambda c:bounds(c)[0]);new=[]
    from expansion_design import heavy_a
    ah=holes(heavy_a(stem),stem)[0]
    new.append(transformed(ah,[1,0,0,1,-194,0]))
    eh=hs[1];bb=bounds(eh);new.append(vertical(eh,bb[1]-.18*delta,bb[3]+.35*delta))
    r[0xE6]['ops']=replace(orig,stem,new)
    # OE: preserve the o interior; give the e eye the same heavy-end relief.
    orig=r[0x153]['ops'];new=[]
    for h in holes(orig,stem):
        bb=bounds(h)
        new.append(vertical(h,bb[1]-.35*delta,bb[3]+.35*delta) if bb[0]>300 else h)
    r[0x153]['ops']=replace(orig,stem,new)
    # A ring accent must remain visibly a ring rather than approach a solid dot.
    orig=r[0x30A]['ops'];h=holes(orig,stem)[0];bb=bounds(h)
    cx=(bb[0]+bb[2])/2;cy=(bb[1]+bb[3])/2
    target_w=57.5-.075*delta;target_h=64-.075*delta
    # Redraw the inner oval: scaling the nearly collapsed original contour
    # magnifies its offset cusps into a visibly angular counter.
    h=positive(path_recording(ellipse(cx,cy,target_w/2,target_h/2)['d']))
    r[0x30A]['ops']=replace(orig,stem,[h])
