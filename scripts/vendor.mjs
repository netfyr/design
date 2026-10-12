import { mkdir, readFile, writeFile, copyFile } from 'node:fs/promises';

const root = new URL('../', import.meta.url);
const output = new URL('public/vendor/', root);
await mkdir(output, { recursive: true });
for (const [source, target] of [
  ['svg.js/dist/svg.esm.js', 'svg.js'],
  ['svg.filter.js/dist/svg.filter.mjs', 'svg-filter.js'],
]) {
  const code = await readFile(new URL(`node_modules/@svgdotjs/${source}`, root), 'utf8');
  await writeFile(new URL(target, output), code
    .replace('"@svgdotjs/svg.js"', '"./svg.js"')
    .replace(/\/\/# sourceMappingURL=.*$/m, ''));
}
await copyFile(new URL('node_modules/@svgdotjs/svg.js/LICENSE.txt', root), new URL('svg-LICENSE.txt', output));
await copyFile(new URL('node_modules/@svgdotjs/svg.filter.js/LICENSE', root), new URL('svg-filter-LICENSE.txt', output));
