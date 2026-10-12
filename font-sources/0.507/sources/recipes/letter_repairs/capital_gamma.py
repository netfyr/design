"""U+0194: preserved oval loop, with longer leg-to-loop transitions."""
from .gamma_transition import gamma as looped_gamma

def apply(r,stem,family,italic):
    r[0x194]["ops"]=looped_gamma(stem,665,245,-8,305,105,515)
