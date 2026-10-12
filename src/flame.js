import { flameCurves, restFlameCurves } from './flame-shape.js';
import { motionBlur } from './flame-blur.js';

const namespace = 'http://www.w3.org/2000/svg';
const flicker = { duration: 1.15, sway: 7, stretch: 6 };

function flameFrame(phase, strength) {
  return flameCurves.map(([command, ...coordinates], segment) => {
    const result = [];
    for (let index = 0; index < coordinates.length; index += 2) {
      const rest = restFlameCurves[segment];
      const x = rest[index + 1] + (coordinates[index] - rest[index + 1]) * strength;
      const y = rest[index + 2] + (coordinates[index + 1] - rest[index + 2]) * strength;
      const height = Math.max(0, (90 - y) / 90);
      const movement = height ** 1.8 * strength;
      const wave = phase + y / 28 + x / 80;
      result.push(x + movement * (Math.sin(wave) * flicker.sway));
      result.push(y - movement * Math.cos(phase + x / 35) * flicker.stretch);
    }
    return [command, ...result];
  });
}

const pathData = curves => curves.map(([command, ...values]) => command + values.map(value => value.toFixed(3)).join(' ')).join(' ');

function element(name, attributes = {}) {
  const node = document.createElementNS(namespace, name);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  return node;
}

function flame(label, width = 32, height = width) {
  const svg = element('svg', { class: 'flame-svg', viewBox: '0 2 128 128', width, height });
  if (label) { svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', label); }
  else svg.setAttribute('aria-hidden', 'true');
  const body = element('g', { class: 'flame-body' });
  body.append(element('use', { href: '#netfyr-flame' }));
  svg.append(body);
  return svg;
}

export async function mountFlames() {
  for (const image of document.querySelectorAll('img[src="assets/netfyr-mark-orange.svg"]')) {
    const svg = flame(image.alt, image.width, image.height);
    if (image.className) svg.classList.add(...image.className.split(/\s+/));
    image.replaceWith(svg);
  }
  for (const image of document.querySelectorAll('.logo-example img, .brand img[data-wordmark]')) {
    try {
      const response = await fetch(image.getAttribute('src'));
      if (!response.ok) continue;
      const artwork = new DOMParser().parseFromString(await response.text(), 'image/svg+xml');
      const paths = artwork.querySelectorAll('path');
      if (paths.length !== 2) continue;
      const root = artwork.documentElement;
      const svg = flame(image.alt, Number(root.getAttribute('width')), Number(root.getAttribute('height')));
      svg.setAttribute('viewBox', root.getAttribute('viewBox'));
      svg.classList.add('flame-lockup');
      svg.querySelector('.flame-body').replaceChildren(document.importNode(paths[0], true));
      const wordmark = document.importNode(paths[1], true);
      if (image.hasAttribute('data-wordmark')) wordmark.setAttribute('fill', 'var(--text)');
      svg.append(wordmark);
      image.replaceWith(svg);
    } catch {}
  }
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const controllers = [];
  for (const [index, svg] of [...document.querySelectorAll('.flame-svg:has(.flame-body)')].entries()) {
    const body = svg.querySelector('.flame-body');
    const original = body.firstElementChild;
    original.classList.add('flame-original');
    const motion = element('path', { class: 'flame-motion-path', fill: svg.closest('.nav-link') ? 'currentColor' : '#FF7A1A', 'fill-rule': 'evenodd' });
    if (original.hasAttribute('transform')) motion.setAttribute('transform', original.getAttribute('transform'));
    else if (original.tagName === 'use' && original.getAttribute('href') === '#netfyr-flame') {
      const [, y] = document.querySelector('#netfyr-flame').getAttribute('viewBox').split(/\s+/).map(Number);
      motion.setAttribute('transform', `translate(0 ${-y})`);
    }
    body.append(motion);
    const blur = motionBlur(svg, body, motion);
    const target = svg.closest('.brand, .mark-tile, .logo-example') || svg;
    const controller = {
      svg,
      frame: 0,
      strength: 0,
      targetStrength: 0,
      phase: index * .3,
      tick(now) {
        const elapsed = Math.max(0, Math.min(now - this.lastTime, 64));
        this.lastTime = now;
        this.phase += elapsed * Math.PI * 2 / (flicker.duration * 1000);
        const progress = Math.max(0, Math.min((now - this.transitionStarted) / this.transitionDuration, 1));
        const ease = progress * progress * (3 - 2 * progress);
        this.strength = this.startStrength + (this.targetStrength - this.startStrength) * ease;
        const curves = flameFrame(this.phase, this.strength);
        const data = pathData(curves);
        const scale = [1 + Math.sin(this.phase) * .012 * this.strength, 1 + Math.sin(this.phase + .5) * .024 * this.strength];
        motion.setAttribute('d', data);
        blur.update(curves, data, elapsed, scale);
        body.style.transform = `scale(${scale.join(',')})`;
        if (progress === 1 && this.targetStrength === 0) {
          this.reset();
          return;
        }
        this.frame = requestAnimationFrame(time => this.tick(time));
      },
      transition(strength) {
        if (this.targetStrength === strength) return;
        this.targetStrength = strength;
        this.startStrength = this.strength;
        this.transitionStarted = performance.now();
        this.transitionDuration = strength ? 320 : 240;
        if (!this.frame) {
          this.lastTime = this.transitionStarted;
          const curves = flameFrame(this.phase, this.strength);
          const data = pathData(curves);
          motion.setAttribute('d', data);
          blur.update(curves, data, 16.667, [1, 1]);
          svg.classList.add('is-burning');
          this.frame = requestAnimationFrame(time => this.tick(time));
        }
      },
      start() {
        if (reducedMotion.matches) return;
        this.transition(1);
      },
      stop() {
        this.transition(0);
      },
      reset() {
        cancelAnimationFrame(this.frame);
        this.frame = 0;
        this.strength = 0;
        this.targetStrength = 0;
        blur.reset();
        body.style.removeProperty('transform');
        svg.classList.remove('is-burning');
      },
    };
    target.addEventListener('pointerenter', () => controller.start());
    target.addEventListener('pointerleave', () => { if (!target.matches(':focus-within')) controller.stop(); });
    target.addEventListener('focusin', () => controller.start());
    target.addEventListener('focusout', event => {
      if (!target.contains(event.relatedTarget) && !target.matches(':hover')) controller.stop();
    });
    if (target.classList.contains('mark-tile') || target.classList.contains('logo-example')) target.tabIndex = 0;
    controllers.push(controller);
    if (target.matches(':hover, :focus-within')) controller.start();
  }
  reducedMotion.addEventListener('change', () => {
    if (reducedMotion.matches) for (const controller of controllers) controller.reset();
  });
}
