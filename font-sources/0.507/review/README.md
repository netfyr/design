# Individual glyph review

The JSONL ledgers record actual subagent decisions per Unicode character, with the SHA-256 of the viewed proof. Each proof includes all 28 netfyr styles and reference glyphs selected from their actual cmap; there is no fallback. Rendering alone does not constitute review.

The initial 0.506 proofs incorrectly label the reference outlines as having the same em scale as netfyr. Netfyr direct outlines use 64 pixels per em; reference direct outlines use 76 pixels per em. The reference fonts share a scale with each other. Use normalized bounds and advances in the case JSON for quantitative comparisons. The proofs remain unchanged to preserve the evidence hashes.

Review distinguishes required character features from valid typeface variants. Combining marks also need shaped contexts; controls and spaces need semantic and advance checks. Private-use symbols are compared with the project's mark and separator geometry. This is agent review, not native-reader or vendor certification. Reference outlines are not imported into the font.

Coverage is complete only when every one of the 2,225 codepoints has an individual decided entry and every repair has reviewed after-evidence. Pending and needs-context entries must not be counted as approval.

`symbol_native_review.py --fonts /path/to/fonts --output /path/to/proofs`
renders each repaired symbol in all 28 styles at 20 px/em and four horizontal
phases. `--codepoints 2224,2226` restricts it to explicit hexadecimal characters.
It uses this release's `sources/review_glyphs.py`, exact-cmap local references,
nearest-neighbour enlargement, per-font hashes, and canvas-bound checks. Run it
with the same Cairo, Pillow and FontTools environment as the primary renderer;
the named reference fonts must be installed locally. Its evidence supplements
the primary and shaped-context proofs rather than replacing their release gate.

Semantic reference for right-side combining marks: [Unicode character data](https://www.unicode.org/Public/17.0.0/ucd/UnicodeData.txt) assigns U+0315, U+031A and U+0358 canonical combining class 232; [property value aliases](https://www.unicode.org/Public/17.0.0/ucd/PropertyValueAliases.txt) names that class Above_Right.

In the initial contextual proofs, the large outline follows the named context; the small text line always shows the first (a-based) context. Final contextual proofs show the named context at both sizes.
