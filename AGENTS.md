# netfyr design library

- Site source: `src/` and `public/`. Components: `web/` and `tui/`; read their
  `AGENTS.md` before changes.
- Check the working tree and fetch `origin/main` before editing. Preserve local work.
- Use native HTML, CSS and JavaScript, local assets and the supplied artwork.
  Keep the name lowercase: **netfyr**.
- Reuse shared components. Keep application behavior in its application and
  SpecDoc branding in deployment configuration.
- Follow [interaction principles](principles.md). Keep copy concise.
- Keep brand pages separate from the Web and TUI categories. Do not add an
  Interface patterns page or flame construction.
- Preserve font sources and licensing. Use real weights, with font synthesis
  disabled. Follow `font-sources/` for font releases.
- Keep review evidence local. Do not add evidence reports or changelogs to Git.

`npm run dev` previews on port 4173. `npm run build` writes `dist/` for GitHub Pages.
Run `npm run check` and `npm run check:pages` for site changes; component checks
are documented in the component READMEs.
