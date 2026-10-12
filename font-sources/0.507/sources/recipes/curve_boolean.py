"""Explicit exact-curve Boolean backends.

Skia PathOps is preferred when installed. Inkscape's native path union is an
alternative, not a silent substitute. No raster tracing or polygonization is
used. The original Bezier segments are kept, split at curve intersections.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import functools, hashlib, os, subprocess, xml.etree.ElementTree as ET
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.svgLib.path import parse_path

BACKEND=os.environ.get("NETFYR_BOOLEAN","inkscape")
_CACHE={}
PROFILE=Path(os.environ.get("NETFYR_PROFILE","/tmp/netfyr-inkscape-"+str(os.getpid())))
PROFILE.mkdir(parents=True,exist_ok=True)
(PROFILE/'preferences.xml').write_text(
    '<inkscape><group id="svgoutput" numericprecision="10" minimumexponent="-10"/></inkscape>')
ENV={**os.environ,"INKSCAPE_PROFILE_DIR":str(PROFILE)}
ENGINE_INFO={}

def _d(rec):
    p=SVGPathPen(None,ntos=lambda n:format(n,'.10g'))
    rec.replay(p)
    return p.getCommands()

def _parse(d):
    r=RecordingPen()
    if d:parse_path(d,r)
    return r

def batch(records):
    if BACKEND=="pathops":
        import pathops
        ENGINE_INFO.update(name="skia-pathops",version=pathops.__version__)
        result={}
        for k,r in records.items():
            p=pathops.Path();r.replay(p.getPen())
            q=RecordingPen()
            pathops.simplify(p,fix_winding=True,keep_starting_points=True,clockwise=True).draw(q)
            result[k]=q
        return result
    if BACKEND!="inkscape":raise ValueError("Unknown Boolean engine")
    if not ENGINE_INFO:
        result=subprocess.run(["inkscape","--version"],capture_output=True,text=True,check=True)
        ENGINE_INFO.update(name="inkscape-path-union",version=result.stdout.strip())
    result={k:RecordingPen() for k in records}
    pending=[]
    for k,r in records.items():
        if not r.value:continue
        d=_d(r)
        h=hashlib.sha256(d.encode()).hexdigest()
        if h in _CACHE:result[k]=_parse(_CACHE[h])
        else:pending.append((k,d,h))
    # Keep individual argv items below Linux's single argument length limit.
    for start in range(0,len(pending),350):
        items=pending[start:start+350]
        with TemporaryDirectory(prefix="netfyr-boolean-") as folder:
            folder=Path(folder);inp=folder/'in.svg';out=folder/'out.svg'
            svg=ET.Element("svg",xmlns="http://www.w3.org/2000/svg",viewBox="-1500 -1500 5000 5000")
            actions=[]
            for i,(k,d,h) in enumerate(items):
                ident=f'g{i}'
                ET.SubElement(svg,"path",id=ident,d=d,style="fill-rule:nonzero")
                actions.extend([f"select-by-id:{ident}","path-union","select-clear"])
            inp.write_bytes(ET.tostring(svg))
            actions.extend(["export-plain-svg",f"export-filename:{out}","export-do"])
            run=subprocess.run(["inkscape",str(inp),"--actions="+";".join(actions)],
                               capture_output=True,text=True,env=ENV,timeout=150)
            if run.returncode or not out.exists():
                raise RuntimeError(f"Curve union failed: {run.stderr[-2000:]}")
            paths={el.get('id'):el.get('d','') for el in ET.parse(out).getroot().iter()
                   if el.tag.endswith("path")}
            for i,(k,d,h) in enumerate(items):
                if f'g{i}' not in paths:raise ValueError(f"Boolean removed glyph {k!r}")
                clean=paths[f'g{i}'];_CACHE[h]=clean;result[k]=_parse(clean)
    return result

def one(rec):
    return batch({0:rec})[0]
