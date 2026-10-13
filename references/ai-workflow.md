# AI colour selection and grid extraction

This optional route implements the paper-figure-csv-ai workflow on top of THU.
AI edits identify one visible series; measurement is anchored in original image
pixels. No numeric reference is provided to an image model or extractor.

## Reproduce all published results without an API key

```bash
python -m pip install -e '.[ai,dev,pdf]'
python -m pytest -q
python scripts/benchmark.py --ablation --require-90
python scripts/validate_paper.py
python scripts/validate_flux.py
python scripts/validate_ai.py --require-90
digitizer grid --config benchmarks/cases/p01/config.json --out runs/grid/p01
python scripts/build_showcase.py
python scripts/build_ai_showcase.py
```

`benchmarks/ai/` contains actual model-returned images, prompts, request metadata,
source configs, reviewed landmarks and hashes. `validate_ai.py` runs no network
requests. Every recreation reads the emitted CSV, not the reference values.

## New figure: prepare → edit → review → extract

```bash
# Review figure.json first; select exactly one existing series.
digitizer ai-prepare --config figure.json --series measured_NEE \
  --target 'thin solid BLUE measured NEE; not red dashed estimates or the blue uncertainty band' \
  --out runs/new-edit
# Credentials are provided privately through APIYI_API_KEY, never committed.
digitizer ai-edit --bundle runs/new-edit --provider apiyi --model gpt-image-2.5-vip
# Inspect original.png and generated.png, then complete review.draft.json and
# save the completed review as review.json. See the skill for the JSON schema.
digitizer ai-extract --bundle runs/new-edit --review runs/new-edit/review.json \
  --columns 49 --out runs/new-extraction
```

Use `--mode markers` with an explicit marker colour, shape and outline for
scatter. The source config determines the THU marker route. Its shape detection
runs on the original before AI filtering; a generated dot cannot manufacture a
marker from a smooth fitted curve. Fully hidden/fused marks stay unsupported.

For Nano Banana Pro through APIYI explicitly choose
`--provider apiyi --model gemini-3-pro-image-preview`. Direct Google uses
`--provider gemini` and `GEMINI_API_KEY`; that adapter is unit-tested but was not
live-tested in this release. Both published models were called through APIYI.
No model is silently changed after failure. There are no automatic paid retries.

Provider names are provider-specific identifiers, not a claim about first-party
OpenAI availability. The APIYI model list on 2026-10-13 contained
`gpt-image-2.5-vip`. Two calls to the historical `gpt-img-2.5-vip` returned 503;
those failures are retained in `benchmarks/ai/failed-requests.json`.
[APIYI platform](https://imagen.apiyi.com/) ·
[Google image API](https://ai.google.dev/gemini-api/docs/image-generation).

## Prompt v2

The prompt locks geometry, preserves external axis context, clears reviewed
legend regions, selects one target, erases unrelated plot elements and forbids
hidden-data reconstruction. Existing red distractors must be removed before
red-pixel extraction. Inputs are padded at (32,32) on a 1536×1024 canvas without
resampling. Inputs larger than 1472×960 require explicit crop/render and a fresh
calibration. No generated grid lines are used for measurement.

A/B control: `ai-prepare --legacy-prompt` retains other plot content. It is not
recommended for production extraction. The salt-marsh A/B uses the same
prepared image and model, one captured output per prompt. It does not isolate
individual clauses or estimate stochastic variance; no general prompt-improvement
claim should be inferred from a single paired example.

## Registration and original-pixel checks

Review the actual returned image, even if dimensions match. The review binds
source and generated SHA-256 and contains ≥4 measured matching landmarks spanning
≥70% of plot width and height. An axis-aligned transform is fitted from those
landmarks, with a maximum residual of 1.5 original pixels. Dimensions alone
never define a transform. Nano Banana's 2528×1696 output required this review.
Reject nonlinear deformations rather than inventing better calibration.

Registered red pixels define a prior. A default 3-pixel neighbourhood intersects
with original target-colour evidence and the original exclusion mask. Line
tracing uses that intersection; scatter candidates must already be valid shapes
in the original. Radius is explicit, limited to 0–5 pixels, and recorded.
The source is never rewritten. Proximity does not prove identity at crossings
or between nearby same-colour series; visually review final overlays.

`support-overlay.png` shows green eligible original colour pixels and magenta
AI red pixels without nearby unexcluded original target-colour support. Green
pixels are candidates, not all accepted observations. The unsupported-red
fraction is a cleanup diagnostic, **not accuracy, precision or hallucination rate**.

## Frozen evaluation, 2026-10-13

| Case | Evaluation | AI-assisted | Direct THU |
|---|---|---:|---:|
| a01 / r03 markers | one-to-one F1 @ 1% normalized axis distance | 96.7742% (15/16) | 96.7742% |
| a02 / f05 winter | no independent author values | unscored, 759 numeric columns | unscored, 792 columns |
| a03 / f04 Stein only | 401 positions; PDF path; ≤1% y-axis range | 97.5062% (391/401) | 97.5062% |

Missing samples count as misses. Scored cases have no improvement over their
THU baselines; AI makes a target-selection/evidence workflow available.
A/B a02 unsupported-red fraction: 34.8133% → 18.8671%; numeric columns: 788 → 759.
The smaller support region trades coverage for stricter selection. No independent
accuracy is claimed for a02. AI scores are not included in the original 11-case
macro. This is a development set, not held-out generalization or a model ranking.

## Two kinds of grid

- Lines: `digitizer grid --columns 49` returns `grid_column`, `grid_x`, nearest
  original `sample_x_pixel`, actual calibrated x/y, status and source hash.
  There is no interpolation. The plot bounds, not just the drawn stroke extent,
  define the grid; empty boundary samples are expected.
- Heatmaps: grid bounds, labels and colourbar are measured from the original.
  `grid.csv` retains row, column, label, value or saturation interval, status and
  source hash. Recolouring quantitative heatmap cells would corrupt their values.
  The 672-cell p01 has 578 numeric cells and 94 saturated intervals. Separate
  workbook validation gives MAE 0.003288, raw score 84.60%, rounding-aware 98.79%.

## Evidence and licenses

`source.png` is the unchanged source. `prepared.png` is a clearly labelled
masked/padded API input; `generated.png` is a model intermediate.
`selection.png`, accepted/unsupported masks, transforms and request hashes retain
provenance. `data.csv` points to the original source; `grid.csv` is an additional
sampling view, not a substitute for the dense extraction.

Cases a02/a03 adapt f05/f04; paper attribution and figure licenses continue to
apply, including **CC BY-NC-SA 2.5 for a03**. a01 is the supplied manuscript task,
not a newly published paper. See [sources](../benchmarks/SOURCES.md). Figures
remain demonstrations and do not register new FLUX stations.
