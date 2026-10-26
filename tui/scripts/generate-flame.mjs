#!/usr/bin/env node
// Source geometry and animation: netfyr design library. See tui/assets/flame-NOTICE.txt.
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const project = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const check = args.includes('--check');
const paths = args.filter(arg => arg !== '--check');
if (paths.length > 1 || paths.some(arg => arg.startsWith('--'))) {
  throw new Error('Usage: node tui/scripts/generate-flame.mjs [netfyr-design directory] [--check]');
}
const design = resolve(paths[0] || resolve(project, '..'));
const sourcePaths = [
  'src/flame-shape.js',
  'src/flame.js',
  'src/styles.css',
  'public/assets/netfyr-mark-orange.svg',
];
const source = Object.fromEntries(await Promise.all(sourcePaths.map(async path =>
  [path, await readFile(resolve(design, path), 'utf8')])));
const { flameCurves, restFlameCurves } = await import(pathToFileURL(resolve(design, sourcePaths[0])));
const animation = source['src/flame.js'];
const flicker = animation.match(/const flicker = \{[^}]+\};/)?.[0];
const frameFunction = animation.match(/function flameFrame\(phase, strength\) \{[\s\S]*?\n\}/)?.[0];
const scaleExpression = animation.match(/const scale = (\[[^;]+\]);/)?.[1];
if (!flicker || !frameFunction || !scaleExpression) {
  throw new Error('Animation source changed; review the source adapter before regenerating.');
}
// Compile the repository's own frame equation, as importing its DOM module needs a browser.
const { flameFrame, duration } = new Function('flameCurves', 'restFlameCurves',
  `${flicker}\n${frameFunction}\nreturn { flameFrame, duration: flicker.duration };`)(flameCurves, restFlameCurves);
const scaleAt = new Function('phase', 'strength', `return ${scaleExpression
  .replaceAll('this.phase', 'phase').replaceAll('this.strength', 'strength')};`);
if (!source['src/styles.css'].includes('transform-origin:50% 90%')) {
  throw new Error('Flame transform origin changed; review the source adapter.');
}

const width = 24, height = 12, frameCount = 12, samples = 8;
const viewport = { x: -16, y: -18, width: 160, height: 160 };
const origin = [64, 2 + 128 * .9];
const ramp = ' .:+*#@';

function contours(curves, scale) {
  const polygons = [];
  let polygon, from;
  const transform = point => point.map((value, axis) => origin[axis] + (value - origin[axis]) * scale[axis]);
  for (const [command, ...coordinates] of curves) {
    if (command === 'M') {
      from = coordinates;
      polygon = [transform(from)];
      polygons.push(polygon);
    } else if (command === 'C') {
      for (let step = 1; step <= 32; step++) {
        const t = step / 32, u = 1 - t;
        polygon.push(transform([0, 1].map(axis => u ** 3 * from[axis]
          + 3 * u ** 2 * t * coordinates[axis]
          + 3 * u * t ** 2 * coordinates[axis + 2]
          + t ** 3 * coordinates[axis + 4])));
      }
      from = coordinates.slice(-2);
    } else if (command !== 'Z') {
      throw new Error(`Unsupported curve command: ${command}`);
    }
  }
  return polygons;
}

function inside(polygons, x, y) {
  let filled = false;
  for (const polygon of polygons) {
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const [ax, ay] = polygon[i], [bx, by] = polygon[j];
      if ((ay > y) !== (by > y) && x < (bx - ax) * (y - ay) / (by - ay) + ax) {
        filled = !filled;
      }
    }
  }
  return filled;
}

function raster(curves, scale = [1, 1]) {
  const polygons = contours(curves, scale);
  return Array.from({ length: height }, (_, row) => Array.from({ length: width }, (_, column) => {
    let coverage = 0;
    for (let y = 0; y < samples; y++) for (let x = 0; x < samples; x++) {
      coverage += inside(polygons,
        viewport.x + (column + (x + .5) / samples) * viewport.width / width,
        viewport.y + (row + (y + .5) / samples) * viewport.height / height);
    }
    return ramp[Math.round(coverage / samples ** 2 * (ramp.length - 1))];
  }).join('')).join('\n');
}

const frames = [raster(restFlameCurves)];
for (let frame = 0; frame < frameCount; frame++) {
  const phase = frame * Math.PI * 2 / frameCount;
  frames.push(raster(flameFrame(phase, 1), scaleAt(phase, 1)));
}
const provenance = {
  source: 'netfyr-design',
  files: Object.fromEntries(sourcePaths.map(path => [path,
    { sha256: createHash('sha256').update(source[path]).digest('hex') }])),
  width, height, frameCount, durationSeconds: duration,
  viewport, origin, samplesPerAxis: samples, asciiRamp: ramp,
  notes: 'First frame is the exact master at rest. Remaining frames sample one full-strength animation cycle. Even/odd fill preserves the hollow interior. Terminal cells assume a 1:2 width-to-height ratio. The viewport preserves at least 16 SVG units around the resting mark. SVG motion blur is omitted.',
};
for (const [name, contents] of [
  ['flame.txt', `${frames.join('\n\f\n')}\n`],
  ['flame-provenance.json', `${JSON.stringify(provenance, null, 2)}\n`],
]) {
  const path = resolve(project, 'assets', name);
  if (check) {
    if (await readFile(path, 'utf8') !== contents) throw new Error(`${name} is out of date`);
  } else {
    await mkdir(dirname(path), { recursive: true });
    await writeFile(path, contents);
  }
}
console.log(check ? 'Flame artwork matches its source.' : 'Generated master and 12 animation frames.');
