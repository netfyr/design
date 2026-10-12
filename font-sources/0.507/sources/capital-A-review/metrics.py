from pathlib import Path
import sys,json,math
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen
W=Path(__import__('os').environ.get('NETFYR_REVIEW_WORK','.'));OUT=Path(__import__('os').environ.get('NETFYR_REVIEW_OUTPUT','./review'))
def measure(file):
 f=TTFont(file);gs=f.getGlyphSet();p=RecordingPen();gs[f.getBestCmap()[65]].draw(p)
 if f['head'].macStyle&2:
  q=RecordingPen();p.replay(TransformPen(q,(1,0,-math.tan(math.radians(10)),1,0,0)));p=q
 parts=[];q=RecordingPen()
 for cmd,args in p.value:
  getattr(q,cmd)(*args)
  if cmd in ['closePath','endPath']:
   a=AreaPen(None);q.replay(a);b=BoundsPen(None);q.replay(b);parts.append((a.value,b.bounds,q));q=RecordingPen()
 hole=next(v for v in parts if v[0]>0);outer=next(v for v in parts if v[0]<0)
 low=None;feet=[];nodes=[]
 last=None
 for cmd,args in outer[2].value:
  if cmd in ['moveTo','lineTo']:
   pt=args[0];nodes.append(pt)
   if last and cmd=='lineTo' and abs(pt[1]-last[1])<1e-5:
    if abs(pt[1])<1e-5:feet.append(abs(pt[0]-last[0]))
    elif 0<pt[1]<700:low=pt[1]
   last=pt
 # closePath is itself a segment; feet on the closure must be counted too.
 if nodes and abs(nodes[-1][1])<1e-5 and abs(nodes[0][1])<1e-5:feet.append(abs(nodes[-1][0]-nodes[0][0]))
 high=hole[1][1];bb=outer[1]
 return dict(cap_height=bb[3],source_ink_width=bb[2]-bb[0],counter_height=hole[1][3]-high,counter_bottom=high,counter_apex=hole[1][3],counter_area=hole[0],bar_bottom=low,bar_thickness=high-low,foot_bands=feet,ink_area=-sum(a for a,b,p in parts),advance=f['hmtx'][f.getBestCmap()[65]][0])
rows=[]
for q in sorted((W/'after/fonts').glob('*.ttf')):
 rows.append({'file':q.name,'before':measure(W/'before/fonts'/q.name),'after':measure(q)})
(OUT/'validation/measurements.json').write_text(json.dumps({'method':'Actual final quadratic outlines; italic outlines inverse-sheared for dimensional comparisons. Counter bounds and area measured analytically with FontTools pens. Foot bands are horizontal cuts at y=0, not vertical-stem weights.','styles':rows},indent=2)+'\n')
for r in rows:
 if r['file']=='netfyrmono-Black.ttf':print(json.dumps(r,indent=2))
