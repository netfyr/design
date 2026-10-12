# Review software

Use the source-family dependencies plus SciPy for raster connected-component tests.
The pair worker additionally needs a C compiler and native HarfBuzz.
No native executables or fonts are included.

```bash
python sources/audit/invariants.py --before ./build-0504/fonts --after ./build-0505/fonts --out ./audit/invariants.json
python sources/audit/check_shapes.py --before ./build-0504/fonts --after ./build-0505/fonts --out ./audit/characters
python sources/audit/curve_checks.py --recipes ./netfyr-family-expansion/sources/recipes --before ./build-0504/fonts --after ./build-0505/fonts --out ./audit/curves.json
python sources/audit/run_target_pairs.py --before ./build-0504/fonts --after ./build-0505/fonts --invariants ./audit/invariants.json --output ./audit/pairs --jobs 4
python sources/make_review.py --before ./build-0504/fonts --after ./build-0505/fonts --output ./review
```

The geometry and raster checks are finite evidence, not independent typography criticism.
