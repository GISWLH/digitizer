# FLUX paper validation

Eight panels, two papers, twelve extracted curves. These are assisted development
examples, selected from the existing local FLUX paper library. They are not a
held-out benchmark or a claim of eight new observation sites.

## Two distinct evidence levels

- **f01–f04**: Veenendaal et al. (2007), Fig. 10a–c and Fig. 11. Rendered at
  4 pixels/PDF point. Independent reference vertices come from the original PDF
  drawing objects, stored in `reference.csv`. The raster extractor receives only
  `input.png` and `config.json`; `validate_flux.py` opens references after extraction.
- **f05–f08**: Mayen et al. (2024), Fig. 5a–d. Cropped from the PDF's embedded
  raster image, without recolouring or upscaling. There are no vector paths or
  independent author values. These panels are **unscored**. Pixel support,
  completeness and visual plausibility must not be reported as accuracy.

## Frozen scoring rule

For each vector-backed series, take 401 uniformly spaced x positions over the
reference path within the plot. Round to the nearest extracted pixel column.
Interpolate the separate PDF path at that column; do not interpolate extracted
values. A hit has absolute y error no greater than 1% of the calibrated plot's
full y range. Missing columns and unsupported samples are misses. The case score
is the arithmetic mean of its two series. Report each series' numerator,
denominator, coverage and normalized MAE. Mask ablation changes exclusions only.

PDF geometry is a reference for the **published drawing**, not an independent
check of instrument accuracy or raw measured values. Calibration and target
colours are visually reviewed. Dense curves can be hidden by the other series;
reference paths still include those spans, so the score penalizes missing data.
No reference-based filling or post-hoc removal of these hard points is permitted.

The current cumulative NEE case scores 95.39%. The three dense daily panels score
52.24%, 63.84% and 53.87%. They remain visible as challenge cases. All four
vector-backed cases average 66.33%; do not generalize the successful single-case
score to this group. Four unscored raster panels are excluded from that mean.

## Scientific semantics and station status

Veenendaal's daily NEE is EC-derived and includes gap filling. Reco and GEP are
partitioned estimates. The cumulative NEE is an integrated series. Preserve
these distinctions when reusing the extraction; none is labelled raw independent
observations. X uses unwrapped Julian day: 2004 day-of-year, then 366 + 2005
 day-of-year, calibrated from published ticks. It is not a calendar date field.
The upper panels use their own tick positions with the shared lower-panel labels.

Mayen's blue line is measured NEE averaged by season and time of day in 2020.
Red NEEmarsh, green GPP and black Reco are estimated quantities and are excluded
from this extraction. The shaded area is a standard deviation, not another series.
X is hour of day. PDF page numbers are one-based.

All output rows are `digitized_approximation`. Per-panel provenance records the
source DOI, PDF SHA-256, crop, calibration, license and observation/estimate
semantics. They are demonstration outputs only; the FLUX station baseline and
DOI/research ledgers are unchanged. Any future admission to `flux/Result/Output`
must independently complete station-baseline matching and the standard 17-column
station export. A missing name match alone does not prove a new station.

## Reproduce

```bash
python scripts/validate_flux.py
python scripts/validate_flux.py --cases f04 --require-90
python scripts/build_showcase.py
```

All eight input images and configurations are bundled. For reference-generation
audit, obtain the two official PDFs listed in each `provenance.json`, preserving
the recorded SHA-256, then use `scripts/prepare_flux.py --papers PATH`. The path
expects the original local library's two hash-named folders (see script). This
preparation step is not used by extraction or CI.

Recreated images read only the emitted CSV. Gaps stay gaps. Calibration/rounding
uncertainty in `extraction_error` is distinct from the independent score.
