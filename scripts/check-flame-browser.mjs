import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';

const session = `netfyr-flame-regression-${process.pid}`;
function browser(args, input) {
  const response = JSON.parse(execFileSync('agent-browser', ['--session', session, '--json', ...args], {
    input, encoding: 'utf8', timeout: 30000,
  }));
  assert.equal(response.success, true, response.error);
  return response.data;
}

const url = new URL(process.argv[2] || 'http://localhost:4173');
url.hash = 'brand';
try {
  browser(['open', url.href]);
  browser(['set', 'media', 'light']);
  browser(['wait', '--fn', 'document.querySelector(".brand .flame-original") !== null']);
  const result = browser(['eval', '--stdin'], `
    (async () => {
      const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
      await document.fonts.ready;
      const marks = [...document.querySelectorAll('.mark-downloads > figure')];
      const expectedColors = new Map();
      for (const mark of marks) {
        const download = mark.querySelector('a[download][href$=".svg"]');
        const response = await fetch(download.href);
        if (!response.ok) throw new Error('Flame download failed: ' + download.href);
        const artwork = new DOMParser().parseFromString(await response.text(), 'image/svg+xml');
        const sample = document.createElement('span');
        sample.style.color = artwork.querySelector('path').getAttribute('fill');
        document.body.append(sample);
        expectedColors.set(mark, getComputedStyle(sample).color);
        sample.remove();
      }
      const targets = [...document.querySelectorAll('.brand, .mark-tile, .logo-example, .mark-downloads > figure')];
      const failures = [], samples = [];
      const layoutProperties = ['display', 'position', 'width', 'height', 'boxSizing', 'padding', 'margin', 'border', 'flexShrink', 'alignSelf'];
      function layout(node) {
        const style = getComputedStyle(node), box = node.getBoundingClientRect();
        return JSON.stringify({ box: [box.x, box.y, box.width, box.height],
          styles: layoutProperties.map(property => style[property]) });
      }
      for (const [index, target] of targets.entries()) {
        const svg = target.querySelector('.flame-svg'), original = svg?.querySelector('.flame-original');
        if (!original) { failures.push(index + ':missing-animation'); continue; }
        const baseline = [target, svg].map(layout);
        const attributes = original.outerHTML;
        const display = getComputedStyle(original).display;
        const transform = getComputedStyle(original).transform;
        const wordmark = svg.classList.contains('flame-lockup') ? svg.querySelector(':scope > path') : null;
        const wordmarkLayout = wordmark && layout(wordmark);
        function check(state) {
          if ([target, svg].some((node, i) => layout(node) !== baseline[i])) failures.push(index + ':' + state + ':layout');
          if (original.outerHTML !== attributes || getComputedStyle(original).display !== display || getComputedStyle(original).transform !== transform) failures.push(index + ':' + state + ':artwork');
          if (original.getBBox().width === 0 || original.getBBox().height === 0) failures.push(index + ':' + state + ':collapsed');
          if (wordmark && layout(wordmark) !== wordmarkLayout) failures.push(index + ':' + state + ':wordmark');
          const color = expectedColors.get(target);
          if (color) {
            const originalColor = original.tagName === 'use' ? getComputedStyle(original).color : getComputedStyle(original).fill;
            if (originalColor !== color) failures.push(index + ':' + state + ':original-color');
            if ([...svg.querySelectorAll('.flame-blur path')].some(path => getComputedStyle(path).fill !== color)) {
              failures.push(index + ':' + state + ':animation-color');
            }
          }
          for (const blur of svg.querySelectorAll('feGaussianBlur')) {
            const strength = parseFloat(blur.getAttribute('stdDeviation'));
            if (!Number.isFinite(strength) || strength < 0 || strength > 2.4) failures.push(index + ':' + state + ':blur');
          }
        }
        target.dispatchEvent(new PointerEvent('pointerenter'));
        if (!svg.classList.contains('is-burning')) failures.push(index + ':hover:inactive');
        const nativeBounds = original.getBoundingClientRect();
        const animationBounds = svg.querySelector('.flame-blur').getBoundingClientRect();
        if (['x', 'y', 'width', 'height'].some(property => Math.abs(nativeBounds[property] - animationBounds[property]) > .01)) failures.push(index + ':entry:coordinate-offset');
        for (let frame = 0; frame < 24; frame++) { await new Promise(requestAnimationFrame); check('entry-' + frame); }
        samples.push([...svg.querySelectorAll('feGaussianBlur')].map(node => parseFloat(node.getAttribute('stdDeviation'))));
        target.dispatchEvent(new PointerEvent('pointerleave'));
        await wait(70); check('exit');
        target.dispatchEvent(new PointerEvent('pointerenter'));
        await wait(70); check('reentry');
        target.dispatchEvent(new PointerEvent('pointerleave'));
        await wait(300); check('rest');
        if (svg.classList.contains('is-burning')) failures.push(index + ':rest:active');
        target.focus({ preventScroll: true }); await wait(100); check('focus');
        if (!svg.classList.contains('is-burning')) failures.push(index + ':focus:inactive');
        target.blur(); target.dispatchEvent(new PointerEvent('pointerleave')); await wait(300); check('blur');
      }
      return { failures, targets: targets.length, marks: marks.map(mark => mark.querySelector('a[download][href$=".svg"]').getAttribute('href')),
        regionalBlur: samples.some(values => Math.max(...values) > Math.min(...values) + .1) };
    })()
  `).result;
  assert.ok(result.targets >= 5, 'Flame examples did not mount');
  assert.deepEqual(result.marks.sort(), ['black', 'orange', 'white'].map(color => 'assets/netfyr-mark-' + color + '.svg'));
  assert.deepEqual(result.failures, []);
  assert.equal(result.regionalBlur, true, 'Blur must respond independently by region');
  browser(['set', 'media', 'light', 'reduced-motion']);
  const reduced = browser(['eval', '--stdin'], `
    (async () => {
      for (const target of document.querySelectorAll('.mark-downloads > figure')) {
        target.focus();
        target.dispatchEvent(new PointerEvent('pointerenter'));
        await new Promise(resolve => setTimeout(resolve, 100));
        if (document.querySelectorAll('.is-burning').length !== 0 ||
          [...document.querySelectorAll('feGaussianBlur')].some(node => parseFloat(node.getAttribute('stdDeviation')) !== 0)) return false;
        target.blur();
        target.dispatchEvent(new PointerEvent('pointerleave'));
      }
      return matchMedia('(prefers-reduced-motion: reduce)').matches;
    })()
  `).result;
  assert.equal(reduced, true, 'Reduced motion must keep the original mark sharp');
  console.log('Flame variants, colors, layout, artwork, wordmark, regional blur, hover, focus and reduced motion pass.');
} finally {
  browser(['close']);
}
