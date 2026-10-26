# Terminal foundations

The design library owns these stable rule IDs. The application specification
links here; do not maintain another copy of these contracts.

## Alignment

These are mandatory presentation rules. An unexplained mismatch is a defect,
including when the text is readable. They make the existing
[shared-structure research decision](../../netfyr-tui/.reseach/design-decisions.md#apply-the-same-structure-across-screens)
testable; the exact terminal-cell geometry is a netfyr decision, not an upstream
standard. This visual contract complements W7 without redefining wording rules.

- **TUI-A1 — One content origin per pane.** Title text, flat body rows, labels,
  help, notices and empty states belonging to that pane share its content column.
  A focus or selection marker occupies a separate, stable two-cell gutter; focus
  changes must not move the text. Table headings align with row text after that
  gutter. Unmarked reading panes may start at their own left edge. Switching
  between Inventory and Overview keeps the same content origin. Page-level
  context and nested child panes have separate, explicit origins.
- **TUI-A2 — Comparable values share columns.** Derive heading and row geometry
  from the same widths. Device roles, addresses and timing values occupy separate
  columns; numeric measurements align consistently. Use terminal display-cell
  widths, not byte counts or character counts, for padding externally supplied
  labels. Focus, longer values, Unicode and optional fields must not push one
  row's sibling column sideways. Deliberately omitted narrow columns retain
  complete values in selected details.
- **TUI-A3 — Wrapping preserves the group.** Wrapped prose stays within its
  pane's content rectangle. A field's label, input text, help and error share
  their content origin. Indentation denotes an actual parent/child relationship,
  such as nested evidence or a device relationship; it is not a spacing patch.
  At narrow widths, stack complete labelled groups or omit optional chrome.
  Do not clip a key/action pair, required consequence or the only copy of a value
  to keep a row on one line.
- **TUI-A4 — Check coordinates, focus and resize.** Presentation changes include
  an alignment sweep of the affected surface and coordinate assertions against
  the actual Ratatui buffer. Cover 32×12, 40×12, 48×14 and 100×32; include a split
  view at 140×42 where relevant, selected/unselected states, monochrome and long
  or Unicode values. Exercise resizing and keyboard access as well as rendering.
  Text-presence assertions alone do not verify alignment. Record any intentional
  exception with its user-facing reason here; do not silently waive it in a test.

The [alignment audit](../../netfyr-tui/.reseach/ui-ux-audit/alignment.md) maps every rendered
surface to its findings, fixes and verification.

## Separation and colour

These requirements apply alongside TUI-A1–A4. Their evidence and contrast
calculations are in the [accessibility research](../../netfyr-tui/.reseach/accessibility-separation.md).

- **TUI-S1 — Groups remain distinguishable.** Adjacent panes and independent
  result groups have a visible rule, whitespace or a clearly styled heading.
  An input, its help and its error stay together. Separate the action area from
  content. Preserve the relationship between a wrapped row and its parent,
  including when scrolling starts in that row. Use the existing gutters and
  boundaries before adding boxes or consuming another compact content row.
- **TUI-S2 — Colour is supplementary.** Focus, selection, state and available
  actions retain textual or shape cues in every palette and `NO_COLOR`.
  No instruction requires identifying a hue. Motion off retains the same data
  and controls. Essential grouping cannot depend solely on subtly different
  background shades.
- **TUI-S3 — Contrast and choice are verified.** Accessible is a persisted,
  searchable Colour palette option. Legacy settings default to Standard;
  `NO_COLOR` overrides all assigned colour roles. Locally target at least 4.5:1
  for built-in palette text against each used background and 3:1 for essential dividers
  and focus indicators, using unrounded sRGB calculations. Verify actual rendered
  roles, markers, commit/cancel, resize and small grids. These targets and the
  option name do not claim WCAG certification or screen-reader compatibility.

The [separation audit](../../netfyr-tui/.reseach/ui-ux-audit/separation.md) records each surface's
findings and checks; presentation review rejects unexplained violations.

Custom palettes use the same semantic roles and non-colour cues. Their RGB values
are user-controlled and are not subject to built-in contrast assertions. See
[palette configuration](palettes.md) and [dropdown states](dropdown.md).

## Optional font glyphs

Keep `GlyphSet::Standard` as the library fallback. Hosts can select
`GlyphSet::Netfyr`, which uses U+100000–U+100004 from the **netfyr symbols** companion.
The application checks the companion's coverage for its local startup default
and retains a settings-file override. SSH sessions default to standard characters.
These codepoints avoid the known Nerd Font and Powerline collisions while font
fallback retains the terminal's text font. Installed coverage does not prove
that every terminal honors fallback; do not change terminal configuration.
The standard flame and separator fallbacks are `*`, `>`, `>`, `<` and `<`.
Both sets must retain labels, visible focus, status and stable cell alignment
(TUI-A2, TUI-S2, W7). Custom glyphs supplement these cues; they must not become a
requirement for using the interface.

## Gallery geometry

At 32×12 the flame example uses all twelve rows for the supplied artwork.
Its title and key hints appear when the terminal is taller; Esc and Ctrl+C remain
available at the minimum size. This gallery-only exception preserves the complete
24×12 mark instead of cropping or resampling it. Other examples retain their
content and action boundaries at the minimum size.
