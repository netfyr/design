"""Exact native curve clipping for authored outline corrections."""
import hashlib
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.basePen import BasePen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.svgLib.path import parse_path
from fontTools.misc.bezierTools import calcCubicParameters, calcQuadraticParameters, solveCubic, solveQuadratic

from curve_boolean import ENV
from outlines import path_recording

_CACHE = {}


def native_boolean(left, right, operation='intersection'):
    if operation not in ('intersection', 'difference'):
        raise ValueError('Unsupported curve operation')
    paths = []
    for outline in (left, right):
        pen = SVGPathPen(None, ntos=lambda number: format(number, '.10g'))
        outline.replay(pen)
        paths.append(pen.getCommands())
    key = hashlib.sha256((operation + '\0' + '\0'.join(paths)).encode()).hexdigest()
    if key not in _CACHE:
        with TemporaryDirectory(prefix='netfyr-clip-') as directory:
            folder = Path(directory)
            source, target = folder / 'in.svg', folder / 'out.svg'
            svg = ET.Element('svg', xmlns='http://www.w3.org/2000/svg',
                             viewBox='-1500 -1500 5000 5000')
            for name, drawing in zip(('left', 'right'), paths):
                ET.SubElement(svg, 'path', id=name, d=drawing,
                              style='fill-rule:nonzero')
            source.write_bytes(ET.tostring(svg))
            actions = ['select-by-id:left,right', 'path-' + operation,
                       'select-clear', 'export-plain-svg',
                       'export-filename:' + str(target), 'export-do']
            result = subprocess.run(['inkscape', str(source), '--actions=' + ';'.join(actions)],
                                    capture_output=True, text=True, env=ENV, timeout=150)
            if result.returncode or not target.exists():
                raise RuntimeError('Native curve clipping failed: ' + result.stderr[-2000:])
            drawings = [element.get('d', '') for element in ET.parse(target).getroot().iter()
                        if element.tag.endswith('path')]
            _CACHE[key] = drawings
    output = RecordingPen()
    for drawing in _CACHE[key]:
        if drawing:
            parse_path(drawing, output)
    return output


def clip_rectangle(outline, xmin, ymin, xmax, ymax):
    if xmax <= xmin or ymax <= ymin:
        raise ValueError('Clip rectangle must have positive area')
    rectangle = path_recording(f'M{xmin} {ymin}H{xmax}V{ymax}H{xmin}Z')
    return native_boolean(outline, rectangle)


def bounds_in_x_range(outline, xmin, xmax):
    """Bound actual Bezier segments within a vertical slab without flattening."""
    class SlabPen(BasePen):
        def __init__(self):
            super().__init__(None)
            self.points = []
            self.start = None

        def segment(self, coefficients):
            a, b, c, d = coefficients
            candidates = {0.0, 1.0}
            for edge in (xmin, xmax):
                for root in solveCubic(a[0], b[0], c[0], d[0] - edge):
                    for _ in range(8):
                        value = ((a[0] * root + b[0]) * root + c[0]) * root + d[0] - edge
                        derivative = (3 * a[0] * root + 2 * b[0]) * root + c[0]
                        if abs(derivative) < 1e-12:
                            break
                        root -= value / derivative
                    candidates.add(root)
            for dimension in (0, 1):
                candidates.update(solveQuadratic(3 * a[dimension], 2 * b[dimension], c[dimension]))
            for t in candidates:
                if -1e-8 <= t <= 1 + 1e-8:
                    t = min(1, max(0, t))
                    point = tuple(((a[k] * t + b[k]) * t + c[k]) * t + d[k] for k in (0, 1))
                    if xmin - 1e-6 <= point[0] <= xmax + 1e-6:
                        self.points.append(point)

        def _moveTo(self, point):
            self.start = point

        def _lineTo(self, point):
            old = self._getCurrentPoint()
            self.segment(((0, 0), (0, 0), tuple(point[k] - old[k] for k in (0, 1)), old))

        def _qCurveToOne(self, control, point):
            self.segment(((0, 0), *calcQuadraticParameters(self._getCurrentPoint(), control, point)))

        def _curveToOne(self, first, second, point):
            self.segment(calcCubicParameters(self._getCurrentPoint(), first, second, point))

        def _closePath(self):
            if self.start is not None and self._getCurrentPoint() != self.start:
                self._lineTo(self.start)

        def _endPath(self):
            pass

    if xmax < xmin:
        raise ValueError('Slab edges must be ordered')
    pen = SlabPen()
    outline.replay(pen)
    if not pen.points:
        return None
    return (min(point[0] for point in pen.points), min(point[1] for point in pen.points),
            max(point[0] for point in pen.points), max(point[1] for point in pen.points))
