"""Validate the retained Nature Medicine heatmap against author data.

The workbook has two-decimal correlations. The rounding-aware comparison uses
distance to [reference - .005, reference + .005], followed by the same 1% of
colour-axis range tolerance (.006). The raw, unadjusted score is also reported.
"""
from pathlib import Path
import argparse
import csv
import json
import sys
import numpy as np
from openpyxl import load_workbook
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from digitizer_core.engine import run,save_json
from digitizer_core.masks import sha256


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'runs/paper/p01');args=ap.parse_args()
    records,report=run(ROOT/'benchmarks/cases/p01/config.json',args.out)
    # Read the reference only AFTER the immutable extraction has been written.
    source=ROOT/'benchmarks/truth/p01-source.xlsx'
    wb=load_workbook(source,read_only=True,data_only=True);sheet=wb['SuppData 8'];it=sheet.values;headers=next(it)
    table={row[0]:dict(zip(headers,row)) for row in it};wb.close()
    mapping={r['biomarker_display']:r['source_stem'] for r in csv.DictReader((ROOT/'benchmarks/truth/p01.csv').open())}
    numeric=[];censored=[];pairs=[]
    for row in records:
        truth=float(table[row['series']][mapping[row['category']]+'_Corr'])
        error=abs(row['y']-truth) if row['y'] is not None else None
        status=row['value_status']
        if status=='numeric':
            numeric.append(error)
        else:
            censored.append((truth>=row['interval_low']-.005) if row['interval_low'] is not None else (truth<=row['interval_high']+.005))
        pairs.append(dict(embedding=row['series'],biomarker=row['category'],digitized=row['y'],reference_rounded=truth,
                          absolute_error=error,status=status))
    errors=np.array([np.inf if e is None else e for e in numeric]);tolerance=.006
    result=dict(id='p01',title='Nature Medicine · proteomics heatmap',reference_kind='author_source_workbook_rounded_2dp',
        metric='Within 1% palette range + reference rounding interval',accuracy_pct=float(np.mean(np.maximum(0,errors-.005)<=tolerance)*100),
        raw_within_1pct_range_pct=float(np.mean(errors<=tolerance)*100),reference_rounding_half_width=.005,
        palette_tolerance=.006,numeric_cells=len(numeric),expected=len(numeric),extracted=int(np.isfinite(errors).sum()),
        endpoint_censored_cells=len(censored),endpoint_interval_consistent=sum(censored),mae=float(np.mean(errors)),
        input_sha256=report['image_sha256'],config_sha256=report['config_sha256'],csv_sha256=report['csv_sha256'],truth_sha256=sha256(source),
        article_url='https://www.nature.com/articles/s41591-026-04303-y',
        license='CC BY 4.0; cropped Figure 4c, original authors credited in benchmarks/SOURCES.md',
        scope='Supplementary source validation. Separate from the 11-case line/scatter benchmark. Endpoint bounds excluded from numeric accuracy; all reported separately.')
    save_json(args.out/'metrics.json',result)
    with (args.out/'source-comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
