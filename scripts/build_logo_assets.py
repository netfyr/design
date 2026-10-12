"""Export the horizontal netfyr logo with shaped, outlined lettering."""
import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen

parser = argparse.ArgumentParser()
parser.add_argument('--fonts', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--shaping-source', type=Path, required=True)
parser.add_argument('--inkscape', type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.shaping_source))
from shaping import Shaper

font_path = args.fonts / 'netfyrsans-Bold.ttf'
shaper = Shaper(font_path)
glyphs = shaper.tt.getGlyphSet()
outline = SVGPathPen(glyphs)
ink = BoundsPen(glyphs)
cursor = 0
for glyph in shaper.shape('netfyr'):
    glyphs[glyph['glyph']].draw(TransformPen(outline, (1, 0, 0, 1, cursor + glyph['x'], glyph['y'])))
    glyphs[glyph['glyph']].draw(TransformPen(ink, (1, 0, 0, 1, cursor + glyph['x'], glyph['y'])))
    cursor += glyph['advance']
wordmark = outline.getCommands()
n_bounds = BoundsPen(glyphs)
glyphs[shaper.cmap[ord('n')]].draw(n_bounds)
scale = (124 - 44) / (n_bounds.bounds[3] - ink.bounds[1])
baseline = 124 + ink.bounds[1] * scale
origin = 146 - ink.bounds[0] * scale
right = 146 + (ink.bounds[2] - ink.bounds[0]) * scale
width = math.ceil(right + 14)
flame = 'M90 12a6 6 0 0 0-10.24264-4.24264L15.75736 71.75736A6 6 0 0 0 14 76a50 50 0 0 0 100 0V52a6 6 0 0 0-10.24264-4.24264L90 61.51472ZM78 26.48528V76a6 6 0 0 0 10.24264 4.24264L102 66.48528V76A38 38 0 0 1 26.07643 78.40885Z'
args.output.mkdir(parents=True, exist_ok=True)
for variant, color in [('ink', '#211C19'), ('paper', '#F7F2EA')]:
    path = args.output / f'netfyr-logo-{variant}.svg'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 128" width="{width}" height="128" role="img" aria-labelledby="title desc">
  <title id="title">netfyr logo</title>
  <desc id="desc">Orange flame with the lowercase netfyr wordmark in {variant}. The netfyr sans Bold lettering is outlined.</desc>
  <path fill="#FF7A1A" transform="translate(0 -2)" d="{flame}"/>
  <path fill="{color}" transform="translate({origin:.6f} {baseline:.6f}) scale({scale:.9f} {-scale:.9f})" d="{escape(wordmark)}"/>
</svg>
'''
    path.write_text(svg)
    subprocess.run([str(args.inkscape.resolve()), str(path.resolve()), '--export-type=png', '--export-width=1024', '--export-filename=' + str(path.with_suffix('.png').resolve())], check=True, capture_output=True)
manifest = {'font': font_path.name, 'font_sha256': hashlib.sha256(font_path.read_bytes()).hexdigest(), 'wordmark': 'netfyr', 'weight': 700, 'width': width, 'height': 128, 'wordmark_scale': scale, 'wordmark_baseline': baseline, 'n_top': baseline - n_bounds.bounds[3] * scale, 'small_flame_tip_top': 44, 'wordmark_ink_bounds': [146, baseline - ink.bounds[3] * scale, right, 124], 'flame_to_wordmark_ink_gap': 32, 'minimum_clear_space': 16, 'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.output.glob('netfyr-logo-*')) if p.suffix in ('.svg', '.png')}}
(args.output / 'netfyr-logo-assets.json').write_text(json.dumps(manifest, indent=2) + '\n')
shaper.close()
print(json.dumps(manifest))
