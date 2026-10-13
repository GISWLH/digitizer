---
name: digitizer
description: Digitize scientific figure images or PDF panels into auditable CSV, using THU Digitizer with precise legend exclusion. Use for calibrated lines, visible scatter markers, bars, and heatmaps.
---

# Digitizer

Turn visible figure geometry into CSV plus original, legend mask, extraction
overlay, recreation and side-by-side comparison. The primary engines are
derived from [THU Digitizer](https://github.com/Rimagination/thu-digitizer) (MIT).
This skill adds precise legend masks and a reproducible evidence workflow.

## Run

From this skill's directory, install once in an isolated environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install '.[pdf]'
.venv/bin/python -m digitizer_core.cli inspect figure.png --plot-bounds 80,30,950,650 --out figure.json
.venv/bin/python -m digitizer_core.cli extract --config figure.json --out runs/figure
```

For a PDF, render the requested page before calibrating:

```bash
.venv/bin/python -m digitizer_core.cli render-pdf paper.pdf --page 4 --dpi 200 --out page4.png
```

Choose the panel and visible representation before measuring. Verify at least
two ticks on each numeric axis, linear versus log10 coordinates, target series
colours and plot bounds on the exact input image. Read
[configuration](references/configuration.md) for the JSON contract and routes.
Use the existing configs under `benchmarks/cases/` as runnable examples.

## Legends are measurement exclusions

- Inspect all corners and the interior, including multi-column legends,
  marker keys, text annotations and panel labels. Never assume a corner is empty.
- `inspect --ocr` (optional `pip install '.[ocr]'`) proposes OCR + swatch
  candidates. `--ocr-json` accepts local OCR output. Proposals are unreviewed.
- Check the overlay against the original. Use small rectangles or polygons for
  separated swatches and labels; keep genuinely visible data between them.
  Exclude the whole background of an opaque legend that covers data.
- Use `series: ["name"]` only when an exclusion applies to that series. Preserve
  the series-colour mapping before excluding legend pixels.
- The agent can complete visual review within the user's task: fill anchors,
  colours, `review_note`, `reviewed: true` and each region's `verified: true`.
  No separate user approval is required for routine calibration or reruns.
- Masks are bound to the image SHA-256 and dimensions. A resized, cropped or
  recoloured image needs fresh inspection. Never edit a hash to bypass review.
- Do not inpaint, interpolate or import source values into a hidden span. A
  legend-covered or inseparable observation stays missing.

## Choose the extraction route

- `line`: THU continuity trace. For low-resolution colour charts, inspect a
  wider colour tolerance/sigma with chroma rejection. A long horizontal stroke
  can be data; grid suppression is opt-in. Inspect gaps and same-colour crossings.
- `scatter`, marker `filled`: THU distance peaks for compact or partly touching
  markers. A failed residual audit blocks numeric authorization; preserve that
  status and refine visibly wrong calibration/masks before rerunning.
- `scatter`, marker `hollow`: visible closed ring interiors. Broken or fully
  occluded rings are unsupported.
- `scatter`, marker `isolated`: outlined compact coloured cores separated from
  same-colour fitted curves. Fused cores are unsupported; partial visible cores
  have larger uncertainty.
- `bar`: inherited THU grouped/stacked calibrated bars. Global rectangle
  exclusions only. Visible tops/bases and category centres must be established.
- `heatmap`: inherited THU grid and separate colour-bar calibration. Endpoint
  colours are interval bounds, never exact hidden magnitudes.

Do not force unsupported 3D charts, arbitrary colour mixtures or unreadable axes
through a convenient route. Explain the unresolved geometry and retain evidence.

## Deliver and validate

Open the original, mask overlay and extraction overlay. Check accepted marks,
false positives, edge points, empty outputs and gaps. Inspect `report.json` for
unauthorized candidates. The CSV marks values as `digitized_approximation` and
keeps pixel coordinates, source hash and estimated pixel/calibration uncertainty.
Uncertainty is not a measured accuracy score.

Recreations must use the extraction CSV only. If author data are available, keep
them in a separate validation step and report matching coverage, missing points,
tolerance and metric. Never replace extracted values with the reference. Read
[benchmark protocol](references/benchmark.md) before quoting a percentage.
The repository's >90% result applies to its declared assisted regression cases,
not arbitrary papers or autonomous legend detection.

When used inside a research subproject, retain its provenance, station rules,
unit conventions and required long-table schema in the downstream export.
