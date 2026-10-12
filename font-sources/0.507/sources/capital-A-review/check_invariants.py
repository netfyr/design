"""Compare every encoded drawing and layout table, not only displayed As."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.areaPen import AreaPen
import unicodedata as ud,json,hashlib,argparse,os,time

def rec(gs,gn):
 p=RecordingPen();gs[gn].draw(p);return p.value

def main():
 pa=argparse.ArgumentParser();pa.add_argument('--before',type=Path,required=True);pa.add_argument('--after',type=Path,required=True);pa.add_argument('--out',type=Path,required=True);ar=pa.parse_args()
 files=[];errors=[];started=time.time();areas={}
 for q in sorted(ar.after.glob('*.ttf')):
  a=TTFont(ar.before/q.name);b=TTFont(q);ca=a.getBestCmap();cb=b.getBestCmap();ga=a.getGlyphSet();gb=b.getGlyphSet()
  assert ca==cb
  active=b['OS/2'].usWeightClass>600
  allowed={cp for cp in cb if ud.normalize('NFD',chr(cp)).startswith('A')}|{0x391,0x20b3,0x213b,0x214d,0x23a}
  changed=[];nominal=[];bounds=[]
  for cp in cb:
   x,y=ca[cp],cb[cp]
   if rec(ga,x)!=rec(gb,y):
    changed.append(cp)
    if not active or cp not in allowed:errors.append([q.name,hex(cp),'unexpected outline change'])
   if a['hmtx'][x][0]!=b['hmtx'][y][0]:nominal.append(cp)
   g0=a['glyf'][x];g1=b['glyf'][y]
   if g0.numberOfContours and g1.numberOfContours and [g0.xMin,g0.yMin,g0.xMax,g0.yMax]!=[g1.xMin,g1.yMin,g1.xMax,g1.yMax]:bounds.append(cp)
  metrics_equal=a['hmtx'].metrics==b['hmtx'].metrics
  tables={t:a.getTableData(t)==b.getTableData(t) for t in ['GSUB','GPOS','GDEF']}
  if nominal or not metrics_equal:errors.append([q.name,'hmtx differences',nominal])
  if not all(tables.values()):errors.append([q.name,'layout tables differ',tables])
  # Counter changes may alter bounds of a clipped/overlaid derivative, so record
  # all bounds differences rather than silently granting an identical-bounds claim.
  p=AreaPen(gb);gb[cb[65]].draw(p);areas[(('mono' if 'mono' in q.name else 'sans'),bool(b['head'].macStyle&2),b['OS/2'].usWeightClass)]=abs(p.value)
  files.append(dict(file=q.name,sha256=hashlib.sha256(q.read_bytes()).hexdigest(),before_sha256=hashlib.sha256((ar.before/q.name).read_bytes()).hexdigest(),encoded=len(cb),changed=changed,changed_names=[ud.name(chr(c),'PRIVATE') for c in changed],advance_changes=nominal,hmtx_identical=metrics_equal,bounds_changes=bounds,layout_tables_identical=tables))
 progression=[]
 for fam in ['sans','mono']:
  for it in [False,True]:
   seq=[(w,areas[fam,it,w]) for w in [300,400,500,600,700,800,900]]
   passed=all(x[1]<y[1] for x,y in zip(seq,seq[1:]));progression.append(dict(family=fam,italic=it,weights_and_ink_areas=seq,strictly_increasing=passed))
   if not passed:errors.append([fam,it,'A ink mass is not increasing'])
 result=dict(passed=not errors,errors=errors,styles=len(files),encoded_cases=sum(f['encoded'] for f in files),changed_cases=sum(len(f['changed']) for f in files),files=files,A_ink_progression=progression,pid=os.getpid(),started=started,ended=time.time())
 ar.out.parent.mkdir(parents=True,exist_ok=True);ar.out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['files','A_ink_progression']},indent=2))
if __name__=='__main__':main()
