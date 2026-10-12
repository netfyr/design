"""U+00C6: retain the diagonal A and E spine, with a true heavy counter.

References: OH no Type School A; Glyphs Intermediate Layers.
The Mono drawing uses its cell directly; no stem-restoration squeeze.
"""
from math import sqrt
from .common import compound

def draw(stem,mono):
    q=(stem-90)/64
    if mono:
        left,right,join=32.,608.,328.
        center=374+34*q;vertical=92+24*q
        diagonal=91+15*q;horizontal=72+16*q
        bar=252.;middle=582.
    else:
        left,right,join=-90.,720.,238.
        center=280+120*q;vertical=stem*.90
        diagonal=stem*.90;horizontal=stem*(.88-.17*q)
        bar=280.;middle=655.
    slope=(join-left)/700
    inner_left=left+diagonal*sqrt(1+slope*slope)
    sl=center-vertical/2;sr=center+vertical/2
    lo=bar-horizontal/2;hi=bar+horizontal/2
    tip=(sl-inner_left)/slope
    if not (tip>hi+60 and sl>inner_left+slope*hi):
        raise ValueError('Capital AE counter is not a valid, useful triangle')
    outer=(f'M{left} 0L{join} 700H{right}V{700-horizontal}H{sr}V{hi}'
           f'H{middle}V{lo}H{sr}V{horizontal}H{right}V0H{sl}V{lo}'
           f'H{inner_left+slope*lo}L{inner_left} 0Z')
    hole=f'M{inner_left+slope*hi} {hi}H{sl}V{tip}Z'
    return compound(outer,[hole])

def apply(r,stem,family,italic):r[0xC6]['ops']=draw(stem,family=='mono')
