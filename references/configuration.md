# Configuration and evidence

`digitizer inspect` writes a draft config and a mask overlay. Paths in a config
are relative to that config, not the shell's working directory. Original raster
pixels start at the top left. Bounds are inclusive. Image identity and visual
review are mandatory even when there is no legend.

```json
{
  "schema_version": 1,
  "image": "input.png",
  "image_sha256": "actual SHA-256 emitted by inspect",
  "image_size": [1024, 768],
  "reviewed": true,
  "review_note": "Verified x ticks 0/120, y ticks 0/100 and blue target; excluded two legend rows.",
  "kind": "line",
  "plot_bounds": [123, 77, 963, 660],
  "axes": {
    "x": {"anchors": [[123, 0], [963, 120]], "scale": "linear"},
    "y": {"anchors": [[660, 0], [77, 100]], "scale": "linear"}
  },
  "series": [{"name": "target", "color": "#2468b4"}],
  "exclusions": [
    {"type": "rectangle", "bounds": [760, 88, 955, 120], "verified": true, "reason": "Legend row"},
    {"type": "polygon", "points": [[760,130],[890,130],[910,159],[760,159]], "series": ["target"], "verified": true, "reason": "Irregular annotation"}
  ]
}
```

Use `log10` for a logarithmic axis whose anchors contain the actual positive
values. `displayed_log10` treats printed log values as coordinates. Never feed
actual values and printed logarithms interchangeably. More than two anchors
use THU's robust fit; inspect residuals for mistakes.

Line series accept `parameters`: `sigma`, `tolerance`, `score_threshold`,
`edge_margin`, `smoothness`, `gap_penalty`, `max_step`, `suppress_horizontal`,
`min_chroma_fraction`. Defaults retain THU tracing except that long horizontal
data are preserved and colourful targets reject near-neutral pixels. The
reviewed JPEG fixture uses sigma 85, tolerance 120, threshold .20. These are
fixture settings, not universal recommendations.

Scatter `marker` selects `filled` (THU distance peaks), `hollow` (closed ring
holes) or `isolated` (compact cores with outlines). Filled accepts THU radius,
colour and residual-audit parameters. Hollow accepts `color_tolerance`,
`min_radius`, `max_radius`; isolated accepts `color_tolerance`, `min_diameter`,
`max_diameter`. Declare the grammar from visible evidence, never an expected count.

For bars, a `bar` object supplies THU's `plot_bounds`, `value_axis`
`[pixel0,value0,pixel1,value1]`, `orientation`, `layout`, `series_colors` and
`categories` `[[label,centre_pixel], ...]`. For heatmaps, `heatmap` supplies
`grid_bounds`, ordered `row_labels`, `column_labels`, `colorbar_bounds`,
`colorbar_top_value` and `colorbar_bottom_value`. See the retained engine's
function signatures for optional parameters. Bars currently accept only global
rectangle exclusions; heatmaps conservatively omit any masked cell.

Every run emits:

| File | Meaning |
|---|---|
| `original.png` | Unmodified decoded source image |
| `data.csv` | Values, missing states, pixel coordinates, uncertainty, provenance |
| `exclusion-mask.png` | Exact binary detector mask |
| `legend-overlay.png` | Pink mask visualization |
| `overlay.png` | Extraction positions on the source |
| `recreated.png` | Replot from extracted records, never reference values |
| `comparison.png` | Original and recreation side by side |
| `report.json` | Input/config/CSV hashes, parameters, traces and confidence gates |

For lines, each plot column is retained even when `y` is empty. Do not drop gaps
before drawing a connected line. Heatmap `clipped_high`/`clipped_low` values are
bounds with interval columns. A filled-scatter `candidate_not_authorized` row
is diagnostic evidence, not an accepted observation. The scientific station
long table is a downstream mapping, not a fabricated property of arbitrary charts.
