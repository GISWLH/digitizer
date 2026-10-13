"""Extract real FLUX figures first; only then read independent PDF paths.

The score measures plotted geometry, not raw-observation accuracy. Four raster
panels have no reference and remain explicitly unscored. No new station admission.
"""
from pathlib import Path
import argparse,csv,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from digitizer_core.engine import run,save_json,axes
from digitizer_core.masks import sha256

def score_vectors(config,records,reference):
 xa,ya=axes(config);yrange=abs(ya.value_at_pixel(config['plot_bounds'][1])-ya.value_at_pixel(config['plot_bounds'][3]));results=[]
 for series in config['series']:
  name=series['name'];truth=[r for r in reference if r['series']==name];tx=np.array([float(r['x_pixel']) for r in truth]);ty=np.array([float(r['y_pixel']) for r in truth]);order=np.argsort(tx);tx,ty=tx[order],ty[order]
  grid=np.linspace(max(tx.min(),config['plot_bounds'][0]),min(tx.max(),config['plot_bounds'][2]),401)
  # Query reference at the same integer columns actually extracted.
  pixels=np.rint(grid).astype(int);target=np.interp(pixels,tx,ty)
  idx={int(r['x_pixel']):r for r in records if r['series']==name and r['y'] is not None and r['status'] not in {'low_confidence','candidate_not_authorized'}}
  pred=np.array([idx.get(int(x),{}).get('y_pixel',np.nan) for x in pixels]);error=abs(pred-target)*abs(ya.value_at_pixel(1)-ya.value_at_pixel(0))/yrange;present=np.isfinite(pred)
  hits=int(np.sum(error<=.01));results.append(dict(series=name,expected=401,matched=hits,extracted=int(present.sum()),accuracy_pct=100*hits/401,coverage_pct=100*float(present.mean()),nmae_pct=100*float(np.mean(error[present])) if present.any() else None))
 return dict(accuracy_pct=float(np.mean([r['accuracy_pct'] for r in results])),coverage_pct=float(np.mean([r['coverage_pct'] for r in results])),expected=sum(r['expected'] for r in results),matched=sum(r['matched'] for r in results),series=results)

def render_evidence(folder, out, config, case):
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from PIL import Image, ImageDraw
 with (out/'data.csv').open() as f: rows=list(csv.DictReader(f))
 original=Image.open(out/'original.png').convert('RGB')
 width=original.width;height=max(original.height,480)
 with plt.rc_context({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#344b43','text.color':'#142723','xtick.color':'#63716c','ytick.color':'#63716c','axes.edgecolor':'#b9c5be'}):
  fig,ax=plt.subplots(figsize=(width/150,height/150),dpi=150)
  for series in config['series']:
   data=[r for r in rows if r['series']==series['name']]
   ax.plot([float(r['x']) for r in data],[float(r['y']) if r['y'] else np.nan for r in data],color=series['color'],lw=1.2,label=series['name'].replace('_',' '))
  xa,ya=axes(config);l,t,r,b=config['plot_bounds'];ax.set_xlim(xa.value_at_pixel(l),xa.value_at_pixel(r));ax.set_ylim(ya.value_at_pixel(b),ya.value_at_pixel(t))
  ax.set_xlabel('Hour of day' if case['reference_kind']=='none' else 'Unwrapped Julian day (2004 to 2005)')
  ax.set_ylabel(config['unit']);ax.set_title(case['title_en'],loc='left',fontweight='bold',pad=15)
  ax.grid(alpha=.15);ax.legend(frameon=False,fontsize=9,loc='upper center',bbox_to_anchor=(.5,-.25),ncol=2)
  fig.tight_layout();fig.savefig(out/'recreated.png',facecolor='white');plt.close(fig)
 recreated=Image.open(out/'recreated.png').convert('RGB');pair=Image.new('RGB',(width*2,max(original.height,recreated.height)+45),'#f4f6f2')
 pair.paste(original,(0,45+(pair.height-45-original.height)//2));pair.paste(recreated,(width,45))
 draw=ImageDraw.Draw(pair);draw.text((20,15),'ORIGINAL PAPER FIGURE',fill='#142723');draw.text((width+20,15),'RECREATED FROM EXTRACTED CSV / gaps retained',fill='#142723');pair.save(out/'comparison.png')

def main():
 p=argparse.ArgumentParser();p.add_argument('--require-90',action='store_true');p.add_argument('--cases',nargs='*');a=p.parse_args();results=[]
 for case in json.loads((ROOT/'benchmarks/flux/manifest.json').read_text()):
  cid=case['id']
  if a.cases and cid not in a.cases:continue
  folder=ROOT/'benchmarks/flux'/cid;out=ROOT/'runs/flux'/cid
  records,report=run(folder/'config.json',out)
  # Deliberately opened only AFTER extraction.
  config=json.loads((folder/'config.json').read_text());prov=json.loads((folder/'provenance.json').read_text())
  result=dict(id=cid,metric='PDF vector geometry: within 1% y-axis range; missing = miss',reference_kind=case['reference_kind'],accuracy_pct=None,source_doi=prov['doi'],license=prov['license'],input_sha256=report['image_sha256'],csv_sha256=report['csv_sha256'],config_sha256=report['config_sha256'],numeric_rows=report['numeric_rows'],source_data_semantics=prov['source_data_semantics'])
  if case['reference_kind']=='independent_pdf_vector_geometry':
   assert sha256(folder/'reference.csv')==prov['reference_sha256'], 'Reference snapshot hash mismatch'
   with (folder/'reference.csv').open() as f:reference=list(csv.DictReader(f))
   result.update(score_vectors(config,records,reference));result['reference_sha256']=sha256(folder/'reference.csv')
   raw,_=run(folder/'config.json',out/'unmasked',ignore_exclusions=True);result['unmasked']=score_vectors(config,raw,reference)
  else:result['metric']='Unscored: no independent numerical reference';result['accuracy_note']=prov['accuracy_note']
  render_evidence(folder,out,config,case)
  save_json(out/'metrics.json',result);results.append(result);print(cid, f"{result['accuracy_pct']:.2f}%" if result['accuracy_pct'] is not None else 'UNSCORED',report['numeric_rows'],'numeric rows',flush=True)
 scored=[r for r in results if r['accuracy_pct'] is not None]
 summary=dict(protocol='flux-pdf-geometry-v1',cases=results,scored_cases=len(scored),unscored_cases=len(results)-len(scored),macro_accuracy_pct=float(np.mean([r['accuracy_pct'] for r in scored])) if scored else None,scope='Assisted development examples. PDF path geometry is independent of raster tracing, but is not raw author observation data. Reco/GEP include partitioned estimates. Salt-marsh panels are unscored.')
 save_json(ROOT/'runs/flux/summary.json',summary)
 if a.require_90 and any(r['accuracy_pct']<90 for r in scored):raise SystemExit(1)
if __name__=='__main__':main()
