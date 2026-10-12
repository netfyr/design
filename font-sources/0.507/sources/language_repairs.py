"""Individually reviewed IPA, Greek and combining-mark corrections."""
from compiled_repairs import repair, record, corrected_record, combine, stem_edges
from outlines import bounds, transformed, expand_stroke, split_contours, path_recording
from fontTools.pens.recordingPen import RecordingPen


def stroke(d, stem, factor=.78, limit=72):
    return expand_stroke(d, min(stem * factor, limit))


def ellipse(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    k = .5522847498307936
    return path_recording(
        f'M{cx+rx} {cy}C{cx+rx} {cy+k*ry} {cx+k*rx} {cy+ry} {cx} {cy+ry}'
        f'C{cx-k*rx} {cy+ry} {cx-rx} {cy+k*ry} {cx-rx} {cy}'
        f'C{cx-rx} {cy-k*ry} {cx-k*rx} {cy-ry} {cx} {cy-ry}'
        f'C{cx+k*rx} {cy-ry} {cx+rx} {cy-k*ry} {cx+rx} {cy}Z')


def ring(cx, cy, radius, width):
    k = .5522847498307936
    return expand_stroke(
        f'M{cx+radius} {cy}C{cx+radius} {cy+k*radius} {cx+k*radius} {cy+radius} {cx} {cy+radius}'
        f'C{cx-k*radius} {cy+radius} {cx-radius} {cy+k*radius} {cx-radius} {cy}'
        f'C{cx-radius} {cy-k*radius} {cx-k*radius} {cy-radius} {cx} {cy-radius}'
        f'C{cx+k*radius} {cy-radius} {cx+radius} {cy-k*radius} {cx+radius} {cy}Z', width)


MARK_PATHS = {
    0x0309: 'M-54 110C-54 170 76 172 76 114C76 73 8 66 8 24',
    0x030B: 'M-140 30L-60 130M35 30L115 130',
    0x030F: 'M-130 130L-50 30M45 130L125 30',
    'mark.030F.narrow': 'M-90 132L-48 30M35 132L77 30',
    'mark.0311.narrow': 'M-68 32C-68 73.973641 -37.555363 108 0 108C37.555363 108 68 73.973641 68 32',
    0x0318: 'M70 -30V-180M70 -105H-85',
    0x0319: 'M-70 -30V-180M-70 -105H85',
    0x031C: 'M50 -25C-95 -25 -95 -155 50 -155',
    0x031F: 'M-100 -100H100M0 -25V-180',
    0x0327: 'M10 35L-25 -25C80 -15 90 -115 15 -120H-45',
    0x032B: 'M-140 -45Q-70 -185 0 -45Q70 -185 140 -45',
    0x0333: 'M-320 -45H320M-320 -150H320',
    0x0339: 'M-50 -25C95 -25 95 -155 -50 -155',
    0x033B: 'M-85 -30H85V-150H-85Z',
    0x033C: 'M-140 -110Q-70 10 0 -110Q70 10 140 -110',
    0x033E: 'M-35 20C55 40 65 75 0 95S-50 155 30 180',
    0x033F: 'M-300 40H300M-300 145H300',
    0x0347: 'M-120 -40H120M-120 -145H120',
    0x0348: 'M-80 -25V-155M80 -25V-155',
    0x034E: 'M0 -205V-25M-80 -100L0 -25L80 -100',
    0x0351: 'M50 25C-95 25 -95 155 50 155',
    0x0357: 'M-50 25C95 25 95 155 -50 155',
    0x0359: 'M0 -20V-180M-95 -45L95 -155M-95 -155L95 -45',
    0x035B: 'M-45 160L45 120H-45L45 30',
}
MARK_LIMITS = {
    0x0309: 48, 'mark.0311.narrow': 58,
    0x031C: 60, 0x0327: 50, 0x032B: 55,
    0x0339: 60, 0x033B: 55, 0x033C: 55,
    0x033E: 46, 0x0351: 60, 0x0357: 60, 0x0359: 48,
    0x035B: 45,
}
for key, drawing in MARK_PATHS.items():
    def mark_path(font, stem, key=key, drawing=drawing):
        return stroke(drawing, stem, limit=MARK_LIMITS.get(key, 72))
    repair(key)(mark_path)


@repair('mark.0308.narrow')
def narrow_diaeresis(font, stem):
    radius = min(stem * .44, 48)
    return combine(ellipse(-65, 50, radius), ellipse(65, 50, radius))


@repair(0x0323)
def separated_dot_below(font, stem):
    return transformed(record(font, 0x0323), (1, 0, 0, 1, 0, -max(0, (stem-90)*.5)))


@repair(0x0325)
def open_ring_below(font, stem):
    return ring(0, -95, 63, min(stem*.62, 52))


@repair(0x0349)
def left_angle_below(font, stem):
    return transformed(record(font, 0x0349), (-1, 0, 0, 1, 5, 0))


@repair(0x034A)
def not_tilde(font, stem):
    return combine(stroke('M-130 45C-90 110 -35 110 10 70S90 30 130 100', stem, limit=52),
                   stroke('M-55 10L55 165', stem, limit=44))


@repair(0x034B)
def homothetic(font, stem):
    return combine(stroke('M-95 80C-60 110 -28 110 0 90S62 68 95 100', stem, limit=44),
                   ellipse(0, 15, min(stem*.20, 20)),
                   ellipse(0, 165, min(stem*.20, 20)))


@repair(0x034C)
def almost_equal(font, stem):
    return combine(stroke('M-130 25C-87 68 -42 70 5 43S86 12 130 57', stem, limit=48),
                   stroke('M-130 130C-87 173 -42 175 5 148S86 117 130 162', stem, limit=48))


@repair(0x0352)
def open_fermata(font, stem):
    return combine(stroke('M-120 35Q0 220 120 35', stem, limit=62),
                   ellipse(0, 40, min(stem*.26, 34)))


@repair(0x0356)
def separate_arrowheads(font, stem):
    return stroke('M-160 -30L-90 -95L-160 -160M15 -135L80 -65L145 -135', stem, limit=52)


@repair(0x035A)
def open_double_ring(font, stem):
    width = min(stem*.60, 43)
    return combine(ring(-65, -100, 55, width), ring(65, -100, 55, width))


@repair(0x0365)
def miniature_dotted_i(font, stem):
    base = record(font, 0x0365)
    dot = max(split_contours(record(font, ord('i'))), key=lambda p: bounds(p)[3])
    x0,y0,x1,y1=bounds(base)
    d0,d1,d2,d3=bounds(dot)
    scaled = transformed(dot, (.34, 0, 0, .34,
                               (x0+x1-(d0+d2)*.34)/2,y1+25-d1*.34))
    return combine(base, scaled)


def vertical_edges(pen, height=200, side='right'):
    segments = []
    current = start = None
    for command, args in pen.value:
        if command == 'moveTo':
            current = start = args[0]
        elif command == 'lineTo':
            end = args[0]
            if current and abs(end[0]-current[0]) < 1.2 and min(current[1],end[1]) <= height <= max(current[1],end[1]):
                segments.append((end[0]+current[0])/2)
            current = end
        elif command in ('curveTo', 'qCurveTo'):
            current = args[-1] if args[-1] is not None else start
        elif command in ('closePath', 'endPath'):
            if current and start and abs(start[0]-current[0]) < 1.2 and min(current[1],start[1]) <= height <= max(current[1],start[1]):
                segments.append((start[0]+current[0])/2)
            current = start
    xs = sorted(set(round(x, 3) for x in segments))
    if len(xs) < 2:
        raise ValueError('No straight stem at requested height')
    return xs[-2:] if side == 'right' else xs[:2]


def extended_stem(font, base, side='right', direction=1, hook=True):
    pen = record(font, base)
    left, right = vertical_edges(pen, 350 if base == 0x0279 else 200, side)
    x = (left+right)/2
    width = right-left
    endpoint = min(x+115, 616-width*.5) if direction > 0 else max(x-115, 24+width*.5)
    path = (f'M{x} 150V-70Q{x} -210 {endpoint} -170' if hook
            else f'M{x} 170V-210')
    return combine(pen, expand_stroke(path, width))


for key, base, side, direction, hook in [
    (0x0256, ord('d'), 'right', 1, True),
    (0x0270, 0x026F, 'right', 1, False),
    (0x0271, ord('m'), 'right', -1, True),
    (0x0272, ord('n'), 'left', -1, True),
    (0x0273, ord('n'), 'right', 1, True),
    (0x027A, 0x0279, 'right', 1, False),
    (0x027B, 0x0279, 'right', 1, True),
    (0x027C, ord('r'), 'left', 1, False),
    (0x027D, ord('r'), 'left', 1, True),
]:
    def joined_extension(font, stem, base=base, side=side, direction=direction, hook=hook):
        return extended_stem(font, base, side, direction, hook)
    repair(key)(joined_extension)


@repair(0x0255)
def c_with_curl(font, stem):
    base = record(font, ord('c'))
    x0, _, x1, _ = bounds(base)
    left, right = x0+stem*.5, x1-stem*.4
    mid = left+(right-left)*.52
    return combine(clip_rectangle(base,-2000,210,2000,2000),
                   expand_stroke(f'M{left} 240C{left} 75 {mid} -10 {mid} 35',stem),
                   inward_curl(mid,right,35,min(stem*.82,96)))


def inward_curl(mid,right,bottom,width):
    return expand_stroke(
        f'M{mid} {bottom}C{mid-15} {bottom-50} {right+20} {bottom-45} {right+20} {bottom+60}'
        f'C{right+20} {bottom+165} {mid-50} {bottom+175} {mid-20} {bottom+45}'
        f'L{mid-70} {bottom-110}',width)


@repair(0x025A)
def hooked_schwa(font, stem):
    base = record(font, 0x0259)
    right = bounds(base)[2]-stem*.45
    return fit_rhotic(font, 0x025A, combine(base, expand_stroke(
        f'M{right-25} 270L{right+90} 320V245Q{right+90} 160 {right+175} 185', min(stem*.8, 94))))


@repair(0x025D)
def hooked_reversed_open_e(font, stem):
    base = record(font, 0x025C)
    right = bounds(base)[2]-stem*.45
    return fit_rhotic(font, 0x025D, combine(base, expand_stroke(
        f'M{right-25} 270L{right+90} 320V245Q{right+90} 160 {right+175} 185', min(stem*.8, 94))))


def fit_rhotic(font, key, outline):
    left, _, right, _ = bounds(outline)
    advance = font['hmtx'][font.getBestCmap()[key]][0]
    scale = min(1, (advance-40-left)/(right-left))
    return transformed(outline, (scale, 0, 0, 1, left*(1-scale), 0))


@repair(0x0264)
def ramshorn(font, stem):
    return expand_stroke('M115 490C165 495 225 355 320 230'
                         'C420 100 435 35 320 35C205 35 220 100 320 230'
                         'C415 355 475 495 525 490', min(stem, 90))


@repair(0x0277)
def closed_omega(font, stem):
    original=transformed(record(font, 0x0277), (1, 0, 0, -1, 0, 520))
    if stem <= 110:
        return original
    return expand_stroke('M320 330V140C320 -45 105 -45 105 250'
                         'C105 585 535 585 535 250C535 -45 320 -45 320 140',110)


@repair(0x0281)
def inverted_small_r(font, stem):
    return transformed(record(font, 0x0280), (1, 0, 0, -1, 0, 520))


@repair(0x0291)
def z_with_curl(font, stem):
    base = record(font, ord('z'))
    x0,_,x1,_=bounds(base)
    left,right=x0+stem*.5,x1-stem*.4
    mid=left+(right-left)*.46
    return combine(expand_stroke(f'M{left} 485H{right}L{mid-20} 80',stem),
                   inward_curl(mid,right,35,min(stem*.82,96)))


@repair(0x0293)
def ezh_with_curl(font, stem):
    base = record(font, 0x0292)
    x0,_,x1,_=bounds(base)
    mid=x0+(x1-x0)*.44
    right=x1-stem*.45
    return combine(clip_rectangle(base,-2000,-45,2000,2000),
                   expand_stroke(f'M{right} 45Q{right} -165 {mid} -165',min(stem,105)),
                   transformed(inward_curl(mid,right,-165,min(stem*.82,72)),
                               (-1,0,0,1,mid+right,0)))


@repair(0x0296)
def inverted_glottal(font, stem):
    return transformed(record(font, 0x0294), (1, 0, 0, -1, 0, 700))


@repair(0x0299)
def solid_small_b(font, stem):
    original = record(font, 0x0299)
    if font['OS/2'].usWeightClass != 800:
        return original
    original_box = bounds(original)
    base = record(font, ord('B'))
    x0,y0,x1,y1 = bounds(base)
    sx = (original_box[2]-original_box[0])/(x1-x0)
    sy = (original_box[3]-original_box[1])/(y1-y0)
    return transformed(base, (sx, 0, 0, sy, original_box[0]-x0*sx, original_box[1]-y0*sy))


@repair(0x02AD)
def bidental_percussive(font, stem):
    return expand_stroke('M135 315V485H505V315M135 35V205H505V35', stem)


@repair(0x02DE)
def rhotic_hook(font, stem):
    return expand_stroke('M195 295L330 340V255Q330 155 445 190', min(stem*.78, 92))


@repair(0x02EB)
def yang_departing(font, stem):
    return expand_stroke('M180 650V100M180 375H465', stem*.78)


@repair(0x02FB)
def beginning_low_tone(font, stem):
    return expand_stroke('M190 300V50H450', stem*.78)


@repair(0x02FC)
def ending_low_tone(font, stem):
    return expand_stroke('M190 50H450V300', stem*.78)


@repair(0x02DD)
def spacing_double_acute(font, stem):
    original = record(font, 0x02DD)
    mark = corrected_record(font, 0x030B, stem)
    a,b,c,d = bounds(original)
    e,f,g,h = bounds(mark)
    return transformed(mark, (1, 0, 0, 1, (a+c-e-g)/2, (b+d-f-h)/2))


for key, base in [(0x02B5,0x027B), (0x02B6,0x0281)]:
    def raised_corrected(font, stem, key=key, base=base):
        target = bounds(record(font, key))
        pen = transformed(corrected_record(font, base, stem), (.55, 0, 0, .55, 144, 360))
        box = bounds(pen)
        return transformed(pen, (1, 0, 0, 1, (target[0]+target[2]-box[0]-box[2])/2, 0))
    repair(key)(raised_corrected)


@repair(0x03A9)
def open_capital_omega(font, stem):
    original = record(font, 0x03A9)
    if stem <= 110:
        return original
    gh = stem*.45
    relief = (stem-110)*.55
    return expand_stroke(f'M85 {gh}H{245-relief}V115C25 275 110 {710-gh} 320 {710-gh}'
                         f'C530 {710-gh} 615 275 {395+relief} 115V{gh}H555', stem)

from compiled_repairs import clip_rectangle


def retroflex_foot(font, base):
    actual = record(font, base)
    left,right = vertical_edges(actual,200,'left')
    center,width = (left+right)/2,right-left
    upper = clip_rectangle(actual,-2000,170,2000,2000)
    return combine(upper,expand_stroke(
        f'M{center} 200V-60C{center} -190 {center+150} -190 {center+135} -100', width))


@repair(0x026D)
def retroflex_l(font,stem):
    return retroflex_foot(font,ord('l'))


@repair(0x0288)
def retroflex_t(font,stem):
    return retroflex_foot(font,ord('t'))


@repair(0x0286)
def lower_curl_esh(font,stem):
    actual=record(font,0x0283)
    left,right=vertical_edges(actual,200)
    center,width=(left+right)/2,right-left
    upper=clip_rectangle(actual,-2000,20,2000,2000)
    return combine(upper,expand_stroke(f'M{center} 80V-65',width),expand_stroke(
        f'M{center} -45V-80C{center} -235 {center-175} -230 {center-175} -125'
        f'C{center-175} -35 {center-75} -55 {center+75} -55',min(width,104)))


@repair(0x0290)
def retroflex_z(font,stem):
    actual=record(font,ord('z'))
    x=bounds(actual)[2]-stem*.5
    return combine(actual,expand_stroke(
        f'M{x} 80V-70C{x} -200 {x+125} -190 {x+115} -105',stem))


@repair(0x02AE)
def turned_h_fishhook(font,stem):
    actual=record(font,0x0265)
    left,right=vertical_edges(actual,350,'left')
    center,width=(left+right)/2,right-left
    return fit_fishhook(font, 0x02AE, combine(actual,expand_stroke(
        f'M{center} 410V520C{center} 640 {center-135} 635 {center-135} 565',width)))


@repair(0x02AF)
def turned_h_fishhook_tail(font,stem):
    actual=corrected_record(font,0x02AE,stem)
    left,right=vertical_edges(actual,200,'right')
    center,width=(left+right)/2,right-left
    upper=clip_rectangle(actual,-2000,-55,2000,2000)
    return fit_fishhook(font, 0x02AF, combine(upper,expand_stroke(
        f'M{center} 140V-75Q{center} -230 {center+140} -170',width)))


def fit_fishhook(font, key, outline):
    left, _, right, _ = bounds(outline)
    advance = font['hmtx'][font.getBestCmap()[key]][0]
    if left >= 24 and right <= advance-24:
        return outline
    scale = (advance-48)/(right-left)
    return transformed(outline, (scale, 0, 0, 1, 24-left*scale, 0))


DIGRAPHS={0x026E:('l','ezh'),0x02A3:('d','z'),0x02A4:('d','ezh'),
          0x02A5:('d','zcurl'),0x02A6:('t','s'),0x02A7:('t','esh'),
          0x02A8:('t','ccurl'),0x02A9:('f','eng'),0x02AA:('l','s'),0x02AB:('l','z')}
for key,(left_kind,right_kind) in DIGRAPHS.items():
    def joined_digraph(font,stem,key=key,left_kind=left_kind,right_kind=right_kind):
        old=bounds(record(font,key))
        span=old[2]-old[0]
        mono='mono' in font['name'].getDebugName(1).lower()
        w=min(stem*(.69 if mono else .85),108 if mono else 140)
        xmin=old[0]+w/2
        xmax=old[2]-w/2
        mid=xmin+(xmax-xmin)*(.48 if left_kind=='d' else .25)
        parts=[]
        if left_kind=='d':
            parts.append(expand_stroke(f'M{mid} 720V35',w))
            cx=(xmin+mid)/2;rx=(mid-xmin)/2
            circle=ellipse(cx,260,rx,225)
            from fontTools.pens.svgPathPen import SVGPathPen
            pen=SVGPathPen(None);circle.replay(pen)
            parts.append(expand_stroke(pen.getCommands(),w))
        else:
            top=720 if left_kind in ('l','f') else 656
            if left_kind=='f':
                parts.append(expand_stroke(f'M{mid} 35V560Q{mid} 690 {mid+100} 690',w))
            else:
                parts.append(expand_stroke(f'M{mid} {top}V35',w))
            if left_kind in ('t','f'):
                parts.append(expand_stroke(f'M{xmin} 485H{mid+(xmax-mid)*.52}',w))
        if right_kind in ('z','zcurl'):
            if right_kind=='z':
                parts.append(expand_stroke(f'M{mid} 485H{xmax}L{mid} 35H{xmax}',w))
            else:
                center=mid+(xmax-mid)*.40
                parts.append(expand_stroke(f'M{mid} 485H{xmax}L{center-20} 80',w))
                parts.append(inward_curl(center,xmax,35,min(w,80)))
        elif right_kind=='ezh':
            q=mid+(xmax-mid)*.40
            parts.append(expand_stroke(f'M{mid} 485H{xmax}L{q} 260C{xmax+45} 295 {xmax+80} -170 {q} -170H{mid}',w))
        elif right_kind=='s':
            q=mid+(xmax-mid)*.55
            parts.append(expand_stroke(f'M{xmax} 445C{q} 560 {mid-35} 400 {mid+35} 315C{mid+90} 245 {xmax+25} 260 {xmax} 130C{xmax-10} -5 {q} -10 {mid} 35',w))
        elif right_kind=='esh':
            center=mid+(xmax-mid)*.48
            parts.append(expand_stroke(f'M{mid} -155C{center} -225 {center} -60 {center} 70V460Q{center} 745 {xmax} 665',w))
            parts.append(expand_stroke(f'M{mid} 130V90Q{mid} 30 {center} 35',w))
        elif right_kind=='eng':
            center=mid+(xmax-mid)*.45
            parts.append(expand_stroke(f'M{mid} 35V340C{mid} 570 {xmax} 570 {xmax} 340V-65Q{xmax} -205 {center} -165',w))
        elif right_kind=='ccurl':
            center=mid+(xmax-mid)*.52
            parts.append(expand_stroke(f'M{xmax} 435C{center} 585 {mid-40} 420 {mid} 190C{mid+20} 20 {center} -10 {center} 35',w))
            parts.append(inward_curl(center,xmax,35,min(w,90)))
        return combine(*parts)
    repair(key)(joined_digraph)


def ring_counter(outline):
    contours = split_contours(outline)
    if len(contours) != 2:
        raise ValueError('Ring must contain an outer contour and one counter')
    inner = min(contours, key=lambda p: (bounds(p)[2]-bounds(p)[0]) * (bounds(p)[3]-bounds(p)[1]))
    return contours, inner


def resize_ring_counter(outline, width, height):
    contours, inner = ring_counter(outline)
    x0, y0, x1, y1 = bounds(inner)
    cx, cy = (x0+x1)/2, (y0+y1)/2
    sx, sy = max(1, width/(x1-x0)), max(1, height/(y1-y0))
    enlarged = transformed(inner, (sx, 0, 0, sy, cx*(1-sx), cy*(1-sy)))
    return combine(*(enlarged if contour is inner else contour for contour in contours))


@repair(0x030A, weights={900}, preserve_contours=True)
def open_black_ring_above(font, stem):
    original = record(font, 0x030A)
    if font['OS/2'].usWeightClass < 900:
        return original
    return resize_ring_counter(original, 84, 90)


@repair(0x02DA, weights={900}, preserve_contours=True)
def open_black_modifier_ring(font, stem):
    original = record(font, 0x02DA)
    if font['OS/2'].usWeightClass < 900:
        return original
    _, parent_inner = ring_counter(corrected_record(font, 0x030A, stem))
    x0, y0, x1, y1 = bounds(parent_inner)
    return resize_ring_counter(original, x1-x0, y1-y0)
