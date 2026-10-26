# Semantic palettes

Use named roles rather than hard-coded widget colours. The current
[theme implementation](../../netfyr-tui/src/theme.rs) owns the built-in RGB
values; [settings](../../netfyr-tui/src/settings.rs) validates user definitions.
Shared components receive these styles from the host.

| Role | Use |
| --- | --- |
| `background` | Page background and inverse keycap text |
| `surface` | Group/input/option-panel surface |
| `selected` | Keyboard candidate or focused row background |
| `foreground` | Primary text |
| `muted` | Secondary text that remains readable |
| `accent` | Interactive emphasis and field-value styling |
| `success` | Reported successful/positive state, accompanied by words |
| `warning` | Limitation or uncertainty, accompanied by its meaning |
| `error` | Failure, accompanied by its reason |
| `border` | Required boundaries and rules |

Standard uses the netfyr identity palette with readable separators. Accessible
uses higher-contrast neutral text and cyan/amber/lilac status colours. Both retain
words, markers and shape cues. Built-in contrast checks cover actual page,
surface and selection backgrounds; see [TUI-S3](foundations.md#separation-and-colour).
NO_COLOR overrides every palette. Motion and Eye candy are independent choices.

## Supply your own palette

Add `custom_palette` to `$XDG_CONFIG_HOME/netfyr-tui/settings.json`, or
`~/.config/netfyr-tui/settings.json` when XDG_CONFIG_HOME is unset. Merge it into
the existing object to retain other preferences. Every role is required and
accepts exactly `#RRGGBB` hexadecimal colour text:

```json
{
  "palette": "custom",
  "custom_palette": {
    "background": "#10151c",
    "surface": "#1b2530",
    "selected": "#293d50",
    "foreground": "#ffffff",
    "muted": "#d4dce6",
    "accent": "#ff9c52",
    "success": "#77caff",
    "warning": "#ffd166",
    "error": "#e6afff",
    "border": "#93a5b8"
  }
}
```

Restart after editing the file. A valid definition adds **Custom** to the
searchable Settings → Colour palette control. Setting `palette` to `custom` in
the file activates it on startup; leaving a built-in value keeps Custom available
for later selection. Switching presets and saving unrelated preferences retain
the definition. No settings file is read during rendering.

Invalid colours, missing/unknown roles or Custom without a definition produce a
load error naming the configuration problem. The application uses its existing
defaults-and-notice fallback. Correct the file before saving another setting,
because a later save writes the active session preferences. RGB values are
canonicalised to lowercase when saved.

Custom colours are user-controlled, so built-in contrast guarantees do not apply
to them. The application does not silently replace a valid user's colour with a
preferred one. NO_COLOR and non-colour selection cues continue to work.
