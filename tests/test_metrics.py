import importlib.util
from pathlib import Path
import numpy as np

spec=importlib.util.spec_from_file_location('benchmark',Path(__file__).parents[1]/'scripts/benchmark.py')
benchmark=importlib.util.module_from_spec(spec);spec.loader.exec_module(benchmark)


def test_scatter_extra_and_missing_points_are_penalized():
    case=dict(kind='scatter',xlim=[0,100],ylim=[0,100])
    truth=np.array([[20,20],[80,80]])
    rows=[dict(x=20,y=20,status='visible'),dict(x=50,y=50,status='visible')]
    result=benchmark.score(case,rows,truth)
    assert result['accuracy_pct']==50 and result['precision_pct']==50 and result['recall_pct']==50


def test_empty_extraction_cannot_get_perfect_accuracy():
    case=dict(kind='scatter',xlim=[0,100],ylim=[0,100])
    assert benchmark.score(case,[],np.array([[20,20]]))['accuracy_pct']==0


def test_line_missing_points_count_against_denominator():
    case=dict(kind='line',xlim=[0,100],ylim=[0,100],bounds=[0,0,400,400])
    rows=[dict(x=50,y=50,x_pixel=200,status='observed')]
    result=benchmark.score(case,rows,np.array([[0,50],[100,50]]))
    assert result['accuracy_pct']<1 and result['expected']==401
