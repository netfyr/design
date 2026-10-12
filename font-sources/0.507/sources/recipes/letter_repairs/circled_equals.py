"""U+229C: lighter enclosing ring, two separated inset equals bars.

The ring is a container around another two-stroke sign. Giving it the same
mass as a plain circle crowded the bars at text sizes. Preserve the exterior
height, relieve the container inward, and retain a real clear passage around
both rules. Mono has an authored cell-width ellipse, not a squeezed ring.
"""
from model import ellipse,rect
from .common import compound

def apply(r,stem,family,italic):
    q=(stem-90)/64
    ry=245+.375*stem
    rx=min(ry,288.) if family=='mono' else ry
    ring_weight=stem*(.75-.24*q)
    outer=ellipse(320,300,rx,ry)['d']
    inner=ellipse(320,300,rx-ring_weight,ry-ring_weight)['d']
    thickness=.48*stem
    r[0x229C]['ops']=compound(outer,[inner])+[
        rect(215,225-thickness/2,210,thickness),
        rect(215,375-thickness/2,210,thickness)]
