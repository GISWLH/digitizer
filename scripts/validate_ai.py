"""Replay frozen model outputs offline; evaluate references only after extraction.

Live generation is opt-in via ai-edit. CI never contacts an image provider.
"""
import argparse,csv,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from digitizer_core.ai_assist import extract
from digitizer_core.engine import run,save_json
from digitizer_core.masks import sha256
from benchmark import score
from validate_flux import score_vectors


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--require-90',action='store_true');args=parser.parse_args()
    results=[]
    for case in json.loads((ROOT/'benchmarks/ai/manifest.json').read_text()):
        folder=ROOT/'benchmarks/ai'/case['id'];out=ROOT/'runs/ai-replay'/case['id']
        rows,report=extract(folder,folder/'review.json',out)
        meta=json.loads((folder/'bundle.json').read_text());config=meta['config']
        config['series']=[s for s in config['series'] if s['name']==meta['series']]
        config['image']=str((folder/meta['source_file']).resolve())
        save_json(out/'baseline-config.json',config)
        baseline,_=run(out/'baseline-config.json',out/'baseline')
        result=dict(id=case['id'],source_case=case['source_case'],model=report['request']['model'],
            provider=report['request']['provider'],metric=case['metric'],accuracy_pct=None,baseline_accuracy_pct=None,
            numeric_rows=report['numeric_rows'],baseline_numeric_rows=sum(p['y'] is not None for p in baseline),
            generated_sha256=report['generated_sha256'],csv_sha256=report['csv_sha256'],
            red_pixels=report['prior_red_pixels'],unsupported_red_pixels=report['unsupported_red_pixels'],
            unsupported_red_pct=100*report['unsupported_red_pixels']/max(report['prior_red_pixels'],1))
        # Neither author/fixture values nor vector references are available to the extractor.
        if case['reference_kind']=='fixture':
            original=next(c for c in json.loads((ROOT/'benchmarks/manifest.json').read_text()) if c['id']==case['source_case'])
            path=ROOT/'benchmarks/truth'/f"{case['source_case']}.csv"
            truth=np.genfromtxt(path,delimiter=',',names=True);truth=np.column_stack([truth['x'],truth['y']])
            result.update(score(original,rows,truth));result['baseline_accuracy_pct']=score(original,baseline,truth)['accuracy_pct']
            result['reference_sha256']=sha256(path)
        elif case['reference_kind']=='pdf_vectors':
            path=ROOT/'benchmarks/flux'/case['source_case']/'reference.csv'
            with path.open() as f:reference=list(csv.DictReader(f))
            result.update(score_vectors(config,rows,reference));result['baseline_accuracy_pct']=score_vectors(config,baseline,reference)['accuracy_pct']
            result['reference_sha256']=sha256(path)
        else:
            result['accuracy_note']='No independent author numerical data; colour support is not an accuracy measure.'
        if (folder/'legacy').exists():
            _,legacy=extract(folder/'legacy',folder/'legacy/review.json',out/'legacy')
            result['legacy_prompt']=dict(red_pixels=legacy['prior_red_pixels'],unsupported_red_pixels=legacy['unsupported_red_pixels'],
                unsupported_red_pct=100*legacy['unsupported_red_pixels']/max(legacy['prior_red_pixels'],1),numeric_rows=legacy['numeric_rows'])
        save_json(out/'metrics.json',result);results.append(result)
        print(case['id'],f"{result['accuracy_pct']:.2f}%" if result['accuracy_pct'] is not None else 'UNSCORED',flush=True)
    scored=[r for r in results if r['accuracy_pct'] is not None]
    summary=dict(protocol='frozen-ai-original-support-v1',cases=results,scored_cases=len(scored),unscored_cases=len(results)-len(scored),
        scope='Development examples, one captured generation per prompt. No provider ranking or generalization claim; original THU baseline separately reported.')
    save_json(ROOT/'runs/ai-replay/summary.json',summary)
    if args.require_90 and (not scored or any(r['accuracy_pct']<90 for r in scored)):raise SystemExit(1)
if __name__=='__main__':main()
