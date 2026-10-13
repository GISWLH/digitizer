"""Re-extract frozen inputs, then score against separate reference files.

The extractor receives only config.json and input.png. The reference files are
read here AFTER extraction. This is a transparent development benchmark, not
an unseen-publication generalization estimate.
"""
from pathlib import Path
import argparse
import csv
import json
import sys
import numpy as np
from scipy.optimize import linear_sum_assignment

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from digitizer_core.engine import run, save_json
from digitizer_core.masks import sha256


def xy_normalized(case, points):
    a=np.asarray(points,dtype=float).reshape(-1,2).copy()
    if case.get("xscale")=="log10":
        a[:,0]=(np.log10(a[:,0])-np.log10(case['xlim'][0]))/np.ptp(np.log10(case['xlim']))
    else:a[:,0]=(a[:,0]-case['xlim'][0])/np.ptp(case['xlim'])
    a[:,1]=(a[:,1]-case['ylim'][0])/np.ptp(case['ylim'])
    return a


def score(case, records, truth):
    valid=[r for r in records if r['y'] is not None and r['status'] not in {'candidate_not_authorized','low_confidence'}]
    if case['kind']=='scatter':
        a=xy_normalized(case,truth);b=xy_normalized(case,[[r['x'],r['y']] for r in valid])
        distances=np.linalg.norm(a[:,None,:]-b[None,:,:],axis=2)
        i,j=linear_sum_assignment(np.where(distances<=.01,distances,1000+distances))
        matched=int((distances[i,j]<=.01).sum());precision=matched/max(len(valid),1);recall=matched/max(len(truth),1)
        return dict(metric='F1 @ 1% axis-distance',accuracy_pct=200*matched/max(len(truth)+len(valid),1),
                    precision_pct=100*precision,recall_pct=100*recall,matched=matched,expected=len(truth),extracted=len(valid))
    grid=np.geomspace(*case['xlim'],401) if case.get('xscale')=='log10' else np.linspace(*case['xlim'],401)
    q=np.log10(grid) if case.get('xscale')=='log10' else grid
    tx=np.log10(truth[:,0]) if case.get('xscale')=='log10' else truth[:,0]
    target=np.interp(q,tx,truth[:,1],left=np.nan,right=np.nan)
    if case.get('truth_representation')=='step_post':
        idx=np.searchsorted(truth[:,0],grid,side='right')-1
        target=truth[:,1][np.clip(idx,0,len(truth)-1)]
        target[(grid<truth[:,0].min())|(grid>truth[:,0].max())]=np.nan
        # Step discontinuities have no unique y. This same fixed rule applies to every method.
        near=np.min(abs(grid[:,None]-truth[:,0]),axis=1)/np.ptp(case['xlim'])*(case['bounds'][2]-case['bounds'][0])<2
        target[near]=np.nan
    hidden=np.zeros(len(grid),bool)
    if case.get('occlusion'):
        lo,hi=case['occlusion'];hidden=(grid>lo+.5)&(grid<hi-.5)
    visible=np.isfinite(target)&~hidden
    # Sample the nearest original pixel only. No evaluation interpolation bridges gaps.
    l,t,r,b=case['bounds'];lo,hi=(np.log10(case['xlim']) if case.get('xscale')=='log10' else case['xlim'])
    px=np.rint(l+(q-lo)/(hi-lo)*(r-l)).astype(int)
    indexed={int(row['x_pixel']):row for row in valid}
    pred=np.array([indexed.get(int(x),{}).get('y',np.nan) for x in px],dtype=float)
    error=abs(pred-target)/np.ptp(case['ylim']);matched=visible&np.isfinite(pred)
    hits=visible&(error<=.01)
    return dict(metric='Within 1% of y-axis range (missing = miss)',accuracy_pct=100*int(hits.sum())/max(int(visible.sum()),1),
        coverage_pct=100*int(matched.sum())/max(int(visible.sum()),1),
        nmae_pct=100*float(np.mean(error[matched])) if matched.any() else None,
        expected=int(visible.sum()),matched=int(hits.sum()),extracted=int(matched.sum()),
        hidden_values=int(np.isfinite(pred[hidden]).sum()))


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'runs/benchmark');p.add_argument('--cases',nargs='*');p.add_argument('--ablation',action='store_true');p.add_argument('--require-90',action='store_true');args=p.parse_args()
    manifest=json.loads((ROOT/'benchmarks/manifest.json').read_text());results=[]
    for case in manifest:
        if args.cases and case['id'] not in args.cases:continue
        if case['kind'] not in {'line','scatter'}:continue
        config=ROOT/'benchmarks/cases'/case['id']/'config.json'
        rows,report=run(config,args.out/case['id'])
        truth_path=ROOT/'benchmarks/truth'/f"{case['id']}.csv"
        truth=np.genfromtxt(truth_path,delimiter=',',names=True,encoding='utf-8-sig')
        truth=np.column_stack([truth['x'],truth['y']])
        result=dict(id=case['id'],title=case['title'],reference_kind=case['reference_kind'],**score(case,rows,truth))
        result.update(input_sha256=report['image_sha256'],config_sha256=report['config_sha256'],csv_sha256=report['csv_sha256'],truth_sha256=sha256(truth_path))
        if args.ablation:
            raw,_=run(config,args.out/case['id']/'unmasked',ignore_exclusions=True)
            result['unmasked']=score(case,raw,truth)
        results.append(result);print(f"{case['id']:5s} {result['accuracy_pct']:7.2f}% {result['metric']} ({result['extracted']}/{result['expected']})",flush=True)
        save_json(args.out/case['id']/'metrics.json',result)
    summary=dict(protocol='development-regression-v1',threshold_pct=90,case_count=len(results),macro_accuracy_pct=float(np.mean([r['accuracy_pct'] for r in results])),passed=sum(r['accuracy_pct']>=90 for r in results),cases=results,
        scope='Frozen repository cases; human-reviewed geometry. Not held-out. No reference data are supplied to extraction.')
    save_json(args.out/'summary.json',summary)
    print(f"Macro: {summary['macro_accuracy_pct']:.2f}%; pass: {summary['passed']}/{len(results)}")
    if args.require_90 and (summary['passed']!=len(results) or any(c.get('hidden_values',0)>0 for c in results)):raise SystemExit(1)


if __name__=='__main__':main()
