"""Safety/measurement contracts, independent of paid model availability."""
import base64
from io import BytesIO
import json
from pathlib import Path
import numpy as np
import pytest
from PIL import Image
from digitizer_core.ai_assist import prepare,registration,support_masks,write_grid
from digitizer_core.ai_provider import decode_image,edit
from digitizer_core.masks import sha256

ROOT=Path(__file__).parents[1]

def test_registration_uses_reviewed_landmarks_not_dimensions():
    points=[[0,0,32,32],[100,0,132,32],[0,100,32,132],[100,100,132,132]]
    review=dict(reviewed=True,review_note='Four visible plot corners checked.',source_sha256='s',generated_sha256='g',anchor_pairs=points)
    matrix,error=registration(review,'s','g',[0,0,100,100])
    assert np.allclose(matrix,[[1,0,-32],[0,1,-32]])
    assert error<1e-10
    with pytest.raises(ValueError,match='both exact images'):registration(review,'s','different',[0,0,100,100])
    review['anchor_pairs'][3][2]+=20
    with pytest.raises(ValueError,match='Inconsistent'):registration(review,'s','g',[0,0,100,100])


def test_ai_cannot_create_pixels_or_restore_masked_data():
    original=np.full((40,40,3),255,np.uint8);original[20,5:35]=[0,0,255]
    generated=np.full_like(original,255);generated[20,5:35]=[255,0,0];generated[10,5:35]=[255,0,0]
    cfg=dict(plot_bounds=[1,1,38,38],exclusions=[dict(bounds=[18,18,22,22],verified=True)])
    prior,accepted,unsupported,mask=support_masks(original,generated,cfg,dict(name='a',color='#0000ff'),np.array([[1,0,0],[0,1,0]],float))
    assert accepted.sum()==25
    assert not accepted[10].any() and not accepted[mask].any()
    assert unsupported[10].sum()==30
    assert np.all(np.all(original[accepted]==[0,0,255],axis=1))


def test_grid_does_not_bridge_missing_or_unauthorized_column(tmp_path):
    config=dict(kind='line',plot_bounds=[0,0,4,4],image_sha256='s',axes={'x':{'anchors':[[0,0],[4,4]]},'y':{'anchors':[[0,4],[4,0]]}})
    Image.new('RGB',(8,8),'white').save(tmp_path/'overlay.png')
    rows=[dict(x_pixel=x,x=x,y=2,status='visible') for x in [0,1,3,4]]
    rows[-1]['status']='low_confidence'
    result=write_grid(rows,config,tmp_path,5)
    assert result[2]['y'] is None and result[4]['y'] is None
    assert result[1]['y']==2


def test_decodes_both_wire_formats_and_rejects_non_image():
    f=BytesIO();Image.new('RGB',(2,3)).save(f,format='PNG');encoded=base64.b64encode(f.getvalue()).decode()
    assert decode_image({'data':[{'b64_json':encoded}]},'apiyi')==f.getvalue()
    assert decode_image({'candidates':[{'content':{'parts':[{'inlineData':{'data':encoded}}]}}]},'gemini')==f.getvalue()
    with pytest.raises(ValueError):decode_image({'data':[{'url':'https://invalid.test/image'}]},'apiyi')


def test_failed_paid_call_is_single_attempt_and_redacts_credentials(tmp_path,monkeypatch):
    bundle=tmp_path/'bundle'
    prepare(ROOT/'benchmarks/cases/r03/config.json','target','blue circular markers',bundle,'markers')
    monkeypatch.setenv('APIYI_API_KEY','private-test-secret')
    calls=[]
    class Response:
        status_code=503
        ok=False
    def post(*args,**kwargs):calls.append(args);return Response()
    import requests
    monkeypatch.setattr(requests,'post',post)
    with pytest.raises(ValueError):edit(bundle)
    assert len(calls)==1 and not (bundle/'generated.png').exists()
    metadata=(bundle/'request.json').read_text()
    assert 'private-test-secret' not in metadata
    assert json.loads(metadata)['http_status']==503
    with pytest.raises(ValueError,match='already has a request'):edit(bundle)
    assert len(calls)==1


def test_prepared_payload_is_hash_bound(tmp_path):
    bundle=tmp_path/'bundle'
    prepare(ROOT/'benchmarks/cases/r03/config.json','target','blue markers',bundle,'markers')
    (bundle/'prompt.txt').write_text('modified without re-preparing')
    with pytest.raises(ValueError,match='changed'):edit(bundle)


def test_ai_dot_cannot_turn_original_fit_into_scatter_point(tmp_path):
    from PIL import ImageDraw
    from digitizer_core.ai_assist import extract
    from digitizer_core.engine import save_json
    image=Image.new('RGB',(100,100),'white');draw=ImageDraw.Draw(image)
    draw.line([(10,80),(90,20)],fill='#0000ff',width=5);image.save(tmp_path/'source.png')
    config=dict(image='source.png',image_sha256=sha256(tmp_path/'source.png'),image_size=[100,100],reviewed=True,review_note='Synthetic isolated fit, no markers.',
        kind='scatter',plot_bounds=[5,5,95,95],axes={'x':{'anchors':[[5,0],[95,1]]},'y':{'anchors':[[5,1],[95,0]]}},exclusions=[],
        series=[dict(name='a',color='#0000ff',marker='isolated',parameters=dict(min_diameter=3,max_diameter=12))])
    save_json(tmp_path/'config.json',config);bundle=tmp_path/'edit';prepare(tmp_path/'config.json','a','blue dots',bundle,'markers')
    generated=Image.new('RGB',(100,100),'white');ImageDraw.Draw(generated).ellipse((44,44,56,56),fill='red');generated.save(bundle/'generated.png')
    review=dict(reviewed=True,review_note='Deliberately hallucinated dot over a fit; must reject.',source_sha256=config['image_sha256'],generated_sha256=sha256(bundle/'generated.png'),anchor_pairs=[[5,5,5,5],[95,5,95,5],[5,95,5,95],[95,95,95,95]])
    save_json(bundle/'review.json',review)
    rows,_=extract(bundle,bundle/'review.json',tmp_path/'out')
    assert rows==[]
