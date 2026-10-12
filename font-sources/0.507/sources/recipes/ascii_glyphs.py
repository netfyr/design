"""Original hand-authored Latin control alphabet and everyday punctuation.

The coordinates below are authored for this project. Proportional fitting is
applied after outline resolution; these skeletons keep a common design origin
without imposing a common ink width. Endings and crossbars receive deliberate
optical corrections.
"""
from math import hypot
from model import glyph,stroke,fill,rect,ellipse,component
from refined_glyphs import d_ops, y_recipe, s_ops, a_ops, b_ops, r_recipe, p_ops, q_ops, g_ops, w_ops, W_ops

def build(reg,weight):
    w=weight;h=w*.45;t=700-h;b=h;xt=520-h
    def add(c,ops,top=None,bottom=None,note=''):
        return glyph(reg,c,ops,top=top,bottom=bottom,note=note)
    def s(d,k=1,**kw):return stroke(d,k,**kw)
    def flatdiag(x0,y0,x1,y1,k=1):
        # Original diagonal strip, cut on horizontal alignment lines. Normal
        # width uses the same 0.9 vertical optical correction as the stroker.
        # An ordinary angled butt cap would leak beyond those lines.
        half=w*k*.5*hypot(x1-x0,(y1-y0)/.9)/abs((y1-y0)/.9)
        return fill(f'M{x0-half} {y0}H{x0+half}L{x1+half} {y1}H{x1-half}Z')
    def cap(c,ops):return add(c,ops,top=(320,755),bottom=(320,-45))
    def lower(c,ops,top=None,bottom=None):return add(c,ops,top=top or (320,575),bottom=bottom or (320,-45))

    glyph(reg,'.notdef',[s('M90 -30V730H550V-30Z',.8),s('M135 20L505 680',.6),s('M135 680L505 20',.6)],note='Visible missing-glyph frame, not the replacement character.')
    add(' ',[],note='Ordinary text space; proportional advance assigned during fitting.')

    # Capitals. A/V/W/X/Y use deliberately cut planar endings; S is an
    # independently drawn continuous curve rather than joined semicircles.
    lo=245-h;hi=245+h
    inner=700-w*1.9
    cap('A',[fill(f'M76 0L{320-w*.53} 700H{320+w*.53}L564 0H{564-w*1.1}L{320+(inner-lo)*.28} {lo}H{320-(inner-lo)*.28}L{76+w*1.1} 0Z M{320-(inner-hi)*.28} {hi}H{320+(inner-hi)*.28}L320 {inner}Z')])
    cap('B',[s('M116 0V700'),s(f'M116 {t}H323C449 {t} 514 612 514 532C514 438 450 376 321 376H116'),s(f'M116 376H330C466 376 536 308 536 198C536 92 457 {b} 326 {b}H116')])
    cap('C',[s(f'M520 611C476 656 414 {t+8} 321 {t+8}C181 {t+8} 107 547 107 350C107 153 181 {b-8} 321 {b-8}C414 {b-8} 480 49 521 95')])
    cap('D',[s(f'M116 {b}V{t}H299C461 {t} 532 568 532 350C532 132 461 {b} 299 {b}Z')])
    cap('E',[s(f'M539 {t}H116V{b}H539'),s('M116 357H465')])
    cap('F',[s(f'M116 0V{t}H539'),s('M116 374H462')])
    cap('G',[s(f'M520 611C474 658 413 {t+8} 321 {t+8}C180 {t+8} 107 548 107 350C107 153 181 {b-8} 321 {b-8}C417 {b-8} 482 69 526 124V321H351')])
    cap('H',[s('M116 0V700'),s('M524 0V700'),s('M116 350H524')])
    cap('I',[s(f'M215 {t}H425'),s(f'M320 {t}V{b}'),s(f'M215 {b}H425')])
    cap('J',[s(f'M160 {t}H526'),s(f'M446 {t}V186C446 76 393 {b-7} 285 {b-7}C190 {b-7} 127 84 114 168')])
    cap('K',[s('M116 0V700'),flatdiag(148,312,531,700,.96),flatdiag(286,466,539,0,.96)])
    cap('L',[s(f'M116 700V{b}H541')])
    cap('M',[s(f'M40 0V{t}L320 340L600 {t}V0',.98)])
    cap('N',[s(f'M116 0V{t}L524 {b}V700',.98)])
    cap('O',[ellipse(320,350,210,350+10-h,True)])
    cap('P',[s('M116 0V700'),s(f'M116 {t}H325C462 {t} 527 608 527 507C527 405 462 342 325 342H116')])
    cap('Q',[component('O'),s('M356 161L552 -32',.88)])
    cap('R',[component('P'),flatdiag(319,342,539,0,.96)])
    cap('S',[s(f'M519 609C472 660 411 {t+8} 316 {t+8}C188 {t+8} 115 612 115 520C115 437 188 406 316 368C450 328 530 292 530 191C530 86 445 {b-8} 320 {b-8}C224 {b-8} 151 53 106 122')])
    cap('T',[s(f'M85 {t}H555'),s(f'M320 {t}V0')])
    cap('U',[s(f'M116 700V190C116 78 184 {b-7} 320 {b-7}C456 {b-7} 524 78 524 190V700')])
    cap('V',[fill(f'M73 700H{73+w*1.1}L320 {w*1.5}L{567-w*1.1} 700H567L{320+w*.52} -5H{320-w*.52}Z')])
    cap('W',W_ops(w))
    k=w*.6
    cap('X',[fill(f'M83 700H{83+w*1.25}L557 0H{557-w*1.25}Z'),fill(f'M557 700H{557-w*1.25}L83 0H{83+w*1.25}Z')])
    cap('Y',[fill(f'M74 700H{74+w*1.22}L320 399L{566-w*1.22} 700H566L{320+w/2} 335V0H{320-w/2}V335Z')])
    cap('Z',[fill(f'M95 700H545V{700-w*.75}L{95+w*1.15} {w*.9}H545V0H95V{w*.75}L{545-w*1.15} {700-w*.9}H95Z')])

    # Lowercase. A double-storey a balances the single-storey descending g.
    lower('a',a_ops(w))
    lower('b',b_ops(w),top=(320,775))
    lower('c',[s(f'M510 438C463 478 416 {xt+8} 320 {xt+8}C178 {xt+8} 111 410 111 260C111 110 178 {b-8} 320 {b-8}C416 {b-8} 468 66 512 82')])
    lower('d',d_ops(w),top=(320,775))
    lower('e',[s(f'M112 265H526C526 414 449 {xt+8} 320 {xt+8}C177 {xt+8} 110 410 110 260C110 108 181 {b-8} 321 {b-8}C414 {b-8} 474 63 516 106')])
    lower('f',[s(f'M284 0V556C284 659 330 {720-h} 407 {720-h}H434'),s(f'M178 {xt}H416')],top=(350,775))
    lower('g',g_ops(w),bottom=(320,-270))
    shoulder=f'M116 338C116 444 197 {xt+8} 321 {xt+8}C445 {xt+8} 524 426 524 319V0'
    lower('h',[s('M116 0V720'),s(shoulder)],top=(320,775))
    lower('i',[component(0x0131),ellipse(320,658,w*.53)],top=(320,740))
    lower('j',[component(0x0237),ellipse(320,658,w*.53)],top=(320,740),bottom=(265,-270))
    lower('k',[s('M124 0V720'),flatdiag(156,193,506,520,.96),flatdiag(300,338,531,0,.96)],top=(320,775))
    lower('l',[s(f'M280 720V96C280 46 311 {b} 374 {b}H390')],top=(280,775))
    lower('m',[s('M0 0V520'),s(f'M0 337C0 443 64 {xt+7} 160 {xt+7}C256 {xt+7} 320 443 320 335V0'),s(f'M320 337C320 443 384 {xt+7} 480 {xt+7}C576 {xt+7} 640 443 640 335V0')])
    lower('n',[s('M116 0V520'),s(shoulder)])
    lower('o',[ellipse(320,260,206,260+10-h,True)])
    lower('p',p_ops(w),bottom=(320,-270))
    lower('q',q_ops(w),bottom=(470,-270))
    lower('r',r_recipe(w))
    lower('s',s_ops(w),top=(312,575),bottom=(315,-45))
    lower('t',[s(f'M286 656V132C286 62 321 {b} 378 {b}H427'),s(f'M175 {xt}H431')],top=(300,710))
    lower('u',[s(f'M116 520V170C116 68 194 {b-8} 310 {b-8}C433 {b-8} 524 110 524 211'),s('M524 520V0')])
    lower('v',[fill(f'M79 520H{79+w*1.1}L320 {w*1.5}L{561-w*1.1} 520H561L{320+w*.51} -5H{320-w*.51}Z')])
    lower('w',w_ops(w))
    lower('x',[fill(f'M86 520H{86+w*1.25}L554 0H{554-w*1.25}Z'),fill(f'M554 520H{554-w*1.25}L86 0H{86+w*1.25}Z')])
    lower('y',y_recipe(w),bottom=(240,-270))
    lower('z',[fill(f'M102 520H538V{520-w*.72}L{102+w*1.15} {w*.9}H538V0H102V{w*.72}L{538-w*1.15} {520-w*.9}H102Z')])

    # Figures sit at the capital height, with separate zero construction.
    add('0',[ellipse(320,350,191,350+9-h,True),ellipse(320,350,w*.43)],top=(320,755),bottom=(320,-45),note='Dotted zero, narrower than capital O.')
    cap('1',[s(f'M179 550L333 {700-h}V{b}'),s(f'M155 {b}H504')])
    cap('2',[s(f'M121 526C127 624 203 {t+8} 325 {t+8}C445 {t+8} 521 611 521 513C521 430 457 374 374 307L113 {b}H539')])
    cap('3',[s(f'M115 605C161 659 233 {t+8} 327 {t+8}C445 {t+8} 514 614 514 526C514 437 447 373 326 373H261'),s(f'M326 373C459 373 529 306 529 198C529 89 447 {b-8} 322 {b-8}C217 {b-8} 148 49 102 119')])
    cap('4',[s('M425 0V700'),flatdiag(425,700,97,233,.94),s('M97 233H562')])
    cap('5',[s(f'M524 {t}H164L146 372C199 408 253 423 324 423C455 423 527 349 527 222C527 99 446 {b-8} 319 {b-8}C225 {b-8} 153 53 108 116')])
    cap('6',[s(f'M489 604C446 657 389 {t+8} 319 {t+8}C180 {t+8} 111 540 111 319C111 117 175 {b-8} 321 {b-8}C450 {b-8} 527 105 527 234C527 356 451 422 329 422C238 422 161 380 114 312')])
    cap('7',[fill(f'M91 700H578V{700-w*.9}L{239+w*.575} 0H{239-w*.575}L{578-w*1.15} {700-w*.9}H91Z')])
    cap('8',[ellipse(320,529,185,171-h,True),ellipse(320,189,208,197-h,True)])
    cap('9',[component('6',sx=-1,sy=-1,dx=640,dy=700)])

    # Punctuation retains its own scale and receives proportional sidebearings.
    add('!',[rect(320-w/2,187,w,513),ellipse(320,w*.58,w*.58)])
    add('"',[s('M243 700V531',.88),s('M397 700V531',.88)])
    add('#',[s('M250 730L134 -30',.85),s('M495 730L379 -30',.85),s('M101 453H565',.85),s('M75 240H539',.85)])
    add('$',[component('S'),s('M320 -80V780',.67)])
    add('%',[ellipse(196,537,84,122,True,.78),ellipse(444,163,84,122,True,.78),s('M119 -8L521 708',.82)])
    add('&',[s(f'M554 {b}L249 409C186 479 145 518 145 575C145 637 204 {t+8} 284 {t+8}C374 {t+8} 433 631 433 562C433 490 378 449 283 384C175 310 110 245 110 163C110 77 191 {b-8} 297 {b-8}C429 {b-8} 518 119 537 308',.94)])
    add("'",[s('M320 700V531',.88)])
    add('(',[s('M439 767C279 602 279 95 439 -70',.88)])
    add(')',[component('(',sx=-1,dx=640)])
    add('*',[s('M320 670V320',.84),s('M164 581L476 408',.84),s('M164 408L476 581',.84)])
    add('+',[s('M115 300H525',.92),s('M320 95V505',.92)])
    add(',',[ellipse(319,w*.57,w*.57),s(f'M348 {w*.57-6}C346 -28 316 -80 264 -117',.68)])
    add('-',[s('M169 260H471',1.0)])
    add('.',[ellipse(320,w*.58,w*.58)])
    add('/',[s('M131 -45L509 745',.9)])
    add(':',[ellipse(320,126,w*.6),ellipse(320,441,w*.6)])
    add(';',[ellipse(320,441,w*.6),component(',')])
    add('<',[s('M502 542L138 300L502 58',.9)])
    add('=',[s('M113 411H527',.9),s('M113 189H527',.9)])
    add('>',[component('<',sx=-1,dx=640)])
    add('?', [s(f'M128 549C143 634 210 {t+8} 321 {t+8}C439 {t+8} 515 613 515 518C515 436 459 394 388 351C340 321 320 279 320 193'),ellipse(320,w*.58,w*.58)])
    add('@',[s('M491 112C444 60 388 33 313 33C153 33 79 146 79 349C79 555 160 671 320 671C477 671 559 555 559 370C559 263 537 198 494 198C453 198 439 230 439 298V493',.72),ellipse(319,351,113,149,True,.76)])
    add('[',[s('M439 764H220V-67H439',.88)])
    add('\\',[component('/',sx=-1,dx=640)])
    add(']',[component('[',sx=-1,dx=640)])
    add('^',[s('M136 455L320 655L504 455',.88)])
    add('_',[rect(60,-153,520,w*.9)])
    add('`',[s('M249 736L360 604',.9)])
    add('{',[s('M470 764H412C312 764 292 711 292 616V437C292 370 266 348 185 348C266 348 292 326 292 259V80C292 -15 312 -68 412 -68H470',.87)])
    add('|',[rect(320-w*.45,-125,w*.9,910)])
    add('}',[component('{',sx=-1,dx=640)])
    add('~',[s('M117 273C239 443 393 161 523 331',.87)])

    assert all(cp in reg for cp in range(0x20,0x7F))
