import assert from 'node:assert/strict';
import { execFileSync, spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readdir, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const session = `netfyr-pages-${process.pid}`;
function browser(args, input) {
  const response = JSON.parse(execFileSync('agent-browser', ['--session', session, '--json', ...args], {
    input, encoding: 'utf8', timeout: 30000,
  }));
  assert.equal(response.success, true, response.error);
  return response.data;
}
function evaluate(source) { return browser(['eval', '--stdin'], source).result; }
function click(selector) {
  browser(['scrollintoview', selector]);
  browser(['wait', '--fn', `(() => {
    const box = document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();
    return box.top >= 0 && box.bottom <= innerHeight;
  })()`]);
  browser(['click', selector]);
}

async function checkFiles(directory) {
  for (const item of await readdir(directory, { withFileTypes: true })) {
    assert.ok(!item.isSymbolicLink(), `Pages artifact contains a symlink: ${item.name}`);
    assert.ok(!/\.pdf$/i.test(item.name), `PDF in Pages artifact: ${item.name}`);
    assert.ok(!['.git', '.openai', '.calira', '.sites-local'].includes(item.name), `Private directory in artifact: ${item.name}`);
    assert.ok(!/^netfyr-(?:(?:mono|sans)-.*\.(?:otf|ttf|woff2)|fonts-0\.(?:401|506)\.zip)$/.test(item.name), `Legacy font in artifact: ${item.name}`);
    if (item.isDirectory()) await checkFiles(path.join(directory, item.name));
  }
}

await checkFiles(path.join(root, 'dist'));
const html = await readFile(path.join(root, 'dist/index.html'), 'utf8');
for (const [file, attribute] of [['styles.css', 'href'], ['app.js', 'src']]) {
  const hash = createHash('sha256').update(await readFile(path.join(root, 'dist', file))).digest('hex').slice(0, 16);
  const reference = new RegExp(`${attribute}="(${file.replace('.', '\\.')}(?:\\?[^"]*)?)"`);
  assert.equal(html.match(reference)?.[1], `${file}?v=${hash}`, `Production ${file} URL must match its content fingerprint`);
}
assert.ok(!html.includes('/__reload'), 'Development reload code reached the production build');
assert.equal((await readFile(path.join(root, 'dist/CNAME'), 'utf8')).trim(), 'design.netfyr.io');
execFileSync('agent-browser', ['--version'], { stdio: 'pipe', timeout: 10000 });

const preview = spawn(process.execPath, ['scripts/preview.mjs', '--port', '0', '--base-path', '/design/'], {
  cwd: root, stdio: ['ignore', 'pipe', 'pipe'],
});
let opened = false;
try {
  const url = await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('Production preview did not start in 10 seconds')), 10000);
    let output = '', errors = '';
    preview.stderr.on('data', chunk => { errors += chunk; });
    preview.once('error', error => { clearTimeout(timeout); reject(error); });
    preview.once('exit', code => { clearTimeout(timeout); reject(new Error(`Preview exited (${code}): ${errors}`)); });
    preview.stdout.on('data', chunk => {
      output += chunk;
      const match = output.match(/Preview: (http:\/\/127\.0\.0\.1:\d+\/design\/)/);
      if (match) { clearTimeout(timeout); resolve(new URL(match[1])); }
    });
  });
  assert.equal((await fetch(new URL('/', url), { signal: AbortSignal.timeout(5000) })).status, 404,
    'Preview must not conceal assets escaping the /design/ base path');
  browser(['open', url.href]);
  opened = true;
  browser(['wait', '--fn', 'document.querySelector(".brand .flame-body") !== null']);
  assert.equal(evaluate('document.querySelector(".page:not([hidden])").id'), 'page-overview');
  assert.equal(evaluate('document.querySelector(".nav-link[aria-current=page]").getAttribute("href")'), '#overview');
  click('.nav-link[href="#typography"]');
  const loaded = evaluate(`(async () => {
    const manifest = await (await fetch('fonts/font-manifest.json')).json();
    const results = await Promise.all(manifest.styles.map(async style => {
      const faces = await document.fonts.load(style.css_style + ' ' + style.weight + ' 24px "' + style.family + '"', 'Ag ģ ≰');
      return faces.length === 1 && faces[0].status === 'loaded';
    }));
    return { count: results.length, failed: results.filter(loaded => !loaded).length,
      inventory: (await (await fetch('assets/glyphs.json')).json()).length,
      fonts: manifest.styles.flatMap(style => ['fonts/' + style.ttf, 'fonts/' + style.woff2]) };
  })()`);
  assert.equal(loaded.count, 28);
  assert.equal(loaded.failed, 0, 'Every real font weight and style must load');
  assert.equal(loaded.inventory, 2225);

  for (const width of [320, 375, 520, 521, 600, 760, 761, 980, 981, 1440, 1920]) {
    browser(['set', 'viewport', String(width), '1000']);
    const hero = evaluate(`(() => {
      const heading = document.querySelector('.type-hero-copy h2');
      const art = document.querySelector('.type-hero-art'), panel = art.getBoundingClientRect();
      const text = art.querySelector('text'), bounds = text.getBoundingClientRect(), style = getComputedStyle(text);
      const baseline = new DOMPoint(0, text.getStartPositionOfChar(0).y).matrixTransform(text.getScreenCTM()).y;
      const canvas = document.createElement('canvas').getContext('2d');
      canvas.font = style.fontWeight + ' ' + style.fontSize + ' ' + style.fontFamily;
      const cap = baseline - canvas.measureText('A').actualBoundingBoxAscent;
      const xHeight = baseline - canvas.measureText('x').actualBoundingBoxAscent;
      const families = document.querySelector('.family-grid').children;
      return {
        titleFits: heading.scrollWidth <= heading.clientWidth && heading.offsetHeight <= 2 * parseFloat(getComputedStyle(heading).lineHeight) + 1,
        labelGap: bounds.left - Math.max(...[...art.querySelectorAll('.metric')].map(label => label.getBoundingClientRect().right)),
        rightGap: panel.right - bounds.right,
        captionGap: cap - art.querySelector('.art-label').getBoundingClientRect().bottom,
        capError: Math.abs(cap - art.querySelector('.cap-line').getBoundingClientRect().top),
        xError: Math.abs(xHeight - art.querySelector('.x-line').getBoundingClientRect().top),
        baselineError: Math.abs(baseline - art.querySelector('.base-line').getBoundingClientRect().top),
        specimenHeight: art.querySelector('.hero-letters').getBoundingClientRect().height,
        columnOffsets: [...document.querySelector('.type-in-context').children].map((child, index) => Math.abs(child.getBoundingClientRect().left - families[index].getBoundingClientRect().left)),
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      };
    })()`);
    assert.equal(hero.titleFits, true, `Hero family names wrap or overflow at ${width}px`);
    assert.ok(hero.labelGap >= 12 && hero.rightGap >= 20 && hero.captionGap >= 12,
      `Hero specimen crowds its labels or panel at ${width}px: ${JSON.stringify(hero)}`);
    assert.ok(hero.specimenHeight >= 100 && hero.capError <= 1.5 && hero.xError <= 1.5 && hero.baselineError <= 1,
      `Hero specimen and guides disagree at ${width}px: ${JSON.stringify(hero)}`);
    assert.ok(hero.columnOffsets.every(offset => offset <= 1), `Text and code columns are misaligned at ${width}px`);
    assert.equal(hero.overflow, 0, `Typography overflows at ${width}px`);
  }
  browser(['set', 'viewport', '1440', '1000']);
  console.log('Typography hero and context columns pass at 11 widths from 320px to 1920px.');

  const references = new Set([...html.matchAll(/(?:href|src)="([^"#][^"]*)"/g)].map(match => match[1]));
  loaded.fonts.forEach(reference => references.add(reference));
  evaluate('performance.getEntriesByType("resource").map(entry => entry.name)').forEach(reference => {
    assert.equal(new URL(reference).origin, url.origin, `Remote asset loaded: ${reference}`);
    references.add(reference);
  });
  const brokenAssets = [];
  for (const reference of references) {
    const asset = new URL(reference, url);
    assert.ok(!/\.pdf$/i.test(decodeURIComponent(asset.pathname)), `PDF link in production site: ${reference}`);
    if (asset.origin !== url.origin) {
      assert.ok(/^https?:$/.test(asset.protocol), `Unexpected link protocol: ${reference}`);
      continue;
    }
    assert.ok(asset.pathname.startsWith(url.pathname), `Asset escapes project base path: ${reference}`);
    const response = await fetch(asset, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
    if (response.status !== 200) brokenAssets.push(`${reference}: HTTP ${response.status}`);
    else if (!(Number(response.headers.get('content-length')) > 0)) brokenAssets.push(`${reference}: empty file`);
  }

  browser(['select', '#font-weight', '700']);
  browser(['select', '#font-style', 'italic']);
  click('[data-family="mono"]');
  assert.deepEqual(evaluate(`(() => {
    const style = getComputedStyle(document.querySelector('#type-input'));
    return [style.fontWeight, style.fontStyle, style.fontFamily.includes('netfyr mono'), style.fontSynthesis];
  })()`), ['700', 'italic', true, 'none']);
  const clipboardFailure = evaluate(`(async () => {
    const writeText = navigator.clipboard.writeText, execCommand = document.execCommand;
    const button = document.querySelector('#copy-type-css');
    navigator.clipboard.writeText = async () => { throw new Error('Clipboard denied'); };
    document.execCommand = () => { throw new Error('Copy unsupported'); };
    try {
      button.focus();
      button.click();
      await new Promise(resolve => setTimeout(resolve, 50));
      return { focus: document.activeElement.id, fields: document.querySelectorAll('textarea').length,
        message: document.querySelector('#toast span').textContent };
    } finally {
      navigator.clipboard.writeText = writeText;
      document.execCommand = execCommand;
    }
  })()`);
  assert.equal(clipboardFailure.focus, 'copy-type-css', 'Clipboard failure lost keyboard focus');
  assert.equal(clipboardFailure.fields, 1, 'Temporary clipboard field leaked');
  assert.match(clipboardFailure.message, /Copy unavailable/);
  evaluate(`window.originalFetch = window.fetch;
    window.fetch = (input, options) => String(input) === 'assets/glyphs.json'
      ? new Promise((resolve, reject) => options?.signal?.addEventListener('abort', () => reject(options.signal.reason), { once: true }))
      : window.originalFetch(input, options);`);
  click('#tab-glyphs');
  browser(['wait', '--fn', 'document.querySelector("#glyph-grid button.empty-state") !== null']);
  assert.equal(evaluate('document.querySelector("#glyph-count").textContent'), 'Character map unavailable');
  evaluate('window.fetch = window.originalFetch; delete window.originalFetch;');
  click('#glyph-grid button.empty-state');
  browser(['wait', '--fn', 'document.querySelectorAll(".glyph-cell").length > 0']);
  for (const code of ['0123', '030A', '2270', 'E0B0']) {
    browser(['fill', '#glyph-search', `U+${code}`]);
    assert.equal(evaluate('document.querySelector(".glyph-code")?.textContent'), `U+${code}`);
  }
  click('.glyph-cell');
  browser(['wait', '--text', 'U+E0B0 copied']);
  const theme = evaluate('document.documentElement.dataset.theme');
  click('#theme-toggle');
  assert.notEqual(evaluate('document.documentElement.dataset.theme'), theme);
  browser(['reload']);
  assert.notEqual(evaluate('document.documentElement.dataset.theme'), theme, 'Theme preference did not persist');

  evaluate(`location.hash = '#colors'`);
  browser(['wait', '--fn', '!document.querySelector("#page-colors").hidden']);
  evaluate(`window.savedClipboardWrite = navigator.clipboard.writeText;
    window.copiedCode = [];
    navigator.clipboard.writeText = async text => { window.copiedCode.push(text); };`);
  try {
    const selector = '#page-colors .code-block';
    const expected = evaluate(`document.querySelector('${selector} code').textContent`);
    click(`${selector} pre`);
    click(selector);
    click(`${selector} .copy-code`);
    browser(['press', 'Enter']);
    browser(['press', 'Space']);
    assert.deepEqual(evaluate('window.copiedCode'), Array(5).fill(expected),
      'The code block and copy button must copy once per pointer or keyboard activation');
    for (let iteration = 0; iteration < 2; iteration++) {
      const appearance = evaluate(`(() => {
        const block = getComputedStyle(document.querySelector('${selector}'));
        const code = getComputedStyle(document.querySelector('${selector} code'));
        const toast = document.querySelector('#toast');
        const style = getComputedStyle(toast);
        return { theme: document.documentElement.dataset.theme, block: block.backgroundColor,
          code: code.color, toast: style.backgroundColor, text: style.color,
          border: style.borderTopWidth, position: style.position, hidden: toast.hidden };
      })()`);
      assert.equal(appearance.block, 'rgb(33, 28, 25)', `Code background in ${appearance.theme} theme`);
      assert.equal(appearance.code, 'rgb(247, 242, 234)', `Code text in ${appearance.theme} theme`);
      assert.equal(appearance.toast, 'rgb(33, 28, 25)');
      assert.equal(appearance.text, 'rgb(247, 242, 234)');
      assert.equal(appearance.border, '1px');
      assert.equal(appearance.position, 'fixed');
      assert.equal(appearance.hidden, false);
      click('#theme-toggle');
      click(`${selector} pre`);
    }
  } finally {
    evaluate(`navigator.clipboard.writeText = window.savedClipboardWrite;
      delete window.savedClipboardWrite; delete window.copiedCode;`);
  }

  browser(['set', 'viewport', '375', '812']);
  for (const page of ['overview', 'typography', 'colors', 'spacing', 'brand', 'resources']) {
    click('#open-menu');
    click(`.nav-link[href="#${page}"]`);
    browser(['wait', '--fn', `!document.querySelector('#page-${page}').hidden`]);
    const layout = evaluate(`({ width: document.documentElement.clientWidth,
      content: document.documentElement.scrollWidth,
      menuClosed: document.querySelector('#open-menu').getAttribute('aria-expanded') === 'false' })`);
    assert.ok(layout.content <= layout.width, `${page} overflows a 375px viewport: ${JSON.stringify(layout)}`);
    assert.equal(layout.menuClosed, true);
  }
  console.log('Production /design/ preview: 28 font faces, glyph search, controls, copy, theme and six mobile pages pass.');
  execFileSync(process.execPath, ['scripts/check-flame-browser.mjs', url.href], {
    cwd: root, stdio: 'inherit', timeout: 60000,
  });
  assert.deepEqual(brokenAssets, [], 'Broken production asset links');
  console.log(`All ${references.size} production asset links pass; no PDFs are published or linked.`);
} finally {
  try { if (opened) browser(['close']); }
  finally {
    if (preview.exitCode === null) {
      const stopped = new Promise(resolve => preview.once('exit', resolve));
      preview.kill('SIGTERM');
      const timeout = setTimeout(() => preview.kill('SIGKILL'), 3000);
      await stopped;
      clearTimeout(timeout);
    }
  }
}
