"""Inherited OpenType composition and mark attachment, retained from 0.401.

This is a helper for expand_family.py, not a separate build entrypoint.
The original archive remains the provenance reference.
"""
import unicodedata as ud
from composition import math_negation_lookups
import spacing
FIXED_TIME=3874262400

def name(cp):return f'uni{cp:04X}' if isinstance(cp,int) else cp

def features(r,family='sans'):
    lines=['languagesystem DFLT dflt;','languagesystem latn dflt;','languagesystem grek dflt;']
    def attachment(g):return 'tone' if g.get('use_stack_right') else (g.get('attachment') or g.get('mark'))
    groups={kind:[cp for cp,g in r.items() if attachment(g)==kind] for kind in ('above','below','overlay','right','ogonek','dotbelow','tone')}
    for kind,cps in groups.items():
        if not cps:continue
        names=' '.join(map(name,cps))
        lines += [f'@SET_{kind} = [{names}];',f'markClass [{names}] <anchor 0 0> @MC_{kind};']
    # CGJ is an invisible combining mark. Keep its GDEF/attachment class, but
    # do not let it trigger dot removal or count as a visible above accent.
    # UseMarkFilteringSet then skips CGJ while looking for a real above mark.
    above=[name(cp) for cp,g in r.items()
           if g.get('mark')=='above' and cp!=0x34F]
    lines += ['@ABOVE_ALL = ['+' '.join(above)+'];', 'feature ccmp {']
    lines += math_negation_lookups(r,name)
    lines += ['  lookup DOTLESS {','    lookupflag UseMarkFilteringSet @ABOVE_ALL;',
              "    sub uni0069' @ABOVE_ALL by uni0131;","    sub uni006A' @ABOVE_ALL by uni0237;"]
    for cp,g in r.items():
        if g.get('dotless_alternate'):lines.append(f"    sub {name(cp)}' @ABOVE_ALL by {g['dotless_alternate']};")
    lines.append('  } DOTLESS;')
    narrow=[]
    for cp,g in r.items():
        if cp in (0x131,0x237):narrow.append(name(cp))
        elif isinstance(cp,int) and ud.normalize('NFD',chr(cp))[0] in 'ij':narrow.append(name(cp))
        elif isinstance(cp,str) and cp.endswith('.dotless'):narrow.append(name(cp))
    lines += ['  @NARROW_BASES = ['+' '.join(narrow)+'];','  lookup NARROW_MARKS {',
              '    lookupflag UseMarkFilteringSet @ABOVE_ALL;']
    for cp,g in r.items():
        if g.get('narrow_alternate'):
            for intervening in range(3):
                middle='@ABOVE_ALL '*intervening
                lines.append(f"    sub @NARROW_BASES {middle}{name(cp)}' by {g['narrow_alternate']};")
    lines.append('  } NARROW_MARKS;')
    below_all=[name(cp) for cp,g in r.items() if g.get('mark')=='below']
    narrow_below=narrow+[name(cp) for cp in r if isinstance(cp,int)
                         and ud.normalize('NFD',chr(cp))[0]=='l']
    lines.append('  @NARROW_BELOW_BASES = ['+' '.join(narrow_below)+'];')
    lines += ['  @BELOW_ALL = ['+' '.join(below_all)+'];',
              '  lookup NARROW_BELOW_MARKS {',
              '    lookupflag UseMarkFilteringSet @BELOW_ALL;']
    for cp,g in r.items():
        if g.get('narrow_below_alternate'):
            for intervening in range(3):
                middle='@BELOW_ALL '*intervening
                lines.append(f"    sub @NARROW_BELOW_BASES {middle}{name(cp)}' by {g['narrow_below_alternate']};")
    lines.append('  } NARROW_BELOW_MARKS;')
    if 'caron.side' in r:
        lines += ['  lookup SIDE_CARON {',
                  '    lookupflag UseMarkFilteringSet @ABOVE_ALL;',
                  "    sub [uni0064 uni006C uni0074 uni004C] uni030C' by caron.side;",
                  '  } SIDE_CARON;']
    if 'cedilla.g' in r:
        lines += ['  lookup CEDILLA_FORMS {',
                  '    lookupflag UseMarkFilteringSet @BELOW_ALL;',
                  "    sub uni0067 uni0327' by cedilla.g;",
                  "    sub [uni0047 uni004B uni006B uni004C uni006C uni004E uni006E uni0052 uni0072] uni0327' by cedilla.comma;",
                  '  } CEDILLA_FORMS;']
    lines += ['} ccmp;','feature mark {']
    for kind,cps in groups.items():
        if not cps:continue
        for cp,g in r.items():
            if g.get('mark') or g['width']==0 or not g.get('bounds'):continue
            anchor=(g.get('top') or (320,755)) if kind=='above' else (g.get('tone') or g.get('top') or (320,755)) if kind=='tone' else (g.get('bottom') or (320,-45)) if kind=='below' else (g.get('right') or (510,510)) if kind=='right' else (g.get('ogonek') or g.get('bottom') or (320,-45)) if kind=='ogonek' else (g.get('dotbelow') or g.get('bottom') or (320,-45)) if kind=='dotbelow' else (g.get('overlay') or (320,260))
            lines.append(f'  pos base {name(cp)} <anchor {round(anchor[0])} {round(anchor[1])}> mark @MC_{kind};')
    lines += ['} mark;','feature mkmk {']
    for kind in ('above','below'):
        if not groups[kind]:continue
        targets=groups[kind]+(groups['ogonek']+groups['dotbelow'] if kind=='below' else groups['tone'])
        lines += [f'  @STACK_SET_{kind} = ['+' '.join(map(name,targets))+'];',f'  lookup STACK_{kind} {{',f'    lookupflag UseMarkFilteringSet @STACK_SET_{kind};']
        for cp in targets:
            g=r[cp];a=g.get('top' if kind=='above' else 'bottom') or (0,175 if kind=='above' else -175)
            lines.append(f'    pos mark {name(cp)} <anchor {round(a[0])} {round(a[1])}> mark @MC_{kind};')
            if kind=='above' and groups['tone']:
                tone=g.get('stack_right') or a
                lines.append(f'    pos mark {name(cp)} <anchor {round(tone[0])} {round(tone[1])}> mark @MC_tone;')
            if kind=='below' and groups['dotbelow']:
                lines.append(f'    pos mark {name(cp)} <anchor {round(a[0])} {round(a[1])}> mark @MC_dotbelow;')
        lines.append(f'  }} STACK_{kind};')
    lines += ['} mkmk;']
    return '\n'.join(lines)+'\n'+(spacing.feature_code(r,name) if family=='sans' else '')

