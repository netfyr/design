
"""Build original netfyr expansion for local proofing.

Requires the supplied 0.401 source archive for protected upright controls.
No font software license is inferred or changed by this compiler.
Uses explicit native Bezier Boolean operations; audit the selected backend.
"""
from pathlib import Path
from time import time
import json,math,hashlib,sys,argparse,unicodedata as ud,os
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib import TTFont,newTable
from fontTools.ttLib.tables.O_S_2f_2 import Panose
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.areaPen import AreaPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
import build_font as old,ascii_glyphs,extended_latin,symbols,technical,interface_symbols,mono,spacing
from model import glyph,component,fill,transform_ops
from outlines import Resolver,bounds,clean_contours,split_contours
from curve_boolean import batch,ENGINE_INFO
import expansion_design as design
import counter_refinement
import letter_repairs
import xml.etree.ElementTree as ET

VERSION='0.506'
def style_name(weight,italic):
    if weight==400:return 'Italic' if italic else 'Regular'
    return design.WEIGHT_NAMES[weight]+('Italic' if italic else '')
def readable(weight,italic):
    return ('Italic' if weight==400 else design.WEIGHT_NAMES[weight]+' Italic') if italic else design.WEIGHT_NAMES[weight]

def set_names(font,family,weight,italic):
    full_family='netfyr '+family;weightname=design.WEIGHT_NAMES[weight]
    legacy=full_family if weight in (400,700) else full_family+' '+weightname
    legacy_sub=('Bold Italic' if italic else 'Bold') if weight==700 else ('Italic' if italic else 'Regular')
    display=readable(weight,italic)
    ps='netfyr'+family+'-'+style_name(weight,italic)
    ns={1:legacy,2:legacy_sub,3:f'{VERSION};NONE;{ps}',4:full_family+' '+display,
        5:'Version '+VERSION,6:ps,16:full_family,17:display}
    # No invented owner, copyright statement or OFL license.
    for id in ns:
        font['name'].removeNames(nameID=id)
        for platform,encoding,lang in [(3,1,0x409),(1,0,0)]:
            font['name'].setName(ns[id],id,platform,encoding,lang)
    font['head'].fontRevision=float(VERSION)
    font['head'].macStyle=(1 if weight==700 else 0)|(2 if italic else 0)
    font['OS/2'].usWeightClass=weight
    font['OS/2'].fsSelection=0x80|(1 if italic else 0)|(0x20 if weight==700 else 0)|(0x40 if not italic and weight!=700 else 0)
    font['post'].italicAngle=-design.ANGLE if italic else 0
    font['post'].isFixedPitch=int(family=='mono')
    font['hhea'].caretSlopeRise=1000
    font['hhea'].caretSlopeRun=round(1000*design.SHEAR) if italic else 0
    font['hhea'].caretOffset=0
    font.recalcTimestamp=False
    font['head'].created=font['head'].modified=old.FIXED_TIME

def registry(stem,family,italic,logo):
    r={};ascii_glyphs.build(r,stem)
    if family=='mono':mono.prepare_ascii(r,stem)
    design.prepare_ascii(r,stem,family,italic)
    counter_refinement.apply_ascii(r,stem,family,italic)
    for m in (extended_latin,symbols,technical,interface_symbols):m.build(r,stem)
    if family=='mono':mono.prepare_extended(r,stem)
    design.prepare_extended(r,stem,family,italic)
    counter_refinement.apply_extended(r,stem,family,italic)
    letter_repairs.apply(r,stem,family,italic)
    r['.notdef']['master_stem']=stem
    for cp,g in list(r.items()):
        if not isinstance(cp,int):continue
        seq=[ord(c) for c in ud.normalize('NFD',chr(cp))]
        if len(seq)>1 and seq[0] in (ord('i'),ord('j')) and not any(r[c].get('mark')=='above' for c in seq[1:]):
            alt=old.name(cp)+'.dotless'
            glyph(r,alt,[])
            r[alt]['decomposition']=[0x131 if seq[0]==ord('i') else 0x237]+seq[1:]
            g['dotless_alternate']=alt
    path=ET.parse(logo).getroot()[0].attrib['d'];scale=700/120
    glyph(r,0xF8FF,transform_ops([fill(path)],sx=scale,sy=-scale,dx=320-64*scale,dy=126*scale),
          top=(320,755),bottom=(320,-45))
    glyph(r,0xE000,[component(0xF8FF)],top=(320,755),bottom=(320,-45))
    return r

def metadata(fb,r,family,weight,italic,fea):
    fb.setupHorizontalMetrics({old.name(cp):(g['width'],round(g['bounds'][0]) if g.get('bounds') else 0) for cp,g in r.items()})
    fb.setupHorizontalHeader(ascent=1000,descent=-250,lineGap=0)
    fb.setupNameTable({'familyName':'netfyr '+family,'styleName':readable(weight,italic),
        'licenseDescription':'Rights unchanged from supplied 0.401 project. No public redistribution license has been assigned; the netfyr name and flame are separately governed.'})
    bb=[g['bounds'] for g in r.values() if g.get('bounds')]
    p=Panose();p.bFamilyType=2;p.bSerifStyle=11;p.bWeight={300:4,400:5,500:6,600:7,700:8,800:9,900:10}[weight]
    p.bProportion=9 if family=='mono' else 3;p.bContrast=2;p.bStrokeVariation=2;p.bArmStyle=2
    p.bLetterForm=11 if italic else 4;p.bMidline=2;p.bXHeight=4
    fb.setupOS2(version=4,sTypoAscender=1000,sTypoDescender=-250,sTypoLineGap=0,
        usWinAscent=max(1000,math.ceil(max(b[3] for b in bb))),
        usWinDescent=max(250,math.ceil(-min(b[1] for b in bb))),
        usWeightClass=weight,usWidthClass=5,fsType=0,fsSelection=0x80,
        sxHeight=520,sCapHeight=700,panose=p,achVendID='NONE')
    fb.setupPost(isFixedPitch=int(family=='mono'),italicAngle=-10 if italic else 0,
                 underlinePosition=-145,underlineThickness=round(design.WEIGHTS[weight]*.85))
    if family=='mono':fb.font['OS/2'].xAvgCharWidth=640
    set_names(fb.font,family,weight,italic)
    addOpenTypeFeaturesFromString(fb.font,fea)
    gasp=newTable('gasp');gasp.gaspRange={65535:10};fb.font['gasp']=gasp

def quantize_union(font):
    """Clean the actual compiled quadratic curves, without raster tracing."""
    gs=font.getGlyphSet();recordings={}
    for gn in font.getGlyphOrder():
        p=RecordingPen();gs[gn].draw(p);recordings[gn]=p
    merged=batch(recordings);removed=[]
    for gn,p in merged.items():
        keep=[]
        for c in split_contours(p):
            ap=AreaPen(None);c.replay(ap)
            if abs(ap.value)<.5:removed.append((gn,ap.value))
            else:keep.append(c)
        pen=TTGlyphPen(None);cu=Cu2QuPen(pen,max_err=.35,reverse_direction=False)
        for c in keep:c.replay(cu)
        g=pen.glyph();g.recalcBounds(font['glyf'])
        if g.numberOfContours>0:g.flags[0]|=0x40
        font['glyf'][gn]=g
        adv=font['hmtx'][gn][0]
        font['hmtx'][gn]=(adv,g.xMin if g.numberOfContours else 0)
    return removed

def build(args):
    t=time();weight=args.weight;family=args.family;italic=args.italic;stem=design.WEIGHTS[weight]
    style=style_name(weight,italic);directory=args.output
    for d in ('fonts','reports'):(directory/d).mkdir(parents=True,exist_ok=True)
    output=directory/'fonts'/f'netfyr{family}-{style}.ttf'
    report={'family':'netfyr '+family,'style':style,'weight':weight,'italic':italic,
            'stem':stem,'version':VERSION,'pid':os.getpid(),'start_unix':t}
    # Preserve actual reference geometry/layout, not only the reconstructed recipes.
    if weight in (400,600) and not italic:
        ref=args.reference/'fonts'/f'netfyr-{family}-{"Regular" if weight==400 else "Semibold"}.ttf'
        f=TTFont(ref);set_names(f,family,weight,False);f.save(output)
        report['protected_reference']=str(ref)
        report['reference_sha256']=hashlib.sha256(ref.read_bytes()).hexdigest()
    else:
        design.configure_spacing(spacing,stem,italic)
        r=registry(stem,family,italic,args.logo)
        resolver=(mono.MonoResolver if family=='mono' else Resolver)(r,stem)
        for cp in r:resolver.resolve(cp)
        cleanup=clean_contours(r,resolver)
        if family=='sans':spacing.fit(r,resolver,stem)
        # All fallback anchors must be made explicit BEFORE shear.
        for cp,g in r.items():
            if g.get('width') and not g.get('mark'):
                g.setdefault('overlay',(320,260))
                g.setdefault('right',(510,510))
        if italic:design.slant(r,resolver)
        order=['.notdef']+[old.name(cp) for cp in r if cp!='.notdef']
        cmap={cp:old.name(cp) for cp in r if isinstance(cp,int)}
        for cp in list(cmap):
            dec=ud.decomposition(chr(cp)).split()
            if len(dec)==1 and not dec[0].startswith('<') and int(dec[0],16) in r:
                cmap[cp]=old.name(int(dec[0],16))
        fb=FontBuilder(1000,isTTF=True);fb.setupGlyphOrder(order);fb.setupCharacterMap(cmap)
        gs={}
        for cp in r:
            p=TTGlyphPen(None)
            resolver.cache[cp].replay(Cu2QuPen(p,max_err=.35,reverse_direction=False))
            g=p.glyph()
            if g.numberOfContours:g.flags[0]|=0x40
            gs[old.name(cp)]=g
        fb.setupGlyf(gs)
        fea=old.features(r,family)
        metadata(fb,r,family,weight,italic,fea)
        # Keep origins: compiled control-point bounds are not cubic ink bounds.
        for gn,g in gs.items():
            fb.font['hmtx'][gn]=(fb.font['hmtx'][gn][0],g.xMin if g.numberOfContours else 0)
        removed=quantize_union(fb.font)
        fb.save(output)
        report['cleanup_engine']=cleanup['engine']
        report['cleanup_max_bound_shift']=max((v['bounds_shift'] for v in cleanup['glyphs']),default=0)
        report['quantized_fragments_removed']=removed
        report['mono_fitting']=getattr(resolver,'mono_records',[])
    f=TTFont(output)
    report.update({'encoded':len(f.getBestCmap()),'glyphs':len(f.getGlyphOrder()),
        'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'seconds':round(time()-t,3),'end_unix':time()})
    (directory/'reports'/f'netfyr{family}-{style}.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:report[k] for k in ('family','style','encoded','seconds','bytes')}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--family',choices=['sans','mono'],required=True)
    p.add_argument('--weight',type=int,choices=list(design.WEIGHTS),required=True)
    p.add_argument('--italic',action='store_true')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--logo',type=Path,required=True)
    build(p.parse_args())
