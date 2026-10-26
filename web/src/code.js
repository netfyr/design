import core from './vendor/highlightjs/core.min.js';
import xml from './vendor/highlightjs/languages/xml.min.js';
import css from './vendor/highlightjs/languages/css.min.js';
import javascript from './vendor/highlightjs/languages/javascript.min.js';
import typescript from './vendor/highlightjs/languages/typescript.min.js';
import json from './vendor/highlightjs/languages/json.min.js';
import bash from './vendor/highlightjs/languages/bash.min.js';
import rust from './vendor/highlightjs/languages/rust.min.js';

const highlighter = core.newInstance();
for (const [name, grammar] of Object.entries({ xml, css, javascript, typescript, json, bash, rust })) {
  highlighter.registerLanguage(name, grammar);
}
const languages = new Map([
  ['html', 'xml'], ['xml', 'xml'], ['css', 'css'],
  ['javascript', 'javascript'], ['js', 'javascript'], ['jsx', 'javascript'],
  ['typescript', 'typescript'], ['ts', 'typescript'], ['tsx', 'typescript'],
  ['json', 'json'], ['bash', 'bash'], ['sh', 'bash'], ['shell', 'bash'],
  ['rust', 'rust'], ['rs', 'rust'],
]);

export function renderCode(code, source, language) {
  const selected = languages.get(String(language || '').trim().toLowerCase());
  if (selected) {
    try {
      const result = highlighter.highlight(source, { language: selected, ignoreIllegals: true });
      const template = code.ownerDocument.createElement('template');
      // HTML parsing normalizes literal carriage returns, including those in CRLF.
      template.innerHTML = result.value.replace(/\r/g, '&#13;');
      const safe = [...template.content.querySelectorAll('*')].every(element =>
        element.localName === 'span' && [...element.attributes].every(attribute => attribute.name === 'class'));
      if (safe && template.content.textContent === source) {
        code.replaceChildren(template.content);
        return;
      }
    } catch {
      // Highlighting is optional; unreadable or unsupported input stays literal.
    }
  }
  code.textContent = source;
}
