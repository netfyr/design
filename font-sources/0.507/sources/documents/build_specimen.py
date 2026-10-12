
"""Full 28-style specimen: actual shaped text plus a complete encoded-glyph atlas.

The atlas centers glyph ink for inspection; it is not a spacing specimen.
The preceding text pages use the font's actual advances and shaping.
All document text uses netfyr fonts; no font attachment is added to the PDF.
"""
from pathlib import Path
import os,json,math,unicodedata as ud
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor
from fontTools.ttLib import TTFont
from shaping import PositionedFont
BUILD=Path(os.environ['NETFYR_BUILD']);DELIVERY=Path(os.environ['NETFYR_DELIVERY'])
W,H=1190.551,841.89;M=34
PAPER=HexColor('#F7F2EA');INK=HexColor('#211C19');ORANGE=HexColor('#FF7A1A');DEEP=HexColor('#AF4D10');LINE=HexColor('#D8CFC4')
WEIGHTS={300:'Light',400:'Regular',500:'Medium',600:'SemiBold',700:'Bold',800:'ExtraBold',900:'Black'}
STYLES=[]
for family in ['sans','mono']:
    for wt,label in WEIGHTS.items():
        for it in [False,True]:
            style=('Italic' if wt==400 else label+'Italic') if it else label
            key=f'{family}-{style}'
            path=BUILD/'fonts'/f'netfyr{family}-{style}.ttf'
            f=PositionedFont('nf-atlas-'+key,path);pdfmetrics.registerFont(f)
            STYLES.append(dict(key=key,family=family,weight=wt,italic=it,label=label,font=f,tt=TTFont(path)))
F={v['key']:v for v in STYLES}
REG=F['sans-Regular'];SEM=F['sans-SemiBold']
OUT=DELIVERY/'netfyr-complete-specimen.pdf'
C=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1,invariant=1,
                initialFontName=REG['font'].fontName,initialFontSize=10)
C.setTitle('netfyr / 28-style specimen and complete glyph atlas')
C.setAuthor('netfyr')
C.setSubject('Source-and-proof expansion 0.507. All 2,225 encoded characters shown in all 28 styles; additional internal glyphs listed separately.')
PAGE=0;RUNS=[];CELLS=[]
def txt(s,x,y,size=11,font=None,color=INK,align='left'):
    font=font or REG
    f=font['font'];wid=f.shaper.width(s,size)
    if align=='center':x-=wid/2
    elif align=='right':x-=wid
    if x<15 or x+wid>W-15:raise ValueError(('Text outside page',PAGE,s,x,wid))
    C.setFont(f.fontName,size);C.setFillColor(color);C.drawString(x,H-y,f.positioned(s))
    RUNS.append({'page':PAGE,'text':s,'font':font['key'],'size':size,'x':x,'y':y,'width':wid})
    return wid
def rect(x,y,w,h,col):
    C.setFillColor(col);C.rect(x,H-y-h,w,h,stroke=0,fill=1)
def line(y,x=M,w=W-2*M):
    C.setStrokeColor(LINE);C.setLineWidth(.5);C.line(x,H-y,x+w,H-y)
def page(title,subtitle=None):
    global PAGE
    if PAGE:C.showPage()
    PAGE+=1;rect(0,0,W,H,PAPER)
    txt('netfyr / type specimen',M,28,10,font=SEM)
    txt('0.507 / source-and-proof edition',W-M,28,9,align='right')
    txt(title,M,76,31,font=SEM)
    if subtitle:txt(subtitle,M,101,11)
    line(812);txt(str(PAGE),M,830,8)
    txt('Glyph atlas is ink-centered. Text proofs use actual spacing.',W-M,830,8,align='right')
def para(s,x,y,width,size=12,leading=18):
    words=s.split();lines=[];row=''
    for word in words:
        candidate=(row+' '+word).strip()
        if row and REG['font'].shaper.width(candidate,size)>width:lines.append(row);row=word
        else:row=candidate
    lines.append(row)
    for i,row in enumerate(lines):txt(row,x,y+i*leading,size)
    return y+(len(lines)-1)*leading
page('Two families. Seven weights. Drawn italics.',
     'This document shows the 28-style expansion as a design proof, with all encoded characters visible in every style.')
rect(M,132,W-2*M,214,INK)
txt('netfyr sans',M+26,174,14,color=PAPER)
txt('A precise outline.',M+26,250,60,font=F['sans-BlackItalic'],color=ORANGE)
txt('netfyr mono  /  desired state',M+26,315,26,font=F['mono-Regular'],color=PAPER)
x2=628
txt('Reading the specimen',M,396,20,font=SEM)
end=para('The next two pages use real words, punctuation and figures across the weight range. Compare the upright and italic independently: an italic is not expected to be a tilted duplicate of the upright.',M,427,514)
para('The original Regular and SemiBold uprights receive the declared character and accent-positioning corrections. Other outlines and layout data are preserved. New styles have their own static drawing controls. A variable interpolation model has not been certified.',M,end+34,514)
txt('What the atlas contains',x2,396,20,font=SEM)
end=para('Each atlas row is a character; each column is a style. Every one of the 2,225 encoded characters appears in all 28 styles. The final rows show the additional unencoded alternates and the missing-character drawing.',x2,427,514)
para('Blank spaces and invisible controls are labeled rather than replaced with visible artwork. Combining marks are centered as isolated shapes here; inspect the text proofs and the shaping audit for attachment behavior.',x2,end+34,514)
line(665)
txt('Seven weights',M,699,15,font=SEM)
txt('300 Light / 400 Regular / 500 Medium / 600 SemiBold / 700 Bold / 800 ExtraBold / 900 Black',M,728,14)
txt('Technical cell',M,768,12,font=SEM)
txt('640-unit advance, 1000-unit em, y -250 to 1000. Use 1.25em line height for joined cells; zero tracking.',M+137,768,12)
for family in ['sans','mono']:
    page('netfyr '+family,
         'Actual font spacing and OpenType shaping. Weight names identify nominal style classes, not uniform stroke widths.')
    for i,s in enumerate([v for v in STYLES if v['family']==family]):
        y=157+i*46
        txt(str(s['weight'])+' / '+('Italic' if s['italic'] else 'Upright'),M,y,12,color=DEEP)
        txt('netfyr. desired state. agdrswym Δδ 0123',192,y,30 if family=='mono' else 32,font=s)
page('Optical controls and technical text',
     'The diagrams below show actual final glyphs. The upright technical characters are shared by the italic of the same weight.')
for i,(title,key,text) in enumerate([
    ('Retained upright','sans-Regular','agfrt'),
    ('Drawn italic','sans-Italic','agfrt'),
    ('Heavy counters','sans-Black','aersw'),
    ('Heavy italic','sans-BlackItalic','aersw')]):
    x=M+i*284
    txt(title,x,156,12,font=SEM)
    txt(text,x,242,58,font=F[key])
    txt(key.replace('-',' / '),x,276,10,color=DEEP)
line(304)
txt('Diacritics and identity',M,350,18,font=SEM)
txt('ắ ấ ợ ǻ ȷ ǰ ąę ďľť Ææ Œœ ß',M,405,28,font=F['sans-Italic'])
txt('ắ ấ ợ ǻ ȷ ǰ ąę ďľť Ææ Œœ ß',M,455,28,font=F['sans-BlackItalic'])
para('The encoded and decomposed forms are checked with the native shaping engine. Font-level composition, side carons, narrow marks and Vietnamese horn placement remain active in the italic.',M,497,530,11.6,17)
txt('Columns stay columns',636,350,18,font=SEM)
terminal=['┌────────────┬────┐','│netfyr      │0.5 │','│░▒▓│ ▁▃▅▇█  │0123│','└────────────┴────┘']
for i,t in enumerate(terminal):
    txt(t,636,395+i*25,20,font=F['mono-BlackItalic'],color=DEEP)
para('Mono has no pair kerning. The text leans; box drawing, shading, Braille, Powerline and the flame remain upright. Accent overhang beside a full-cell graphic remains a separate review case.',636,527,520,11.6,17)
line(636)
txt('Proof status',M,674,16,font=SEM)
para('This is an unhinted static proof build. The accompanying reports distinguish shape and metadata checks, canonical shaping, finite raster collision screening, and remaining review gates. A computational pass does not replace a native-reader or specialist type review.',M,704,W-2*M,12,18)
txt('No Google Fonts acceptance or licensing decision is implied.',M,780,11,color=DEEP)

# Complete glyph atlas. An ink-centered glyph is explicitly not a spacing proof.
ref=STYLES[0]['tt'];cps=sorted(ref.getBestCmap())
entries=[('unicode',cp) for cp in cps]
mapped=set(ref.getBestCmap().values())
internal=[gn for gn in ref.getGlyphOrder() if gn not in mapped]
entries += [('internal',gn) for gn in internal]
ROWS=21;LEFT=112;COL=(W-M-LEFT)/28;RH=31.0;TOP=140
atlas_start=PAGE+1
for start in range(0,len(entries),ROWS):
    subset=entries[start:start+ROWS]
    first=subset[0][1];last=subset[-1][1]
    label=(f'U+{first:04X}' if isinstance(first,int) else str(first))+' — '+(f'U+{last:04X}' if isinstance(last,int) else str(last))
    page('Character atlas / '+label)
    for fi,fam in enumerate(['sans','mono']):
        x=LEFT+fi*14*COL
        txt('netfyr '+fam,x+7*COL,96,12,font=SEM,align='center')
        for wi,(wt,weightname) in enumerate(WEIGHTS.items()):
            pos=x+wi*2*COL
            txt(str(wt),pos+COL,113,8.2,font=SEM,align='center')
            txt('u',pos+COL/2,128,7.4,align='center')
            txt('i',pos+1.5*COL,128,7.4,align='center')
    for ri,(kind,value) in enumerate(subset):
        y=TOP+ri*RH
        line(y+RH,x=M,w=W-2*M)
        if kind=='unicode':
            code=f'{value:04X}';name=ud.name(chr(value),'PRIVATE USE')
        else:code='internal';name=value
        txt(code,M,y+12,8.1,font=SEM)
        short=name.lower()
        if len(short)>17:short=short[:16]+'…'
        txt(short,M,y+24,5.7)
        for col,s in enumerate(STYLES):
            tt=s['tt'];cm=tt.getBestCmap()
            gn=cm.get(value) if kind=='unicode' else value
            if gn not in tt.getGlyphOrder():raise ValueError(('Absent atlas glyph',s['key'],value))
            g=tt['glyf'][gn];x=LEFT+col*COL;cx=x+COL/2
            if not g.numberOfContours:
                txt('blank',cx,y+18,4.8,align='center',color=DEEP)
                CELLS.append({'page':PAGE,'style':s['key'],'kind':kind,'value':value,'blank':True})
                continue
            bounds=[g.xMin,g.yMin,g.xMax,g.yMax]
            size=min(22,(COL-4)*1000/max(1,g.xMax-g.xMin),25*1000/max(1,g.yMax-g.yMin))
            scale=size/1000
            xx=cx-(g.xMin+g.xMax)*scale/2
            baseline=H-(y+RH/2)-(g.yMin+g.yMax)*scale/2
            # Direct vector outline for unencoded glyphs; encoded glyphs use
            # their actual PDF-embedded glyph mapping without contextual reshaping.
            if kind=='unicode':
                C.setFillColor(INK);C.setFont(s['font'].fontName,size)
                C.drawString(xx,baseline,chr(value))
            else:
                from fontTools.pens.reportLabPen import ReportLabPen
                C.saveState();C.translate(xx,baseline);C.scale(scale,scale)
                path=C.beginPath();path.closePath=path.close
                tt.getGlyphSet()[gn].draw(ReportLabPen(tt.getGlyphSet(),path))
                C.setFillColor(INK);C.drawPath(path,stroke=0,fill=1,fillMode=1);C.restoreState()
            CELLS.append({'page':PAGE,'style':s['key'],'kind':kind,'value':value,'bounds':bounds,'size':size})
C.save()
audit=BUILD/'document-audit';audit.mkdir(exist_ok=True)
(audit/'specimen-layout.json').write_text(json.dumps({
    'pages':PAGE,'atlas_start_page':atlas_start,'encoded_per_style':len(cps),'styles':len(STYLES),
    'encoded_cells':len(cps)*len(STYLES),'internal_glyphs_per_style':len(internal),
    'glyph_cells':len(CELLS),'text_runs':RUNS,'all_styles':[s['key'] for s in STYLES],
    'centering':'Glyphs are centered/fitted within atlas cells. Text proof pages use native advances.'
},ensure_ascii=False,indent=2))
print(json.dumps({'pdf':str(OUT),'pages':PAGE,'encoded_cells':len(cps)*len(STYLES),'cells':len(CELLS),'bytes':OUT.stat().st_size}))
