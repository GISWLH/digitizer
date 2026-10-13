"""Reviewed, image-bound masks in original image coordinates.

Masks alter detector support, never the source image or underlying observations.
One small region per swatch/text row is preferable to a whole legend rectangle
when data remain visible between rows. Opaque legend backgrounds stay excluded.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_config(path):
    path = Path(path).resolve()
    config = json.loads(path.read_text(encoding="utf-8"))
    image = (path.parent / config["image"]).resolve()
    with Image.open(image) as im:
        size = list(im.size)
    if config.get("image_sha256") != sha256(image) or config.get("image_size") != size:
        raise ValueError("Image changed: re-inspect this exact image and its coordinates.")
    if config.get("reviewed") is not True:
        raise ValueError("Review axes, series and legend overlay before setting reviewed=true.")
    if not config.get("review_note", "").strip():
        raise ValueError("A review_note describing the visual calibration is required.")
    return config, image


def region_mask(size, regions, series=None, *, require_review=True):
    width, height = size
    canvas = Image.new("1", size, 0)
    draw = ImageDraw.Draw(canvas)
    for region in regions:
        if require_review and region.get("verified") is not True:
            raise ValueError("Each retained region needs verified=true after visual review.")
        scope = region.get("series")
        if scope is not None and series is not None and series not in scope:
            continue
        kind = region.get("type", "rectangle")
        if kind == "rectangle":
            points = region.get("bounds", [])
            if len(points) != 4:
                raise ValueError("Rectangle needs bounds [left, top, right, bottom].")
            l, t, r, b = points
            if not (0 <= l < r < width and 0 <= t < b < height):
                raise ValueError("Rectangle is outside the image or has no area.")
            vertices = [(l, t), (r, b)]
        elif kind == "polygon":
            vertices = region.get("points", [])
            if len(vertices) < 3 or any(len(p) != 2 for p in vertices):
                raise ValueError("Polygon needs at least three [x, y] vertices.")
            area = abs(sum(vertices[i][0]*vertices[(i+1)%len(vertices)][1] - vertices[(i+1)%len(vertices)][0]*vertices[i][1] for i in range(len(vertices))))
            if area == 0:
                raise ValueError("Polygon has no area.")
        else:
            raise ValueError("Use rectangle or polygon masks.")
        for x, y in vertices:
            if isinstance(x, bool) or isinstance(y, bool) or not (float(x).is_integer() and float(y).is_integer() and 0 <= x < width and 0 <= y < height):
                raise ValueError("Masks use integer original-image pixels inside the canvas.")
        if kind == "rectangle":
            draw.rectangle([tuple(p) for p in vertices], fill=1)
        else:
            draw.polygon([tuple(p) for p in vertices], fill=1)
    return np.asarray(canvas, dtype=bool)


def mask_overlay(image, mask):
    rgb = np.asarray(image.convert("RGB")).copy()
    rgb[mask] = (rgb[mask].astype(float)*.35 + np.array([245, 74, 139])*.65).astype(np.uint8)
    return Image.fromarray(rgb)


def propose(image_path, bounds, ocr_items=None):
    """OCR + swatch candidates are suggestions, never extraction authorization."""
    from ._thu.legend_regions import propose_legends
    image_path = Path(image_path)
    with Image.open(image_path) as im:
        regions = propose_legends(im, bounds, ocr_items or [])
        size = list(im.size)
    return dict(schema_version=1, image=image_path.name, image_sha256=sha256(image_path),
                image_size=size, plot_bounds=bounds, reviewed=False, review_note="",
                exclusions=[dict(type="rectangle", **r) for r in regions],
                axes={"x": {"anchors": [], "scale": "linear"}, "y": {"anchors": [], "scale": "linear"}},
                kind="line", series=[],
                note="Verify tick anchors, series colours and exclusions; no detected legend does not mean none exists.")
