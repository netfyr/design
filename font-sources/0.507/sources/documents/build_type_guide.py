#!/usr/bin/env python3
"""Three-page font usage guide, entirely shaped in the locally built netfyr family."""
from pathlib import Path
import os,json
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor
from shaping import PositionedFont
BUILD=Path(os.environ['NETFYR_BUILD']);OUT=Path(os.environ['NETFYR_DELIVERY']);OUT.mkdir(parents=True,exist_ok=True)
W,H=595.2756,841.8898;M=42;CW=W-2*M
INK=HexColor('#211C19');PAPER=HexColor('#F7F2EA');ACC=HexColor('#AF4D10');ORANGE=HexColor('#FF7A1A');RULE=HexColor('#D8CFC4')
WEIGHTS=[(300,'Light'),(400,'Regular'),(500,'Medium'),(600,'SemiBold'),(700,'Bold'),(800,'ExtraBold'),(900,'Black')]
F={}
for family in ['sans','mono']:
 for weight,label in WEIGHTS:
  for italic in [False,True]:
   style=('Italic' if weight==400 else label+'Italic') if italic else label
   key=f'{family}-{style}'
   f=PositionedFont('nf-guide-'+key,BUILD/'fonts'/f'netfyr{family}-{style}.ttf');pdfmetrics.registerFont(f);F[key]=f
C=canvas.Canvas(str(OUT/'netfyr-font-guide.pdf'),pagesize=(W,H),pageCompression=1,invariant=1,initialFontName=F['sans-Regular'].fontName)
C.setTitle('netfyr / font guide / 0.507');C.setAuthor('netfyr');C.setSubject('Three-page usage guide for the final 28-style source-and-specimen release.')
PAGE=0;RUNS=[]
def rect(x,y,w,h,col):
 C.setFillColor(col);C.rect(x,H-y-h,w,h,fill=1,stroke=0)
def line(y):
 C.setStrokeColor(RULE);C.setLineWidth(.55);C.line(M,H-y,W-M,H-y)
def text(s,x,y,size=10.7,font='sans-Regular',color=INK,align='left'):
 f=F[font];width=f.shaper.width(s,size)
 if align=='right':x-=width
 if align=='center':x-=width/2
 if x<M-1 or x+width>W-M+1:raise ValueError((PAGE,s,x,width))
 C.setFillColor(color);C.setFont(f.fontName,size);C.drawString(x,H-y,f.positioned(s))
 RUNS.append({'page':PAGE,'text':s,'font':font,'x':x,'y':y,'size':size,'width':width})
def para(s,x,y,width=CW,size=11,leading=16,font='sans-Regular',color=INK):
 rows=[];row=''
 for word in s.split():
  candidate=(row+' '+word).strip()
  if row and F[font].shaper.width(candidate,size)>width:rows.append(row);row=word
  else:row=candidate
 if row:rows.append(row)
 for i,row in enumerate(rows):text(row,x,y+i*leading,size,font,color)
 return y+(len(rows)-1)*leading

def page(title,sub):
 global PAGE
 if PAGE:C.showPage()
 PAGE+=1;rect(0,0,W,H,PAPER)
 text('netfyr / fonts',M,32,10,'sans-SemiBold');text('0.507',W-M,32,9,align='right')
 text(title,M,92,32,'sans-SemiBold');para(sub,M,119,size=11,leading=16)
 line(795);text(f'{PAGE} / 3',M,815,9);text('netfyr sans + mono',W-M,815,9,align='right')

def heading(label,y):text(label,M,y,14,'sans-SemiBold')

page('Font styles','netfyr sans and mono: seven weights in upright and italic.')
rect(M,161,CW,83,INK)
text('Aa',M+17,223,58,'sans-BlackItalic',ORANGE)
text('Network settings',M+136,197,18,'sans-SemiBold',PAPER)
text('interface = "eth0"',M+137,225,15,'mono-Regular',PAPER)
text('Weight',M,280,10,'sans-SemiBold',ACC)
text('netfyr sans',M+132,280,11,'sans-SemiBold',ACC)
text('netfyr mono',M+337,280,11,'sans-SemiBold',ACC)
line(293)
for i,(weight,label) in enumerate(WEIGHTS):
 y=328+i*46
 text(f'{weight} / {label}',M,y-3,10.5)
 it='Italic' if weight==400 else label+'Italic'
 text('Aa',M+132,y,30,f'sans-{label}')
 text('Aa',M+210,y,30,f'sans-{it}')
 text('Aa',M+337,y,30,f'mono-{label}')
 text('Aa',M+415,y,30,f'mono-{it}')
 line(y+14)
para('Each row pairs the upright with its drawn italic. These are static styles: choose the actual weight and italic file rather than synthetic bold or a geometric shear.',M,682,size=11,leading=16)
para('Both families contain 2,225 encoded characters per style. The complete specimen shows every character; its atlas centers ink for inspection, while its text pages use actual spacing.',M,742,size=10.5,leading=15)

page('Spacing','Use normal letter spacing and select the supplied weight and italic style.')
heading('Sans / ordinary text and headings',174)
para('netfyr sans has proportional letter widths, optical sidebearings and pair positioning. Use normal letter spacing and keep shaping enabled. Select a real supplied italic at the intended weight.',M,199)
text('HAMBURG  AV To Wa  0123456789',M,277,21,'sans-Regular')
text('hamburg  agerswy  æœ  Ɣɣ',M,312,21,'sans-Italic')
line(339)
heading('Mono / code and connected cells',371)
para('netfyr mono gives each spacing glyph a 640-unit advance in a 1,000-unit em. Marks and designated controls remain zero-width; pair kerning is disabled. Technical graphics stay upright in italic styles.',M,395)
mono=F['mono-Regular'];size=18
for i,row in enumerate(['┌───────────────────┐','│'+'  netfyr 0.507'.ljust(19)+'│','│'+'  ░▒▓│  0123456789'.ljust(19)+'│','└───────────────────┘']):
 text(row,M,477+i*22.5,size,'mono-Regular',ACC)
para('Joined diagrams: 1.25em line height, zero letter spacing and preserved whitespace. Ordinary text with stacked accents: start at 1.5em line height and inspect the intended application.',M,584,size=11,leading=16)
line(639)
heading('Baselines and overshoot',670)
para('Flat endings use their alignment lines; rounded forms retain optical overshoot. Heavy counters and joins have local corrections. The revised heavy A keeps its outside diagonals and advance, while the inner legs, crossbar and counter work together.',M,695,size=10.8,leading=15.5)

page('Build fonts','The library includes 28 TTF and WOFF2 styles, documents and the review record.')
heading('1 / Build the 28 TTFs locally',175)
para('Use your original 0.401 source kit. The builder first reproduces 0.506, applies the declared glyph corrections, then checks the new revision. Choose a fresh output directory.',M,201)
rect(M,257,CW,141,INK)
commands=['python sources/build_reviewed.py \\', '  --reference "/path/to/netfyr-type-kit(1).zip" \\', '  --output ./build \\', '  --jobs 4 \\', '  --documents']
for i,s in enumerate(commands):text(s,M+16,282+23*i,10,'mono-Regular',PAPER)
para('Install the pinned Python dependencies and native Inkscape, Cairo, FreeType and HarfBuzz libraries first. The README gives setup details. Outputs go to build/fonts and build/documents.',M,422,size=10.8,leading=15.5)
heading('2 / Optional web delivery',498)
text('python sources/export_web.py --build ./build',M,526,10.2,'mono-Regular')
para('This converts your local TTFs to WOFF2 and creates netfyr.css. Keep the generated web directory together, or select only the files and declarations your site uses.',M,552,size=10.8,leading=15.5)
line(611)
heading('3 / Keep the review scope intact',641)
para('Current build hashes, individual agent decisions and declared glyph changes are recorded with the release. Earlier counter and pair reviews retain their original dates and versions. Software checks are not independent native-reader review.',M,667,size=10.5,leading=15)
para('The fonts are static and unhinted, licensed under SIL OFL 1.1. See OFL.txt in the download. The netfyr name and standalone logo artwork remain reserved. Font licensing does not grant trademark permission.',M,737,size=10.5,leading=15)
C.save()
audit=BUILD/'document-audit';audit.mkdir(exist_ok=True)
(audit/'type-guide-layout.json').write_text(json.dumps({'pages':PAGE,'runs':RUNS,'fonts':'All text is positioned with netfyr/HarfBuzz; no font-file attachment.'},indent=2))
print(json.dumps({'pdf':str(OUT/'netfyr-font-guide.pdf'),'pages':PAGE,'text_runs':len(RUNS)}))
