"""THU engines with source-locked masks, gap preservation and shared evidence."""
from pathlib import Path
import csv
import json
import math
import shutil
import numpy as np
import cv2
from PIL import Image, ImageDraw
from .masks import read_config, region_mask, mask_overlay, sha256
from ._thu.raster_digitizer_core import AxisCalibration, trace_colour_path
from ._thu.candidate_digitize_scatter import extract_scatter_points
from ._thu.candidate_digitize_bar_chart import extract_bar_chart
from ._thu.candidate_digitize_heatmap import extract_heatmap


FIELDS = ["series", "x", "y", "x_pixel", "y_pixel", "status", "data_type", "extraction_error", "x_error", "source_file", "source_sha256", "source_doi", "figure_or_table", "unit", "category", "value_status", "interval_low", "interval_high", "bar_left_pixel", "bar_top_pixel", "bar_right_pixel", "bar_bottom_pixel", "start_value", "end_value"]


def save_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")


def axes(config):
    result = []
    for name in ("x", "y"):
        c = config["axes"][name]
        pairs = np.asarray(c["anchors"], dtype=float)
        if pairs.ndim != 2 or pairs.shape[1] != 2 or not np.isfinite(pairs).all():
            raise ValueError("Axis anchors must be finite [pixel, value] pairs.")
        result.append(AxisCalibration.fit(pairs, scale=c.get("scale", "linear")))
    return result


def hollow_points(rgb, mask, bounds, color, tolerance, min_radius=2, max_radius=18):
    """Measure complete visible ring interiors; no repair or invented centres.

    Child contours describe ring holes, so touching rings can still have separate
    centres. Ellipse/circularity evidence rejects labels and open arc fragments.
    """
    target = np.array([int(color[i:i+2], 16) for i in (1,3,5)])
    binary = (np.linalg.norm(rgb.astype(float)-target, axis=2) <= tolerance).astype(np.uint8)
    l,t,r,b = bounds
    roi = np.zeros(binary.shape, bool); roi[t:b+1,l:r+1] = True
    binary[~roi | mask] = 0
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    points = []
    if hierarchy is None:
        return points
    for contour, relation in zip(contours, hierarchy[0]):
        if relation[3] < 0 or len(contour) < 8:
            continue
        (x,y),(w,h),_ = cv2.fitEllipse(contour)
        perimeter = cv2.arcLength(contour,True); area = cv2.contourArea(contour)
        radius = (w+h)/4
        if not (min_radius <= radius <= max_radius and .65 <= w/h <= 1.54 and 4*math.pi*area/max(perimeter**2,1) > .55):
            continue
        # A masked hole cannot become an observation.
        x0,x1 = max(0,int(x-radius-2)), min(mask.shape[1],int(x+radius+3))
        y0,y1 = max(0,int(y-radius-2)), min(mask.shape[0],int(y+radius+3))
        if mask[y0:y1,x0:x1].any():
            continue
        points.append(dict(x_pixel=float(x), y_pixel=float(y), uncertainty_px=.75))
    return points


def isolated_points(rgb, mask, bounds, color, color_tolerance=36, min_diameter=4, max_diameter=18):
    """Measure isolated compact coloured cores separated by an outline.

    Useful for marker + same-colour curve composites: long curve components
    cannot qualify as isolated marks. Partial edge cores stay visibly flagged.
    This route cannot split fused markers; use THU distance peaks for those.
    """
    target=np.array([int(color[i:i+2],16) for i in (1,3,5)])
    foreground=np.linalg.norm(rgb.astype(float)-target,axis=2)<=color_tolerance
    l,t,r,b=bounds;roi=np.zeros(mask.shape,bool);roi[t:b+1,l:r+1]=True
    foreground[~roi|mask]=False
    _,labels,stats,centres=cv2.connectedComponentsWithStats(foreground.astype(np.uint8),8)
    points=[]
    for (x,y,w,h,area),(cx,cy) in zip(stats[1:],centres[1:]):
        if not (min_diameter<=w<=max_diameter and min_diameter<=h<=max_diameter and .5<=w/h<=2 and .5<=area/(w*h)<=.94):continue
        if mask[max(0,y-1):y+h+1,max(0,x-1):x+w+1].any():continue
        partial=(x<=l or x+w-1>=r or y<=t or y+h-1>=b or min(w,h)/max(w,h)<.75)
        points.append(dict(x_pixel=float(cx),y_pixel=float(cy),uncertainty_px=max(w,h)/4 if partial else .75,
                           status="partial_visible_marker" if partial else "visible"))
    return points


def run(config_path, output_dir, *, ignore_exclusions=False):
    config_path, output_dir = Path(config_path), Path(output_dir)
    config, image_path = read_config(config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    source_name = 'source' + image_path.suffix.lower()
    if image_path.resolve() != (output_dir/source_name).resolve():
        shutil.copyfile(image_path, output_dir/source_name)
    image = Image.open(image_path).convert("RGB"); rgb = np.asarray(image)
    kind = config["kind"]
    if kind not in {"line", "scatter", "bar", "heatmap"}:
        raise ValueError("Supported kinds: line, scatter, bar, heatmap.")
    exclusions = [] if ignore_exclusions else config.get("exclusions", [])
    all_mask = region_mask(image.size, exclusions)
    mask_overlay(image, all_mask).save(output_dir/"legend-overlay.png")
    Image.fromarray(all_mask.astype(np.uint8)*255).save(output_dir/"exclusion-mask.png")
    image.save(output_dir/"original.png")
    records, details = [], {}
    if kind in {"line", "scatter"}:
        xaxis, yaxis = axes(config)
        bounds = tuple(config["plot_bounds"])
        names = [s["name"] for s in config["series"]]
        if not names or len(names) != len(set(names)):
            raise ValueError("Provide unique, nonempty series names.")
        for series in config["series"]:
            name, color = series["name"], series["color"]
            if series.get("marker", "filled") not in {"filled", "hollow", "isolated"}:
                raise ValueError("Unknown marker route: use filled, hollow, or isolated.")
            mask = region_mask(image.size, exclusions, name)
            options = dict(series.get("parameters", {}))
            if kind == "line":
                # A long horizontal stroke can be valid scientific data.
                # Axes/grid lines need explicit geometry; occupancy is not proof.
                options.setdefault("suppress_horizontal", False)
                options.setdefault("min_chroma_fraction", .12)
                trace = trace_colour_path(rgb, target=color, plot_bounds=bounds, exclusion_bitmap=mask, **options)
                details[name] = trace
                points = [dict(x_pixel=p["x_pixel"], y_pixel=p["y_pixel"], status=p["status"], uncertainty_px=p.get("uncertainty_px")) for p in trace["path"]]
            elif series.get("marker", "filled") == "hollow":
                points = hollow_points(rgb, mask, bounds, color, **dict(tolerance=options.pop("color_tolerance",36), **options))
                details[name] = {"route": "visible_ring_interiors", "status": "candidate", "count": len(points)}
            elif series.get("marker") == "isolated":
                points = isolated_points(rgb, mask, bounds, color, **options)
                details[name] = {"route": "isolated_compact_cores", "status": "candidate", "count": len(points),
                    "limitations": "Fused or fully occluded cores are not recoverable. Partial cores have increased uncertainty."}
            else:
                report = extract_scatter_points(image_path, plot_bounds=bounds,
                    x_anchors=config["axes"]["x"]["anchors"], y_anchors=config["axes"]["y"]["anchors"],
                    x_scale=xaxis.scale, y_scale=yaxis.scale, marker_mode="color", marker_color=color,
                    exclusion_bitmap=mask, **options)
                details[name] = report
                points = [dict(x_pixel=p["pixel_x"],y_pixel=p["pixel_y"],uncertainty_px=.75,
                               status="visible" if report["numeric_output_authorized"] else "candidate_not_authorized") for p in report["points"]]
            for p in points:
                px, py = p["x_pixel"], p["y_pixel"]
                if py is not None and mask[int(round(py)), int(round(px))]:
                    raise RuntimeError("Extractor emitted a value inside an exclusion.")
                status = p.get("status", "visible")
                records.append(dict(series=name,x=xaxis.value_at_pixel(px),y=yaxis.value_at_pixel(py) if py is not None else None,
                    x_pixel=px,y_pixel=py,status=status,
                    extraction_error=yaxis.uncertainty_at_pixel(py,pixel_sigma=p.get("uncertainty_px") or .75) if py is not None else None,
                    x_error=xaxis.uncertainty_at_pixel(px,pixel_sigma=.75)))
    elif kind == "bar":
        if any(r.get("type", "rectangle") != "rectangle" or r.get("series") for r in exclusions):
            raise ValueError("Bar route currently supports global rectangles only.")
        native = extract_bar_chart(image_path, exclude_regions=[tuple(r["bounds"]) for r in exclusions], **config["bar"])
        details["bar"] = native
        for p in native["marks"]:
            comp=p.get("component", {})
            records.append(dict(series=p["series"],category=p["category"],x=p["category"],y=p.get("value"),
                x_pixel=comp.get("category_pixel") if config['bar']['orientation']=='vertical' else p.get("end_pixel"),
                y_pixel=p.get("end_pixel") if config['bar']['orientation']=='vertical' else comp.get("category_pixel"),status=p["status"],
                bar_left_pixel=comp.get('left_pixel'),bar_right_pixel=comp.get('right_pixel'),
                bar_top_pixel=comp.get('top_pixel'),bar_bottom_pixel=comp.get('bottom_pixel'),
                start_value=p.get('start_value'),end_value=p.get('end_value'),
                extraction_error=abs((config["bar"]["value_axis"][3]-config["bar"]["value_axis"][1])/(config["bar"]["value_axis"][2]-config["bar"]["value_axis"][0]))))
    else:
        native = extract_heatmap(image_path, **config["heatmap"])
        details["heatmap"] = native
        for p in native["cells"]:
            bounds = p.get("cell_bounds_pixel")
            masked = bounds is not None and all_mask[bounds[1]:bounds[3]+1,bounds[0]:bounds[2]+1].any()
            interval = p.get("value_interval") or [None,None]
            records.append(dict(series=p["row_label"],category=p["column_label"],x=p["column_index"],y=None if masked else p.get("value"),
                x_pixel=(bounds[0]+bounds[2])/2 if bounds else None,y_pixel=(bounds[1]+bounds[3])/2 if bounds else None,
                status="excluded" if masked else p.get("status", "candidate"),value_status=p.get("value_status"),
                interval_low=interval[0],interval_high=interval[1],
                extraction_error=abs(config["heatmap"]["colorbar_top_value"]-config["heatmap"]["colorbar_bottom_value"])/(config["heatmap"]["colorbar_bounds"][3]-config["heatmap"]["colorbar_bounds"][1])))
    for row in records:
        row.update(data_type="digitized_approximation",source_file=source_name,source_sha256=config["image_sha256"],
            source_doi=config.get("source_doi", ""),figure_or_table=config.get("figure", ""),unit=config.get("unit", ""))
    with (output_dir/"data.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(records)
    present=sum(row["y"] is not None for row in records)
    report=dict(schema_version=1,engine="THU Digitizer + GISWLH legend-aware extensions",kind=kind,
        image_sha256=config["image_sha256"],config_sha256=sha256(config_path),csv_sha256=sha256(output_dir/"data.csv"),
        rows=len(records),numeric_rows=present,excluded_pixels=int(all_mask.sum()),
        ablation_ignore_exclusions=ignore_exclusions,config=config,details=details,
        note="Pixel uncertainty is an estimate, not measured accuracy. Compare separate reference data for accuracy.")
    save_json(output_dir/"report.json",report)
    render(image, config, records, output_dir, all_mask)
    return records, report


def render(image, config, records, out, mask):
    """Original-size extraction overlay and recreation, from CSV records only."""
    overlay = mask_overlay(image, mask); draw = ImageDraw.Draw(overlay)
    for p in records:
        x,y=p.get("x_pixel"),p.get("y_pixel")
        if p.get("y") is not None and x is not None and y is not None:
            draw.ellipse((x-2,y-2,x+2,y+2),outline="#0089de",width=1)
    overlay.save(out/"overlay.png")
    recreated = Image.new("RGB",image.size,"white"); d=ImageDraw.Draw(recreated)
    if config["kind"] in {"line","scatter"}:
        l,t,r,b=config["plot_bounds"];d.rectangle((l,t,r,b),outline="#475569",width=1)
        xa,ya=axes(config)
        for axis,cal in [("x",xa),("y",ya)]:
            for px,val in cal.anchors:
                if axis=="x":d.text((px,b+8),f"{val:g}",fill="#475569")
                else:d.text((max(0,l-40),px),f"{val:g}",fill="#475569")
        for series in config["series"]:
            previous=None
            for p in (p for p in records if p["series"]==series["name"]):
                x,y=p["x_pixel"],p["y_pixel"]
                if p["y"] is None:previous=None;continue
                if config["kind"]=="line":
                    if previous is not None and x-previous[0]<=1.5:d.line([previous,(x,y)],fill=series["color"],width=3)
                    previous=(x,y)
                else:d.ellipse((x-4,y-4,x+4,y+4),fill=series["color"])
    elif config["kind"]=="heatmap":
        hc=config["heatmap"];l,t,r,b=hc["grid_bounds"]
        source=np.asarray(image);bl,bt,br,bb=hc["colorbar_bounds"]
        for p in records:
            if p["y"] is None:continue
            i=hc["row_labels"].index(p["series"]);j=hc["column_labels"].index(p["category"])
            # Palette comes from the visible colour bar, values only from extracted rows.
            k=int(round(bt+(p["y"]-hc["colorbar_top_value"])/(hc["colorbar_bottom_value"]-hc["colorbar_top_value"])*(bb-bt)))
            color=tuple(map(int,np.median(source[np.clip(k,bt,bb),bl:br+1],axis=0)))
            w=(r-l)/len(hc["column_labels"]);h=(b-t)/len(hc["row_labels"])
            d.rectangle((l+j*w,t+i*h,l+(j+1)*w,t+(i+1)*h),fill=color)
    else:
        bc=config["bar"];l,t,r,b=bc["plot_bounds"];d.rectangle((l,t,r,b),outline="#475569")
        for p in records:
            if p["y"] is None:continue
            d.rectangle((p['bar_left_pixel'],p['bar_top_pixel'],p['bar_right_pixel'],p['bar_bottom_pixel']),fill=bc["series_colors"][p["series"]])
    recreated.save(out/"recreated.png")
    pair=Image.new("RGB",(image.width*2,image.height+48),"#f8fafc")
    pair.paste(image,(0,48));pair.paste(recreated,(image.width,48))
    draw=ImageDraw.Draw(pair);draw.text((20,17),"ORIGINAL",fill="#0f172a");draw.text((image.width+20,17),"RECREATED FROM CSV",fill="#0f172a")
    pair.save(out/"comparison.png")
