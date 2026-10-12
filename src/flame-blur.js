import { SVG } from './vendor/svg.js';
import './vendor/svg-filter.js';

const bounds = { x: -20, y: -20, width: 168, height: 168 };
const rows = [-20, 32, 58, 88, 148];

function mask(draw, axis, low, high) {
  const gradient = draw.gradient('linear', add => {
    const stops = [[-20, low === -20 ? 1 : 0], [low - 6, 0], [low + 6, 1],
      [high - 6, 1], [high + 6, 0], [148, high === 148 ? 1 : 0]];
    for (const [position, opacity] of stops) {
      if (position < -20 || position > 148) continue;
      if ((low === -20 && position <= low + 6) || (high === 148 && position >= high - 6)) {
        add.stop((position + 20) / 168, '#fff');
      } else add.stop((position + 20) / 168, opacity ? '#fff' : '#000');
    }
  }).from(0, 0).to(axis === 'x' ? 1 : 0, axis === 'y' ? 1 : 0);
  const result = draw.mask().attr({ maskUnits: 'userSpaceOnUse', ...bounds });
  result.rect(bounds.width, bounds.height).move(bounds.x, bounds.y).fill(gradient);
  return result;
}

function points(curves, scale, origin) {
  const result = [];
  let from;
  for (const [command, ...coordinates] of curves) {
    if (command === 'M') from = coordinates;
    if (command !== 'C') continue;
    for (let step = 1; step <= 6; step++) {
      const t = step / 6, u = 1 - t;
      const point = [0, 1].map(axis => u ** 3 * from[axis] + 3 * u ** 2 * t * coordinates[axis]
        + 3 * u * t ** 2 * coordinates[axis + 2] + t ** 3 * coordinates[axis + 4]);
      result.push(point.map((value, axis) => origin[axis] + (value - origin[axis]) * scale[axis]));
    }
    from = coordinates.slice(-2);
  }
  return result;
}

export function motionBlur(svg, body, motion) {
  const draw = SVG(svg);
  const origin = getComputedStyle(body).transformOrigin.split(' ').map(parseFloat);
  const group = SVG(body).group().addClass('flame-blur').css('isolation', 'isolate');
  const horizontal = [mask(draw, 'x', -20, 92), mask(draw, 'x', 92, 148)];
  const vertical = rows.slice(0, -1).map((low, index) => mask(draw, 'y', low, rows[index + 1]));
  const regions = vertical.flatMap((rowMask, row) => horizontal.map((columnMask, column) => {
    const layer = group.group().maskWith(columnMask).css('mix-blend-mode', 'plus-lighter');
    const path = layer.group().maskWith(rowMask).path().fill(motion.getAttribute('fill')).attr('fill-rule', 'evenodd');
    if (motion.hasAttribute('transform')) path.attr('transform', motion.getAttribute('transform'));
    let blur;
    path.filterWith(add => {
      add.attr({ filterUnits: 'userSpaceOnUse', ...bounds, 'color-interpolation-filters': 'sRGB' });
      blur = add.gaussianBlur(0);
    });
    return { row, column, path, blur, strength: 0 };
  }));
  let previous;
  return {
    update(curves, pathData, elapsed, scale) {
      const current = points(curves, scale, origin);
      const speeds = regions.map(() => ({ sum: 0, count: 0 }));
      if (previous) for (let index = 0; index < current.length; index++) {
        const [x, y] = current[index];
        const row = Math.min(3, Math.max(0, rows.findIndex((edge, i) => i > 0 && y < edge) - 1));
        const speed = Math.hypot(x - previous[index][0], y - previous[index][1]) * 16.667 / Math.max(elapsed, 1);
        const region = speeds[row * 2 + (x < 92 ? 0 : 1)];
        region.sum += speed ** 2;
        region.count++;
      }
      for (const [index, region] of regions.entries()) {
        const speed = speeds[index];
        const target = Math.min(2.4, Math.sqrt(speed.sum / Math.max(speed.count, 1)) * 1.6);
        region.strength += (target - region.strength) * (1 - Math.exp(-elapsed / 45));
        region.blur.update([region.strength]);
        region.path.plot(pathData);
      }
      previous = current;
    },
    reset() {
      previous = undefined;
      for (const region of regions) { region.strength = 0; region.blur.update([0]); }
    },
  };
}
