# Accuracy protocol

The primary suite contains **all 11 frozen line/scatter cases** from the local
Digitizer benchmark: eight synthetic fixtures and three manuscript panels.
Configs are visually assisted and development-tuned. They are not a held-out
publication sample, and the scores do not measure autonomous OCR/legend detection.

1. Extraction sees only the image, calibration and exclusions.
2. After saving the CSV, the evaluator reads the independent reference file.
3. Input, config, extraction and reference hashes accompany each result.
4. All cases count equally in the macro average; no case is removed after failure.
5. A release gate requires **every primary case ≥90%**.

## Lines

401 uniformly spaced x samples (log-uniform on log axes). Use the closest
original image column, without filling a missing column from neighbours.
Accuracy = samples with absolute y error ≤1% of the declared y-axis range /
all visible reference samples. Missing samples are misses. Reference endpoints,
known opaque occlusions and 2-pixel step discontinuities follow fixed declared
rules; errors are never excluded after inspecting them. Coverage, normalized MAE
and hidden-span emitted values are reported separately.

## Scatter

Normalize x and y by their axis ranges (transformed x on log axes). Match
predictions to references one-to-one with a distance gate of 1% and gated Hungarian
assignment. Report precision, recall and F1. Missing and spurious points both
reduce F1. Unauthorized candidate points are not accepted matches.

## Mask ablation

Run the exact same enhanced engine and config with exclusions enabled and
disabled. This isolates the contribution of masks. It is **not** a comparison
against all upstream THU features; THU and this workspace already had rectangle
exclusions before this project.

## Supplementary real-paper source validation

Nature Medicine Fig. 4c has 672 cells: 578 numeric colours and 94 saturated
endpoint colours. The supplied author workbook rounds correlations to 0.01.
Report both (a) raw error ≤.006, 1% of the .6 colour range, and (b) distance from
the author's rounding interval [value−.005, value+.005] ≤.006. This distinction
is declared rather than silently relaxing the primary metric. The 94 endpoint
interval checks are reported separately and never treated as exact values.
This validation is supplementary and does not enter the 11-case headline score.

## Reproduce

```bash
python -m pip install -e '.[dev,pdf]'
python -m pytest -q
python scripts/benchmark.py --ablation --require-90
python scripts/validate_paper.py
python scripts/build_showcase.py
```

The primary benchmark is fully offline. PDF and OCR are optional. Validation
workbooks are never imported by the engine or its recreation renderer.

`benchmarks/run-environment.json` records the local software versions and code
hashes used for this release. `requirements.lock` freezes the development
environment; use `python -m pip install -r requirements.lock` before installing
the repository when reproducing that environment. Platform-specific native
wheels can differ; the accuracy gate is also run independently on Linux CI.
