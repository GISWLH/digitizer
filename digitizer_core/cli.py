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
    p=subs.add_parser("ai-prepare",help="Prepare reviewed masks and a single-target image-edit prompt (offline)")
    p.add_argument("--config",type=Path,required=True);p.add_argument("--series",required=True)
    p.add_argument("--target",required=True);p.add_argument("--mode",choices=["line","markers"],default="line")
    p.add_argument("--legacy-prompt",action="store_true",help="A/B control only: retain other plot content")
    p.add_argument("--out",type=Path,required=True)
    p=subs.add_parser("ai-edit",help="Make one paid image-edit request; explicit opt-in, no fallback")
    p.add_argument("--bundle",type=Path,required=True);p.add_argument("--provider",choices=["apiyi","gemini"],required=True)
    p.add_argument("--model");p.add_argument("--timeout",type=int,default=600)
    p=subs.add_parser("ai-extract",help="Use reviewed AI colour selection to gate original-pixel extraction")
    p.add_argument("--bundle",type=Path,required=True);p.add_argument("--review",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True);p.add_argument("--radius",type=int,default=3)
    p.add_argument("--columns",type=int,default=49)
    p=subs.add_parser("grid",help="Offline fixed-column line sampling or calibrated heatmap-cell extraction")
    p.add_argument("--config",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    p.add_argument("--columns",type=int,default=49)
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
        elif args.command=="ai-prepare":
            from .ai_assist import prepare
            print(prepare(args.config,args.series,args.target,args.out,args.mode,args.legacy_prompt))
        elif args.command=="ai-edit":
            from .ai_provider import edit
            info=edit(args.bundle,args.provider,args.model,args.timeout)
            print(f"{info['provider']} / {info['model']}: {info['status']}")
        elif args.command=="ai-extract":
            from .ai_assist import extract
            _,report=extract(args.bundle,args.review,args.out,args.radius,args.columns)
            print(f"{report['numeric_rows']} source-supported rows; evidence: {args.out}")
        elif args.command=="grid":
            from .grid import extract_grid
            report=extract_grid(args.config,args.out,args.columns)
            print(f"{report['grid_rows']} grid rows; evidence: {args.out}")
        else:
            import fitz
            with fitz.open(args.pdf) as doc:
                if not 1<=args.page<=len(doc) or not 36<=args.dpi<=1200:raise ValueError("Invalid page or DPI.")
                args.out.parent.mkdir(parents=True,exist_ok=True);doc[args.page-1].get_pixmap(dpi=args.dpi).save(args.out)
            print(args.out)
    except (ValueError,KeyError,ImportError) as exc:
        parser.exit(2,f"digitizer: {exc}\n")


if __name__=="__main__":main()
