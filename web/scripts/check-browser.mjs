import assert from 'node:assert/strict';
import { execFileSync, spawn } from 'node:child_process';
import { readdir, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { packageFiles } from './build.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const session = 'netfyr-web-' + process.pid;
function browser(args, input) {
  const response = JSON.parse(execFileSync('agent-browser', ['--session', session, '--json', ...args], {
    input, encoding: 'utf8', timeout: 30000,
  }));
  assert.equal(response.success, true, response.error);
  return response.data;
}
function script(fn, argument) { return '(' + fn.toString() + ')(' + JSON.stringify(argument) + ')'; }
function evaluate(fn, argument) { return browser(['eval', '--stdin'], script(fn, argument)).result; }
function wait(fn, argument) { browser(['wait', '--fn', script(fn, argument)]); }
function click(selector) {
  browser(['scrollintoview', selector]);
  wait(selector => {
    const element = document.querySelector(selector);
    const box = element.getBoundingClientRect();
    const position = [selector, box.x, box.y, box.width, box.height].join(':');
    const settled = window.webCheckLastPosition === position;
    window.webCheckLastPosition = position;
    const hit = document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2);
    return settled && box.top >= 0 && box.bottom <= innerHeight && element.contains(hit);
  }, selector);
  browser(['click', selector]);
}
function setMode(mode) {
  if (evaluate(() => document.body.dataset.uiMode) !== mode) click('#gallery-theme-toggle');
  wait(expected => document.body.dataset.uiMode === expected, mode);
}
function tabState(selector) {
  return evaluate(selector => ({
    selected: [...document.querySelectorAll(selector + ' [role=tab][aria-selected=true]')].map(tab => tab.id),
    visible: [...document.querySelectorAll(selector + ' [role=tabpanel]')].filter(panel => !panel.hidden).map(panel => panel.id),
    focus: document.activeElement.id,
  }), selector);
}

async function checkArtifact(directory) {
  for (const item of await readdir(directory, { withFileTypes: true })) {
    assert.ok(!item.isSymbolicLink(), 'Symlink in web artifact: ' + item.name);
    assert.ok(!['.git', '.calira', 'node_modules', 'website', 'font-sources'].includes(item.name),
      'Source/private directory in web artifact: ' + item.name);
    assert.ok(!/\.pdf$/i.test(item.name), 'Reference PDF in web artifact: ' + item.name);
    if (item.isDirectory()) await checkArtifact(path.join(directory, item.name));
  }
}

await checkArtifact(path.join(root, 'dist'));
const html = await readFile(path.join(root, 'dist/index.html'), 'utf8');
const manifest = JSON.parse(await readFile(path.join(root, 'package.json'), 'utf8'));
const archive = path.join(root, 'dist/downloads', manifest.name.replace(/^@/, '').replaceAll('/', '-') + '-' + manifest.version + '.tgz');
const packedFiles = execFileSync('tar', ['-tzf', archive], { encoding: 'utf8', timeout: 10000 }).trim().split('\n');
assert.ok(packedFiles.includes('package/src/components.js') && packedFiles.includes('package/src/components.css'),
  'Download must contain the reusable exports');
assert.deepEqual(packedFiles.sort(), packageFiles.map(file => 'package/' + file).sort(),
  'Package differs from its public source and license allowlist');
execFileSync('agent-browser', ['--version'], { stdio: 'pipe', timeout: 10000 });
const preview = spawn(process.execPath, ['scripts/serve.mjs', '--production', '--port', '0', '--base-path', '/components/'], {
  cwd: root, stdio: ['ignore', 'pipe', 'pipe'],
});
let opened = false;
let cdp;
try {
  const url = await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('Web preview did not start in 10 seconds')), 10000);
    let output = '', errors = '';
    preview.stderr.on('data', chunk => { errors += chunk; });
    preview.once('error', error => { clearTimeout(timeout); reject(error); });
    preview.once('exit', code => { clearTimeout(timeout); reject(new Error('Preview exited (' + code + '): ' + errors)); });
    preview.stdout.on('data', chunk => {
      output += chunk;
      const match = output.match(/http:\/\/127\.0\.0\.1:\d+\/components\//);
      if (match) { clearTimeout(timeout); resolve(new URL(match[0])); }
    });
  });
  assert.equal((await fetch(new URL('/', url), { signal: AbortSignal.timeout(5000) })).status, 404,
    'Production preview must expose incorrect absolute asset paths');
  browser(['open', url.href]);
  opened = true;
  wait(() => document.documentElement.dataset.galleryReady === 'true');
  browser(['set', 'viewport', '1440', '1000']);
  browser(['snapshot', '-i']);

  const designNavigation = checkDesignNavigation(url, 'web');
  const assets = new Set([...html.matchAll(/(?:href|src)="([^"#][^"]*)"/g)].map(match => match[1]));
  const fontAssets = evaluate(async () => {
    await document.fonts.ready;
    const loaded = await Promise.all([
      document.fonts.load('400 16px "netfyr sans"'),
      document.fonts.load('600 16px "netfyr sans"'),
      document.fonts.load('400 16px "netfyr mono"'),
    ]);
    return { loaded: loaded.map(faces => faces.length), resources: performance.getEntriesByType('resource').map(entry => entry.name) };
  });
  assert.ok(fontAssets.loaded.every(count => count > 0), 'Gallery fonts must load locally');
  fontAssets.resources.forEach(asset => {
    assert.equal(new URL(asset).origin, url.origin, 'Remote gallery resource: ' + asset);
    assert.ok(new URL(asset).pathname.startsWith(url.pathname), 'Loaded resource escapes the gallery: ' + asset);
    assets.add(asset);
  });
  for (const asset of assets) {
    const target = new URL(asset, url);
    if (target.origin !== url.origin || designNavigation.has(target.href)) continue;
    assert.ok(target.pathname.startsWith(url.pathname), 'Asset escapes deployment subpath: ' + target.href);
    const response = await fetch(target, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
    assert.equal(response.status, 200, 'Broken gallery asset: ' + target.href);
  }
  await checkProgressiveShell(url);
  checkShell(url);
  checkTheme(url);
  await checkTuiCatalogue(url);

  click('#demo-form button[type=submit]');
  wait(() => document.querySelector('#demo-name').getAttribute('aria-invalid') === 'true');
  assert.equal(evaluate(() => document.activeElement.id), 'demo-name');
  browser(['fill', '#demo-name', 'Example workspace']);
  browser(['fill', '#demo-email', 'invalid']);
  browser(['fill', '#demo-description', 'Retain this draft after correction.']);
  click('#demo-form button[type=submit]');
  assert.equal(evaluate(() => document.querySelector('#demo-email').getAttribute('aria-invalid')), 'true');
  assert.equal(evaluate(() => document.querySelector('#demo-description').value), 'Retain this draft after correction.');
  browser(['fill', '#demo-email', 'person@example.test']);
  click('#demo-form button[type=submit]');
  wait(() => document.querySelector('#demo-form-status').textContent.trim().length > 0);
  assert.ok(evaluate(() => [...document.querySelectorAll('#demo-form [aria-invalid]')].every(field => field.getAttribute('aria-invalid') !== 'true')));
  click('#demo-form button[type=reset]');
  assert.equal(evaluate(() => document.querySelector('#demo-name').value), '');
  assert.equal(evaluate(() => document.querySelector('#demo-form-status').textContent.trim()), '');
  assert.ok(evaluate(() => [...document.querySelectorAll('#demo-form [aria-invalid]')].every(field => field.getAttribute('aria-invalid') !== 'true')));

  const switchBefore = evaluate(() => document.querySelector('#demo-motion').checked);
  browser(['focus', '#demo-motion']);
  browser(['press', 'Space']);
  assert.equal(evaluate(() => document.querySelector('#demo-motion').checked), !switchBefore);
  const density = evaluate(() => [...document.querySelector('#demo-density').options].find(option => !option.selected && !option.disabled).value);
  browser(['select', '#demo-density', density]);
  assert.equal(evaluate(() => document.querySelector('#demo-density').value), density);

  click('#demo-tab-overview');
  browser(['press', 'ArrowRight']);
  assert.deepEqual(tabState('#demo-tabs').selected, ['demo-tab-activity']);
  assert.equal(tabState('#demo-tabs').focus, 'demo-tab-activity');
  browser(['press', 'ArrowRight']);
  assert.deepEqual(tabState('#demo-tabs').selected, ['demo-tab-overview'], 'Arrow navigation must skip the disabled tab and wrap');
  browser(['press', 'End']);
  assert.deepEqual(tabState('#demo-tabs').selected, ['demo-tab-activity']);
  browser(['press', 'Home']);
  assert.deepEqual(tabState('#demo-tabs').selected, ['demo-tab-overview']);
  assert.equal(tabState('#demo-tabs').visible.length, 1);
  browser(['press', 'Tab']);
  assert.ok(evaluate(() => document.activeElement.closest('[role=tablist]') === null), 'Tab must leave the tablist');

  click('#demo-open-dialog');
  wait(() => document.querySelector('#demo-dialog').open);
  assert.equal(evaluate(() => document.activeElement.id), 'demo-dialog-cancel', 'Cancel receives initial focus');
  browser(['press', 'Shift+Tab']);
  const modalFocus = evaluate(() => ({
    inside: document.querySelector('#demo-dialog').contains(document.activeElement),
    body: document.activeElement === document.body,
    active: document.activeElement.outerHTML.slice(0, 200),
  }));
  assert.ok(modalFocus.inside || modalFocus.body, 'Modal focus entered an outside control: ' + JSON.stringify(modalFocus));
  browser(['press', 'Tab']);
  assert.ok(evaluate(() => document.querySelector('#demo-dialog').contains(document.activeElement)), 'Modal focus escaped forward');
  assert.ok(evaluate(() => {
    document.querySelector('#demo-name').focus();
    return document.querySelector('#demo-dialog').contains(document.activeElement);
  }), 'Outside page controls remain focusable during the modal');
  browser(['press', 'Escape']);
  wait(() => !document.querySelector('#demo-dialog').open);
  assert.equal(evaluate(() => document.activeElement.id), 'demo-open-dialog');
  click('#demo-open-dialog');
  click('#demo-dialog-cancel');
  assert.equal(evaluate(() => document.querySelector('#demo-dialog').returnValue), 'cancel');
  assert.equal(evaluate(() => document.activeElement.id), 'demo-open-dialog');
  click('#demo-open-dialog');
  click('#demo-dialog-confirm');
  wait(() => !document.querySelector('#demo-dialog').open);
  assert.equal(evaluate(() => document.querySelector('#demo-dialog').returnValue), 'confirm');
  assert.ok(evaluate(() => document.querySelector('#demo-dialog-status').textContent.trim().length > 0));
  assert.equal(evaluate(() => document.activeElement.id), 'demo-open-dialog');

  const beforeRetry = evaluate(() => document.querySelector('#demo-feedback-status').textContent);
  click('#demo-retry');
  wait(before => document.querySelector('#demo-feedback-status').textContent !== before, beforeRetry);
  const rows = evaluate(() => [...document.querySelectorAll('#demo-table-body tr')].map(row => row.innerText));
  assert.ok(rows.length > 1, 'Table fixture needs comparable rows');
  browser(['fill', '#demo-table-filter', rows[0].split('\t')[0].trim()]);
  assert.ok(evaluate(() => [...document.querySelectorAll('#demo-table-body tr:not([hidden])')].length > 0));
  browser(['fill', '#demo-table-filter', 'no-matching-row-8273']);
  assert.equal(evaluate(() => document.querySelectorAll('#demo-table-body tr:not([hidden])').length), 0);
  assert.match(evaluate(() => document.querySelector('#demo-table-count').textContent), /0|no/i);
  browser(['fill', '#demo-table-filter', '']);
  assert.equal(evaluate(() => document.querySelectorAll('#demo-table-body tr:not([hidden])').length), rows.length);
  assert.ok(evaluate(() => {
    const table = document.querySelector('#demo-table-body').closest('table');
    const nameCells = [table.querySelector('thead th'), ...table.querySelectorAll('tbody th')];
    return nameCells.every(cell => ['start', 'left'].includes(getComputedStyle(cell).textAlign));
  }), 'Table names and their column heading must share left alignment');

  const codeText = checkCodebox();

  await checkIsolatedHost(url);
  checkHighlighting(url);
  for (const mode of ['light', 'dark']) {
      setMode(mode);
      const contrast = evaluate(() => {
        function luminance(color) {
          const channels = color.match(/[\d.]+/g).slice(0, 3).map(Number)
            .map(value => value / 255).map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4);
          return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2];
        }
        function ratio(first, second) {
          const [low, high] = [luminance(first), luminance(second)].sort((a, b) => a - b);
          return (high + .05) / (low + .05);
        }
        const field = getComputedStyle(document.querySelector('#demo-name'));
        const button = getComputedStyle(document.querySelector('#demo-add'));
        const theme = getComputedStyle(document.querySelector('#gallery-theme-toggle'));
        const topbar = getComputedStyle(document.querySelector('.gallery-topbar'));
        const statuses = [];
        for (const role of ['success', 'warning', 'danger']) {
          const probe = document.createElement('span');
          probe.style.color = 'var(--ui-' + role + ')';
          document.body.append(probe);
          const expected = getComputedStyle(probe).color;
          probe.remove();
          const badge = document.querySelector('#feedback .ui-badge--' + role);
          const notice = document.createElement('div');
          notice.className = 'ui-notice ui-notice--' + role;
          notice.textContent = role;
          document.body.append(notice);
          for (const [kind, element] of [['badge', badge], ['notice', notice]]) {
            const style = getComputedStyle(element);
            statuses.push({
              kind, role, expected, color: style.color, border: style.borderTopColor,
              contrast: ratio(style.color, style.backgroundColor),
            });
          }
          notice.remove();
        }
        return {
          input: ratio(field.color, field.backgroundColor),
          border: ratio(field.borderTopColor, field.backgroundColor),
          button: ratio(button.color, button.backgroundColor),
          theme: ratio(theme.color, topbar.backgroundColor),
          statuses,
          tokens: [...document.querySelectorAll('pre.ui-code code span')].map(token => ({
            name: token.className,
            contrast: ratio(getComputedStyle(token).color, getComputedStyle(token.closest('pre')).backgroundColor),
          })),
        };
      });
      assert.ok(contrast.input >= 4.5 && contrast.button >= 4.5 && contrast.border >= 3,
        'Control contrast fails in ' + mode + ': ' + JSON.stringify(contrast));
      assert.ok(contrast.theme >= 3, 'Theme icon contrast fails in ' + mode);
      for (const state of contrast.statuses) {
        const label = mode + ' ' + state.role + ' ' + state.kind;
        assert.equal(state.color, state.expected, label + ' does not use its semantic color');
        assert.equal(state.border, state.expected, label + ' border does not use its semantic color');
        assert.ok(state.contrast >= 4.5, label + ' text contrast is ' + state.contrast);
      }
      assert.ok(contrast.tokens.length > 0, 'Code examples have no highlighted tokens');
      for (const token of contrast.tokens) assert.ok(token.contrast >= 4.5,
        mode + ' syntax token ' + token.name + ' text contrast is ' + token.contrast);
      for (const width of [320, 375, 768, 1440]) {
        browser(['set', 'viewport', String(width), '1000']);
        assert.ok(evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1),
          'Page overflows at ' + width + 'px in ' + mode);
        assertCodeboxLayout(codeText, width <= 375);
      }
  }
  browser(['set', 'viewport', '375', '900']);
  evaluate(() => {
    window.scaledText = [...document.querySelectorAll('body, body *')]
      .filter(element => element instanceof HTMLElement)
      .map(element => [element, element.style.fontSize, parseFloat(getComputedStyle(element).fontSize)]);
    for (const [element, , size] of window.scaledText) element.style.fontSize = size * 2 + 'px';
  });
  assert.ok(evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1), '200% text overflows the page');
  assertCodeboxLayout(codeText, true);
  evaluate(() => {
    for (const [element, original] of window.scaledText) element.style.fontSize = original;
    delete window.scaledText;
  });
  browser(['set', 'media', 'light', 'reduced-motion']);
  assert.equal(evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches), true);
  browser(['focus', '#navigation .ui-brand']);
  assert.equal(evaluate(() => getComputedStyle(document.querySelector('#navigation .ui-brand-mark')).animationName), 'none',
    'Reduced motion must disable brand animation');
  click('#demo-open-dialog');
  browser(['press', 'Escape']);
  assert.equal(evaluate(() => document.querySelector('#demo-dialog').open), false);
  cdp = await connectCDP(url);
  await cdp.send('Emulation.setEmulatedMedia', { features: [
    { name: 'forced-colors', value: 'active' }, { name: 'prefers-reduced-motion', value: 'reduce' },
  ] });
  assert.equal(evaluate(() => matchMedia('(forced-colors: active)').matches), true);
  browser(['focus', '#demo-motion']);
  browser(['press', 'Space']);
  assert.ok(evaluate(() => {
    const style = getComputedStyle(document.querySelector('#demo-motion'));
    return style.outlineStyle !== 'none' && parseFloat(style.outlineWidth) > 0;
  }), 'Forced colors must retain visible keyboard focus');
  browser(['focus', '#gallery-theme-toggle']);
  assert.ok(evaluate(() => {
    const button = document.querySelector('#gallery-theme-toggle');
    const style = getComputedStyle(button);
    const icon = getComputedStyle(button.querySelector('svg:not([hidden])'));
    return style.outlineStyle !== 'none' && parseFloat(style.outlineWidth) > 0
      && icon.stroke !== 'none' && icon.display !== 'none';
  }), 'Forced colors must retain the theme icon and keyboard focus');
  assert.ok(evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1), 'Forced colors overflow the page');
  console.log('Web library: packed exports, local assets, forms, selection, tabs, dialogs, retry, filtering, syntax highlighting and exact code copying pass.');
  console.log('Theme toggle, mobile navigation, host isolation, lifecycle, four viewport sizes, light/dark modes, 200% text, reduced motion and forced colors pass.');
  console.log('TUI catalogue: Rust frame playback, GIF recordings, motion controls, visibility, reduced motion, source copying and surface navigation pass under a deployment subpath.');
} finally {
  cdp?.close();
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

function checkDesignNavigation(url, surface) {
  const home = new URL('../', url);
  const pages = ['overview', 'typography', 'colors', 'spacing', 'brand', 'resources'];
  const navigation = evaluate(() => ({
    site: [...document.querySelectorAll('.gallery-site-links [data-design-page]')].map(link => link.dataset.designPage),
    links: [...document.querySelectorAll('[data-design-page]')].map(link => ({ page: link.dataset.designPage, href: link.href })),
    current: [...document.querySelectorAll('.gallery-site-links [aria-current]')].map(link => [link.dataset.surface, link.getAttribute('aria-current')]),
    categories: [...document.querySelectorAll('.gallery-site-links [data-surface]')].map(link => [link.dataset.surface, link.textContent.trim()]),
    subtitle: document.querySelector('.gallery-brand .ui-brand-subtitle').textContent,
    home: document.querySelector('.gallery-brand').href,
    footer: document.querySelector('.gallery-footer .ui-footer-brand').textContent.trim(),
    local: document.querySelectorAll('.gallery-component-links [aria-current="location"]').length,
  }));
  assert.deepEqual(navigation.site, pages, 'Each catalogue must expose the same design-library pages');
  assert.deepEqual(navigation.categories, [['web', 'Web components'], ['tui', 'TUI components']]);
  assert.deepEqual(navigation.current, [[surface, 'page']], 'Only the current category is the current page');
  assert.equal(navigation.local, 1, 'The component location is independent of the current category');
  assert.equal(navigation.subtitle, 'design library');
  assert.equal(navigation.home, new URL('#overview', home).href);
  assert.equal(navigation.footer, 'netfyr design library');
  for (const link of navigation.links) {
    assert.ok(pages.includes(link.page), 'Unknown design page link: ' + link.page);
    assert.equal(link.href, new URL('#' + link.page, home).href, 'Design links must stay within the site deployment');
  }
  if (surface === 'web') {
    assert.equal(evaluate(() => document.querySelector('#navigation .ui-nav-links a[aria-label$="(external site)"]').href),
      'https://github.com/netfyr/design', 'The external-link example must remain external to the design site');
  }
  return new Set(navigation.links.map(link => link.href));
}

async function checkProgressiveShell(url) {
  const media = await connectCDP(url);
  const pages = [url, new URL('tui/', url)];
  try {
    await media.send('Network.enable');
    await media.send('Network.setCacheDisabled', { cacheDisabled: true });
    await media.send('Network.setBlockedURLs', { urls: ['*/gallery.js'] });
    for (const [index, page] of pages.entries()) {
      const selected = index === 0 ? 'light' : 'dark';
      evaluate(mode => localStorage.setItem('netfyr-theme', mode), selected);
      await media.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: selected === 'light' ? 'dark' : 'light' }] });
      browser(['open', page.href]);
      assert.equal(evaluate(() => document.body.dataset.uiMode), selected,
        'The saved theme must apply before the gallery module loads');
      assert.equal(evaluate(() => getComputedStyle(document.body).backgroundColor), selected === 'dark' ? 'rgb(33, 28, 25)' : 'rgb(250, 248, 244)');
      assert.ok(evaluate(() => !document.documentElement.classList.contains('has-navigation')
        && document.querySelector('#gallery-theme-toggle').hidden), 'The blocked module must leave the static shell usable');
    }
    await media.send('Emulation.setScriptExecutionDisabled', { value: true });
    browser(['set', 'viewport', '375', '900']);
    for (const page of pages) {
      browser(['open', page.href]);
      for (const mode of ['dark', 'light']) {
        await media.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: mode }] });
        assert.equal(evaluate(() => document.body.hasAttribute('data-ui-mode')), false, 'No-JavaScript check unexpectedly ran the theme initializer');
        assert.equal(evaluate(() => getComputedStyle(document.body).backgroundColor), mode === 'dark' ? 'rgb(33, 28, 25)' : 'rgb(250, 248, 244)',
          'Without JavaScript, the gallery must follow the operating-system theme');
        assert.ok(evaluate(() => {
          const sidebar = document.querySelector('#gallery-sidebar');
          const style = getComputedStyle(sidebar);
          return !sidebar.inert && style.visibility === 'visible' && style.position === 'static'
            && sidebar.getBoundingClientRect().width <= innerWidth
            && getComputedStyle(document.querySelector('#gallery-open-menu')).display === 'none'
            && getComputedStyle(document.querySelector('#gallery-close-menu')).display === 'none'
            && [...sidebar.querySelectorAll('a')].every(link => link.getClientRects().length > 0);
        }), 'Mobile catalogue navigation must remain reachable without JavaScript');
      }
    }
  } finally {
    await media.send('Emulation.setScriptExecutionDisabled', { value: false });
    await media.send('Network.setBlockedURLs', { urls: [] });
    await media.send('Network.setCacheDisabled', { cacheDisabled: false });
    await media.send('Emulation.setEmulatedMedia', { features: [] });
    media.close();
    browser(['set', 'viewport', '1440', '1000']);
    browser(['open', url.href]);
    wait(() => document.documentElement.dataset.galleryReady === 'true');
  }
}

async function checkTuiCatalogue(url) {
  const tuiUrl = new URL('tui/', url);
  const redirect = await fetch(new URL('tui?preview=1', url), {
    redirect: 'manual', signal: AbortSignal.timeout(5000),
  });
  assert.equal(redirect.status, 308, 'TUI directory route must preserve relative asset resolution');
  assert.equal(redirect.headers.get('location'), tuiUrl.pathname + '?preview=1');
  for (const relative of ['tui/', 'tui/index.html']) {
    const response = await fetch(new URL(relative, url), { method: 'HEAD', signal: AbortSignal.timeout(5000) });
    assert.equal(response.status, 200, 'Missing TUI page route: ' + relative);
    assert.match(response.headers.get('content-type'), /^text\/html/);
  }
  assert.equal((await fetch(new URL('tui/screenshots/', url), { signal: AbortSignal.timeout(5000) })).status, 404,
    'Only explicitly published directory indexes may be served');
  assert.equal(evaluate(() => document.querySelector('.gallery-site-links [aria-current="page"]').dataset.surface), 'web');
  setMode('dark');
  click('.gallery-site-links a[data-surface="tui"]');
  wait(expected => location.pathname === expected && document.documentElement.dataset.galleryReady === 'true', tuiUrl.pathname);
  assert.equal(evaluate(() => document.body.dataset.uiMode), 'dark', 'Changing catalogue lost the chosen theme');
  assert.equal(evaluate(() => document.querySelector('.gallery-site-links [aria-current="page"]').dataset.surface), 'tui');
  assert.ok(evaluate(() => document.querySelector('.gallery-sidebar nav a[href="#footer"]').getAttribute('aria-current') === 'location'),
    'Component location must be separate from the current catalogue page');

  assert.deepEqual(evaluate(() => [...document.querySelectorAll('.gallery-component-links > a')]
    .map(link => [link.hash, link.textContent.trim()])), [
    ['#footer', 'Action footer'], ['#activity', 'Activity indicators'], ['#dropdown', 'Dropdown'],
    ['#flame', 'Flame'], ['#glyphs', 'Glyphs'], ['#settings', 'Settings row'], ['#replay', 'Trace replay'], ['#traffic', 'Traffic lanes'],
  ], 'TUI components must stay in alphabetical navigation order');

  const designNavigation = checkDesignNavigation(url, 'tui');
  const pageHtml = await readFile(path.join(root, 'dist/tui/index.html'), 'utf8');
  const resources = new Set([...pageHtml.matchAll(/(?:href|src)="([^"#][^"]*)"/g)].map(match => new URL(match[1], tuiUrl).href));
  const loaded = evaluate(async () => {
    await document.fonts.ready;
    return {
      fonts: (await Promise.all(['netfyr sans', 'netfyr mono'].map(name => document.fonts.load('400 16px "' + name + '"'))))
        .map(faces => faces.length),
      resources: performance.getEntriesByType('resource').map(entry => entry.name),
    };
  });
  assert.ok(loaded.fonts.every(count => count > 0), 'TUI catalogue fonts must load locally');
  for (const resource of loaded.resources) {
    assert.equal(new URL(resource).origin, url.origin, 'Remote TUI resource: ' + resource);
    assert.ok(new URL(resource).pathname.startsWith(url.pathname), 'Loaded TUI resource escapes the gallery: ' + resource);
    resources.add(resource);
  }
  for (const resource of resources) {
    const target = new URL(resource);
    if (target.origin !== url.origin || designNavigation.has(target.href)) continue;
    assert.ok(target.pathname.startsWith(url.pathname), 'TUI asset escapes deployment subpath: ' + resource);
    const response = await fetch(target, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
    assert.equal(response.status, 200, 'Broken TUI catalogue asset: ' + resource);
    if (target.pathname.endsWith('.png')) assert.equal(response.headers.get('content-type'), 'image/png');
    if (target.pathname.endsWith('.gif')) assert.equal(response.headers.get('content-type'), 'image/gif');
  }
  await checkTuiRecordings(tuiUrl);

  await checkTuiPreviews(tuiUrl);
  await checkTuiGlyphFallback(tuiUrl);

  click('#tui-run-gallery > summary');
  const command = evaluate(() => {
    const element = document.querySelector('#tui-gallery-command');
    window.tuiClipboardWrite = navigator.clipboard.writeText;
    navigator.clipboard.writeText = async text => { window.tuiCopiedCommand = text; };
    return (element.querySelector('code') || element).textContent;
  });
  assert.match(command, /cargo run --locked --manifest-path tui\/Cargo\.toml --example gallery/);
  try {
    click('#tui-run-gallery [data-ui-copy]');
    wait(expected => window.tuiCopiedCommand === expected, command);
  } finally {
    evaluate(() => {
      navigator.clipboard.writeText = window.tuiClipboardWrite;
      delete window.tuiClipboardWrite;
      delete window.tuiCopiedCommand;
    });
  }
  for (const mode of ['light', 'dark']) {
    setMode(mode);
    for (const width of [320, 375, 768, 1440]) {
      browser(['set', 'viewport', String(width), '1000']);
      assert.ok(evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1),
        'TUI catalogue overflows at ' + width + 'px in ' + mode);
      assert.ok(evaluate(() => [...document.querySelectorAll('[data-tui-recording] img')].every(image => {
        const box = image.getBoundingClientRect();
        return box.width > 0 && box.left >= -1 && box.right <= innerWidth + 1;
      })), 'TUI recordings escape the viewport at ' + width + 'px in ' + mode);
      assert.ok(evaluate(() => [...document.querySelectorAll('[data-tui-preview] svg')].every(svg => {
        const box = svg.getBoundingClientRect();
        return box.width > 0 && box.left >= -1 && box.right <= innerWidth + 1;
      })), 'TUI frame previews escape the viewport at ' + width + 'px in ' + mode);
    }
  }
  browser(['set', 'viewport', '375', '900']);
  wait(() => document.querySelector('#gallery-sidebar').inert);
  click('#gallery-open-menu');
  wait(() => document.activeElement.id === 'gallery-close-menu');
  assert.ok(evaluate(() => document.querySelector('.gallery-workspace').inert
    && document.querySelector('#gallery-sidebar').getAttribute('aria-modal') === 'true'));
  browser(['press', 'Escape']);
  assert.equal(evaluate(() => document.activeElement.id), 'gallery-open-menu');
  click('#gallery-open-menu');
  click('.gallery-sidebar nav a[href="#dropdown"]');
  wait(() => document.activeElement === document.querySelector('#dropdown h2'));
  assert.ok(evaluate(() => document.querySelector('#gallery-sidebar').inert
    && !document.querySelector('.gallery-workspace').inert));
  click('#gallery-open-menu');
  click('.gallery-site-links a[data-surface="web"]');
  wait(expected => location.pathname === expected && document.documentElement.dataset.galleryReady === 'true', url.pathname);
  assert.equal(evaluate(() => document.body.dataset.uiMode), 'dark', 'Returning to Web lost the chosen theme');
  assert.equal(evaluate(() => document.querySelector('.gallery-site-links [aria-current="page"]').dataset.surface), 'web');
  assert.ok(evaluate(() => document.querySelector('#gallery-sidebar').inert
    && !document.querySelector('.gallery-workspace').inert), 'Changing catalogue retained the previous mobile modal state');
  browser(['set', 'viewport', '1440', '1000']);
  wait(() => !document.querySelector('#gallery-sidebar').inert);
  setMode('light');
}

function checkGifRecording(data) {
  let offset = 0, frames = 0;
  function take(length) {
    assert.ok(offset + length <= data.length, 'Truncated GIF block');
    const block = data.subarray(offset, offset + length);
    offset += length;
    return block;
  }
  function palette(packed) {
    if (packed & 0x80) take(3 * 2 ** ((packed & 7) + 1));
  }
  function subblocks() {
    for (let length; (length = take(1)[0]) !== 0;) take(length);
  }
  const header = take(13);
  assert.match(header.toString('ascii', 0, 6), /^GIF8[79]a$/, 'Recording is not a GIF file');
  const width = header.readUInt16LE(6), height = header.readUInt16LE(8);
  assert.deepEqual([width, height], [624, 480]);
  palette(header[10]);
  for (;;) {
    const block = take(1)[0];
    if (block === 0x3b) break;
    if (block === 0x21) {
      take(1);
      subblocks();
      continue;
    }
    assert.equal(block, 0x2c, 'Unexpected GIF block');
    const descriptor = take(9);
    const left = descriptor.readUInt16LE(0), top = descriptor.readUInt16LE(2);
    const frameWidth = descriptor.readUInt16LE(4), frameHeight = descriptor.readUInt16LE(6);
    assert.ok(frameWidth > 0 && frameHeight > 0 && left + frameWidth <= width && top + frameHeight <= height,
      'GIF frame escapes the recording dimensions');
    palette(descriptor[8]);
    const codeSize = take(1)[0];
    assert.ok(codeSize >= 2 && codeSize <= 8, 'Invalid GIF LZW code size');
    subblocks();
    frames++;
  }
  assert.equal(offset, data.length, 'Unexpected data after GIF trailer');
  assert.ok(frames >= 2, 'Recording must contain multiple GIF frames');
}

async function checkTuiRecordings(tuiUrl) {
  const ids = ['dropdown-choice', 'dropdown-interfaces', 'dropdown-empty', 'dropdown-loading', 'dropdown-failed', 'settings'];
  const recordings = evaluate(() => [...document.querySelectorAll('[data-tui-recording]')].map(host => {
    const image = host.querySelector('img');
    return {
      id: host.dataset.tuiRecording, alt: image.alt,
      gif: new URL(image.dataset.gif, location.href).href,
      poster: new URL(image.dataset.poster, location.href).href,
      link: image.closest('a')?.href,
      labelledButton: !!host.querySelector('[data-recording-toggle]')?.getAttribute('aria-label')?.trim(),
    };
  }));
  assert.deepEqual(recordings.map(recording => recording.id), ids);
  for (const recording of recordings) {
    assert.ok(recording.alt.trim() && recording.labelledButton, 'Recording requires text alternatives and a labelled control: ' + recording.id);
    assert.equal(recording.link, recording.gif, 'Recording must link to its full-size GIF');
    assert.equal(recording.gif, new URL('screenshots/' + recording.id + '.gif', tuiUrl).href);
    assert.equal(recording.poster, new URL('screenshots/' + recording.id + '.png', tuiUrl).href);
    for (const [source, type] of [[recording.gif, 'image/gif'], [recording.poster, 'image/png']]) {
      assert.ok(source.startsWith(tuiUrl.href), 'Recording resource escapes its deployment path');
      const response = await fetch(source, { signal: AbortSignal.timeout(5000) });
      assert.equal(response.status, 200, 'Missing recording resource: ' + source);
      assert.equal(response.headers.get('content-type'), type);
      if (type === 'image/gif') {
        checkGifRecording(Buffer.from(await response.arrayBuffer()));
      }
    }
  }

  const selector = id => '[data-tui-recording="' + id + '"]';
  function position(id) {
    evaluate(id => document.querySelector('[data-tui-recording="' + id + '"]')
      .scrollIntoView({ behavior: 'instant', block: 'center' }), id);
  }
  function showing(id, kind) {
    wait(({ id, kind }) => {
      const image = document.querySelector('[data-tui-recording="' + id + '"] img');
      return image.src === new URL(image.dataset[kind], location.href).href
        && image.complete && image.naturalWidth === 624 && image.naturalHeight === 480;
    }, { id, kind });
  }
  const media = await connectCDP(tuiUrl);
  let backgroundTarget;
  try {
    await media.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
    wait(() => matchMedia('(prefers-reduced-motion: reduce)').matches
      && [...document.querySelectorAll('[data-recording-toggle]')].every(button => button.textContent === 'Play'));
    for (const id of ids) {
      position(id);
      showing(id, 'poster');
      browser(['focus', selector(id) + ' [data-recording-toggle]']);
      browser(['press', 'Enter']);
      showing(id, 'gif');
      assert.equal(evaluate(id => document.querySelector('[data-tui-recording="' + id + '"] [data-recording-toggle]').textContent, id), 'Stop');
      browser(['press', 'Space']);
      showing(id, 'poster');
      assert.equal(evaluate(id => document.querySelector('[data-tui-recording="' + id + '"] [data-recording-toggle]').textContent, id), 'Play');
    }

    await media.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }] });
    for (const id of ids) {
      position(id);
      showing(id, 'gif');
    }
    const first = ids[0];
    position(first);
    showing(first, 'gif');
    click(selector(first) + ' [data-recording-toggle]');
    showing(first, 'poster');
    position('settings');
    showing('settings', 'gif');
    position(first);
    showing(first, 'poster');
    assert.equal(evaluate(id => document.querySelector('[data-tui-recording="' + id + '"] [data-recording-toggle]').textContent, first), 'Play',
      'Manual Stop must remain stopped when the recording re-enters the viewport');
    click(selector(first) + ' [data-recording-toggle]');
    showing(first, 'gif');
    position('settings');
    wait(() => document.querySelector('[data-tui-recording="dropdown-choice"]').getBoundingClientRect().bottom < 0);
    showing(first, 'poster');
    position(first);
    showing(first, 'gif');

    ({ targetId: backgroundTarget } = await media.send('Target.createTarget', { url: 'about:blank' }));
    await media.send('Target.activateTarget', { targetId: backgroundTarget });
    const hidden = await media.send('Runtime.evaluate', {
      expression: `new Promise(resolve => {
        const stopped = () => document.hidden && [...document.querySelectorAll('[data-tui-recording] img')]
          .every(image => image.src === new URL(image.dataset.poster, location.href).href);
        if (stopped()) return resolve(true);
        document.addEventListener('visibilitychange', () => setTimeout(() => resolve(stopped()), 0), { once: true });
        setTimeout(() => resolve(stopped()), 1500);
      })`, awaitPromise: true, returnByValue: true,
    });
    assert.equal(hidden.result.value, true, 'A hidden page must replace all GIFs with static posters');
    await media.send('Target.activateTarget', { targetId: media.targetId });
    await media.send('Target.closeTarget', { targetId: backgroundTarget });
    backgroundTarget = undefined;
    wait(() => !document.hidden);
    showing(first, 'gif');
  } finally {
    if (backgroundTarget) {
      await media.send('Target.activateTarget', { targetId: media.targetId });
      await media.send('Target.closeTarget', { targetId: backgroundTarget });
    }
    await media.send('Emulation.setEmulatedMedia', { features: [] });
    media.close();
  }
}

async function checkTuiPreviews(tuiUrl) {
  const response = await fetch(new URL('previews.json', tuiUrl), { signal: AbortSignal.timeout(5000) });
  assert.equal(response.status, 200, 'Missing exported Rust frame data');
  assert.match(response.headers.get('content-type'), /^application\/json\b/);
  const exported = await response.json();
  const animated = ['activity', 'flame', 'replay', 'traffic'];
  const ids = ['footer', 'activity', 'flame', 'glyphs', 'replay', 'traffic'];
  wait(() => [...document.querySelectorAll('[data-tui-preview]')].every(host => host.dataset.ready === 'true'));
  const hosts = evaluate(() => [...document.querySelectorAll('[data-tui-preview]')].map(host => ({
    id: host.dataset.tuiPreview, ready: host.dataset.ready,
    labelled: host.querySelector('svg[role="img"]')?.getAttribute('aria-label')?.trim(),
    text: host.querySelectorAll('svg text').length,
    button: !!host.querySelector('.gallery-tui-toolbar button'),
  })));
  assert.deepEqual(hosts.map(host => host.id), ids);
  for (const host of hosts) {
    assert.equal(host.ready, 'true');
    assert.ok(host.labelled && host.text > 0, 'Preview must have a label and actual rendered text: ' + host.id);
    assert.equal(host.button, animated.includes(host.id), 'Only animated previews need playback controls: ' + host.id);
  }
  const glyphs = evaluate(() => {
    const host = document.querySelector('[data-tui-preview="glyphs"]');
    return { mode: host.dataset.glyphs, characters: [...host.querySelectorAll('svg text')]
      .filter(text => /[\u{100000}-\u{100004}]/u.test(text.textContent))
      .map(text => ({ text: text.textContent, width: Number(text.getAttribute('textLength')) })) };
  });
  assert.equal(glyphs.mode, 'netfyr', 'The bundled font should enable its custom glyphs');
  assert.deepEqual(glyphs.characters, ['\u{100000}', '\u{100001}', '\u{100002}', '\u{100003}', '\u{100004}']
    .map(text => ({ text, width: 10 })), 'Custom glyphs must retain one terminal cell each');
  for (const id of ['footer', 'glyphs', 'settings']) {
    click('#' + id + ' .gallery-source > summary');
    const source = evaluate(id => {
      const box = document.querySelector('#' + id + ' .ui-codebox');
      window.tuiSourceClipboard = navigator.clipboard.writeText;
      navigator.clipboard.writeText = async text => { window.tuiSourceCopy = text; };
      return { text: box.querySelector('code').textContent, tokens: box.querySelectorAll('code span').length };
    }, id);
    assert.ok(source.tokens > 0, 'Rust source should use syntax highlighting');
    try {
      click('#' + id + ' [data-ui-copy]');
      wait(expected => window.tuiSourceCopy === expected, source.text);
    } finally {
      evaluate(() => {
        navigator.clipboard.writeText = window.tuiSourceClipboard;
        delete window.tuiSourceClipboard;
        delete window.tuiSourceCopy;
      });
    }
    click('#' + id + ' .gallery-source > summary');
  }

  const selector = id => '[data-tui-preview="' + id + '"]';
  const duration = id => Math.max(160, Math.min(1000,
    exported.previews.find(preview => preview.id === id).intervalMs * 3));
  function position(id) {
    evaluate(id => document.querySelector('[data-tui-preview="' + id + '"]')
      .scrollIntoView({ behavior: 'instant', block: 'center' }), id);
  }
  function advances(id) {
    wait(id => Number(document.querySelector('[data-tui-preview="' + id + '"]').dataset.frame) >= 0, id);
    const before = evaluate(id => document.querySelector('[data-tui-preview="' + id + '"] svg').innerHTML, id);
    wait(({ id, before }) => document.querySelector('[data-tui-preview="' + id + '"] svg').innerHTML !== before, { id, before });
  }
  function unchanged(id, message) {
    const state = evaluate(async ({ id, duration }) => {
      const host = document.querySelector('[data-tui-preview="' + id + '"]');
      const svg = host.querySelector('svg');
      const before = { frame: host.dataset.frame, content: svg.innerHTML };
      let changes = 0;
      const observer = new MutationObserver(() => { changes++; });
      observer.observe(svg, { childList: true, subtree: true, attributes: true, characterData: true });
      await new Promise(resolve => setTimeout(resolve, duration));
      observer.disconnect();
      return { before, after: { frame: host.dataset.frame, content: svg.innerHTML }, changes };
    }, { id, duration: duration(id) });
    assert.deepEqual(state.after, state.before, message);
    assert.equal(state.changes, 0, message);
  }

  const media = await connectCDP(tuiUrl);
  let backgroundTarget;
  try {
    await media.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
    wait(() => matchMedia('(prefers-reduced-motion: reduce)').matches
      && [...document.querySelectorAll('.gallery-tui-toolbar button')].every(button => button.textContent === 'Play'));
    for (const preview of exported.previews.filter(preview => ids.includes(preview.id))) {
      const state = evaluate(preview => {
        const host = document.querySelector('[data-tui-preview="' + preview.id + '"]');
        const cellWidth = host.querySelector('svg').viewBox.baseVal.width / preview.columns;
        return { frame: host.dataset.frame, runs: [...host.querySelectorAll('svg text')].map(text => ({
          text: text.textContent, x: Number(text.getAttribute('x')) / cellWidth,
          width: Number(text.getAttribute('textLength')) / cellWidth,
          whitespace: getComputedStyle(text).whiteSpace,
        })) };
      }, { id: preview.id, columns: preview.columns });
      assert.equal(state.frame, '-1', 'Reduced motion must show the still frame: ' + preview.id);
      const runs = preview.still.filter(run => run[3].trim()).map(([x, , , text, width]) => {
        const content = text.replace(/^ +| +$/g, '');
        const leading = text.indexOf(content);
        return { text: content, x: x + leading, width: width - (text.length - content.length), whitespace: 'pre' };
      });
      assert.deepEqual(state.runs, runs,
        'Preview must preserve Rust cell positions without stretching glyphs across blank cells: ' + preview.id);
    }
    position('activity');
    unchanged('activity', 'Reduced motion preview changed without opting in');
    browser(['focus', selector('activity') + ' .gallery-tui-toolbar button']);
    browser(['press', 'Enter']);
    advances('activity');
    assert.equal(evaluate(() => document.querySelector('[data-tui-preview="activity"] button').textContent), 'Pause');
    browser(['press', 'Space']);
    unchanged('activity', 'Keyboard Pause did not freeze the visible preview');

    await media.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }] });
    for (const id of animated) {
      position(id);
      advances(id);
      click(selector(id) + ' .gallery-tui-toolbar button');
      assert.equal(evaluate(id => document.querySelector('[data-tui-preview="' + id + '"] button').textContent, id), 'Play');
      unchanged(id, 'Pause did not freeze the ' + id + ' preview');
      click(selector(id) + ' .gallery-tui-toolbar button');
      advances(id);
    }

    position('activity');
    advances('activity');
    evaluate(() => scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' }));
    wait(() => document.querySelector('[data-tui-preview="activity"]').getBoundingClientRect().bottom < 0);
    evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    unchanged('activity', 'Offscreen playback must stop and retain its frame');
    position('activity');
    advances('activity');

    ({ targetId: backgroundTarget } = await media.send('Target.createTarget', { url: 'about:blank' }));
    await media.send('Target.activateTarget', { targetId: backgroundTarget });
    const hidden = await media.send('Runtime.evaluate', {
      expression: `new Promise(resolve => {
        if (document.hidden) return resolve(true);
        document.addEventListener('visibilitychange', () => resolve(document.hidden), { once: true });
        setTimeout(() => resolve(document.hidden), 1500);
      })`, awaitPromise: true, returnByValue: true,
    });
    assert.equal(hidden.result.value, true, 'Background-tab check requires a real hidden document');
    const capture = () => media.send('Runtime.evaluate', { expression: `JSON.stringify({
      frame: document.querySelector('[data-tui-preview="activity"]').dataset.frame,
      content: document.querySelector('[data-tui-preview="activity"] svg').innerHTML,
    })`, returnByValue: true });
    const hiddenBefore = (await capture()).result.value;
    await new Promise(resolve => setTimeout(resolve, duration('activity')));
    assert.equal((await capture()).result.value, hiddenBefore, 'Hidden document playback must retain its frame');
    await media.send('Target.activateTarget', { targetId: media.targetId });
    await media.send('Target.closeTarget', { targetId: backgroundTarget });
    backgroundTarget = undefined;
    wait(() => !document.hidden);
    advances('activity');
  } finally {
    if (backgroundTarget) {
      await media.send('Target.activateTarget', { targetId: media.targetId });
      await media.send('Target.closeTarget', { targetId: backgroundTarget });
    }
    await media.send('Emulation.setEmulatedMedia', { features: [] });
    media.close();
  }
}

async function checkTuiGlyphFallback(tuiUrl) {
  const response = await fetch(new URL('previews.json', tuiUrl), { signal: AbortSignal.timeout(5000) });
  const preview = (await response.json()).previews.find(preview => preview.id === 'glyphs');
  const expected = preview.fallback.filter(run => run[3].trim()).map(([x, y, , text, width]) => {
    const content = text.replace(/^ +| +$/g, '');
    return { text: content, x: x + text.indexOf(content), y, width: width - (text.length - content.length) };
  });
  const state = () => evaluate(() => {
    const host = document.querySelector('[data-tui-preview="glyphs"]');
    return { mode: host.dataset.glyphs, runs: [...host.querySelectorAll('svg text')].map(text => ({
      text: text.textContent, x: Number(text.getAttribute('x')) / 10,
      y: (Number(text.getAttribute('y')) - 16) / 20,
      width: Number(text.getAttribute('textLength')) / 10,
    })) };
  });
  const media = await connectCDP(tuiUrl);
  try {
    evaluate(() => {
      for (const text of document.querySelectorAll('[data-tui-preview="glyphs"] svg text')) {
        if (/[\u{100000}-\u{100004}]/u.test(text.textContent)) text.dataset.symbolProof = '';
      }
    });
    await media.send('DOM.enable');
    await media.send('CSS.enable');
    const { root } = await media.send('DOM.getDocument');
    const { nodeIds } = await media.send('DOM.querySelectorAll', {
      nodeId: root.nodeId, selector: '[data-symbol-proof]',
    });
    assert.equal(nodeIds.length, 5, 'Each supplementary symbol needs a font rendering check');
    for (const nodeId of nodeIds) {
      const { fonts } = await media.send('CSS.getPlatformFontsForNode', { nodeId });
      assert.equal(fonts.length, 1, 'A symbol must render from one font');
      assert.equal(fonts[0].familyName, 'netfyr symbols');
      assert.equal(fonts[0].isCustomFont, true, 'Symbols must use the bundled companion font');
      assert.equal(fonts[0].glyphCount, 1);
    }
    await media.send('Network.enable');
    await media.send('Network.setCacheDisabled', { cacheDisabled: true });
    await media.send('Network.setBlockedURLs', { urls: ['*assets/fonts/netfyrsymbols-Regular.woff2'] });
    const missingUrl = new URL(tuiUrl);
    missingUrl.searchParams.set('font-check', 'missing');
    browser(['open', missingUrl.href]);
    wait(() => document.documentElement.dataset.galleryReady === 'true');
    assert.ok(evaluate(() => [...document.fonts].some(face => face.family.includes('netfyr symbols') && face.status === 'error')),
      'Fallback check must actually block the bundled font');
    assert.ok(evaluate(() => document.fonts.check('400 16px "netfyr mono"', 'Interfaces')),
      'Missing symbols must not affect the ordinary terminal text font');
    assert.deepEqual(state(), { mode: 'standard', runs: expected },
      'A missing font must retain the Rust-rendered standard glyphs and labels');
    assert.ok(expected.every(run => !/[\ue000-\uf8ff\u{f0000}-\u{ffffd}\u{100000}-\u{10fffd}]/u.test(run.text)),
      'Standard fallback must not depend on private-use font characters');
    await media.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
    wait(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
    evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    assert.deepEqual(state(), { mode: 'standard', runs: expected },
      'Changing motion preferences must not restore unavailable font glyphs');
  } finally {
    await media.send('Network.setBlockedURLs', { urls: [] });
    await media.send('Network.setCacheDisabled', { cacheDisabled: false });
    await media.send('Emulation.setEmulatedMedia', { features: [] });
    media.close();
    browser(['open', tuiUrl.href]);
    wait(() => document.documentElement.dataset.galleryReady === 'true');
  }
  assert.equal(state().mode, 'netfyr', 'Custom glyphs should return when their font loads');
}

function checkShell(url) {
  evaluate(() => localStorage.removeItem('netfyr-theme'));
  browser(['open', url.href]);
  wait(() => document.documentElement.dataset.galleryReady === 'true');
  browser(['set', 'media', 'dark']);
  wait(() => document.body.dataset.uiMode === 'dark');
  assert.equal(evaluate(() => document.querySelector('#gallery-theme-toggle').getAttribute('aria-label')), 'Switch to light theme');
  click('#gallery-theme-toggle');
  wait(() => document.body.dataset.uiMode === 'light');
  assert.equal(evaluate(() => localStorage.getItem('netfyr-theme')), 'light');
  assert.equal(evaluate(() => document.querySelector('#gallery-theme-toggle').getAttribute('aria-label')), 'Switch to dark theme');
  browser(['set', 'media', 'light']);
  browser(['set', 'media', 'dark']);
  assert.equal(evaluate(() => document.body.dataset.uiMode), 'light', 'System changes replaced the chosen theme');
  browser(['open', url.href]);
  wait(() => document.documentElement.dataset.galleryReady === 'true');
  assert.equal(evaluate(() => document.body.dataset.uiMode), 'light', 'Theme choice was lost on reload');
  assert.ok(evaluate(() => document.querySelectorAll('.ui-navigation .ui-brand-logo').length === 2),
    'Gallery sidebar and Navigation example must use the same brand component');
  browser(['hover', '.gallery-brand']);
  assert.ok(evaluate(() => getComputedStyle(document.querySelector('.gallery-brand .ui-brand-mark')).animationName === 'ui-brand-flicker'
    && getComputedStyle(document.querySelector('#navigation .ui-brand-mark')).animationName === 'none'),
  'Hover animation leaked into an independent navigation instance');
  browser(['hover', '#gallery-theme-toggle']);
  browser(['focus', '#navigation .ui-brand']);
  browser(['press', 'Tab']);
  browser(['press', 'Shift+Tab']);
  assert.ok(evaluate(() => getComputedStyle(document.querySelector('#navigation .ui-brand-mark')).animationName === 'ui-brand-flicker'
    && getComputedStyle(document.querySelector('#navigation .ui-brand-logo > path')).animationName === 'none'
    && getComputedStyle(document.querySelector('#navigation .ui-brand-logo')).transform === 'none'),
  'Keyboard focus must animate only the mark');
  browser(['focus', '#gallery-theme-toggle']);

  browser(['set', 'viewport', '375', '900']);
  wait(() => document.querySelector('#gallery-sidebar').inert);
  click('#gallery-open-menu');
  wait(() => document.activeElement.id === 'gallery-close-menu');
  assert.ok(evaluate(() => document.querySelector('.gallery-workspace').inert
    && !document.querySelector('#gallery-sidebar').inert
    && document.querySelector('#gallery-sidebar').getAttribute('aria-modal') === 'true'));
  assert.equal(evaluate(() => document.activeElement.id), 'gallery-close-menu');
  browser(['focus', '.gallery-sidebar-footer a:last-child']);
  browser(['press', 'Tab']);
  assert.ok(evaluate(() => document.activeElement.classList.contains('gallery-brand')), 'Tab escaped the mobile menu');
  browser(['press', 'Shift+Tab']);
  assert.ok(evaluate(() => document.activeElement === document.querySelector('.gallery-sidebar-footer a:last-child')));
  browser(['press', 'Escape']);
  assert.equal(evaluate(() => document.activeElement.id), 'gallery-open-menu');
  assert.ok(evaluate(() => document.querySelector('#gallery-sidebar').inert
    && !document.querySelector('.gallery-workspace').inert));
  click('#gallery-open-menu');
  click('.gallery-sidebar nav a[href="#codebox"]');
  wait(() => document.activeElement.id === 'codebox-heading');
  assert.ok(evaluate(() => document.querySelector('#gallery-sidebar').inert
    && !document.querySelector('.gallery-workspace').inert));
  click('#gallery-open-menu');
  browser(['set', 'viewport', '1440', '1000']);
  wait(() => !document.querySelector('#gallery-sidebar').inert
    && !document.querySelector('.gallery-workspace').inert);
  assert.ok(evaluate(() => document.querySelector('#gallery-sidebar').contains(document.activeElement)
    && document.activeElement.id !== 'gallery-close-menu'), 'Resizing left focus on a hidden menu control');
  browser(['set', 'viewport', '375', '900']);
  wait(() => document.activeElement.id === 'gallery-open-menu');
  browser(['set', 'viewport', '1440', '1000']);
  wait(() => !document.querySelector('#gallery-sidebar').inert);
}

function checkTheme(url) {
  assert.ok(evaluate(() => [...document.querySelectorAll('[data-ui-theme-toggle]')].every(button => {
    const box = button.getBoundingClientRect();
    return button.type === 'button' && box.width >= 44 && box.height >= 44;
  })), 'Theme controls need native button behavior and a 44px target');
  const before = evaluate(() => ({
    page: document.body.dataset.uiMode,
    saved: localStorage.getItem('netfyr-theme'),
    preview: document.querySelector('#demo-theme').dataset.uiMode,
  }));
  browser(['focus', '#demo-theme [data-ui-theme-toggle]']);
  browser(['press', 'Enter']);
  assert.ok(evaluate(before => {
    const root = document.querySelector('#demo-theme');
    const button = root.querySelector('[data-ui-theme-toggle]');
    const mode = before.preview === 'light' ? 'dark' : 'light';
    return root.dataset.uiMode === mode
      && document.body.dataset.uiMode === before.page
      && localStorage.getItem('netfyr-theme') === before.saved
      && button.getAttribute('aria-label') === `Switch to ${before.preview} theme`
      && button.querySelectorAll('svg:not([hidden])').length === 1
      && button.querySelector('svg:not([hidden])').dataset.uiThemeIcon === mode;
  }, before), 'Keyboard activation must update only the preview and its icon/label');
  browser(['press', 'Space']);
  assert.equal(evaluate(() => document.querySelector('#demo-theme').dataset.uiMode), before.preview);
  click('#gallery-theme-toggle');
  assert.equal(evaluate(() => document.querySelector('#demo-theme').dataset.uiMode), before.preview,
    'The gallery theme changed the independent example');
  click('#gallery-theme-toggle');
  const source = evaluate(() => document.querySelector('#source-theme').textContent);
  assert.ok(source.includes('href="./src/theme.css"') && source.includes("import { mountTheme } from './src/theme.js';")
    && source.includes("mountTheme(document.querySelector('#demo-theme'))"), 'Theme source must include its stylesheet and initialization');

  const lifecycle = evaluate(async base => {
    const { mountTheme } = await import(new URL('src/theme.js', base).href);
    const sample = document.querySelector('#demo-theme [data-ui-theme-toggle]');
    const root = document.createElement('section');
    root.className = 'ui';
    root.dataset.uiTheme = '';
    const buttons = [sample.cloneNode(true), sample.cloneNode(true)];
    buttons.forEach(button => { button.hidden = true; root.append(button); });
    const nested = document.createElement('section');
    nested.className = 'ui';
    nested.dataset.uiTheme = '';
    const nestedButton = sample.cloneNode(true);
    nestedButton.hidden = true;
    nested.append(nestedButton);
    root.append(nested);
    document.body.append(root);
    const key = 'netfyr-theme-browser-check';
    localStorage.setItem(key, 'unsupported');
    const system = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const other = system === 'light' ? 'dark' : 'light';
    let cleanup = mountTheme(root, { storageKey: key });
    const nestedCleanup = mountTheme(nested);
    try {
      const initial = root.dataset.uiMode;
      const duplicateCleanup = mountTheme(root, { storageKey: key });
      duplicateCleanup();
      let changes = 0;
      root.addEventListener('ui:themechange', event => { if (event.target === root) changes++; });
      buttons[0].click();
      const singleActivation = root.dataset.uiMode === other && changes === 1;
      const synchronized = buttons.every(button => !button.hidden
        && button.getAttribute('aria-label') === `Switch to ${system} theme`
        && button.querySelector('svg:not([hidden])').dataset.uiThemeIcon === other);
      const independent = nested.dataset.uiMode === system && !nestedButton.hidden;
      cleanup();
      cleanup();
      buttons[0].click();
      const detached = root.dataset.uiMode === other && changes === 1 && buttons.every(button => button.hidden);
      cleanup = mountTheme(root);
      const reset = root.dataset.uiMode === system;
      buttons[1].click();
      const remounted = root.dataset.uiMode === other && buttons.every(button => !button.hidden);
      return { system, initial, singleActivation, synchronized, independent, detached, reset, remounted };
    } finally {
      cleanup();
      nestedCleanup();
      localStorage.removeItem(key);
      root.remove();
    }
  }, url.href);
  assert.equal(lifecycle.initial, lifecycle.system, 'Invalid stored values must fall back to the system preference');
  for (const key of ['singleActivation', 'synchronized', 'independent', 'detached', 'reset', 'remounted']) {
    assert.equal(lifecycle[key], true, 'Theme lifecycle failed: ' + key);
  }

  const blocked = evaluate(async base => {
    const { mountTheme } = await import(new URL('src/theme.js', base).href);
    const root = document.createElement('div');
    root.dataset.uiTheme = '';
    const button = document.querySelector('#demo-theme [data-ui-theme-toggle]').cloneNode(true);
    button.hidden = true;
    root.append(button);
    document.body.append(root);
    const descriptor = Object.getOwnPropertyDescriptor(window, 'localStorage');
    let attempts = 0;
    try {
      Object.defineProperty(window, 'localStorage', { configurable: true, get() {
        attempts++;
        throw new DOMException('Storage blocked', 'SecurityError');
      } });
      const cleanup = mountTheme(root, { storageKey: 'unavailable-theme' });
      const initial = root.dataset.uiMode;
      button.click();
      window.themeStorageFixture = { root, cleanup, mode: root.dataset.uiMode };
      return { attempts, initial, selected: root.dataset.uiMode, visible: !button.hidden };
    } finally {
      Object.defineProperty(window, 'localStorage', descriptor);
      if (!window.themeStorageFixture) root.remove();
    }
  }, url.href);
  try {
    assert.equal(blocked.attempts, 2, 'Blocked storage check must exercise both read and write');
    assert.equal(blocked.visible, true);
    assert.notEqual(blocked.selected, blocked.initial, 'Unavailable storage prevented theme switching');
    browser(['set', 'media', blocked.selected]);
    browser(['set', 'media', blocked.initial]);
    assert.equal(evaluate(() => window.themeStorageFixture.root.dataset.uiMode), blocked.selected,
      'System changes replaced an explicit choice after storage failed');
  } finally {
    evaluate(() => {
      window.themeStorageFixture.cleanup();
      window.themeStorageFixture.root.remove();
      delete window.themeStorageFixture;
    });
  }
}

function checkCodebox() {
  const sample = evaluate(() => {
    const code = document.querySelector('#demo-code-content');
    window.savedClipboardWrite = navigator.clipboard.writeText;
    window.codeCopyWrites = [];
    navigator.clipboard.writeText = async text => { window.codeCopyWrites.push(text); };
    return {
      text: code.textContent, highlighted: code.querySelectorAll('span').length,
      safe: [...code.querySelectorAll('*')].every(node => node.localName === 'span'
        && [...node.attributes].every(attribute => attribute.name === 'class')),
    };
  });
  assert.ok(sample.highlighted > 0, 'Example code must expose syntax tokens');
  assert.equal(sample.safe, true, 'Highlighting must insert only token spans, not interpret sample HTML');
  assert.match(sample.text, /\n/);
  assert.match(sample.text, /^ +\S/m, 'Code example must exercise indentation');
  assert.ok(sample.text.includes('<') && sample.text.includes('&'), 'Code example must exercise escaped markup');
  try {
    browser(['focus', '#demo-code-copy']);
    browser(['press', 'Enter']);
    wait(() => document.querySelector('#demo-codebox [data-ui-copy-status]').textContent === 'Code copied.');
    assert.deepEqual(evaluate(() => window.codeCopyWrites), [sample.text], 'Copy must match displayed code exactly');
    assert.equal(evaluate(() => document.activeElement.id), 'demo-code-copy');

    const source = evaluate(() => {
      document.querySelector('#buttons .gallery-source').open = true;
      return document.querySelector('#source-buttons').textContent;
    });
    click('#buttons [data-ui-copy]');
    wait(() => document.querySelector('#buttons [data-ui-copy-status]').textContent === 'Code copied.');
    assert.deepEqual(evaluate(() => window.codeCopyWrites), [sample.text, source], 'Source examples must use the shared codebox copy behavior');
    assert.ok(evaluate(() => document.querySelector('#source-buttons span') !== null), 'Source examples must reuse syntax highlighting');
    assert.ok(/^ +\S/m.test(source), 'Generated HTML must have readable nesting');

    evaluate(() => { navigator.clipboard.writeText = async () => { throw new Error('Clipboard denied'); }; });
    browser(['focus', '#demo-code-copy']);
    browser(['press', 'Enter']);
    wait(() => /Copy unavailable/.test(document.querySelector('#demo-codebox [data-ui-copy-status]').textContent));
    assert.equal(evaluate(() => document.activeElement.id), 'demo-code-copy', 'Copy denial must retain the initiating focus');
    assert.equal(evaluate(() => document.querySelector('#buttons [data-ui-copy-status]').textContent), 'Code copied.',
      'A failed copy must not overwrite another codebox result');
  } finally {
    evaluate(() => {
      navigator.clipboard.writeText = window.savedClipboardWrite;
      delete window.savedClipboardWrite;
      delete window.codeCopyWrites;
    });
  }
  return sample.text;
}

function assertCodeboxLayout(expected, needsScrolling) {
  const state = evaluate(() => {
    const code = document.querySelector('#demo-code-content');
    const pre = code.closest('pre');
    const before = pre.scrollLeft;
    pre.scrollLeft = pre.scrollWidth;
    const scrolled = pre.scrollLeft;
    pre.scrollLeft = before;
    const style = getComputedStyle(pre);
    const header = code.closest('[data-ui-codebox]').querySelector('.ui-codebox-header');
    const bounds = header.getBoundingClientRect();
    return {
      text: code.textContent, whiteSpace: style.whiteSpace, overflow: style.overflowX,
      width: pre.clientWidth, content: pre.scrollWidth, scrolled,
      focusable: pre.tabIndex >= 0,
      headerFits: [...header.querySelectorAll('button')].every(control => {
        const rect = control.getBoundingClientRect();
        return rect.left >= bounds.left - 1 && rect.right <= bounds.right + 1;
      }),
    };
  });
  assert.equal(state.text, expected, 'Resizing altered the code content');
  assert.equal(state.whiteSpace, 'pre', 'Code indentation and line breaks must remain intact');
  assert.ok(['auto', 'scroll'].includes(state.overflow), 'Long code must scroll inside its own box');
  assert.equal(state.focusable, true, 'The code scroll region must be keyboard reachable');
  assert.equal(state.headerFits, true, 'Codebox header clips its Copy control');
  if (needsScrolling) assert.ok(state.content > state.width && state.scrolled > 0, 'The long-line fixture is not reachable by local scrolling');
}

async function checkIsolatedHost(url) {
  const result = evaluate(async base => {
    const frame = document.createElement('iframe');
    frame.id = 'isolated-host';
    frame.title = 'Package isolation check';
    frame.style.cssText = 'width:100%;height:300px';
    const loaded = new Promise(resolve => frame.addEventListener('load', resolve, { once: true }));
    frame.srcdoc = '<!doctype html><html><head></head><body><button id="host-button">Host button</button><input id="host-input"><section class="ui"><button class="ui-button">Library button</button><section id="fixture"></section></section></body></html>';
    document.body.append(frame);
    await loaded;
    const doc = frame.contentDocument, win = frame.contentWindow;
    const properties = ['fontFamily', 'fontSize', 'color', 'backgroundColor', 'borderTopWidth', 'borderRadius', 'padding', 'display'];
    const sample = () => ['host-button', 'host-input'].map(id => {
      const style = win.getComputedStyle(doc.getElementById(id));
      return properties.map(property => style[property]);
    });
    const before = sample();
    const sheet = doc.createElement('link');
    sheet.rel = 'stylesheet';
    sheet.href = new URL('src/components.css', base).href;
    const styled = new Promise((resolve, reject) => { sheet.onload = resolve; sheet.onerror = reject; });
    doc.head.append(sheet);
    await styled;
    const after = sample();
    const fixture = doc.querySelector('#fixture');
    fixture.innerHTML = ['first', 'second'].map(prefix =>
      '<div data-ui-tabs><div role="tablist" aria-label="' + prefix + '"><button type="button" role="tab" id="' + prefix + '-a" aria-controls="' + prefix + '-panel-a" aria-selected="true">First</button><button type="button" role="tab" id="' + prefix + '-b" aria-controls="' + prefix + '-panel-b" aria-selected="false" tabindex="-1">Second</button></div><div role="tabpanel" id="' + prefix + '-panel-a" aria-labelledby="' + prefix + '-a">First content</div><div role="tabpanel" id="' + prefix + '-panel-b" aria-labelledby="' + prefix + '-b" hidden>Second content</div></div>').join('');
    const module = await win.eval('import(' + JSON.stringify(new URL('src/components.js', base).href) + ')');
    win.cleanup = module.enhance(fixture);
    module.enhance(fixture);
    let focusCalls = 0;
    const second = doc.querySelector('#first-b');
    const focus = second.focus.bind(second);
    second.focus = (...args) => { focusCalls++; return focus(...args); };
    const first = doc.querySelector('#first-a');
    first.focus();
    first.dispatchEvent(new win.KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
    const independent = doc.querySelector('#second-a').getAttribute('aria-selected') === 'true';
    const activated = second.getAttribute('aria-selected') === 'true';
    win.cleanup();
    first.click();
    const destroyed = second.getAttribute('aria-selected') === 'true';
    win.cleanup = module.enhance(fixture);
    first.click();
    const reinitialized = first.getAttribute('aria-selected') === 'true';
    win.cleanup();
    const font = win.getComputedStyle(doc.querySelector('.ui-button')).fontFamily;
    const boxes = doc.createElement('div');
    boxes.innerHTML = ['one', 'two'].map(id =>
      '<div class="ui-codebox" data-ui-codebox><header class="ui-codebox-header"><span>' + id
      + '</span><button type="button" class="ui-button" data-ui-copy aria-disabled="false" aria-busy="false">Copy</button></header>'
      + '<pre class="ui-code" tabindex="0"><code></code></pre><p class="ui-codebox-status" data-ui-copy-status role="status"></p></div>').join('');
    doc.querySelector('.ui').append(boxes);
    const examples = [...boxes.querySelectorAll('[data-ui-codebox]')];
    const values = ['  const html = "<tag>&value</tag>";\n\n    return html;\n', 'second example\n  keeps its spaces\n'];
    examples.forEach((box, index) => { box.querySelector('code').textContent = values[index]; });
    const button = examples[0].querySelector('[data-ui-copy]');
    const status = examples[0].querySelector('[data-ui-copy-status]');
    const otherStatus = examples[1].querySelector('[data-ui-copy-status]');
    const clipboard = win.navigator.clipboard;
    const originalWrite = clipboard.writeText;
    const writes = [];
    const tick = () => new Promise(resolve => win.requestAnimationFrame(resolve));
    clipboard.writeText = async text => { writes.push(text); };
    let cleanup = module.enhance(boxes);
    module.enhance(boxes);
    let copies;
    try {
      button.click();
      await tick();
      const isolated = status.textContent === 'Code copied.' && otherStatus.textContent === '';
      examples[1].querySelector('[data-ui-copy]').click();
      await tick();
      const firstWrites = [...writes];
      cleanup();
      button.click();
      const detachedWrites = writes.length;
      cleanup = module.enhance(boxes);
      let rejectOld;
      clipboard.writeText = text => {
        writes.push(text);
        return new Promise((resolve, reject) => { rejectOld = reject; });
      };
      button.click();
      button.click();
      const pendingWrites = writes.length;
      const busy = button.getAttribute('aria-busy') === 'true' && button.getAttribute('aria-disabled') === 'true';
      cleanup();
      const restored = button.getAttribute('aria-busy') === 'false' && button.getAttribute('aria-disabled') === 'false';
      cleanup = module.enhance(boxes);
      let resolveNew;
      clipboard.writeText = text => {
        writes.push(text);
        return new Promise(resolve => { resolveNew = resolve; });
      };
      button.click();
      const pendingStatus = status.textContent;
      rejectOld(new Error('Old clipboard attempt was denied'));
      await tick();
      const staleIgnored = status.textContent === pendingStatus
        && button.getAttribute('aria-busy') === 'true' && button.getAttribute('aria-disabled') === 'true';
      resolveNew();
      await tick();
      copies = {
        values, firstWrites, detachedWrites, pendingWrites, busy, restored, staleIgnored,
        writes, finalStatus: status.textContent, otherStatus: otherStatus.textContent,
        finalBusy: button.getAttribute('aria-busy'), finalDisabled: button.getAttribute('aria-disabled'), isolated,
      };
    } finally {
      cleanup();
      clipboard.writeText = originalWrite;
      boxes.remove();
    }
    frame.remove();
    return { before, after, independent, activated, focusCalls, destroyed, reinitialized, font, copies };
  }, url.href);
  assert.deepEqual(result.after, result.before, 'Core CSS changes unrelated host controls');
  assert.equal(result.independent, true);
  assert.equal(result.activated, true);
  assert.equal(result.focusCalls, 1, 'Repeated enhancement duplicates keyboard handlers');
  assert.equal(result.destroyed, true, 'Cleanup left active handlers');
  assert.equal(result.reinitialized, true);
  assert.ok(result.font.includes('system-ui'), 'Core typography must include a fallback for hosts without font assets');
  const copies = result.copies;
  assert.equal(copies.isolated, true, 'A copy result leaked to another codebox');
  assert.deepEqual(copies.firstWrites, copies.values, 'Repeated enhancement duplicated or changed code copies');
  assert.equal(copies.detachedWrites, 2, 'Codebox cleanup left an active copy handler');
  assert.equal(copies.pendingWrites, 3, 'Repeated activation dispatched an extra pending copy');
  assert.equal(copies.busy, true, 'Pending copy must expose its unavailable/busy state');
  assert.equal(copies.restored, true, 'Cleanup must restore the original button state');
  assert.equal(copies.staleIgnored, true, 'A stale clipboard response overwrote the reinitialized codebox');
  assert.deepEqual(copies.writes, [copies.values[0], copies.values[1], copies.values[0], copies.values[0]]);
  assert.equal(copies.finalStatus, 'Code copied.');
  assert.equal(copies.otherStatus, 'Code copied.');
  assert.equal(copies.finalBusy, 'false');
  assert.equal(copies.finalDisabled, 'false');
}

function checkHighlighting(url) {
  const result = evaluate(async base => {
    const module = await import(new URL('src/components.js', base).href);
    const host = document.createElement('div');
    host.className = 'ui';
    host.innerHTML = ['javascript', 'unsupported-language'].map(language =>
      '<div class="ui-codebox" data-ui-codebox data-ui-language="' + language + '">'
      + '<div class="ui-codebox-header">'
      + '<button type="button" data-ui-copy>Copy</button></div><pre class="ui-code"><code></code></pre>'
      + '<p data-ui-copy-status role="status"></p></div>').join('');
    document.body.append(host);
    const [box, unknown] = host.querySelectorAll('[data-ui-codebox]');
    const code = box.querySelector('code');
    const status = box.querySelector('[data-ui-copy-status]'), button = box.querySelector('button');
    const original = '  const label = "<tag>&";\r\n \tcall("inline\tvalue");\r\n \t\r\n';
    const fallback = '<img src=x onerror="window.unexpectedCodeExecution = true">&\n  plain\ttext';
    code.textContent = original;
    unknown.querySelector('code').textContent = fallback;
    let cleanup = module.enhance(host);
    const tick = () => new Promise(resolve => requestAnimationFrame(resolve));
    const clipboard = navigator.clipboard, savedWrite = clipboard.writeText;
    const writes = [];
    try {
      const preserved = code.textContent;
      const highlighted = code.querySelectorAll('span').length;
      const unsupported = unknown.querySelector('code').textContent === fallback
        && unknown.querySelector('code').children.length === 0 && !window.unexpectedCodeExecution;
      cleanup();
      cleanup = module.enhance(host);
      const restored = code.textContent;
      const unchangedOther = unknown.querySelector('code').textContent;
      clipboard.writeText = async text => { writes.push(text); };
      button.click();
      await tick();
      return { original, fallback, preserved, highlighted, unsupported, restored,
        unchangedOther, writes, copied: status.textContent };
    } finally {
      cleanup();
      clipboard.writeText = savedWrite;
      host.remove();
      delete window.unexpectedCodeExecution;
    }
  }, url.href);
  assert.equal(result.preserved, result.original, 'Highlighting changed original CRLF or whitespace');
  assert.ok(result.highlighted > 0, 'JavaScript fixture was not highlighted');
  assert.equal(result.unsupported, true, 'Unknown language must retain safe, readable plain text');
  assert.equal(result.restored, result.original, 'Cleanup/reinitialization changed code whitespace');
  assert.equal(result.unchangedOther, result.fallback, 'Highlighting changed an independent instance');
  assert.deepEqual(result.writes, [result.original], 'Clipboard contents lost original tabs, spaces or CRLF');
  assert.equal(result.copied, 'Code copied.');
}

async function connectCDP(url) {
  const reported = browser(['get', 'cdp-url']);
  const endpoint = typeof reported === 'string' ? reported : Object.values(reported).find(value => typeof value === 'string' && value.startsWith('ws'));
  assert.ok(endpoint, 'agent-browser did not report its CDP endpoint');
  const socket = new WebSocket(endpoint);
  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => { socket.close(); reject(new Error('CDP connection timed out')); }, 5000);
    socket.addEventListener('open', () => { clearTimeout(timeout); resolve(); }, { once: true });
    socket.addEventListener('error', error => { clearTimeout(timeout); reject(error); }, { once: true });
  });
  let nextId = 0, sessionId;
  const pending = new Map();
  socket.addEventListener('message', event => {
    const response = JSON.parse(event.data);
    const item = pending.get(response.id);
    if (!item) return;
    pending.delete(response.id);
    clearTimeout(item.timeout);
    if (response.error) item.reject(new Error(response.error.message));
    else item.resolve(response.result);
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++nextId;
    const timeout = setTimeout(() => { pending.delete(id); reject(new Error('CDP timeout: ' + method)); }, 5000);
    pending.set(id, { resolve, reject, timeout });
    socket.send(JSON.stringify({ id, method, params, ...(sessionId && { sessionId }) }));
  });
  const { targetInfos } = await send('Target.getTargets');
  const target = targetInfos.find(target => target.type === 'page' && target.url.startsWith(url.href));
  assert.ok(target, 'Could not find the gallery page for media emulation');
  ({ sessionId } = await send('Target.attachToTarget', { targetId: target.targetId, flatten: true }));
  return { send, close: () => socket.close(), targetId: target.targetId };
}
