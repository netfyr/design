"""Authored glyph recipe vocabulary. No external font outlines are read.

Coordinates use a 1000-unit em, y up, baseline 0. Spacing glyph advance is 640.
Recipes are expanded by the build engine; reusable components remain explicit.
"""
from math import pi

EM=1000
ADVANCE=640
ASCENT=1000
DESCENT=-250
CAP=700
XHEIGHT=520

def stroke(d, width=1.0, cap='butt', join='round', optical=True):
    return {'kind':'stroke','d':d,'width':width,'cap':cap,'join':join,'optical':optical}

def fill(d):
    return {'kind':'fill','d':d}

def component(cp, sx=1, sy=1, dx=0, dy=0, xy=0, yx=0):
    if isinstance(cp,str) and len(cp)==1: cp=ord(cp)
    return {'kind':'component','glyph':cp,'transform':[sx,yx,xy,sy,dx,dy]}

def rect(x,y,w,h):
    return fill(f'M{x} {y}v{h}h{w}v{-h}Z')

def ellipse(cx,cy,rx,ry=None,stroked=False,width=1.0):
    if ry is None:ry=rx
    k=.5522847498307936
    d=(f'M{cx+rx} {cy}C{cx+rx} {cy-k*ry} {cx+k*rx} {cy-ry} {cx} {cy-ry}'
       f'C{cx-k*rx} {cy-ry} {cx-rx} {cy-k*ry} {cx-rx} {cy}'
       f'C{cx-rx} {cy+k*ry} {cx-k*rx} {cy+ry} {cx} {cy+ry}'
       f'C{cx+k*rx} {cy+ry} {cx+rx} {cy+k*ry} {cx+rx} {cy}Z')
    return stroke(d,width) if stroked else fill(d)

def glyph(reg,cp,ops=None,width=ADVANCE,top=None,bottom=None,mark=None,note=''):
    if isinstance(cp,str) and len(cp)==1:cp=ord(cp)
    if cp in reg:raise ValueError(f'Duplicate glyph recipe: {cp!r}')
    reg[cp]={'ops':ops or [],'width':width,'top':top,'bottom':bottom,'mark':mark,'note':note}
    return reg[cp]

def transform_ops(ops,sx=1,sy=1,dx=0,dy=0):
    """Retain an explicit affine operation around a hand-authored recipe."""
    return [{'kind':'group','ops':ops,'transform':[sx,0,0,sy,dx,dy]}]

