"""U+2119: a double-struck P, with a stem slot independent of the bowl.

Unicode Letterlike Symbols specifies identity, not a mandated contour.
Dense strokes receive individual contrast; the slot is not an overlap artifact.
"""
from .common import compound

def apply(r,stem,family,italic):
    left=116-stem/2;right=527+stem/2
    first=stem*.54;second=stem*.40;gap=66+(154-stem)*.09
    a=left+first;b=a+gap;c=b+second
    bottom=342-.45*stem;h=stem*.68;lo=bottom+h;hi=700-h
    ir=right-stem*.84
    outer=(f'M{left} 0V700H325C494 700 {right} 635 {right} 507'
           f'C{right} 378 486 {bottom} 325 {bottom}H{c}V0H{b}V{bottom}H{a}V0Z')
    slot=f'M{a} {lo}H{b}V{hi}H{a}Z'
    bowl=(f'M{c} {lo}H325C428 {lo} {ir} 438 {ir} 507'
          f'C{ir} 575 429 {hi} 325 {hi}H{c}Z')
    r[0x2119]['ops']=compound(outer,[slot,bowl])
