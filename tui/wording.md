# Wording, phrasing and terms

The owning rules are [W1–W9](../../specs/wording.md),
[identity I1–I8](../../specs/identity.md) and
[interaction U1–U7](../../specs/interaction.md). This reference applies them to TUI
wording and terminology. Update the owning rule when changing a cross-project
convention; do not create a competing copy.

| Context | Use | Avoid | Rule |
| --- | --- | --- | --- |
| Project name | `netfyr` | `Netfyr`, repeated program prefixes in every TUI error | I1, W1 |
| Labels/headings/hints | Sentence case, no trailing period | Title Case or full explanatory sentences in controls | W1 |
| Explanations/errors | Short factual sentences with normal punctuation | Jokes, blame, praise, generic lifecycle narration | I4, W1, W6 |
| Action | Specific verb and object: `edit config`, `Replace IPv4 addresses` | `Proceed` or `Confirm` without an adjacent named action | W2, W4 |
| Requested facts | Show values once | Success banner plus repeated result plus serialized output | W1, W5, W9 |
| Empty optional field | Omit field and empty heading | `Peer not observed`, `MAC Unknown` as schema filler | W9 |
| Requested missing result | `No reply`, `Unknown`, or a concrete failed/incomplete result | Silence that looks like success | W5, W9 |
| Source attribution | Name it when it affects interpretation, trust or recovery | `via RIPEstat` on routine controls/results/Help | W9 |
| Dropdown field value | Accent/underline; candidate has its own highlight and gutter | `· current`, prose selection badges, colour alone | TUI-D2, W7, W9 |
| Confirmation | Named action/target and `[y/N]`; explicit affirmative only | Enter approving, preselected Yes, navigation confirming | W3 |
| Key names | `Enter`, `Esc`, `PgUp/PgDown`, `Ctrl+U` | Clipped key names or hints the handler does not support | W4, W7 |
| Failed save | State that settings apply to the session, give reason and retry | Pretending the preference persisted | W6, W9 |

## Network terminology

| Term | User-facing meaning |
| --- | --- |
| Enabled: Yes/No | Administrative setting: whether the interface is enabled for use. Choices are Enabled/Disabled. |
| Carrier: Present/Absent/Unknown | Reported lower-layer signal. It is separate from administrative enablement and Internet reachability. |
| Operational state | The kernel's reported readiness state when available. Do not infer it solely from Enabled or Carrier. |
| MTU | Maximum transmission unit, displayed in bytes. |
| IPv4 addresses | The observed or requested list; replacement review must show removed addresses. |
| Estimated egress | A route lookup's chosen outgoing interface. It is not proof that every application packet took that route. |
| Trace hop / No reply | A responding hop / no response to the requested probe. Silence does not establish a broken hop or absent device. |
| Network name | Registry/ASN ownership information. It does not by itself identify hardware or prove the user's ISP. |
| Unknown outcome | An operation may have been dispatched but its effect is unconfirmed. Keep this visible until resolved or replaced. |

"Administratively up" means enabled; it does not imply carrier, authentication,
a usable route or Internet access. The Linux kernel explicitly separates
administrative and operational state. The short Enabled label is our translation
of that distinction. See [kernel operational states](https://docs.kernel.org/networking/operstates.html)
and the [implementation research](../../netfyr-tui/.reseach/controls-palettes-library.md).

The [keyboard contract](bindings.md), TUI-K1–K5, owns action keys and focus
semantics. W4 owns their spelling. Use `e edit config` and `e edit inputs`,
`Enter next` or `Enter submit` where that is the actual effect, and `Esc close`
for an open dropdown. Use `Enter details` / `Esc less detail` for diagnostic
disclosure and `r retry` for result recovery. Review keeps Enter as decline.
Do not rename the same key between screens.

## Notices and information relevance

Before adding text, identify what it helps the user understand, decide or do in
this task. If there is no concrete use, omit it even when it fits. Moving it into
Help or an expanded pane does not automatically make it useful. Preserve actual
errors, requested empty results, completeness, consequences and unknown outcomes.
Show each fact once and keep unresolved conditions reachable across navigation.

The [Linux wording research](../../netfyr-tui/.reseach/linux-wording-research.md)
records GNU, systemd, GNOME, KDE and nano sources and conflicting conventions.
These are deliberate netfyr choices, not claims of a universal Linux style guide.
