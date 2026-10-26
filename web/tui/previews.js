const namespace = 'http://www.w3.org/2000/svg';

function element(name, attributes = {}) {
  const node = document.createElementNS(namespace, name);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  return node;
}

function mountPreview(host, preview, styles) {
  const svg = host.querySelector('svg');
  const button = host.querySelector('.gallery-tui-toolbar button');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const animated = preview.frames.length > 0;
  let playing = animated && !reduced.matches;
  let visible = false;
  let index = -1;
  let elapsed = 0;
  let previous;
  let request;
  svg.setAttribute('viewBox', `0 0 ${preview.columns * 10} ${preview.rows * 20}`);
  svg.setAttribute('width', preview.columns * 10);
  svg.setAttribute('height', preview.rows * 20);

  function paint(frame) {
    const group = element('g');
    for (const [x, y, styleIndex, text, width] of frame) {
      const style = styles[styleIndex];
      group.append(element('rect', {
        x: x * 10, y: y * 20, width: width * 10, height: 20, fill: style.bg,
      }));
      if (!text.trim()) continue;
      const leading = text.match(/^ */)[0].length;
      const trailing = text.match(/ *$/)[0].length;
      const run = element('text', {
        x: (x + leading) * 10, y: y * 20 + 16, fill: style.fg,
        'font-weight': style.bold ? 600 : 400,
        'text-decoration': style.underline ? 'underline' : 'none',
        textLength: (width - leading - trailing) * 10, lengthAdjust: 'spacingAndGlyphs',
      });
      run.style.whiteSpace = 'pre';
      run.textContent = text.slice(leading, trailing ? -trailing : undefined);
      group.append(run);
    }
    svg.replaceChildren(group);
    host.dataset.frame = String(index);
  }

  function tick(now) {
    request = undefined;
    if (!playing || !visible || document.hidden) return;
    if (previous !== undefined) elapsed += now - previous;
    previous = now;
    if (index < 0 || elapsed >= preview.intervalMs) {
      index = (index + 1) % preview.frames.length;
      elapsed %= preview.intervalMs;
      paint(preview.frames[index]);
    }
    request = requestAnimationFrame(tick);
  }

  function synchronize() {
    if (request !== undefined) cancelAnimationFrame(request);
    request = undefined;
    previous = undefined;
    if (playing && visible && !document.hidden) request = requestAnimationFrame(tick);
    if (button) {
      button.hidden = !animated;
      button.textContent = playing ? 'Pause' : 'Play';
      button.setAttribute('aria-label', `${playing ? 'Pause' : 'Play'} ${host.dataset.title.toLowerCase()} preview`);
    }
  }

  button?.addEventListener('click', () => { playing = !playing; synchronize(); });
  reduced.addEventListener('change', () => {
    playing = animated && !reduced.matches;
    index = -1;
    elapsed = 0;
    paint(preview.still);
    synchronize();
  });
  document.addEventListener('visibilitychange', synchronize);
  const observer = new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting;
    synchronize();
  }, { threshold: 0 });
  observer.observe(host);
  paint(preview.still);
  host.dataset.ready = 'true';
  synchronize();
}

export async function initializePreviews() {
  const hosts = [...document.querySelectorAll('[data-tui-preview]')];
  try {
    const response = await fetch(new URL('./previews.json', import.meta.url));
    if (!response.ok) throw new Error('Preview data unavailable');
    const data = await response.json();
    if (data.version !== 1) throw new Error('Unsupported preview data');
    for (const host of hosts) {
      let preview = data.previews.find(preview => preview.id === host.dataset.tuiPreview);
      if (!preview) throw new Error('Missing component preview');
      if (preview.fallback) {
        let available = false;
        try {
          const fonts = await document.fonts.load('400 16px "netfyr symbols"', '\u{100000}\u{100001}\u{100002}\u{100003}\u{100004}');
          available = fonts.some(font => font.status === 'loaded');
        } catch {}
        host.dataset.glyphs = available ? 'netfyr' : 'standard';
        host.querySelector('.gallery-tui-toolbar span').textContent = available ? 'Optional · netfyr symbols' : 'Standard characters';
        if (!available) preview = { ...preview, still: preview.fallback };
      }
      mountPreview(host, preview, data.styles);
    }
  } catch {
    for (const host of hosts) {
      host.querySelector('.gallery-tui-toolbar button')?.setAttribute('hidden', '');
      if (host.dataset.ready) continue;
      host.querySelector('[role="status"]').textContent = 'Preview unavailable. Run the terminal gallery to try this component.';
    }
  }
}
