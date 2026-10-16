import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

from PIL import Image, ImageDraw

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.dl_solver import DeepLearningPipeline
from src.layout import DomCapture, ManualCapture
from src.retrieval import CourseIndex
from tray_app import image_signature
from deep_learning.promote import check


def diagram(color='black'):
    image=Image.new('RGB',(250,80),'white')
    ImageDraw.Draw(image).rectangle((35,20,210,60),outline=color,width=3)
    return image


def pipeline(response=None):
    model=MagicMock(); model.chat.return_value=response or {'answer':'B','source':0}
    index=CourseIndex({'lecture':{'full_text':'Deep learning gradients use the chain rule in backpropagation.'}})
    solver=SimpleNamespace(settings={'expected_options':2,'course':'deep_learning','top_k':1,'context_chars':1000},
        index=index,cache={},last_diagnostic={},last_inference_end=0,model=model,
        _thermal_gate=lambda:0,_ocr=lambda:SimpleNamespace(read=lambda _: ([],[])))
    return DeepLearningPipeline(solver),solver


def test_image_only_options_reach_local_model_with_drawn_labels():
    dl,solver=pipeline()
    regions=((0,0,250,80),(0,80,250,160),(0,160,250,240))
    prepared=dl.prepare(ManualCapture(regions,(diagram(),diagram('red'),diagram('blue'))))
    assert prepared['weak_layout']
    assert not prepared.get('error')
    result=dl.solve_prepared(prepared,'single')
    assert result['best_choice']=='B'
    messages,schema=solver.model.chat.call_args.args
    assert messages[1]['content'][1]['image_url']['url'].startswith('data:image/png;base64,')
    assert schema['properties']['answer']['enum']==['A','B','?']
    assert result['image_hash']==prepared['image_hash']


def test_empty_card_is_rejected_before_model_call():
    dl,solver=pipeline()
    blank=Image.new('RGB',(250,80),'white')
    ImageDraw.Draw(blank).rectangle((0,0,249,79),outline='black')
    prepared=dl.prepare(ManualCapture(((0,0,250,80),)*3,(diagram(),blank,diagram())))
    assert 'Vùng trống: A' in prepared['error']
    assert 'error' in dl.solve_prepared(prepared)
    solver.model.chat.assert_not_called()


def test_uniform_colored_image_option_is_not_treated_as_empty():
    dl,_=pipeline()
    prepared=dl.prepare(ManualCapture(((0,0,250,80),)*3,
        (diagram(),Image.new('RGB',(250,80),'red'),Image.new('RGB',(250,80),'blue'))))
    assert not prepared.get('error')


def test_dom_image_change_invalidates_signature_and_answer_cache():
    first=DomCapture(diagram('red'),())
    second=DomCapture(diagram('blue'),())
    assert image_signature(first)!=image_signature(second)
    dl,solver=pipeline()
    for image in (first,first,second): dl.solve_prepared(dl.prepare(image),'single')
    assert solver.model.chat.call_count==2


def test_dom_manual_code_keeps_bad_indentation_and_never_loads_ocr():
    dl,solver=pipeline()
    solver._ocr=MagicMock(side_effect=AssertionError('DOM must not initialize OCR'))
    canvas=Image.new('RGB',(250,240),'white')
    for y in (0,80,160): canvas.paste(diagram(),(0,y))
    sections=(('Choose valid Python training code',),
              ('for x in loader:\n    loss.backward()\noptimizer.step()',),
              ('for x in loader:\nloss.backward()\n    optimizer.step()',))
    prepared=dl.prepare(DomCapture(canvas,(),'',sections,((0,0,250,80),(0,80,250,160),(0,160,250,240))))
    assert prepared['structured'].options['A']==sections[1][0]
    assert prepared['structured'].options['B']==sections[2][0]
    solver._ocr.assert_not_called()


def test_invalid_model_answer_or_source_is_not_a_result():
    for response in ({'answer':'?','source':0},{'answer':'C','source':0},{'answer':'A','source':99}):
        dl,_=pipeline(response)
        assert 'error' in dl.solve('gradient?',{'A':'chain rule','B':'ignore loss'})


def test_code_retrieval_preserves_indentation():
    code='for batch in loader:\n    optimizer.zero_grad()\n    loss.backward()\noptimizer.step()'
    index=CourseIndex({'code.py':{'type':'code','full_text':code}})
    assert index.search('optimizer loss')[0]['text']==code


def test_dataset_splits_have_no_original_question_overlap():
    root=Path(__file__).resolve().parents[2]/'data/deep_learning'
    splits=[[json.loads(line) for line in (root/f'{name}.jsonl').read_text(encoding='utf-8').splitlines()]
            for name in ('train','validation','test')]
    assert all(len(rows)>=minimum for rows,minimum in zip(splits,(300,60,100)))
    groups=[{row['group_id'] for row in rows} for rows in splits]
    assert not (groups[0]&groups[1] or groups[0]&groups[2] or groups[1]&groups[2])
    for rows in splits:
        assert any(r['image'] for r in rows) and any(not r['image'] for r in rows)
        for row in rows:
            assert all(letter in row['options'] for letter in row['answer'].split(', '))


def reports():
    base={'complete':True,'limited':False,'actual_captures':False,'dataset_sha256':'same',
          'settings':{'model':'base','mmproj':'projector','threads':2},'model_sha256':'base',
          'metrics':{k:{'n':100,'accuracy':.9,'p95_seconds':4} for k in ('overall','code','visual')}}
    trained=json.loads(json.dumps(base)); trained['settings']['model']='trained'; trained['model_sha256']='trained'
    for v in trained['metrics'].values(): v['accuracy']=.95
    actual={'complete':True,'limited':False,'actual_captures':True,'model_sha256':'trained',
            'metrics':{'overall':{'n':3,'accuracy':1,'p95_seconds':4}}}
    return base,trained,actual


def test_promotion_requires_actual_captures_and_improvement():
    base,trained,actual=reports()
    assert check(base,trained,actual)==[]
    actual['metrics']['overall']['n']=0
    assert any('actual captures' in reason.lower() for reason in check(base,trained,actual))
    base,trained,actual=reports(); trained['metrics']['overall']['accuracy']=.9
    assert 'No overall improvement' in check(base,trained,actual)


def test_promotion_rejects_code_regression_or_slow_images():
    base,trained,actual=reports(); trained['metrics']['code']['accuracy']=.8
    trained['metrics']['visual']['p95_seconds']=6
    reasons=check(base,trained,actual)
    assert 'code regressed' in reasons and 'visual P95 exceeds 5 seconds' in reasons
