"""Original symbol recipes for netfyr sans.

No font outlines are imported. Skeletons, curve handles and compositions below
are authored here. Unicode names/charts were consulted for symbol semantics,
not as outlines. Stroke widths are factors of the build engine's master stem.
Dense multi-part symbols intentionally use lighter strokes to retain counters.
"""
import math
import unicodedata as ud
from model import glyph, stroke, fill, component, rect, ellipse, transform_ops
from delta_replacement import delta_capital_ops, delta_lower_ops, partial_ops


def _fit_greek_skeletons(ops,weight,low,high):
    """Constrain authored Greek centerlines to their chosen optical heights.

    The narrow numeric search changes only centerline y coordinates; every
    trial is expanded with the actual master width. This avoids thinning the
    horizontal strokes as a post-expansion outline scale would do.
    """
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.pens.recordingPen import RecordingPen
    from outlines import path_recording,expand_stroke,bounds
    assert all(op['kind']=='stroke' for op in ops)
    def transformed(scale,dy=0):
        result=[]
        for op in ops:
            pen=SVGPathPen(None)
            path_recording(op['d']).replay(TransformPen(pen,(1,0,0,scale,0,dy)))
            result.append(dict(op,d=pen.getCommands()))
        return result
    def extrema(items):
        rec=RecordingPen()
        for op in items:
            expand_stroke(op['d'],weight*op.get('width',1),op.get('cap','butt'),
                          op.get('join','round'),op.get('optical',True)).replay(rec)
        bb=bounds(rec);return bb[1],bb[3]
    a,b=.65,1.2
    for _ in range(22):
        scale=(a+b)/2;lo,hi=extrema(transformed(scale))
        if hi-lo>high-low:b=scale
        else:a=scale
    scale=(a+b)/2;lo,_=extrema(transformed(scale))
    return transformed(scale,low-lo)


def build(reg, weight):
    w = 90 if weight == 600 else 72 if weight == 400 else weight
    def put(cp, ops, note='', width=640):
        return glyph(reg, cp, ops, width=width, note=note)
    def path(d, k=1): return [stroke(d, k)]
    def line(x1,y1,x2,y2,k=.85): return path(f'M{x1} {y1}L{x2} {y2}',k)
    def bar(y=300,x1=115,x2=525,k=.85): return line(x1,y,x2,y,k)
    def dot(x=320,y=300,r=None): return [ellipse(x,y,r or w*.65)]
    def ring(x=320,y=300,r=190,k=.78): return [ellipse(x,y,r,stroked=True,width=k)]
    def ref(cp,**kw): return [component(cp,**kw)]
    def flip(ops): return transform_ops(ops,sx=-1,dx=640)
    def turn(ops,axis=300): return transform_ops(ops,sx=-1,sy=-1,dx=640,dy=2*axis)
    def shift(ops,dy): return transform_ops(ops,dy=dy)
    def smaller(ops,s=.7,cy=300):
        return transform_ops(ops,sx=s,sy=s,dx=320*(1-s),dy=cy*(1-s))
    def slash(y1=60,y2=610,k=.7):return line(195,y1,445,y2,k)
    def neg(ops):return ops+slash()
    def eq(y=300,gap=150):return bar(y-gap/2)+bar(y+gap/2)
    def plus(y=300,size=180,k=.85):
        return bar(y,320-size,320+size,k)+line(320,y-size,320,y+size,k)
    def times(y=300,size=150,k=.85):
        return line(320-size,y-size,320+size,y+size,k)+line(320-size,y+size,320+size,y-size,k)
    def wave(y=300):
        return path(f'M105 {y-35}C205 {y+155} 415 {y-155} 535 {y+35}',.85)
    def angle(y=300,size=190):
        return path(f'M{320+size} {y+145}L{320-size} {y}L{320+size} {y-145}',.85)
    def precedes(y=300):
        return path(f'M510 {y+150}Q355 {y+55} 130 {y}Q355 {y-55} 510 {y-150}',.85)
    def subset(y=300):
        return path(f'M520 {y+170}H300C65 {y+170} 65 {y-170} 300 {y-170}H520',.85)
    def star(cx=320,cy=300,r=155,k=.8,n=6):
        out=[]
        for i in range(n):
            a=math.pi/2+2*math.pi*i/n
            out += line(cx,cy,cx+r*math.cos(a),cy+r*math.sin(a),k)
        return out
    def multiletter(text,y=0,scale=None):
        # All letters remain explicitly chosen: no compatibility-decomposition
        # fallback can silently erase a semantic distinction.
        s=scale or min(.75, .9/len(text))
        total=640*s*len(text); start=(640-total)/2
        return [component(c,sx=s,sy=s,dx=start+640*s*i,dy=y) for i,c in enumerate(text)]

    # Greek: shared capital anatomy uses our own Latin components; Greek-only
    # shapes have their own paths. This is basic unaccented Greek, not a claim
    # of a complete modern/polytonic Greek text family.
    shared={0x391:'A',0x392:'B',0x395:'E',0x396:'Z',0x397:'H',0x399:'I',
            0x39A:'K',0x39C:'M',0x39D:'N',0x39F:'O',0x3A1:'P',
            0x3A4:'T',0x3A5:'Y',0x3A7:'X'}
    for cp,c in shared.items():put(cp,ref(c),note='Shared Latin/Greek capital anatomy.')
    # Nominal heights describe ink, not centerlines. Horizontal centerlines
    # sit half the optically corrected stem inside those heights. Shared O/V
    # anatomy also keeps the Greek round and pointed overshoots in the family.
    gh=w*.45
    greek={
      0x393:path(f'M145 0V{700-gh}H520'),
      0x394:delta_capital_ops(w),
      0x398:ref('O')+bar(350,175,465),
      0x39B:ref('V',sy=-1,dy=700),
      0x39E:bar(700-gh*.85,100,540)+bar(350,160,480)+bar(gh*.85,100,540),
      0x3A0:path(f'M140 0V{700-gh}H500V0'),
      0x3A3:path(f'M535 {700-gh}H105L355 350L105 {gh}H535'),
      0x3A6:[ellipse(320,350,218,225,stroked=True)]+line(320,0,320,700,1),
      0x3A8:path('M110 700V490C110 280 530 280 530 490V700 M320 700V0'),
      0x3A9:path(f'M85 {gh}H245V115C25 275 110 {710-gh} 320 {710-gh}C530 {710-gh} 615 275 395 115V{gh}H555'),
      0x3B1:path('M475 490C160 645 55 40 290 0C430 -20 470 170 470 315 M490 520L460 110Q460 5 555 0'),
      0x3B2:path('M135 -205V490C135 800 490 790 490 565C490 430 350 400 205 405C440 470 560 335 510 155C480 40 315 -20 145 80'),
      0x3B3:path('M85 490C275 650 345 220 335 30C325 -180 400 -240 410 -110C430 155 475 345 545 520'),
      0x3B4:delta_lower_ops(w),
      0x3B5:path('M525 450C385 580 130 535 130 390C130 285 230 265 385 265C235 265 120 230 120 115C120 -30 380 -55 530 65'),
      0x3B6:path('M175 705Q350 650 490 700C275 540 105 340 150 140C180 0 400 20 470 -35Q530 -100 390 -175'),
      0x3B7:ref('n')+line(524,-220,524,0,1),
      0x3B8:[ellipse(320,350,180,360-gh,stroked=True)]+bar(350,155,485),
      0x3B9:path(f'M275 520V{105+gh}Q275 {gh-10} 440 {gh-10}'),
      0x3BA:path('M145 520V0 M155 245Q335 280 500 520 M300 310L530 0'),
      0x3BB:path('M135 720Q225 750 275 590L495 0 M325 445L115 0'),
      0x3BC:path('M130 520V-220 M130 420V160C130 -70 455 -65 475 155V520 M475 190V100Q475 -15 555 10'),
      0x3BD:path('M120 520L300 0C480 160 540 305 525 520'),
      0x3BE:path('M175 710Q325 655 470 700 M395 685C85 620 80 350 425 380C165 385 80 165 230 75C350 -5 540 5 475 -100Q450 -155 365 -165'),
      0x3BF:ref('o'),
      0x3C0:path(f'M80 {520-gh}H560 M195 {520-gh}V0 M440 {520-gh}V{100+gh}Q440 {gh-10} 530 {gh-10}'),
      0x3C1:[ellipse(320,260,204,270-gh,stroked=True)]+line(116,-220,116,260,1),
      0x3C2:path('M520 465C175 660 30 110 280 45C390 15 520 -20 460 -125Q440 -165 355 -175'),
      0x3C3:path(f'M555 {520-gh}H315C70 {520-gh} 50 {gh-10} 315 {gh-10}C550 {gh-10} 560 330 400 {520-gh}'),
      0x3C4:path(f'M85 {520-gh}H555 M330 {520-gh}V{110+gh}Q330 {gh-10} 480 {gh-10}'),
      0x3C5:path('M125 520V205C125 -100 530 -80 515 225C510 355 485 445 445 520'),
      0x3C6:[ellipse(320,260,218,270-gh,stroked=True)]+line(320,-220,320,720,1),
      0x3C7:path('M90 520L535 -220 M550 520L115 -220'),
      0x3C8:path(f'M115 520V210C115 100 195 {gh-10} 320 {gh-10}C445 {gh-10} 525 100 525 210V520 M320 720V-220'),
      0x3C9:path('M160 520C15 150 120 -25 255 0Q340 20 320 285Q300 20 385 0C520 -25 625 150 480 520'),
    }
    # These individually authored curved skeletons used nominal ink extrema
    # in the first draft. Fit their skeletons before expansion to declared
    # optical ranges. Re-expanding at the original stroke width preserves stem
    # weight; this does not rescale finished outlines or import any font data.
    # Each target is explicit, rather than a fallback for an unknown glyph.
    greek_ranges={0x3B1:(-10,530),0x3B2:(-220,730),0x3B3:(-220,530),
                  0x3B5:(-10,530),0x3B6:(-220,730),
                  0x3BA:(0,520),0x3BB:(0,730),0x3BD:(-5,520),
                  0x3BE:(-220,730),0x3C2:(-220,530),0x3C5:(-10,520),
                  0x3C7:(-220,520),0x3C9:(-10,520)}
    for cp,ops in greek.items():
        if cp in greek_ranges:ops=_fit_greek_skeletons(ops,w,*greek_ranges[cp])
        put(cp,ops)

    # General punctuation. Space characters retain one cell; format controls
    # are deliberately zero-width and carry no visible diagnostic placeholder.
    for cp in range(0x2000,0x2070):
        if not ud.name(chr(cp),''):continue
        if ud.category(chr(cp))=='Cf' or cp in (0x2028,0x2029):
            put(cp,[],width=0,note='Invisible format/control character.');continue
        if ud.category(chr(cp))=='Zs':put(cp,[],note='One-cell monospaced space.');continue
    punctuation={
      0x2010:bar(265,190,450),0x2011:ref(0x2010),0x2012:bar(300,110,530),
      0x2013:bar(300,70,570),0x2014:bar(300,0,640),0x2015:bar(300,0,640),
      0x2016:line(225,-130,225,700)+line(415,-130,415,700),
      0x2017:bar(-100,70,570,.7)+bar(-210,70,570,.7),
      0x2020:line(320,80,320,730)+bar(500,155,485),
      0x2021:line(320,40,320,730)+bar(515,155,485)+bar(220,155,485),
      0x2022:dot(r=102),0x2023:[fill('M170 100V510L520 305Z')],
      0x2024:dot(y=45),0x2025:dot(205,45)+dot(435,45),
      0x2026:dot(100,45)+dot(320,45)+dot(540,45),0x2027:dot(r=45),
      0x2038:path('M170 -125L320 30L470 -125',.8),
      0x2039:path('M410 460L230 260L410 60'),
      0x203A:path('M230 460L410 260L230 60'),
      0x203B:times(size=230,k=.7)+dot(320,650,40)+dot(320,-50,40)+dot(65,300,40)+dot(575,300,40),
      0x203C:line(200,220,200,700,.85)+line(440,220,440,700,.85)+dot(200,40)+dot(440,40),
      0x203D:path('M150 550C150 790 530 745 510 545C495 400 335 440 325 220 M320 665V220')+dot(320,40),
      0x203E:bar(800,0,640,.75),
      0x203F:path('M40 -80C160 -245 480 -245 600 -80',.7),
      0x2040:path('M40 740C160 905 480 905 600 740',.7),
      0x2041:path('M120 0L320 250L520 0 M320 250L480 700',.85),
      0x2042:star(320,540,90,.6)+star(150,260,90,.6)+star(490,260,90,.6),
      0x2043:bar(300,190,450,1.2),0x2044:line(100,0,540,700,.75),
      0x2045:path('M435 750H225V-100H435 M225 325H350'),
      0x2046:path('M205 750H415V-100H205 M415 325H290'),
      0x2047:ref('?',sx=.55,dx=-5)+ref('?',sx=.55,dx=295),
      0x2048:ref('?',sx=.65,dx=-15)+line(490,220,490,700,.85)+dot(490,40),
      0x2049:line(150,220,150,700,.85)+dot(150,40)+ref('?',sx=.65,dx=240),
      0x204A:path('M115 510H480L270 275V-80'),
      0x204B:ref(0xB6,sx=-1,dx=640),
      0x204C:[fill('M315 180C65 180 65 420 315 420Z')]+line(380,180,380,420,.65)+line(480,180,480,420,.65),
      0x204D:[fill('M325 420C575 420 575 180 325 180Z')]+line(260,180,260,420,.65)+line(160,180,160,420,.65),
      0x204E:star(cy=170,r=150),0x204F:ref(';',sx=-1,dx=640),
      0x2050:path('M115 530Q320 790 525 530 M115 70Q320 -190 525 70',.8),
      0x2051:star(cy=530,r=115,k=.7)+star(cy=160,r=115,k=.7),
      0x2052:slash(20,630)+dot(150,555,40)+dot(490,60,40),
      0x2053:wave(),0x2054:path('M40 -210C160 -45 480 -45 600 -210',.7),
      0x2055:star(n=8,r=205,k=.8)+ring(r=65,k=.65),
      0x2056:dot(200,300)+dot(440,520)+dot(440,80),
      0x2058:dot(320,570)+dot(150,300)+dot(490,300)+dot(320,30),
      0x2059:dot(140,550)+dot(500,550)+dot(320,300)+dot(140,50)+dot(500,50),
      0x205A:dot(320,650)+dot(320,30),
      0x205B:dot(320,850)+dot(120,300)+dot(520,300)+dot(320,-185),
      0x205C:plus(size=180,k=.7)+dot(165,555,36)+dot(475,555,36)+dot(165,45,36)+dot(475,45,36),
      0x205D:dot(320,620)+dot()+dot(320,-20),
      0x205E:dot(320,730,40)+dot(320,450,40)+dot(320,170,40)+dot(320,-110,40),
    }
    # Filled comma-like quote heads with one tapered tail. The previous curled
    # centerline resembled a miniature question mark. Double quotes translate
    # two full-weight forms rather than thinning them by horizontal scaling.
    qr=w*.55
    qright=[ellipse(320,700-qr,qr),
            fill(f'M{320+qr} {700-qr}C{320+qr} 590 330 538 280 505L265 530C302 560 316 588 320 613Z')]
    qleft=turn(qright,axis=602.5)
    def double_quote(ops):return transform_ops(ops,dx=-70)+transform_ops(ops,dx=70)
    low=-(700-w*1.14)
    punctuation.update({0x2018:qleft,0x2019:qright,0x201A:shift(qright,low),
      0x201B:flip(qright),0x201C:double_quote(qleft),0x201D:double_quote(qright),
      0x201E:shift(double_quote(qright),low),0x201F:flip(double_quote(qright))})
    for cp,n,reverse in [(0x2032,1,False),(0x2033,2,False),(0x2034,3,False),(0x2035,1,True),(0x2036,2,True),(0x2037,3,True),(0x2057,4,False)]:
        step=125;start=320-(n-1)*step/2
        ops=[]
        for i in range(n):
            x=start+i*step;ops+=line(x+(-42 if reverse else 42),730,x+(42 if reverse else -42),485,.75)
        punctuation[cp]=ops
    for cp,n in [(0x2030,2),(0x2031,3)]:
        ops=line(95,0,475,710,.7)+[ellipse(155,575,75,100,stroked=True,width=.65)]
        for i in range(n):ops += [ellipse(300+i*125,125,45,85,stroked=True,width=.55)]
        punctuation[cp]=ops
    for cp,ops in punctuation.items():put(cp,ops)

    # Superscripts/subscripts: authored base components, reduced and positioned.
    supermap={0x2070:'0',0x2071:'i',0x207A:'+',0x207B:0x2212,0x207C:'=',0x207D:'(',0x207E:')',0x207F:'n'}
    supermap.update({0x2074+i:str(4+i) for i in range(6)})
    submap={0x2080+i:str(i) for i in range(10)}
    submap.update({0x208A:'+',0x208B:0x2212,0x208C:'=',0x208D:'(',0x208E:')'})
    submap.update(dict(zip(range(0x2090,0x209D),['a','e','o','x',0x259,'h','k','l','m','n','p','s','t'])))
    for mapping,y in [(supermap,370),(submap,-180)]:
        for cp,base in mapping.items():
            if cp==0x209A:
                ops=path('M195 -235V145',.62)+[ellipse(320,-20,125,161,stroked=True,width=.62)]
                put(cp,ops,note='Subscript p retains its descender inside the line cell.')
            else:put(cp,ref(base,sx=.62,sy=.62,dx=122,dy=y),note='Explicit raised/lowered form; fixed cell advance.')

    # Currency abbreviations are explicit compositions. The ECU, legacy rupee,
    # lira and Indian/Turkish signs remain distinct characters and designs.
    currency={
      0x20A0:ref('C',sx=.75,dx=10)+ref('E',sx=.65,sy=.8,dx=225,dy=70),
      0x20A1:ref('C')+line(265,-80,355,780,.65)+line(380,-80,470,780,.65),
      0x20A2:ref('C')+ref('r',sx=.6,sy=.65,dx=240,dy=80),
      0x20A3:ref('F')+bar(160,70,380,.7),
      0x20A4:ref(0xA3)+bar(300,100,445,.65),
      0x20A5:ref('m')+line(175,-80,475,640,.65),
      0x20A6:ref('N')+bar(290,55,585,.65)+bar(440,55,585,.65),
      0x20A7:ref('P',sx=.33,dx=0)+ref('t',sx=.33,dx=210)+ref('s',sx=.33,dx=420),
      0x20A8:ref('R',sx=.49,dx=0)+ref('s',sx=.49,dx=320),
      0x20A9:ref('W')+bar(365,30,610,.65),
      0x20AA:path('M115 0V610H385V180 M255 430V0H525V610',.9),
      0x20AB:ref('d')+bar(625,315,580,.65)+bar(-130,130,540,.65),
      0x20AC:ref('C')+bar(420,60,460,.7)+bar(280,60,440,.7),
      0x20AD:ref('K')+bar(335,45,540,.65),
      0x20AE:ref('T')+line(135,310,510,490,.7)+line(135,180,510,360,.7),
      0x20AF:ref('D',sx=.62,xy=.16,dx=-25)+ref(0x3C1,sx=.48,sy=.6,dx=345,dy=-40),
      0x20B0:path('M115 80C215 275 425 700 305 735C130 790 285 400 445 40Q520 -135 350 -160 M260 370L195 -20',.85),
      0x20B1:ref('P')+bar(475,45,595,.6)+bar(580,45,595,.6),
      0x20B2:ref('G')+line(320,-90,320,790,.65),
      0x20B3:ref('A')+bar(370,60,580,.65)+bar(490,100,540,.65),
      0x20B4:path('M155 600C440 860 640 505 340 365C30 210 160 -150 485 80',.95)+bar(300,60,580,.65)+bar(450,60,580,.65),
      0x20B5:ref('C')+line(215,-50,435,760,.65),
      0x20B6:ref(0x2113,sx=.65,dx=-10)+path('M425 700V135Q425 0 565 40 M90 480H550',.8),
      0x20B7:ref('S',sx=.72,dx=145)+ref('m',sx=.48,sy=.5,dx=-10,dy=-55),
      0x20B8:path('M85 690H555 M85 540H555 M320 540V0',.9),
      0x20B9:path('M100 700H550 M100 535H550 M225 700C600 700 545 335 150 350L505 0',.95),
      0x20BA:path('M260 710V0C455 0 520 80 540 220 M95 385L465 580 M95 250L465 445',.9),
      0x20BB:path('M205 90V620C205 845 45 760 125 650Q180 595 355 605C600 625 625 290 360 315 M120 345Q215 455 265 290Q310 170 360 305Q410 450 470 305 M235 290C190 90 400 -40 515 115',.8),
      0x20BC:path('M110 0V340C110 730 530 730 530 340V0 M320 0V750',.9),
      0x20BD:ref('P')+bar(195,55,415,.7),
      0x20BE:path('M520 350C520 800 140 800 140 350C140 110 225 0 320 0 M265 350V745 M390 350V715 M105 0H550',.85),
      0x20BF:ref('B',sx=.85,dx=45)+line(235,-80,235,790,.6)+line(385,-80,385,790,.6),
      0x20C0:ref('C')+bar(-120,125,545,.75),
    }
    for cp,ops in currency.items():
        if ud.name(chr(cp),''):put(cp,ops)

    _letterlike(reg,w,put,path,line,bar,dot,ring,ref,flip,turn,multiletter)
    _math(reg,w,put,path,line,bar,dot,ring,ref,flip,turn,shift,smaller,slash,neg,eq,plus,times,wave,angle,precedes,subset,star,multiletter)
    # Encoded ligatures preserve the chosen reading sequence; no automatic
    # code-operator substitutions are implied by their presence.
    ligatures={
      0xFB00:path('M155 0V560Q155 725 285 705 M375 0V560Q375 725 535 705 M85 490H530',.86),
      0xFB01:path('M205 0V560Q205 725 375 705 M100 490H510 M460 490V0',.86)+dot(460,655,w*.55),
      0xFB02:path('M185 0V560Q185 725 350 705 M90 490H335 M445 720V100Q445 25 555 30',.86),
      0xFB03:path('M135 0V575Q135 725 255 700 M300 0V575Q300 725 415 700 M75 490H385 M510 490V0',.78)+dot(510,655,w*.52),
      0xFB04:path('M130 0V575Q130 725 250 700 M300 0V575Q300 725 410 700 M70 490H380 M500 720V95Q500 25 580 30',.78),
      0xFB05:path('M170 0V555Q170 730 325 705 M450 645V115Q450 -5 565 25 M330 490H570',.85),
      0xFB06:path('M295 435C135 610 15 330 200 265C390 195 285 -105 80 65 M445 645V115Q445 -5 565 25 M335 490H570',.85),
    }
    for cp,ops in ligatures.items():put(cp,ops,note='Encoded Latin ligature; original narrow skeletons retain full letter heights.')
    circle=[]
    for i in range(12):
        a=2*math.pi*i/12;circle += dot(320+225*math.cos(a),300+300*math.sin(a),29)
    put(0x25CC,circle,note='Dotted-circle mark-placement support.')
    put(0xFFFD,path('M320 735L590 350L320 -35L50 350Z',.85)+ref('?',sx=.45,sy=.65,dx=176,dy=110),note='Distinct replacement diamond and question mark.')


def _letterlike(reg,w,put,path,line,bar,dot,ring,ref,flip,turn,multiletter):
    """Distinguish mathematical alphabets instead of folding them to plain Latin."""
    def italic(c):return ref(c,sx=.84,xy=.16,dx=8)
    def double(c,extra):return ref(c)+path(extra,.5)
    def frac(a,b):return ref(a,sx=.48,sy=.48,dx=5,dy=350)+line(125,0,510,700,.6)+ref(b,sx=.48,sy=.48,dx=340,dy=0)
    data={
      0x2100:frac('a','c'),0x2101:frac('a','s'),0x2102:double('C','M275 645C205 540 205 160 275 55'),
      0x2103:[ellipse(145,650,62,stroked=True,width=.6)]+ref('C',sx=.65,sy=.75,dx=240),
      0x2104:ref('C')+ref('L',sx=.65,sy=.85,dx=195),0x2105:frac('c','o'),0x2106:frac('c','u'),
      0x2107:path('M525 625C320 840 80 650 160 430Q230 300 400 345C65 400 65 -65 400 15Q475 25 535 100'),
      0x2108:path('M145 590C475 870 615 195 335 80C175 20 70 110 125 260 M125 350H430 M145 590V445',.85),
      0x2109:[ellipse(145,650,62,stroked=True,width=.6)]+ref('F',sx=.65,sy=.75,dx=240),
      0x210A:path('M490 430C250 700 55 65 275 40Q430 40 485 500L375 -130C300 -250 65 -200 145 -100Q210 -20 435 30',.85),
      0x210B:path('M100 610Q325 850 230 520L125 0 M435 695L335 90Q335 -25 540 65 M145 305Q355 465 510 350',.9),
      0x210C:path('M90 635L210 720L285 635L220 560V365L385 405V625L470 705L550 620L480 555V70L395 0L340 80V300L220 260V75L145 0L85 70 M110 350L280 400',.8),
      0x210D:double('H','M230 0V700 M420 0V700'),0x210E:italic('h'),
      0x210F:italic('h')+line(135,585,380,630,.65),
      0x2110:path('M105 580C240 805 625 735 500 610Q435 555 325 620L230 110C195 -90 85 0 120 85 M135 10Q385 -55 525 80',.9),
      0x2111:path('M100 615L280 720L490 625L405 545V135L315 15L145 90L215 190 M210 620L295 540V260L185 160 M405 430L540 510',.85),
      0x2112:path('M125 240C530 470 580 825 340 685C180 590 265 125 95 35Q200 115 340 20Q470 -55 555 80',.9),
      0x2113:path('M120 190C555 475 505 845 315 670C155 520 175 60 330 0Q425 -20 510 105',.9),
      0x2114:ref('l',sx=.6,dx=-10)+ref('b',sx=.6,dx=250)+line(100,430,565,540,.7),
      0x2115:double('N','M230 0V700 M410 0V700'),
      0x2116:ref('N',sx=.65,dx=-10)+ref('o',sx=.36,sy=.45,dx=400,dy=370)+bar(300,440,600,.65),
      0x2117:ring(y=350,r=285,k=.7)+ref('P',sx=.56,sy=.66,dx=141,dy=115),
      0x2118:path('M110 -190L255 425C365 675 610 415 465 155C365 5 185 45 175 235 M80 385Q165 590 255 425',.85),
      0x2119:double('P','M230 0V700'),0x211A:double('Q','M275 645C205 540 205 160 275 55'),
      0x211B:path('M100 570C310 825 620 680 495 460Q405 315 205 360 M265 665L125 0 M280 350Q445 -70 555 60',.9),
      0x211C:path('M85 620L235 725L495 635V440L350 340L525 0 M235 670V80L135 0L75 75 M235 415L370 460V600 M130 310L310 380',.85),
      0x211D:double('R','M230 0V700'),0x211E:ref('R')+line(350,0,560,260,.75),
      0x211F:ref('R')+line(230,-60,440,745,.65)+line(300,785,440,745,.65),0x2120:multiletter('SM',y=390,scale=.43),
      0x2121:multiletter('TEL',y=250,scale=.3),0x2122:multiletter('TM',y=390,scale=.43),
      0x2123:ref('V')+line(315,185,550,325,.75),0x2124:double('Z','M150 80L450 610'),
      0x2125:path('M115 480H495L150 110Q345 210 440 75Q520 -50 355 -175 M230 330H450',.9),
      0x2126:ref(0x3A9),0x2127:ref(0x3A9,sx=-1,sy=-1,dx=640,dy=700),
      0x2128:path('M110 620L245 710L505 640L245 345L465 265L450 90L295 -30L115 75 M270 645L195 565 M220 320L340 375 M180 85L275 190',.85),
      0x2129:ref(0x3B9,sx=-1,sy=-1,dx=640,dy=520),0x212A:ref('K'),0x212B:ref(0xC5),
      0x212C:path('M95 555C185 815 635 685 455 465Q375 365 240 360C595 450 630 30 310 10Q120 -15 185 180L300 670',.9),
      0x212D:path('M525 610L395 710L160 600L110 175L275 0L520 100 M285 625V145L400 80 M90 390L330 470',.85),
      0x212E:path('M115 300H535V350C535 615 100 615 100 300C100 -20 440 -65 535 100 M115 370H535',.8),
      0x212F:path('M130 210C550 345 480 675 270 475C-5 190 310 -135 540 105',.9),
      0x2130:path('M520 625C300 845 60 575 345 365C35 375 65 -70 355 25Q485 45 550 165',.9),
      0x2131:path('M105 575C175 765 345 640 545 700 M340 680L210 90Q160 -85 90 25 M135 350Q355 465 485 380',.9),
      0x2132:ref('F',sx=-1,sy=-1,dx=640,dy=700),
      0x2133:path('M75 80Q165 -70 195 150L230 695L320 90L475 690L470 105Q475 -35 565 60',.9),
      0x2134:path('M465 405C290 685 65 335 135 115C200 -90 430 40 495 320Q530 485 370 475',.9),
      0x2135:path('M110 690L515 15 M140 620L165 0 M495 700L470 390 M115 30L210 130 M420 660L510 710',.95),
      0x2136:path('M105 660H465V40H90 M465 40H565',.95),
      0x2137:path('M235 685H405V55L535 0 M405 275L130 0',.95),
      0x2138:path('M85 660H565 M450 660V0',.95),
      0x2139:ref('i'),
      0x213A:[component('Q',sx=0,sy=0,xy=-.78,yx=.78,dx=593,dy=100)],
      0x213B:multiletter('FAX',y=250,scale=.3),
      0x213C:ref(0x3C0)+line(260,0,260,510,.45),
      0x213D:path('M100 520H215L405 -70C480 -265 255 -270 290 -75C325 165 430 350 540 520 M100 520L300 -65C335 -205 380 -180 355 -40',.55),
      0x213E:ref(0x393)+line(235,0,235,700,.45),
      0x213F:ref(0x3A0)+line(230,0,230,700,.45)+line(410,0,410,700,.45),
      0x2140:ref(0x2211)+path('M210 650L455 350L210 50',.45),
      0x2141:ref('G',sx=-1,sy=-1,dx=640,dy=700),
      0x2142:ref('L',sx=-1,sy=-1,dx=640,dy=700),0x2143:ref('L',sx=-1,dx=640),
      0x2144:ref('Y',sx=-1,sy=-1,dx=640,dy=700),
      0x2145:italic('D')+line(195,0,300,700,.45),
      0x2146:italic('d')+line(365,0,480,720,.45),
      0x2147:italic('e')+path('M310 470C210 385 220 170 350 80',.45),
      0x2148:path('M240 0L335 520H425L330 0Z M360 625L375 710H460L445 625Z',.5),
      0x2149:path('M145 -145Q260 -190 290 -50L385 520H475L370 -75Q335 -245 145 -220 M410 625L425 710H510L495 625Z',.5),
      0x214A:ref('P')+ref('L',sx=.6,sy=.7,dx=250,dy=0),
      0x214B:ref('&',sx=-1,sy=-1,dx=640,dy=700),
      0x214C:path('M90 630Q85 755 190 675L175 30C155 -205 345 -185 325 40L310 615C315 815 590 660 500 425 M100 240C220 395 490 355 530 255Q565 170 485 130',.8),0x214D:frac('A','S'),
      0x214E:ref('f',sx=-1,sy=-1,dx=640,dy=520),
      0x214F:path('M40 100C210 100 220 515 135 480C40 440 100 80 275 90C410 95 425 505 330 480C235 440 295 80 470 90C605 95 615 505 520 480C430 440 480 115 615 100',.75),
    }
    for cp,ops in data.items():put(cp,ops)


def _math(reg,w,put,path,line,bar,dot,ring,ref,flip,turn,shift,smaller,slash,neg,eq,plus,times,wave,angle,precedes,subset,star,multiletter):
    """All 256 mathematical operators, preserving each encoded distinction."""
    cup=path('M125 520V245C125 -70 515 -70 515 245V520',.85)
    cap=transform_ops(cup,sy=-1,dy=600)
    member=path('M535 520H300C45 520 45 80 300 80H535 M115 300H535',.85)
    integ=path('M480 725C265 865 385 165 245 0Q200 -50 155 10',.8)
    diamond=path('M320 525L540 300L320 75L100 300Z',.8)
    m={
      0x2200:path('M100 700L320 0L540 700 M175 470H465'),
      0x2201:path('M520 640C240 815 115 595 115 350C115 105 240 -115 520 60'),
      0x2202:partial_ops(w),
      0x2203:path('M110 700H515V0H110 M110 350H515'),
      0x2205:ring(y=350,r=255,k=.85)+line(100,40,540,660,.75),
      0x2206:delta_capital_ops(w,height=700),
      0x2207:path('M85 700H555L320 0Z'),
      0x2208:member,0x220A:smaller(member,.72),0x220B:flip(member),0x220D:flip(smaller(member,.72)),
      0x220E:[rect(100,40,440,440)],
      0x220F:path('M75 700H565 M155 700V0 M485 700V0'),
      0x2210:path('M75 0H565 M155 0V700 M485 0V700'),
      0x2211:path('M550 700H85L360 350L85 0H550'),
      0x2212:bar(),0x2213:bar(520)+plus(y=200,size=175),0x2214:plus()+dot(320,625,40),
      0x2215:line(135,0,505,700,.8),0x2216:line(135,700,505,0,.8),
      0x2217:star(r=170),0x2218:ring(r=90,k=.7),0x2219:dot(r=55),
      0x221A:path('M65 300L180 160L300 700H580',.95),
      0x221B:path('M65 260L180 100L315 650H585',.9)+ref('3',sx=.35,sy=.35,dx=-5,dy=435),
      0x221C:path('M65 260L180 100L315 650H585',.9)+ref('4',sx=.35,sy=.35,dx=-5,dy=435),
      0x221D:path('M545 490C415 440 400 140 245 135C20 130 20 475 245 470C400 465 410 160 545 110',.85),
      0x221E:path('M320 300C20 710 0 -110 320 300C640 710 620 -110 320 300Z',.85),
      0x221F:path('M135 615V90H550',.85),
      0x2220:path('M520 625L115 90H555',.85),
      0x2221:path('M520 625L115 90H555 M390 90Q390 225 285 315',.8),
      0x2222:path('M515 625L130 85H550 M120 210C315 45 490 275 285 440',.8),
      0x2223:line(320,50,320,650),0x2225:line(230,50,230,650)+line(410,50,410,650),
      0x2227:path('M115 80L320 540L525 80',.85),0x2228:path('M115 540L320 80L525 540',.85),
      0x2229:cap,0x222A:cup,0x222B:integ,
      0x222C:transform_ops(integ,sx=.72,dx=-50)+transform_ops(integ,sx=.72,dx=230),
      0x222D:transform_ops(integ,sx=.5,dx=-20)+transform_ops(integ,sx=.5,dx=160)+transform_ops(integ,sx=.5,dx=340),
      0x222E:integ+ring(y=350,r=130,k=.65),
      0x2234:dot(320,555,42)+dot(135,100,42)+dot(505,100,42),
      0x2235:dot(135,555,42)+dot(505,555,42)+dot(320,100,42),
      0x2236:dot(320,475,42)+dot(320,150,42),
      0x2237:dot(205,475,42)+dot(205,150,42)+dot(435,475,42)+dot(435,150,42),
      0x2238:bar()+dot(320,560,42),0x2239:bar(300,90,410)+dot(530,465,40)+dot(530,135,40),
      0x223A:bar(300,180,460)+dot(130,510,40)+dot(130,90,40)+dot(510,510,40)+dot(510,90,40),
      0x223B:wave()+dot(320,610,40)+dot(320,-10,40),
      0x223C:wave(),0x223D:flip(wave()),
      0x223E:path('M520 490C605 145 250 440 125 250C40 105 125 30 220 80',.85),
      0x223F:path('M70 300C175 830 240 780 320 300C400 -180 465 -230 570 300',.85),
      0x2240:path('M360 660C65 495 575 150 280 -30',.85),
      0x2242:bar(505)+wave(165),0x2243:wave(440)+bar(130),
      0x2245:wave(540)+eq(165,145),
      0x2248:wave(445)+wave(155),0x224A:wave(530)+wave(300)+bar(40),
      0x224B:wave(535)+wave(300)+wave(65),
      0x224C:flip(wave(540))+eq(165,145),
      0x224D:path('M105 560Q320 315 535 560 M105 40Q320 285 535 40',.85),
      0x224E:path('M105 450H225Q320 605 415 450H535 M105 150H225Q320 -5 415 150H535',.85),
      0x224F:path('M105 450H225Q320 605 415 450H535',.85)+bar(150),
      0x2250:eq()+dot(320,590,38),0x2251:eq()+dot(320,610,38)+dot(320,-10,38),
      0x2252:eq()+dot(150,595,38)+dot(490,5,38),
      0x2253:eq()+dot(490,595,38)+dot(150,5,38),
      0x2254:bar(220,240,545)+bar(380,240,545)+dot(105,220,35)+dot(105,380,35),
      0x2255:bar(220,95,400)+bar(380,95,400)+dot(535,220,35)+dot(535,380,35),
      0x2256:eq()+ring(y=300,r=80,k=.65),0x2257:eq()+ring(y=590,r=65,k=.6),
      0x2258:eq()+path('M160 555Q320 740 480 555',.7),
      0x2259:eq()+path('M180 550L320 700L460 550',.7),
      0x225A:eq()+path('M180 700L320 550L460 700',.7),
      0x225B:eq()+star(cy=625,r=80,k=.55),
      0x225C:eq()+path('M195 550L320 765L445 550Z',.6),
      0x225D:eq()+multiletter('def',y=525,scale=.24),
      0x225E:eq()+multiletter('m',y=525,scale=.35),
      0x225F:eq()+ref('?',sx=.32,sy=.32,dx=218,dy=515),
      0x2260:neg(eq()),0x2261:bar(110)+bar(300)+bar(490),
      0x2263:bar(60)+bar(220)+bar(380)+bar(540),
      0x2264:angle(395)+bar(85),0x2265:flip(angle(395))+bar(85),
      0x2266:angle(515)+eq(145,120),0x2267:flip(angle(515))+eq(145,120),
      0x2268:angle(515)+eq(145,120)+line(275,35,390,260,.6),
      0x2269:flip(angle(515))+eq(145,120)+line(275,35,390,260,.6),
      0x226A:transform_ops(angle(),sx=.6,dx=0)+transform_ops(angle(),sx=.6,dx=245),
      0x226B:flip(transform_ops(angle(),sx=.6,dx=0)+transform_ops(angle(),sx=.6,dx=245)),
      0x226C:path('M200 620C425 540 425 60 200 -20 M440 620C215 540 215 60 440 -20',.85),
      0x226E:neg(angle()),0x226F:neg(flip(angle())),
      0x2272:angle(485)+wave(130),0x2273:flip(angle(485))+wave(130),
      0x2276:angle(495)+flip(angle(100)),0x2277:flip(angle(495))+angle(100),
      0x227A:precedes(),0x227B:flip(precedes()),
      0x227C:precedes(425)+bar(85),0x227D:flip(precedes(425))+bar(85),
      0x227E:precedes(470)+wave(105),0x227F:flip(precedes(470))+wave(105),
      0x2282:subset(),0x2283:flip(subset()),
      0x2286:subset(445)+bar(45),0x2287:flip(subset(445))+bar(45),
      0x228A:subset(445)+bar(45)+line(275,-30,380,120,.6),
      0x228B:flip(subset(445))+bar(45)+line(275,-30,380,120,.6),
      0x228C:cup+path('M445 300H225 M295 375L225 300L295 225',.65),0x228D:cup+dot(320,325,48),
      0x228E:cup+plus(y=320,size=100,k=.65),
      0x228F:path('M530 520H130V80H530',.85),
      0x2290:path('M110 520H510V80H110',.85),
      0x2291:path('M530 590H130V190H530',.85)+bar(30),
      0x2292:path('M110 590H510V190H110',.85)+bar(30),
      0x2293:path('M125 70V535H515V70',.85),0x2294:path('M125 535V70H515V535',.85),
    }
    # Negated relations are intentional composites; local negations in 2268,
    # 228A and friends are kept local rather than using a full cancellation.
    for cp,base in [(0x2204,0x2203),(0x2209,0x2208),(0x220C,0x220B),(0x2224,0x2223),(0x2226,0x2225),
      (0x2241,0x223C),(0x2244,0x2243),(0x2247,0x2245),(0x2249,0x2248),(0x2262,0x2261),(0x226D,0x224D),
      (0x2270,0x2264),(0x2271,0x2265),(0x2274,0x2272),(0x2275,0x2273),(0x2278,0x2276),(0x2279,0x2277),
      (0x2280,0x227A),(0x2281,0x227B),(0x2284,0x2282),(0x2285,0x2283),(0x2288,0x2286),(0x2289,0x2287)]:
        m[cp]=neg(m[base])
    m[0x2246]=m[0x2245]+line(275,65,385,260,.6)
    m[0x222F]=m[0x222C]+[ellipse(320,350,200,110,stroked=True,width=.6)]
    m[0x2230]=m[0x222D]+[ellipse(320,350,235,110,stroked=True,width=.55)]
    m[0x2231]=integ+path('M425 315Q270 210 190 340 M220 245L190 340L285 320',.65)
    m[0x2232]=m[0x222E]+path('M435 370L450 265L530 325',.6)
    m[0x2233]=m[0x222E]+path('M205 370L190 265L110 325',.6)
    # Circled and squared operators share containers, not semantic interiors.
    interiors={0x2295:plus(size=125,k=.65),0x2296:bar(300,185,455,.65),
      0x2297:times(size=105,k=.65),0x2298:line(200,155,440,445,.65),
      0x2299:dot(r=45),0x229A:ring(r=78,k=.6),0x229B:star(r=125,k=.6),
      0x229C:eq(300,110),0x229D:bar(300,220,420,.65)}
    for cp,inside in interiors.items():m[cp]=ring(r=245,k=.75)+inside
    for cp,base in [(0x229E,0x2295),(0x229F,0x2296),(0x22A0,0x2297),(0x22A1,0x2299)]:
        m[cp]=path('M80 60H560V540H80Z',.75)+interiors[base]
    def tack(n=1,doub=False):
        ops=[]
        for i in range(n):ops+=line(120+i*105,40,120+i*105,600,.75)
        x=120+(n-1)*105
        return ops+(bar(225,x,555,.75)+bar(415,x,555,.75) if doub else bar(320,x,555,.75))
    m.update({
      0x22A2:tack(),0x22A3:flip(tack()),
      0x22A4:bar(550,80,560)+line(320,550,320,30),
      0x22A5:bar(50,80,560)+line(320,50,320,570),
      0x22A6:line(155,160,155,485)+bar(320,155,555),
      0x22A7:line(150,45,150,600)+dot(425,440,38)+dot(425,200,38),
      0x22A8:tack(doub=True),0x22A9:tack(n=2),0x22AA:tack(n=3),0x22AB:tack(n=2,doub=True),
      0x22B0:path('M510 150Q355 245 130 300Q355 355 450 400C610 455 510 650 415 540',.85),
      0x22B1:flip(path('M510 150Q355 245 130 300Q355 355 450 400C610 455 510 650 415 540',.85)),
      0x22B2:path('M530 550L120 300L530 50Z',.8),0x22B3:path('M110 550L520 300L110 50Z',.8),
      0x22B4:path('M530 650L120 400L530 150Z',.8)+bar(-20),
      0x22B5:path('M110 650L520 400L110 150Z',.8)+bar(-20),
      0x22B6:bar(300,130,500,.75)+ring(130,300,85,.65)+dot(510,300,75),
      0x22B7:bar(300,130,500,.75)+dot(130,300,75)+ring(510,300,85,.65),
      0x22B8:bar(300,80,430,.75)+ring(480,300,100,.7),
      0x22B9:bar(300,85,260,.8)+bar(300,380,555,.8)+line(320,70,320,240,.8)+line(320,360,320,530,.8),
      0x22BA:bar(520,110,530)+line(320,100,320,650),
      0x22BB:m[0x2228]+bar(-55),0x22BC:m[0x2227]+bar(690),0x22BD:m[0x2228]+bar(690),
      0x22BE:path('M125 625V75H550 M125 345Q390 345 390 75',.8),
      0x22BF:path('M130 80H545V625Z',.8),
      0x22C0:transform_ops(m[0x2227],sy=1.4,dy=-100),
      0x22C1:transform_ops(m[0x2228],sy=1.4,dy=-100),
      0x22C2:transform_ops(cap,sy=1.3,dy=-50),0x22C3:transform_ops(cup,sy=1.3,dy=-20),
      0x22C4:diamond,0x22C5:dot(r=58),0x22C6:star(r=195,k=.75),
      0x22C7:times(size=140,k=.8)+dot(320,605,38)+dot(320,-5,38)+dot(60,300,38)+dot(580,300,38),
      0x22C8:path('M110 530L530 70V530L110 70Z',.8),
      0x22C9:path('M115 540V60L530 540 M115 540L530 60',.8),
      0x22CA:path('M525 540V60L110 540 M525 540L110 60',.8),
      0x22CB:path('M120 550L535 65 M310 325L105 65',.85),
      0x22CC:path('M520 550L105 65 M330 325L535 65',.85),
      0x22CD:flip(wave(450))+bar(120),
      0x22CE:path('M110 550C160 165 265 345 320 70C375 345 480 165 530 550',.85),
      0x22CF:path('M110 70C160 455 265 275 320 550C375 275 480 455 530 70',.85),
      0x22D0:subset()+transform_ops(subset(),sx=.6,sy=.6,dx=215,dy=120),
      0x22D1:flip(subset()+transform_ops(subset(),sx=.6,sy=.6,dx=215,dy=120)),
      0x22D2:cap+transform_ops(cap,sx=.55,sy=.85,dx=144,dy=-25),
      0x22D3:cup+transform_ops(cup,sx=.55,sy=.85,dx=144,dy=115),
      0x22D4:cap+line(320,-90,320,675),
      0x22D5:eq()+line(220,-30,220,650,.7)+line(420,-30,420,650,.7),
      0x22D6:angle()+dot(410,300,38),0x22D7:flip(angle())+dot(230,300,38),
      0x22D8:transform_ops(angle(),sx=.4,dx=-5)+transform_ops(angle(),sx=.4,dx=188)+transform_ops(angle(),sx=.4,dx=381),
      0x22DA:angle(675)+bar(325)+flip(angle(-25)),
      0x22DB:flip(angle(675))+bar(325)+angle(-25),
      0x22DC:bar(590)+angle(185),0x22DD:bar(590)+flip(angle(185)),
      0x22DE:bar(590)+precedes(185),0x22DF:bar(590)+flip(precedes(185)),
      0x22E4:m[0x2291]+line(260,-40,370,120,.6),
      0x22E5:m[0x2292]+line(260,-40,370,120,.6),
      0x22E6:m[0x2272]+line(270,-10,375,255,.6),
      0x22E7:m[0x2273]+line(270,-10,375,255,.6),
      0x22E8:m[0x227E]+line(270,-10,375,235,.6),
      0x22E9:m[0x227F]+line(270,-10,375,235,.6),
      0x22EE:dot(320,600,40)+dot(r=40)+dot(320,0,40),
      0x22EF:dot(105,300,40)+dot(r=40)+dot(535,300,40),
      0x22F0:dot(105,0,40)+dot(r=40)+dot(535,600,40),
      0x22F1:dot(105,600,40)+dot(r=40)+dot(535,0,40),
      0x22F2:member+bar(300,115,595),
      0x22F3:member+line(530,100,530,500,.7),
      0x22F4:smaller(member+line(530,100,530,500,.7),.72),
      0x22F5:member+dot(330,680,38),0x22F6:member+bar(680),
      0x22F7:smaller(member,.72)+bar(580),0x22F8:member+bar(-70),
      0x22F9:path('M535 570H300C45 570 45 30 300 30H535 M115 410H535 M115 190H535',.8),
      0x22FF:path('M540 540H120V60H540 M120 300H540',.85),
    })
    m[0x22D9]=flip(m[0x22D8])
    def filled_star(cx,cy,r):
        # Ten explicitly alternating vertices, clockwise in y-up coordinates.
        pts=[]
        for i in range(10):
            a=math.pi/2-i*math.pi/5
            rr=r if i%2==0 else r*.42
            pts.append((cx+rr*math.cos(a),cy+rr*math.sin(a)))
        return [fill('M'+'L'.join(f'{x} {y}' for x,y in pts)+'Z')]
    m[0x225B]=eq()+filled_star(320,635,100)
    m[0x22C6]=filled_star(320,300,200)
    for cp,base in [(0x22AC,0x22A2),(0x22AD,0x22A8),(0x22AE,0x22A9),(0x22AF,0x22AB),
      (0x22E0,0x227C),(0x22E1,0x227D),(0x22E2,0x2291),(0x22E3,0x2292),
      (0x22EA,0x22B2),(0x22EB,0x22B3),(0x22EC,0x22B4),(0x22ED,0x22B5)]:m[cp]=neg(m[base])
    for cp,base in [(0x22FA,0x22F2),(0x22FB,0x22F3),(0x22FC,0x22F4),(0x22FD,0x22F6),(0x22FE,0x22F7)]:m[cp]=flip(m[base])
    missing=set(range(0x2200,0x2300))-set(m)
    assert not missing, 'Unassigned mathematical recipes: '+str(sorted(missing))
    def isotropic(ops):
        for op in ops:
            if op['kind']=='stroke':op['optical']=False
            if op['kind']=='group':isotropic(op['ops'])
    for cp,ops in m.items():
        isotropic(ops)
        put(cp,ops)
