export function initializeRecordings() {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  for (const host of document.querySelectorAll('[data-tui-recording]')) {
    const image = host.querySelector('img');
    const button = host.querySelector('[data-recording-toggle]');
    const poster = new URL(image.dataset.poster, document.baseURI).href;
    const animation = new URL(image.dataset.gif, document.baseURI).href;
    let playing = !reduced.matches;
    let visible = false;

    function synchronize() {
      const active = playing && visible && !document.hidden;
      const source = active ? animation : poster;
      if (image.src !== source) image.src = source;
      button.textContent = playing ? 'Stop' : 'Play';
      button.setAttribute('aria-label', `${playing ? 'Stop' : 'Play'} ${host.dataset.title.toLowerCase()} recording`);
      button.hidden = false;
    }

    button.addEventListener('click', () => { playing = !playing; synchronize(); });
    reduced.addEventListener('change', () => { playing = !reduced.matches; synchronize(); });
    document.addEventListener('visibilitychange', synchronize);
    const observer = new IntersectionObserver(entries => {
      visible = entries[0].isIntersecting;
      synchronize();
    });
    observer.observe(host);
    synchronize();
  }
}
