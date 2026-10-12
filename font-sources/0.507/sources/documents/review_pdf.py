
from pathlib import Path
import sys,json,fitz,time,os
p=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(exist_ok=True)
d=fitz.open(p);rows=[];t=time.time()
for i,page in enumerate(d):
    pix=page.get_pixmap(matrix=fitz.Matrix(.8,.8),alpha=False)
    q=out/f'specimen-{i+1:03}.png';pix.save(q)
    text=page.get_text()
    names=sorted(set(f[3] for f in page.get_fonts()))
    spans=[s for b in page.get_text('dict')['blocks'] if 'lines'in b for l in b['lines'] for s in l['spans']]
    outside=[{'text':s['text'],'bbox':s['bbox']} for s in spans if s['bbox'][0]<0 or s['bbox'][1]<0 or s['bbox'][2]>page.rect.width+.5 or s['bbox'][3]>page.rect.height+.5]
    rows.append({'page':i+1,'render':str(q),'fonts':names,'outside_spans':outside,'chars':len(text)})
report={'pages':len(d),'all_pages_rendered':True,'seconds':time.time()-t,'pid':os.getpid(),'pages_data':rows}
(out/'render-audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:report[k] for k in ['pages','all_pages_rendered','seconds','pid']}))
