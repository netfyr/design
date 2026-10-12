"""U+0153 Mono: paired bowl and counter proportions drawn within one cell."""
from .loop_contours import mono_pair

def draw(stem):return mono_pair(stem,'oe')
def apply(r,stem,family,italic):
    if family=='mono':r[0x153]['ops']=draw(stem)
