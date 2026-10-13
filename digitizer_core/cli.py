"""Command line interface: inspect, extract, and optional PDF rendering."""
import argparse
import json
import os
from pathlib import Path
from PIL import Image
from .masks import propose, region_mask, mask_overlay
from .engine import run, save_json


def main(argv=None):
    parser=argparse.ArgumentParser(description="Digitizer · Make figures reusable.")
    subs=parser.add_subparsers(dest="command",required=True)
    p=subs.add_parser("inspect",help="Create an unreviewed, image-bound calibration config")
    p.add_argument("image",type=Path);p.add_argument("--plot-bounds",required=True,help="left,top,right,bottom")
    p.add_argument("--ocr",action="store_true");p.add_argument("--ocr-json",type=Path);p.add_argument("--out",type=Path,required=True)
    p=subs.add_parser("extract",help="Extract from visually reviewed config")
    p.add_argument("--config",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    p=subs.add_parser("render-pdf",help="Render one PDF page before calibrating")
    p.add_argument("pdf",type=Path);p.add_argument("--page",type=int,required=True,help="1-based page")
    p.add_argument("--dpi",type=int,default=200);p.add_argument("--out",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=="inspect":
            bounds=[int(x) for x in args.plot_bounds.split(",")]
            with Image.open(args.image) as im:region_mask(im.size,[dict(bounds=bounds,verified=True)])
            items=json.loads(args.ocr_json.read_text()) if args.ocr_json else []
            if args.ocr:
                from rapidocr_onnxruntime import RapidOCR
                items,_=RapidOCR()(str(args.image));items=items or []
            config=propose(args.image,bounds,items);args.out.parent.mkdir(parents=True,exist_ok=True)
            config["image"]=os.path.relpath(args.image.resolve(),args.out.parent.resolve());save_json(args.out,config)
            im=Image.open(args.image);mask=region_mask(im.size,config["exclusions"],require_review=False)
            mask_overlay(im,mask).save(args.out.with_suffix(".overlay.png"))
            print(f"{args.out}: review {len(config['exclusions'])} proposed regions, axes and series.")
        elif args.command=="extract":
            _,report=run(args.config,args.out);print(f"{report['numeric_rows']} numeric rows; evidence: {args.out}")
        else:
            import fitz
            with fitz.open(args.pdf) as doc:
                if not 1<=args.page<=len(doc) or not 36<=args.dpi<=1200:raise ValueError("Invalid page or DPI.")
                args.out.parent.mkdir(parents=True,exist_ok=True);doc[args.page-1].get_pixmap(dpi=args.dpi).save(args.out)
            print(args.out)
    except (ValueError,KeyError,ImportError) as exc:
        parser.exit(2,f"digitizer: {exc}\n")


if __name__=="__main__":main()
