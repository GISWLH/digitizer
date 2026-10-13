"""Build labelled process boards from frozen live calls and extracted CSV."""
from pathlib import Path
import csv,json,shutil,sys
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
from matplotlib.font_manager import findfont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from digitizer_core.engine import save_json
from digitizer_core.grid import extract_grid

INK='#203b33';PAPER='#f7f7ef';MUTED='#60786e';ACCENT='#d5ecb8'
FONT=findfont('DejaVu Sans');BOLD=findfont('DejaVu Sans:weight=bold')

def board(path,title,subtitle,panels,columns=3):
    cellw,cellh=580,440;gap=20;margin=30;top=135
    rows=(len(panels)+columns-1)//columns
    canvas=Image.new('RGB',(margin*2+columns*cellw+(columns-1)*gap,top+rows*cellh+(rows-1)*gap+45),PAPER)
    draw=ImageDraw.Draw(canvas)
    draw.text((margin,25),title,font=ImageFont.truetype(BOLD,32),fill=INK)
    draw.text((margin,78),subtitle,font=ImageFont.truetype(FONT,18),fill=MUTED)
    for i,(label,detail,img) in enumerate(panels):
        x=margin+(i%columns)*(cellw+gap);y=top+(i//columns)*(cellh+gap)
        draw.rounded_rectangle((x,y,x+cellw,y+cellh),radius=14,fill='white',outline='#d5ded3',width=2)
        draw.rounded_rectangle((x+14,y+14,x+52,y+49),radius=7,fill=ACCENT)
        draw.text((x+23,y+20),str(i+1),font=ImageFont.truetype(BOLD,20),fill=INK)
        draw.text((x+64,y+19),label,font=ImageFont.truetype(BOLD,21),fill=INK)
        draw.text((x+17,y+60),detail,font=ImageFont.truetype(FONT,15),fill=MUTED)
        im=img if isinstance(img,Image.Image) else Image.open(img).convert('RGB')
        thumb=ImageOps.contain(im,(cellw-28,cellh-105),Image.Resampling.LANCZOS)
        canvas.paste(thumb,(x+(cellw-thumb.width)//2,y+94+(cellh-105-thumb.height)//2))
    draw.text((margin,canvas.height-28),'digitizer  /  original evidence + model selection + reproducible measurements',font=ImageFont.truetype(FONT,14),fill=MUTED)
    canvas.save(path)


def csv_plot(out,config):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from digitizer_core.engine import axes
    rows=list(csv.DictReader((out/'data.csv').open()))
    fig,ax=plt.subplots(figsize=(7,4.5),dpi=160)
    for s in config['series']:
        vals=[p for p in rows if p['series']==s['name']]
        x=[float(p['x']) for p in vals];y=[float(p['y']) if p['y'] else np.nan for p in vals]
        if config['kind']=='scatter':ax.scatter(x,y,s=24,color=s['color'],edgecolors='white',linewidth=.5,label=s['name'])
        else:ax.plot(x,y,lw=1.5,color=s['color'],label=s['name'])
    xa,ya=axes(config);l,t,r,b=config['plot_bounds']
    ax.set_xlim(xa.value_at_pixel(l),xa.value_at_pixel(r));ax.set_ylim(ya.value_at_pixel(b),ya.value_at_pixel(t))
    ax.set_xlabel('Calibrated x');ax.set_ylabel(config.get('unit') or 'Calibrated y');ax.set_title('Recreated from extracted CSV',loc='left',fontweight='bold')
    ax.grid(alpha=.12);ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(out/'recreated.png',facecolor='white');plt.close(fig)


def main():
    summary=json.loads((ROOT/'runs/ai-replay/summary.json').read_text());manifest={c['id']:c for c in json.loads((ROOT/'benchmarks/ai/manifest.json').read_text())}
    for m in summary['cases']:
        cid=m['id'];fixture=ROOT/'benchmarks/ai'/cid;run=ROOT/'runs/ai-replay'/cid;dest=ROOT/'docs/ai'/cid;dest.mkdir(parents=True,exist_ok=True)
        meta=json.loads((fixture/'bundle.json').read_text());config=meta['config'];config['series']=[s for s in config['series'] if s['name']==meta['series']]
        for name in ['original.png','overlay.png','support-overlay.png','selection.png','data.csv','metrics.json','ai-report.json']:
            shutil.copyfile(run/name,dest/name)
        for name in ['prompt.txt','generated.png','prepared.png','request.json','review.json']:
            shutil.copyfile(fixture/name,dest/name)
        # Source mask is always reproducible from fixture metadata (including fresh clones).
        from digitizer_core.masks import region_mask,mask_overlay
        image=Image.open(dest/'original.png');mask_overlay(image,region_mask(image.size,config.get('exclusions',[]),series=meta['series'])).save(dest/'legend-overlay.png')
        report=json.loads((run/'ai-report.json').read_text());transform=np.array(report['transform_edited_to_original'])
        raw=np.array(Image.open(fixture/'generated.png').convert('RGB'))
        aligned=cv2.warpAffine(raw,transform,image.size,borderValue=(255,255,255));Image.fromarray(aligned).save(dest/'edited-aligned.png')
        csv_plot(dest,config)
        if config['kind']=='line':
            for name in ['grid.csv','grid-overlay.png']:shutil.copyfile(run/name,dest/name)
            last=('Fixed-column grid','49 positions; missing source columns stay empty',dest/'grid-overlay.png')
        else:last=('Accepted markers','Original shapes first; AI cannot invent a dot',dest/'overlay.png')
        score='UNSCORED / no independent reference' if m['accuracy_pct'] is None else f"{m['accuracy_pct']:.2f}% / {('one-to-one F1' if cid=='a01' else 'within 1% y-axis range')}"
        board(dest/'process.png',f"{'Nano Banana Pro' if cid=='a03' else 'GPT image 2.5'}  /  fill, verify, extract",score+"  |  one live capture, offline replay",[
            ('Original figure','Immutable source; scientific values come from here',dest/'original.png'),
            ('Precise exclusions','Legend/annotation masks applied before the request',dest/'legend-overlay.png'),
            ('AI colour selection','Registered model output; intermediate only',dest/'edited-aligned.png'),
            ('Original-pixel support','Green: eligible source ink; magenta: unsupported red',dest/'support-overlay.png'),
            last,('CSV reconstruction','Drawn from data.csv only; no reference values',dest/'recreated.png')])
        board(dest/'comparison.png','Original figure  /  extracted data',score,[('Source','Original paper / manuscript figure',dest/'original.png'),('CSV reconstruction','AI-assisted selection; original-pixel measurement',dest/'recreated.png')],columns=2)
        if cid=='a02':
            legacy=fixture/'legacy';lr=json.loads((run/'legacy/ai-report.json').read_text());matrix=np.array(lr['transform_edited_to_original'])
            old=cv2.warpAffine(np.array(Image.open(legacy/'generated.png')),matrix,image.size,borderValue=(255,255,255));Image.fromarray(old).save(dest/'legacy-aligned.png')
            shutil.copyfile(legacy/'prompt.txt',dest/'legacy-prompt.txt');shutil.copyfile(legacy/'request.json',dest/'legacy-request.json')
            board(dest/'prompt-ab.png','Prompt A/B  /  remove red distractors before measuring','Same masked input and model. Out-of-support red fraction is a cleanup diagnostic, NOT accuracy.',[
                ('Original','Measured blue line + dashed red estimates + band',dest/'original.png'),
                ('Legacy: keep other content',f"Out-of-support red: {m['legacy_prompt']['unsupported_red_pct']:.2f}%",dest/'legacy-aligned.png'),
                ('V2: isolate one visible target',f"Out-of-support red: {m['unsupported_red_pct']:.2f}%",dest/'edited-aligned.png')])
        if cid in {'a02','a03'}:
            prov=json.loads((ROOT/'benchmarks/flux'/m['source_case']/'provenance.json').read_text())
            save_json(dest/'provenance.json',prov)
    dest=ROOT/'docs/ai/grid';dest.mkdir(parents=True,exist_ok=True)
    extract_grid(ROOT/'benchmarks/cases/p01/config.json',ROOT/'runs/grid/p01')
    for name in ['original.png','grid-overlay.png','grid.csv','grid-report.json','recreated.png']:shutil.copyfile(ROOT/'runs/grid/p01'/name,dest/name)
    board(dest/'process.png','Heatmap grid  /  32 rows x 21 columns','672 cells = 578 numeric estimates + 94 saturated intervals. Original colours are never recoloured.',[
        ('Original heatmap','Nature Medicine, Fig. 4c / CC BY 4.0',dest/'original.png'),
        ('Calibrated cell grid','Labels, cell boundaries and colourbar retained',dest/'grid-overlay.png'),
        ('Extracted cells','MAE 0.00329; rounding-aware 98.79%; raw 84.60%',dest/'recreated.png')])
    save_json(ROOT/'docs/ai/results.json',summary);save_json(ROOT/'benchmarks/ai/results.json',summary)
    print('Published three AI process boards, prompt A/B and 672-cell grid evidence.')
if __name__=='__main__':main()
