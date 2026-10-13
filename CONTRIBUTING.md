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

## AI colour-selection cases

Use `digitizer ai-prepare` to create a reviewed, source-bound bundle. Paid image
calls are explicit (`ai-edit`); never add automatic live API calls to tests or CI.
Publish the exact prompt, prepared image, generated image, sanitized request
metadata and reviewed landmarks when redistribution rights permit. Keep keys,
raw API responses, private paths and complete restricted PDFs out of commits.

Replay with `scripts/validate_ai.py`. Report the same-target direct THU baseline,
missing-point denominator and independent-reference provenance. A prompt A/B
must use the same input and disclose generation counts. Colour support, attractive
output and agreement with another extractor are not independent accuracy.
