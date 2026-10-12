"""Individual symbol corrections from the complete 28-style visual ledger.

Only enumerated targets change. Centerlines and compositions are our existing
editable drawings or newly authored geometry; comparison fonts supply no paths.
Dense symbols bound local stroke growth to preserve semantic parts at text size.
"""
from functools import lru_cache
from pathlib import Path
import copy
import math

from compiled_repairs import (repair, record, corrected_record, combine, bounds,
                              transformed, expand_stroke, slant_matrix)
from outlines import Resolver, path_recording
from model import stroke, fill, ellipse, rect, component, transform_ops
import expand_family
import technical

TARGETS = tuple(int(code, 16) for code in '''
201C 201D 201E 201F 2026 2030 2031 2034 2037 2042 204C 204D 204E 2051 2055 2057 205F
20A1 20A4 20A6 20A9 20AA 20AC 20B0 20B1 20B6 20B7 20B9 20BA 20BB 20BD 20BE 20BF
2102 2103 2104 2109 210C 210D 210F 2111 2115 2117 2118 211A 211C 211D 2123 2124
2127 212F 2133 2135 213C 213D 213E 213F 2140 2145 2146 2147 2148 2149 214C 214F
219E 219F 21A0 21A1 21AB 21AC 21AE 21CD 21CE 21CF 21D0 21D1 21D2 21D3 21D4 21D5
21D6 21D7 21D8 21D9 21DA 21DB 21DC 21DD 21DE 21DF 21EA 21EC 21ED 21EE 21EF 21F0
21F1 21F2 21F4 21FA 21FB 21FC 21FD 21FE 21FF 2200 2204 2206 2209 220C 2217 2218
221E 221F 2221 2222 2224 2226 222E 222F 2230 2231 2232 2233 2240 2244 2245 2246
2247 2249 224C 2250 2251 2252 2253 2254 2255 2256 2257 2258 2259 225A 225B 225C
225D 225E 225F 2260 2262 2263 2266 2267 2268 2269 226C 226D 2270 2271 2274 2275
2278 2279 227C 227D 2284 2285 2288 2289 228A 228B 228C 228E 2291 2292 229A 229B
22A7 22A9 22AA 22AB 22AC 22AD 22AE 22AF 22B0 22B1 22B6 22B7 22B8 22B9 22BA 22BB
22BC 22BE 22C7 22C8 22C9 22CA 22D0 22D1 22D2 22D3 22D5 22D6 22D7 22DE 22DF
22E0 22E1 22E2 22E3 22E4 22E5 22E6 22E7 22E8 22E9 22EA 22EB 22EC 22ED 22F2
22F3 22F4 22F6 22F7 22F8 22FA 22FB 22FC 22FD 22FE 2318 238B 23CE 23FC 25C9
2611 2612 26A0 FFFD
'''.split())

# These alter identity or missing parts, so their corrections apply in every face.
SEMANTIC = {
    0x205F, 0x20A4, 0x20BD, 0x2104, 0x2117, 0x2118, 0x2123, 0x2124, 0x2127, 0x2135,
    0x21AB, 0x21AC, 0x21DC, 0x21DD, 0x21DE, 0x21DF, 0x21EA, 0x21EC, 0x21ED, 0x21F4,
    0x2204, 0x221F, 0x2221, 0x2222, 0x2224, 0x2226, 0x2231, 0x2232, 0x2233,
    0x2240, 0x2270, 0x2271, 0x227C, 0x227D,
    0x2288, 0x2289, 0x22A7, 0x22B0, 0x22B1,
    0x22BA, 0x22BE, 0x22C7, 0x22DE, 0x22DF, 0x22E0, 0x22E1, 0x22E2, 0x22E3,
    0x22EC, 0x22ED,
    0x22F2, 0x22F3, 0x22F4, 0x22FA, 0x22FB, 0x22FC, 0x23FC,
}

# Small enclosures need less growth than full-size symbols, independently of
# the master weight. Limits are attached to reviewed targets, not the family.
LIMITS = {
    0x2030: 56, 0x2031: 56, 0x2042: 76, 0x204E: 76, 0x2051: 76, 0x2055: 68,
    0x2102: 72, 0x2103: 62, 0x2109: 62, 0x210D: 72, 0x2115: 72,
    0x2117: 80, 0x211A: 72, 0x211D: 72, 0x213C: 68, 0x213D: 68,
    0x213E: 68, 0x213F: 68, 0x2140: 68, 0x2145: 68, 0x2146: 68,
    0x2147: 68, 0x2148: 48, 0x2149: 48, 0x214F: 74,
    0x2218: 66, 0x222E: 76, 0x222F: 72, 0x2230: 72,
    0x2231: 76, 0x2232: 76, 0x2233: 76, 0x2256: 60, 0x2257: 60,
    0x229A: 64, 0x229B: 76, 0x22B6: 68, 0x22B7: 68, 0x22B8: 72,
    0x22B9: 76, 0x22D0: 76, 0x22D1: 76, 0x22D2: 76, 0x22D3: 76,
    0x2318: 68, 0x23CE: 78, 0x25C9: 80, 0x2611: 82, 0x2612: 80,
    0x26A0: 80, 0xFFFD: 80,
}
for _cp in TARGETS:
    if 0x2190 <= _cp <= 0x21FF:
        LIMITS[_cp] = 72


def s(d, width=.85):
    return stroke(d, width, optical=False)


def line(x1, y1, x2, y2, width=.85):
    return s(f'M{x1} {y1}L{x2} {y2}', width)


def bar(y, x1=115, x2=525, width=.85):
    return line(x1, y, x2, y, width)


def flip(ops):
    return transform_ops(ops, sx=-1, dx=640)


def preceding(y=300):
    return [s(f'M510 {y+150}Q355 {y+55} 130 {y}Q355 {y-55} 510 {y-150}')]


def lower_relation(y):
    return [s(f'M130 {y}Q355 {y-55} 510 {y-150}')]


def upper_relation(y):
    return [s(f'M510 {y+150}Q355 {y+55} 130 {y}')]


def add_cancel(reg, cp, base, low=-45, high=740):
    reg[cp]['ops'] = copy.deepcopy(reg[base]['ops']) + [line(175, low, 465, high, .65)]


def revise(reg, w):
    """Correct authored centerlines before native vector stroke expansion."""
    t = min(w * .68, 49)
    def put(cp, ops):
        reg[cp]['ops'] = ops
    # Keep the lira's two crossbars distinct from the single-bar pound.
    put(0x20A4, [s('M135 75H540 M190 75V500C190 795 460 785 530 590', .9),
                 bar(305, 100, 445, .6), bar(440, 100, 445, .6)])
    # Bound both crossbars to the established ink span so fitting preserves N stems.
    put(0x20A6, [component('N'), bar(290, 55, 585, .65), bar(440, 55, 585, .65)])
    put(0x20A9, [component('W'), bar(365, 30, 610, .65)])
    put(0x20B1, [component('P'), bar(475, 0, 640, .5), bar(610, 0, 640, .5)])
    put(0x20AC, [component('C'), bar(420, -20, 440, .6), bar(265, -20, 420, .6)])
    put(0x20BD, [component('P'), bar(195, 30, 435, .65)])
    put(0x2104, [component('C'), s('M300 760V-55H625', .7)])
    put(0x2117, [ellipse(320,350,285,stroked=True,width=.7),
                 component('P',sx=.5,sy=.52,dx=160,dy=175)])
    put(0x210F, [component('h',sx=.84,xy=.16,dx=8), line(50,575,415,640,.55)])
    put(0x2123, [component('V'), s('M160 -110L450 745L225 805', .6)])
    put(0x2118, [s('M235 430C80 540 65 325 180 350C340 385 520 625 525 420'
                   'C530 160 370 40 235 95C90 150 130 450 235 430'
                   'C320 420 205 70 195 -125C180 -300 -10 -220 65 -65'
                   'C120 45 225 115 240 200', .8)])
    put(0x2124, [bar(675, 115, 530, .8), bar(25, 105, 525, .8),
                 line(150, 25, 535, 675, .42), line(50, 25, 435, 675, .42)])
    # Hebrew alef has a central oblique, opposing branches and visible terminals.
    put(0x2135, [s('M140 625L500 75 M130 560L280 410L170 60'
                   ' M505 655L415 455L320 350 M100 55H230 M405 660H535', .85)])
    for cp, direction in [(0x21AB, 'L'), (0x21AC, 'R')]:
        ops = [s('M100 375H450C585 375 585 605 455 605'
                 'C355 605 355 450 455 375V240', t/w)]
        ops += technical._head((100, 375), (-1, 0), t)
        put(cp, ops if direction == 'L' else flip(ops))
    zig = [(100,375),(165,445),(235,305),(305,445),(375,305),(445,375),(540,375)]
    squiggle = technical._lines(zig,t,True)+technical._head((540,375),(1,0),t)
    put(0x21DD, squiggle);put(0x21DC, flip(squiggle))
    up = technical._arrow(*technical._axis('U'),t)
    up += [technical._line((195,y),(445,y),t) for y in (285,435)]
    put(0x21DE,up);put(0x21DF,transform_ops(up,sx=-1,sy=-1,dx=640,dy=750))
    white = technical._white_arrow('U',t*.8,w,base=225)
    white += [s('M190 25H450V135H190Z',t*.7/w)]
    put(0x21EA,white)
    pedestal = technical._white_arrow('U',t*.8,w,pedestal=True)
    put(0x21EC,pedestal+[bar(485,230,410,t*.7/w)])
    put(0x21ED,pedestal+[line(320,85,320,715,t*.6/w)])
    ring = ellipse(320,375,120,stroked=True,width=min(t*.65,24)/w)
    ring['optical'] = False
    put(0x21F4,[ring]+technical._arrow((100,375),(550,375),t))
    # Measured and spherical angles have arcs crossing, rather than ending
    # inside, their angle limbs. Their authored curvature is independent.
    put(0x2221,[s('M520 625L115 90H555',.8),s('M380 15Q440 230 270 370',.7)])
    put(0x2222,[s('M535 615L120 315L535 15',.8),s('M375 670C535 515 535 115 375 -40',.7)])
    for cp,base,rx in [(0x222F,0x222C,280),(0x2230,0x222D,320)]:
        oval = ellipse(320,350,rx,145,stroked=True,width=.5)
        oval['optical'] = False
        put(cp,copy.deepcopy(reg[base]['ops'])+[oval])
    put(0x2240,flip(reg[0x2240]['ops']))
    pe = preceding(400)+lower_relation(200)
    ep = preceding(200)+upper_relation(400)
    put(0x227C,pe);put(0x227D,flip(pe));put(0x22DE,ep);put(0x22DF,flip(ep))
    curly = [s('M415 575C540 690 620 465 450 400Q355 355 130 300'
               'Q355 245 450 200C620 135 540 -90 415 25')]
    put(0x22B0,curly);put(0x22B1,flip(curly))
    put(0x22A7,[line(150,45,150,600),bar(220,150,555),bar(420,150,555)])
    put(0x22BA,[bar(550,110,530),line(320,100,320,550)])
    put(0x22C7,[line(180,160,460,440,.7),line(180,440,460,160,.7),
                 bar(300,100,540,.7),ellipse(320,530,38),ellipse(320,70,38)])
    member = [s('M535 520H300C45 520 45 80 300 80H535 M115 300H535')]
    put(0x22F2,member+[bar(300,-75,535)])
    put(0x22F3,member+[line(535,200,535,400,.65)])
    put(0x22F4,transform_ops(reg[0x22F3]['ops'],sx=.72,sy=.72,dx=89.6,dy=84))
    for cp,base in [(0x22FA,0x22F2),(0x22FB,0x22F3),(0x22FC,0x22F4)]:
        put(cp,flip(reg[base]['ops']))
    # Full cancellation extends beyond the silhouette. Local cancellations
    # cross only the designated subordinate relation and remain visibly long.
    full = [(0x2204,0x2203),(0x2209,0x2208),(0x220C,0x220B),
            (0x2224,0x2223),(0x2226,0x2225),(0x2244,0x2243),
            (0x2247,0x2245),(0x2249,0x2248),(0x2262,0x2261),
            (0x226D,0x224D),(0x2270,0x2264),(0x2271,0x2265),
            (0x2274,0x2272),(0x2275,0x2273),(0x2278,0x2276),(0x2279,0x2277),
            (0x2284,0x2282),(0x2285,0x2283),(0x2288,0x2286),(0x2289,0x2287),
            (0x22AC,0x22A2),(0x22AD,0x22A8),(0x22AE,0x22A9),(0x22AF,0x22AB),
            (0x22E0,0x227C),(0x22E1,0x227D),(0x22E2,0x2291),(0x22E3,0x2292),
            (0x22EA,0x22B2),(0x22EB,0x22B3),(0x22EC,0x22B4),(0x22ED,0x22B5)]
    for cp,base in full:add_cancel(reg,cp,base,low=-150 if cp in (0x22EC,0x22ED) else -60)
    add_cancel(reg,0x2204,0x2203,low=-100,high=820)
    for cp,base in [(0x2224,0x2223),(0x2226,0x2225)]:
        put(cp,copy.deepcopy(reg[base]['ops'])+[line(175,235,465,465,.65)])
    integral=copy.deepcopy(reg[0x222B]['ops'])
    clockwise_head=s('M450 450L520 350L590 450',.65)
    anticlockwise_head=s('M50 450L120 350L190 450',.65)
    put(0x2231,integral+[s('M120 350C120 610 520 610 520 350',.65),clockwise_head])
    contour=s('M520 350C520 615 120 615 120 350C120 85 520 85 520 350Z',.65)
    put(0x2232,integral+[contour,clockwise_head])
    put(0x2233,integral+[contour,anticlockwise_head])
    local = [(0x2246,0x2245,0,315),(0x2268,0x2266,-65,340),(0x2269,0x2267,-65,340),
             (0x228A,0x2286,-100,230),(0x228B,0x2287,-100,230),
             (0x22E4,0x2291,-145,195),(0x22E5,0x2292,-145,195),
             (0x22E6,0x2272,-105,310),(0x22E7,0x2273,-105,310),
             (0x22E8,0x227E,-105,310),(0x22E9,0x227F,-105,310)]
    for cp,base,low,high in local:add_cancel(reg,cp,base,low,high)
    put(0x23FC,[s('M555 350C555 40 85 40 85 350C85 660 555 660 555 350Z',.65),
                 s('M320 200V500',.65)])


@lru_cache(None)
def authored_registry(stem,family,italic):
    logo = Path(__file__).resolve().parents[1]/'assets/netfyr-mark.svg'
    reg = expand_family.registry(stem,family,italic,logo)
    revise(reg,stem)
    return reg


def draw_recipe(font,stem,cp):
    limit = LIMITS.get(cp,90)
    local = min(stem,limit)
    family = 'mono' if font['post'].isFixedPitch else 'sans'
    reg = authored_registry(local,family,bool(font['post'].italicAngle))
    pen = Resolver(reg,local).resolve(cp)
    old = bounds(record(font,cp));new = bounds(pen)
    if not old or not new:return pen
    # Preserve the actual compiled baseline origin and advance. Extended bars
    # and multipart forms fit within each glyph's existing horizontal ink span.
    span=old[2]-old[0]
    # Directional integral heads need a visible arc without shrinking the stem.
    if cp in (0x2231,0x2232,0x2233):span=max(span,520)
    scale = min(1,span/(new[2]-new[0]))
    pen = transformed(pen,(scale,0,0,1,0,0));new = bounds(pen)
    return transformed(pen,(1,0,0,1,(old[0]+old[2]-new[0]-new[2])/2,0))


def make_repair(cp):
    def corrected(font,stem):
        if cp==0x205F:
            return record(font,cp),640 if font['post'].isFixedPitch else 222
        if cp==0x2127:
            omega = corrected_record(font,0x03A9,stem)
            b = bounds(omega)
            original = bounds(record(font,cp))
            inverted = transformed(omega,(-1,0,0,-1,b[0]+b[2],700))
            bb = bounds(inverted)
            return transformed(inverted,(1,0,0,1,(original[0]+original[2]-bb[0]-bb[2])/2,0))
        if cp not in SEMANTIC and stem<=LIMITS.get(cp,90):
            return record(font,cp)
        output = draw_recipe(font,stem,cp)
        if cp in (0x221F,0x22BE):
            # A named right angle must retain perpendicular limbs in Italics;
            # compensate the shared export shear only for this exact geometry.
            matrix = slant_matrix(font,cp,inverse=True)
            if matrix:output = transformed(output,matrix)
        return output
    corrected.__name__ = f'symbol_{cp:04x}'
    return repair(cp)(corrected)


for _cp in TARGETS:
    make_repair(_cp)
