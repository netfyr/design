
"""Disjoint read-only validation tracks for the actual expansion TTFs."""
from pathlib import Path
import argparse,json,hashlib,time,os,math,unicodedata as ud,ctypes as C
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from shaping import Shaper,HB

WEIGHTS={300:'Light',400:'Regular',500:'Medium',600:'SemiBold',700:'Bold',800:'ExtraBold',900:'Black'}
def ident(f,w,i):
    st=('Italic' if w==400 else WEIGHTS[w]+'Italic') if i else WEIGHTS[w]
    return f'netfyr{f}-{st}'
def listed(folder):
    return [(folder/(ident(f,w,i)+'.ttf'),f,w,i) for f in ['sans','mono'] for w in WEIGHTS for i in [False,True]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cell(cp):
    return 0x2500<=cp<=0x259f or 0x2800<=cp<=0x28ff or 0xe0a0<=cp<=0xe0d7 or cp in (0xf8ff,0xe000)
def glyph_record(f,gn):
    p=RecordingPen();f.getGlyphSet()[gn].draw(p);return p.value
def metadata(args):
    rows=[];issues=[]
    repair_rows={row['file']:row for row in json.loads(args.repairs.read_text())['files']} if args.repairs else {}
    refcmap=set(TTFont(args.reference/'fonts/netfyr-sans-Regular.ttf').getBestCmap())
    for p,fam,w,it in listed(args.fonts):
        f=TTFont(p);cm=f.getBestCmap();errs=[]
        if set(cm)!=refcmap:errs.append('encoded set differs from reference')
        if f['OS/2'].usWeightClass!=w:errs.append('wrong weight class')
        if bool(f['head'].macStyle&2)!=it:errs.append('wrong italic bit')
        if bool(f['OS/2'].fsSelection&1)!=it:errs.append('wrong fsSelection italic')
        if (f['post'].italicAngle<0)!=it:errs.append('wrong post angle')
        if bool(f['post'].isFixedPitch)!=(fam=='mono'):errs.append('wrong pitch')
        if tuple((f['hhea'].ascent,f['hhea'].descent,f['hhea'].lineGap))!=(1000,-250,0):errs.append('cell metrics changed')
        if args.repairs and (f['OS/2'].usWinAscent < f['head'].yMax or f['OS/2'].usWinDescent < -f['head'].yMin):
            errs.append('Windows clipping extents exclude final glyph ink')
        if fam=='mono':
            bad=[(cp,f['hmtx'][gn][0]) for cp,gn in cm.items() if f['hmtx'][gn][0] not in (0,640)]
            if bad:errs.append(('non-cell advances',bad))
            if 'GPOS' in f and f['GPOS'].table.FeatureList:
                if any(r.FeatureTag=='kern' for r in f['GPOS'].table.FeatureList.FeatureRecord):errs.append('Mono has kern feature')
        if w in (400,600) and not it:
            ref=TTFont(args.reference/'fonts'/f'netfyr-{fam}-{"Regular" if w==400 else "Semibold"}.ttf')
            declared=repair_rows.get(p.name,{})
            allowed=set(declared.get('approved_glyphs',[]))
            metric_changes=declared.get('metric_changes',{})
            for gn,metric in ref['hmtx'].metrics.items():
                actual=f['hmtx'][gn]
                approved_metric=metric_changes.get(gn)
                if ((approved_metric and tuple(approved_metric['after'])!=actual) or
                    (not approved_metric and actual[0]!=metric[0]) or (gn not in allowed and actual!=metric)):
                    errs.append(('undeclared protected metric change',gn));break
            for gn in ref.getGlyphOrder():
                if gn not in allowed and ref['glyf'][gn].compile(ref['glyf'])!=f['glyf'][gn].compile(f['glyf']):
                    errs.append(('protected outline changed',gn));break
        row=dict(file=p.name,sha256=sha(p),encoded=len(cm),glyphs=len(f.getGlyphOrder()),
                 names={str(n):f['name'].getDebugName(n) for n in [1,2,4,6,16,17]},
                 weight=w,italic=it,fixed_pitch=bool(f['post'].isFixedPitch),issues=errs)
        rows.append(row)
        if errs:issues.append((p.name,errs))
    return {'track':'metadata, encoding and protected references','files':rows,'issues':issues,'passed':not issues}

def aggregate(sh,text):
    run=sh.shape(text);pos=0;bp=BoundsPen(sh.tt.getGlyphSet())
    for g in run:
        sh.tt.getGlyphSet()[g['glyph']].draw(TransformPen(bp,(1,0,0,1,pos+g['x'],g['y'])))
        pos+=g['advance']
    return pos,bp.bounds,run

def shaping(args):
    records=[];allissues=[]
    for p,fam,w,it in listed(args.fonts):
        sh=Shaper(p);cm=sh.cmap;cases=[];cgj=[];bad=[]
        for cp in sorted(cm):
            decomp=ud.normalize('NFD',chr(cp))
            if len(decomp)>1 and all(ord(c) in cm for c in decomp):
                a=aggregate(sh,chr(cp));b=aggregate(sh,decomp)
                diff=max([abs(x-y) for x,y in zip(a[1] or [0]*4,b[1] or [0]*4)]+[abs(a[0]-b[0])])
                cases.append((cp,diff))
                if diff>1.5:bad.append({'codepoint':cp,'kind':'canonical','bound_or_advance_difference':diff})
                if ud.category(decomp[0]).startswith('L'):
                    cg=decomp[0]+'\u034f'+decomp[1:]
                    d=aggregate(sh,cg)
                    diff=max([abs(x-y) for x,y in zip(a[1] or [0]*4,d[1] or [0]*4)]+[abs(a[0]-d[0])])
                    cgj.append((cp,diff))
                    if diff>3:bad.append({'codepoint':cp,'kind':'CGJ rendering bounds','bound_or_advance_difference':diff})
        regressions=['i\u034f','j\u034f','i\u034f\u0301','i\u0328\u0301',
          'a\u0302\u0301','U\u031b\u0301','u\u031b\u0300','≠','=\u034f\u0338','∈\u034f\u0338',
          'a\u0301b','ǻ ắ ớ ȷ ǰ','\uf8ff\ue000']
        for text in regressions:
            run=sh.shape(text)
            if any(g['gid']==0 for g in run):bad.append({'kind':'missing contextual glyph','text':text})
            if fam=='mono':
                for g in run:
                    if g['advance'] not in (0,640):bad.append({'kind':'non-cell shaped advance','text':text})
        rec={'file':p.name,'sha256':sha(p),'canonical_cases':len(cases),
             'canonical_max_bounds_delta':max([d for _,d in cases],default=0),
             'CGJ_cases':len(cgj),'CGJ_max_bounds_delta':max([d for _,d in cgj],default=0),
             'CGJ_scope':'A bounds/advance test, not complete outline identity.',
             'context_cases':len(regressions),'issues':bad}
        records.append(rec)
        if bad:allissues.append((p.name,bad))
        sh.close()
    return {'track':'native HarfBuzz canonical and contextual shaping','files':records,'issues':allissues,'passed':not allissues}

def geometry(args):
    files=[];areas={};issues=[];control='HabdegopqrswWAMOnm'
    for p,fam,w,it in listed(args.fonts):
        f=TTFont(p);cm=f.getBestCmap();gs=f.getGlyphSet();small=[];bad=[];metrics={}
        for cp,gn in cm.items():
            g=f['glyf'][gn]
            if g.numberOfContours:
                if g.xMax<=g.xMin or g.yMax<=g.yMin:bad.append((cp,'zero-dimensional outline'))
                ap=AreaPen(gs);gs[gn].draw(ap)
                if abs(ap.value)<.1 and cp not in (0x34f,):small.append((cp,ap.value))
                if not all(math.isfinite(x) for pt in g.getCoordinates(f['glyf'])[0] for x in pt):
                    bad.append((cp,'nonfinite coordinates'))
        for c in control:
            gn=cm[ord(c)];g=f['glyf'][gn];ap=AreaPen(gs);gs[gn].draw(ap)
            metrics[c]={'area':abs(ap.value),'contours':g.numberOfContours,
                        'bounds':[g.xMin,g.yMin,g.xMax,g.yMax]}
            areas[(fam,it,w,c)]=abs(ap.value)
        files.append({'file':p.name,'sha256':sha(p),'encoded_outlines_inspected':len(cm),
                     'tiny_signed_areas':small,'issues':bad,'controls':metrics})
        if bad:issues.append((p.name,bad))
    monotonic=[]
    for fam in ['sans','mono']:
        for it in [False,True]:
            for c in 'HOnom':
                seq=[(w,areas.get((fam,it,w,c))) for w in WEIGHTS]
                if any(a[1]>b[1]*1.02 for a,b in zip(seq,seq[1:])):
                    monotonic.append({'family':fam,'italic':it,'character':c,'areas':seq})
    return {'track':'all-encoded outline integrity and optical mass progression','files':files,
            'issues':issues,'mass_progression_flags':monotonic,'passed':not issues and not monotonic}

def cells(args):
    rows=[];issues=[]
    for p,fam,w,it in listed(args.fonts):
        f=TTFont(p);cm=f.getBestCmap();bad=[]
        for cp in [0x2591,0x2592,0x2593,0x2502]:
            g=f['glyf'][cm[cp]]
            if (g.yMin,g.yMax)!=(-250,1000):bad.append((cp,'wrong full height',[g.yMin,g.yMax]))
            if f['hmtx'][cm[cp]][0]!=640:bad.append((cp,'wrong cell width'))
        if it:
            upright=TTFont(args.fonts/(ident(fam,w,False)+'.ttf'));uc=upright.getBestCmap()
            for cp,gn in cm.items():
                if cell(cp):
                    if glyph_record(f,gn)!=glyph_record(upright,uc[cp]):
                        # A node-start difference alone is not a geometry failure.
                        ap=AreaPen(f.getGlyphSet());f.getGlyphSet()[gn].draw(ap)
                        bp=AreaPen(upright.getGlyphSet());upright.getGlyphSet()[uc[cp]].draw(bp)
                        a=f['glyf'][gn];b=upright['glyf'][uc[cp]]
                        if abs(ap.value-bp.value)>1 or [a.xMin,a.yMin,a.xMax,a.yMax]!=[b.xMin,b.yMin,b.xMax,b.yMax]:
                            bad.append((cp,'upright graphics changed in italic'))
        rows.append({'file':p.name,'sha256':sha(p),'full_height_probes':4,
                     'upright_graphics_compared':sum(cell(cp) for cp in cm) if it else 0,'issues':bad})
        if bad:issues.append((p.name,bad))
    return {'track':'terminal cells and upright graphics','files':rows,'issues':issues,'passed':not issues}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--track',choices=['metadata','shaping','geometry','cells'],required=True)
    p.add_argument('--fonts',type=Path,required=True);p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--repairs',type=Path,help='Declared corrections; all other protected glyphs and advances remain unchanged')
    args=p.parse_args()
    begin=time.time();report=globals()[args.track](args)
    report.update(pid=os.getpid(),started=begin,ended=time.time(),seconds=time.time()-begin)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({'track':args.track,'passed':report['passed'],'seconds':report['seconds'],'files':len(report['files'])}))
