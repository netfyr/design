import { mountTheme } from './src/theme.js';

export function initializeGallery() {
  mountTheme(document.body, { storageKey: 'netfyr-theme' });

  const sidebar = document.querySelector('#gallery-sidebar');
  const backdrop = document.querySelector('#gallery-backdrop');
  const openMenu = document.querySelector('#gallery-open-menu');
  const closeMenu = document.querySelector('#gallery-close-menu');
  const workspace = document.querySelector('.gallery-workspace');
  const mobile = matchMedia('(max-width: 760px)');
  let menuOpen = false;
  let previousOverflow;
  let lastFocused = document.activeElement;
  document.addEventListener('focusin', event => {
    if (event.target !== document.body) lastFocused = event.target;
  });

  function setMenu(open, restoreFocus = false) {
    const visible = open && mobile.matches;
    if (visible && !menuOpen) previousOverflow = document.body.style.overflow;
    if (visible) document.body.style.overflow = 'hidden';
    else if (menuOpen) document.body.style.overflow = previousOverflow;
    menuOpen = visible;
    sidebar.classList.toggle('is-open', visible);
    backdrop.hidden = !visible;
    openMenu.setAttribute('aria-expanded', String(visible));
    sidebar.inert = mobile.matches && !visible;
    workspace.inert = visible;
    if (visible) {
      sidebar.setAttribute('role', 'dialog');
      sidebar.setAttribute('aria-modal', 'true');
      closeMenu.focus({ preventScroll: true });
      requestAnimationFrame(() => {
        if (menuOpen && !sidebar.contains(document.activeElement)) closeMenu.focus({ preventScroll: true });
      });
    } else {
      sidebar.removeAttribute('role');
      sidebar.removeAttribute('aria-modal');
      if (restoreFocus && mobile.matches) openMenu.focus({ preventScroll: true });
    }
  }

  openMenu.addEventListener('click', () => setMenu(true));
  closeMenu.addEventListener('click', () => setMenu(false, true));
  backdrop.addEventListener('click', () => setMenu(false, true));
  sidebar.addEventListener('click', event => {
    const link = event.target.closest?.('a[href]');
    if (!menuOpen || !link || !sidebar.contains(link) || event.defaultPrevented
      || event.button !== 0 || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    const local = link.origin === location.origin && link.pathname === location.pathname && link.search === location.search;
    const target = local && link.hash ? document.getElementById(decodeURIComponent(link.hash.slice(1))) : null;
    setMenu(false, !target);
    if (target) {
      const destination = target.querySelector('h2') || target;
      if (!destination.hasAttribute('tabindex')) destination.tabIndex = -1;
      requestAnimationFrame(() => destination.focus({ preventScroll: true }));
    }
  });
  mobile.addEventListener('change', () => {
    const active = document.activeElement === document.body ? lastFocused : document.activeElement;
    const wasInSidebar = sidebar.contains(active);
    setMenu(false);
    if (mobile.matches && wasInSidebar) openMenu.focus({ preventScroll: true });
    else if (!mobile.matches && (active === closeMenu || active === openMenu)) {
      (sidebar.querySelector('nav a[aria-current]') || sidebar.querySelector('a[href]'))?.focus({ preventScroll: true });
    }
  });
  document.addEventListener('keydown', event => {
    if (!menuOpen || event.defaultPrevented) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      setMenu(false, true);
      return;
    }
    if (event.key !== 'Tab') return;
    const controls = [...sidebar.querySelectorAll('a[href], button:not(:disabled), [tabindex]:not([tabindex="-1"])')]
      .filter(element => element.tabIndex >= 0 && element.getClientRects().length);
    const first = controls[0];
    const last = controls.at(-1);
    if (!first) return;
    if (event.shiftKey && (document.activeElement === first || !sidebar.contains(document.activeElement))) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !sidebar.contains(document.activeElement))) {
      event.preventDefault();
      first.focus();
    }
  });
  document.documentElement.classList.add('has-navigation');
  setMenu(false);

  const links = [...document.querySelectorAll('.gallery-component-links a[href^="#"]')];
  const sections = links.map(link => document.getElementById(link.hash.slice(1)));
  if (sections.some(section => !section)) throw new Error('Missing component section');
  function updateNavigation() {
    const atBottom = scrollY + innerHeight >= document.documentElement.scrollHeight - 2;
    const current = atBottom ? sections.at(-1)
      : sections.findLast(section => section.getBoundingClientRect().top <= 120) || sections[0];
    for (const link of links) {
      if (link.hash === `#${current.id}`) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    }
    const breadcrumb = document.querySelector('#gallery-current-component');
    if (breadcrumb) breadcrumb.textContent = links.find(link => link.hash === `#${current.id}`).textContent.trim();
  }
  let queued = false;
  addEventListener('scroll', () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; updateNavigation(); });
  }, { passive: true });
  updateNavigation();
}
