from pathlib import Path
from functools import lru_cache
import cairo,json,math,hashlib
from fontTools.ttLib import TTFont
from fontTools.pens.cairoPen import CairoPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.transformPen import TransformPen
from PIL import Image,ImageDraw,ImageFont
W=Path(__import__('os').environ.get('NETFYR_REVIEW_WORK','.'));OUT=Path(__import__('os').environ.get('NETFYR_REVIEW_OUTPUT','./review'));P=OUT/'proofs';P.mkdir(exist_ok=True)
PAPER='#F7F2EA';INK='#211C19';MUTED='#74665C';ORANGE='#AF4D10'
@lru_cache(None)
def ft(stage,name):return TTFont(W/stage/'fonts'/name)
@lru_cache(None)
def label(size=24,bold=False):return ImageFont.truetype(str(W/'after/fonts'/('netfyrsans-SemiBold.ttf' if bold else 'netfyrsans-Regular.ttf')),size,layout_engine=ImageFont.Layout.RAQM)
def surface(w,h):
 s=cairo.ImageSurface(cairo.FORMAT_ARGB32,w,h);c=cairo.Context(s);c.set_source_rgb(247/255,242/255,234/255);c.paint();return s,c
def draw_glyph(c,font,ch,x,baseline,scale,colour=INK):
 gs=font.getGlyphSet();gn=font.getBestCmap()[ord(ch)];c.save();c.translate(x,baseline);c.scale(scale,-scale);v=[int(colour[i:i+2],16)/255 for i in [1,3,5]];c.set_source_rgb(*v);gs[gn].draw(CairoPen(gs,c));c.fill();c.restore()
def save(s,path,labels):
 s.write_to_png(str(path));im=Image.open(path).convert('RGB');d=ImageDraw.Draw(im)
 for x,y,text,size,bold,col in labels:d.text((x,y),text,font=label(size,bold),fill=col)
 im.save(path,optimize=True)
# Four directly comparable Black shapes. No per-glyph scaling.
s,c=surface(1500,820);labels=[(30,18,'netfyr · capital A / 0.506',35,True,INK)]
for col,(fam,it) in enumerate([('sans',False),('sans',True),('mono',False),('mono',True)]):
 name=f'netfyr{fam}-Black'+('Italic' if it else '')+'.ttf'
 labels.append((col*375+36,76,f'{fam} Black'+(' Italic' if it else ''),26,False,INK))
 for row,stage in enumerate(['before','after']):
  font=ft(stage,name);g=font['glyf'][font.getBestCmap()[65]];scale=.345;cx=col*375+187.5;dx=cx-(g.xMin+g.xMax)*scale/2;baseline=385+row*350
  draw_glyph(c,font,'A',dx,baseline,scale)
  labels.append((col*375+36,110+row*350,'0.505' if stage=='before' else '0.506',22,False,MUTED))
labels.append((30,779,'Same 700-unit cap height and ink width. No per-letter normalization.',24,False,MUTED))
save(s,P/'netfyr-capital-a-before-after.png',labels)
# All weights, two columns of upright/italic before-after.
for fam in ['sans','mono']:
 s,c=surface(1200,1640);labels=[(30,16,f'netfyr {fam} · weight progression',32,True,INK)]
 for j,heading in enumerate(['0.505 upright','0.506 upright','0.505 italic','0.506 italic']):labels.append((210+j*235,65,heading,22,False,MUTED))
 for i,style in enumerate(['Light','Regular','Medium','SemiBold','Bold','ExtraBold','Black']):
  y=135+i*207;labels.append((30,y+48,style,24,True,INK))
  for j,(stage,it) in enumerate([('before',False),('after',False),('before',True),('after',True)]):
   sty=('Italic' if style=='Regular' else style+'Italic') if it else style
   f=ft(stage,f'netfyr{fam}-{sty}.ttf');g=f['glyf'][f.getBestCmap()[65]];scale=.21;dx=300+j*235-(g.xMin+g.xMax)*scale/2
   draw_glyph(c,f,'A',dx,y+153,scale)
 labels.append((30,1600,'Light through SemiBold are unchanged. Heavy ink mass still increases at every weight.',24,False,MUTED))
 save(s,P/f'{fam}-all-weights.png',labels)
# Native sizes: the text is rendered by Pillow/RAQM, no resizing of result.
for fam in ['sans','mono']:
 for it in [False,True]:
  name=f'netfyr{fam}-Black'+('Italic' if it else '')+'.ttf';im=Image.new('RGB',(1320,970),PAPER);d=ImageDraw.Draw(im)
  d.text((28,20),f'netfyr {fam} Black'+(' Italic' if it else '')+' / native-size proofs',font=label(31,True),fill=INK)
  d.text((100,74),'0.505',font=label(24),fill=MUTED);d.text((735,74),'0.506',font=label(24),fill=MUTED)
  y=143
  for px in [16,24,32,48,64]:
   d.text((24,y-10),str(px)+' px',font=label(22),fill=MUTED)
   for x,stage in [(115,'before'),(745,'after')]:
    font=ImageFont.truetype(str(W/stage/'fonts'/name),px,layout_engine=ImageFont.Layout.RAQM)
    d.text((x,y),'HAVA ÀÂÅ',font=font,fill=INK,anchor='ls')
    d.text((x,y+px*1.5),'A À Á Ā Ạ Ắ',font=font,fill=INK,anchor='ls')
   y+=int(px*3.5+30)
  d.text((28,925),'View at 100%. These text samples use actual font advances and native shaping.',font=label(24),fill=MUTED)
  im.save(P/f'native-{fam}-Black'+('Italic' if it else '')+'.png' if False else P/f'native-{fam}-Black{("Italic" if it else "")}.png',optimize=True)
# References, uniform cap height but each typeface retains own width.
references=[];s,c=surface(1440,675);labels=[(25,20,'Reference check / equal capital height, independent typeface widths',30,True,INK)]
refs=[('/usr/share/fonts/truetype/noto/NotoSans-Black.ttf','Noto Sans Black','Version 2.004'),('/usr/share/fonts/truetype/noto/NotoSansMono-Black.ttf','Noto Sans Mono Black','Version 2.006'),(str(W/'after/fonts/netfyrmono-Black.ttf'),'netfyr mono Black','Version 0.506')]
for col,(path,cap,version) in enumerate(refs):
 f=TTFont(path);gs=f.getGlyphSet();cm=f.getBestCmap();bp=BoundsPen(gs);gs[cm[65]].draw(bp);scale=300/bp.bounds[3];dx=col*480+240-(bp.bounds[0]+bp.bounds[2])*scale/2
 draw_glyph(c,f,'A',dx,480,scale);labels.append((col*480+30,96,cap,28,True,INK));labels.append((col*480+30,135,version,24,False,MUTED));references.append({'name':cap,'version':f['name'].getDebugName(5),'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'upem':f['head'].unitsPerEm,'bounds_A':bp.bounds,'comparison':'Same capital height; no width matching or reference contour import.'})
labels.extend([(25,542,'Compare the sloping lower opening, tall counter and relieved apex—not identical ratios.',25,False,INK),(25,586,'Noto samples are installed, version-identified references. They are not claimed to be current releases.',23,False,MUTED),(25,622,'Reference outlines were not copied. The corrected drawing uses netfyr’s existing 700-unit cap and 488-unit source footprint.',23,False,MUTED)])
save(s,P/'reference-comparison.png',labels);(OUT/'research/reference-inventory.json').write_text(json.dumps(references,indent=2)+'\n')
print('Proof PNGs complete')
