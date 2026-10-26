# netfyr design library

Fonts, colors, spacing, logo artwork and shared terminal and web components for netfyr.
The design site uses HTML, CSS and JavaScript, with fonts and assets served locally.

## Source and components

This directory is the `netfyr/design` Git checkout. The old
`.build/github/design` path links here; `website/` is a historical preparation
copy and is not the source for site changes.

| Content | Location |
| --- | --- |
| Brand site and downloads | `src/` and `public/` |
| Shared TUI widgets, contracts and interactive gallery | [tui/](tui/README.md) |
| Web controls and browser gallery | [web/](web/README.md) |
| Font sources and review records | [font-sources/0.507/](font-sources/0.507/README.md) |

The web library contains native HTML/CSS controls and reusable navigation with
an animated logo and subtitle. JavaScript adds tabs, dialogs, syntax highlighting
and code copying. It supports light and dark netfyr styles.
Applications own their data and actions; SpecDoc remains organization-neutral.

The site sidebar separates brand pages from Web and TUI components. Web lives at
`/components/`; TUI lives at `/components/tui/`, with terminal screenshots,
recorded interactions and renderer previews. All three areas share the saved theme.

`npm run dev` previews the complete site at http://localhost:4173;
`npm run dev:web` offers the same preview on port 4175.
`npm run build:web` writes the gallery artifact and downloadable web package to
`web/dist/`. The root build includes that artifact under `dist/components/`.
`npm run check:web` checks the package and assets; `npm run check:web:browser`
exercises the controls.

The TUI application imports `netfyr-tui-design` from `tui/`. Run its tests and
gallery from this repository:

```sh
cargo test --locked --manifest-path tui/Cargo.toml --all-targets
cargo run --locked --manifest-path tui/Cargo.toml --example gallery
```

The gallery previews shared dropdowns, setting rows, footers and animations with
offline fixtures. It requires a terminal; append `-- --snapshot` for text output
or `-- --fixture flame` to open an example directly.

TUI documents link to sibling `netfyr-tui/` and `specs/` checkouts for application
code and cross-project requirements. The website build excludes these developer
references and the TUI source.

## Develop

Requires Node.js 24.

```sh
npm ci
npm run dev
```

Open http://localhost:4173. Changes in `src/` and `public/` reload automatically.
Set `PORT` to use another port.

Check, build and preview the production site:

```sh
npm run check
npm run build
npm run preview
```

The build writes the complete static site to `dist/` for the existing
`design.netfyr.io` GitHub Pages deployment.

Overview is the home page. The Logo page has transparent SVG and PNG downloads
of the full logo in brand colors, black and white, and the standalone flame in
orange, black and white. PNGs are 1024 pixels wide. Rebuild the variants from
the approved SVG artwork with Python 3 and Inkscape:

```sh
python3 scripts/build_logo_variants.py
```

To run the browser checks:

```sh
npm install --global agent-browser@0.26.0
agent-browser install --with-deps
npm run check:pages
```

`check:pages` starts a production preview at `/design/` and checks fonts, links,
layout and the flame animation. `npm run check:flame` runs the animation checks
against a running development server.

## Fonts and licenses

netfyr Sans and Mono 0.507 each have seven weights, upright and italic:
28 styles in TTF and WOFF2. The fonts are included in the repository. See the
[font source README](font-sources/0.507/README.md) for review records and rebuild
instructions. Rebuilding requires the original reference archive.

Fonts and font source code use SIL OFL 1.1; website, TUI and web component code use MIT. All rights
reserved for standalone flame, logo and wordmark artwork. See
[LICENSES.md](LICENSES.md) for details and third-party notices.

## GitHub Pages

The [Pages workflow](.github/workflows/pages.yml) checks and deploys `main`
to `design.netfyr.io`. The [TUI workflow](.github/workflows/tui.yml) checks
terminal component changes on pull requests and pushes to `main`.
