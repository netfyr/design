import { enhance } from './src/components.js';
import { mountTheme } from './src/theme.js';
import { initializeGallery } from './gallery-shell.js';

function exampleMarkup(element, depth = 0) {
  const indent = '  '.repeat(depth);
  const literal = ['pre', 'code', 'textarea', 'script', 'style'].includes(element.localName);
  const mixed = [...element.childNodes].some(node => node.nodeType !== 1
    && (node.nodeType !== 3 || node.textContent.trim()));
  if (literal || mixed || !element.children.length) return indent + element.outerHTML;
  const shell = element.cloneNode(false).outerHTML;
  const closing = `</${element.localName}>`;
  if (!shell.endsWith(closing)) return indent + element.outerHTML;
  return indent + shell.slice(0, -closing.length) + '\n'
    + [...element.children].map(child => exampleMarkup(child, depth + 1)).join('\n')
    + '\n' + indent + closing;
}

for (const example of document.querySelectorAll('[data-example]')) {
  const clone = example.querySelector('.gallery-stage').cloneNode(true);
  for (const element of [clone, ...clone.querySelectorAll('[class]')]) {
    for (const name of [...element.classList]) if (name.startsWith('gallery-')) element.classList.remove(name);
    if (!element.className) element.removeAttribute('class');
  }
  clone.querySelector('[novalidate]')?.removeAttribute('novalidate');
  let source = [...clone.children].map(element => exampleMarkup(element)).join('\n');
  if (example.dataset.example === 'theme') {
    source = '<link rel="stylesheet" href="./src/components.css">\n'
      + '<link rel="stylesheet" href="./src/theme.css">\n' + source
      + '\n<script type="module">\n'
      + "  import { mountTheme } from './src/theme.js';\n"
      + "  const cleanup = mountTheme(document.querySelector('#demo-theme'));\n"
      + '</script>';
  }
  example.querySelector('.gallery-source pre code').textContent = source;
}
enhance();
mountTheme(document.querySelector('#demo-theme'));

const items = document.querySelector('#demo-items');
const remove = document.querySelector('#demo-remove');
let nextItem = 3;
document.querySelector('#demo-add').addEventListener('click', () => {
  const item = document.createElement('li');
  item.textContent = `Item ${nextItem++}`;
  items.append(item);
  remove.disabled = false;
});
remove.addEventListener('click', () => {
  items.lastElementChild?.remove();
  remove.disabled = !items.childElementCount;
});

const form = document.querySelector('#demo-form');
const formStatus = document.querySelector('#demo-form-status');
const fields = [document.querySelector('#demo-name'), document.querySelector('#demo-email')];
function fieldError(field) {
  if (!field.value.trim()) return field.id === 'demo-name' ? 'Enter a project name.' : 'Enter a contact email.';
  if (!field.validity.valid) return 'Enter a valid email address.';
  return '';
}
function showError(field, message) {
  const error = document.querySelector(`#${field.id}-error`);
  error.textContent = message;
  error.hidden = !message;
  if (message) field.setAttribute('aria-invalid', 'true');
  else field.removeAttribute('aria-invalid');
}
form.addEventListener('submit', event => {
  event.preventDefault();
  let invalid;
  for (const field of fields) {
    const message = fieldError(field);
    showError(field, message);
    if (message && !invalid) invalid = field;
  }
  if (invalid) {
    formStatus.textContent = '';
    invalid.focus();
  } else {
    formStatus.textContent = `Saved “${fields[0].value.trim()}” for ${fields[1].value.trim()}.`;
  }
});
form.addEventListener('input', event => {
  formStatus.textContent = '';
  if (fields.includes(event.target) && event.target.hasAttribute('aria-invalid')) {
    showError(event.target, fieldError(event.target));
  }
});
form.addEventListener('reset', () => {
  fields.forEach(field => showError(field, ''));
  formStatus.textContent = '';
});

const dialog = document.querySelector('#demo-dialog');
dialog.addEventListener('close', () => {
  document.querySelector('#demo-dialog-status').textContent = dialog.returnValue === 'confirm'
    ? 'Example archived.' : 'Example left unchanged.';
});

const feedback = document.querySelector('#demo-feedback-status');
const retry = document.querySelector('#demo-retry');
let failed = true;
retry.addEventListener('click', () => {
  failed = !failed;
  feedback.classList.toggle('ui-notice--danger', failed);
  feedback.classList.toggle('ui-notice--success', !failed);
  feedback.querySelector('strong').textContent = failed
    ? 'Could not load the example records.' : '4 example records loaded.';
  retry.textContent = failed ? 'Retry example' : 'Show failure again';
});

const rows = [...document.querySelectorAll('#demo-table-body tr')];
document.querySelector('#demo-table-filter').addEventListener('input', event => {
  const query = event.target.value.trim().toLocaleLowerCase();
  let count = 0;
  for (const row of rows) {
    row.hidden = !row.textContent.toLocaleLowerCase().includes(query);
    if (!row.hidden) count++;
  }
  document.querySelector('#demo-table-count').textContent = `${count} ${count === 1 ? 'record' : 'records'}`;
  document.querySelector('#demo-table-empty').hidden = count > 0;
});

initializeGallery();
document.documentElement.dataset.galleryReady = 'true';
