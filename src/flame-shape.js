const cartoonCurves = [
  ['M', 14, 76],
  ['C', 22, 56, 64, 30, 80, 8],
  ['C', 87, 1, 94, 6, 90, 18],
  ['C', 85, 40, 92, 53, 88, 62],
  ['C', 91, 58, 99, 50, 103, 48],
  ['C', 111, 43, 116, 48, 114, 58],
  ['C', 113, 65, 114, 69, 114, 76],
  ['C', 114, 104, 92, 126, 64, 126],
  ['C', 36, 126, 14, 104, 14, 76],
  ['Z'],
  ['M', 26, 76],
  ['C', 32, 64, 59, 43, 78, 26],
  ['C', 74, 43, 78, 61, 78, 76],
  ['C', 78, 82, 85, 85, 90, 80],
  ['C', 94, 76, 99, 70, 102, 66],
  ['C', 102, 70, 102, 73, 102, 76],
  ['C', 102, 97, 85, 114, 64, 114],
  ['C', 43, 114, 26, 97, 26, 76],
  ['Z'],
];

function line(from, to) {
  return ['C', ...from.map((value, index) => value + (to[index] - value) / 3),
    ...from.map((value, index) => value + (to[index] - value) * 2 / 3), ...to];
}

function arc(cx, cy, radius, start, end) {
  const tangent = 4 / 3 * Math.tan((end - start) / 4);
  return ['C',
    cx + radius * (Math.cos(start) - tangent * Math.sin(start)),
    cy + radius * (Math.sin(start) + tangent * Math.cos(start)),
    cx + radius * (Math.cos(end) + tangent * Math.sin(end)),
    cy + radius * (Math.sin(end) - tangent * Math.cos(end)),
    cx + radius * Math.cos(end), cy + radius * Math.sin(end)];
}

const radians = degrees => degrees * Math.PI / 180;
export const restFlameCurves = [
  ['M', 14, 76],
  arc(20, 76, 6, radians(180), radians(225)),
  line([15.75736, 71.75736], [79.75736, 7.75736]),
  arc(84, 12, 6, radians(-135), radians(-67.5)),
  arc(84, 12, 6, radians(-67.5), 0),
  line([90, 12], [90, 18]),
  line([90, 18], [90, 61.51472]),
  line([90, 61.51472], [103.75736, 47.75736]),
  arc(108, 52, 6, radians(-135), radians(-67.5)),
  arc(108, 52, 6, radians(-67.5), 0),
  line([114, 52], [114, 58]),
  line([114, 58], [114, 76]),
  arc(64, 76, 50, 0, Math.PI / 2),
  arc(64, 76, 50, Math.PI / 2, Math.PI),
  ['Z'],
  ['M', 26.07643, 78.40885],
  line([26.07643, 78.40885], [78, 26.48528]),
  line([78, 26.48528], [78, 76]),
  arc(84, 76, 6, Math.PI, radians(112.5)),
  arc(84, 76, 6, radians(112.5), radians(45)),
  line([88.24264, 80.24264], [102, 66.48528]),
  line([102, 66.48528], [102, 76]),
  arc(64, 76, 38, 0, Math.PI / 2),
  arc(64, 76, 38, Math.PI / 2, Math.atan2(2.40885, -37.92357)),
  ['Z'],
];

function split(from, curve, t) {
  const mix = (a, b) => a.map((value, index) => value + (b[index] - value) * t);
  const p1 = curve.slice(1, 3), p2 = curve.slice(3, 5), end = curve.slice(5);
  const a = mix(from, p1), b = mix(p1, p2), c = mix(p2, end);
  const d = mix(a, b), e = mix(b, c), point = mix(d, e);
  return [['C', ...a, ...d, ...point], ['C', ...e, ...c, ...end]];
}

const subdivisions = { 1: [.07], 2: [.45, .75], 5: [.45, .75], 13: [.5] };
let from;
export const flameCurves = cartoonCurves.flatMap((curve, index) => {
  const parts = [];
  let remaining = curve, previous = 0, start = from;
  for (const t of subdivisions[index] || []) {
    const [first, second] = split(start, remaining, (t - previous) / (1 - previous));
    parts.push(first);
    remaining = second;
    start = first.slice(-2);
    previous = t;
  }
  if (curve[0] !== 'Z') from = curve.slice(-2);
  return [...parts, remaining];
});
