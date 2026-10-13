"""Guard the independent-score contract: gaps must reduce the denominator score."""
import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('validate_flux',Path(__file__).parents[1]/'scripts/validate_flux.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def test_vector_score_preserves_missing_samples():
 config={'plot_bounds':[0,0,400,100],'axes':{'x':{'anchors':[[0,0],[400,400]]},'y':{'anchors':[[0,100],[100,0]]}},'series':[{'name':'a'}]}
 reference=[{'series':'a','x_pixel':0,'y_pixel':50},{'series':'a','x_pixel':400,'y_pixel':50}]
 rows=[dict(series='a',x_pixel=x,y_pixel=50,y=50,status='observed') for x in range(401)]
 assert module.score_vectors(config,rows,reference)['accuracy_pct']==100
 result=module.score_vectors(config,rows[:201],reference)
 assert result['expected']==401
 assert result['matched']==201
 assert result['accuracy_pct']==pytest.approx(100*201/401)
 assert module.score_vectors(config,[],reference)['accuracy_pct']==0

def test_low_confidence_is_not_scored_as_valid():
 config={'plot_bounds':[0,0,400,100],'axes':{'x':{'anchors':[[0,0],[400,400]]},'y':{'anchors':[[0,100],[100,0]]}},'series':[{'name':'a'}]}
 reference=[{'series':'a','x_pixel':0,'y_pixel':50},{'series':'a','x_pixel':400,'y_pixel':50}]
 rows=[dict(series='a',x_pixel=x,y_pixel=50,y=50,status='low_confidence') for x in range(401)]
 assert module.score_vectors(config,rows,reference)['matched']==0
