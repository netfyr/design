import { renderCode } from './code.js';

const tabInstances = new WeakMap();
const dialogOpeners = new WeakMap();
const dialogs = new WeakMap();
const codeBoxes = new WeakMap();

function matching(root, selector) {
  const elements = [...root.querySelectorAll(selector)];
  if (root.matches?.(selector)) elements.unshift(root);
  return elements;
}

function unavailable(element) {
  return element.matches(':disabled') || element.getAttribute('aria-disabled') === 'true';
}

function mountTabs(group) {
  const owned = element => element.closest('[data-ui-tabs]') === group;
  const list = [...group.querySelectorAll('[role="tablist"]')].find(owned);
  if (!list) return null;
  const tabs = [...list.querySelectorAll('[role="tab"]')]
    .filter(tab => owned(tab) && tab.closest('[role="tablist"]') === list);
  const pairs = tabs.map(tab => {
    const id = tab.getAttribute('aria-controls');
    return { tab, panel: id ? group.ownerDocument.getElementById(id) : null };
  });
  if (!pairs.length || pairs.some(({ panel }) => !panel || !group.contains(panel)
    || !owned(panel) || panel.getAttribute('role') !== 'tabpanel')) return null;
  if (new Set(pairs.map(({ panel }) => panel)).size !== pairs.length) return null;
  const enabled = () => pairs.filter(({ tab }) => !unavailable(tab) && !tab.hidden);
  const initial = enabled().find(({ tab }) => tab.getAttribute('aria-selected') === 'true')
    || enabled()[0];
  if (!initial) return null;
  let selected;

  function activate(pair, focus = false, notify = false) {
    const changed = selected !== pair;
    selected = pair;
    for (const candidate of pairs) {
      const active = candidate === pair;
      candidate.tab.setAttribute('aria-selected', String(active));
      candidate.tab.tabIndex = active ? 0 : -1;
      candidate.panel.hidden = !active;
    }
    if (focus) pair.tab.focus({ preventScroll: true });
    if (changed && notify) {
      const Event = group.ownerDocument.defaultView.CustomEvent;
      group.dispatchEvent(new Event('ui:tabchange', {
        bubbles: true,
        detail: { tab: pair.tab, panel: pair.panel },
      }));
    }
  }

  function eventPair(event) {
    const tab = event.target.closest?.('[role="tab"]');
    return pairs.find(pair => pair.tab === tab && !unavailable(tab) && !tab.hidden);
  }

  function click(event) {
    const pair = eventPair(event);
    if (!pair || event.defaultPrevented) return;
    event.preventDefault();
    activate(pair, true, true);
  }

  function keydown(event) {
    if (event.defaultPrevented || event.isComposing || event.altKey || event.ctrlKey
      || event.metaKey || event.shiftKey) return;
    const pair = eventPair(event);
    if (!pair) return;
    const vertical = list.getAttribute('aria-orientation') === 'vertical';
    const previous = vertical ? 'ArrowUp' : 'ArrowLeft';
    const next = vertical ? 'ArrowDown' : 'ArrowRight';
    const choices = enabled();
    let index = choices.indexOf(pair);
    if (event.key === previous) index = (index - 1 + choices.length) % choices.length;
    else if (event.key === next) index = (index + 1) % choices.length;
    else if (event.key === 'Home') index = 0;
    else if (event.key === 'End') index = choices.length - 1;
    else return;
    event.preventDefault();
    activate(choices[index], true, true);
  }

  activate(initial);
  list.addEventListener('click', click);
  list.addEventListener('keydown', keydown);
  return () => {
    list.removeEventListener('click', click);
    list.removeEventListener('keydown', keydown);
  };
}

function retainDialog(dialog) {
  let entry = dialogs.get(dialog);
  if (!entry) {
    entry = { references: 0, opener: null };
    entry.close = () => {
      if (dialog.open) return;
      const opener = entry.opener;
      entry.opener = null;
      if (opener?.isConnected && !unavailable(opener)) opener.focus({ preventScroll: true });
    };
    dialog.addEventListener('close', entry.close);
    dialogs.set(dialog, entry);
  }
  entry.references++;
  return entry;
}

function mountDialogOpener(opener, root) {
  const id = opener.dataset.uiOpenDialog;
  const dialog = id ? opener.ownerDocument.getElementById(id) : null;
  if (!dialog || dialog.localName !== 'dialog' || typeof dialog.showModal !== 'function'
    || !root.contains(dialog)) return null;
  const entry = retainDialog(dialog);
  function click(event) {
    if (event.defaultPrevented || event.button !== 0 || event.altKey || event.ctrlKey
      || event.metaKey || event.shiftKey) return;
    event.preventDefault();
    if (unavailable(opener) || !dialog.isConnected || dialog.hidden || dialog.open) return;
    dialog.returnValue = '';
    entry.opener = opener;
    dialog.showModal();
  }
  opener.addEventListener('click', click);
  return () => {
    opener.removeEventListener('click', click);
    entry.references--;
    if (entry.references === 0) {
      dialog.removeEventListener('close', entry.close);
      dialogs.delete(dialog);
    }
  };
}

function mountCodeBox(box) {
  const owned = element => element.closest('[data-ui-codebox]') === box;
  const button = [...box.querySelectorAll('button[data-ui-copy]')].find(owned);
  const code = [...box.querySelectorAll('pre.ui-code > code')].find(owned);
  const status = [...box.querySelectorAll('[data-ui-copy-status]')].find(owned);
  if (!button || !code || !status) return null;
  let active = true;
  let pending = false;
  let restorePending = () => {};

  async function copy(event) {
    if (event.defaultPrevented) return;
    event.preventDefault();
    if (pending || unavailable(button)) return;
    pending = true;
    const copiedText = code.textContent;
    const previousBusy = button.getAttribute('aria-busy');
    const previousDisabled = button.getAttribute('aria-disabled');
    button.setAttribute('aria-busy', 'true');
    button.setAttribute('aria-disabled', 'true');
    restorePending = () => {
      if (previousBusy === null) button.removeAttribute('aria-busy');
      else button.setAttribute('aria-busy', previousBusy);
      if (previousDisabled === null) button.removeAttribute('aria-disabled');
      else button.setAttribute('aria-disabled', previousDisabled);
    };
    try {
      const clipboard = box.ownerDocument.defaultView.navigator.clipboard;
      await clipboard.writeText(copiedText);
      if (active && code.textContent === copiedText) {
        status.textContent = 'Code copied.';
        status.hidden = false;
      }
    } catch {
      if (active && code.textContent === copiedText) {
        status.textContent = 'Copy unavailable. Select the code and copy it manually.';
        status.hidden = false;
      }
    } finally {
      pending = false;
      if (active) restorePending();
    }
  }

  renderCode(code, code.textContent, box.dataset.uiLanguage);
  button.addEventListener('click', copy);
  return () => {
    active = false;
    button.removeEventListener('click', copy);
    if (pending) restorePending();
  };
}

/** Enhance native markup within root. The returned function removes this call's listeners. */
export function enhance(root = document) {
  const owned = [];
  for (const group of matching(root, '[data-ui-tabs]')) {
    if (tabInstances.has(group)) continue;
    const cleanup = mountTabs(group);
    if (!cleanup) continue;
    tabInstances.set(group, cleanup);
    owned.push(() => {
      cleanup();
      tabInstances.delete(group);
    });
  }
  for (const opener of matching(root, '[data-ui-open-dialog]')) {
    if (dialogOpeners.has(opener)) continue;
    const cleanup = mountDialogOpener(opener, root);
    if (!cleanup) continue;
    dialogOpeners.set(opener, cleanup);
    owned.push(() => {
      cleanup();
      dialogOpeners.delete(opener);
    });
  }
  for (const box of matching(root, '[data-ui-codebox]')) {
    if (codeBoxes.has(box)) continue;
    const cleanup = mountCodeBox(box);
    if (!cleanup) continue;
    codeBoxes.set(box, cleanup);
    owned.push(() => {
      cleanup();
      codeBoxes.delete(box);
    });
  }
  let active = true;
  return () => {
    if (!active) return;
    active = false;
    owned.forEach(cleanup => cleanup());
  };
}
