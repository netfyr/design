"""Export transparent logo variants from the approved SVG artwork."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--inkscape', default='inkscape')
args = parser.parse_args()

assets = Path(__file__).resolve().parents[1] / 'public' / 'assets'
namespace = 'http://www.w3.org/2000/svg'
ET.register_namespace('', namespace)
exported = []


def export_png(svg):
    png = svg.with_suffix('.png')
    subprocess.run([
        args.inkscape, str(svg), '--export-type=png', '--export-width=1024',
        '--export-background-opacity=0', f'--export-filename={png}',
    ], check=True, capture_output=True)
    exported.extend([svg, png])


for kind, source in [('logo', 'netfyr-logo-ink.svg'), ('mark', 'netfyr-mark-orange.svg')]:
    for name, color in [('black', '#000000'), ('white', '#FFFFFF')]:
        root = ET.parse(assets / source).getroot()
        for path in root.iter(f'{{{namespace}}}path'):
            path.set('fill', color)
        for tag in ('title', 'desc'):
            for child in root.findall(f'{{{namespace}}}{tag}'):
                root.remove(child)
        root.set('role', 'img')
        root.set('aria-labelledby', 'title desc')
        title = ET.Element(f'{{{namespace}}}title', id='title')
        title.text = f'netfyr {kind} in {name}'
        desc = ET.Element(f'{{{namespace}}}desc', id='desc')
        artwork = 'Flame with the outlined lowercase netfyr wordmark' if kind == 'logo' else 'Standalone netfyr flame'
        desc.text = f'{artwork} in {name} on a transparent background.'
        root.insert(0, title)
        root.insert(1, desc)
        if kind == 'mark':
            root.set('width', '128')
            root.set('height', '128')
        target = assets / f'netfyr-{kind}-{name}.svg'
        ET.indent(root, space='  ')
        target.write_text(ET.tostring(root, encoding='unicode') + '\n')
        export_png(target)

export_png(assets / 'netfyr-mark-orange.svg')
manifest_path = assets / 'netfyr-logo-assets.json'
manifest = json.loads(manifest_path.read_text())
manifest['files'].update({file.name: hashlib.sha256(file.read_bytes()).hexdigest() for file in exported})
manifest['files'] = dict(sorted(manifest['files'].items()))
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
print('Exported black and white logos and orange, black and white flame marks as transparent SVG and PNG assets.')
