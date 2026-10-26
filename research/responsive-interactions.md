# Responsive interaction research adoption

Recorded 2026-10-26. Josie supplied *Responsive Interaction Design Patterns:
A Cross-Platform Research Report*, dated 2026-10-26, as input to the design
language. Original filename: `deep-research-report(8).md`.
SHA-256: `003217ca1b4678e947326978cc4d79c40f4fe8c821886709449aec994911ed6d`.

The export has 104 citation markers but no source URLs or bibliography. Its
comparative ratings are explicitly analytical synthesis. Treat the report as
supplied research; the primary references below independently support the
mechanisms we adopted. Company conversion figures are not netfyr targets or
evidence of a universal benefit. Framework versions and example snippets are
not component contracts or production implementations.

The resulting [interaction principles](../principles.md) govern design choices.
The decisions below are local adaptations of the report, not claims that all
these features exist or should be built.

## Pattern decisions

| Pattern | Decision for netfyr |
| --- | --- |
| Skeleton loaders | Conditional on a real wait and predictable content geometry. Keep decoration out of the accessibility tree and expose meaningful loading status. Terminal pending text and existing activity indicators remain sufficient where there is no useful geometry to preview. |
| Optimistic updates | Local drafts and reversible previews can respond immediately. Remote writes need explicit pending, failure and reconciliation behavior; an older failure must not overwrite newer edits. Network apply, observed connectivity and rollback require evidence under W5. |
| Command menus | Consider when action density makes discovery difficult. Reuse contextual actions and searchable choices first; keep important actions discoverable outside the palette. No shared command-palette export currently exists. |
| Shortcut hints | Adopt contextual, truthful hints and consistent key families. Preserve text entry and browser/OS shortcuts. This extends the existing W4 and TUI-K guidance. |
| Undo toasts | Conditional on an implemented, reversible operation. A timed message must not be the only consequential recovery path. Required mutation review and confirmed rollback semantics remain unchanged. |
| Stale-while-revalidate | Conditional on an application-owned freshness policy. Distinguish cached observations from current evidence and preserve edits during replacement. Structured TUI inspection currently clears the previous snapshot during refresh and after failure; this report does not change that policy. |
| Pre-rendering / prefetching | Consider only after measuring a likely navigation benefit and its resource cost. Speculative work must not dispatch mutations or trigger activation-only effects. Do not add speculation to the static sites by default. |
| BlurHash | Conditional on a substantial image-loading problem. Reserve image dimensions first; placeholders are decorative and cannot replace the final alternative text. No current need for a terminal analogue or an extra logo placeholder. |
| View transitions | Optional continuity for a concrete change of context. Keep focus, history and the next input correct, with a reduced-motion path. Do not animate every route. |
| Swipe-to-dismiss sheets | Only for a surface that needs a sheet. Prefer native behavior; retain a clickable Close/Back action, keyboard dismissal and correct modal focus. No terminal gesture imitation. |
| Interruptible animations | Adopt as a host interaction requirement. New input takes precedence over decorative motion; operation validity cannot depend on an animation-completion callback. Renderers remain independent of application event loops. |
| Predictive back | Use supported platform navigation when building for that platform. On the web preserve browser history; in the TUI preserve understandable parent return and drafts. Do not reproduce Android gestures across surfaces. |
| Balanced headlines | Prefer responsive wrapping for short headings over viewport-specific line breaks. Keep real heading text and test narrow/large-text layouts. This is not a global body-text setting. |
| Tabular numbers | Use for values whose changing digit widths hinder comparison; verify the font and preserve correct units/formatting. Terminal cell alignment already supplies the relevant geometry. Do not change all web text to monospace. |
| Safe triangle / polygon | Only when an actual cascading hover menu needs pointer-intent handling. Retain keyboard, click and touch operation. Existing sidebars do not justify adding flyouts. |

Gallery retry fixtures are not production request handling, and cached dropdown
choices are not a general stale-while-revalidate policy. The existing
[snapshot decision](../../netfyr-tui/.reseach/design-decisions.md) and application
refresh tests retain their authority.

## Primary references checked

- [WCAG keyboard access](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html),
  [character shortcuts](https://www.w3.org/WAI/WCAG22/Understanding/character-key-shortcuts.html)
  and [dragging alternatives](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html):
  keyboard access and a single-pointer alternative to dragging are separate
  requirements; keyboard support alone is not that pointer alternative.
- [WCAG status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html):
  expose meaningful results/progress without moving focus. This does not justify
  announcing every telemetry refresh or adding routine success notices.
- [WCAG interaction motion](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html)
  is Level AAA; [automatic movement and updates](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html)
  have separate Level A requirements. netfyr retains its existing motion-off
  convention; this adoption does not claim WCAG conformance or terminal assistive-technology support.
- [Android animation guidance](https://developer.android.com/develop/ui/compose/animation/advanced)
  supports interrupting and retargeting animation for new interaction. Applying
  that behavior to netfyr's browser and terminal hosts is our design decision.
- [RFC 5861 §3](https://www.rfc-editor.org/rfc/rfc5861.html#section-3) defines
  bounded HTTP stale-response reuse during revalidation. It does not define a
  product's acceptable observation age or authorize a network change from stale data.
- [Android write strategies](https://developer.android.com/topic/architecture/data-layer/offline-first#write-strategies)
  distinguishes online-only, queued and local-first writes. netfyr's mutation
  authority remains governed by its own application contracts and W5.
- [CSS Text 4 wrapping](https://www.w3.org/TR/css-text-4/#text-wrap-style) and
  [CSS Fonts 4 numeric variants](https://www.w3.org/TR/css-fonts-4/#font-variant-numeric-prop)
  describe balancing and tabular figures. These working drafts explain mechanisms,
  not universal browser/font support or proven readability gains for netfyr.
- [Chrome prerendering guidance](https://developer.chrome.com/docs/web-platform/prerender-pages)
  describes speculative execution and resource limits. Our adoption requires a
  measured use case and separation of speculative work from user-authorized effects.

No new runtime behavior, performance benchmark, representative-user study or
screen-reader study was produced by this documentation change. Check a pattern's
current platform API and its actual failure behavior when an implementation is proposed.
