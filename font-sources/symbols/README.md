# netfyr symbols

This symbols-only companion contains the five existing netfyr Mono symbols at
supplementary private-use codepoints. It has its own family name and revision,
1.000. The original 28 fonts, their 0.507 download, review and license-amendment
records remain unchanged.

| Character | Symbol | Original mapping |
| --- | --- | --- |
| U+100000 | Flame | U+E000 |
| U+100001 | Right solid | U+E0B0 |
| U+100002 | Right outline | U+E0B1 |
| U+100003 | Left solid | U+E0B2 |
| U+100004 | Left outline | U+E0B3 |

The companion exposes no Latin, space or legacy private-use characters. It has
only those five mappings and an unencoded `.notdef` glyph. Its fallback can supply
symbols without replacing the terminal's normal text font. The mappings avoid
the known Nerd Font and Powerline ranges; private-use values are not globally
reserved. A terminal may implement its own font matching, so an installed font
does not establish support in every terminal. With SSH, the font is needed on
the computer displaying the terminal.

The source is the published `netfyrmono-Regular.ttf` from 0.507, SHA-256
`242ae4bb9d29636c4105ac1c745421fdf73f181f5803bab3cc5861cf059a892f`.
The generator verifies that exact source and the matching OFL file before
building. It preserves source outlines, bearings, 640-unit advances, vertical
cell metrics and copyright/license records. Both Unicode and Windows cmap
subtables use format 12. The new identity, cmap and subset are deliberate changes;
this is a derivation check, not a repeated visual review.

The fonts, this source and this document use SIL OFL 1.1, in the repository's
`OFL.txt`. The existing reservation of standalone artwork and trademarks is
separate from the OFL rights covering these glyphs.

From the design repository root:

```sh
.venv/bin/python font-sources/symbols/build.py \
  --source public/fonts --output public/fonts/symbols
.venv/bin/python font-sources/symbols/build.py \
  --source public/fonts --output public/fonts/symbols --verify
```

The full build needs FontTools and Brotli. The checked-in outputs use FontTools
4.61.1 and Brotli 1.2.0. Each output's hash and its source/generator provenance
are recorded in `symbols-manifest.json`. TTF and WOFF2 are both checked against
the original outlines, cell metrics, cmap and OFL records. `--verify` rebuilds
in memory and requires byte-identical outputs, including the deterministic ZIP.

For a distribution package, `--ttf-only` generates the TTF, manifest and notices
without importing the WOFF2 exporter or requiring Brotli. The standalone script
can run against the original extracted 0.507 ZIP and needs no repository imports:

```sh
python build.py --source netfyr-fonts-0.507 --output symbols --ttf-only
```
