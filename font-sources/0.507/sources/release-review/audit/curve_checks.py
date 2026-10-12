"""Independent numeric checks of the delivered gamma construction.

Checks the underlying width polynomials, cubic approximation bounds,
unchanged source counters, endpoint tangent/curvature constraints, and the
actual compiled inner contours. This is a deterministic software review,
not a second typography designer's judgment.
"""
from pathlib import Path
import argparse,sys,json,hashlib,math,os,time
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.areaPen import AreaPen

def contours(font,cp,positive=False):
 p=RecordingPen();font.getGlyphSet()[font.getBestCmap()[cp]].draw(p)
 result=[];q=RecordingPen()
 for cmd,args in p.value:
  getattr(q,cmd)(*args)
  if cmd in ('closePath','endPath'):
   a=AreaPen(None);q.replay(a)
   if (not positive) or a.value>0:result.append(q.value)
   q=RecordingPen()
 return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--recipes',type=Path,required=True);ap.add_argument('--before',type=Path,required=True);ap.add_argument('--after',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
 sys.path.insert(0,str(args.recipes))
 from letter_repairs.gamma_transition import construction,CUBIC_ERROR_LIMIT
 from letter_repairs.loop_contours import gamma as oldgamma
 from outlines import Resolver,split_contours
 started=time.time();issues=[];models=[]
 for stem in [110,132,154]:
  for cp,data in [(0x194,(665,245,-8,305,105,515)),(0x263,(485,35,-220,320,105,535))]:
   outer,hole,record=construction(stem,*data)
   original=Resolver({},stem)._ops(oldgamma(stem,*data))
   original_holes=[]
   for c in split_contours(original):
    a=AreaPen(None);c.replay(a)
    if a.value>0:original_holes.append(c.value)
   from letter_repairs.gamma_transition import gamma as newgamma
   revised=Resolver({},stem)._ops(newgamma(stem,*data));new_holes=[]
   for c in split_contours(revised):
    a=AreaPen(None);c.replay(a)
    if a.value>0:new_holes.append(c.value)
   if original_holes!=new_holes:issues.append([stem,cp,'source hole differs'])
   for side,p in record['profiles'].items():
    a=np.polynomial.Polynomial(p['polynomial']);d=a.deriv();dy=p['y_end']-p['y_start']
    roots=[float(z.real) for z in d.roots() if abs(z.imag)<1e-7 and 1e-6<z.real<1-1e-6]
    if len(roots)!=1:issues.append([stem,cp,side,'extra extrema'])
    sign=1 if side=='right' else -1
    cx=record['oval']['cx']
    # A half-profile must stay strictly on its own side of the interior.
    xs=[float(a(t)) for t in [0,1]+roots]
    if min(sign*(x-cx) for x in xs)<=record['oval']['rx']:issues.append([stem,cp,side,'counter-side clearance'])
    if abs(p['start_d2x_dy2'])>1e-10 or abs(p['end_dx_dy'])>1e-10:issues.append([stem,cp,side,'endpoint constraint'])
    if p['max_source_approximation_error']>CUBIC_ERROR_LIMIT:issues.append([stem,cp,side,'approximation'])
    # Retain the signed curvature distribution for inspection; it is not an
    # invented optical quality score and does not certify the integer font.
    ts=np.linspace(0,1,2001);xp=d(ts)/dy;xpp=a.deriv(2)(ts)/dy**2
    curvature=xpp/(1+xp*xp)**1.5
    p['max_abs_profile_curvature']=float(np.max(np.abs(curvature)))
   models.append({'stem':stem,'cp':cp,'source_counter_identical':original_holes==new_holes,**record})
 compiled=[]
 for p in sorted(args.after.glob('*.ttf')):
  a=TTFont(args.before/p.name);b=TTFont(p)
  if b['OS/2'].usWeightClass<=600:continue
  for cp in [0x194,0x263,0x2e0]:
   same=contours(a,cp,True)==contours(b,cp,True)
   if not same:issues.append([p.name,cp,'compiled hole differs'])
   compiled.append({'font':p.name,'cp':cp,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'compiled_counter_exactly_identical':same})
 report={'passed':not issues,'issues':issues,'pid':os.getpid(),'started':started,'ended':time.time(),'models':models,'compiled_counters':compiled,'scope':__doc__}
 args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':not issues,'models':len(models),'compiled_counter_comparisons':len(compiled),'issues':issues}))
 if issues:raise SystemExit(1)
if __name__=='__main__':main()
