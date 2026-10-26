# netfyr design library

Source for [design.netfyr.io](https://design.netfyr.io/).

- Brand pages and downloads: `src/` and `public/`
- [Web components](web/README.md): `/components/`
- [TUI components](tui/README.md): `/components/tui/`
- [Font sources](font-sources/0.507/README.md)
- [Design principles](principles.md)

## Develop

Requires Node.js 24.

```sh
npm ci
npm run dev
```

Open http://localhost:4173. To build and preview the production site:

```sh
npm run check
npm run build
npm run preview
```

The build writes `dist/`. GitHub Pages deploys `main` to `design.netfyr.io`.

See [LICENSES.md](LICENSES.md) for code, font and artwork licenses.
