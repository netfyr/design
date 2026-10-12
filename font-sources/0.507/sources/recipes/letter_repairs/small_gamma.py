"""U+0263: the lower-case gamma keeps its descender loop and own alignment.

Unicode IPA chart distinguishes this character from U+0264 ram's horns.
The derived U+02E0 modifier is explicitly checked, not mistaken for a base.
"""
from .capital_gamma import looped_gamma

def apply(r,stem,family,italic):r[0x263]['ops']=looped_gamma(stem,485,35,-220,320,105,535)
