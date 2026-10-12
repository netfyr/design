# Reproduce the review

Requires actual 0.505 and 0.506 locally built TTFs. The files are not included.
The scripts do not synthesize an untested font from the proof images.

```bash
python check_invariants.py --before /path/to/0.505/fonts \
  --after /path/to/0.506/fonts --out ./invariants.json
python check_shapes.py --before /path/to/0.505/fonts \
  --after /path/to/0.506/fonts --out ./shapes
python run_target_pairs.py --before /path/to/0.505/fonts \
  --after /path/to/0.506/fonts --invariants ./invariants.json \
  --output ./pair-audit --jobs 4
```

Dependencies follow the full design kit. The shape checker additionally uses
SciPy. The native pair scanner builds `target_pairs.c` with a C compiler and
links the installed HarfBuzz library. It classifies combining/control/technical
and complex pairs separately; `passed_screen` is not a vector-collision or
optical-spacing certificate. Code and command logs identify the sampling method.

To regenerate the report assets, arrange the two local builds under a review
work directory as `before/fonts` and `after/fonts`. Set
`NETFYR_REVIEW_WORK` to that directory and `NETFYR_REVIEW_OUTPUT` to the desired
review output folder, which must contain `proofs`, `research` and `validation`
subdirectories. Run `metrics.py`, then `make_proofs.py`, then `make_review.py`.
The printed review counts correspond to this recorded release; rerun and review
the validation before reusing those statements for any later changes.

The reference proof generator expects Noto Sans Black and Noto Sans Mono Black
under `/usr/share/fonts/truetype/noto/`. Inspect the available versions and update
the reference paths/labels deliberately on another machine. Reference fonts are
not part of this package. The large A samples in the PDF are vector outlines;
normal report text uses the built netfyr Regular/SemiBold.
