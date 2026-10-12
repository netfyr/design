#!/usr/bin/env python3
"""Render final-build proofs and an offline kit browser. No web fonts embedded."""
from pathlib import Path
import argparse, json, hashlib, concurrent.futures, base64, io, html
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1]
WEIGHTS={300:'Light',400:'Regular',500:'Medium',600:'SemiBold',700:'Bold',800:'ExtraBold',900:'Black'}

def one(job):
 fontdir,family,weight,italic,output=job
 label=WEIGHTS[weight];style=('Italic' if weight==400 else label+'Italic') if italic else label
 path=fontdir/f'netfyr{family}-{style}.ttf'
 body=fontdir/'netfyrsans-Regular.ttf'
 font=TTFont(path);cmap=font.getBestCmap()
 rows=[('clear ideas. exact shapes.',83,190),('agrswy  Ɣɣ  æœ',114,360),('A8B  O0  Δδ  Ææ  Œœ  ℙ⊜',69,500),('ǻ ắ ợ Ű ḷ ąę ďľť  |  0123456789',42,610),('state / desired state / plan / apply / reconcile',30,710),('→  ≠  ∉  ⊈   ░▒▓│ ▁▃▅▇█',42,805)]
 for text,_,_ in rows:
  missing={ord(c) for c in text if ord(c) not in cmap}
  assert not missing,(path,missing)
 images={}
 for dark in [False,True]:
  theme='dark' if dark else 'light'
  bg='#211C19' if dark else '#F7F2EA';ink='#F7F2EA' if dark else '#211C19';accent='#FF7A1A' if dark else '#AF4D10'
  im=Image.new('RGB',(1600,880),bg);d=ImageDraw.Draw(im)
  small=ImageFont.truetype(str(body),28,layout_engine=ImageFont.Layout.RAQM)
  title=f'netfyr {family} / {label}'+(' Italic' if italic else '')
  d.text((64,62),title,font=small,fill=accent,anchor='ls')
  d.text((1536,62),'0.506',font=small,fill=accent,anchor='rs')
  for text,size,y in rows:
   f=ImageFont.truetype(str(path),size,layout_engine=ImageFont.Layout.RAQM)
   box=d.textbbox((64,y),text,font=f,anchor='ls')
   assert box[0]>=32 and box[2]<=1568 and box[3]<=848,(title,text,box)
   d.text((64,y),text,font=f,fill=ink,anchor='ls')
  fn=f'netfyr-{family}-{style}-{theme}.png';target=output/fn
  im.save(target,optimize=True)
  images[theme]=f'proofs/styles/{fn}'
 return {'key':f'{family}-{weight}-{int(italic)}','images':images,'font_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'title':title}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fonts',type=Path,required=True);p.add_argument('--jobs',type=int,default=4);a=p.parse_args()
 out=ROOT/'proofs/styles';out.mkdir(parents=True,exist_ok=True)
 jobs=[(a.fonts,f,w,i,out) for f in ['sans','mono'] for w in WEIGHTS for i in [False,True]]
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:records=list(pool.map(one,jobs))
 frames={r['key']:r['images'] for r in records}
 options=''.join(f'<option value="{w}"'+(' selected' if w==400 else '')+f'>{w} / {n}</option>' for w,n in WEIGHTS.items())
 template=(ROOT/'sources/preview-template.html').read_text().replace('@@WEIGHTS@@',options).replace('@@FRAMES@@',json.dumps(frames,separators=(',',':')))
 assert '@@' not in template
 (ROOT/'preview.html').write_text(template)
 audit=ROOT/'validation/current';audit.mkdir(parents=True,exist_ok=True)
 (audit/'preview-binding.json').write_text(json.dumps({'version':'0.506','images_per_style':2,'style_count':len(records),'records':records,'font_payloads_embedded':False},indent=2)+'\n')
 print(json.dumps({'styles':len(records),'images':2*len(records),'preview':str(ROOT/'preview.html')}))
if __name__=='__main__':main()
