# Component catalogue

Choose a component by the user's task. Reuse its contract and renderer; a new
view does not justify inventing another focus marker, input style or notice.

| Component | Use and required states | Current implementation |
| --- | --- | --- |
| Searchable dropdown | Interfaces, finite form values and Settings choices. Value, candidate, ready/loading/empty/no-match/error; corrected and cancelled input. [TUI-D1–D6](dropdown.md). | **Shared Rust component:** [dropdown](src/dropdown.rs); two application adapters |
| Navigation and breadcrumbs | Peer task destinations plus real object/action parents. Preserve selected object and drafts; Escape reaches the represented parent. Do not add a Home screen solely for a breadcrumb. | [Application shell](../../netfyr-tui/src/ui.rs), [controller](../../netfyr-tui/src/app.rs); W2, U2–U4 |
| Inventory and selected details | Scan comparable objects, then inspect one. Fixed heading/value columns, active selection, no matches, refresh, retained identity, pinned detail title and complete values. | [Inspection](../../netfyr-tui/src/ui/inspection.rs), [Paths](../../netfyr-tui/src/ui/paths.rs); TUI-A1–A4 |
| Contextual object actions | Edit the selected supported object from its list, overview or details. Prefill its identity. Explain an unsupported selected type briefly; never retarget a pending plan. | [App](../../netfyr-tui/src/app.rs), [shell](../../netfyr-tui/src/ui.rs); W2, W3, U2 |
| Text input | Free text, numeric values, addresses and queries. Visible label/cursor, in-place correction, retained draft, syntax help and adjacent error. Finite values use the dropdown instead. | [Text editor](../../netfyr-tui/src/text_input.rs), [forms](../../netfyr-tui/src/ui.rs); W4, W6 |
| Setting row and binary toggle | Label/value alignment, visible selection and On/Off values. Application owns keys, session effect and saving failures. Do not use a toggle for mutation approval. | **Shared Rust component:** [setting_row](src/setting_row.rs); [Settings adapter](../../netfyr-tui/src/ui/settings.rs); W3, W4, TUI-A1–A3 |
| Action footer | Discover the current focus's actions. Complete key/action pairs, a visible content boundary, one continuous panel background including borders and unused rows, equal approval/decline emphasis, truthful overflow hints. Printable shortcuts disappear while consumed as input. | **Shared Rust component:** [footer](src/footer.rs); [Shell adapter](../../netfyr-tui/src/ui.rs) retains contextual actions and consent policy; W4, TUI-S1–S3 |
| Facts and evidence | Read a result once. Labelled values, aligned comparable fields and optional relevant diagnostics. Omit absent optional facts and empty headings; retain incomplete/unknown requested results. | [Evidence](../../netfyr-tui/src/ui/evidence.rs), [core evidence](../../netfyr-tui/src/ui/evidence/core.rs); W1, W5, W9 |
| Change review and receipt | Show target, additions/removals and relevant consequences before consent. Long reviews require reading; editing invalidates the old plan. A no-op completes without apply. Result/error/unknown outcome remains reachable. | [Review renderer](../../netfyr-tui/src/ui.rs), [engine](../../netfyr-tui/src/engine.rs); W3, W5–W7 |
| Notice and field error | Explain a condition that affects the task, an actual failure or correction. Keep the reason and implemented recovery near their owner. Do not narrate routine success or require acknowledgement without consequence. | [Shell and forms](../../netfyr-tui/src/ui.rs), [Settings](../../netfyr-tui/src/ui/settings.rs); W6, W9 |
| Flame | Decorative terminal rendering of the supplied mark, with a static master when motion is off. | **Shared Rust component:** [flame](src/flame.rs); separate [mark notice](assets/flame-NOTICE.txt); I7, TUI-S2 |
| Font glyphs | Optional single-cell flame and left/right solid or outlined separators from the netfyr symbols companion. Hosts choose the glyph set and retain standard-character fallbacks. Text, focus and state remain readable in either set. | **Shared Rust component:** [glyphs](src/glyphs.rs), `GlyphSet::character(Glyph)`; used in the [application header and breadcrumbs](../../netfyr-tui/src/ui.rs) with local companion-font detection and a settings-file override; [font contract](foundations.md#optional-font-glyphs), TUI-A2, TUI-S2 |
| Activity indicators | Spinner, cycling dots or a travelling pulse beside pending work. These do not measure progress or completion. | **Shared Rust component:** [animation](src/animation.rs); spinner used by the application, dots/pulse are new gallery variants; W5, TUI-S2 |
| Traffic and trace lanes | Supplement measured values. Interface motion follows observed throughput; trace motion replays measured RTT. Idle/stale samples stop; motion off preserves data. Never invent hidden devices or adjacent-hop timings. | **Shared Rust component:** [lanes](src/lanes.rs); [Traffic](../../netfyr-tui/src/ui/traffic.rs) and [Paths](../../netfyr-tui/src/ui/paths.rs) retain evidence validation; I6, W5, W7 |
| Palette | Apply the semantic roles consistently, including selection and boundaries. Standard/Accessible are built-ins; Custom comes from validated settings. NO_COLOR overrides all palettes. | [Theme](../../netfyr-tui/src/theme.rs), [palette contract](palettes.md); TUI-S2–S3 |

All interactive entries follow [TUI-K1–K5](bindings.md). New components inherit
those key families and focus rules; their handlers and hints are reviewed together.

Entries marked **Shared Rust component** are exported by this crate. The remaining
entries are usage contracts mapped to application code. Extract additional
components by preserving their contracts and updating their application adapters.

The [interactive gallery](README.md#code-and-examples) exercises the exported
components. The website plays dropdown/settings recordings and deterministic
Rust-rendered frames for the other components, including glyphs with standard
fallbacks.

Every component review covers entry, normal result, empty/missing data, failure,
correction, cancellation, return and resize where relevant.
