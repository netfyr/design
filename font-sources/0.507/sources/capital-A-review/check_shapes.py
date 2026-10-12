"""Per-family/slant counter and ink checks; software workers, not independent critics.

Scope: compiled counter topology, ink connectivity, sampled sizes,
full-family drawing isolation and advances. Sampling does not certify every
renderer or optical spacing. Records retain all failures and font hashes.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.cairoPen import CairoPen
from fontTools.pens.areaPen import AreaPen
import numpy as np,cairo,json,time,os,hashlib,math,argparse
from scipy import ndimage as ndi
CP={0x41:[0x41]}

def rec(f,cp):
 p=RecordingPen();f.getGlyphSet()[f.getBestCmap()[cp]].draw(p);return p

def plain(p,italic):
 q=RecordingPen();p.replay(TransformPen(q,(1,0,-math.tan(math.radians(10)),1,math.tan(math.radians(10))*260,0)) if italic else q);return q

def raster(p,size=500,phase=(0,0),box=(-200,-300,900,1050)):
 k=size/1000;x0,y0,x1,y1=box;w=math.ceil((x1-x0)*k)+8;h=math.ceil((y1-y0)*k)+8
 s=cairo.ImageSurface(cairo.FORMAT_A8,w,h);c=cairo.Context(s);c.translate(4-x0*k+phase[0],4+y1*k+phase[1]);c.scale(k,-k);p.replay(CairoPen(None,c));c.set_source_rgba(1,1,1,1);c.fill();s.flush()
 a=np.frombuffer(s.get_data(),np.uint8).reshape(h,s.get_stride())[:,:w].copy();return a

def topology(p,size=500,phase=(0,0)):
 a=raster(p,size,phase);ink=a>=128;wh=ndi.binary_fill_holes(ink)&~ink;labels,n=ndi.label(wh);s=1000/size
 holes=[]
 for i in range(1,n+1):
  yy,xx=np.where(labels==i);area=len(xx)*s*s
  holes.append({'area':round(area,5),'width':(xx.max()-xx.min()+1)*s,'height':(yy.max()-yy.min()+1)*s})
 return {'ink_components':int(ndi.label(ink,np.ones((3,3),bool))[1]),'raw_holes':n,'significant_holes':sum(x['area']>=32 for x in holes),'holes':holes}

def contours(p):
 q=RecordingPen();out=[]
 for cmd,args in p.value:
  getattr(q,cmd)(*args)
  if cmd in ('closePath','endPath'):
   a=AreaPen(None);q.replay(a);out.append(a.value);q=RecordingPen()
 return out

def worker(cp,before,after,out,family,italic_group):
 start=time.time();cases=[];errors=[]
 for file in sorted(after.glob('*.ttf')):
  a=TTFont(before/file.name);b=TTFont(file);weight=b['OS/2'].usWeightClass;italic=bool(b['head'].macStyle&2);ismono='mono' in file.name
  if ('mono' if ismono else 'sans')!=family or italic!=italic_group:continue
  active=weight>600 and (cp not in [0xE6,0x153] or ismono)
  for char in CP[cp]:
   pa=rec(a,char);pb=rec(b,char);old=topology(pa);new=topology(pb)
   if active:
    if new['significant_holes']!=(2 if cp in [0xE6,0x153] else 1):errors.append([file.name,hex(char),'counter topology',new])
    if char==cp and new['ink_components']!=1:errors.append([file.name,hex(char),'disconnected ink'])
   sa=[]
   if active and char==cp:
    for size in [16,24,32,48,64]:
     before_vals=[];after_vals=[]
     for x in (0,.25,.5,.75):
      for y in (0,.25,.5,.75):before_vals.append(topology(pa,size,(x,y)));after_vals.append(topology(pb,size,(x,y)))
     expected=2 if cp in [0xE6,0x153] else 1
     sa.append({'px_per_em':size,'placements':16,'before_hole_counts':[x['raw_holes'] for x in before_vals],'after_hole_counts':[x['raw_holes'] for x in after_vals],'before_counter_survival':sum(x['raw_holes']>=expected for x in before_vals),'after_counter_survival':sum(x['raw_holes']>=expected for x in after_vals),'before_ink_survival':sum(x['ink_components']==1 for x in before_vals),'after_ink_survival':sum(x['ink_components']==1 for x in after_vals)})
   item={'file':file.name,'cp':char,'active':active,'before':old,'after':new,'after_contour_areas':contours(pb),'size_proofs':sa}

   cases.append(item)
 out.mkdir(exist_ok=True,parents=True);result={'cp':cp,'family':family,'italic':italic_group,'character':chr(cp),'pid':os.getpid(),'started':start,'ended':time.time(),'passed':not errors,'errors':errors,'cases':cases}
 (out/f'U{cp:04X}-{family}-{"italic" if italic_group else "upright"}.json').write_text(json.dumps(result,indent=2));return {k:result[k] for k in ['cp','pid','started','ended','passed','errors']}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path,required=True);ap.add_argument('--after',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(exist_ok=True,parents=True)
 with ProcessPoolExecutor(max_workers=4) as pool:
  jobs=[pool.submit(worker,cp,a.before,a.after,a.out,fam,it) for cp in CP for fam in ['sans','mono'] for it in [False,True]];results=[f.result() for f in as_completed(jobs)]
 (a.out/'jobs.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
if __name__=='__main__':main()
