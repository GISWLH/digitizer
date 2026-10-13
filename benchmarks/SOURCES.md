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
