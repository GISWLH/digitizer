# Contributing

Useful contributions are real paper figures with reviewable calibration,
independent numerical references, and a clear description of a failure.
Start with a [figure case](https://github.com/GISWLH/digitizer/issues/new?template=figure.yml)
or [bug report](https://github.com/GISWLH/digitizer/issues/new?template=bug.yml).

## A reproducible change

1. Fork, create a branch, install `python -m pip install -e '.[dev,pdf]'`.
2. Keep source images unchanged. Record DOI, figure/panel, PDF page, image hash,
   axes, units, series semantics and reviewed legend exclusions.
3. Keep reference data separate from extraction. State the reference's provenance
   and license. No reference means no accuracy percentage. Include failures.
4. Run `make check`. For gallery changes, run `make showcase` after the complete
   benchmarks, then inspect desktop and mobile views.
5. Submit a pull request describing the failure, resulting behavior, checks and
   remaining limitations. Do not commit credentials, personal files or full PDFs.

The original eleven regression fixtures stay stable; adding FLUX cases does not
silently change their denominator. Mark protocol changes explicitly and retain
prior results. Algorithm changes should include a small meaningful regression.

README.md, README.en.md and README.ja.md describe the same features, commands and
scientific limitations. Update all three when behavior or claims change.

Software contributions use MIT. Figure and reference-data licenses remain
separate. Do not relabel CC BY-NC-SA assets as MIT. Derived material must retain
attribution, license, modification notice and applicable reuse restrictions.
