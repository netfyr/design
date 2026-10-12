"""Original mono U/u skeletons that preserve the full Vietnamese horn.

The 432-unit outer body envelope is shared by both weights. Horizontal
positions belong to the authored centerlines; the 72/90-unit stroke is applied
afterward. No finished outline is condensed. Right-side attachments travel
with the right upright, preserving the horn aperture and ogonek connection.
"""
from model import stroke


def prepare_mono_u_horn(reg,stem):
    h=.45*stem
    inset=24+(stem-72)/2
    left=116+inset
    right=524-inset
    lower_left=184+2*inset/3
    lower_right=456-2*inset/3
    reg[ord('U')]['ops']=[stroke(
        f'M{left} 700V190C{left} 78 {lower_left} {h-7} 320 {h-7}'
        f'C{lower_right} {h-7} {right} 78 {right} 190V700')]
    reg[ord('u')]['ops']=[stroke(
        f'M{left} 520V170C{left} 68 {194+2*inset/3} {h-8} 310 {h-8}'
        f'C{433-inset/2} {h-8} {right} 110 {right} 211'),
        stroke(f'M{right} 520V0')]
    reg[0x31B]['ops']=[stroke('M0 -15C75 -25 95 40 80 100',.78)]
    reg[0x31B]['top']=(80,140)
    horn_x=518+16*max(-1.12,min(1.,(stem-72)/18))-inset
    reg[ord('U')]['right']=(horn_x,645)
    reg[ord('u')]['right']=(horn_x,465)
    reg[ord('U')]['ogonek']=(450-inset,25)
    reg[ord('u')]['ogonek']=(480-inset,0)
