"""Original extended-Latin and diacritic recipes for netfyr sans.

No external outlines are read. Unicode canonical decomposition is character
metadata, not outline data; compatibility characters are authored explicitly.
All visible forms below are paths or affine uses of this family's own letters.
"""
import unicodedata as ud
from model import glyph, stroke, fill, component, ellipse, rect
from refined_glyphs import section_ops
from refined_glyphs import eth_ops, sharp_s_ops, ae_ops, capital_sharp_s_ops


def build(reg, weight):
    h = weight * .45
    def S(d, w=1): return stroke(d, w)
    def C(cp, **kw): return component(cp, **kw)
    def put(cp, ops, height=520, **kw):
        return glyph(reg, cp, ops, top=kw.pop('top',(320,height+50)),
                     bottom=kw.pop('bottom',(320,-50)),
                     note=ud.name(chr(cp),'private component'), **kw)
    def alias(cp, base, **kw):
        return put(cp,[C(base,**kw)],700 if ud.category(chr(cp))=='Lu' else 520)
    def pair(cp, left, right, sy=1, dy=0):
        # Full-weight components, with authored width classes. A digraph is
        # allowed to be wider than a letter; squeezing both x axes to .47
        # made its vertical strokes visibly lighter than the surrounding text.
        widths={'i':72,'j':170,'l':180,'f':250,'r':290,'t':280,
                'I':220,'J':410,'L':425,'M':650,'W':680,'m':650,'w':650}
        def span(c):
            c=ord(c) if isinstance(c,str) else c
            base=ud.normalize('NFD',chr(c))[0]
            return widths.get(base,490)
        a,b=span(left),span(right);gap=65
        return put(cp,[C(left,sy=sy,dx=-(b+gap)/2,dy=dy),
                       C(right,sy=sy,dx=(a+gap)/2,dy=dy)],
                   700 if ud.category(chr(cp)) in ('Lu','Lt') else 520,
                   width=a+b+gap+100)
    def bar(cp, base, d, height=None):
        return put(cp,[C(base),S(d,.8)],height or (700 if ud.category(chr(cp))=='Lu' else 520))
    def smallcap(cp, base):
        return put(cp,[C(base,sx=.9,sy=520/700,dx=32)])
    def turned(cp, base, height=520):
        return put(cp,[C(base,sx=-1,sy=-1,dx=640,dy=height)],height)
    def reflected(cp, base, height=520):
        return put(cp,[C(base,sx=-1,dx=640)],height)
    def hook(cp, base, d, height=520):
        return put(cp,[C(base),S(d)],height)

    # Every combining sign is centered on its attachment origin, not on a cell.
    def mark(cp, ops, kind='above', top=None, bottom=None, compact=True):
        # Marks are drawn at their final optical dimensions. Line metrics must
        # accommodate accents, rather than flattening all accents into a cell.
        # ``compact`` remains a call-site compatibility argument, not scaling.
        if top is None: top=(0,160) if kind in ('above','right') else (0,0)
        if bottom is None: bottom=(0,-175) if kind=='below' else (0,0)
        return glyph(reg,cp,ops,width=0,mark=kind,top=top,bottom=bottom,
                     note=ud.name(chr(cp)))
    def MS(d,w=.78): return S(d,w)
    above = {
      0x300:[MS('M-62 130L43 30')],
      0x301:[MS('M-43 30L62 130')],
      0x302:[MS('M-110 30L0 112L110 30')],
      0x303:[MS('M-130 40C-87 103 -42 109 5 66S86 20 130 86')],
      0x304:[MS('M-125 48H125')],
      0x305:[MS('M-320 75H320')],
      0x306:[MS('M-110 100Q0 -18 110 100')],
      0x307:[ellipse(0,50,weight*.46)],
      0x308:[ellipse(-77,50,weight*.44),ellipse(77,50,weight*.44)],
      0x309:[MS('M-48 112C-48 168 61 164 61 115C61 77 5 67 5 24')],
      0x30A:[ellipse(0,82,62,stroked=True,width=.74)],
      0x30B:[MS('M-115 30L-35 130M15 30L95 130')],
      0x30C:[MS('M-110 112L0 30L110 112')],
      0x30D:[MS('M0 25V155')],
      0x30E:[MS('M-65 25V155M65 25V155')],
      0x30F:[MS('M-105 130L-25 30M25 130L105 30')],
      0x310:[MS('M-110 80Q0 -30 110 80'),ellipse(0,140,weight*.28)],
      0x311:[MS('M-110 35Q0 180 110 35')],
      0x312:[MS('M35 135C-40 135 -45 50 20 40')],
      0x313:[MS('M-10 140C55 130 40 65 -35 30')],
      0x314:[MS('M10 140C-55 130 -40 65 35 30')],
      0x315:[MS('M15 140C80 130 65 65 -10 30')],
      0x31A:[MS('M-85 120H90V25')],
      0x33D:[MS('M-85 25L85 155M-85 155L85 25')],
      0x33E:[MS('M-35 20C55 40 65 75 0 95S-50 155 30 180')],
      0x33F:[MS('M-300 45H300M-300 135H300')],
      0x342:[MS('M-130 55C-90 145 -35 145 10 95S90 40 130 125')],
      0x346:[MS('M-110 20V110H110V20')],
      0x34A:[MS('M-130 45C-90 110 -35 110 10 70S90 30 130 100M-85 155H85')],
      0x34B:[MS('M-95 90H95'),ellipse(0,25,weight*.25),ellipse(0,155,weight*.25)],
      0x34C:[MS('M-130 50C-85 115 -35 115 10 75S90 35 130 105M-100 160H100')],
      0x350:[MS('M-50 25L55 90L-50 155')],
      0x351:[MS('M50 25C-95 25 -95 155 50 155')],
      0x352:[MS('M-120 35Q0 220 120 35'),ellipse(0,40,weight*.26)],
      0x357:[MS('M-50 25C95 25 95 155 -50 155')],
      0x358:[ellipse(65,75,weight*.30)],
      0x35B:[MS('M-110 35L-40 125L30 35L100 125')],
      0x35D:[MS('M-130 135Q320 -90 770 135')],
      0x35E:[MS('M-140 80H780')],
      0x360:[MS('M-130 55C20 190 150 185 320 100S620 10 770 145')],
      0x361:[MS('M-130 35Q320 260 770 35')],
    }
    for cp,ops in above.items():
        mark(cp,ops,top=(320,145) if cp>=0x35C else (0,155) if cp==0x33E else None)
    # Contextual forms are different drawings, not x-scaled copies: their
    # stroke weight stays comparable to the ordinary marks on narrow i/j.
    narrow={
      0x300:[MS('M-35 132L26 30')],
      0x301:[MS('M-26 30L35 132')],
      0x302:[MS('M-69 30L0 108L69 30')],
      0x303:[MS('M-83 43C-53 95 -28 96 4 64S56 27 83 81')],
      0x304:[MS('M-79 48H79')],
      0x306:[MS('M-73 98Q0 -8 73 98')],
      0x308:[ellipse(-57,50,weight*.44),ellipse(57,50,weight*.44)],
      0x30C:[MS('M-69 108L0 30L69 108')],
      0x30F:[MS('M-67 132L-25 30M25 132L67 30')],
      0x311:[MS('M-68 32C-68 73.973641 -37.555363 108 0 108C37.555363 108 68 73.973641 68 32')],
    }
    for cp,ops in narrow.items():
        name=f'mark.{cp:04X}.narrow'
        glyph(reg,name,ops,width=0,mark='above',top=(0,160),bottom=(0,0),
              note=f'Optically redrawn narrow {ud.name(chr(cp))}')
        reg[cp]['narrow_alternate']=name
    for cp in (0x300,0x301,0x309):
        reg[cp]['use_stack_right']=True
        if cp in narrow:reg[f'mark.{cp:04X}.narrow']['use_stack_right']=True
    # Tone marks beside Vietnamese circumflex/breve; tilde retains the
    # ordinary centered continuation. The engine applies these identically
    # to canonical composites and decomposed input.
    reg[0x302]['stack_right']=(135,74)
    reg[0x306]['stack_right']=(138,60)
    reg['mark.0302.narrow']['stack_right']=(112,74)
    reg['mark.0306.narrow']['stack_right']=(112,60)
    below = {
      0x316:[MS('M-65 -30L45 -140')],
      0x317:[MS('M-45 -140L65 -30')],
      0x318:[MS('M70 -30V-145M70 -85H-85')],
      0x319:[MS('M-70 -30V-145M-70 -85H85')],
      0x31C:[MS('M50 -25C-95 -25 -95 -155 50 -155')],
      0x31D:[MS('M-100 -135H100M0 -135V-25')],
      0x31E:[MS('M-100 -30H100M0 -30V-140')],
      0x31F:[MS('M-100 -85H100M0 -25V-145')],
      0x320:[MS('M-110 -80H110')],
      0x321:[MS('M0 0V-95C0 -180 -95 -180 -95 -110')],
      0x322:[MS('M0 0V-95C0 -180 95 -180 95 -110')],
      0x323:[ellipse(0,-65,weight*.46)],
      0x324:[ellipse(-77,-65,weight*.44),ellipse(77,-65,weight*.44)],
      0x325:[ellipse(0,-95,63,stroked=True,width=.62)],
      0x326:[MS('M-10 -35C55 -45 40 -110 -35 -145')],
      0x327:[MS('M10 35L-25 -25C80 -15 90 -115 15 -120H-45')],
      0x328:[MS('M45 0C-65 -60 -100 -155 -5 -155Q40 -155 65 -125')],
      0x329:[MS('M0 -25V-155')],
      0x32A:[MS('M-110 -145V-45H110V-145')],
      0x32B:[MS('M-140 -45Q-70 -185 0 -45Q70 -185 140 -45')],
      0x32C:[MS('M-110 -35L0 -130L110 -35')],
      0x32D:[MS('M-110 -130L0 -35L110 -130')],
      0x32E:[MS('M-110 -35Q0 -180 110 -35')],
      0x32F:[MS('M-110 -135Q0 10 110 -135')],
      0x330:[MS('M-130 -110C-90 -20 -35 -20 10 -70S90 -125 130 -40')],
      0x331:[MS('M-125 -75H125')],
      0x332:[MS('M-320 -75H320')],
      0x333:[MS('M-320 -45H320M-320 -135H320')],
      0x339:[MS('M-50 -25C95 -25 95 -155 -50 -155')],
      0x33A:[MS('M-110 -25V-125H110V-25')],
      0x33B:[MS('M-85 -30H85V-150H-85Z')],
      0x33C:[MS('M-140 -110Q-70 10 0 -110Q70 10 140 -110')],
      0x345:[MS('M15 -25V-140Q15 -180 65 -155')],
      0x347:[MS('M-120 -45H120M-120 -130H120')],
      0x348:[MS('M-65 -25V-155M65 -25V-155')],
      0x349:[MS('M-85 -145V-35H90')],
      0x34D:[MS('M-150 -85H150M-80 -25L-150 -85L-80 -145M80 -25L150 -85L80 -145')],
      0x34E:[MS('M0 -155V-25M-80 -100L0 -25L80 -100')],
      0x353:[MS('M-85 -25L85 -155M-85 -155L85 -25')],
      0x354:[MS('M50 -25L-55 -90L50 -155')],
      0x355:[MS('M-50 -25L55 -90L-50 -155')],
      0x356:[MS('M-115 -50L-45 -115L-115 -180M0 -110L65 -40L130 -110')],
      0x359:[MS('M0 -20V-160M-80 -45L80 -135M-80 -135L80 -45')],
      0x35A:[ellipse(-65,-100,55,stroked=True,width=.6),ellipse(65,-100,55,stroked=True,width=.6)],
      0x35C:[MS('M-130 -35Q320 -260 770 -35')],
      0x35F:[MS('M-140 -80H780')],
      0x362:[MS('M-140 -85H770M680 -15L770 -85L680 -155')],
    }
    for cp,ops in below.items(): mark(cp,ops,'below',bottom=(320,-185) if cp>=0x35C else None)
    # Narrow below tilde: two separately authored boundaries avoid the
    # self-intersections caused by stroking a steep, compressed centerline.
    # Its horizontal extent remains 184 units in both masters; weight grows
    # through the two curves and terminal cuts, not by x-scaling the mark.
    narrow_t=(weight-72)/18
    t=narrow_t
    narrow_below_tilde=fill(
        f'M-92 -108C-74 {-62-3*t} -51 {-39+5*t} -29 {-39+5*t}'
        f'C-5 {-39+5*t} 12 {-62+5*t} 28 {-73+5*t}'
        f'C44 {-84+5*t} {53-4*t} {-67+7*t} {66-5*t} {-41+5*t}'
        f'L92 -68C74 {-111-3*t} 54 {-133-5*t} 31 {-133-5*t}'
        f'C7 {-133-5*t} -9 {-112-5*t} -27 {-100-5*t}'
        f'C-45 {-88-5*t} {-54+3*t} {-101-6*t} {-67+5*t} {-131-5*t}Z')
    glyph(reg,'mark.0330.narrow',[narrow_below_tilde],width=0,mark='below',
          top=(0,0),bottom=(0,-175),
          note='Hand-drawn narrow below tilde for i and j; keeps the i/j dot.')
    reg[0x330]['narrow_below_alternate']='mark.0330.narrow'
    # A narrow macron is an independently drawn 158-unit horizontal stroke,
    # retaining the normal mark weight. Its width must not widen an i/j/l.
    glyph(reg,'mark.0331.narrow',[MS('M-79 -75H79')],width=0,mark='below',
          top=(0,0),bottom=(0,-175),
          note='Authored narrow macron below for i, j and l.')
    reg[0x331]['narrow_below_alternate']='mark.0331.narrow'
    glyph(reg,'mark.032D.narrow',[MS('M-69 -125L0 -47L69 -125')],
          width=0,mark='below',top=(0,0),bottom=(0,-175),
          note='Authored narrow circumflex below for i, j and l; full mark weight.')
    reg[0x32D]['narrow_below_alternate']='mark.032D.narrow'
    reg[0x328]['attachment']='ogonek'
    # The underdot needs its own attachment class: on y it sits alongside the
    # descender, while wider below marks keep their ordinary lower anchor.
    reg[0x323]['attachment']='dotbelow'
    if ord('y') in reg: reg[ord('y')]['dotbelow']=(440,-45)
    for cp,d in {
      0x334:'M-150 -40C-85 65 -35 65 20 0S100 -45 150 40',
      0x335:'M-130 0H130', 0x336:'M-300 0H300',
      0x337:'M-120 -130L120 130',0x338:'M-250 -350L250 350',
    }.items(): mark(cp,[MS(d)],'overlay')
    mark(0x31B,[MS('M0 -15C75 -25 95 40 80 100')],'right',top=(80,140))
    mark(0x34F,[],'above',top=(0,0),bottom=(0,0))
    for cp,base in {0x340:0x300,0x341:0x301,0x343:0x313}.items():
        mark(cp,[C(base)],compact=False)
    mark(0x344,[C(0x308),C(0x301,dy=160)],top=(0,320),compact=False)
    for cp,base in zip(range(0x363,0x370),'aeiouc dhmrtvx'.replace(' ','')):
        mark(cp,[C(0x131 if base=='i' else ord(base),sx=.34,sy=.27,dx=-109,dy=30)],top=(0,160))

    # Contextual side caron: the engine uses the same alternate for NFC/NFD.
    glyph(reg,'caron.side',[S('M22 145L0 35',.58)],width=0,
          mark='right',top=(0,175),bottom=(0,0),note='Side caron for d l t L')
    # Cedilla-coded Latvian letters retain their canonical character recipes.
    # The Resolver and ccmp select these original comma alternates for the same
    # base+U0327 sequence: g above; G/K/k/L/l/N/n/R/r below. S/T keep cedillas.
    glyph(reg,'cedilla.g',[C(0x326,sx=-1,sy=-1,dy=-15)],width=0,
          mark='above',top=(0,160),bottom=(0,0),
          note='Rotated comma above for Latvian g with cedilla')
    glyph(reg,'cedilla.comma',[C(0x326)],width=0,
          mark='below',top=(0,0),bottom=(0,-175),
          note='Comma below for cedilla-coded Latvian G K k L l N n R r')
    for base,anchor in {'d':(596,570),'l':(390,570),'t':(410,505),'L':(215,550)}.items():
        if ord(base) in reg: reg[ord(base)]['right']=anchor
    # Full-weight horns share a tip height; the u aperture receives extra
    # room in Semibold without changing the letter's advance.
    horn_u_x=518+16*max(-1.12,min(1.,(weight-72)/18))
    for base,anchor in {'O':(460,645),'U':(horn_u_x,645),'o':(460,465),'u':(horn_u_x,465)}.items():
        if ord(base) in reg: reg[ord(base)]['right']=anchor
    for base,anchor in {'A':(515,0),'a':(495,0),'E':(515,0),'e':(415,15),
                        'I':(365,0),'i':(370,0),'O':(350,0),'o':(365,15),
                        'U':(450,25),'u':(480,0)}.items():
        if ord(base) in reg: reg[ord(base)]['ogonek']=anchor

    # Dotless stems are shared with the ASCII i and j authored by the root.
    put(0x131,[S('M320 0V520')],top=(320,570))
    reg[0x131]['ogonek']=(320,0)
    put(0x237,[S(f'M320 520V-76C320 -160 292 {-220+h} 228 {-220+h}H205')],top=(320,570),bottom=(265,-270))

    # Latin-1 signs: their encoded semantics remain intact.
    glyph(reg,0xA0,[],note='NO-BREAK SPACE; same advance as SPACE')
    put(0xA1,[C('!',sy=-1,dy=520)])
    put(0xA2,[C('c'),S('M350 -75L290 630',.8)])
    put(0xA3,[S('M115 35H535M115 335H430M195 35V480C195 705 520 760 535 515')],700)
    put(0xA4,[ellipse(320,350,155,stroked=True),S('M105 135L205 235M435 465L535 565M105 565L205 465M435 235L535 135')],700)
    put(0xA5,[C('Y'),S('M130 320H510M130 180H510',.85)],700)
    put(0xA6,[S('M320 35V270M320 430V700')],700)
    put(0xA7,section_ops(weight),700)
    put(0xA8,[C(0x308,dx=320,dy=520)])
    for cp,letter in [(0xA9,'C'),(0xAE,'R')]:
        put(cp,[ellipse(320,350,267,stroked=True,width=.65),C(letter,sx=.49,sy=.52,dx=163,dy=168)],700)
    for cp,base in [(0xAA,'a'),(0xBA,'o')]:
        put(cp,[C(base,sx=.58,sy=.58,dx=135,dy=335),S('M160 260H490',.68)],700)
    put(0xAB,[S('M295 455L115 270L295 85M515 455L335 270L515 85',.85)])
    put(0xAC,[S('M105 360H535V170')])
    alias(0xAD,'-')
    put(0xAF,[C(0x304,dx=320,dy=555)])
    put(0xB0,[ellipse(320,540,112,stroked=True,width=.75)],700)
    put(0xB1,[S('M120 390H520M320 200V600M120 65H520')],700)
    for cp,base in [(0xB2,'2'),(0xB3,'3'),(0xB9,'1')]:
        put(cp,[C(base,sx=.58,sy=.58,dx=134,dy=294)],700)
    put(0xB4,[C(0x301,dx=320,dy=510)])
    put(0xB5,[S('M155 485V-210M155 170C155 -20 460 -20 470 180V485M470 180V35H540')],bottom=(320,-265))
    put(0xB6,[S('M510 35V665H315C60 665 60 340 315 340H345M345 35V665')],700)
    put(0xB7,[ellipse(320,270,weight*.52)])
    put(0xB8,[C(0x327,dx=320)])
    reflected(0xBB,0xAB)
    for cp,n,d in [(0xBC,'1','4'),(0xBD,'1','2'),(0xBE,'3','4')]:
        put(cp,[C(n,sx=.42,sy=.47,dx=0,dy=370),S('M175 35L465 665',.75),C(d,sx=.42,sy=.47,dx=370,dy=0)],700)
    put(0xBF,[C('?',sx=-1,sy=-1,dx=640,dy=520)])
    # Broad ligatures are authored as coherent forms at natural proportions.
    # They share the family's stroke weight instead of fitting two letters
    # into one terminal cell. Final text fitting is performed after assembly.
    ae_left=-90+weight*1.13
    ae_slope=328/700
    ae_lo=280-h;ae_hi=280+h
    ae_inner_apex=(280-weight/2-ae_left)/ae_slope
    put(0xC6,[fill(f'M-90 0L238 700H720V{700-2*h}H{280+weight/2}V{ae_hi}H655V{ae_lo}H{280+weight/2}V{2*h}H720V0H{280-weight/2}V{ae_lo}H{ae_left+ae_slope*ae_lo}L{ae_left} 0Z '
                  f'M{ae_left+ae_slope*ae_hi} {ae_hi}H{280-weight/2}V{ae_inner_apex}Z')],
        700,width=920,top=(300,735))
    bar(0xD0,'D','M35 350H375')
    put(0xD7,[S('M150 160L490 500M150 500L490 160')],700)
    bar(0xD8,'O','M115 30L525 670')
    put(0xDE,[S('M150 35V665M150 560H315C565 560 565 200 315 200H150')],700)
    put(0xDF,sharp_s_ops(weight),720,top=(313,775),bottom=(320,-45))
    put(0xE6,ae_ops(weight),width=940,top=(330,555))
    put(0xF0,eth_ops(weight),720,top=(304,775),bottom=(320,-45))
    put(0xF7,[S('M130 330H510'),ellipse(320,530,weight*.49),ellipse(320,130,weight*.49)])
    bar(0xF8,'o','M130 20L515 510')
    put(0xFE,[S('M145 -180V685M145 415C420 625 555 445 515 225C480 15 305 -20 145 100')],720,bottom=(320,-250))

    # Distinct extended Latin letters, not compatibility-folded substitutes.
    for cp,base,d in [
      (0x110,'D','M45 350H345'),(0x111,'d','M295 605H585'),
      (0x126,'H','M60 490H580'),(0x127,'h','M75 605H385'),
      (0x141,'L','M100 275L430 465'),(0x142,'l','M170 310L445 470'),
      (0x166,'T','M160 380H480'),(0x167,'t','M125 245H490'),
      (0x180,'b','M70 600H380'),(0x189,'D','M40 365H330'),
      (0x197,'I','M150 355H490'),(0x19A,'l','M160 305H480'),
      (0x19F,'O','M125 345C220 420 400 270 515 355'),
      (0x1B5,'Z','M150 350H490'),(0x1B6,'z','M145 260H495'),
      (0x1E4,'G','M285 270H590'),
      (0x23A,'A','M70 235L550 455'),(0x23B,'C','M140 295L505 480'),
      (0x23C,'c','M130 170L500 365'),(0x23D,'L','M75 365H380'),
      (0x23E,'T','M185 260L470 420'),(0x243,'B','M60 365H370'),
      (0x244,'U','M65 365H575'),(0x246,'E','M65 250L570 440'),
      (0x247,'e','M120 155L515 365'),(0x248,'J','M150 365H530'),
      (0x249,'j','M150 260H485'),(0x24C,'R','M70 360H470'),
      (0x24D,'r','M95 245H430'),(0x24E,'Y','M180 230H460'),
      (0x24F,'y','M140 160H485'),
    ]: bar(cp,base,d)
    put(0x1E5,[C('g'),S('M385 -55H605',.74)],
        top=reg[ord('g')]['top'],bottom=reg[ord('g')]['bottom'])
    pair(0x132,'I','J');pair(0x133,'i','j')
    put(0x138,[S('M145 35V485M505 485L145 195M285 305L515 35')])
    put(0x13F,[C('L'),ellipse(465,390,weight*.50)],700)
    put(0x140,[C('l'),ellipse(495,285,weight*.50)],720)
    put(0x149,[C('n',sx=.75,dx=155),C(0x2BC,sx=.65,sy=.7,dx=-10,dy=195)])
    put(0x14A,[S('M140 35V665L505 35V665M505 35V-75Q505 -185 390 -185H340')],700,bottom=(350,-250))
    put(0x14B,[S('M145 35V485M145 335C180 545 495 545 495 340V-70Q495 -185 365 -185H315')],bottom=(350,-250))
    put(0x152,[ellipse(110,350,225,350+10-h,stroked=True),
              S(f'M735 {700-h}H335V{h}H735M335 350H670')],
        700,width=960,top=(305,735))
    put(0x153,[ellipse(110,260,225,260+10-h,stroked=True),
              S(f'M335 265H768C768 414 691 {520-h+8} 555 {520-h+8}C410 {520-h+8} 335 410 335 260C335 108 412 {h-8} 557 {h-8}C649 {h-8} 719 62 759 105')],
        width=960,top=(320,555))
    put(0x17F,[S('M270 35V555C270 720 435 745 530 650')],720)

    # Shared anatomies for hooked and historical forms.
    hook(0x181,'B','M145 640C145 790 60 765 75 650',700)
    put(0x182,[S('M145 35V665H400M145 440H325C595 440 595 35 325 35H145')],700)
    put(0x183,[C('b'),S('M120 710H400')],720)
    put(0x184,[S('M470 660H165V35M165 440H325C595 440 595 35 325 35H165')],700)
    put(0x185,[C(0x184,sy=520/700)])
    reflected(0x186,'C',700)
    hook(0x187,'C','M500 605Q630 715 540 770',700)
    hook(0x188,'c','M500 430Q620 550 535 610')
    hook(0x18A,'D','M145 650C145 780 20 770 40 650',700)
    reflected(0x18B,0x182,700);reflected(0x18C,0x183,720)
    turned(0x18D,0x1E9F)
    reflected(0x18E,'E',700)
    put(0x18F,[C('e',sx=-1,sy=-700/520,dx=640,dy=700)],700)
    put(0x190,[S('M515 605C300 800 75 625 145 440Q180 350 320 350Q170 350 140 250C80 50 320 -75 525 115')],700)
    hook(0x191,'F','M155 120V-50Q155 -180 45 -180',700)
    put(0x192,[S('M100 -120Q280 -205 320 0L390 510Q425 750 580 665M165 350H535')],700,bottom=(320,-260))
    hook(0x193,'G','M485 610Q640 735 535 790',700)
    put(0x194,[S('M105 665L305 245L515 665M305 245C100 -70 520 -70 305 245')],700)
    pair(0x195,'h','v')
    put(0x196,[S('M380 665H255V150Q255 35 385 35H455')],700)
    hook(0x198,'K','M140 645Q135 780 30 720',700)
    hook(0x199,'k','M140 645Q135 780 30 720',720)
    put(0x19B,[S('M125 690C275 700 280 540 325 440L520 35M325 440L100 35M175 260L475 445')],720)
    turned(0x19C,'M',700)
    hook(0x19D,'N','M140 95V-75Q140 -200 45 -170',700)
    hook(0x19E,'n','M500 220V-210')
    put(0x1A2,[C('O',sx=.74,dx=-5),S('M420 55V625C420 770 580 755 580 625V-145')],700,bottom=(320,-250))
    put(0x1A3,[C('o',sx=.74,dx=-5),S('M420 60V440C420 590 580 580 580 435V-150')],bottom=(320,-250))
    hook(0x1A4,'P','M140 645C140 775 15 750 40 635',700)
    hook(0x1A5,'p','M145 450C140 580 25 570 40 455')
    put(0x1A6,[S('M125 35V665H325C565 665 565 360 325 360H125M325 360L520 35M520 35V350')],700)
    reflected(0x1A7,'2',700);put(0x1A8,[C(0x1A7,sy=520/700)])
    put(0x1A9,[S('M525 665H130L385 350L130 35H525')],700)
    put(0x1AA,[C(0x283,sx=-1,dx=640),S('M410 150C550 230 590 20 440 -65')],720)
    hook(0x1AB,'t','M286 132V-80C286 -200 186 -180 196 -95')
    hook(0x1AC,'T','M500 665Q635 700 575 790',700)
    hook(0x1AD,'t','M407 488Q537 528 472 638')
    hook(0x1AE,'T','M320 110V-75C320 -195 430 -165 420 -95',700)
    put(0x1B1,[S('M115 665H220M525 665H420M165 665V255C165 -65 475 -65 475 255V665')],700)
    put(0x1B2,[S('M105 665L270 65C530 -75 620 450 490 665')],700)
    hook(0x1B3,'Y','M500 650Q640 755 535 800',700)
    hook(0x1B4,'y','M500 465Q635 570 535 625')
    put(0x1B7,[S('M115 665H525L295 390C565 445 605 35 335 35H140')],700)
    reflected(0x1B8,0x1B7,700)
    put(0x1B9,[C(0x1B8,sy=520/700)])
    hook(0x1BA,0x292,'M475 60V-155Q475 -235 565 -180')
    bar(0x1BB,'2','M160 290H495',700)
    put(0x1BC,[S('M520 665H145V385H335C590 385 580 35 325 35H130')],700)
    put(0x1BD,[C(0x1BC,sy=520/700)])
    bar(0x1BE,0x296,'M120 200H470')
    put(0x1BF,[S('M145 -185V485C545 555 585 145 145 95')],bottom=(320,-250))
    put(0x1C0,[S('M320 35V665',.70)],700)
    put(0x1C1,[S('M220 35V665M420 35V665',.70)],700)
    put(0x1C2,[S('M320 35V665M165 290H475M165 430H475',.70)],700)
    alias(0x1C3,'!')
    for cp,l,r in [(0x1C4,'D',0x17D),(0x1C5,'D',0x17E),(0x1C6,'d',0x17E),
                   (0x1C7,'L','J'),(0x1C8,'L','j'),(0x1C9,'l','j'),
                   (0x1CA,'N','J'),(0x1CB,'N','j'),(0x1CC,'n','j'),
                   (0x1F1,'D','Z'),(0x1F2,'D','z'),(0x1F3,'d','z')]: pair(cp,l,r)
    turned(0x1DD,'e')
    pair(0x1F6,'H','V')
    put(0x1F7,[S('M145 -160V665C580 730 590 245 145 185')],700,bottom=(320,-250))
    put(0x21C,[S('M125 575C220 750 535 735 505 545Q480 425 310 370C550 360 570 150 445 15Q330 -110 155 -45')],700,bottom=(320,-130))
    put(0x21D,[C(0x21C,sy=520/700)])
    hook(0x220,'N','M500 180V-210',700)
    hook(0x221,'d','M480 90C680 80 545 -125 435 -75')
    put(0x222,[ellipse(320,205,190,170,stroked=True),S('M170 665V490C170 300 470 300 470 490V665')],700)
    put(0x223,[C(0x222,sy=520/700)])
    hook(0x224,'Z','M480 120V-50C480 -190 580 -155 575 -80',700)
    hook(0x225,'z','M480 120V-50C480 -190 580 -155 575 -80')
    for cp,base,d in [(0x234,'l','M355 38C540 48 445 -172 315 -112'),
                      (0x235,'n','M495 70C680 80 585 -140 455 -80'),
                      (0x236,'t','M385 36C570 46 475 -174 345 -114')]:
        hook(cp,base,d)
    pair(0x238,'d','b');pair(0x239,'q','p')
    for cp,base in [(0x23F,'s'),(0x240,'z')]:
        hook(cp,base,'M450 55C530 -75 385 -225 245 -175')
    put(0x241,[S('M145 535C145 770 515 770 515 535C515 395 320 405 320 255V35')],700)
    put(0x242,[C(0x241,sy=520/700)])
    turned(0x245,'V',700)
    hook(0x24A,'Q','M430 60V-60Q430 -180 560 -145',700)
    hook(0x24B,'q','M470 -70Q470 -240 585 -145')

    # IPA: small capitals, rotations, hooks and independently authored anatomies.
    turned(0x250,'a')
    put(0x251,[ellipse(300,260,180,225,stroked=True),S('M480 485V35H535')])
    turned(0x252,0x251)
    hook(0x253,'b','M145 650C145 780 30 745 40 635',720)
    reflected(0x254,'c')
    hook(0x255,'c','M460 115C635 70 515 -135 415 -65')
    hook(0x256,'d','M480 85V-80Q480 -205 580 -170')
    hook(0x257,'d','M475 650C470 790 595 755 580 630',720)
    reflected(0x258,'e')
    alias(0x259,0x1DD)
    hook(0x25A,0x259,'M470 275Q610 350 580 195')
    put(0x25B,[S('M500 440C300 580 105 440 150 325Q180 260 320 260Q180 260 145 185C80 25 330 -50 510 105')])
    reflected(0x25C,0x25B)
    hook(0x25D,0x25C,'M480 255Q625 345 585 195')
    put(0x25E,[C(0x25C),S('M145 95C80 175 80 350 145 430')])
    bar(0x25F,0x237,'M165 270H505')
    hook(0x260,'g','M500 440Q635 590 535 630')
    put(0x261,[ellipse(300,265,185,220,stroked=True),S('M485 485V-60Q485 -245 155 -160')],bottom=(320,-265))
    smallcap(0x262,'G')
    put(0x263,[S('M105 485L320 35L535 485M320 35C115 -260 525 -260 320 35')],bottom=(320,-265))
    put(0x264,[S('M320 35L150 330Q75 490 175 490Q275 490 275 340M320 35L490 330Q565 490 465 490Q365 490 365 340')])
    turned(0x265,'h')
    hook(0x266,'h','M145 650Q140 790 25 720',720)
    hook(0x267,0x266,'M495 165V-60Q495 -205 370 -185',720)
    bar(0x268,0x131,'M165 265H500')
    put(0x269,[S('M260 485V130Q260 35 365 35H425')])
    smallcap(0x26A,'I')
    bar(0x26B,'l','M135 300C235 405 350 225 475 330',720)
    put(0x26C,[C('l'),S('M320 400C90 425 115 250 320 280H440')],720)
    hook(0x26D,'l','M280 100V-70C280 -185 410 -165 380 -90',720)
    pair(0x26E,'l',0x292)
    turned(0x26F,'m')
    hook(0x270,0x26F,'M640 400V-190')
    hook(0x271,'m','M640 170V-65Q640 -200 515 -165')
    hook(0x272,'n','M145 165V-65Q145 -205 45 -165')
    hook(0x273,'n','M495 135V-65Q495 -200 580 -170')
    smallcap(0x274,'N')
    bar(0x275,'o','M140 260H505')
    smallcap(0x276,0x152)
    put(0x277,[S('M320 375C170 640 55 320 160 105C230 -35 410 -35 480 105C585 320 470 640 320 375M320 375V130')])
    put(0x278,[ellipse(320,270,210,210,stroked=True),S('M320 -170V655')],720,bottom=(320,-250))
    turned(0x279,'r')
    hook(0x27A,0x279,'M428 420V-200')
    hook(0x27B,0x279,'M428 180V-70Q428 -200 523 -155')
    hook(0x27C,'r','M212 180V-210')
    hook(0x27D,'r','M212 180V-70Q212 -200 337 -160')
    put(0x27E,[S('M235 35V315C235 510 410 565 510 440')])
    reflected(0x27F,0x27E)
    smallcap(0x280,'R');turned(0x281,0x280)
    hook(0x282,'s','M445 80V-70Q445 -200 565 -155')
    put(0x283,[S('M140 -155C265 -225 335 -115 335 70V460C335 705 455 780 555 660')],720,bottom=(320,-265))
    hook(0x284,0x25F,'M350 470Q350 665 525 590')
    put(0x285,[C(0x283,sx=-1,sy=.72,dx=640,dy=0)])
    hook(0x286,0x283,'M410 610C590 750 610 555 480 550',720)
    turned(0x287,'t')
    hook(0x288,'t','M286 135V-75C286 -205 421 -165 391 -85')
    bar(0x289,'u','M100 260H555')
    put(0x28A,[S('M110 485H230M530 485H410M160 485V205C160 -40 480 -40 480 205V485')])
    put(0x28B,[S('M105 485L270 45C505 -65 590 300 490 485')])
    turned(0x28C,'v');turned(0x28D,'w');turned(0x28E,'y')
    smallcap(0x28F,'Y')
    hook(0x290,'z','M455 100V-70C455 -190 570 -160 550 -85')
    hook(0x291,'z','M460 90C635 90 535 -130 420 -70')
    put(0x292,[S('M135 485H510L300 260C580 290 610 -175 300 -175H155')],bottom=(320,-250))
    hook(0x293,0x292,'M475 -105C650 -40 610 -240 460 -220')
    put(0x294,[S('M145 535C145 770 515 770 515 535C515 395 320 405 320 255V35')],700)
    reflected(0x295,0x294,700)
    turned(0x296,0x294,700)
    put(0x297,[S('M515 665C215 805 75 475 115 190C145 -70 410 -155 530 65')],700,bottom=(320,-175))
    put(0x298,[C('O'),ellipse(320,350,weight*.49)],700)
    smallcap(0x299,'B')
    put(0x29A,[C(0x25B),S('M495 110C560 180 560 365 495 425')])
    hook(0x29B,0x262,'M470 460Q595 575 535 655')
    smallcap(0x29C,'H')
    hook(0x29D,'j','M250 -145L440 -30')
    turned(0x29E,'k')
    smallcap(0x29F,'L')
    hook(0x2A0,'q','M470 455Q615 555 560 655')
    bar(0x2A1,0x294,'M155 270H490',700)
    bar(0x2A2,0x295,'M155 270H490',700)
    for cp,l,r in [(0x2A3,'d','z'),(0x2A4,'d',0x292),(0x2A5,'d',0x291),
                   (0x2A6,'t','s'),(0x2A7,'t',0x283),(0x2A8,'t',0x255),
                   (0x2A9,'f',0x14B),(0x2AA,'l','s'),(0x2AB,'l','z')]:pair(cp,l,r)
    put(0x2AC,[S('M115 485L220 305L320 465L420 305L525 485M115 215L220 35L320 195L420 35L525 215')])
    put(0x2AD,[S('M135 485V315H505V485M135 205V35H505V205')])
    hook(0x2AE,0x265,'M490 430Q630 555 550 655')
    hook(0x2AF,0x2AE,'M490 120V-70Q490 -205 580 -155')

    # Spacing modifier letters retain distinct raised/low positions and widths.
    supers = {0x2B0:'h',0x2B1:0x266,0x2B2:'j',0x2B3:'r',0x2B4:0x279,
              0x2B5:0x27B,0x2B6:0x281,0x2B7:'w',0x2B8:'y',
              0x2C0:0x294,0x2C1:0x295,0x2E0:0x263,0x2E1:'l',
              0x2E2:'s',0x2E3:'x',0x2E4:0x295}
    for cp,base in supers.items():put(cp,[C(base,sx=.55,sy=.55,dx=144,dy=360)],760)
    modpaths={
      0x2B9:'M275 475L365 690',0x2BA:'M185 475L275 690M365 475L455 690',
      0x2BB:'M360 700C225 665 220 555 310 525',
      0x2BC:'M300 700C415 645 385 545 260 510',
      0x2BD:'M340 700C225 645 255 545 380 510',
      0x2BE:'M260 500C470 500 470 730 260 730',
      0x2BF:'M380 500C170 500 170 730 380 730',
      0x2C2:'M400 180L235 310L400 440',0x2C3:'M240 180L405 310L240 440',
      0x2C4:'M175 230L320 380L465 230',0x2C5:'M175 380L320 230L465 380',
      0x2C8:'M320 440V700',0x2CC:'M320 -210V50',
      0x2D2:'M260 160C470 160 470 390 260 390',
      0x2D3:'M380 160C170 160 170 390 380 390',
      0x2D4:'M175 200H465M320 200V420',0x2D5:'M175 410H465M320 410V190',
      0x2D6:'M175 300H465M320 155V445',0x2D7:'M175 300H465',
      0x2DE:'M220 280Q470 440 420 210',0x2DF:'M220 530L420 730M220 730L420 530',
      0x2EA:'M180 650V100H465',0x2EB:'M180 650V100H465M180 375H465',
      0x2EC:'M190 -40L320 -165L450 -40',0x2ED:'M180 535H460M180 655H460',
      0x2EE:'M240 710C350 650 310 555 180 510M410 710C520 650 480 555 350 510',
      0x2EF:'M190 -35L320 -165L450 -35',0x2F0:'M190 -165L320 -35L450 -165',
      0x2F1:'M405 10L235 -105L405 -210',0x2F2:'M235 10L405 -105L235 -210',
      0x2F4:'M260 425L380 245',0x2F5:'M180 425L280 245M355 425L455 245',
      0x2F6:'M180 245L280 425M355 245L455 425',
      0x2F9:'M190 450V700H450',0x2FA:'M190 700H450V450',
      0x2FB:'M190 50V300H450',0x2FC:'M190 300H450V50',
      0x2FD:'M170 160V35H470V160',0x2FE:'M170 160V35H470',
      0x2FF:'M500 60H150L255 155M150 60L255 -35',
    }
    for cp,d in modpaths.items():put(cp,[S(d,.76)],700)
    accents={0x2C6:(0x302,520),0x2C7:(0x30C,520),0x2C9:(0x304,565),
      0x2CA:(0x301,520),0x2CB:(0x300,520),0x2CD:(0x331,0),
      0x2CE:(0x316,0),0x2CF:(0x317,0),0x2D8:(0x306,520),
      0x2D9:(0x307,520),0x2DA:(0x30A,520),0x2DB:(0x328,0),
      0x2DC:(0x303,520),0x2DD:(0x30B,520),0x2F7:(0x330,0)}
    for cp,(base,dy) in accents.items():put(cp,[C(base,dx=320,dy=dy)],700)
    tri=fill('M260 400H380L320 300Z')
    put(0x2D1,[tri])
    put(0x2D0,[tri,fill('M260 180H380L320 280Z')])
    for cp,level in zip(range(0x2E5,0x2EA),[660,510,360,210,60]):
        put(cp,[S(f'M435 35V685M180 {level}H435',.74)],700)
    put(0x2F3,[ellipse(320,-90,75,stroked=True,width=.68)])
    put(0x2F8,[ellipse(320,545,weight*.4),ellipse(320,700,weight*.4)],760)

    # Additional historical forms in the requested complete Additional block.
    put(0x1E9A,[C('a'),C(0x2BE,sx=.45,sy=.5,dx=350,dy=250)])
    bar(0x1E9C,0x17F,'M160 250L445 470',720)
    bar(0x1E9D,0x17F,'M140 540H445',720)
    put(0x1E9E,capital_sharp_s_ops(weight),700,top=(361,735),bottom=(350,-35))
    reg[0x1E9E]['dotbelow']=(350,-10)
    put(0x1E9F,[S('M470 675C300 650 100 505 135 245C170 -35 530 -30 510 225C495 395 345 450 220 465')],720)
    pair(0x1EFA,'L','L');pair(0x1EFB,'l','l')
    put(0x1EFC,[C('V'),S('M120 640Q50 795 200 735')],700)
    put(0x1EFD,[C('v'),S('M120 465Q50 620 200 560')])
    put(0x1EFE,[C('Y'),ellipse(315,410,90,105,stroked=True,width=.8)],700)
    put(0x1EFF,[C('y'),ellipse(315,275,85,95,stroked=True,width=.8)])

    # Optical attachment origins remain in the original design coordinate
    # system. Final proportional fitting translates bases and these anchors
    # together. Marks may overhang; their width must not widen the base cell.
    for base in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
        g=reg[ord(base)]
        if g.get('top'):
            x,y=g['top'];g['top']=(x,y-20)
        if g.get('bottom') and g['bottom'][1]>-100:
            x,_=g['bottom'];g['bottom']=(x,-35)
        if base not in 'gpqjy':g['dotbelow']=(g.get('bottom',(320,0))[0],-10)
    reg[ord('y')]['dotbelow']=(440,-15)
    # Below signs balance the l stem and its baseline curl. Underdots retain
    # their independent attachment point.
    reg[ord('l')]['bottom']=(300,-35)
    reg[0x1E5]['top']=reg[ord('g')]['top']
    reg[0x1E5]['bottom']=reg[ord('g')]['bottom']
    reg[0x131]['top']=(320,550)
    # Removing a dot for an above accent must not move a lower accent.
    reg[0x131]['bottom']=reg[ord('i')]['bottom']
    reg[0x131]['dotbelow']=reg[ord('i')]['dotbelow']
    reg[0x237]['top']=(320,550)
    reg[0x131]['ogonek']=(320,0)
    # Narrow l/i need attachment points on their actual strokes, not on the
    # former wide foot used to occupy a monospaced cell.
    reg[ord('i')]['ogonek']=(320,0)
    reg[ord('I')]['ogonek']=(350,0)

    # The engine assembles only canonical decompositions. Distinct compatibility
    # characters above retain deliberately authored shapes and encoded identity.
    ranges=[(0xA0,0x36F),(0x1E00,0x1EFF)]
    for first,last in ranges:
        for cp in range(first,last+1):
            if cp in reg: continue
            dec=ud.decomposition(chr(cp))
            if dec and not dec.startswith('<'):
                rec=glyph(reg,cp,[],note=ud.name(chr(cp)))
                rec['decomposition']=[int(x,16) for x in dec.split()]
    missing=[f'U+{cp:04X} {ud.name(chr(cp),"UNASSIGNED")}'
             for first,last in ranges for cp in range(first,last+1) if cp not in reg]
    if missing: raise ValueError('Unimplemented extended Latin: '+', '.join(missing))
