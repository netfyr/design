# Keyboard bindings

This is the canonical TUI binding contract, TUI-K1–K5. It applies to every
screen and both dropdown adapters. W3 owns consent, W4 owns hint spelling and
active-context truthfulness. These are netfyr decisions informed by the
[keyboard audit and source comparison](../../netfyr-tui/.reseach/keybindings.md),
not a claim that Linux applications share a universal keymap.

## TUI-K1: One action family, one primary key

Use the same key for the same action across screens. Do not allocate a new key
because a component has a different implementation. Labels may name the object
(`edit config`, `edit inputs`) while retaining the same edit key. Local aliases
must be documented here and in Help; primary hints show the canonical key.

| Context | Key | Action |
| --- | --- | --- |
| Outside text entry | `1`, `2`, `s`, `?` | Interfaces, Paths, Settings, Help |
| Retained change | `3` | Resume the existing change |
| Outside text entry | `q`; `m` | Quit; toggle motion |
| Everywhere | `Ctrl+C` | Quit; stop local orchestration without approving work |
| Lists | `↑` / `↓`; `j` / `k` outside text entry | Move selection |
| Interface and connection lists | `Home` / `End`; `PgUp` / `PgDown` | First/last row; move by a visible page |
| Task, interface and connection lists | `/` | Search/filter; while editing, arrows and page keys move through matches |
| Task, interface and connection entries | `Enter` | Open the selected entry or details; pressing again in details does not return |
| Focused interface/connection details or completed result | `Enter`; `Esc` | Open diagnostic details without retrying; close the visible expansion before returning |
| Completed result with recovery | `r` | Follow the offered recovery; e still edits retained inputs |
| Interface/connection list and details | `Tab` / `Shift+Tab` | Move focus between panes |
| Editable interface or run | `e` | Edit selected config or retained inputs |
| Observation | `r` | Refresh; on a failed Settings save, retry that save |
| Focused readable content | `↑` / `↓`, `PgUp` / `PgDown` | Scroll the content |
| Task browser, API reference and Settings | `PgUp` / `PgDown` | Scroll the adjacent description; task search instead pages its matching entries |
| Forms and Settings | `Tab` / `Shift+Tab` | Next/previous field or setting |
| Plain form field | `Enter` | Advance; submit through validation on the last field |
| Complete form | `F5` / `Ctrl+Enter` | Submit from any field; never approve the resulting review |
| Finite field or Settings choice | `Enter`, `F4` / `Alt+↓` | Open choices |
| Interface field | `F4` / `Alt+↓`; `↓` when closed | Open choices; a closed field uses its exact typed name on Enter |
| Open dropdown | `↑` / `↓`; `PgUp` / `PgDown` | Move candidate; page through visible options |
| Open dropdown | `Enter` | Choose; a form advances or submits on its last field; Settings commits and closes |
| Open dropdown | `Tab` / `Shift+Tab` | Choose and move to the next/previous field or setting, without submitting a form |
| Open dropdown | `Esc` / `F4` | Close without choosing the candidate |
| Interface choices | `Ctrl+R` | Refresh the list without replacing entered text |
| Text and search | `←` / `→`, `Home` / `End`, `Backspace`, `Delete`, `Ctrl+U` | Move cursor, correct text, clear text |
| Search | `Enter`; `Esc` | Accept filter; clear filter and leave its editor |
| Binary setting | `Enter` / `Space`; `←` / `→` | Toggle; set Off/On |
| Review | `y` / `Y`; `n` / `N` / `Enter` / `Esc` | Approve; decline (W3) |
| Interface inspection | `v` | Switch overview/list |
| Paths | `t`; `a`; `i` | Trace selected peer; enter destination; request public IP names |
| Help | `c` | Open API reference |

API reference shows the selected operation immediately. Arrows select operations;
page keys read its description. Enter and Tab do not open another level there.

Compatibility aliases: `c` still edits interface config outside Help; `p` opens
Paths; `x` toggles diagnostic details. During a pending review, `x` remains the
detail control because Enter and Esc must decline (W3). Primary hints use `e`
and `2`. The Help-local `c` is an existing reference shortcut, not another edit action. Do not add more such overlaps.

## TUI-K2: Focus owns input; modifiers are explicit

Handle documented global interruption first, then the active editor/dropdown,
then navigation and contextual actions. All printable shortcut letters are text
inside fields and queries, including `j`, `k`, `q`, `e`, `s`, `y` and `n`.
Home/End moves the cursor there, not the result selection. Arrow/page navigation
may change a filtered candidate without leaving the editor or changing its query.

Match modifier combinations explicitly. Ctrl, Alt, Super, Hyper or Meta plus a
letter is not an alias for that letter. Ctrl+Y and Alt+Y must never approve.
Ctrl+Enter applies only to a form, not a Settings choice. Documented Shift+Tab
and uppercase review answers remain supported. Ignore release/repeat events for
activation and consent. Do not invent a chord fallback when a terminal cannot
distinguish it: F5 is the portable form-submit key; Tab and Shift+Tab retain their
terminal encodings. No keyboard enhancement protocol is required.

## TUI-K3: Shared controls share behavior

Both dropdowns support F4/Alt+↓ opening and the same navigation, closing and
focus keys. Interface choices open automatically on field entry; a deliberately
closed interface list lets Enter accept the exact typed name. Finite fields use
Enter to open their available values first.
Page by the visible option rows. Do not close an available list as a side effect
of paging. With no candidates, interface lookup errors may use the host's page
scrolling so their full text remains reachable.

A finite no-match query cannot invent a value: Enter keeps it open; Tab closes
and moves focus while retaining the prior value, without saving or submitting.
An editable interface accepts a nonempty manual name. Closing retains its typed
draft. These data-entry differences do not justify different navigation keys.

Enter advances through form fields regardless of type. F5/Ctrl+Enter submits
all values through the same validation. Tab changes focus without submitting.
No key may commit a hidden candidate or submit an unavailable form below the
minimum viewport. Closing and global interruption remain available.

## TUI-K4: Escape unwinds the active interaction

Close a dropdown or editor first. Outside an editor, stop active Paths work
before leaving its result, collapse a visible diagnostic expansion, then close
a nested detail/name view before clearing a
retained filter, then return to its parent. Escape in a review declines; it never
navigates past consent. Preserve drafts, observations and unresolved outcomes.
An expansion in an unfocused pane must not consume Esc just to change hidden
content. Enter opens details idempotently: repeating it never closes, retries or
leaves the result. Forms, searches, dropdowns and reviews keep their distinct
Enter actions from the table above.
The current hint names what that press will do, such as `close`, `stop` or `back`.

## TUI-K5: Hints and behavior change together

Footer, Help, docs and tests must agree with the actual handler (W4, W8).
Use complete key/action pairs at every width. Omit a lower-priority pair or an
alias rather than clipping its action. Keep the primary action, return path and
review answers reachable at 32×12; Help records less-frequent alternatives.

New binding reviews cover entry, movement, typing, correction, commit, cancel,
return, no matches, failed lookup/save, modifiers and resizing. Test real input
handlers with deterministic providers and the rendered footer; string presence
alone cannot establish behavior. See [keyboard regressions](../../netfyr-tui/tests/keybindings.rs),
[footer tests](../../netfyr-tui/tests/footer.rs) and the
[verification record](../../netfyr-tui/.reseach/ui-ux-audit/verification.md).

Handlers remain application-owned in [App](../../netfyr-tui/src/app.rs) and
[text_input](../../netfyr-tui/src/text_input.rs); this contract is not a Rust keymap
export. The [dropdown renderer](src/dropdown.rs) stays independent of app actions.
