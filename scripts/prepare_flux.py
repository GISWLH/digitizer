"""Rebuild FLUX image fixtures and independent PDF-path references.

Requires the two existing local papers; PDF files are never published here.
Vector paths are written ONLY to reference files, never to extractor configs.
"""
from pathlib import Path
import argparse, csv, hashlib, json, sys
import pymupdf as fitz
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from digitizer_core.engine import save_json
from digitizer_core.masks import sha256

def main():
 p=argparse.ArgumentParser();p.add_argument('--papers',type=Path,default=ROOT.parent/'flux/data/raw/papers');a=p.parse_args()
 out=ROOT/'benchmarks/flux';out.mkdir(exist_ok=True);manifest=[]
 paper=a.papers/'ef263d1c5a9d4328d47f/paper.pdf';assert sha256(paper)=='7ae6c2e3f79e59ae7cd0db31c594d75a03dfd0dd13d10c9d4bad1fc87f5a9360', 'Unexpected Veenendaal PDF snapshot'
 doc=fitz.open(paper)
 context=out/'context';context.mkdir(exist_ok=True)
 doc[8].get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(120,308,474,603)).save(context/'veenendaal-figure10.png')
 # Coordinates are PDF points. Axes reviewed against ticks; day-of-year wraps
 # at the 2004/2005 boundary, so x is explicitly unwrapped (366 + 2005 DOY).
 definitions=[
 ('f01','泥炭草地 · 日 NEE','Peat grassland · daily NEE','泥炭草地の日別 NEE',8,[120,308,474,403],[161,321,467,393],[[161.506,275],[463.309,635]],[[362.05,0],[323.2,750]],[158,161],[-600,800],'NEE',[([350,321,356,341],['Oukoop']),([374,320,381,338],['Stein'])]),
 ('f02','泥炭草地 · 生态系统呼吸','Peat grassland · respiration','泥炭草地の生態系呼吸',8,[120,404,474,484],[159,407,467,480],[[159.224,275],[463.256,635]],[[474.71,0],[408.53,900]],[344,347],[-150,950],'Reco',[([283,436,290,455],[])]),
 ('f03','泥炭草地 · 总生态系统光合','Peat grassland · gross photosynthesis','泥炭草地の総生態系光合成',8,[120,484,474,603],[161,494,467,568],[[161.18,275],[462.77,635]],[[565,-950],[499.69,50]],[1537,1540],[-1000,150],'GEP',[]),
 ('f04','泥炭草地 · 累积碳交换','Peat grassland · cumulative NEE','泥炭草地の累積炭素交換',9,[124,60,478,252],[170,69,464,208],[[170.09,275],[460.731,635]],[[207.70,-10],[69.03,15]],[214,217],[-10,15],'cumulative_NEE',[])]
 for cid,zh,en,ja,page,crop,bounds,xx,yy,paths,ylim,var,regions in definitions:
  folder=out/cid;folder.mkdir(exist_ok=True);scale=4
  clip=fitz.Rect(crop);pix=doc[page].get_pixmap(matrix=fitz.Matrix(scale,scale),clip=clip);pix.save(folder/'input.png')
  def x(v):return (v-crop[0])*scale
  def y(v):return (v-crop[1])*scale
  b=[round(x(bounds[0])),round(y(bounds[1])),round(x(bounds[2])),round(y(bounds[3]))]
  drawings=doc[page].get_drawings();series=[];truth=[]
  for name,index in zip(['Oukoop','Stein'],paths):
   drawing=drawings[index];color='#'+''.join(f'{round(c*255):02x}' for c in drawing['color'])
   series.append(dict(name=name,color=color,parameters=dict(smoothness=.02,tolerance=85,sigma=45)))
   points=[drawing['items'][0][1]]+[item[2] for item in drawing['items']]
   for pt in points:truth.append(dict(series=name,x_pixel=x(pt.x),y_pixel=y(pt.y)))
  exclusions=[]
  for rect,names in regions:
   reg=dict(type='rectangle',bounds=[round(x(rect[0])),round(y(rect[1])),round(x(rect[2])),round(y(rect[3]))],verified=True,reason='Published event arrow; not an observation')
   if names:reg['series']=names
   exclusions.append(reg)
  if cid=='f01':
   exclusions=[]
   for name,points in [('Oukoop',[(352.1,323.1),(354,323.1),(354,331.1),(356.4,331.1),(353,339.4),(349.7,331.1),(352.1,331.1)]),('Stein',[(376.7,321),(378.7,321),(378.7,329),(381.1,329),(377.7,337.2),(374.3,329),(376.7,329)])]:
    exclusions.append(dict(type='polygon',points=[[round(x(a)),round(y(b))] for a,b in points],series=[name],verified=True,reason='Tight event-arrow outline; preserves nearby visible curve pixels'))
  config=dict(schema_version=1,image='input.png',image_sha256=sha256(folder/'input.png'),image_size=[pix.width,pix.height],reviewed=True,review_note='PDF ticks, series and event arrows visually reviewed; shared x axis for Fig. 10 a/b uses panel c. PDF paths are validation only.',kind='line',plot_bounds=b,axes=dict(x=dict(anchors=[[x(v),n] for v,n in xx]),y=dict(anchors=[[y(v),n] for v,n in yy])),series=series,exclusions=exclusions,source_doi='10.5194/bg-4-1027-2007',figure={'f01':'Fig. 10a','f02':'Fig. 10b','f03':'Fig. 10c','f04':'Fig. 11'}[cid],unit='mol CO2 m-2' if cid=='f04' else 'mmol CO2 m-2 d-1')
  save_json(folder/'config.json',config)
  with (folder/'reference.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=['series','x_pixel','y_pixel']);w.writeheader();w.writerows(truth)
  provenance=dict(doi=config['source_doi'],title='CO2 exchange and carbon balance in two grassland sites on eutrophic drained peat soils',authors='Veenendaal et al.',year=2007,pdf_page=page+1,pdf_sha256=sha256(paper),pdf_url='https://bg.copernicus.org/articles/4/1027/2007/bg-4-1027-2007.pdf',license='CC BY-NC-SA 2.5',license_url='https://creativecommons.org/licenses/by-nc-sa/2.5/',crop_pdf_points=crop,render_scale=scale,reference_kind='independent_pdf_vector_geometry',context_image='../context/veenendaal-figure10.png' if cid!='f04' else None,reference_path_indices=paths,reference_sha256=sha256(folder/'reference.csv'),variable=var,source_data_semantics='EC-derived published daily series includes gap filling; Reco and GEP are partitioned estimates, not independently measured fluxes.',x_semantics='Unwrapped Julian day: 2004 DOY, then 366 + 2005 DOY. Not a calendar timestamp.',station_admission='demonstration_only; no new station claim or Result/Output admission')
  save_json(folder/'provenance.json',provenance)
  manifest.append(dict(id=cid,title=zh,title_en=en,title_ja=ja,kind='line',group='flux',reference_kind=provenance['reference_kind'],ylim=ylim))
 # Fig. 5 is an embedded raster. It has no independent numerical reference.
 paper=a.papers/'45502235dd3c6bdc83b0/paper.pdf';assert sha256(paper)=='9cfdaa05aec227c4f0ef5b6a573e120518005cb05635deaff93ff2dbfe2bd1da', 'Unexpected Mayen PDF snapshot'
 doc=fitz.open(paper);raw=doc.extract_image(doc[11].get_images()[0][0]);import io
 image=Image.open(io.BytesIO(raw['image'])).convert('RGB')
 image.save(context/'mayen-figure5.png')
 ratio=image.width/1950
 for i,(season,zh,ja,crop0) in enumerate([('winter','冬季','冬季',[0,0,1034,616]),('spring','春季','春季',[1035,0,1950,616]),('summer','夏季','夏季',[0,624,1034,1280]),('fall','秋季','秋季',[1035,624,1950,1280])]):
  cid=f'f0{i+5}';folder=out/cid;folder.mkdir(exist_ok=True);crop=[round(v*ratio) for v in crop0];im=image.crop(crop);im.save(folder/'input.png')
  def x(v):return v*ratio-crop[0]
  def y(v):return v*ratio-crop[1]
  right=i%2==1;bottom=i>=2;left=1047 if right else 121;top=695 if bottom else 69
  x2=1155 if right else 230;x22=1845 if right else 919;y0=841 if bottom else 213;yneg8=1110 if bottom else 482
  bounds=[round(x(left)),round(y(top)),im.width-2,round(y(1234 if bottom else 606))]
  ex=[]
  if i==0:ex=[dict(type='rectangle',bounds=[round(x(764)),round(y(428)),round(x(1022)),round(y(604))],verified=True,reason='Four-series legend; preserves visible NEE above it')]
  config=dict(schema_version=1,image='input.png',image_sha256=sha256(folder/'input.png'),image_size=list(im.size),reviewed=True,review_note='Target is solid blue measured NEE only. Red NEEmarsh, green GPP and black Reco are estimates. Shared ticks calibrated from full Fig. 5.',kind='line',plot_bounds=bounds,axes=dict(x=dict(anchors=[[x(x2),2],[x(x22),22]]),y=dict(anchors=[[y(y0),0],[y(yneg8),-8]])),series=[dict(name='measured_NEE',color='#0000ff',parameters=dict(tolerance=80,sigma=45))],exclusions=ex,source_doi='10.5194/bg-21-993-2024',figure='Fig. 5'+chr(97+i),unit='umol CO2 m-2 s-1')
  save_json(folder/'config.json',config)
  provenance=dict(doi=config['source_doi'],title='Atmospheric CO2 exchanges measured by eddy covariance over a temperate salt marsh and influence of environmental controlling factors',authors='Mayen et al.',year=2024,pdf_page=12,pdf_sha256=sha256(paper),pdf_url='https://bg.copernicus.org/articles/21/993/2024/bg-21-993-2024.pdf',license='CC BY 4.0',license_url='https://creativecommons.org/licenses/by/4.0/',context_image='../context/mayen-figure5.png',embedded_figure_size=list(image.size),crop_image_pixels=crop,reference_kind='none',variable='NEE',source_data_semantics='Seasonal diurnal mean of measured eddy-covariance NEE, 2020. Blue shaded area is standard deviation; it is not extracted as data.',x_semantics='Hour of day, shared lower panels of Fig. 5.',station_admission='demonstration_only; no new station claim or Result/Output admission',accuracy_note='Authors provide raw data on request. No independent reference available; do not assign accuracy from pixel support or visual similarity.')
  save_json(folder/'provenance.json',provenance);manifest.append(dict(id=cid,title=f'盐沼实测 NEE · {zh}',title_en=f'Salt-marsh measured NEE · {season}',title_ja=f'塩性湿地の実測 NEE · {ja}',kind='line',group='flux',reference_kind='none',ylim=[-12,4]))
 save_json(out/'manifest.json',manifest)
 print('Prepared',len(manifest),'real-paper panels; vector references are separate.')
if __name__=='__main__':main()
