"""Native 20 px individual glyph phases, explicit cmap references and traced hashes."""
import argparse,json,sys,unicodedata
from pathlib import Path
import cairo
from PIL import Image,ImageDraw,ImageFont
release=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(release/'sources'));import review_glyphs as review
p=argparse.ArgumentParser();p.add_argument('--fonts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--codepoints');a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=True)
rows=[json.loads(x) for x in (release/'review/symbols.jsonl').read_text().splitlines()]
cps=[int(x,16) for x in a.codepoints.split(',')] if a.codepoints else [int(r['code'][2:],16) for r in rows if r['verdict']=='repair']
fontpaths=[]
for weight,name in review.WEIGHTS:
 for fam,slant in [('sans',False),('sans',True),('mono',False),('mono',True)]:
  suffix='Italic' if name=='Regular' and slant else name+('Italic' if slant else '')
  fontpaths.append((f'{fam} {weight}'+(' Italic' if slant else ''),a.fonts/f'netfyr{fam}-{suffix}.ttf'))
label=ImageFont.truetype('/usr/share/fonts/noto/NotoSans-Regular.ttf',14)
for cp in cps:
 refs=[]
 for title,path in [('DejaVu Bold','/usr/share/fonts/TTF/DejaVuSans-Bold.ttf'),('Noto Sans Bold','/usr/share/fonts/noto/NotoSans-Bold.ttf')]+review.REFERENCES:
  if cp in review.font(str(path))._review_cmap:
   refs.append((title,Path(path)))
   if len(refs)==4:break
 im=Image.new('RGB',(1380,990),'white');d=ImageDraw.Draw(im);d.text((12,8),f'U+{cp:04X} {unicodedata.name(chr(cp), "PROJECT PRIVATE USE")} | actual 20 px/em, nearest x2; phases 0/.25/.5/.75',font=label,fill='black')
 cases=[]
 for idx,(title,path) in enumerate(fontpaths+refs):
  row,col=divmod(idx,4);left=40+col*335;top=40+row*115
  d.text((left,top),title,font=label,fill='black')
  for phaseidx,phase in enumerate([0,.25,.5,.75]):
   surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,40,40);ctx=cairo.Context(surface);ctx.set_source_rgb(1,1,1);ctx.paint();ctx.set_source_rgb(0,0,0);review.draw_direct(ctx,str(path),cp,phase,28,20,38)
   surface.write_to_png(str(a.output/'temp.png'));pic=Image.open(a.output/'temp.png').convert('RGB').resize((80,80),Image.Resampling.NEAREST);im.paste(pic,(left+phaseidx*80,top+22))
  detail=review.details(str(path),cp);bounds=detail['bounds'];pixel_bounds=None
  if bounds:
   scale=20/detail['upem'];origin=(38-detail['advance']*scale)/2
   pixel_bounds=[origin+bounds[0]*scale,28-bounds[3]*scale,origin+bounds[2]*scale+.75,28-bounds[1]*scale]
   assert min(pixel_bounds[:2])>=0 and max(pixel_bounds[2:])<=40,(cp,title,pixel_bounds)
  cases.append({'font':str(path),'sha256':review.sha(path),'reference':idx>=28,'pixel_bounds':pixel_bounds})
 dest=a.output/f'U{cp:04X}-native.png';im.save(dest)
 (a.output/f'U{cp:04X}-native.json').write_text(json.dumps({'code':f'U+{cp:04X}','inspected_styles':28,'font_size':20,'raster_scale':2,'phases':[0,.25,.5,.75],'proof_sha256':review.sha(dest),'fonts':cases},indent=2)+'\n')
 print(f'U+{cp:04X}',flush=True)
(a.output/'temp.png').unlink(missing_ok=True)
