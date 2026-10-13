import json
import numpy as np
import pytest
from PIL import Image, ImageDraw
from digitizer_core.masks import sha256, read_config, region_mask
from digitizer_core.engine import run, hollow_points


def fixture(tmp_path, regions=()):
    image=Image.new('RGB',(240,160),'white');d=ImageDraw.Draw(image)
    d.line([(20,110),(220,110)],fill='#2468b4',width=4)
    d.line([(120,35),(195,35)],fill='#2468b4',width=8)
    path=tmp_path/'input.png';image.save(path)
    config=dict(image='input.png',image_sha256=sha256(path),image_size=[240,160],reviewed=True,review_note='Fixture calibration',
        kind='line',plot_bounds=[10,10,230,150],exclusions=list(regions),
        axes={'x':{'anchors':[[10,0],[230,100]]},'y':{'anchors':[[150,0],[10,100]]}},series=[dict(name='water',color='#2468b4')])
    cfg=tmp_path/'config.json';cfg.write_text(json.dumps(config));return cfg,path,config


def test_legend_mask_preserves_real_data_at_same_x(tmp_path):
    cfg,_,_=fixture(tmp_path,[dict(type='polygon',points=[[115,25],[201,25],[201,45],[115,45]],verified=True)])
    rows,_=run(cfg,tmp_path/'out')
    ys=[r['y_pixel'] for r in rows if 25<=r['x_pixel']<=215]
    assert all(y is not None and abs(y-110.5)<1 for y in ys)


def test_masked_data_remains_missing_and_original_is_unchanged(tmp_path):
    regions=[dict(bounds=[115,25,201,45],verified=True),dict(bounds=[98,95,104,125],verified=True)]
    cfg,path,c=fixture(tmp_path,regions);before=sha256(path)
    rows,_=run(cfg,tmp_path/'out')
    assert all(r['y'] is None for r in rows if 98<=r['x_pixel']<=104)
    assert sha256(path)==before


def test_same_size_edited_image_is_rejected(tmp_path):
    cfg,path,_=fixture(tmp_path);im=Image.open(path);im.putpixel((0,0),(0,0,0));im.save(path)
    with pytest.raises(ValueError,match='Image changed'):read_config(cfg)


def test_unreviewed_config_fails(tmp_path):
    cfg,_,c=fixture(tmp_path);c['reviewed']=False;cfg.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='Review axes'):read_config(cfg)


def test_no_corner_assumptions_and_series_scope():
    assert not region_mask((100,100),[]).any()
    regions=[dict(bounds=[1,1,20,20],verified=True,series=['water'])]
    assert region_mask((100,100),regions,'water')[10,10]
    assert not region_mask((100,100),regions,'heat').any()


@pytest.mark.parametrize('region',[
    dict(bounds=[-1,0,10,10],verified=True),dict(bounds=[0,0,10,10],verified=False),
    dict(type='polygon',points=[[1,1],[5,5],[9,9]],verified=True),
    dict(bounds=[0,0,3.5,8],verified=True)])
def test_invalid_masks_are_rejected(region):
    with pytest.raises(ValueError):region_mask((100,100),[region])


def test_hollow_markers_are_measured_without_filling_image():
    im=Image.new('RGB',(160,120),'white');d=ImageDraw.Draw(im)
    for x,y in [(30,30),(80,70),(130,35)]:d.ellipse((x-7,y-7,x+7,y+7),outline='#2468b4',width=2)
    rgb=np.asarray(im);copy=rgb.copy()
    points=hollow_points(rgb,np.zeros((120,160),bool),(1,1,158,118),'#2468b4',36)
    assert len(points)==3 and np.array_equal(rgb,copy)
    assert sorted(round(p['x_pixel']) for p in points)==[30,80,130]


def test_scatter_bitmap_is_used_by_primary_and_residual_passes(tmp_path):
    from digitizer_core._thu.candidate_digitize_scatter import extract_scatter_points
    im=Image.new('RGB',(180,140),'white');d=ImageDraw.Draw(im)
    for x,y in [(35,90),(135,35)]:d.ellipse((x-6,y-6,x+6,y+6),fill='#2468b4')
    path=tmp_path/'scatter.png';im.save(path)
    mask=region_mask(im.size,[dict(type='polygon',points=[[120,20],[150,20],[150,50],[120,50]],verified=True)])
    report=extract_scatter_points(path,plot_bounds=(5,5,175,135),x_anchors=[(5,0),(175,100)],y_anchors=[(135,0),(5,100)],marker_mode='color',marker_color='#2468b4',exclusion_bitmap=mask)
    assert len(report['points'])==1 and report['numeric_output_authorized']
    assert report['points'][0]['pixel_x']==pytest.approx(35,abs=.5)


def test_bar_geometry_and_source_bytes_survive_export(tmp_path):
    cfg,path,c=fixture(tmp_path)
    im=Image.new('RGB',(240,160),'white');d=ImageDraw.Draw(im)
    d.rectangle((50,50,90,129),fill='#2468b4');im.save(path)
    c.update(image_sha256=sha256(path),kind='bar',bar=dict(plot_bounds=[10,10,230,130],value_axis=[130,0,30,100],
        orientation='vertical',layout='grouped',series_colors={'water':'#2468b4'},categories=[['A',70]]))
    cfg.write_text(json.dumps(c));rows,_=run(cfg,tmp_path/'out')
    assert rows[0]['y']==pytest.approx(80,abs=1)
    assert rows[0]['bar_top_pixel']==50 and rows[0]['bar_bottom_pixel']==130
    assert sha256(tmp_path/'out'/rows[0]['source_file'])==rows[0]['source_sha256']
