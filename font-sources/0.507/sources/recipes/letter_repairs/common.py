"""Simple path tools shared by the individually authored letter recipes."""
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.svgPathPen import SVGPathPen
from outlines import path_recording,split_contours,Resolver,bounds
from model import fill
from curve_boolean import one

def area(c):
    p=AreaPen(None);c.replay(p);return p.value

def compound(outer,holes=()):
    """One nonzero-filled shape: negative exteriors, positive counters."""
    out=RecordingPen()
    for text,positive in [(outer,False)]+[(h,True) for h in holes]:
        for c in split_contours(path_recording(text)):
            target=(area(c)>0)==positive
            if target:c.replay(out)
            else:c.replay(ReverseContourPen(out))
    pen=SVGPathPen(None,ntos=lambda n:format(n,'.10g'));out.replay(pen)
    return [fill(pen.getCommands())]

def outer_with_holes(ops,stem,hole_strings):
    """Unite the authored exterior then insert deliberately drawn counters.

This does not try to enlarge an absent old counter. It is useful for a
junction where the arm and loop shapes overlap during construction.
"""
    p=one(Resolver({},stem)._ops(ops));out=SVGPathPen(None,ntos=lambda n:format(n,'.10g'))
    for c in split_contours(p):
        if area(c)<-.25:c.replay(out)
    return compound(out.getCommands(),hole_strings)
