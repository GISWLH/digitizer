"""Deterministic grids measured from original pixels, never drawn by a model."""
import csv
from pathlib import Path
from PIL import Image,ImageDraw
from .ai_assist import write_grid
from .engine import run,save_json,axes
from .masks import read_config,sha256


def extract_grid(config_path,out,columns=49):
    config,_=read_config(config_path);out=Path(out)
    if config['kind'] not in {'line','heatmap'}:
        raise ValueError('Grid extraction supports fixed-x line sampling and heatmap cells.')
    records,report=run(config_path,out)
    if config['kind']=='line':
        # One independent grid for each target series, with identical source columns.
        combined=[]
        for series in config['series']:
            rows=write_grid([p for p in records if p['series']==series['name']],config,out,columns)
            combined.extend(dict(series=series['name'],**r) for r in rows)
        with (out/'grid.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(combined[0]));writer.writeheader();writer.writerows(combined)
        # Overlay every series, not merely the last grid written in the loop.
        image=Image.open(out/'grid-overlay.png').convert('RGB');draw=ImageDraw.Draw(image);_,ya=axes(config)
        for row in combined:
            if row['y'] is not None:
                x=row['sample_x_pixel'];y=ya.pixel_at_value(row['y'])
                draw.ellipse((x-3,y-3,x+3,y+3),fill='#e43a57')
        image.save(out/'grid-overlay.png')
        count=len(combined)
    else:
        rows=[];image=Image.open(out/'original.png').convert('RGB');draw=ImageDraw.Draw(image)
        cells=report['details']['heatmap']['cells']
        for rec,cell in zip(records,cells):
            bounds=cell['cell_bounds_pixel'];draw.rectangle(bounds,outline='#193d39',width=1)
            rows.append(dict(row=cell['row_index'],column=cell['column_index'],row_label=cell['row_label'],column_label=cell['column_label'],
                value=rec['y'],status=rec['status'],value_status=rec['value_status'],interval_low=rec['interval_low'],interval_high=rec['interval_high'],
                data_type='digitized_approximation',source_sha256=config['image_sha256'],
                source_file=rec['source_file'],source_doi=config.get('source_doi',''),figure_or_table=config.get('figure',''),unit=config.get('unit',''),
                extraction_error=rec['extraction_error'],x_pixel=rec['x_pixel'],y_pixel=rec['y_pixel']))
        with (out/'grid.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        image.save(out/'grid-overlay.png');count=len(rows)
    grid_report=dict(grid_rows=count,kind=config['kind'],source_sha256=config['image_sha256'],grid_sha256=sha256(out/'grid.csv'),
        note='Line samples use nearest source column without interpolation. Heatmap values use original calibrated colours; saturated endpoints are intervals.')
    save_json(out/'grid-report.json',grid_report)
    return grid_report
