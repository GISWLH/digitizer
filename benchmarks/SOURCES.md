# Case provenance

| IDs | Source | Reference | Reuse |
|---|---|---|---|
| s01–s08 | Local Digitizer fixtures, fixed seed 20260924 | Frozen generating values | Project-generated fixtures |
| r01 | User-provided manuscript, meridional ocean heat transport | Retained manuscript source values | Included as part of the requested local-case publication; not a published-paper accuracy claim |
| r02–r03 | User-provided manuscript, monthly RMSE panel | Retained fitted curve and monthly points, respectively | Same supplied panel; two distinct extraction tasks |
| p01 | *A deep joint-learning proteomics model for diagnosis of six conditions associated with dementia*, Nature Medicine (2026), Fig. 4c | Official supplementary workbook, SuppData 8 | CC BY 4.0; original authors retain copyright |

Paper: https://www.nature.com/articles/s41591-026-04303-y

Original Fig. 4: https://www.nature.com/articles/s41591-026-04303-y/figures/4

Author workbook: https://static-content.springer.com/esm/art%3A10.1038%2Fs41591-026-04303-y/MediaObjects/41591_2026_4303_MOESM3_ESM.xlsx

License: https://creativecommons.org/licenses/by/4.0/

The p01 input is THU's retained panel crop, original figure pixels
`[1000, 650, 1951, 1510]`. Masks, extraction overlays, recreations and comparisons
are adaptations made for digitization demonstration. Data values are measured
from the raster before the author workbook is read. The reference CSV retains
THU's column mapping; the new validation re-reads the workbook's actual values.
The article license was checked on its official page on 2026-10-13.

All 11 original benchmark inputs are preserved byte-for-byte. Their hashes and
the source categories are in `manifest.json`. Personal machine paths were
removed from public metadata. No complete paper PDFs are distributed.

## FLUX papers added in v0.2.0

All eight cases originate in the existing local FLUX paper library. Full PDFs
are not redistributed. Each case under `benchmarks/flux/` contains a source
hash, crop coordinates, page, units, series semantics and license in
`provenance.json`. Preparation and independent scoring are reproducible with
`scripts/prepare_flux.py` and `scripts/validate_flux.py`.

### f01–f04 · Veenendaal et al. (2007)

[CO2 exchange and carbon balance in two grassland sites on eutrophic drained
peat soils](https://bg.copernicus.org/articles/4/1027/2007/), Biogeosciences 4,
1027–1040. DOI: 10.5194/bg-4-1027-2007. Fig. 10a–c (PDF page 9) and Fig. 11
(page 10). Copyright © Author(s) 2007.

**CC BY-NC-SA 2.5**, as stated on the publisher's article page (checked
2026-10-13): <https://creativecommons.org/licenses/by-nc-sa/2.5/>. The input crops,
vector references, extraction CSVs and adapted visual evidence for these cases
retain that license; the repository's software MIT license does not override it.
Changes: panel crops, raster rendering, legend/annotation masks, extracted curves
and new comparison/reconstruction figures. No endorsement is implied.

Reference values represent original PDF path geometry, not raw author observations.
NEE includes gap filling; respiration and GEP are partitioned estimates. The
blue series is Stein and the red series is Oukoop. No new station admission is
made. Three daily-series panels remain difficult and score below 90%.

### f05–f08 · Mayen et al. (2024)

[Atmospheric CO2 exchanges measured by eddy covariance over a temperate salt
marsh and influence of environmental controlling factors](https://bg.copernicus.org/articles/21/993/2024/),
Biogeosciences 21, 993–1016. DOI: 10.5194/bg-21-993-2024. Fig. 5a–d, PDF page 12.
Copyright © Author(s) 2024, **CC BY 4.0**:
<https://creativecommons.org/licenses/by/4.0/> (publisher page checked 2026-10-13).

Changes: the embedded figure is cropped into four panels; masks, extracted CSV,
overlays, reconstructions and comparisons are added. Extracted target: blue
measured NEE only. Other curves are estimates, and the band is standard deviation.
Author data are available upon request, not provided with this release. These
four cases have no independent numerical reference and are explicitly unscored.
No new station admission is made. No endorsement is implied.

## AI-assisted adaptations added in v0.3.0

- a01 adapts r03, the supplied monthly-RMSE manuscript panel.
- a02 adapts Mayen et al. (2024) Fig. 5a / f05, **CC BY 4.0**. It includes a
  legacy-prompt control on the identical masked input.
- a03 adapts Veenendaal et al. (2007) Fig. 11 / f04, **CC BY-NC-SA 2.5**.
  This license applies to its source, generated adaptation, extracted CSV and
  process/comparison images. Original author attribution is retained.
- The grid demonstration adapts p01 under its **CC BY 4.0** license.

New changes: masked/padded API inputs, AI red target selection, reviewed
registration, original-pixel gating, fixed-grid sampling, and process boards.
Generated images are labelled intermediate adaptations, not original paper
figures or recovered hidden observations. APIYI calls and full prompts are
retained in `benchmarks/ai/`; no complete PDFs, credentials or raw API bodies are
published. Both live model routes were served by APIYI on 2026-10-13. No author,
provider or upstream project endorsement is implied.
