# Searchable dropdown

Use a searchable dropdown for selecting an interface, a finite form value or a
Settings choice. Binary appearance settings use a labelled toggle. Navigation
lists are navigation, not nested dropdowns.

The shared implementation is [src/dropdown.rs](src/dropdown.rs). Application
adapters supply labels, option content, current field value, keyboard candidate,
status and semantic colours. They do not reproduce the option-panel renderer.

## Rust API

`Dropdown` carries a title, prepared `DropdownOption` text, a selected index and
a fallback message. Each option marks whether it matches the field value.
`DropdownStyle::new` receives foreground, surface, border, accent and selected
colours. `draw` returns the panel row rectangle and physical `page_rows`,
plus `page_up`/`page_down` option-index steps. Use those steps for candidate
paging: wrapped options occupy multiple rows, so row counts are not option
counts. Forward paging fits subsequent prepared heights; backward paging uses
the rendered list offset. `content_width` reserves the gutter and right edge
for adapter wrapping.

Adapters sanitize external labels and prepare complete wrapped lines before
constructing options. They retain input values, event handling, filtering, async
lookup tokens and full error paging. See the working
[gallery example](examples/gallery.rs) and [component tests](tests/dropdown.rs).

## TUI-D1: One option-panel structure

Both adapters use the same top/right boundary, title in the top rule, two-cell
candidate gutter, option text origin and empty/loading/error content area.
The title and option text start at the same content column. Use semantic styles
from the active palette; do not hard-code a second set of widget colours.

An editable form field supplies its own query line. Its options open beside that
field, above or below as space permits. A finite chooser uses its labelled search
line in the available content pane. These hosts differ because the interface
input accepts arbitrary names and remains part of a form. Their option panels,
focus cues and typography remain the same. Do not introduce another dropdown
variant merely because a setting or form has a different value type.

## TUI-D2: Value and keyboard candidate are distinct

The option matching the field's value uses accent and underline. The keyboard
candidate uses the selected-row background and `▎` in the stable two-cell gutter.
The candidate can move away from the value without committing it. Underline and
the gutter remain in NO_COLOR. Do not append `· current`, `selected` or equivalent
prose to options. Do not depend on hue alone.

For finite choices, the value changes on commit. The editable interface field
also holds a typed draft, so its underlined match represents that draft, not
a claim that the interface is applied or configured. An option's selection is
never consent to a network mutation.

## TUI-D3: Search does not erase alternatives by default

Opening with a value highlights its matching option without treating that value
as an implicit filter. Deliberate typing filters; cursor movement, Delete,
Backspace and Ctrl+U support correction. Characters used as global shortcuts
remain input while editing. Focus changes do not move the text column.

[TUI-K1–K5](bindings.md) owns the shared keyboard map. F4/Alt+↓ opens choices;
Esc/F4 closes. Arrows and PgUp/PgDown move candidates; Tab/Shift+Tab chooses and
moves to the next/previous field or setting without submitting a form. Enter
chooses, then advances a form or submits on its last field; Settings commits and
closes. F5/Ctrl+Enter submits a form. Ctrl+R refreshes interface choices.

A finite no-match query cannot invent a value. Enter keeps it open; Tab closes
and moves focus while retaining the old value without saving. Editable interface
fields also accept nonempty manual names and retain typed drafts on closing.

These differences are data-entry semantics, not styling exceptions. Hints must
describe the actual handler and current state (W4). A form's mutation review
still has the separate W3 negative-default confirmation.

## TUI-D4: Missing choices have useful states

| State | What to show | Recovery |
| --- | --- | --- |
| Ready | Options and position/count where useful | Move, search, choose |
| Loading | A short loading state for the requested list | Interface manual entry remains available |
| Successful empty list | No interfaces found, or the appropriate requested empty result | Type a manual interface name or refresh |
| Filter has no matches | No matching choices/interfaces | Correct or clear the query; finite choices cannot commit |
| Lookup failed | The affected list and concrete reason | Retry or type a manual name; complete error remains reachable |

Do not substitute an empty list for a failed lookup. Do not display internal
provider names solely as attribution. Late replies must not overwrite a newer
query, field, form or namespace. These state rules belong to the adapter; the
shared widget renders the supplied state without starting work.

## TUI-D5: Small viewports retain a usable choice

Borders and headings must not consume the final available option row. Keep the
query cursor, active option and complete key/action hints usable at 32×12.
Wrap complete option labels where supported; shortened interface rows retain the
complete selected name in the editable field. Preserve Unicode display-cell
alignment. Long lookup errors remain reachable through the host's paging.

## TUI-D6: Changes update both hosts

Verify the shared widget and both application adapters. Cover initial value,
moving away from it, filtering, no matches, commit, cancellation, loading/failure,
manual interface entry, stale replies, long labels, Unicode, focus, resize and
NO_COLOR. Compare actual gutter/border/style coordinates, not just label presence.

Adapters:
[finite choices](../../netfyr-tui/src/ui/choice_picker.rs),
[interfaces](../../netfyr-tui/src/ui/interface_picker.rs).
Controller semantics remain in [App](../../netfyr-tui/src/app.rs).
Research: [selection mechanisms](../../netfyr-tui/.reseach/interface-dropdown.md),
[source comparison](../../netfyr-tui/.reseach/sources.md),
[colour-independent meaning](../../netfyr-tui/.reseach/accessibility-separation.md).
