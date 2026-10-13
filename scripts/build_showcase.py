"""Publish evidence artifacts; editorial READMEs and Excalidraw assets stay editable."""
from pathlib import Path
import json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from digitizer_core.engine import save_json
TITLES={'s02':'同色交叉线 × 内嵌图例','s03':'阶梯线 × 不可见遮挡','s06':'密集重叠散点','s08':'低清 JPEG × 压缩伪影','r01':'海洋热输送 × 图例与注释','r02':'多系列曲线 × 置信带','r03':'同色散点 × 拟合曲线','p01':'Nature Medicine · 672 格热图'}
ORDER=['f04','f05','f06','f07','f08','f01','f02','f03','r01','r03','s02','s08','s06','p01','r02','s03']

def public_report(value):
 if isinstance(value,dict):return {k:public_report(v) for k,v in value.items()}
 if isinstance(value,list):return [public_report(v) for v in value]
 if isinstance(value,str) and value.startswith(str(ROOT)):return str(Path(value).relative_to(ROOT))
 return value

def main():
 summary=json.loads((ROOT/'runs/benchmark/summary.json').read_text());flux=json.loads((ROOT/'runs/flux/summary.json').read_text())
 if summary['case_count']!=11 or len(flux['cases'])!=8:raise ValueError('Run all regression and FLUX cases first.')
 manifest={c['id']:c for c in json.loads((ROOT/'benchmarks/manifest.json').read_text())+json.loads((ROOT/'benchmarks/flux/manifest.json').read_text())};cases=[]
 for case in flux['cases']+summary['cases']+[json.loads((ROOT/'runs/paper/p01/metrics.json').read_text())]:
  cid=case['id']
  if cid not in ORDER:continue
  source=ROOT/('runs/flux/'+cid if cid.startswith('f') else 'runs/paper/p01' if cid=='p01' else 'runs/benchmark/'+cid);dest=ROOT/'docs/cases'/cid;dest.mkdir(parents=True,exist_ok=True)
  for name in ['source.png','original.png','legend-overlay.png','exclusion-mask.png','overlay.png','recreated.png','comparison.png','data.csv','metrics.json']:
   shutil.copy2(source/name,dest/name)
  save_json(dest/'report.json',public_report(json.loads((source/'report.json').read_text())))
  if cid=='p01':shutil.copy2(source/'source-comparison.csv',dest/'source-comparison.csv')
  extra={}
  if cid.startswith('f'):
   prov=json.loads((ROOT/'benchmarks/flux'/cid/'provenance.json').read_text());save_json(dest/'provenance.json',prov)
   extra=dict(group='flux',doi=prov['doi'],license=prov['license'],title_en=manifest[cid]['title_en'],title_ja=manifest[cid]['title_ja'])
  cases.append(dict(id=cid,title=manifest[cid]['title'] if cid.startswith('f') else TITLES[cid],kind='heatmap' if cid=='p01' else manifest[cid]['kind'],source_label='FLUX 论文' if cid.startswith('f') else '论文' if cid=='p01' else '合成回归' if cid.startswith('s') else '书稿',metrics=case,**extra))
 # Only explicitly retired showcase folders are removed. Fixtures remain in benchmarks.
 for cid in ['s01','s04','s05','s07']:
  if (ROOT/'docs/cases'/cid).exists():shutil.rmtree(ROOT/'docs/cases'/cid)
 cases.sort(key=lambda c:ORDER.index(c['id']))
 save_json(ROOT/'docs/cases.json',dict(macro_accuracy_pct=summary['macro_accuracy_pct'],flux_summary=flux,cases=cases))
 save_json(ROOT/'benchmarks/results.json',summary);save_json(ROOT/'benchmarks/flux/results.json',flux);(ROOT/'docs/.nojekyll').touch()
 print(f'Published {len(cases)} cards, including 8 FLUX panels. READMEs and design sources preserved.')
if __name__=='__main__':main()
