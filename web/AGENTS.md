# Web component library

- Keep `src/` usable independently of the gallery and any application. Use native
  controls, scoped `.ui` styles, semantic `--ui-*` properties and opt-in behavior.
- Components use netfyr styling with light and dark modes. Keep SpecDoc branding
  in its deployment configuration. Do not copy application source into
  this MIT package; SpecDoc's code has a separate AGPL license.
- Read [shared principles](../principles.md) and `README.md` for the public API.
  Browser focus, input and navigation conventions take precedence over terminal
  geometry and keys. Reuse W4/W5/W6/W7/W9 for clear, relevant feedback.
- Examples use the actual exported implementation. Keep gallery-only data and
  handlers in `gallery.js`, with no network operations or real application state.
- Preserve native form participation, labelled controls, hidden content, keyboard
  operation and focus return. Test real input and multiple independent instances.
- Build the gallery artifact in `web/dist/`. The root build publishes its allowed
  files under `dist/components/`, beside the brand pages in the same Pages site.
  Keep component implementations and examples in `web/`, with relative navigation
  that also works when the complete site is served under a path such as `/design/`.
- The source package excludes gallery fonts and marks. The gallery build uses an
  explicit asset allowlist and retains font and mark notices.
- Run `npm run check:web` and `npm run check:web:browser` from the repository root.
  Inspect narrow and wide layouts in both modes.
