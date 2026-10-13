"""Generative colour selection grounded in immutable source pixels.

The generated image supplies a spatial prior, never scientific coordinates.
Reviewed anchor correspondences register that prior. THU measures only original
colour evidence that overlaps the prior, after original-image exclusions.
"""
from copy import deepcopy
import csv
import json
from pathlib import Path
import shutil

import cv2
import numpy as np
from PIL import Image, ImageDraw
from .engine import axes, FIELDS, render, run, save_json
from .masks import mask_overlay, read_config, region_mask, sha256

PROMPT_VERSION = 'visible-selection-v2'


def prepare(config_path, series_name, target, out, mode='line', legacy=False):
    config_path, out = Path(config_path), Path(out)
    config, source = read_config(config_path)
    if config['kind'] not in {'line', 'scatter'}:
        raise ValueError('AI selection supports lines and scatter. Heatmap colour values must use the original image.')
    if mode not in {'line', 'markers'} or (mode == 'line') != (config['kind'] == 'line'):
        raise ValueError('Use line for line charts and markers for scatter charts.')
    matches = [s for s in config['series'] if s['name'] == series_name]
    if len(matches) != 1 or not target.strip():
        raise ValueError('Choose exactly one existing series and a visual target description.')
    if out.exists() and any(out.iterdir()):
        raise ValueError('Use an empty bundle directory; existing evidence is never overwritten.')
    image = Image.open(source).convert('RGB')
    if image.width > 1472 or image.height > 960:
        raise ValueError('Crop/render to at most 1472×960, then recalibrate before preparing. No automatic resizing.')
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, out / ('source' + source.suffix.lower()))
    image.save(out / 'original.png')
    exclusions = region_mask(image.size, config.get('exclusions', []), series=series_name)
    mask_overlay(image, exclusions).save(out / 'legend-overlay.png')
    pixels = np.array(image); pixels[exclusions] = 255
    cleaned = Image.fromarray(pixels)
    # Pure padding, with recorded offset. No original marks are moved or scaled.
    canvas = Image.new('RGB', (1536, 1024), 'white'); canvas.paste(cleaned, (32, 32))
    canvas.save(out / 'prepared.png')
    l, t, r, b = [v + 32 for v in config['plot_bounds']]
    if legacy:
        prompt = f'Change ONLY {target} to solid red. Keep all other lines, axes, gridlines, legend, and caption exactly as they are. Keep the full 1536×1024 canvas unchanged.'
    else:
        shape = ('Recolour the existing stroke only. Keep every original bend, discontinuity and stroke width. Do not smooth or connect gaps.' if mode == 'line' else
                 'Fill ONLY the already-visible target marker interiors solid red (#ff0000). Preserve each centre, outer boundary, diameter and partial edge clipping. Do not create circles at inferred locations. Do not recolour the fitted line, error bars, or confidence bands.')
        prompt = f'''SCIENTIFIC IMAGE SEGMENTATION — {PROMPT_VERSION}
Edit the supplied image, preserving the exact 1536×1024 canvas and layout.
ONE target: {target}
The plot rectangle on this padded canvas is ({l}, {t}) to ({r}, {b}), inclusive.

1. GEOMETRY LOCK. Outside this plot rectangle preserve every pixel, axis label, tick, panel title and blank margin. Inside it preserve axis/spine positions. Do not crop, zoom, stretch, rotate, re-typeset or redraw the chart. Never use a nicer representative curve.
2. EXCLUDE FIRST. White rectangles already applied are reviewed legend/annotation exclusions. Keep them blank. Remove all remaining legend samples, legend text, panel annotations and decorative symbols INSIDE the plot. A legend key is never a data point even when its colour matches the target. Do not erase an entire column merely because it contains a legend.
3. SELECT. Identify the target by its original colour AND line/marker style AND series identity. {shape}
4. CLEAN. Erase all other curves, markers, gridlines, uncertainty ribbons, error bars, fit lines and text inside the plot to white, except the selected target and axis spines. Remove any pre-existing red non-target series. Red must encode the target alone, never the background or axes.
5. NO INVENTION. Hidden, occluded, ambiguous or inseparable marks stay blank. Never reconstruct data under a removed legend, fill a confidence band, complete a partial marker, add points on a smooth fit, or extrapolate endpoints. Do not output numbers, tables, a new legend, or a drawing of an extraction grid.
6. CHECK. Output one edited image only: identical canvas, same axes, target-visible-pixels in pure red (#ff0000), other plot content white. If selection is ambiguous, omit it rather than inventing geometry.
'''
    (out / 'prompt.txt').write_text(prompt + '\n', encoding='utf-8')
    save_json(out / 'bundle.json', dict(schema_version=1, config=config, series=series_name, mode=mode,
        target=target, prompt_version='legacy-retain-others-v1' if legacy else PROMPT_VERSION,
        source_file='source'+source.suffix.lower(), source_sha256=sha256(source), prepared_sha256=sha256(out/'prepared.png'),
        prompt_sha256=sha256(out/'prompt.txt'), padding_offset=[32,32], canvas_size=[1536,1024]))
    return out


def registration(review, source_hash, generated_hash, bounds):
    if not review.get('reviewed') or not str(review.get('review_note','')).strip():
        raise ValueError('Visually review the edited image and record review_note before extracting.')
    if review.get('source_sha256') != source_hash or review.get('generated_sha256') != generated_hash:
        raise ValueError('Review must be bound to both exact images. Never copy hashes to bypass review.')
    points = np.asarray(review.get('anchor_pairs', []), dtype=float)
    if points.ndim != 2 or points.shape[1] != 4 or len(points) < 4 or not np.isfinite(points).all():
        raise ValueError('Need ≥4 reviewed [original_x,original_y,edited_x,edited_y] landmarks.')
    l,t,r,b = bounds
    if np.ptp(points[:,0]) < .7*(r-l) or np.ptp(points[:,1]) < .7*(b-t):
        raise ValueError('Landmarks must span ≥70% of both plot dimensions.')
    # Axis-aligned affine fit, justified by reviewed anchors, never by image sizes.
    a = np.linalg.lstsq(np.column_stack([points[:,2], np.ones(len(points))]), points[:,0], rcond=None)[0]
    d = np.linalg.lstsq(np.column_stack([points[:,3], np.ones(len(points))]), points[:,1], rcond=None)[0]
    transform = np.array([[a[0],0,a[1]],[0,d[0],d[1]]], dtype=float)
    predicted = points[:,2:] @ transform[:,:2].T + transform[:,2]
    residual = float(np.linalg.norm(predicted-points[:,:2], axis=1).max())
    if residual > 1.5 or a[0] <= 0 or d[0] <= 0 or not .2 <= a[0]/d[0] <= 5:
        raise ValueError('Inconsistent landmarks; reject distorted edit and review the source again.')
    return transform, residual


def support_masks(original, generated, config, series, transform, radius=3):
    if not 0 <= radius <= 5:
        raise ValueError('Support radius must be between 0 and 5 source pixels.')
    red = (generated[:,:,0] > 150) & (generated[:,:,1] < 100) & (generated[:,:,2] < 100)
    prior = cv2.warpAffine(red.astype(np.uint8), transform, (original.shape[1],original.shape[0]), flags=cv2.INTER_NEAREST).astype(bool)
    mask = region_mask((original.shape[1],original.shape[0]), config.get('exclusions',[]), series=series['name'])
    l,t,r,b = config['plot_bounds']; roi=np.zeros(mask.shape,bool);roi[t:b+1,l:r+1]=True
    target = np.array([int(series['color'][i:i+2],16) for i in (1,3,5)])
    params = series.get('parameters', {})
    tolerance = params.get('color_tolerance', params.get('tolerance',48))
    original_support = np.linalg.norm(original.astype(float)-target,axis=2) <= tolerance
    original_support &= roi & ~mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*radius+1,2*radius+1))
    accepted = original_support & cv2.dilate(prior.astype(np.uint8),kernel).astype(bool)
    near_source = cv2.dilate(original_support.astype(np.uint8),kernel).astype(bool)
    unsupported = prior & ~near_source
    return prior, accepted, unsupported, mask


def write_grid(records, config, out, columns=49):
    """Fixed x-grid, nearest source column only; missing columns stay missing."""
    if config['kind'] != 'line' or not 2 <= columns <= 5001:
        raise ValueError('Fixed x grid needs a line chart and 2–5001 columns.')
    xa,ya=axes(config); l,t,r,b=config['plot_bounds']
    lookup={int(p['x_pixel']):p for p in records}
    rows=[]
    for i,xp in enumerate(np.linspace(l,r,columns)):
        nearest=int(np.floor(xp+.5)); p=lookup.get(nearest,{})
        if p.get('status') in {'low_confidence','candidate_not_authorized'}:p={**p,'y':None}
        # Grid coordinate and measured source column are both retained.
        rows.append(dict(grid_column=i,grid_x=float(xa.value_at_pixel(xp)),sample_x_pixel=nearest,
            x=p.get('x',float(xa.value_at_pixel(nearest))), y=p.get('y'), status=p.get('status','missing'),
            data_type='digitized_approximation',source_sha256=config['image_sha256'],
            extraction_error=p.get('extraction_error') if p.get('y') is not None else None,x_error=p.get('x_error'),
            source_file=p.get('source_file',''),source_doi=config.get('source_doi',''),
            figure_or_table=config.get('figure',''),unit=config.get('unit','')))
    with (out/'grid.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    im=Image.open(out/'overlay.png').convert('RGB');draw=ImageDraw.Draw(im)
    for xp in np.linspace(l,r,columns):draw.line([(xp,t),(xp,b)],fill='#b8cbc5',width=1)
    for p in rows:
        if p['y'] is not None:
            xp=p['sample_x_pixel'];yp=float(ya.pixel_at_value(p['y']));draw.ellipse((xp-4,yp-4,xp+4,yp+4),fill='#e43a57')
    im.save(out/'grid-overlay.png')
    return rows


def extract(bundle, review_path, out, radius=3, grid_columns=49):
    bundle,out=Path(bundle),Path(out);meta=json.loads((bundle/'bundle.json').read_text());config=meta['config']
    source=bundle/meta['source_file'];generated_path=bundle/'generated.png'
    if sha256(source)!=meta['source_sha256'] or config['image_sha256']!=meta['source_sha256']:
        raise ValueError('Source changed after preparation.')
    review=json.loads(Path(review_path).read_text())
    transform,residual=registration(review,sha256(source),sha256(generated_path),config['plot_bounds'])
    series=next(s for s in config['series'] if s['name']==meta['series'])
    original=np.array(Image.open(source).convert('RGB'));generated=np.array(Image.open(generated_path).convert('RGB'))
    prior,accepted,unsupported,mask=support_masks(original,generated,config,series,transform,radius)
    out.mkdir(parents=True,exist_ok=True)
    selection=np.full_like(original,255);selection[accepted]=[255,0,0];Image.fromarray(selection).save(out/'selection.png')
    for name,array in [('ai-prior.png',prior),('accepted-mask.png',accepted),('unsupported-mask.png',unsupported)]:
        Image.fromarray(array.astype(np.uint8)*255).save(out/name)
    cfg=deepcopy(config);cfg.update(image='selection.png',image_sha256=sha256(out/'selection.png'),
        review_note='Derived selection: original colour pixels gated by reviewed AI prior; source review is retained in ai-report.json.')
    cfg['series']=[deepcopy(series)];cfg['series'][0]['color']='#ff0000'
    if config['kind']=='line':
        cfg['series'][0].setdefault('parameters',{}).update(tolerance=10,sigma=10)
    else:
        cfg['series'][0].setdefault('parameters',{})['color_tolerance']=10
    save_json(out/'selection-config.json',cfg)
    if config['kind']=='scatter':
        # Detect complete original marks BEFORE using AI selection. Cropping a
        # smooth fit with an AI dot must not manufacture a compact marker.
        source_cfg=deepcopy(config);source_cfg['image']=str(source.resolve());source_cfg['series']=[series]
        save_json(out/'source-candidates-config.json',source_cfg)
        candidates,_=run(out/'source-candidates-config.json',out/'source-candidates')
        nearby=cv2.dilate(prior.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*radius+1,2*radius+1)))
        records=[p for p in candidates if p['y'] is not None and p['status'] not in {'candidate_not_authorized','low_confidence'}
                 and nearby[int(round(p['y_pixel'])),int(round(p['x_pixel']))] and not mask[int(round(p['y_pixel'])),int(round(p['x_pixel']))]]
    else:
        records,_=run(out/'selection-config.json',out/'trace')
    # Restore scientific provenance to the unchanged original; selection is intermediate.
    shutil.copyfile(source,out/('source'+source.suffix.lower()))
    for row in records:
        row.update(source_file='source'+source.suffix.lower(),source_sha256=sha256(source))
    with (out/'data.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(records)
    final_cfg=deepcopy(config);final_cfg['series']=[series]
    render(Image.fromarray(original),final_cfg,records,out,mask)
    Image.fromarray(original).save(out/'original.png')
    image=Image.fromarray(original.copy());p=np.array(image);p[unsupported]=[255,0,180];p[accepted]=[0,180,130];Image.fromarray(p).save(out/'support-overlay.png')
    grid=write_grid(records,final_cfg,out,grid_columns) if config['kind']=='line' else []
    report=dict(schema_version=1,method='AI spatial prior + original-pixel support + THU',
        prompt_version=meta['prompt_version'],source_sha256=sha256(source),generated_sha256=sha256(generated_path),
        prompt_sha256=sha256(bundle/'prompt.txt'),csv_sha256=sha256(out/'data.csv'),review=review,
        transform_edited_to_original=transform.tolist(),max_anchor_residual_px=residual,support_radius_px=radius,
        prior_red_pixels=int(prior.sum()),accepted_original_pixels=int(accepted.sum()),unsupported_red_pixels=int(unsupported.sum()),
        numeric_rows=sum(p['y'] is not None for p in records),grid_rows=len(grid),
        limitations='Original pixel proximity does not prove series identity. Review crossings and false selections. No independent accuracy implied.',
        source_config=config,request=json.loads((bundle/'request.json').read_text()) if (bundle/'request.json').exists() else None)
    save_json(out/'ai-report.json',report)
    return records,report
