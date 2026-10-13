# Prompt and review checklist

The runnable prompt source is `digitizer_core/ai_assist.py` in the Digitizer
repository. Each prepared bundle stores its full `prompt.txt` and SHA-256.

## Selection wording

| Representation | Target wording | Must exclude |
|---|---|---|
| Line + confidence band | “thin solid blue measured NEE” | pale blue band, dashed estimates, legend swatches |
| Markers + fit | “blue circular observation markers with white outlines” | smooth same-colour fit, error bars, legend samples |
| Same-colour curves | colour **and** solid/dashed style and semantic label | other styles; inseparable crossings remain uncertain |
| Step curve | exact horizontal and vertical visible stroke | smoothing, invented midpoint samples, hidden plateaus |

Select one panel and one series per call. Describe existing objects rather than
asking the model to “redraw a clean chart”. Do not provide expected numeric values
or author reference data. Preserve original target-colour metadata before
clearing the legend. Bounding boxes in prompts supplement exact masks; they do
not replace them.

## Review JSON

```json
{
  "reviewed": true,
  "review_note": "Describe actual inspected ticks, frame corners and observed distortions.",
  "source_sha256": "hash of exact original",
  "generated_sha256": "hash of saved generated.png",
  "anchor_pairs": [[120,80,152,112],[950,80,982,112],[120,660,152,692],[950,660,982,692]]
}
```

Numbers are illustrative. Measure the actual image. Landmarks must span at least
70% of plot width and height. The residual threshold is 1.5 original pixels.
Registration cannot correct a model that independently moves a curve relative
to its axes. Original-pixel support prevents direct fabricated coordinates but
can still select the wrong nearby original series.

## Failure handling

- Missing/blank output: preserve the failure; do not reuse an old CSV.
- HTTP 503 / timeout: inspect sanitized request metadata. Create a new bundle only
  for a deliberate new call. Never silently switch providers/models.
- Changed geometry: measure anchors; reject inconsistent/nonlinear deformation.
- Extra red legend/curve: correct original masks/target wording, not the truth data.
- Heatmap colour drift: extract original calibrated cells; AI recolouring is inappropriate.
- No independent reference: show overlays and coverage, write “unscored”.

Provider references: [APIYI platform](https://imagen.apiyi.com/),
[Google image-generation API](https://ai.google.dev/gemini-api/docs/image-generation).
