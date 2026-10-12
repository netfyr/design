"""Authored optical fitting, applied after component assembly.

The recipes retain their original design-space origin. Completed outlines and
their anchors are translated together; canonical composites inherit the base
advance even when a diacritic overhangs. No outline is stretched to make it fit.
The values here are design decisions refined against actual text proofs.
"""
import unicodedata as ud
from outlines import transformed, bounds
from kern_exceptions import EXCEPTIONS

# Negative-space families: straight sides need more bearing than round sides;
# open sides and diagonal sides have their own fitting. These are not bbox-gap
# equalization targets. Pair-specific optical exceptions are in KERN below.
BEARINGS = {
    '§':(50,50),
    'A':(28,28),'B':(62,43),'C':(40,33),'D':(62,44),'E':(62,40),
    'F':(62,28),'G':(40,48),'H':(62,62),'I':(48,48),'J':(32,45),
    'K':(62,25),'L':(62,26),'M':(62,62),'N':(62,62),'O':(40,40),
    'P':(62,36),'Q':(40,32),'R':(62,24),'S':(40,38),'T':(27,27),
    'U':(58,58),'V':(25,25),'W':(25,25),'X':(27,27),'Y':(25,25),'Z':(32,32),
    'ß':(62,42),'ẞ':(62,42),'æ':(43,32),'ð':(40,40),'œ':(40,32),
    'a':(43,55),'b':(62,42),'c':(40,30),'d':(42,62),'e':(40,32),
    'f':(24,18),'g':(42,57),'h':(62,52),'i':(70,70),'j':(18,62),
    'k':(62,27),'l':(62,35),'m':(62,52),'n':(62,52),'o':(40,40),
    'p':(62,42),'q':(42,62),'r':(62,25),'s':(36,33),'t':(29,28),
    'u':(55,62),'v':(22,22),'w':(22,22),'x':(25,25),'y':(22,22),'z':(30,30),
}

COMMON_BASE = {
    0x131:'i',0x237:'j',0xD0:'D',0x110:'D',0x111:'d',0x126:'H',0x127:'h',
    0x141:'L',0x142:'l',0x166:'T',0x167:'t',0xD8:'O',0xF8:'o',
    0x180:'b',0x189:'D',0x197:'I',0x19A:'l',0x19F:'O',0x1B5:'Z',0x1B6:'z',
    0x240:'z',0x249:'j',0x24B:'q',0x24D:'r',0x24F:'y',
    0x391:'A',0x392:'B',0x395:'E',0x397:'H',0x399:'I',0x39A:'K',
    0x39C:'M',0x39D:'N',0x39F:'O',0x3A1:'P',0x3A4:'T',0x3A5:'Y',0x3A7:'X',
    0x3BF:'o',0x3C1:'p',0x3BD:'v',0x3C5:'u',0x3BA:'k',0x3C4:'t',
}

# Both quote styles share metrics and kerning classes. The shapes remain
# independently authored and retain their semantics.
PUNCT_BASE = {0x2018:"'",0x2019:"'",0x201A:',',0x201B:"'",0x201C:'"',
              0x201D:'"',0x201E:'"',0x201F:'"',0x2032:"'",0x2033:'"',
              0x2010:'-',0x2011:'-',0xAD:'-',0x2024:'.',0xFE52:'.'}

KERN = {}
def pairs(left,right,value):
    for a in left:
        for b in right:KERN[a,b]=value

pairs('A','VY',-65);pairs('A','WT',-45);pairs('A','OUCGQ',-15)
pairs('VY','A',-65);pairs('WT','A',-45)
pairs('V','acdegoqs',-45);pairs('V','u',-25)
pairs('W','acdegoqs',-30);pairs('W','u',-18)
pairs('Y','acdegoqs',-65);pairs('Y','u',-40)
pairs('T','acdegoqs',-65);pairs('T','nmrup',-40);pairs('T','yvw',-25)
pairs('F','adegoq',-30);pairs('F','.,',-60)
pairs('P','A',-40);pairs('P','.,',-70)
pairs('L','TYVW',-55);pairs('L','O',-15)
pairs('OQ','A',-15);pairs('O','TY',-20)
pairs('R','TYV',-18)
pairs('r','.,',-65);pairs('r','adegoq',-10)
pairs('vwy','.,',-40);pairs('vwy','adegoq',-12)
pairs('k','adegoq',-15);pairs('x','adegoq',-15)
pairs('oaec','vwy',-10)
pairs('.,','TYVW',-65);pairs('TYVW','.,',-65)
pairs('A','\'"',-45);pairs('\'"','A',-45)
pairs('f','\'"',18);pairs('f',')]}',12)
pairs('(','j',20)

# The ash ligature has the outside profiles of a on the left and e on the right.
for (left,right),value in list(KERN.items()):
    if right=='a':KERN[left,'æ']=value
    if right=='o':KERN[left,'œ']=value
    if left=='e':
        KERN['æ',right]=value
        KERN['œ',right]=value

# Eth has o's bowl fit, while its ascender requires its own upper-case contexts.
# Its lowercase outside contours share the appropriate round-side pairs.
for (left,right),value in list(KERN.items()):
    if right=='o' and left in 'rvwykx':KERN[left,'ð']=value
    if left=='o' and right in 'vwy':KERN['ð',right]=value

def base_key(cp,r):
    if isinstance(cp,str):
        if cp.endswith('.dotless'):
            source=int(cp[3:7],16)
            return base_key(source,r)
        return None
    decomp=ud.normalize('NFD',chr(cp))
    if len(decomp)>1:return base_key(ord(decomp[0]),r)
    if cp in COMMON_BASE:return COMMON_BASE[cp]
    if cp in PUNCT_BASE:return PUNCT_BASE[cp]
    ch=chr(cp)
    return ch if ch in BEARINGS or ch in '0123456789.,:;!?\'"()[]{}-+*/=<>\\|_~' else None

def fit(r,resolver,stem):
    original={cp:tuple(g['bounds']) if g.get('bounds') else None for cp,g in r.items()}
    fitted={}
    def metrics(cp):
        if cp in fitted:return fitted[cp]
        g=r[cp];bb=original[cp];key=base_key(cp,r)
        if g.get('mark') or g['width']==0:
            result=(0,0,key)
        elif isinstance(cp,int) and ud.normalize('NFD',chr(cp))!=chr(cp) and g.get('decomposition'):
            first=resolver.flatten(cp)[0]
            result=metrics(first)
        elif isinstance(cp,str) and cp.endswith('.dotless'):
            result=metrics(int(cp[3:7],16))
        elif cp in (ord('i'),ord('j')):
            result=metrics(0x131 if cp==ord('i') else 0x237)
        elif cp==0x1E5:
            result=metrics(ord('g'))
        elif cp in (0x20,0xA0):result=(275,0,'space')
        elif cp in (0x2000,0x2002):result=(500,0,None)
        elif cp in (0x2001,0x2003):result=(1000,0,None)
        elif cp==0x2004:result=(333,0,None)
        elif cp==0x2005:result=(250,0,None)
        elif cp==0x2006:result=(167,0,None)
        elif cp==0x2007:result=(600,0,None)
        elif cp==0x2008:result=(255,0,None)
        elif cp in (0x2009,0x202F):result=(200,0,None)
        elif cp==0x200A:result=(100,0,None)
        elif not bb:result=(g['width'],0,key)
        elif isinstance(cp,int) and (0x2500<=cp<=0x259F or 0x2800<=cp<=0x28FF or 0xE0A0<=cp<=0xE0D7 or cp in (0xF8FF,0xE000)):
            result=(640,0,key)
        elif key and key in '0123456789':
            result=(600,round((600-(bb[2]-bb[0]))/2-bb[0]),key)
        elif key in BEARINGS:
            lft,rgt=BEARINGS[key]
            # Heavier counters need a modestly tighter surrounding rhythm.
            reduction=(stem-72)/3
            lft-=reduction;rgt-=reduction
            dx=round(lft-bb[0]);adv=round(bb[2]+dx+rgt)
            result=(adv,dx,key)
        elif key in ('.',',',':',';'):
            adv=255 if key in ('.',',') else 275
            # Align the round dot, rather than the comma's descending tail.
            dx=round(adv/2-320)
            result=(adv,dx,key)
        elif key in ("'",'"'):
            margin=57 if key=="'" else 50
            result=(round(bb[2]-bb[0]+2*margin),round(margin-bb[0]),key)
        elif key in ('(',')','[',']','{','}'):
            left,right=(65,43) if key in '([{' else (43,65)
            result=(round(bb[2]-bb[0]+left+right),round(left-bb[0]),key)
        elif key=='!':result=(295,round(147.5-(bb[0]+bb[2])/2),key)
        elif key=='?':result=(round(bb[2]-bb[0]+88),round(42-bb[0]),key)
        elif key=='-':result=(420,round(210-(bb[0]+bb[2])/2),key)
        elif cp in (0x2013,):result=(600,round(300-(bb[0]+bb[2])/2),key)
        elif cp in (0x2014,):result=(1000,round(500-(bb[0]+bb[2])/2),key)
        elif isinstance(cp,int) and ud.category(chr(cp)).startswith('L'):
            category=ud.category(chr(cp))
            lft,rgt=(52,48) if category in ('Lu','Lt') else (48,42)
            reduction=(stem-72)/3
            result=(round(bb[2]-bb[0]+lft+rgt-2*reduction),round(lft-reduction-bb[0]),key)
        elif isinstance(cp,int) and ud.category(chr(cp)) in ('Pe','Pf','Pi','Ps'):
            result=(round(bb[2]-bb[0]+105),round(52-bb[0]),key)
        elif isinstance(cp,int) and ud.category(chr(cp))=='Pd':
            result=(round(bb[2]-bb[0]+100),round(50-bb[0]),key)
        elif isinstance(cp,int) and ud.category(chr(cp))=='Sc':
            # Broad original currency signs (notably won and mill) need their
            # own fitted width. A 640-unit advance previously clipped their
            # sidebearings and caused repeated symbols to collide.
            adv=max(640,round(bb[2]-bb[0]+96))
            result=(adv,round((adv-bb[2]-bb[0])/2),key)
        else:result=(640,0,key)
        fitted[cp]=result;return result
    for cp in r:metrics(cp)
    for cp,g in r.items():
        advance,dx,key=fitted[cp]
        g['width']=advance;g['fit_key']=key;g['fit_translation']=dx
        if g.get('mark'):continue
        g.setdefault('overlay',(320,260))
        if dx:
            resolver.cache[cp]=transformed(resolver.cache[cp],[1,0,0,1,dx,0])
            for anchor in ('top','bottom','right','ogonek','dotbelow','overlay','tone'):
                if g.get(anchor):g[anchor]=(g[anchor][0]+dx,g[anchor][1])
        g['bounds']=list(bounds(resolver.cache[cp])) if original[cp] else None
    return fitted

def feature_code(r,name):
    groups={}
    for cp,g in r.items():
        key=g.get('fit_key')
        if key and g['width'] and any(key in pair for pair in KERN):groups.setdefault(key,[]).append(name(cp))
    labels={key:'K_'+str(i) for i,key in enumerate(sorted(groups))}
    lines=[]
    for key,chars in groups.items():lines.append('@'+labels[key]+' = ['+' '.join(chars)+'];')
    lines += ['feature kern {','  lookup KERN_TEXT {','    lookupflag IgnoreMarks;']
    for (a,b),value in sorted(KERN.items()):
        if a in groups and b in groups:lines.append(f'    pos @{labels[a]} @{labels[b]} {value};')
    lines+=['  } KERN_TEXT;']
    exceptions=EXCEPTIONS.get(r['.notdef'].get('master_stem',72),{})
    if exceptions:
        lines+=['  lookup KERN_CLEARANCE {','    lookupflag IgnoreMarks;']
        for (a,b),value in sorted(exceptions.items()):
            lines.append(f'    pos {a} {b} {value};')
        lines+=['  } KERN_CLEARANCE;']
    lines+=['} kern;']
    return '\n'.join(lines)+'\n'
