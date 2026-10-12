from pathlib import Path
import math,io,json,functools
import cairo
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.cairoPen import CairoPen
from fontTools.pens.basePen import BasePen
class CanvasPen(BasePen):
 def __init__(self,canvas):
  super().__init__(None);self.path=canvas.beginPath()
 def _moveTo(self,p):self.path.moveTo(*p)
 def _lineTo(self,p):self.path.lineTo(*p)
 def _curveToOne(self,a,b,c):self.path.curveTo(*(a+b+c))
 def _closePath(self):self.path.close()
 def _endPath(self):pass
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RFont
from reportlab.lib.colors import HexColor
import argparse
ap=argparse.ArgumentParser(description='Render the compiled local .504/.505 fonts into this proof set.')
ap.add_argument('--before',type=Path,required=True)
ap.add_argument('--after',type=Path,required=True)
ap.add_argument('--output',type=Path,required=True)
args=ap.parse_args()
BEFORE=args.before;AFTER=args.after;OUT=args.output;P=OUT/'proofs';P.mkdir(parents=True,exist_ok=True)
INK='#211C19';PAPER='#F7F2EA';ORANGE='#AF4D10';MUTED='#695F58'
@functools.lru_cache(None)
def font(folder,name):return TTFont(Path(folder)/name)
@functools.lru_cache(None)
def record(folder,name,cp):
 f=font(folder,name);p=RecordingPen();f.getGlyphSet()[f.getBestCmap()[cp]].draw(p);return p

def rgb(h):return tuple(int(h[i:i+2],16)/255 for i in (1,3,5))

def glyph(ctx,folder,name,cp,x,y,em):
 ctx.save();ctx.translate(x,y);ctx.scale(em/1000,-em/1000);ctx.new_path();record(str(folder),name,cp).replay(CairoPen(None,ctx));ctx.set_source_rgb(*rgb(INK));ctx.fill();ctx.restore()

def pnglabel(im,text,x,y,size=28,color=INK):
 d=ImageDraw.Draw(im);f=ImageFont.truetype(str(AFTER/'netfyrsans-Regular.ttf'),size,layout_engine=ImageFont.Layout.RAQM);d.text((x,y),text,font=f,fill=color)

def pair_sheet():
 W,H=1600,960;s=cairo.ImageSurface(cairo.FORMAT_RGB24,W,H);c=cairo.Context(s);c.set_source_rgb(*rgb(PAPER));c.paint()
 n='netfyrmono-Black.ttf'
 for label,folder,y in [('0.504',BEFORE,450),('0.505',AFTER,825)]:
  for j,cp in enumerate([0x194,0x263]):glyph(c,folder,n,cp,320+j*610,y,380)
 data=io.BytesIO();s.write_to_png(data);im=Image.open(data).convert('RGB')
 pnglabel(im,'gamma junction',45,26,44)
 pnglabel(im,'netfyr mono Black  /  same em size and advances',45,91,26,MUTED)
 pnglabel(im,'U+0194',320,143,22,ORANGE);pnglabel(im,'U+0263',930,143,22,ORANGE)
 pnglabel(im,'0.504',45,320,32);pnglabel(im,'0.505',45,695,32)
 im.save(P/'netfyr-gamma-junction-before-after.png')

def weights_sheets():
 for family in ['sans','mono']:
  for italic in [False,True]:
   W,H=1500,930;s=cairo.ImageSurface(cairo.FORMAT_RGB24,W,H);c=cairo.Context(s);c.set_source_rgb(*rgb(PAPER));c.paint()
   for i,sty in enumerate(['Bold','ExtraBold','Black']):
    name=f'netfyr{family}-{sty}'+('Italic' if italic else '')+'.ttf'
    for row,folder in enumerate([BEFORE,AFTER]):
     for j,cp in enumerate([0x194,0x263]):glyph(c,folder,name,cp,125+i*460+j*185,435+row*365,280)
   q=io.BytesIO();s.write_to_png(q);im=Image.open(q).convert('RGB')
   pnglabel(im,f'netfyr {family}'+(' italic' if italic else ' upright'),40,28,36)
   pnglabel(im,'0.504 above / 0.505 below   ·   280 px/em',40,83,24,MUTED)
   for i,sty in enumerate(['Bold','ExtraBold','Black']):pnglabel(im,sty,145+i*460,151,26,ORANGE)
   pnglabel(im,'0.504',32,224,22);pnglabel(im,'0.505',32,589,22)
   im.save(P/(f'{family}-'+('italic' if italic else 'upright')+'-weights.png'))

def native():
 for family in ['sans','mono']:
  for italic in [False,True]:
   name=f'netfyr{family}-Black'+('Italic' if italic else '')+'.ttf'
   im=Image.new('RGB',(1350,990),PAPER);d=ImageDraw.Draw(im)
   pnglabel(im,f'netfyr {family} Black'+(' Italic' if italic else '')+' / native sizes',35,27,32)
   pnglabel(im,'0.504 left / 0.505 right. View at 100% for pixel-size comparisons.',35,78,23,MUTED)
   y=150
   for size in [16,24,32,48,64]:
    pnglabel(im,f'{size} px/em',35,y,20,ORANGE)
    for col,folder in enumerate([BEFORE,AFTER]):
     f=ImageFont.truetype(str(folder/name),size,layout_engine=ImageFont.Layout.RAQM)
     d.text((170+col*575,y),'oɣo dɣb ƔO OƔ',font=f,fill=INK)
     d.text((170+col*575,y+size+14),'Ɣɣ  nɣo  ˠ',font=f,fill=INK)
    y+=size*2+45
   im.save(P/(f'native-{family}-'+('italic' if italic else 'upright')+'.png'))

def report():
 for key,name in [('regular','netfyrsans-Regular.ttf'),('semi','netfyrsans-SemiBold.ttf')]:pdfmetrics.registerFont(RFont('netfyr-'+key,str(AFTER/name)))
 C=Canvas(str(OUT/'netfyr-gamma-junction.pdf'),pagesize=(595.276,841.89),initialFontName='netfyr-regular',initialFontSize=10,pageCompression=1,invariant=1)
 C.setTitle('netfyr 0.505 - gamma junction');C.setAuthor('netfyr design review')
 def rectbg():C.setFillColor(HexColor(PAPER));C.rect(0,0,595.276,841.89,fill=1,stroke=0)
 def text(s,x,y,size=10,font='regular',color=INK):C.setFillColor(HexColor(color));C.setFont('netfyr-'+font,size);C.drawString(x,841.89-y,s)
 def para(s,x,y,width,size=10,leading=14):
  lines=[];row=''
  for word in s.split():
   test=(row+' '+word).strip()
   if row and pdfmetrics.stringWidth(test,'netfyr-regular',size)>width:lines.append(row);row=word
   else:row=test
  if row:lines.append(row)
  for i,line in enumerate(lines):text(line,x,y+i*leading,size)
  return y+len(lines)*leading
 def fg(folder,name,cp,x,y,em):
  C.saveState();C.translate(x,841.89-y);C.scale(em/1000,em/1000);pen=CanvasPen(C);record(str(folder),name,cp).replay(pen);C.setFillColor(HexColor(INK));C.drawPath(pen.path,fill=1,stroke=0);C.restoreState()
 def footer(n):text('netfyr 0.505 · gamma junction',42,810,9,color=MUTED);text(str(n),545,810,9,color=MUTED)
 rectbg();text('Gamma junction',42,64,31,'semi');text('A smoother leg-to-loop transition',42,92,14,color=MUTED)
 text('0.504',42,219,12);text('0.505',42,413,12)
 for y,folder in [(295,BEFORE),(490,AFTER)]:
  fg(folder,'netfyrmono-Black.ttf',0x194,153,y,201)
  fg(folder,'netfyrmono-Black.ttf',0x263,359,y-30,201)
 text('U+0194',154,128,10,color=ORANGE);text('U+0263',360,128,10,color=ORANGE)
 text('netfyr mono Black · identical em size and advances',42,545,10,color=MUTED)
 text('The correction',42,581,15,'semi')
 para('The previous outer contour tightened abruptly at the neck. The revised contour starts turning earlier and carries the leg into the loop with a broader, more gradual transition.',42,604,510,10.8,15)
 text('Preserved',42,669,15,'semi')
 para('The oval counter, inner V, upper endpoints and lower half of the loop are unchanged. Mono æ/œ, the other letters, advance widths and existing layout tables are preserved.',42,692,510,10.8,15)
 para('Bold, ExtraBold and Black in Sans and Mono, upright and italic. The modifier gamma inherits the new contour. The 16 lighter styles are untouched.',42,747,510,9.7,13)
 footer(1);C.showPage()
 rectbg();text('Weight and slant',42,61,29,'semi');text('Final compiled outlines · 0.505',42,88,13,color=MUTED)
 for i,sty in enumerate(['Bold','ExtraBold','Black']):text(sty,160+i*132,123,11,'semi',ORANGE)
 for j,(fam,it,label) in enumerate([('sans',False,'Sans'),('sans',True,'Sans Italic'),('mono',False,'Mono'),('mono',True,'Mono Italic')]):
  base=218+j*122;text(label,42,base-22,10,'semi')
  for i,sty in enumerate(['Bold','ExtraBold','Black']):
   name=f'netfyr{fam}-{sty}'+('Italic' if it else '')+'.ttf'
   for k,cp in enumerate([0x194,0x263]):fg(AFTER,name,cp,149+i*132+k*60,base-(13 if cp==0x263 else 0),94)
 text('Construction and review',42,652,14,'semi')
 para('Each outer side uses an eased width profile, converted to cubic sections within 0.04 design units. The profile matches the incoming leg direction and the preserved lower bowl. Quadratic export rounding is checked separately.',42,674,510,10,14)
 para('The drawing principles are consistent tangents, controlled curvature and review at reading size. References: Glyphs, Drawing good paths; Glyphs, Spacing. The package records the tests and their limits.',42,734,510,9.8,13)
 footer(2);C.save()

if __name__=='__main__':
 pair_sheet();weights_sheets();native();report();print('Built actual-outline proofs and two-page netfyr report')
