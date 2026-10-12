"""Full 28-style encoded-drawing comparison and metric/feature checks."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
import json,hashlib,argparse
TARGETS={0x194,0x263,0x2E0}
def record(f,gn):
 p=RecordingPen();f.getGlyphSet()[gn].draw(p);return p.value

def main():
 p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
 files=[];errors=[];count=0;changed=0
 for q in sorted(args.after.glob('*.ttf')):
  a=TTFont(args.before/q.name);b=TTFont(q);ca=a.getBestCmap();cb=b.getBestCmap();active=b['OS/2'].usWeightClass>600;mono='mono' in q.name;altered=[];advances=[]
  assert ca==cb
  for cp in cb:
   count+=1
   if a['hmtx'][ca[cp]][0]!=b['hmtx'][cb[cp]][0]:advances.append(cp)
   if record(a,ca[cp])!=record(b,cb[cp]):
    changed+=1;altered.append(cp)
    if not active or cp not in TARGETS or(cp in {0xE6,0x1E3,0x1FD,0x153} and not mono):errors.append([q.name,hex(cp),'untargeted change'])
  if advances:errors.append([q.name,'advance changed',advances])
  tables={tag:a.getTableData(tag)==b.getTableData(tag) for tag in ['GSUB','GPOS','GDEF']}
  expected_gpos=False
  if not tables['GSUB'] or not tables['GDEF'] or (not tables['GPOS'] and not expected_gpos):errors.append([q.name,'unexpected layout table change',tables])
  files.append({'file':q.name,'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'encoded':len(cb),'changed':altered,'advance_changes':advances,'layout_tables_identical':tables,'expected_gpos_followup':expected_gpos})
 result={'passed':not errors,'errors':errors,'styles':len(files),'encoded_cases':count,'changed_cases':changed,'files':files};args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))
if __name__=='__main__':main()
