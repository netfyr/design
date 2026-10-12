"""0.505: longer gamma transitions; retain the 0.504 loop and oval counter.

The previous two short turns pinch the legs into a scalloped neck. Here each
side is an explicitly controlled width profile, with the original straight
leg at one end and the original lower-bowl cubic at the other. The degree-six
profile eases curvature; it is emitted as cubic Hermite sections with a
bounded approximation error. This is not synthetic emboldening or a font
outline borrowed from a reference face. Compiled quadratic rounding is tested
separately; exact second-order continuity is not claimed after quantization.
"""
from math import isfinite
import numpy as np
from model import stroke
from outlines import Resolver
from .common import compound
from .loop_contours import oval

START_HEIGHT=280.0
PROFILE_RELIEF=20.0
CUBIC_ERROR_LIMIT=0.04


def _hermite(x0,x1,dy,m0,m1,c0,c1):
    """Quintic x(t): endpoint position, dx/dy and d2x/dy2 constraints."""
    c=np.zeros(7,dtype=float)
    c[:3]=(x0,m0*dy,c0*dy*dy/2)
    # Closed-form quintic Hermite remainder; no external optimizer is used.
    p=x1-sum(c[:3]);v=m1*dy-c[1]-2*c[2];a=c1*dy*dy-2*c[2]
    c[3:6]=(10*p-4*v+a/2,-15*p+7*v-a,6*p-3*v+a/2)
    return np.polynomial.Polynomial(c)


def _cubic(p,a,b,y0,dy):
    d=p.deriv();h=b-a
    v0=float(p(a));v1=float(p(b));s0=float(d(a));s1=float(d(b))
    # Error is a polynomial; test its interior stationary points and ends.
    t=np.polynomial.Polynomial([a,h]);exact=p(t)
    cubic=np.polynomial.Polynomial([v0,s0*h,3*(v1-v0)-h*(2*s0+s1),2*(v0-v1)+h*(s0+s1)])
    error=exact-cubic
    points=[0.,1.]+[float(z.real) for z in error.deriv().roots() if abs(z.imag)<1e-7 and 0<z.real<1]
    maximum=max(abs(float(error(x))) for x in points)
    controls=((v0+s0*h/3,y0+dy*(a+h/3)),
              (v1-s1*h/3,y0+dy*(b-h/3)),(v1,y0+dy*b))
    return controls,maximum


def _profile(x0,x1,y0,y1,slope,curvature,sign):
    dy=y1-y0
    p=_hermite(x0,x1,dy,slope,0,0,curvature)
    # The relief vanishes with its first two derivatives at both ends.
    p-=sign*PROFILE_RELIEF*np.polynomial.Polynomial([0,0,0,64,-192,192,-64])
    stationary=sorted(float(z.real) for z in p.deriv().roots()
                      if abs(z.imag)<1e-7 and 1e-6<z.real<1-1e-6)
    if len(stationary)!=1:
        raise ValueError('Gamma transition must have exactly one interior waist')
    # Subdivide around the real waist, not a nearby regular-grid knot.
    # A short extra section next to an extremum became a flat spot when
    # converted to integer quadratic coordinates.
    nodes=[0.,stationary[0],1.]
    segments=[];errors=[]
    def fit(a,b,depth=0):
        c,e=_cubic(p,a,b,y0,dy)
        if e>CUBIC_ERROR_LIMIT:
            if depth>=12:raise ValueError('Gamma cubic approximation failed')
            mid=(a+b)/2;fit(a,mid,depth+1);fit(mid,b,depth+1)
        else:segments.append(c);errors.append(e)
    for a,b in zip(nodes[:-1],nodes[1:]):fit(a,b)
    return segments,{'polynomial':p.coef.tolist(),'y_start':y0,'y_end':y1,
        'waist':(float(p(stationary[0])),y0+dy*stationary[0]),
        'cubic_sections':len(segments),'max_source_approximation_error':max(errors),
        'start_dx_dy':float(p.deriv()(0)/dy),'end_dx_dy':float(p.deriv()(1)/dy),
        'start_d2x_dy2':float(p.deriv(2)(0)/(dy*dy)),
        'end_d2x_dy2':float(p.deriv(2)(1)/(dy*dy))}


def construction(stem,top,cross,bottom,cx,left,right):
    arms=Resolver({},stem)._ops([stroke(f'M{left} {top}L{cx} {cross}L{right} {top}')])
    pts=sorted({p for cmd,ps in arms.value if cmd in ('moveTo','lineTo')
                for p in ps if p[1]>top-stem})
    lp=[p for p in pts if p[0]<cx];rp=[p for p in pts if p[0]>cx]
    if len(lp)!=2 or len(rp)!=2:raise ValueError('Unexpected gamma cap geometry')
    Lout,Lin=lp;Rin,Rout=rp
    q=max(0.,min(1.,(stem-90)/64))
    radius=139+15*q;cy=bottom+122+7*q
    v=71+13*q;innerx=radius-v;innery=cy-bottom-.82*v
    valley=cy+innery+1.05*v
    # Match the endpoint curvature of the preserved lower-bowl cubic.
    side_curvature=(2/3)*radius*(1-.56)/(.56*(cy-bottom))**2
    profiles={};pathparts={}
    for label,sign,cap,m in [('right',1,Rout,(right-cx)/(top-cross)),
                             ('left',-1,Lout,(cx-left)/(top-cross))]:
        y0=cy+START_HEIGHT;x0=cap[0]+sign*m*(y0-cap[1])
        seg,info=_profile(x0,cx+sign*radius,y0,cy,sign*m,-sign*side_curvature,sign)
        profiles[label]=info
        if sign==1:
            pathparts[label]=f'L{x0} {y0}'+''.join('C'+' '.join(f'{x:.10g} {y:.10g}' for x,y in s) for s in seg)
        else:
            previous=[(x0,y0)]+[s[-1] for s in seg]
            pathparts[label]=''.join('C'+' '.join(f'{x:.10g} {y:.10g}' for x,y in
                (seg[i][1],seg[i][0],previous[i])) for i in reversed(range(len(seg))))+f'L{cap[0]} {cap[1]}'
    outer=(f'M{Lout[0]} {Lout[1]}L{Lin[0]} {Lin[1]}L{cx} {valley}'
        f'L{Rin[0]} {Rin[1]}L{Rout[0]} {Rout[1]}'+pathparts['right']+
        f'C{cx+radius} {cy-(cy-bottom)*.56} {cx+radius*.56} {bottom} {cx} {bottom}'
        f'C{cx-radius*.56} {bottom} {cx-radius} {cy-(cy-bottom)*.56} {cx-radius} {cy}'+pathparts['left']+'Z')
    hole=oval(cx,cy,innerx,innery)
    return outer,hole,{'profiles':profiles,'oval':{'cx':cx,'cy':cy,'rx':innerx,'ry':innery},
                      'inner_valley':(cx,valley),'outer_radius':radius,'bottom':bottom,
                      'cap_endpoints':[Lout,Lin,Rin,Rout]}


def gamma(stem,top,cross,bottom,cx,left,right):
    outer,hole,_=construction(stem,top,cross,bottom,cx,left,right)
    return compound(outer,[hole])
