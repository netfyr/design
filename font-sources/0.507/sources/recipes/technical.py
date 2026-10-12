"""Original cell graphics and directional symbols for netfyr mono.

All geometry is authored here; no font outlines are imported. Unicode names
describe the encoded arm/dot semantics, not a glyph shape to trace. Spacing is
640 units; the joining cell is x=0..640, y=-250..1000. Solid cell graphics are
filled, edge-clipped contours rather than live strokes with overhanging caps.
"""
from math import hypot, cos, sin, pi
import unicodedata as ud
from model import glyph, stroke, fill, rect, ellipse, component

X0, X1, Y0, Y1 = 0.0, 640.0, -250.0, 1000.0
CX, CY = 320.0, 375.0
BOX_ARMS = {}
BOX_ENDPOINTS = {}


def _num(x):
    return f'{x:.6f}'.rstrip('0').rstrip('.') if x else '0'


def _poly(points):
    """A solid clockwise contour in font coordinates."""
    p = list(points)
    if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1])) > 0:
        p.reverse()
    return fill('M'+' L'.join(f'{_num(x)} {_num(y)}' for x,y in p)+'Z')


def _clip(points):
    """Clip an authored polygon to the exact joining cell."""
    p=list(points)
    for axis,limit,low in [(0,X0,True),(0,X1,False),(1,Y0,True),(1,Y1,False)]:
        q=[]
        if not p:break
        for a,b in zip(p,p[1:]+p[:1]):
            ia=a[axis]>=limit if low else a[axis]<=limit
            ib=b[axis]>=limit if low else b[axis]<=limit
            if ia:q.append(a)
            if ia != ib:
                t=(limit-a[axis])/(b[axis]-a[axis])
                q.append(tuple(a[j]+t*(b[j]-a[j]) for j in range(2)))
        p=q
    return p


def _line(a,b,width):
    dx,dy=b[0]-a[0],b[1]-a[1]
    n=hypot(dx,dy)
    if not n:raise ValueError('Zero-length technical segment')
    nx,ny=-dy*width/(2*n),dx*width/(2*n)
    return _poly(_clip([(a[0]+nx,a[1]+ny),(b[0]+nx,b[1]+ny),
                         (b[0]-nx,b[1]-ny),(a[0]-nx,a[1]-ny)]))


def _lines(points,width,round_join=False):
    result=[_line(a,b,width) for a,b in zip(points,points[1:])]
    if round_join:
        result += [ellipse(x,y,width/2) for x,y in points[1:-1]]
    return result


def _r(x,y,w,h):
    xa,xb=max(X0,x),min(X1,x+w)
    ya,yb=max(Y0,y),min(Y1,y+h)
    return rect(xa,ya,xb-xa,yb-ya) if xb>xa and yb>ya else None


def _arm(direction,offset,width,reach=0):
    """Fill an arm from its edge to a declared centerward joining limit."""
    if direction=='L': return _r(X0,CY+offset-width/2,CX+reach-X0,width)
    if direction=='R': return _r(CX-reach,CY+offset-width/2,X1-CX+reach,width)
    if direction=='U': return _r(CX+offset-width/2,CY-reach,width,Y1-CY+reach)
    if direction=='D': return _r(CX+offset-width/2,Y0,width,CY+reach-Y0)
    raise ValueError(direction)


def _decode_arms(cp):
    """Read every arm in the standardized name, including mixed clauses.

    LIGHT UP AND HEAVY DOWN differs from UP HEAVY AND DOWN LIGHT; a weight
    before all direction words is global, while clause-local weights override.
    """
    name=ud.name(chr(cp)).removeprefix('BOX DRAWINGS ')
    special=any(x in name for x in ['DASH','ARC','DIAGONAL'])
    if special:return None
    direction={'LEFT':'L','RIGHT':'R','UP':'U','DOWN':'D',
               'HORIZONTAL':'LR','VERTICAL':'UD'}
    weight={'LIGHT':'light','HEAVY':'heavy','SINGLE':'light','DOUBLE':'double'}
    words=name.split()
    default=weight.get(words[0])
    result={}
    for clause in name.split(' AND '):
        tokens=clause.split()
        local=[weight[t] for t in tokens if t in weight]
        value=local[-1] if local else default
        if value is None:raise ValueError(f'Unweighted arm: {cp:04X} {clause}')
        for t in tokens:
            for d in direction.get(t,''):result[d]=value
    if not result:raise ValueError(f'No arms: {cp:04X}')
    return result


def _double_network(arms,thin,d):
    """Outline a rectilinear network with two parallel rails.

    Difference of outer and inner rectangular networks yields the correct
    nested corner, three-way and four-way turns. The open ends are at cell
    edges, so no transverse end cap can appear between neighboring cells.
    """
    outer=[];inner=[]
    for dest,half in [(outer,d+thin/2),(inner,d-thin/2)]:
        dest.append((CX-half,CY-half,CX+half,CY+half))
        for a in arms:
            if a=='L':dest.append((X0,CY-half,CX,CY+half))
            if a=='R':dest.append((CX,CY-half,X1,CY+half))
            if a=='U':dest.append((CX-half,CY,CX+half,Y1))
            if a=='D':dest.append((CX-half,Y0,CX+half,CY))
    xs=sorted({X0,X1,*[v for r in outer+inner for v in (max(X0,r[0]),min(X1,r[2]))]})
    ys=sorted({Y0,Y1,*[v for r in outer+inner for v in (max(Y0,r[1]),min(Y1,r[3]))]})
    inside=lambda x,y,rs:any(a<=x<=c and b<=y<=d for a,b,c,d in rs)
    ops=[]
    for x,xx in zip(xs,xs[1:]):
        for y,yy in zip(ys,ys[1:]):
            mx,my=(x+xx)/2,(y+yy)/2
            if inside(mx,my,outer) and not inside(mx,my,inner):ops.append(rect(x,y,xx-x,yy-y))
    return ops


def _mixed_double(arms,thin,d):
    """Single/double junctions retain their encoded one/two rail interfaces."""
    ops=[]
    if len(arms)==2:
        # A mixed elbow: the single rule caps and meets both parallel rails.
        for a,w in arms.items():
            offsets=[-d,d] if w=='double' else [0]
            reach=thin/2 if w=='double' else d+thin/2
            ops += [_arm(a,o,thin,reach) for o in offsets]
    elif len(arms)==3:
        trunk='LR' if 'L' in arms and 'R' in arms else 'UD'
        branch=next(a for a in arms if a not in trunk)
        for a in trunk:
            offsets=[-d,d] if arms[a]=='double' else [0]
            ops += [_arm(a,o,thin,thin/2) for o in offsets]
        if arms[branch]=='double':
            ops += [_arm(branch,o,thin,thin/2) for o in [-d,d]]
        else:
            # A single branch stops at the near rail of a double trunk; it
            # does not protrude into the clear channel between those rails.
            ops.append(_arm(branch,0,thin,-d+thin/2))
    elif len(arms)==4:
        for a,w in arms.items():
            ops += [_arm(a,o,thin,thin/2) for o in ([-d,d] if w=='double' else [0])]
    else:raise ValueError(f'Unsupported mixed double graph: {arms}')
    return [o for o in ops if o]


def _arc_elbow(thin):
    # D+R elbow: a true quarter-circle turn with flat cell-edge terminals.
    h=thin/2;r=200.0;x=520.0;y=175.0
    return fill(f'M{CX-h} {Y0}V{y}'
                f'A{r+h} {r+h} 0 0 0 {x} {CY+h}H{X1}V{CY-h}H{x}'
                f'A{r-h} {r-h} 0 0 1 {CX+h} {y}V{Y0}Z')


def _build_boxes(reg,weight):
    thin=min(weight*.75,90);heavy=min(weight*1.5,190);d=thin*1.2
    for cp in range(0x2500,0x2580):
        name=ud.name(chr(cp));arms=_decode_arms(cp)
        if arms is not None:
            if all(w=='double' for w in arms.values()):ops=_double_network(arms,thin,d)
            elif 'double' in arms.values():ops=_mixed_double(arms,thin,d)
            else:
                # Overlap only the perpendicular arms. A weight change along
                # one axis must not produce a nub on the other, absent axis;
                # half-line glyphs stop exactly at the center of the cell.
                widths={a:heavy if w=='heavy' else thin for a,w in arms.items()}
                ops=[]
                for a,width in widths.items():
                    perpendicular='UD' if a in 'LR' else 'LR'
                    reach=max((widths.get(p,0) for p in perpendicular))/2
                    ops.append(_arm(a,0,width,reach))
            BOX_ARMS[cp]=dict(arms)
            BOX_ENDPOINTS[cp]={a:[(o,thin if w=='double' else heavy if w=='heavy' else thin)
                                  for o in ([-d,d] if w=='double' else [0])]
                               for a,w in arms.items()}
        elif 'DASH' in name:
            count=3 if 'TRIPLE' in name else 4 if 'QUADRUPLE' in name else 2
            horizontal='HORIZONTAL' in name
            length=X1-X0 if horizontal else Y1-Y0
            width=heavy if 'HEAVY' in name else thin
            period=length/count;on=period*.64;gap=(period-on)/2
            ops=[]
            for i in range(count):
                start=(X0 if horizontal else Y0)+i*period+gap
                ops.append(rect(start,CY-width/2,on,width) if horizontal else rect(CX-width/2,start,width,on))
        elif 0x256D<=cp<=0x2570:
            if cp==0x256D:ops=[_arc_elbow(thin)]
            else:
                sx=-1 if cp in [0x256E,0x256F] else 1
                sy=-1 if cp in [0x256F,0x2570] else 1
                ops=[component(0x256D,sx=sx,sy=sy,dx=640 if sx<0 else 0,dy=750 if sy<0 else 0)]
        elif 0x2571<=cp<=0x2573:
            ops=[]
            if cp!=0x2572:ops.append(_line((X0,Y0),(X1,Y1),thin))
            if cp!=0x2571:ops.append(_line((X0,Y1),(X1,Y0),thin))
        else:raise ValueError(f'Unhandled box: {name}')
        glyph(reg,cp,ops,note=f'{name}; cell-clipped; light=.75w, heavy=1.5w, double rail offsets=±.9w')


def _build_blocks(reg,weight):
    h=Y1-Y0;w=X1-X0
    for cp in range(0x2580,0x25A0):
        if cp==0x2580:ops=[rect(0,CY,w,h/2)]
        elif 0x2581<=cp<=0x2588:ops=[rect(0,Y0,w,h*(cp-0x2580)/8)]
        elif 0x2589<=cp<=0x258F:ops=[rect(0,Y0,w*(0x2590-cp)/8,h)]
        elif cp==0x2590:ops=[rect(CX,Y0,w/2,h)]
        elif 0x2591<=cp<=0x2593:
            # One periodic 8x16 checker family; exact 25/50/75% source area.
            # Translate by half a tile and clip matching wrapped halves at
            # every cell edge. Light shade then reaches the same vertical
            # bounds as medium/dark shade, full block, and the vertical rule.
            level=cp-0x2590;ops=[]
            for row in range(17):
                for col in range(9):
                    idx=(col%2)+2*(row%2)
                    draw=(idx==0) if level==1 else (idx in [0,3]) if level==2 else (idx!=0)
                    if draw:
                        op=_r((col-.5)*w/8,Y0+(row-.5)*h/16,w/8,h/16)
                        if op:ops.append(op)
        elif cp==0x2594:ops=[rect(0,Y1-h/8,w,h/8)]
        elif cp==0x2595:ops=[rect(X1-w/8,Y0,w/8,h)]
        else:
            # Named quadrants are not inferred from a binary numerical order.
            quadrants={0x2596:'DL',0x2597:'DR',0x2598:'UL',0x2599:'UL DL DR',
                       0x259A:'UL DR',0x259B:'UL UR DL',0x259C:'UL UR DR',
                       0x259D:'UR',0x259E:'UR DL',0x259F:'UR DL DR'}[cp].split()
            ops=[rect(0 if a[1]=='L' else CX,Y0 if a[0]=='D' else CY,w/2,h/2) for a in quadrants]
        glyph(reg,cp,ops,note=ud.name(chr(cp))+'; exact cell partition, unaffected by text weight')


BRAILLE_POSITIONS={1:(200,820),2:(200,525),3:(200,230),4:(440,820),
                   5:(440,525),6:(440,230),7:(200,-65),8:(440,-65)}


def _build_braille(reg,weight):
    radius=max(45,min(82,54+(weight-72)*7/18))
    for pattern in range(256):
        ops=[ellipse(*BRAILLE_POSITIONS[dot],radius) for dot in range(1,9) if pattern&(1<<(dot-1))]
        glyph(reg,0x2800+pattern,ops,note=ud.name(chr(0x2800+pattern))+'; eight fixed dot centers; blank retains advance')


def _build_powerline(reg,weight):
    glyph(reg,0xE0B0,[_poly([(0,Y0),(640,CY),(0,Y1)])],note='Private-use Powerline right solid separator')
    glyph(reg,0xE0B1,[_poly([(0,Y0),(560,CY),(0,Y1),(80,Y1),(640,CY),(80,Y0)])],note='Private-use Powerline right outlined separator')
    glyph(reg,0xE0B2,[component(0xE0B0,sx=-1,dx=640)],note='Private-use Powerline left solid separator')
    glyph(reg,0xE0B3,[component(0xE0B1,sx=-1,dx=640)],note='Private-use Powerline left outlined separator')


def _curve(d,width,weight,join='round'):
    return stroke(d,width/weight,cap='butt',join=join,optical=False)


def _head(tip,u,thickness,length=112,spread=100,barb=None):
    """An open chevron head or one-sided harpoon barb."""
    ux,uy=u;nx,ny=-uy,ux
    back=(tip[0]-length*ux,tip[1]-length*uy)
    sides=[1,-1] if barb is None else [barb]
    result=[_line(tip,(back[0]+s*spread*nx,back[1]+s*spread*ny),thickness) for s in sides]
    # A small round join closes the tip without a miter spike.
    if barb is None:result.append(ellipse(*tip,thickness/2))
    return result


def _axis(direction,center=(CX,CY),short=False):
    x,y=center
    if direction=='R':return (x-220,y),(x+220,y)
    if direction=='L':return (x+220,y),(x-220,y)
    if direction=='U':return (x,y-300),(x,y+300)
    if direction=='D':return (x,y+300),(x,y-300)
    dx,dy={'NW':(-1,1),'NE':(1,1),'SE':(1,-1),'SW':(-1,-1)}[direction]
    return (x-dx*180,y-dy*180),(x+dx*180,y+dy*180)


def _arrow(a,b,t,rail=1,both=False,barb=None,open_head=False):
    dx,dy=b[0]-a[0],b[1]-a[1];length=hypot(dx,dy)
    u=(dx/length,dy/length);n=(-u[1],u[0])
    if open_head:
        # A hollow triangular head has a back edge; ordinary arrows do not.
        back=(b[0]-125*u[0],b[1]-125*u[1])
        pts=[b,(back[0]+95*n[0],back[1]+95*n[1]),(back[0]-95*n[0],back[1]-95*n[1]),b]
        start=(a[0]+125*u[0],a[1]+125*u[1]) if both else a
        ops=[_line(start,back,t)]+_lines(pts,t*.75,True)
        if both:
            backa=(a[0]+125*u[0],a[1]+125*u[1])
            ops+=_lines([a,(backa[0]+95*n[0],backa[1]+95*n[1]),(backa[0]-95*n[0],backa[1]-95*n[1]),a],t*.75,True)
        return ops
    offsets=[0] if rail==1 else [-52,52] if rail==2 else [-86,0,86]
    head_spread=100 if rail==1 else 145
    head_length=112 if rail==1 else 145
    ops=[]
    for off in offsets:
        inset=abs(off)*head_length/head_spread
        aa=(a[0]+off*n[0]+(inset*u[0] if both else 0),a[1]+off*n[1]+(inset*u[1] if both else 0))
        bb=(b[0]+off*n[0]-inset*u[0],b[1]+off*n[1]-inset*u[1])
        ops.append(_line(aa,bb,t))
    ops+=_head(b,u,t,head_length,head_spread,barb)
    if both:ops+=_head(a,(-u[0],-u[1]),t,head_length,head_spread)
    return ops


def _bar(point,u,t,half=120):
    n=(-u[1],u[0])
    return _line((point[0]-n[0]*half,point[1]-n[1]*half),
                 (point[0]+n[0]*half,point[1]+n[1]*half),t)


def _white_arrow(direction,t,weight,both=False,pedestal=False,base=100):
    """Outlined broad arrow. Rotation affects its authored points only."""
    if pedestal:
        points=[(165,70),(475,70),(475,200),(410,200),(410,485),(535,485),
                (320,730),(105,485),(230,485),(230,200),(165,200)]
    elif both:
        points=[(320,20),(105,265),(230,265),(230,485),(105,485),(320,730),
                (535,485),(410,485),(410,265),(535,265)]
    else:
        points=[(230,base),(410,base),(410,485),(535,485),(320,730),(105,485),(230,485)]
    def turn(p):
        x,y=p[0]-CX,p[1]-CY
        if direction=='U':return p
        if direction=='D':return (CX-x,CY-y)
        # Horizontal forms are compacted along the former vertical direction
        # to fit the same cell without changing the outline stroke weight.
        if direction=='R':return (CX+y*.62,CY-x)
        if direction=='L':return (CX-y*.62,CY+x)
        raise ValueError(direction)
    p=[turn(q) for q in points]
    d='M'+' L'.join(f'{x} {y}' for x,y in p)+'Z'
    return [_curve(d,t,weight,'miter')]


def _build_arrows(reg,weight):
    """Complete U+2190..21FF; every special construction is explicit.

    Arrowheads retain a clear distinction between ordinary chevrons, one-sided
    harpoons, multiple shafts, broad white arrows and hollow triangular heads.
    All strokes are optically unmodified and safely inset from the cell edges.
    """
    t=min(weight*.68,82)
    recipes={}
    def put(cp,ops):
        if cp in recipes:raise ValueError(f'Duplicate arrow {cp:04X}')
        recipes[cp]=ops
    def simple(cp,d,**kw):put(cp,_arrow(*_axis(d),t,**kw))
    def reflected(cp,base,sx=1,sy=1):put(cp,[component(base,sx=sx,sy=sy,dx=640 if sx<0 else 0,dy=750 if sy<0 else 0)])
    for cp,d in zip(range(0x2190,0x2194),'LURD'):simple(cp,d)
    simple(0x2194,'R',both=True);simple(0x2195,'U',both=True)
    for cp,d in zip(range(0x2196,0x219A),['NW','NE','SE','SW']):simple(cp,d)
    for cp,d in [(0x219A,'L'),(0x219B,'R'),(0x21AE,'R')]:
        put(cp,_arrow(*_axis(d),t,both=cp==0x21AE)+[_line((270,255),(370,495),t)])
    # Broad wave: two flowing lobes; squiggle below deliberately has more turns.
    wave='M100 375C170 475 240 275 320 375S470 475 540 375'
    put(0x219D,[_curve(wave,t,weight)]+_head((540,375),(1,0),t))
    reflected(0x219C,0x219D,sx=-1)
    put(0x21AD,[_curve(wave,t,weight)]+_head((540,375),(1,0),t)+_head((100,375),(-1,0),t))
    for cp,d in zip(range(0x219E,0x21A2),'LURD'):
        a,b=_axis(d);dx,dy=b[0]-a[0],b[1]-a[1];n=hypot(dx,dy);u=(dx/n,dy/n)
        put(cp,_arrow(a,b,t)+_head((b[0]-105*u[0],b[1]-105*u[1]),u,t,95,88))
    for cp,d in [(0x21A2,'L'),(0x21A3,'R')]:
        a,b=_axis(d);u=(-1,0) if d=='L' else (1,0)
        # Tail is a short reverse fork at the rear, not another front head.
        tip=(a[0]+75*u[0],a[1])
        put(cp,_arrow(a,b,t)+_lines([(a[0],a[1]+75),tip,(a[0],a[1]-75)],t,True))
    for cp,d in zip(range(0x21A4,0x21A8),'LURD'):
        a,b=_axis(d);n=hypot(b[0]-a[0],b[1]-a[1]);u=((b[0]-a[0])/n,(b[1]-a[1])/n)
        put(cp,_arrow(a,b,t)+[_bar(a,u,t)])
    put(0x21A8,_arrow(*_axis('U'),t,both=True)+[_line((190,-5),(450,-5),t)])
    # Return hooks curl at the non-head end, ending above the main shaft.
    put(0x21A9,[_curve('M380 545C555 545 555 375 420 375H100',t,weight)]+_head((100,375),(-1,0),t))
    reflected(0x21AA,0x21A9,sx=-1)
    put(0x21AB,[_curve('M100 375H450C585 375 585 605 455 605C355 605 355 450 455 375',t,weight)]+_head((100,375),(-1,0),t))
    reflected(0x21AC,0x21AB,sx=-1)
    zig=[(350,710),(240,490),(395,510),(250,275),(365,295),(275,50)]
    u=(zig[-1][0]-zig[-2][0],zig[-1][1]-zig[-2][1]);n=hypot(*u);u=(u[0]/n,u[1]/n)
    put(0x21AF,_lines(zig,t,True)+_head(zig[-1],u,t,105,92))
    # Bent-tip arrows: the long axis and the actual pointing tip are distinct.
    put(0x21B0,_lines([(430,100),(430,625),(135,625)],t,True)+_head((135,625),(-1,0),t))
    reflected(0x21B1,0x21B0,sx=-1);reflected(0x21B2,0x21B0,sy=-1);reflected(0x21B3,0x21B0,sx=-1,sy=-1)
    put(0x21B4,_lines([(110,620),(510,620),(510,170)],t,True)+_head((510,170),(0,-1),t))
    put(0x21B5,_lines([(500,670),(500,190),(125,190)],t,True)+_head((125,190),(-1,0),t))
    put(0x21B6,[_curve('M540 340C540 690 100 690 100 340',t,weight)]+_head((100,340),(0,-1),t))
    reflected(0x21B7,0x21B6,sx=-1)
    put(0x21B8,_arrow((500,160),(170,590),t)+[_line((100,680),(540,680),t)])
    # Paired arrows with bars at their destinations, not their tails.
    paired=[]
    for y,d in [(515,'L'),(235,'R')]:
        a,b=_axis(d,(320,y));u=(-1,0) if d=='L' else (1,0)
        end=(b[0]-u[0]*40,b[1]);paired+=_arrow(a,end,t*.8)+[_bar(b,u,t*.8,100)]
    put(0x21B9,paired)
    # Three-quarter open circle: CCW has a down-pointing head at the left.
    put(0x21BA,[_curve('M205 185C365 80 555 210 540 410C525 655 135 690 105 445',t,weight)]+_head((105,445),(-.10,-.995),t,105,90))
    reflected(0x21BB,0x21BA,sx=-1)
    harpoons={0x21BC:('L',-1),0x21BD:('L',1),0x21BE:('U',-1),0x21BF:('U',1),
              0x21C0:('R',1),0x21C1:('R',-1),0x21C2:('D',1),0x21C3:('D',-1)}
    for cp,(d,barb) in harpoons.items():simple(cp,d,barb=barb)
    # Horizontal and vertical paired arrows use independent parallel lanes.
    hpairs={0x21C4:('R','L'),0x21C6:('L','R'),0x21C7:('L','L'),0x21C9:('R','R')}
    for cp,ds in hpairs.items():
        put(cp,sum((_arrow(*_axis(d,(320,y)),t*.8) for d,y in zip(ds,[515,235])),[]))
    vpairs={0x21C5:('U','D'),0x21C8:('U','U'),0x21CA:('D','D'),0x21F5:('D','U')}
    for cp,ds in vpairs.items():
        put(cp,sum((_arrow(*_axis(d,(x,375)),t*.8) for d,x in zip(ds,[205,435])),[]))
    put(0x21CB,_arrow(*_axis('L',(320,495)),t,barb=-1)+_arrow(*_axis('R',(320,255)),t,barb=-1))
    put(0x21CC,_arrow(*_axis('R',(320,495)),t,barb=1)+_arrow(*_axis('L',(320,255)),t,barb=1))
    for cp,d,both in [(0x21CD,'L',False),(0x21CE,'R',True),(0x21CF,'R',False)]:
        put(cp,_arrow(*_axis(d),t*.8,rail=2,both=both)+[_line((260,235),(380,515),t*.85)])
    for cp,d in zip(range(0x21D0,0x21D4),'LURD'):simple(cp,d,rail=2)
    simple(0x21D4,'R',rail=2,both=True);simple(0x21D5,'U',rail=2,both=True)
    for cp,d in zip(range(0x21D6,0x21DA),['NW','NE','SE','SW']):simple(cp,d,rail=2)
    for cp,d in [(0x21DA,'L'),(0x21DB,'R')]:simple(cp,d,rail=3)
    squiggle='M100 375C140 490 180 260 220 375S300 490 340 375S420 260 460 375H540'
    put(0x21DD,[_curve(squiggle,t,weight)]+_head((540,375),(1,0),t))
    reflected(0x21DC,0x21DD,sx=-1)
    put(0x21DE,_arrow(*_axis('U'),t)+[_line((205,280),(435,380),t),_line((205,385),(435,485),t)])
    reflected(0x21DF,0x21DE,sy=-1)
    for cp,d in zip(range(0x21E0,0x21E4),'LURD'):
        a,b=_axis(d);vx,vy=b[0]-a[0],b[1]-a[1];n=hypot(vx,vy);u=(vx/n,vy/n)
        pieces=[]
        for lo,hi in [(0,.19),(.29,.48),(.58,1)]:pieces.append(_line((a[0]+vx*lo,a[1]+vy*lo),(a[0]+vx*hi,a[1]+vy*hi),t))
        put(cp,pieces+_head(b,u,t))
    for cp,d in [(0x21E4,'L'),(0x21E5,'R')]:
        a,b=_axis(d);u=(-1,0) if d=='L' else (1,0)
        tip=(b[0]-40*u[0],b[1])
        put(cp,_arrow(a,tip,t)+[_bar(b,u,t)])
    for cp,d in zip(range(0x21E6,0x21EA),'LURD'):put(cp,_white_arrow(d,t*.8,weight))
    put(0x21EA,_white_arrow('U',t*.8,weight,base=140)+[_line((180,45),(460,45),t*.8)])
    put(0x21EB,_white_arrow('U',t*.8,weight,pedestal=True))
    put(0x21EC,_white_arrow('U',t*.8,weight,pedestal=True)+[_line((150,135),(490,135),t*.8)])
    put(0x21ED,_white_arrow('U',t*.8,weight,pedestal=True)+[_line((320,75),(320,240),t*.8)])
    # White double arrows contain a second broad outlined head above the shaft.
    double_head=_lines([(150,625),(320,820),(490,625)],t*.8,True)
    put(0x21EE,_white_arrow('U',t*.8,weight)+double_head)
    put(0x21EF,_white_arrow('U',t*.8,weight,pedestal=True)+double_head)
    # Wall is a closed narrow rectangle, distinct from the one-rule from-bar.
    put(0x21F0,_white_arrow('R',t*.8,weight)+[_curve('M75 220H125V530H75Z',t*.8,weight,'miter')])
    put(0x21F1,_arrow((505,160),(170,590),t)+_lines([(105,500),(105,685),(290,685)],t,True))
    reflected(0x21F2,0x21F1,sx=-1,sy=-1)
    put(0x21F3,_white_arrow('U',t*.8,weight,both=True))
    circle=ellipse(175,375,60,stroked=True,width=.68);circle['optical']=False
    put(0x21F4,[circle]+_arrow((235,375),(550,375),t))
    put(0x21F6,sum((_arrow(*_axis('R',(320,y)),t*.67) for y in [620,375,130]),[]))
    for cp,d,both,count in [(0x21F7,'L',False,1),(0x21F8,'R',False,1),(0x21F9,'R',True,1),
                             (0x21FA,'L',False,2),(0x21FB,'R',False,2),(0x21FC,'R',True,2)]:
        bars=[320] if count==1 else [275,365]
        put(cp,_arrow(*_axis(d),t,both=both)+[_line((x,255),(x,495),t) for x in bars])
    simple(0x21FD,'L',open_head=True);simple(0x21FE,'R',open_head=True);simple(0x21FF,'R',open_head=True,both=True)
    expected=set(range(0x2190,0x2200))
    assert set(recipes)==expected,('Arrow coverage',sorted(expected-set(recipes)),sorted(set(recipes)-expected))
    for cp in sorted(recipes):
        glyph(reg,cp,recipes[cp],note=ud.name(chr(cp))+'; original explicit directional construction')


def validate_arm_semantics():
    """Focused, outline-independent checks of the decoded junction contract.

    The complete map is exported in BOX_ARMS/BOX_ENDPOINTS for downstream
    raster validation. These intentionally asymmetric examples catch swapped
    clause weights, accidentally global weights and lost double-line arms.
    """
    cases={0x250D:{'D':'light','R':'heavy'},0x251E:{'U':'heavy','R':'light','D':'light'},
           0x2521:{'D':'light','R':'heavy','U':'heavy'},
           0x253D:{'L':'heavy','R':'light','U':'light','D':'light'},
           0x2543:{'L':'heavy','U':'heavy','R':'light','D':'light'},
           0x2552:{'D':'light','R':'double'},0x256A:{'U':'light','D':'light','L':'double','R':'double'},
           0x257C:{'L':'light','R':'heavy'},0x257F:{'U':'heavy','D':'light'}}
    for cp,expected in cases.items():
        actual=_decode_arms(cp)
        assert actual==expected,(hex(cp),actual,expected)
    decoded={cp:_decode_arms(cp) for cp in range(0x2500,0x2580) if _decode_arms(cp) is not None}
    assert len(decoded)==109,len(decoded)
    for cp,arms in decoded.items():
        assert set(arms)<=set('LRUD') and 1<=len(arms)<=4
        assert set(arms.values())<={'light','heavy','double'}
    return {'box_codepoints':128,'decoded_solid_junctions':len(decoded),
            'dashed':12,'arcs':4,'diagonals':3,'explicit_asymmetric_cases':len(cases)}


def build(reg,weight):
    if not 40<=weight<=170:raise ValueError('Technical stem must be within reviewed expansion range 40..170')
    validate_arm_semantics()
    _build_boxes(reg,weight)
    _build_blocks(reg,weight)
    _build_braille(reg,weight)
    _build_arrows(reg,weight)
    _build_powerline(reg,weight)
