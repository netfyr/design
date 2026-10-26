# netfyr terminal design library

The definitive reference for netfyr TUI components: their implementation,
appropriate uses, interaction states, layout and language. The application
imports the `netfyr-tui-design` Rust crate from this directory. Change a shared
component here rather than creating a second renderer in an application.

## Start here

| Reference | Owns |
| --- | --- |
| [Component catalogue](components.md) | Which component to use, its states, implementation and verification |
| [Keyboard bindings](bindings.md) | Canonical action families, focus, modifiers and hints; TUI-K1–K5 |
| [Searchable dropdown](dropdown.md) | One shared option panel for editable interface fields and finite choices; TUI-D1–D6 |
| [Animations](animations.md) | Flame, activity indicators, traffic lanes and RTT replay; timing and motion-off behavior |
| [Foundations](foundations.md) | Alignment, wrapping, visual separation and colour; TUI-A1–A4 and TUI-S1–S3 |
| [Wording and terms](wording.md) | TUI application of the shared W/I/U rules, terminology and examples |
| [Palettes](palettes.md) | Semantic colour roles, built-in palettes and user-defined colours |

The component contracts and foundations here are normative for new TUI work.
Cross-project [wording](../../specs/wording.md),
[identity](../../specs/identity.md) and [interaction](../../specs/interaction.md)
remain their owning documents; their approval status is unchanged. The
[application specification](../../netfyr-tui/specs/tui.md) owns netfyr-specific
flows and backend capabilities. This library cannot create a networking
capability or override a reviewed plan's authority.

## Code and examples

The crate exports [dropdown](src/dropdown.rs), [setting rows](src/setting_row.rs),
[action footers](src/footer.rs), [flame](src/flame.rs),
[activity indicators](src/animation.rs), [traffic/replay lanes](src/lanes.rs)
and optional [font glyphs](src/glyphs.rs).
Renderers accept display data, styles and animation ticks. Applications retain
input, network operations, preferences and evidence validation.

From this directory:

```sh
cargo test --locked --all-targets
cargo run --locked --example gallery
```

The [interactive gallery](examples/gallery.rs) previews the shared components
with offline fixtures. Choose an entry with arrows and Enter; Space pauses an
animation, and Esc returns to the catalogue. Dropdowns retain their editing,
filtering and commit/cancel behavior. `NO_COLOR` removes assigned colors while
preserving text, markers and underline. No network or preferences are accessed.

Open a specific example with `--fixture flame`, `--fixture activity`, or another
ID listed by `--help`.

The glyph example defaults to standard characters. With the **netfyr symbols**
companion font installed and a terminal that supports font fallback, opt in with:

```sh
cargo run --locked --example gallery -- --fixture glyphs --glyphs netfyr
```

Use `--glyphs standard` for the default fallback; either mode can be combined
with `--snapshot`. Font fallback lets the terminal keep its normal text font.
The library performs no host font detection; applications choose the glyph set:

```rust
use netfyr_tui_design::glyphs::{Glyph, GlyphSet};

let mark = GlyphSet::Netfyr.character(Glyph::Flame);
```

`GlyphSet::Standard` is the default. `Glyph` provides `Flame`, `RightSolid`,
`RightOutline`, `LeftSolid` and `LeftOutline`, with `*`, `>`, `>`, `<` and `<`
fallbacks. The companion maps these five shapes to U+100000–U+100004, outside
the Nerd Font and Powerline ranges. The original font mappings remain intact.
All font glyphs use the OFL; see [licenses and marks](../LICENSES.md) and the
[companion font source](../font-sources/symbols/README.md). The application enables
the header flame and breadcrumb glyphs when the companion and its five characters
are available locally; its settings file allows an explicit override. Availability
does not guarantee that every terminal honors font fallback. The standalone
gallery retains explicit selection.

For a deterministic text snapshot without a terminal:

```sh
cargo run --locked --example gallery -- --snapshot
```

Snapshots omit colour and underline; buffer tests verify those styles.

The design site's `/components/tui/` catalogue plays exported frames from these
same renderers. Regenerate
them from the repository root after changing a shared component or gallery fixture:

```sh
cargo run --locked --manifest-path tui/Cargo.toml --example gallery -- --export-previews > web/tui/previews.json
```

The export includes a motion-off frame and complete animation cycles. The browser
only paints supplied terminal cells; it does not recreate the animation logic.
Its glyph preview exports both sets and uses the bundled netfyr symbols font when
available, so visitors do not need a local installation.

Capture the dropdown screenshots for the design site in Kitty, at 48×16 cells
with Noto Sans Mono, 16 pt. Generate the PNGs from the repository root with
`python3 tui/scripts/capture-gallery.py`. This requires Cargo, fontconfig, the
Noto Sans Mono font, a display and Kitty with its `screenshot` remote command.
The script opens its own hidden terminal and controls it through a private
socket; it does not send input to existing windows.

To record dropdown and settings interactions as GIFs, run
`python3 tui/scripts/capture-gallery.py --gifs`. This also requires ImageMagick.
It drives the actual gallery keys, checks the resulting terminal text, captures
each interaction, and encodes a loop with readable pauses. It writes six GIFs
and a settings poster; the existing dropdown PNGs stay unchanged.

Do not treat hand-drawn diagrams or old screenshots as the implementation.
Change the shared renderer, update its example and affected adapter tests, and
record the rule and reason in the same change. Components must remain usable
at 32×12, with Unicode, without colour and while resizing.
