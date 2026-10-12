"""Original capital A optical correction, netfyr 0.506.

Scope: stem coordinates (90, 154], i.e. Bold, ExtraBold and Black.
The accepted SemiBold construction is the interpolation endpoint at 90.
This is a static glyph-specific design operation, not a variable-font claim.

The outside diagonal boundaries, 700-unit cap height, 488-unit source
footprint, family fitting, advances, anchors and italic transform are retained.
The lower inner legs are sloped, the crossbar lowered and relieved, and
curved counter sides relieve the congested apex. No reference outline is used.
"""
from math import isfinite
from model import fill


def parameters(stem: float) -> dict[str, float]:
    if not isfinite(stem) or not 90 <= stem <= 154:
        raise ValueError('capital A correction expects a stem in [90, 154]')
    t=(stem-90)/64
    # Authored Black endpoint; dimensions are not borrowed typeface metrics.
    low=204.5+(140-204.5)*t
    high=285.5+(256-285.5)*t
    foot_band=99+(139-99)*t
    foot_inner=76+foot_band
    original_lower_slope=((320-(529-204.5)*.28)-(76+99))/204.5
    lower_slope=original_lower_slope+(.17-original_lower_slope)*t
    lower_inner=foot_inner+lower_slope*low
    high_inner=251.82+(76+139+.17*256-251.82)*t
    counter_apex=529+(565-529)*t
    span=(counter_apex-high)/3
    # Deliberate taper at the apex; at 90 both sides are exactly linear.
    start_slope=.28+(.22-.28)*t
    end_slope=.28+(.12-.28)*t
    return dict(stem=stem,progress=t,bar_bottom=low,bar_top=high,
        bar_thickness=high-low,foot_band=foot_band,foot_inner=foot_inner,
        lower_slope=lower_slope,lower_inner=lower_inner,counter_left=high_inner,
        counter_apex=counter_apex,span=span,
        control1_x=high_inner+start_slope*span,
        control2_x=320-end_slope*span)


def capital_a_ops(stem: float) -> list[dict]:
    p=parameters(stem)
    low=p['bar_bottom'];high=p['bar_top'];base=p['foot_inner']
    inner=p['counter_left'];li=p['lower_inner'];tip=p['counter_apex']
    span=p['span'];c1=p['control1_x'];c2=p['control2_x']
    # Outer clockwise path, counter counterclockwise, in font coordinates.
    outside=(f'M76 0L{320-stem*.53} 700H{320+stem*.53}L564 0'
             f'H{640-base}L{640-li} {low}H{li}L{base} 0Z')
    counter=(f'M{inner} {high}H{640-inner}'
             f'C{640-c1} {high+span} {640-c2} {tip-span} 320 {tip}'
             f'C{c2} {tip-span} {c1} {high+span} {inner} {high}Z')
    return [fill(outside+' '+counter)]
