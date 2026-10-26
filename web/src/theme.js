const themes = new WeakMap();

export function mountTheme(root, { storageKey = null } = {}) {
  if (!root?.matches('[data-ui-theme]')) {
    throw new TypeError('Theme roots require data-ui-theme.');
  }
  if (themes.has(root)) return () => {};

  const view = root.ownerDocument.defaultView;
  const systemTheme = view.matchMedia('(prefers-color-scheme: dark)');
  const buttons = [...root.querySelectorAll('button[data-ui-theme-toggle]')]
    .filter(button => button.closest('[data-ui-theme]') === root);
  const initiallyHidden = new Map(buttons.map(button => [button, button.hidden]));
  let choice = null;
  let mode;
  if (storageKey !== null) {
    try { choice = view.localStorage.getItem(storageKey); } catch {}
  }
  if (choice !== 'light' && choice !== 'dark') choice = null;

  function apply(next) {
    const changed = root.dataset.uiMode !== next;
    mode = next;
    root.dataset.uiMode = mode;
    for (const button of buttons) {
      button.setAttribute('aria-label', `Switch to ${mode === 'light' ? 'dark' : 'light'} theme`);
      for (const icon of button.querySelectorAll('[data-ui-theme-icon]')) {
        icon.toggleAttribute('hidden', icon.dataset.uiThemeIcon !== mode);
      }
      button.hidden = false;
    }
    if (changed) {
      root.dispatchEvent(new view.CustomEvent('ui:themechange', { bubbles: true, detail: { mode } }));
    }
  }

  function toggle(event) {
    if (event.currentTarget.disabled || event.currentTarget.getAttribute('aria-disabled') === 'true') return;
    choice = mode === 'light' ? 'dark' : 'light';
    if (storageKey !== null) {
      try { view.localStorage.setItem(storageKey, choice); } catch {}
    }
    apply(choice);
  }

  function followSystem(event) {
    if (choice === null) apply(event.matches ? 'dark' : 'light');
  }

  let active = true;
  const cleanup = () => {
    if (!active) return;
    active = false;
    systemTheme.removeEventListener('change', followSystem);
    for (const button of buttons) {
      button.removeEventListener('click', toggle);
      button.hidden = initiallyHidden.get(button);
    }
    themes.delete(root);
  };
  themes.set(root, cleanup);
  buttons.forEach(button => button.addEventListener('click', toggle));
  systemTheme.addEventListener('change', followSystem);
  apply(choice || (systemTheme.matches ? 'dark' : 'light'));
  return cleanup;
}
