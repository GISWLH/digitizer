# Attribution

Digitizer is a derivative of [Rimagination / THU Digitizer](https://github.com/Rimagination/thu-digitizer),
licensed MIT, copyright © 2026 Rimagination. Its continuity tracing, axis
calibration, compact-scatter distance peaks, bar extraction, heatmap extraction,
coverage contracts and OCR/swatch legend proposals form the core of this project.
The full upstream license is retained in `digitizer_core/_thu/LICENSE`.
`UPSTREAM.json` records the SHA-256 of each imported local source file. The local
snapshot already included reviewed, image-bound rectangular legend exclusions;
those pre-existing capabilities are not claimed as newly invented here.

GISWLH additions (2026): polygon and series-scoped bitmap exclusions across
primary and residual passes; neutral-colour rejection for wide JPEG thresholds;
preservation of long horizontal data; isolated outlined-marker and hollow-ring
routes; one CLI and installable skill; reproducible scoring and visual evidence.
Two imported modules have small marked extensions: `raster_digitizer_core.py`
and `candidate_digitize_scatter.py`. The other imported files are unchanged.

The adjacent `paper-figure-csv-ai` workflow informed the legend-first review
design. No API credentials, model-edited images or remote recolouring are needed.

Scientific figures and author workbooks retain their own licenses and attribution;
the software MIT license does not relicense them. See [case sources](benchmarks/SOURCES.md).

## FLUX figures and brand rendering

The f01–f04 Veenendaal et al. figure crops, vector references and derived evidence
are CC BY-NC-SA 2.5. The f05–f08 Mayen et al. figure crops and derived evidence
retain CC BY 4.0 attribution. These are exceptions to the software MIT license;
see [SOURCES.md](benchmarks/SOURCES.md) for authors, DOI, modifications and terms.

The optional brand studio uses Excalidraw 0.18.1 (MIT), Copyright (c) 2020
Excalidraw. Exported SVGs embed the Virgil handwriting font supplied by Excalidraw.
Excalidraw’s license is reproduced in [design/EXCALIDRAW-LICENSE](design/EXCALIDRAW-LICENSE).
Virgil is by Ellinor Rapp, SIL OFL 1.1; see [design/VIRGIL-LICENSE](design/VIRGIL-LICENSE).
Brand artwork is authored for this project; it does not imply Excalidraw endorsement.
