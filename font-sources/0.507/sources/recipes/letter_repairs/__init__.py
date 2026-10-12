"""One authored repair module per reported base character.

These are design recipes, not autonomous reviewers. Parallel validation is
recorded separately; no independent subagent execution is claimed.
"""
from . import capital_ae,capital_gamma,small_gamma,double_p,circled_equals,mono_ae,mono_oe

def apply(r,stem,family,italic):
    if stem<=90:return  # preserve the accepted Light–SemiBold construction
    for module in (capital_ae,capital_gamma,small_gamma,double_p,circled_equals,mono_ae,mono_oe):
        module.apply(r,stem,family,italic)
