# netfyr 0.507 reviewed source

Review and repairs are complete. `RELEASE.json` records the exact 28 final TTF
reviewed hashes, and `review/final-verification.json` binds passing individual
decisions to those files and their repair sources. Published font hashes are
recorded separately after the OFL metadata amendment.

The initial individual review covers all 2,225 encoded characters in all 28
styles. The 512 initial repair decisions led to 691 changed encoded characters,
including dependent compositions. Their final proofs and six internal variants
pass individual visual review. Context sheets cover 469 shaped examples; the
244 changed symbols also have native 20-pixel proofs at four subpixel phases.
All five validation tracks and all 28 WOFF2 exports pass. The three regenerated
PDFs contain 118 pages in total and passed text-boundary and rendering checks.

`sources/build_reviewed.py` first reproduces the original 0.506 binaries exactly,
then applies explicitly registered outline and accent-positioning corrections.
The original coordinate recipes remain at 0.506. This also corrects the four
original upright fonts, which the baseline builder copies from the reference kit.
Reference font outlines are used for comparison and are not imported.

Use the original 0.401 reference archive and the pinned Python requirements.
Inkscape 1.4, Cairo, FreeType, and HarfBuzz must be available. From the repository
root, create a Python environment and build into a fresh directory. Set
`NETFYR_REFERENCE` to your original archive; it is deliberately not distributed
in this repository.

```sh
python3 -m venv .venv
.venv/bin/pip install -r font-sources/0.507/sources/requirements.txt
export NETFYR_REFERENCE=/path/to/netfyr-type-kit.zip
PATH="$PWD/.build/native/bin-1.4:$PATH" \
  .venv/bin/python font-sources/0.507/sources/build_reviewed.py \
  --reference "$NETFYR_REFERENCE" \
  --output .build/fonts-0.507 --jobs 4 --documents
.venv/bin/python font-sources/0.507/sources/export_web.py \
  --build .build/fonts-0.507
```

An exact existing baseline can be reused with
`--baseline-build .build/fonts-0.506-matched`. Its 28 hashes must match
`baseline-font-hashes.json`; the supplied reference archive is still verified.
On the original Linux build environment, `scripts/prepare_inkscape_14.sh`
prepares the pinned Inkscape binary under `.build/native/`. It checks its shared
libraries before use; other platforms need a compatible native setup.

Build reports declare every changed glyph, advance, and layout operation. The
validation checks metadata, canonical shaping, outline geometry, technical cells,
and unchanged HarfBuzz runs outside the declared positioning or advance changes.
Document generation also exports 62,300 character/style rows from the actual
corrected fonts.

Individual review uses `sources/review_glyphs.py`, exact-cmap reference selection,
all 28 styles, and contextual proofs for combining marks. Reference fingerprints
are in `review/reference-inputs.json`. `--baseline-evidence-labels` reproduces the
documented original proof-label and small-context errata; omit it for corrected
after-proofs. Proof images stay in local build directories; their SHA-256 hashes
are retained in the review ledgers.

`sources/audit_review.py --require-complete` requires decisions for all 2,225
encoded characters and no unresolved cases. `sources/verify_reviewed_release.py`
requires individual passing after-decisions, contextual evidence, and matching
font hashes for every changed character and internal variant. Importing a 0.507
build is blocked until that gate writes a complete final verification report.
The gate also checks the six repair-source hashes recorded by the build; an
older candidate cannot be paired with newer source files.

The fonts and source code in `sources/` use SIL OFL 1.1; see `OFL.txt`.
Standalone artwork in `assets/` remains reserved as described in the repository's
`LICENSES.md`. Reference font outlines are not redistributed.

The original review and validation reports retain their original font hashes.
The license publication step changes only copyright/license name records and the
font checksum. Its report records both the reviewed and published hashes, checks
every unchanged raw table, and preserves unrelated name records. WOFF2 exports
are then checked against the licensed TTFs. This avoids treating changed metadata
as a repeated visual review.

`sources/import_release.py --release font-sources/0.507 --build BUILD` imports a
canonical reviewed build into `public/`. Apply the OFL publication step after
importing and before preparing a public release. The historical baseline builder
still reproduces its original metadata so its exact-hash comparison remains valid.

From the repository root, stage the licensed publication in a fresh directory.
Set `NETFYR_COPYRIGHT_HOLDER` to the exact holder recorded in `OFL.txt`:

```sh
.venv/bin/python font-sources/0.507/sources/publish_ofl.py \
  --build .build/fonts-0.507 \
  --output .build/fonts-0.507-ofl \
  --copyright-holder "$NETFYR_COPYRIGHT_HOLDER" \
  --copyright-year 2026 --license-file OFL.txt
cp -a .build/fonts-0.507-ofl/public/fonts/. public/fonts/
cp .build/fonts-0.507-ofl/RELEASE.json font-sources/0.507/RELEASE.json
cp .build/fonts-0.507-ofl/OFL.txt font-sources/0.507/OFL.txt
npm run check
```

The publication command verifies the canonical inputs before writing anything,
creates a fresh output directory, and includes OFL.txt and NOTICE.txt in the ZIP.
It never modifies the reviewed build. The website check rejects a canonical
import until its licensing metadata has been applied and verified.
