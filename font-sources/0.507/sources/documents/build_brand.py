"""Three pages. Every text run is shaped in the original netfyr sans family."""
from pathlib import Path
import json,math,xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor
from fontTools.pens.reportLabPen import ReportLabPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path
from shaping import PositionedFont

ROOT=Path(__file__).resolve().parents[2]
import os
BUILD=Path(os.environ['NETFYR_BUILD'])
DELIVERY=Path(os.environ['NETFYR_DELIVERY'])
OUT=DELIVERY/'netfyr-identity.pdf'
WORK=BUILD/'document-audit'
FONTDIR=BUILD/'fonts'
FONTS={}
for key,family,style in [('Regular','sans','Regular'),('Semibold','sans','Semibold'),('Bold','sans','Bold'),('Mono','mono','Regular'),('MonoSemibold','mono','Semibold')]:
    f=PositionedFont('netfyr-'+key,FONTDIR/f'netfyr{family}-{style.replace("Semibold","SemiBold")}.ttf')
    pdfmetrics.registerFont(f);FONTS[key]=f
W,H=595.2756,841.8898;M=42;CW=W-2*M;G=23;COL=(CW-G)/2;RIGHT=M+COL+G
INK=HexColor('#211C19');PAPER=HexColor('#F7F2EA');ORANGE=HexColor('#FF7A1A')
DEEP=HexColor('#AF4D10');LINE=HexColor('#D8CFC4')
D=ET.parse(ROOT/'assets/netfyr-mark.svg').getroot()[0].attrib['d']
CENTER='M20 76L84 12V76L108 52V76A44 44 0 0 1 20 76Z'
C=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1,invariant=1,
                initialFontName='netfyr-Regular',initialFontSize=10,initialLeading=14)
C.setTitle('netfyr | Visual identity');C.setAuthor('netfyr')
C.setSubject('Original flame, color system and the 28-style source-and-proof expansion; geometric and typographic construction')
PAGE=0;RUNS=[];PARAS=[]
def rect(x,y,w,h,color,stroke=None):
    C.setFillColor(color)
    if stroke:C.setStrokeColor(stroke);C.setLineWidth(.5)
    C.rect(x,H-y-h,w,h,fill=1,stroke=bool(stroke))
def rule(y,x=M,w=CW,color=LINE,width=.55):
    C.setStrokeColor(color);C.setLineWidth(width);C.line(x,H-y,x+w,H-y)
def text(s,x,y,size=10,font='Regular',color=INK,align='left'):
    f=FONTS[font];width=f.shaper.width(s,size)
    if align=='right':x-=width
    elif align=='center':x-=width/2
    assert x>=M-2 and x+width<=W-M+2,(PAGE,s,x,x+width)
    shaped=f.positioned(s);C.setFillColor(color);C.setFont(f.fontName,size)
    C.drawString(x,H-y,shaped)
    RUNS.append(dict(page=PAGE,text=s,font=font,size=size,x=round(x,2),baseline=round(y,2),width=round(width,2)))
    return width
def para(s,x,y,w=COL,size=10.7,leading=14.4,font='Regular',color=INK):
    # Fixed measures, ragged right, and the font's own shaping. No justification,
    # artificial letterspacing, per-letter layout correction, or fallback face.
    lines=[]
    for p in s.split('\n'):
        line=''
        for word in p.split():
            candidate=(line+' '+word).strip()
            if line and FONTS[font].shaper.width(candidate,size)>w:
                lines.append(line);line=word
            else:line=candidate
        lines.append(line)
    for i,line in enumerate(lines):text(line,x,y+i*leading,size,font,color)
    end=y+(len(lines)-1)*leading
    PARAS.append(dict(page=PAGE,text=s,top=y-size*.72,bottom=end+size*.23,lines=len(lines),measure=w))
    return end
def section(label,x,y):text(label,x,y,12.8,'Semibold')
def path(d,x,y,size,fill=None,stroke=None,width=1,alpha=1,dash=None):
    C.saveState();C.translate(x,H-y);C.scale(size/128,-size/128);C.translate(0,-2)
    p=C.beginPath();p.closePath=p.close;parse_path(d,ReportLabPen(None,p))
    if fill:C.setFillColor(fill);C.setFillAlpha(alpha)
    if stroke:C.setStrokeColor(stroke);C.setLineWidth(width);C.setLineJoin(1)
    if dash:C.setDash(*dash)
    C.drawPath(p,fill=fill is not None,stroke=stroke is not None,fillMode=1);C.restoreState()
def logo(x,y,size,color=ORANGE):path(D,x,y,size,fill=color)
def lockup(x,y,height,color=PAPER):
    shaper=FONTS['Bold'].shaper;glyphs=shaper.tt.getGlyphSet()
    ink=BoundsPen(glyphs);cursor=0
    for glyph in shaper.shape('netfyr'):
        glyphs[glyph['glyph']].draw(TransformPen(ink,(1,0,0,1,cursor+glyph['x'],glyph['y'])))
        cursor+=glyph['advance']
    n=BoundsPen(glyphs);glyphs[shaper.cmap[ord('n')]].draw(n)
    scale=80/(n.bounds[3]-ink.bounds[1]);ratio=height/128
    logo(x,y,height)
    text('netfyr',x+(146-ink.bounds[0]*scale)*ratio,
         y+(124+ink.bounds[1]*scale)*ratio,1000*scale*ratio,'Bold',color)
def page(title,sub):
    global PAGE
    if PAGE:C.showPage()
    PAGE+=1;rect(0,0,W,H,PAPER)
    text('netfyr',M,32,10,'Semibold');text('VISUAL IDENTITY / 0.507',W-M,32,8.5,align='right')
    text(title,M,90,29.5,'Semibold')
    if sub:para(sub,M,116,CW,size=11.3,leading=15)
    rule(797);text(f'{PAGE} / 3',M,817,9);text('netfyr sans + mono',W-M,817,9,align='right')
def point(label,px,py,x,y,size,dx=0,dy=0):
    xx=x+px*size/128;yy=y+(py-2)*size/128
    C.setFillColor(DEEP);C.circle(xx,H-yy,1.6,stroke=0,fill=1)
    text(label,xx+dx,yy+dy,8.8,'Regular',DEEP)

page('Symbol, color and type','')
rect(M,147,CW,193,INK);lockup(61,164,128)
text('Wordmark / netfyr sans Bold / 700',61,316,9.4,'Regular',PAPER)

section('Two spacing systems',M,378)
end=para('Straight stems, open curves and flat terminals connect the letters to the flame. netfyr sans fits the width of each letter. netfyr mono gives each spacing glyph a 640-unit advance.',M,401)
end=para('Mono m, w and W have separate drawings. A footed i, curved l and dotted zero distinguish common code characters. Both families share the same alignment lines.',M,end+25)
text('minimum  /  network',M,end+38,19.2)
text('I l 1  O 0  ąę',M,end+73,19.2,'Mono')

section('Color roles',RIGHT,378)
colors=[('Ink','#211C19','Text on paper'),('Paper','#F7F2EA','Text on ink'),
        ('Orange','#FF7A1A','The flame'),('Deep orange','#AF4D10','Links on paper')]
for i,(label,value,role) in enumerate(colors):
    y=396+i*48;rect(RIGHT,y,29,29,HexColor(value),LINE if label=='Paper' else None)
    text(label,RIGHT+41,y+11,10.5,'Semibold')
    text(value,RIGHT+COL,y+11,9.7,align='right')
    text(role,RIGHT+41,y+28,9.7)
para('Grey PNG backgrounds: #242424 with orange; #E6E6E6 with deep orange. These neutral export fields supplement the core brand palette.',RIGHT,607,size=9.7,leading=13.2)

rule(663)
section('The mark',M,689)
para('Use the orange flame upright with a transparent interior. Leave 16 SVG units of clear space. The wordmark uses Sans Bold (700): align n with the smaller flame tip and y with the flame base; keep a 32-unit gap. Minimum widths: flame 16 px, full logo 92 px.',M,712,size=9.6,leading=12.8)
section('Project and rights',RIGHT,689)
para('netfyr is independent and is not endorsed by Red Hat. The fonts use SIL OFL 1.1. The netfyr name and standalone flame, logo and wordmark remain reserved. Website code uses MIT.',RIGHT,712,size=9.8,leading=13.3)

page('Flame construction','Two right triangles, one lower half-disk and a single expanded boundary.')
DW=(CW-30)/3;DS=139;DY=149
XS=[M+i*(DW+15)+(DW-DS)/2 for i in range(3)]
for p,alpha in [('M20 76H108A44 44 0 0 1 20 76Z',.20),('M20 76L84 12V76Z',.45),('M84 76L108 52V76Z',.75)]:
    path(p,XS[0],DY,DS,ORANGE,DEEP,.8,alpha)
path('M20 76H108',XS[0],DY,DS,stroke=DEEP,width=.8,dash=(3,2))
for s,px,py in [('A',64,54),('B',97,68),('D',61,103)]:
    text(s,XS[0]+px*DS/128,DY+(py-2)*DS/128,10,'Semibold')
path(CENTER,XS[1],DY,DS,stroke=DEEP,width=1.3)
path('M64 76V120',XS[1],DY,DS,stroke=LINE,width=.6)
for label,px,py,dx,dy in [('s',20,76,-11,4),('u',84,12,-3,-8),('b',84,76,-12,5),
                         ('v',108,52,5,-2),('t',108,76,5,4),('c',64,76,-12,3)]:
    point(label,px,py,XS[1],DY,DS,dx,dy)
text('44',XS[1]+68*DS/128,DY+102*DS/128,9,'Regular',DEEP)
logo(XS[2],DY,DS);path(CENTER,XS[2],DY,DS,stroke=INK,width=.7)
captions=[('1  Build','A has legs 64. B has legs 24. D has radius 44, centered at c.'),
          ('2  Cancel','Split the diameter at b. Cancel shared edges s-b and b-t. One closed boundary remains.'),
          ('3  Expand','Take points within 6 units of the boundary: a 12-unit band with round joins.')]
for i,(label,copy) in enumerate(captions):
    xx=M+i*(DW+15);text(label,xx,309,11.2,'Semibold');para(copy,xx,329,DW,size=9.7,leading=13.1)
rule(395)

section('Coordinates and path',M,421)
for i,(key,xy,role) in enumerate([('s','20, 76','Left end'),('u','84, 12','Major apex'),
 ('b','84, 76','Inner return'),('v','108, 52','Minor apex'),('t','108, 76','Right end'),('c','64, 76','Bowl center')]):
    yy=447+i*20;text(key,M,yy,10.4,'Semibold');text('('+xy+')',M+21,yy,10.4);text(role,M+111,yy,10.2)
for i,s in enumerate(['M20 76 L84 12 V76','L108 52 V76','A44 44 0 0 1 20 76 Z']):
    text(s,M,589+i*17,10.3)
para('SVG coordinates run right and down. Viewport: 0 2 128 128. Ink bounds: x 14-114, y 6-126. Outer bowl radius 50; inner radius 38. One filled path, two closed contours.',M,650,size=9.8,leading=13.4)

section('A network operation',RIGHT,421)
text('∂D ⊕ ∂A ⊕ ∂B = Γ',RIGHT,455,15.5,'Regular',DEEP)
end=para('Represent each boundary as a set of edges. Symmetric difference keeps an edge that occurs once and removes an edge shared by two sets.',RIGHT,487)
end=para('This is the same set operation used to compare the edges of undirected routes. Here it removes the internal baselines and leaves the flame.',RIGHT,end+25)
para('The connection is geometric. It does not describe the software implementation.',RIGHT,end+25,size=10.1,leading=13.5)

rule(721)
text('\uf8ff',M,769,34,'Regular',ORANGE)
para('U+F8FF and U+E000 contain this exact mark in all 28 styles. Scale 35/6 maps its 120-unit ink height to 700 font units; translation centers it in a 640-unit cell. The mapping is local to this font.',M+46,745,CW-46,size=9.7,leading=13.1)

page('Typeface construction','')
# Draw real compiled glyphs. Alignment annotations do not alter their geometry.
BASE=285;SCALE=.112;GX=76;RUN='Hno';GW=FONTS['Regular'].shaper.width(RUN,1000)*SCALE
for units,label in [(720,'720'),(700,'700'),(520,'520'),(0,'0')]:
    yy=BASE-units*SCALE
    if units==720:
        # Ascender reference indicated at the side, so near cap lines stay clear.
        rule(yy,GX,GW,color=LINE,width=.4)
    else:
        rule(yy,GX,GW,color=DEEP if units==0 else LINE,width=.6)
        text(label,M,yy+3,8.6,'Regular',DEEP if units==0 else INK)
text(RUN,GX,BASE,112)
text('round overshoot: 10 units',M,312,9.6,'Regular',DEEP)
rows=[('Em / cap / x-height','1000 / 700 / 520'),('Nominal letter extents','720 / -220'),
      ('Nominal stems, Light to Black','52 / 72 / 81 / 90 / 110 / 132 / 154'),('Italic construction','10° / pivot at 260 units')]
for i,(label,value) in enumerate(rows):
    yy=169+i*40;text(label,RIGHT,yy,9.6);text(value,RIGHT,yy+17,11.2,'Semibold')

rule(340)
section('Optical relationships',M,367)
end=para('Black uses separate counter and join controls. Italic a, e, f, r, t and l have their own drawings. The existing Regular and SemiBold uprights remain the controls.',M,390)
end=para('n/o and H/O establish the spacing rhythm. Bearings follow the shape, then pair corrections address local clearance. The slope is applied about half the x-height.',M,end+25)
text('AV  To  Wa  noononno',M,end+34,17.5)
end=para('Accents attach to base and mark anchors. Narrow marks keep i, j and l compact. Side carons, ogoneks and Vietnamese stacks receive distinct placement.',M,end+66,size=10.1,leading=13.6)
text('Ææ  Œœ  ąę  ďľť  ắấợ',M,end+35,17)

section('The mono cell',RIGHT,367)
para('Mono letters, digits, punctuation and spaces advance 640 units. Combining marks have zero advance. Pair kerning is disabled so columns remain aligned.',RIGHT,390)
text('┌───┬───┐',RIGHT,483,18,'Mono',DEEP)
text('│░▒▓│▁▃▅│',RIGHT,505.5,18,'Mono',DEEP)
text('└───┴───┘',RIGHT,528,18,'Mono',DEEP)
end=para('Box, block and Braille glyphs use the same 640-unit cell in both families. Shade tiles and vertical box rules span y -250 to 1000. Joined diagrams use 1.25 em leading and zero tracking.',RIGHT,558,size=10.1,leading=13.6)
para('Vector cell edges meet exactly. Fractional raster positions can show fine seams. Use at least 1.5 em leading for text with stacked marks.',RIGHT,end+25,size=9.7,leading=13.2)

rule(708)
text('2,225 characters / 28 styles',M,728,12,'Semibold')
para('Latin, IPA, combining marks, common punctuation and currencies; 256 math operators; 112 arrows; 128 box drawings; 32 blocks; 256 Braille patterns; selected Greek and interface symbols.',M,747,COL,size=9.1,leading=12.4)
para('Seven weights, upright and italic, in each family. The source build includes OpenType composition and mark attachment. Sans has kerning; Mono does not. This is an unhinted design proof, not a Google Fonts approval.',RIGHT,732,COL,size=9.1,leading=12.4)
C.save()
assert PAGE==3
assert all(p['bottom']<790 for p in PARAS),[p for p in PARAS if p['bottom']>=790]
WORK.mkdir(parents=True,exist_ok=True)
(WORK/'guide-layout.json').write_text(json.dumps(dict(runs=RUNS,paragraphs=PARAS),indent=2,ensure_ascii=False))
print(OUT)
