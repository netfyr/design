"""Forty original keyboard, state and geometric symbol recipes.

Unicode names and official chart annotations establish the intended character,
not an outline to copy. The selected repertoire is explicitly enumerated; this
module does not claim complete Miscellaneous Technical or dingbat coverage.
All symbols keep the family's 640-unit advance. Their inset artwork is not a
cell-joining rule; the full-cell rules live in technical.py.
"""
from math import cos, sin, pi
import unicodedata as ud
from model import glyph, stroke, fill, rect, ellipse, component

CODEPOINTS=(0x2303,0x2318,0x2325,0x2326,0x232B,0x238B,0x23CE,0x23CF,
            0x23FB,0x23FC,0x23FD,0x23FE,
            0x25A0,0x25A1,0x25AA,0x25AB,0x25B2,0x25B3,0x25B6,0x25B7,
            0x25BC,0x25BD,0x25C0,0x25C1,0x25C6,0x25C7,0x25C9,0x25CB,
            0x25CF,0x25EF,0x2605,0x2606,0x2610,0x2611,0x2612,
            0x2713,0x2714,0x2717,0x2718,0x26A0)


def _poly(points):
    points=list(points)
    if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))>0:
        points.reverse()
    return fill('M'+'L'.join(f'{x:.5f} {y:.5f}' for x,y in points)+'Z')


def build(reg, weight):
    if not 40<=weight<=170:raise ValueError('Interface stem outside reviewed expansion range')
    made=set()
    def put(cp,ops,note=''):
        glyph(reg,cp,ops,width=640,note=ud.name(chr(cp))+'; original inset geometry. '+note)
        made.add(cp)
    def s(d,k=.72):return stroke(d,k,optical=False)
    def ring(r=210,k=.72):
        op=ellipse(320,350,r,stroked=True,width=k);op['optical']=False;return op
    def outline(points,k=.72):
        return s('M'+'L'.join(f'{x} {y}' for x,y in points)+'Z',k)
    def check(k=.8):return s('M100 345L245 175L545 600',k)
    def cross(k=.8):return [s('M130 140L510 560',k),s('M130 560L510 140',k)]

    # Keyboard symbols retain conventional functional distinctions. The four
    # command loops are a single authored path around a central rectangle.
    put(0x2303,[s('M120 310L320 540L520 310')])
    put(0x2318,[s('M220 450H490Q560 450 560 520Q560 590 490 590'
                   'Q420 590 420 520V180Q420 110 490 110Q560 110 560 180'
                   'Q560 250 490 250H150Q80 250 80 180Q80 110 150 110'
                   'Q220 110 220 180V520Q220 590 150 590Q80 590 80 520'
                   'Q80 450 150 450Z',.66)])
    put(0x2325,[s('M85 605H215L425 95H555 M375 605H555')])
    put(0x232B,[outline([(75,350),(235,560),(560,560),(560,140),(235,140)],.65),
                  s('M295 260L460 440 M295 440L460 260',.62)])
    put(0x2326,[component(0x232B,sx=-1,dx=640)])
    # An open circular boundary and a northwest-pointing arrow are explicit;
    # this is not a closed circle crossed by an undirected diagonal.
    put(0x238B,[s('M350 585C590 595 630 265 430 155C270 60 90 190 110 360',.7),
                  s('M365 315L95 585 M95 440V585H240',.7)])
    put(0x23CE,[outline([(540,650),(430,650),(430,350),(265,350),(265,485),
                        (65,295),(265,105),(265,240),(540,240)],.58)],
        'A hollow bent return arrow; U+21B5 remains a separate arrow glyph.')
    put(0x23CF,[_poly([(100,280),(320,645),(540,280)]),rect(100,80,440,95)])

    # Standby has an open ring. On-off closes that ring; on is a single rule.
    # The sleep crescent is one filled contour, with a deliberately open right.
    put(0x23FB,[s('M190 550C-5 405 85 100 320 100C555 100 645 405 450 550',.85),
                  s('M320 350V690',.85)])
    put(0x23FC,[ring(235,.85),s('M320 350V585',.85)])
    put(0x23FD,[s('M320 90V650',.95)])
    put(0x23FE,[fill('M420 650C225 690 70 540 90 340C105 135 325 50 505 180'
                       'C320 150 220 280 250 450C267 545 326 613 420 650Z')])

    # Filled and outlined shapes have the same nominal outer construction.
    # Small squares and the large circle have intentionally distinct scales.
    put(0x25A0,[rect(100,130,440,440)])
    put(0x25A1,[outline([(100,130),(100,570),(540,570),(540,130)])])
    put(0x25AA,[rect(195,225,250,250)])
    put(0x25AB,[outline([(195,225),(195,475),(445,475),(445,225)],.62)])
    triangles={0x25B2:[(85,100),(320,620),(555,100)],
               0x25B6:[(110,80),(110,620),(570,350)],
               0x25BC:[(85,600),(555,600),(320,80)],
               0x25C0:[(70,350),(530,620),(530,80)]}
    for cp,p in triangles.items():
        put(cp,[_poly(p)]);put(cp+1,[outline(p,.66)])
    diamond=[(320,650),(565,350),(320,50),(75,350)]
    put(0x25C6,[_poly(diamond)]);put(0x25C7,[outline(diamond,.66)])
    put(0x25C9,[ring(),ellipse(320,350,108)])
    put(0x25CB,[ring()]);put(0x25CF,[ellipse(320,350,210)])
    put(0x25EF,[ring(265,.66)])

    star=[]
    for i in range(10):
        angle=pi/2+i*pi/5;r=265 if i%2==0 else 112
        star.append((320+r*cos(angle),350+r*sin(angle)))
    put(0x2605,[_poly(star)]);put(0x2606,[outline(star,.6)])
    box=[outline([(85,115),(85,585),(555,585),(555,115)],.62)]
    put(0x2610,box)
    put(0x2611,box+[s('M175 355L285 235L485 505',.7)])
    put(0x2612,box+[s('M180 225L460 475 M180 475L460 225',.7)])
    put(0x2713,[check(.8)]);put(0x2714,[check(1.35)])
    put(0x2717,cross(.8));put(0x2718,cross(1.35))
    put(0x26A0,[outline([(60,80),(320,670),(580,80)],.64),
                  s('M320 445V255',.82),ellipse(320,172,weight*.44)])
    assert made==set(CODEPOINTS),(made^set(CODEPOINTS))
