
"""Apply the measured, style-specific positive clearance deltas.

No glyph outline, advance width, or Mono positioning is changed here.
The resulting source build should be rerun through QA on the local platform.
"""
from pathlib import Path
import json
from fontTools.ttLib import TTFont
from fontTools.otlLib.builder import buildPairPosGlyphs,buildValue,buildLookup
def apply(folder,datafile):
    folder=Path(folder)
    for stem,records in json.loads(Path(datafile).read_text()).items():
        if not records:continue
        path=folder/(stem+'.ttf');f=TTFont(path)
        if f['post'].isFixedPitch:raise ValueError('Mono must not have pair kerning')
        groups={}
        for row in records:groups.setdefault(row['left'],[]).append(row)
        chunks=[];chunk={}
        for values in groups.values():
            if chunk and len(chunk)+len(values)>2500:chunks.append(chunk);chunk={}
            for row in values:chunk[row['left'],row['right']]=(buildValue({'XAdvance':row['advance']}),None)
        if chunk:chunks.append(chunk)
        lookups=f['GPOS'].table.LookupList.Lookup
        features=[r.Feature for r in f['GPOS'].table.FeatureList.FeatureRecord if r.FeatureTag=='kern']
        if not features:raise ValueError('Sans kern feature missing')
        ids=[]
        for values in chunks:
            ids.append(len(lookups))
            lookups.append(buildLookup(buildPairPosGlyphs(values,f.getReverseGlyphMap()),flags=8,table='GPOS',extension=True))
        f['GPOS'].table.LookupList.LookupCount=len(lookups)
        for feature in features:
            feature.LookupListIndex.extend(ids);feature.LookupCount=len(feature.LookupListIndex)
        f.recalcTimestamp=False;f.save(path)
if __name__=='__main__':
    import sys
    apply(sys.argv[1],sys.argv[2])
