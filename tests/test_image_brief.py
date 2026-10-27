"""Offline image planning: choice effects, provenance and state integration."""
import json
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from image_brief import build_image_brief, DEFAULTS, OPTIONS, VISUAL_STYLES
from promotional_brief import build_detailed_brief, case_highlights, CASE_CATEGORIES
ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def brief():
    d=json.loads((ROOT/'data/wuzhen_xizha.json').read_text()); h=case_highlights(d)
    return build_detailed_brief(name=d['name'],category=CASE_CATEGORIES[d['category']],style='简洁',purpose='种草推荐',audience='一般游客',highlights=h,selected=[x['label'] for x in h[:2]],primary=h[0]['label'],data=d)

@pytest.mark.parametrize('field',list(OPTIONS))
def test_each_choice_changes_a_concrete_instruction(brief,field):
    base=build_image_brief(brief,'本次文案',subject='水乡风景',reference={'size':[50,50]},portrait={'size':[50,50]})
    for value in OPTIONS[field]:
        if value==DEFAULTS[field]: continue
        actual=build_image_brief(brief,'本次文案',subject='水乡风景',selections={field:value},reference={'size':[50,50]},portrait={'size':[50,50]})
        assert OPTIONS[field][value][2] in actual['image_prompt']
        assert actual['image_prompt']!=base['image_prompt']
        assert actual['content']==base['content']

def test_style_changes_structure_not_facts(brief):
    plans=[build_image_brief(brief,'同一文案',sid,subject='水乡风景') for sid in VISUAL_STYLES]
    assert len({p['image_prompt'] for p in plans})==3
    assert all(p['content']==plans[0]['content'] for p in plans)
    assert all(p['references'] and p['status']=='prompt_only_not_generated' for p in plans)
    assert '三格内容顺序' in plans[2]['image_prompt']

def test_missing_assets_do_not_pretend_to_style(brief):
    with pytest.raises(ValueError,match='景区参考'):build_image_brief(brief,'',subject='水乡',selections={'mode':'reference'})
    with pytest.raises(ValueError,match='人物参考'):build_image_brief(brief,'',subject='水乡',selections={'people':'portrait'})
    with pytest.raises(ValueError):build_image_brief(brief,'','made-up',subject='水乡')
    with pytest.raises(ValueError):build_image_brief(brief,'',subject=' ')

def test_ui_state_translation_caption_edits_and_reference_gate(monkeypatch):
    import engine
    monkeypatch.setattr(engine,'generate_cloudflare_image',lambda *a,**k:pytest.fail('No image API allowed'))
    monkeypatch.setattr(engine,'generate_caption_variants',lambda *a,**k:pytest.fail('No text API allowed'))
    a=AppTest.from_file(str(ROOT/'app.py')).run()
    a.button(key='generate_caption').click().run();a.button(key='workflow_next').click().run()
    a.radio(key='image_template').set_value('heritage').run()
    a.selectbox(key='image_mood').select('warm').run()
    a.selectbox(key='image_ratio').select('1:1').run()
    p=a.session_state['result']['visual_brief']
    assert '水墨' in p['image_prompt'] and p['selections']['ratio']=='1:1'
    a.radio(key='language').set_value('中文').run()
    assert a.radio(key='image_template').value=='heritage'
    assert a.selectbox(key='image_ratio').value=='1:1'
    a.button(key='workflow_next').click().run()
    a.text_input(key='draft_0_title').set_value('新标题').run()
    assert any('文案已修改' in x.value for x in a.warning)
    a.button(key='workflow_back').click().run()
    assert '新标题' in a.session_state['result']['visual_brief']['image_prompt']
    a.checkbox(key='image_use_portrait').check().run()
    assert 'visual_brief' not in a.session_state['result']
    assert any('人物参考' in x.value for x in a.info)
    a.checkbox(key='image_use_portrait').uncheck().run()
    assert a.session_state['result']['visual_brief']['style_id']=='heritage'
    assert a.button(key='generate_image').disabled and not a.exception

def test_new_attraction_clears_old_photos_and_subject():
    from PIL import Image
    a=AppTest.from_file(str(ROOT/'app.py')).run()
    a.button(key='generate_caption').click().run();a.button(key='workflow_next').click().run()
    a.selectbox(key='image_subject_choice').select('custom').run()
    a.text_input(key='image_subject').set_value('乌镇的个人取景').run()
    a.session_state['result']['image']=Image.new('RGB',(5,5))
    a.button(key='workflow_back').click().run()
    a.selectbox(key='input_category').select('自然景观').run()
    a.button(key='generate_caption').click().run();a.button(key='workflow_next').click().run()
    assert a.session_state['result'].get('image') is None
    assert '乌镇' not in a.selectbox(key='image_subject_choice').value
    assert '乌镇' not in a.session_state['result']['visual_brief']['image_prompt']
    assert not a.exception


def test_simple_choices_map_to_instructions_and_photos(brief):
    from image_workspace import simple_selections, MOODS
    prompts=[]
    for mood in MOODS:
        selections=simple_selections('heritage',mood,'3:4')
        plan=build_image_brief(brief,'同一文案','heritage',subject='水乡风景',selections=selections)
        assert plan['selections']['treatment']=='ink'
        prompts.append(plan['image_prompt'])
    assert len(set(prompts))==len(MOODS)
    assert simple_selections('natural','auto','1:1',True)['mode']=='reference'
    assert simple_selections('natural','auto','1:1',False)['mode']=='concept'


def test_simple_ui_hides_technical_tools_and_ignores_legacy_options():
    from PIL import Image
    a=AppTest.from_file(str(ROOT/'app.py')).run()
    a.button(key='generate_caption').click().run()
    a.session_state['form_image_treatment']='cutout'
    a.session_state['form_image_light']='night'
    a.session_state['result']['image']=Image.new('RGB',(5,5))
    a.button(key='workflow_next').click().run()
    a.radio(key='image_template').set_value('heritage').run()
    p=a.session_state['result']['visual_brief']
    assert p['selections']['mode']=='reference'
    assert p['selections']['light']=='auto' and p['selections']['treatment']=='ink'
    assert not a.get('download_button')
    assert len(a.selectbox)==3  # subject, mood, shape; no expert settings
    a.selectbox(key='image_subject_choice').select('蓝印花布').run()
    assert a.session_state['result']['visual_brief']['subject']=='蓝印花布'
    a.button(key='remove_photo').click().run()
    assert a.session_state['result']['visual_brief']['selections']['mode']=='concept'
    assert not a.exception
