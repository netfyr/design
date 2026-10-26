# netfyr design library

Fonts, colors, spacing and logo artwork for netfyr. The site uses HTML, CSS
and JavaScript, with all fonts and assets served locally.

This directory is the canonical `netfyr/design` checkout. `website/` is the
historical preparation copy and is not the source for site changes.

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

The build writes the static site to `dist/`.

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

Fonts and font source code use SIL OFL 1.1; website code uses MIT. All rights
reserved for standalone flame, logo and wordmark artwork. See
[LICENSES.md](LICENSES.md) for details and third-party notices.

## GitHub Pages

The [Pages workflow](.github/workflows/pages.yml) checks and deploys `main`
to `design.netfyr.io`. Pull requests run the same checks.
