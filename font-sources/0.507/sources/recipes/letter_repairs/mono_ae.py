"""U+00E6 Mono: centred D counter and regular e eye; no pointed right wedge."""
from .loop_contours import mono_pair

def draw(stem):return mono_pair(stem,'ae')
def apply(r,stem,family,italic):
    if family=='mono':r[0xE6]['ops']=draw(stem)
