from pathlib import Path
import json,math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RLFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.colors import HexColor
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
class CanvasPen(BasePen):
 def __init__(self,gs):
  super().__init__(gs);self.path=c.beginPath()
 def _moveTo(self,p):self.path.moveTo(*p)
 def _lineTo(self,p):self.path.lineTo(*p)
 def _curveToOne(self,p1,p2,p3):self.path.curveTo(*p1,*p2,*p3)
 def _closePath(self):self.path.close()
 def _endPath(self):pass
from fontTools.pens.boundsPen import BoundsPen
from functools import lru_cache
W=Path(__import__('os').environ.get('NETFYR_REVIEW_WORK','.'));OUT=Path(__import__('os').environ.get('NETFYR_REVIEW_OUTPUT','./review'));P=OUT/'proofs'
CW,CH=595.276,841.89;M=42;RIGHT=CW-M
INK=HexColor('#211C19');PAPER=HexColor('#F7F2EA');MUTED=HexColor('#73675D');RULE=HexColor('#D8CFC4');ACC=HexColor('#AF4D10')
for k,sty in [('R','Regular'),('B','SemiBold')]:pdfmetrics.registerFont(RLFont('netfyr-'+k,str(W/'after/fonts'/f'netfyrsans-{sty}.ttf')))
pdfmetrics.registerFontFamily('netfyr-R',normal='netfyr-R',bold='netfyr-B',italic='netfyr-R',boldItalic='netfyr-B')
c=canvas.Canvas(str(OUT/'netfyr-capital-a-review.pdf'),pagesize=(CW,CH),initialFontName='netfyr-R',initialFontSize=10,invariant=True,pageCompression=1)
c.setTitle('netfyr 0.506 — capital A review');c.setAuthor('netfyr');c.setSubject('Targeted capital A geometry, references and finite validation')
checks=[]
def txt(t,x,y,size=10,bold=False,color=INK):
 c.setFillColor(color);c.setFont('netfyr-B' if bold else 'netfyr-R',size);c.drawString(x,CH-y,t)
 checks.append({'page':c.getPageNumber(),'text':t,'x':x,'baseline_from_top':y,'width':pdfmetrics.stringWidth(t,'netfyr-B' if bold else 'netfyr-R',size)})
def paragraph(t,x,y,width,size=11,leading=15,color=INK):
 p=Paragraph(t,ParagraphStyle('body',fontName='netfyr-R',fontSize=size,leading=leading,textColor=color))
 aw,h=p.wrap(width,CH);p.drawOn(c,x,CH-y-h);checks.append({'page':c.getPageNumber(),'paragraph':t,'box':[x,y,x+width,y+h]});return y+h
def line(y):c.setStrokeColor(RULE);c.setLineWidth(.6);c.line(M,CH-y,RIGHT,CH-y)
def page(n,title,subtitle):
 c.setFillColor(PAPER);c.rect(0,0,CW,CH,fill=1,stroke=0)
 txt('netfyr',M,30,10,True);txt('0.506 / capital A',CW-164,30,9,color=MUTED)
 txt(title,M,80,28,True);paragraph(subtitle,M,98,CW-2*M,10.4,14,MUTED)
 line(790);txt('Drawing review · source-and-proof release',M,812,8.5,color=MUTED);txt(str(n)+' / 3',CW-63,812,8.5,color=MUTED)
def image(path,x,y,width):
 from PIL import Image
 im=Image.open(path);h=width*im.height/im.width;c.drawImage(str(path),x,CH-y-h,width=width,height=h);return y+h
@lru_cache(None)
def font(stage,name):return TTFont(W/stage/'fonts'/name)
def glyph(stage,name,ch,cx,baseline,cap):
 f=font(stage,name);gs=f.getGlyphSet();gn=f.getBestCmap()[ord(ch)];bp=BoundsPen(gs);gs[gn].draw(bp);scale=cap/700
 pen=CanvasPen(gs);gs[gn].draw(pen);c.saveState();c.setFillColor(INK);c.translate(cx-(bp.bounds[0]+bp.bounds[2])*scale/2,CH-baseline);c.scale(scale,scale);c.drawPath(pen.path,fill=1,stroke=0);c.restoreState()
# 1: inspect the actual heavy drawing.
page(1,'A, proportioned as a whole','The two negative spaces, diagonals and apex are adjusted together. The cap height, outside width and spacing remain unchanged.')
for col,(fam,it) in enumerate([('sans',False),('sans',True),('mono',False),('mono',True)]):
 cx=M+64+col*128;name=f'netfyr{fam}-Black'+('Italic' if it else '')+'.ttf'
 txt(fam+' Black'+(' Italic' if it else ''),M+col*128,156,9.1,True)
 txt('0.505',M+col*128,179,9,color=MUTED);glyph('before',name,'A',cx,276,80)
 txt('0.506',M+col*128,305,9,color=MUTED);glyph('after',name,'A',cx,405,80)
line(434);txt('Mono Black / measured final outlines',M,458,13,True)
vals=[('Capital height','700','700'),('Counter height','201','309'),('Crossbar top','314','256'),('Crossbar thickness','138','116'),('Foot band, horizontal','169','139')]
txt('0.505',350,458,10,True);txt('0.506',445,458,10,True)
for i,(label,a,b) in enumerate(vals):
 y=485+i*23;txt(label,M,y,10.5);txt(a,350,y,10.5);txt(b,445,y,10.5,True);line(y+8)
paragraph('Dimensions are design units in a 1,000-unit em. They describe this drawing; they are not universal ratios or a rule that all strokes must be equal.',M,611,511,10.1,14,MUTED)
paragraph('<b>What was repaired.</b> The former counter enlargement kept an almost vertical lower opening and a congested apex. The new lower legs slope; the crossbar sits lower; the curved counter sides relieve the join. The ink mass still increases from Light to Black.',M,659,511,11,15)
paragraph('Gammas, Mono æ/œ, the flame and the terminal graphics are untouched.',M,744,511,10.5,14)
c.showPage()
# 2: every weight in the identical scale.
page(2,'A consistent weight ladder','Same cap height in every sample. In each pair: 0.505 at left, 0.506 at right. The 16 lighter styles retain their drawings.')
heads=['Sans upright','Sans italic','Mono upright','Mono italic']
for i,h in enumerate(heads):txt(h,107+i*112,157,9.5,True)
for row,(sty,weight) in enumerate([('Light',300),('Regular',400),('Medium',500),('SemiBold',600),('Bold',700),('ExtraBold',800),('Black',900)]):
 y=177+row*78;txt(str(weight),M,y+25,11,True);txt(sty,M,y+41,7.9,color=MUTED)
 for col,(fam,it) in enumerate([('sans',False),('sans',True),('mono',False),('mono',True)]):
  style=('Italic' if sty=='Regular' else sty+'Italic') if it else sty;name=f'netfyr{fam}-{style}.ttf'
  for off,stage in [(0,'before'),(48,'after')]:glyph(stage,name,'A',127+col*112+off,y+56,42)
 if row<6:line(y+70)
paragraph('The heavy-end drawing uses a separate optical progression anchored to SemiBold—not a uniform scale applied to an existing hole. The exact earlier upright Regular and SemiBold references are preserved.',M,737,511,10.3,14)
c.showPage()
# 3: primary references and honest validation.
page(3,'Reference, then test','The reference check compares structure at equal capital height. Different typefaces retain their own widths and contrast models.')
image(P/'reference-comparison.png',M,147,511)
paragraph('<b>Design basis.</b> OH no’s A lesson treats the upper counter, lower opening and joint weight as one optical problem. Glyphs’ guidance supports glyph-specific corrections across a wide weight range, rather than global scaling. [1–2]',M,405,511,10.7,14.5)
line(476);txt('Verified in the final builds',M,500,13,True)
paragraph('432 changed character/style cases, all belonging to A or components that reuse it. All 62,300 encoded cases were compared. Advances, bounds and GSUB/GPOS/GDEF tables are unchanged. Ink area rises at every weight.',M,515,246,10.1,14)
paragraph('960 A size/placement samples at 16–64 px/em retain the counter and connected ink. A targeted 1,906,848-pair screen per stage finds no new or worsened ordinary negative-gap candidates.',309,515,244,10.1,14)
paragraph('These are concurrent software checks, not independent typography reviewers. They do not certify every renderer, longer mark cluster or optical pair; no hinting or Google Fonts acceptance is claimed.',M,602,511,9.8,13.5,MUTED)
line(665)
refs=[('[1] OH no Type School: A — James Edmondson','https://ohnotype.co/blog/ohno-type-school-a'),('[2] Glyphs — Intermediate layers / Drawing good paths','https://glyphsapp.com/learn/intermediate-layers'),('[3] Glyphs — Spacing: evaluate text at reading size','https://glyphsapp.com/learn/spacing'),('[4] Noto — Sans Mono design and reference repository','https://notofonts.github.io/noto-docs/specimen/NotoSansMono/')]
for i,(label,url) in enumerate(refs):
 y=691+i*20;txt(label,M,y,9.1,color=ACC);c.linkURL(url,(M,CH-y-3,RIGHT,CH-y+10),relative=0,thickness=0)
c.showPage();c.save();(OUT/'validation/pdf-layout.json').write_text(json.dumps(checks,indent=2))
print('Wrote three-page review')
