
"""Measured positive clearance corrections for new proportional styles.

A 500px/em Cairo raster of the actual quadratic outlines confirms negative
profile gaps. False envelope overlaps are not treated as real collisions.
Only non-mark, non-control, non-technical two-glyph text runs are eligible.
No correction is allowed to a fixed-width font or the protected uprights.
This is finite raster validation, not a certification of all vector contexts.
"""
from pathlib import Path
import sys,json,argparse,time,os,hashlib,math
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.otlLib.builder import buildPairPosGlyphs,buildValue,buildLookup
import raster_profiles as rp
from shaping import Shaper
DT=np.dtype([('count','<u2'),('flags','<u2'),('gap','<i2'),('optical','<i2'),('kern','<i2'),('overlap_rows','<i2'),('advance','<i4')])

def overlaps(a,b,ax,ay,bx,by):
    # Four neighboring pixel translations conservatively cover fractional shifts.
    aa,x0,y0=a;bb,x1,y1=b
    aa=aa>=128;bb=bb>=128
    for dx in {math.floor((bx-ax)/2),math.ceil((bx-ax)/2)}:
        for dy in {math.floor((by-ay)/2),math.ceil((by-ay)/2)}:
            left0=x0;top0=-y0;left1=x1+dx;top1=-y1-dy
            l=max(left0,left1);r=min(left0+aa.shape[1],left1+bb.shape[1])
            t=max(top0,top1);bot=min(top0+aa.shape[0],top1+bb.shape[0])
            if r>l and bot>t:
                if np.any(aa[t-top0:bot-top0,l-left0:r-left0] & bb[t-top1:bot-top1,l-left1:r-left1]):return True
    return False

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--font',type=Path,required=True)
    ap.add_argument('--audit',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--verify-only',action='store_true')
    args=ap.parse_args();start=time.time()
    font=TTFont(args.font);name=font['name'].getDebugName(4)
    if font['post'].isFixedPitch:raise ValueError('Never apply pair correction to Mono')
    sha=hashlib.sha256(args.font.read_bytes()).hexdigest()
    inv=json.loads((args.audit/'individual-audit.json').read_text())
    if inv['sha256']!=sha:raise ValueError('Profile is not from this exact font')
    cc=inv['characters'];n=len(cc);m=np.memmap(args.audit/'pairs.bin',dtype=DT,mode='r',offset=24,shape=(n,n))
    flags=np.array([c['flags'] for c in cc])
    allowed=((flags&(1|2|4|8))==0)
    ordinary=(m['flags']&(8|16|32|64))==0
    eligible=ordinary & allowed[:,None] & allowed[None,:]
    ii,jj=np.where(eligible&(m['gap']<0))
    sh=Shaper(args.font);gs=font.getGlyphSet();rendered={};corrections={};records=[];false=0
    def image(gn):
        if gn not in rendered:
            g=font['glyf'][gn]
            bb=[g.xMin,g.yMin,g.xMax,g.yMax] if g.numberOfContours else None
            rendered[gn]=rp.render(gs,gn,bb)
        return rendered[gn]
    for i,j in zip(ii,jj):
        cpa=cc[int(i)]['decimal'];cpb=cc[int(j)]['decimal'];text=chr(cpa)+chr(cpb)
        run=sh.shape(text)
        if len(run)!=2:continue
        a,b=run;im1=image(a['glyph']);im2=image(b['glyph'])
        if im1 is None or im2 is None:continue
        x1=a['x'];y1=a['y'];x2=a['advance']+b['x'];y2=b['y']
        if not overlaps(im1,im2,x1,y1,x2,y2):
            false+=1;continue
        delta=18-int(m[int(i),int(j)]['gap'])
        pair=(a['glyph'],b['glyph'])
        corrections[pair]=max(corrections.get(pair,0),delta)
        records.append({'first':cpa,'second':cpb,'pair':list(pair),'gap':int(m[int(i),int(j)]['gap']),'additional_advance':delta})
    sh.close()
    # Chunk by first glyph. Extension lookups prevent a large global offset.
    if corrections and not args.verify_only:
        groups={}
        for pair,value in corrections.items():groups.setdefault(pair[0],[]).append((pair,value))
        chunks=[];chunk={}
        for first,values in groups.items():
            if len(chunk)+len(values)>2500 and chunk:chunks.append(chunk);chunk={}
            for pair,value in values:chunk[pair]=(buildValue({'XAdvance':value}),None)
        if chunk:chunks.append(chunk)
        lookups=font['GPOS'].table.LookupList.Lookup
        kern_features=[x.Feature for x in font['GPOS'].table.FeatureList.FeatureRecord if x.FeatureTag=='kern']
        if not kern_features:raise ValueError('No kern feature to extend')
        indices=[]
        for c in chunks:
            st=buildPairPosGlyphs(c,font.getReverseGlyphMap())
            lookup=buildLookup(st,flags=8,table='GPOS',extension=True)
            indices.append(len(lookups));lookups.append(lookup)
        font['GPOS'].table.LookupList.LookupCount=len(lookups)
        for feat in kern_features:
            feat.LookupListIndex.extend(indices);feat.LookupCount=len(feat.LookupListIndex)
        font.recalcTimestamp=False;font.save(args.font)
    report={'font':name,'input_sha256':sha,'output_sha256':hashlib.sha256(args.font.read_bytes()).hexdigest(),
      'method':__doc__,'eligible_pairs':int(eligible.sum()),'profile_candidates':len(ii),
      'confirmed_encoded_pairs':len(records),'unique_glyph_pairs':len(corrections),
      'envelope_only_not_changed':false,'max_positive_correction':max(corrections.values(),default=0),
      'corrections':records,'glyph_pairs':[{'left':a,'right':b,'advance':d} for (a,b),d in sorted(corrections.items())],
      'pid':os.getpid(),'seconds':time.time()-start,'read_only':args.verify_only}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({k:report[k] for k in ['font','profile_candidates','confirmed_encoded_pairs','unique_glyph_pairs','seconds']}))
if __name__=='__main__':main()
