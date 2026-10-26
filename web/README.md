# Web components

Native HTML controls, scoped CSS, and opt-in JavaScript for tabs, dialogs, code boxes and theme controls.
The package includes a local Highlight.js subset and needs no additional packages.
The gallery uses the exported styles
and behaviors with local example data; applications own their data and actions.

## Preview

From the design repository root:

```sh
npm run dev:web
```

Open http://localhost:4175/components/ for Web components or
http://localhost:4175/components/tui/ for the TUI catalogue and terminal screenshots.
Both are categories in the design site, sharing its navigation and saved theme.
`npm run build:web` writes the gallery artifact and downloadable web package to
`web/dist/`; the root build includes it at `dist/components/` for GitHub Pages.
`npm run check:web` checks the package and assets; `npm run check:web:browser`
exercises the gallery controls, and `npm run check:pages` covers the combined site.

## Install

Download the package from the gallery, then install it locally:

```sh
npm install ./netfyr-web-components-0.1.0.tgz
```

With a bundler:

```js
import '@netfyr/web-components/styles.css';
import { enhance } from '@netfyr/web-components';

const cleanup = enhance(document.querySelector('.ui'));
```

For plain HTML, copy `src/` into your project, load `src/components.css` with a
stylesheet link, and import `enhance` from `./src/components.js` in a module
script. Put the controls inside an element with `class="ui"`. Styles and custom
properties are scoped to that element; the package does not reset the host page.

```html
<main class="ui" data-ui-mode="light">
  <button class="ui-button ui-button--primary" type="button">Add item</button>
</main>
```

## Components

| Component | Markup/API |
| --- | --- |
| Button or link | `.ui-button`; `--primary`, `--danger`, `--quiet` modifiers |
| Text field | `.ui-field`, `.ui-label`, `.ui-input`, `.ui-help`, `.ui-error` |
| Select | Native `select.ui-select` |
| Checkbox/radio | Native input inside `label.ui-check` |
| Switch | `input.ui-switch[type="checkbox"][role="switch"]` inside `label.ui-check` |
| Tabs | `.ui-tabs[data-ui-tabs]`, native buttons with `role="tab"`, `.ui-tabpanel` |
| Dialog | Native `dialog.ui-dialog`, opened by `[data-ui-open-dialog="dialog-id"]` |
| Notice or badge | `.ui-notice`, `.ui-badge`; `--success`, `--warning`, `--danger` modifiers |
| Disclosure | Native `details.ui-disclosure` and `summary` |
| Footer | `.ui-footer`, `.ui-footer-brand`, `.ui-footer-mark`, `.ui-footer-link` |
| Navigation | `.ui-navigation`, `.ui-brand`, `.ui-brand-logo`, `.ui-brand-mark`, `.ui-brand-subtitle`, `.ui-nav-links`, `.ui-nav-label`, `.ui-nav-divider`, `.ui-nav-trailing` |
| Table | Native `table.ui-table` inside `.ui-table-wrap`; `.ui-table-cell--end` for right-aligned headers/cells |
| Code box | `.ui-codebox[data-ui-codebox]`, `pre.ui-code > code`, `[data-ui-copy]` |
| Theme | `[data-ui-theme]`, `button.ui-theme-toggle[data-ui-theme-toggle]`, `mountTheme(root, options)` |

Use explicit button types, associated labels, and `aria-describedby` for help
and errors. Controls keep their native form values, validation and reset behavior.
Set `aria-invalid="true"` only while a field is invalid. The gallery's form
validation, record filtering and retry fixtures are examples of
application logic, not package APIs.

### Enhanced components

Call `enhance(root)` after inserting their markup. It returns a cleanup function
for the listeners created by that call. Repeated or overlapping calls do not
register a widget twice; cleanup allows it to be initialized again.

Tabs require unique IDs, `aria-controls` on each tab, and matching
`aria-labelledby` on its panel. Keep each tablist and its panels inside its own
`[data-ui-tabs]` group. The selected tab has `aria-selected="true"`; other
panels start hidden. Arrow keys, Home and End activate preloaded panels and skip
disabled tabs. Horizontal tabs leave Up/Down to browser scrolling. A selection
change emits a bubbling `ui:tabchange` event with `{ tab, panel }` in `detail`.

Dialog openers name the target ID in `data-ui-open-dialog`. Give the dialog an
accessible title and a visible close action, using a `form method="dialog"`
with button values for the result. Native `close` and `cancel` events retain
their normal meaning. Use `autofocus` to choose initial focus; consequential
examples focus Cancel. Closing returns focus to the opener when it still exists.

### Footer

Supply your own mark asset and text. The footer wraps at narrow widths.

```html
<footer class="ui-footer">
  <span class="ui-footer-brand">
    <img class="ui-footer-mark" src="./logo.svg" alt="" width="18" height="18">
    Design library
  </span>
  <a class="ui-footer-link" href="/resources">
    Assets &amp; resources
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 12h14m-6-6 6 6-6 6"/>
    </svg>
  </a>
</footer>
```

### Navigation

Supply the logo artwork and subtitle, then mark the current link with
`aria-current="page"` or `"location"`.

```html
<aside class="ui-navigation" aria-label="Project navigation">
  <a class="ui-brand" href="/" aria-label="Project home">
    <svg class="ui-brand-logo" viewBox="0 0 440 128" aria-hidden="true">
      <g class="ui-brand-mark"><!-- Your mark paths --></g>
    </svg>
    <span class="ui-brand-subtitle">project settings</span>
  </a>
  <nav class="ui-nav-links" aria-label="Settings">
    <p class="ui-nav-label">Project</p>
    <a href="/overview" aria-current="page">Overview</a>
    <a href="/connections">Connections</a>
    <hr class="ui-nav-divider">
    <p class="ui-nav-label">Resources</p>
    <a href="/help">Help</a>
    <a href="https://github.com/netfyr/design" aria-label="Source repository (external site)">
      Source repository
      <svg class="ui-nav-trailing" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M7 17 17 7M7 7h10v10"/>
      </svg>
    </a>
  </nav>
</aside>
```

Use `.ui-nav-label` for section subtitles and `hr.ui-nav-divider` for a separator.
Both are optional.
External links use a trailing `.ui-nav-trailing` arrow and an accessible label
identifying the external destination. The example follows normal same-tab navigation.

The mark animates on hover and keyboard focus; the wordmark and subtitle stay
still. Reduced-motion preferences disable the animation. The package supplies
the styles, not logo artwork or font files. The gallery owns its responsive
drawer layout and scroll tracking; applications own their routes. Its theme
control uses the standalone component below.

### Code box

Code boxes use a labelled, keyboard-scrollable `pre`. Highlighting keeps the
source text intact, including tabs, spaces and line endings. Copy writes that
same text. Escape HTML in the source, or set `code.textContent` when inserting
code dynamically.

```html
<div class="ui-codebox" data-ui-codebox data-ui-language="javascript">
  <div class="ui-codebox-header">
    <span id="code-label">example.js</span>
    <button class="ui-button ui-button--quiet" type="button" data-ui-copy>Copy</button>
  </div>
  <pre class="ui-code" tabindex="0" role="region" aria-labelledby="code-label"><code>const answer = 42;</code></pre>
  <p class="ui-codebox-status" data-ui-copy-status role="status"></p>
</div>
```

Call `enhance(root)` to enable highlighting and Copy.
`data-ui-language` supports HTML/XML, CSS, JavaScript, TypeScript, JSON, Bash
and Rust. Omit it, or use an unsupported language, for plain text. Highlighting
uses locally bundled grammars without automatic language detection or network requests.

Copy writes only the displayed code text to the clipboard,
with a status message for success or failure. Clipboard access requires a secure
context such as HTTPS or localhost; when unavailable, the code remains selectable.
Use unique label IDs for multiple boxes.

### Theme

Load `theme.css` and call `mountTheme` explicitly. This standalone module has no
dependencies and does not load the other controls or syntax highlighting.

```js
import '@netfyr/web-components/theme.css';
import { mountTheme } from '@netfyr/web-components/theme.js';

const cleanup = mountTheme(document.querySelector('[data-ui-theme]'), {
  storageKey: 'site-theme',
});
```

For plain HTML, copy `src/theme.js` and `src/theme.css`, link the stylesheet,
and import `mountTheme` from the copied module. Supply the button's icons:

```html
<main class="ui" data-ui-theme data-ui-mode="light">
  <button class="ui-theme-toggle" data-ui-theme-toggle type="button"
    aria-label="Switch to dark theme" hidden>
    <svg data-ui-theme-icon="light" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" />
    </svg>
    <svg data-ui-theme-icon="dark" viewBox="0 0 24 24" aria-hidden="true" hidden>
      <path d="M20 14a8.5 8.5 0 0 1-10-10A8.5 8.5 0 1 0 20 14Z" />
    </svg>
  </button>
</main>
```

The root follows the system preference until the user chooses a mode. An optional
`storageKey` saves `light` or `dark` locally and restores it on the next mount;
omitting it keeps the choice in memory. Unavailable storage does not prevent
switching. The current mode is written to `data-ui-mode`; the icon shows that
mode and the button's accessible label names the next action. A mode change
emits a bubbling `ui:themechange` event with `{ mode }` in `detail`.

Each `[data-ui-theme]` root owns its buttons, excluding nested roots. Repeated
mounts do not add listeners; only the first call's cleanup removes them. Cleanup
is safe to repeat and restores each button's initial hidden state. Mount again
after replacing controls. Buttons start hidden so they only appear when working.

The standalone stylesheet styles the button without requiring `.ui` or the full
component stylesheet. It uses `--ui-text`, `--ui-accent`, `--ui-nav-hover` and
`--ui-radius` when provided. Applications supply their page colors and
`color-scheme` for each `data-ui-mode`; the full component stylesheet already
provides these for `.ui` roots.

## Appearance

The stylesheet uses netfyr colors, with `data-ui-mode="light"` or `"dark"` on
the `.ui` root. The gallery supplies local netfyr fonts; the package includes
neither fonts nor logo artwork. Without those fonts it uses system fallbacks.
Applications can override the `--ui-*` properties for their deployment.

The component code uses MIT; bundled Highlight.js uses BSD-3-Clause (see
`src/vendor/highlightjs/LICENSE`). The gallery's fonts use SIL OFL 1.1 and its
flame artwork has reserved rights. Package metadata does not grant mark rights.
See the gallery's asset notices and the repository's `LICENSES.md`.
