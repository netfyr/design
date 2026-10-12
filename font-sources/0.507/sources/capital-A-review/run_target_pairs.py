"""Parallel before/after pair checks for the repaired character set only.

Each changed code point appears before and after every encoded code point.
Repeated pairs are not counted twice. Profiles are an ink-envelope screen;
marks, controls, intended cell joins and complex runs are separate categories.
This is not an exhaustive optical review of the family or a vector collision
certificate. Old and new ordinary candidates are retained for comparison.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import subprocess,sys,json,time,os,hashlib,argparse,numpy as np
DT=np.dtype([('i','<u4'),('j','<u4'),('count','<u2'),('flags','<u2'),('gap','<i2'),('optical','<i2'),('kern','<i2'),('overlap_rows','<i2'),('advance','<i4')])
def worker(info,before,after,audit,tools):
 A=audit;SOURCE=tools
 name=info['file'];start=time.time()
 assert hashlib.sha256((after/name).read_bytes()).hexdigest()==info['sha256'], 'Stale invariant font hash'
 root=A/'pairs'/name[:-4];root.mkdir(parents=True,exist_ok=True);t=root/'targets.txt';t.write_text('\n'.join(map(str,info['changed']))+'\n');data={}
 for label,folder in [('before',before),('after',after)]:
  out=root/label;out.mkdir(exist_ok=True);font=folder/name
  with (out/'log.txt').open('w') as log:
   subprocess.run([sys.executable,str(SOURCE/'raster_profiles.py'),str(font),str(out)],stdout=log,stderr=subprocess.STDOUT,check=True)
   subprocess.run([str(tools/'target_pairs'),str(font),str(out/'profiles.bin'),str(out/'pairs.bin'),str(t)],stdout=log,stderr=subprocess.STDOUT,check=True)
  v=np.fromfile(out/'pairs.bin',dtype=DT,offset=24);j=json.loads((out/'individual-audit.json').read_text());cps=[x['decimal'] for x in j['characters']];data[label]=v
  assert j['sha256']==hashlib.sha256(font.read_bytes()).hexdigest()
 assert np.array_equal(data['before']['i'],data['after']['i']) and np.array_equal(data['before']['j'],data['after']['j'])
 a=data['before'];b=data['after'];ordinary=(b['flags']&(8|16|32|64))==0
 bad=ordinary&(b['gap']<0);new=bad&((a['gap']>=0)|(b['gap']<a['gap']-2));miss=(b['flags']&1)!=0
 rows=[]
 for k in np.flatnonzero(new):
  aa,bb=cps[int(b[k]['i'])],cps[int(b[k]['j'])]
  rows.append({'a':aa,'b':bb,'text':chr(aa)+chr(bb),'before_gap':int(a[k]['gap']),'after_gap':int(b[k]['gap']),'flags':int(b[k]['flags'])})
 advance_diff=int(np.count_nonzero(a['advance']!=b['advance']))
 expected_changes=[];unexpected_changes=[]
 for k in np.flatnonzero(a['advance']!=b['advance']):
  aa,bb=cps[int(b[k]['i'])],cps[int(b[k]['j'])];delta=int(b[k]['advance'])-int(a[k]['advance'])
  item={'a':aa,'b':bb,'delta':delta}
  approved=False
  (expected_changes if approved else unexpected_changes).append(item)
 result={'font':name,'process_id':os.getpid(),'started':start,'ended':time.time(),'sha256':info['sha256'],'before_sha256':hashlib.sha256((before/name).read_bytes()).hexdigest(),'characters':len(cps),'changed_characters':info['changed'],'ordered_pairs':len(b),'ordinary_pairs':int(ordinary.sum()),'missing':int(miss.sum()),'changed_run_advances':advance_diff,'expected_run_advance_changes':expected_changes,'unexpected_run_advance_changes':unexpected_changes,'ordinary_negative_before':int(((a['flags']&(8|16|32|64)==0)&(a['gap']<0)).sum()),'ordinary_negative_after':int(bad.sum()),'new_or_worse_negative_candidates':rows,'passed_screen':not rows and not miss.any() and not unexpected_changes}
 (root/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True)
 p.add_argument('--invariants',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--jobs',type=int,default=4);args=p.parse_args()
 if not 1<=args.jobs<=16:p.error('--jobs must be 1..16')
 A=args.output;A.mkdir(parents=True,exist_ok=True);tools=Path(__file__).resolve().parent
 if not (tools/'target_pairs').exists():
  subprocess.run(['cc','-O3','-Wall',str(tools/'target_pairs.c'),'-Wl,-l:libharfbuzz.so.0','-o',str(tools/'target_pairs')],check=True)
 inv=json.loads(args.invariants.read_text());jobs=[x for x in inv['files'] if x['changed']]
 with ProcessPoolExecutor(args.jobs) as p:
  results=[f.result() for f in as_completed([p.submit(worker,x,args.before,args.after,A,tools) for x in jobs])]
 report={'method':__doc__,'styles':results,'ordered_pairs':sum(v['ordered_pairs'] for v in results),'passed_screen':all(v['passed_screen'] for v in results),'software_workers_are_not_independent_reviewers':True}
 (A/'targeted-pairs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='styles'}))
