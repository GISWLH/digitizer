"""Source-locked, reviewed legend exclusions. Boxes use inclusive image pixels.

Standalone companion, mirrored into THU. No remote service, recoloring or resize.
"""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from PIL import Image,ImageDraw

def parse_region(value):
    try:
        box=tuple(int(x.strip()) for x in value.split(','))
        if len(box)!=4 or box[0]>=box[2] or box[1]>=box[3]:raise ValueError()
        return box
    except ValueError as exc:raise argparse.ArgumentTypeError('use left,top,right,bottom integers') from exc

def validate_regions(regions,width,height):
    result=[]
    for box in regions:
        if len(box)!=4 or any(isinstance(v,bool) or int(v)!=v for v in box):raise ValueError('region must have four integer pixel coordinates')
        l,t,r,b=map(int,box)
        if not (0<=l<r<width and 0<=t<b<height):raise ValueError(f'exclusion {box} outside {width}x{height}')
        if (l,t,r,b) not in result:result.append((l,t,r,b))
    return result

def exclusion_mask(shape,regions):
    h,w=shape[:2];mask=np.zeros((h,w),bool)
    for l,t,r,b in validate_regions(regions,w,h):mask[t:b+1,l:r+1]=True
    return mask

def inside_region(x,y,regions):
    return any(l<=x<=r and t<=y<=b for l,t,r,b in regions)

def resolve_regions(image_path,regions=(),config_path=None):
    path=Path(image_path)
    with Image.open(path) as im:w,h=im.size
    boxes=list(regions)
    if config_path:
        data=json.loads(Path(config_path).read_text(encoding='utf-8-sig'))
        if data.get('image_sha256')!=hashlib.sha256(path.read_bytes()).hexdigest() or data.get('image_size')!=[w,h]:
            raise ValueError('exclusion source mismatch: review this exact image; do not reuse resized/recolored coordinates')
        if data.get('reviewed') is not True:raise ValueError('legend candidates need visual review; set reviewed=true only after checking the overlay')
        for item in data.get('regions',[]):
            if item.get('verified') is not True:raise ValueError('every retained region must be verified or removed')
            boxes.append(item['bounds'])
    return validate_regions(boxes,w,h)

def draw_regions(image,regions):
    out=image.convert('RGB').copy();d=ImageDraw.Draw(out)
    for i,box in enumerate(regions):d.rectangle(box,outline='#e9a400',width=2);d.text((box[0]+3,box[1]+2),f'exclude {i+1}',fill='#9b6400')
    return out

def save_exclusion_evidence(image_path,regions,report_path,overlay_path=None,**metadata):
    path=Path(image_path);im=Image.open(path);boxes=validate_regions(regions,*im.size)
    record=dict(image_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),image_size=list(im.size),coordinate_space='original_raster_pixels',exclude_regions=boxes,excluded_pixels=int(exclusion_mask((im.height,im.width),boxes).sum()),**metadata)
    report_path=Path(report_path);report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(json.dumps(record,indent=2,ensure_ascii=False),encoding='utf8')
    if overlay_path:draw_regions(im,boxes).save(overlay_path)

def propose_legends(image,plot_bounds,ocr_items):
    """Candidate only: OCR label plus a nearby short line or compact swatch.

    No blind corner masks; neither labels alone nor short strokes alone qualify.
    Review is mandatory, because data annotations can have the same grammar.
    """
    import cv2
    rgb=np.asarray(image.convert('RGB'));h,w=rgb.shape[:2];pl,pt,pr,pb=plot_bounds;found=[]
    # Whole-image components prevent a clipped grid line looking like a swatch.
    fg=(rgb.min(2)<200).astype(np.uint8)
    _,labels,stats,centers=cv2.connectedComponentsWithStats(fg,8)
    for poly,label,confidence in ocr_items:
        if float(confidence)<.70 or not any(ch.isalpha() for ch in label):continue
        q=np.asarray(poly);l,t=q.min(0);r,b=q.max(0);th=b-t;cy=(t+b)/2
        if th<6 or r<pl or l>pr or cy<pt or cy>pb:continue
        candidates=[]
        for x,y,cw,ch,area in stats[1:]:
            if not (max(pl,l-9*th)<=x and x+cw<=l+3 and abs(y+ch/2-cy)<.5*th):continue
            short_line=(.8*th<=cw<=8*th and ch<=.7*th and cw/max(ch,1)>=3 and area/(cw*ch)>.35)
            marker=(.25*th<=cw<=1.4*th and .25*th<=ch<=1.4*th and .5<=cw/ch<=2 and area/(cw*ch)>.45)
            if short_line or marker:candidates.append((x,y,x+cw-1,y+ch-1))
        # Dashed legend keys consist of several small, collinear components.
        if not candidates:
            pieces=[]
            for x,y,cw,ch,area in stats[1:]:
                if max(pl,l-5*th)<=x and x+cw<=l+3 and abs(y+ch/2-cy)<.22*th and 2<=cw<=3*th and ch<=.45*th and cw>=ch:
                    pieces.append((x,y,x+cw-1,y+ch-1))
            if len(pieces)>=2:
                xl=min(z[0] for z in pieces);xr=max(z[2] for z in pieces)
                if .8*th<=xr-xl<=5*th:candidates.append((xl,min(z[1] for z in pieces),xr,max(z[3] for z in pieces)))
        if not candidates:continue
        sw=max(candidates,key=lambda z:z[2]);pad=3
        box=[max(pl,int(min(l,sw[0]))-pad),max(pt,int(min(t,sw[1]))-pad),min(pr,int(max(r,sw[2]))+pad),min(pb,int(max(b,sw[3]))+pad)]
        if box[0]<box[2] and box[1]<box[3]:found.append(dict(bounds=box,label=label,verified=False,reason='OCR label with nearby short line/compact marker; requires visual confirmation'))
    return found

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);ap.add_argument('--plot-bounds',required=True,type=parse_region);ap.add_argument('--exclude-region',action='append',type=parse_region,default=[]);ap.add_argument('--ocr',action='store_true',help='optional local RapidOCR candidate proposals (never auto-approved)');args=ap.parse_args()
    im=Image.open(args.input).convert('RGB');validate_regions([args.plot_bounds,*args.exclude_region],*im.size)
    regions=[dict(bounds=list(b),verified=True,reason='explicit user/agent-selected rectangle') for b in args.exclude_region];ocr_status='not_requested'
    if args.ocr:
        try:from rapidocr_onnxruntime import RapidOCR
        except ImportError as exc:raise SystemExit('Optional local OCR missing. Install rapidocr_onnxruntime or supply --exclude-region.') from exc
        items,_=RapidOCR(intra_op_num_threads=2,inter_op_num_threads=2)(str(args.input));regions+=propose_legends(im,args.plot_bounds,items or []);ocr_status='completed'
    data=dict(schema_version=1,image_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),image_size=list(im.size),plot_bounds=args.plot_bounds,reviewed=bool(args.exclude_region) and not args.ocr,regions=regions,ocr_status=ocr_status,note='Review overlay; confirm, refine or remove candidates. An empty candidate list does not prove there is no legend. Same dimensions do not justify reusing this config after AI editing.')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf8');draw_regions(im,[r['bounds'] for r in regions]).save(args.output.with_suffix('.overlay.png'));print(f'{len(regions)} regions; reviewed={data["reviewed"]}; {args.output}')

if __name__=='__main__':main()
