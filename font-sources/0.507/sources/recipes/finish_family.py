
"""Family-level metadata and explicitly upright terminal-graphics finishing."""
from pathlib import Path
from copy import deepcopy
from fontTools.ttLib import TTFont
from expansion_design import WEIGHT_NAMES
def finish(folder):
    folder=Path(folder)
    for family in ('sans','mono'):
        for weight,style in WEIGHT_NAMES.items():
            up=folder/f'netfyr{family}-{style}.ttf'
            ip=folder/f'netfyr{family}-{"Italic" if weight==400 else style+"Italic"}.ttf'
            uf=TTFont(up);f=TTFont(ip);uc=uf.getBestCmap()
            for cp,gn in f.getBestCmap().items():
                if (0x2500<=cp<=0x259f or 0x2800<=cp<=0x28ff or
                    0xe0a0<=cp<=0xe0d7 or cp in (0xf8ff,0xe000)):
                    f['glyf'][gn]=deepcopy(uf['glyf'][uc[cp]])
                    f['hmtx'][gn]=uf['hmtx'][uc[cp]]
            f.recalcTimestamp=False;f.save(ip)
        files=sorted(folder.glob(f'netfyr{family}-*.ttf'))
        fonts=[TTFont(p) for p in files]
        asc=max(f['OS/2'].usWinAscent for f in fonts)
        desc=max(f['OS/2'].usWinDescent for f in fonts)
        for p,f in zip(files,fonts):
            f['OS/2'].usWinAscent=asc;f['OS/2'].usWinDescent=desc
            f.recalcTimestamp=False;f.save(p)
if __name__=='__main__':
    import sys
    finish(sys.argv[1])
