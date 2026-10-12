import { mountFlames } from './flame.js';

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const pages = {
  overview: ['Library', 'Overview'],
  typography: ['Foundations', 'Typography'],
  colors: ['Foundations', 'Color palette'],
  spacing: ['Foundations', 'Space & scale'],
  brand: ['Identity', 'Logo'],
  resources: ['Resources', 'Downloads'],
};
let activePage;
let toastTimer;

function notify(message) {
  clearTimeout(toastTimer);
  $('#toast span').textContent = message;
  $('#toast').hidden = false;
  toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 3000);
}

async function copy(text, message = 'Copied to clipboard') {
  try {
    await navigator.clipboard.writeText(text);
    notify(message);
  } catch {
    const focus = document.activeElement;
    const field = document.createElement('textarea');
    field.value = text;
    field.style.cssText = 'position:fixed;left:-9999px';
    document.body.append(field);
    let copied = false;
    try {
      field.select();
      copied = document.execCommand('copy');
    } catch {} finally {
      field.remove();
      if (focus?.isConnected) focus.focus({ preventScroll: true });
    }
    notify(copied ? message : 'Copy unavailable. Select and copy the value manually.');
  }
}

function route(initial = false) {
  const [target, tab] = location.hash.slice(1).split('/');
  if (target === 'main') return;
  if (target === 'family-details') {
    if (activePage !== 'typography') showPage('typography');
    selectTab('playground');
    $('#family-details').scrollIntoView({ block: 'start' });
    return;
  }
  const page = Object.hasOwn(pages, target) ? target : 'typography';
  const changed = activePage !== page;
  showPage(page);
  if (page === 'typography' && ['playground', 'glyphs', 'usage'].includes(tab)) selectTab(tab);
  if (changed && !initial) {
    window.scrollTo({ top: 0, behavior: 'instant' });
    $('#main').focus({ preventScroll: true });
  }
  resizeText();
}

function showPage(page) {
  activePage = page;
  for (const section of $$('.page')) section.hidden = section.id !== `page-${page}`;
  for (const link of $$('.nav-link')) {
    const selected = link.getAttribute('href') === `#${page}`;
    link.classList.toggle('active', selected);
    if (selected) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }
  $('#breadcrumb-group').textContent = pages[page][0];
  $('#breadcrumb-page').textContent = pages[page][1];
  document.title = `${pages[page][1]} · netfyr design library`;
}

window.addEventListener('hashchange', () => route());

const systemTheme = matchMedia('(prefers-color-scheme: dark)');
let savedTheme;
try { savedTheme = localStorage.getItem('netfyr-theme'); } catch {}
if (!['light', 'dark'].includes(savedTheme)) savedTheme = null;
function setTheme(theme, persist = false) {
  document.documentElement.dataset.theme = theme;
  $('#theme-toggle').setAttribute('aria-label', `Switch to ${theme === 'light' ? 'dark' : 'light'} theme`);
  $('#theme-toggle use').setAttribute('href', theme === 'light' ? '#i-sun' : '#i-moon');
  $('meta[name="theme-color"]').content = theme === 'light' ? '#F7F2EA' : '#211C19';
  if (persist) {
    savedTheme = theme;
    try { localStorage.setItem('netfyr-theme', theme); } catch {}
  }
}
setTheme(savedTheme || (systemTheme.matches ? 'dark' : 'light'));
systemTheme.addEventListener('change', event => {
  if (!savedTheme) setTheme(event.matches ? 'dark' : 'light');
});
$('#theme-toggle').addEventListener('click', () => setTheme(document.documentElement.dataset.theme === 'light' ? 'dark' : 'light', true));

const mobile = matchMedia('(max-width: 760px)');
function setMenu(open, restoreFocus = false) {
  const visible = open && mobile.matches;
  $('#sidebar').classList.toggle('open', visible);
  $('#sidebar-backdrop').hidden = !visible;
  $('#open-menu').setAttribute('aria-expanded', String(visible));
  $('#sidebar').inert = mobile.matches && !visible;
  $('.workspace').inert = visible;
  document.body.style.overflow = visible ? 'hidden' : '';
  if (visible) {
    $('#sidebar').setAttribute('role', 'dialog');
    $('#sidebar').setAttribute('aria-modal', 'true');
    $('#close-menu').focus();
  } else {
    $('#sidebar').removeAttribute('role');
    $('#sidebar').removeAttribute('aria-modal');
    if (restoreFocus) $('#open-menu').focus();
  }
}
$('#open-menu').addEventListener('click', () => setMenu(true));
$('#close-menu').addEventListener('click', () => setMenu(false, true));
$('#sidebar-backdrop').addEventListener('click', () => setMenu(false, true));
$('#sidebar').addEventListener('click', event => {
  if (event.target.closest('a')) setMenu(false);
});
mobile.addEventListener('change', () => setMenu(false));
document.addEventListener('keydown', event => {
  if (!$('#sidebar').classList.contains('open')) return;
  if (event.key === 'Escape') { setMenu(false, true); return; }
  if (event.key !== 'Tab') return;
  const controls = [...$('#sidebar').querySelectorAll('a, button')].filter(el => el.getClientRects().length);
  const first = controls[0];
  const last = controls.at(-1);
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
});
setMenu(false);

function selectTab(name) {
  for (const tab of $$('[data-tab]')) {
    const selected = tab.dataset.tab === name;
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
    $(`#panel-${tab.dataset.tab}`).hidden = !selected;
  }
  if (name === 'glyphs') loadGlyphs();
  if (name === 'playground') resizeText();
}
const tabs = $$('[data-tab]');
for (const tab of tabs) {
  tab.addEventListener('click', () => selectTab(tab.dataset.tab));
  tab.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    let index = tabs.indexOf(tab);
    if (event.key === 'Home') index = 0;
    else if (event.key === 'End') index = tabs.length - 1;
    else index = (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
    selectTab(tabs[index].dataset.tab);
    tabs[index].focus();
  });
}

const weightNames = { 300: 'Light', 400: 'Regular', 500: 'Medium', 600: 'SemiBold', 700: 'Bold', 800: 'ExtraBold', 900: 'Black' };
const preview = { family: 'sans', weight: 400, style: 'normal', size: matchMedia('(max-width: 520px)').matches ? 42 : 64, align: 'left' };
function resizeText() {
  const input = $('#type-input');
  if (!input.getClientRects().length) return;
  input.style.height = 'auto';
  input.style.height = `${Math.max(148, input.scrollHeight)}px`;
}
function updatePreview() {
  $('#type-input').style.fontFamily = `"netfyr ${preview.family}", ${preview.family === 'sans' ? 'sans-serif' : 'monospace'}`;
  $('#type-input').style.fontWeight = preview.weight;
  $('#type-input').style.fontStyle = preview.style;
  $('#type-input').style.fontSize = `${preview.size}px`;
  $('#type-input').style.textAlign = preview.align;
  $('#font-size').value = preview.size;
  $('#font-weight').value = preview.weight;
  $('#font-style').value = preview.style;
  $('#size-output').textContent = `${preview.size} px`;
  $('#preview-meta').textContent = `netfyr ${preview.family} / ${weightNames[preview.weight]}${preview.style === 'italic' ? ' Italic' : ''} / ${preview.size} px`;
  for (const button of $$('[data-family]')) {
    const selected = button.dataset.family === preview.family;
    button.classList.toggle('selected', selected);
    button.setAttribute('aria-pressed', String(selected));
  }
  for (const button of $$('[data-align]')) {
    const selected = button.dataset.align === preview.align;
    button.classList.toggle('selected', selected);
    button.setAttribute('aria-pressed', String(selected));
  }
  resizeText();
  document.fonts.load(`${preview.style} ${preview.weight} ${preview.size}px "netfyr ${preview.family}"`).then(resizeText).catch(() => notify("This font could not load. Try reloading the page."));
}
for (const button of $$('[data-family]')) button.addEventListener('click', () => { preview.family = button.dataset.family; updatePreview(); });
for (const button of $$('[data-align]')) button.addEventListener('click', () => { preview.align = button.dataset.align; updatePreview(); });
$('#font-size').addEventListener('input', event => { preview.size = Number(event.target.value); updatePreview(); });
$('#font-weight').addEventListener('change', event => { preview.weight = Number(event.target.value); updatePreview(); });
$('#font-style').addEventListener('change', event => { preview.style = event.target.value; updatePreview(); });
$('#type-input').addEventListener('input', resizeText);
window.addEventListener('resize', resizeText);
$('#reset-type').addEventListener('click', () => {
  Object.assign(preview, { family: 'sans', weight: 400, style: 'normal', size: matchMedia('(max-width: 520px)').matches ? 42 : 64, align: 'left' });
  $('#type-input').value = 'Network settings\nReview changes.';
  updatePreview();
  notify('Playground reset');
});
$('#copy-type-css').addEventListener('click', () => copy(`font-family: "netfyr ${preview.family}", ${preview.family === 'sans' ? 'sans-serif' : 'monospace'};\nfont-weight: ${preview.weight};\nfont-style: ${preview.style};\nfont-synthesis: none;\nfont-size: ${preview.size}px;\nline-height: 1.3;\ntext-align: ${preview.align};`, 'Type styles copied'));
for (const button of $$('[data-use-family]')) button.addEventListener('click', () => {
  preview.family = button.dataset.useFamily;
  selectTab('playground');
  updatePreview();
  $('.playground').scrollIntoView({ block: 'center' });
  $('#type-input').focus({ preventScroll: true });
});
updatePreview();
document.fonts.ready.then(resizeText);

let glyphs;
let glyphLoading = false;
let glyphPage = 0;
const pageSize = 64;
function categoryMatches(cp, category, unicodeCategory) {
  if (category === 'all') return true;
  if (category === 'latin') return cp <= 0x024f || (cp >= 0x1e00 && cp <= 0x1eff) || (cp >= 0x0250 && cp <= 0x02af);
  if (category === 'marks') return unicodeCategory.startsWith('M');
  if (category === 'math') return (cp >= 0x2190 && cp <= 0x22ff) || (cp >= 0x27c0 && cp <= 0x2aff);
  if (category === 'technical') return (cp >= 0x2500 && cp <= 0x259f) || (cp >= 0x2800 && cp <= 0x28ff);
  return !categoryMatches(cp, 'latin', unicodeCategory) && !categoryMatches(cp, 'marks', unicodeCategory) && !categoryMatches(cp, 'math', unicodeCategory) && !categoryMatches(cp, 'technical', unicodeCategory);
}
async function loadGlyphs() {
  if (glyphs) { renderGlyphs(); return; }
  if (glyphLoading) return;
  glyphLoading = true;
  $('#glyph-count').textContent = 'Loading characters…';
  try {
    const response = await fetch('assets/glyphs.json', { signal: AbortSignal.timeout(10000) });
    if (!response.ok) throw new Error('Character map unavailable');
    glyphs = await response.json();
    renderGlyphs();
  } catch {
    $('#glyph-count').textContent = 'Character map unavailable';
    const button = document.createElement('button');
    button.className = 'button button-outlined empty-state';
    button.textContent = 'Could not load the characters. Try again.';
    button.addEventListener('click', loadGlyphs);
    $('#glyph-grid').replaceChildren(button);
  } finally { glyphLoading = false; }
}
function renderGlyphs() {
  if (!glyphs) return;
  const query = $('#glyph-search').value.trim().toLowerCase();
  const group = $('#glyph-category').value;
  const results = glyphs.filter(([cp, character, name, category]) => {
    const code = `u+${cp.toString(16).padStart(4, '0')}`;
    return categoryMatches(cp, group, category) && (!query || character === query || `${name.toLowerCase()} ${code}`.includes(query));
  });
  const totalPages = Math.max(1, Math.ceil(results.length / pageSize));
  glyphPage = Math.min(glyphPage, totalPages - 1);
  const fragment = document.createDocumentFragment();
  for (const [cp, character, name, category] of results.slice(glyphPage * pageSize, (glyphPage + 1) * pageSize)) {
    const code = `U+${cp.toString(16).toUpperCase().padStart(4, '0')}`;
    const button = document.createElement('button');
    button.className = 'glyph-cell';
    button.title = `${code} · ${name}`;
    button.setAttribute('aria-label', `Copy ${name}, ${code}`);
    const shape = document.createElement('span');
    shape.className = 'glyph-character';
    shape.style.fontFamily = `"netfyr ${$('#glyph-family').value}", monospace`;
    shape.setAttribute('aria-hidden', 'true');
    shape.textContent = category.startsWith('M') ? `◌${character}` : ['Cc', 'Cf', 'Cn'].includes(category) ? '·' : character.trim() ? character : '␣';
    const label = document.createElement('span');
    label.className = 'glyph-code';
    label.textContent = code;
    button.append(shape, label);
    button.addEventListener('click', () => copy(character, `${code} copied`));
    fragment.append(button);
  }
  if (!results.length) {
    const empty = document.createElement('p');
    empty.className = 'empty-state';
    empty.textContent = 'No characters match. Try a name, a character, or a Unicode code point.';
    fragment.append(empty);
  }
  $('#glyph-grid').replaceChildren(fragment);
  $('#glyph-count').textContent = `${results.length.toLocaleString()} characters`;
  $('#glyph-page').textContent = `Page ${glyphPage + 1} of ${totalPages}`;
  $('#glyph-previous').disabled = glyphPage === 0;
  $('#glyph-next').disabled = glyphPage + 1 >= totalPages;
}
for (const id of ['glyph-search', 'glyph-category']) $(`#${id}`).addEventListener(id === 'glyph-search' ? 'input' : 'change', () => { glyphPage = 0; renderGlyphs(); });
$('#glyph-family').addEventListener('change', renderGlyphs);
$('#glyph-previous').addEventListener('click', () => { glyphPage = Math.max(0, glyphPage - 1); renderGlyphs(); });
$('#glyph-next').addEventListener('click', () => { glyphPage += 1; renderGlyphs(); });

for (const [weight, name] of Object.entries(weightNames)) {
  const row = document.createElement('tr');
  row.innerHTML = `<td>${weight} / ${name}</td><td>Upright + Italic</td><td>Upright + Italic</td>`;
  $('#weight-rows').append(row);
}
for (const block of $$('.code-block')) {
  block.addEventListener('click', () => copy(block.querySelector('code').textContent, 'Code copied'));
}
for (const button of $$('[data-copy]')) button.addEventListener('click', () => copy(button.dataset.copy, `${button.dataset.copy} copied`));

function luminance(hex) {
  const rgb = hex.match(/[a-f\d]{2}/gi).map(value => parseInt(value, 16) / 255).map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4);
  return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2];
}
function contrast(a, b) {
  const values = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return ((values[0] + .05) / (values[1] + .05)).toFixed(2) + ':1';
}
$('#contrast-ink').textContent = contrast('#211C19', '#F7F2EA');
$('#contrast-orange').textContent = contrast('#FF7A1A', '#211C19');
for (const step of [1, 2, 3, 4, 6, 8, 12, 16]) {
  const value = step * 4;
  const button = document.createElement('button');
  button.className = 'space-step';
  button.setAttribute('aria-label', `Copy --space-${step}: ${value}px`);
  button.innerHTML = `<code>--space-${step}</code><span class="space-bar" style="width:${value}px"></span><span class="space-value">${value} px</span><svg aria-hidden="true"><use href="#i-copy"/></svg>`;
  button.addEventListener('click', () => copy(`--space-${step}: ${value}px;`, 'Spacing token copied'));
  $('#space-scale').append(button);
}
mountFlames();
route(true);
