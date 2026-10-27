"""User-facing behavior: choices, factual isolation, validation and edit protection."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from promotional_brief import (build_detailed_brief, case_highlights, parse_highlights,
                               CATEGORIES, STYLES, PURPOSES, AUDIENCES)
from template_engine import load_attraction, generate_drafts, parse_drafts, export_result


def make_brief(**changes):
    data = load_attraction('杭州西湖')
    args = dict(name=data['name'], category='自然景观', style='简洁', purpose='种草推荐',
                audience='一般游客', highlights=case_highlights(data), selected=['苏堤', '白堤'],
                primary='苏堤', data=data)
    args.update(changes)
    return build_detailed_brief(**args)


def caption(**changes):
    return generate_drafts(make_brief(**changes))['versions'][0]['caption']


def test_style_changes_expression_without_changing_facts():
    copies = {s: generate_drafts(make_brief(style=s)) for s in STYLES}
    assert len({c['versions'][0]['caption'] for c in copies.values()}) == 3
    assert '先看苏堤' in copies['活泼']['versions'][0]['caption']
    assert '主要看点——苏堤' in copies['严肃']['versions'][0]['caption']
    assert len(copies['简洁']['versions'][0]['caption']) < len(copies['活泼']['versions'][0]['caption'])
    for c in copies.values():
        assert '苏堤是西湖堤岸之一' in c['versions'][0]['caption']
        assert c['versions'][0]['used_fact_ids'] == ['F01', 'F03', 'F04']


def test_purpose_changes_structure_and_requires_event_facts():
    assert '观察问题' in caption(purpose='宣传科普')
    assert '观察问题' not in caption(purpose='种草推荐')
    guide = caption(purpose='游玩攻略', duration='半天')
    assert '计划停留半天' in guide and '安排重点' in guide
    assert '经过核实的路线' in guide
    with pytest.raises(ValueError, match='活动名称'):
        make_brief(purpose='活动宣传')
    event = dict(name='测试活动', date='2026-11-01', location='测试集合点', participation='通过主办方报名')
    result = generate_drafts(make_brief(purpose='活动宣传', event=event))
    for v in result['versions']:
        assert all(value in v['caption'] for value in event.values())
        assert '苏堤' in v['title']
    # Hidden fields cannot leak into another purpose.
    assert make_brief(event=event, duration='半天')['event'] == {}
    assert make_brief(event=event, duration='半天')['visit_duration'] == '不限定'


def test_audience_changes_reader_task_not_facility_claims():
    texts = {a: caption(audience=a) for a in AUDIENCES}
    assert len(set(texts.values())) == len(AUDIENCES)
    assert '问孩子' in texts['亲子家庭']
    assert '各自选出' in texts['朋友结伴']
    assert '共同感兴趣' in texts['情侣']
    assert '一幅画' in caption(audience='学生／研学团体', stage='小学')
    assert '资料依据' in caption(audience='学生／研学团体', stage='高中')
    for text in texts.values():
        assert not any(x in text for x in ['儿童课程', '推车通道', '我上周去了', '免费门票', '研学导师'])


def test_only_selected_highlights_appear_and_primary_changes_title_and_order():
    text = caption(selected=['苏堤'], primary='苏堤')
    assert '白堤' not in text and '湖面山景：' not in text
    result = generate_drafts(make_brief(primary='白堤'))
    assert all('白堤' in v['title'] for v in result['versions'])
    assert result['versions'][0]['caption'].index('白堤：') < result['versions'][0]['caption'].index('苏堤：')
    assert result['versions'][0]['used_fact_ids'] == ['F01', 'F04', 'F03']
    with pytest.raises(ValueError, match='主重点'):
        make_brief(selected=['苏堤'], primary='白堤')
    with pytest.raises(ValueError, match='1至3'):
        make_brief(selected=[])


@pytest.mark.parametrize('category', CATEGORIES)
def test_custom_category_uses_only_user_facts_and_records_provenance(category):
    highlights = parse_highlights('主题展｜介绍本地植物。\n观察区｜展示三种叶片。')
    b = build_detailed_brief(name='测试场所', category=category, style='严肃', purpose='宣传科普',
        audience='学生／研学团体', highlights=highlights, selected=['主题展'], primary='主题展',
        introduction='这是用于测试的场所简介。', supplement='请携带纸笔。')
    result = generate_drafts(b)
    serialized = json.dumps(result, ensure_ascii=False)
    assert '介绍本地植物' in serialized and '请携带纸笔' in serialized
    assert all(x not in serialized for x in ['西湖', '西栅', '宋城', '展示三种叶片'])
    assert '未独立核验' in b['facts'][0]['source']
    assert parse_drafts(json.dumps(result), b)['versions'] == result['versions']
    export = export_result(dict(brief=b, copy=result, generated_at='test'), result['versions'])
    assert export['brief']['audience'] == '学生／研学团体'
    assert 'SUP' in result['versions'][0]['used_fact_ids']


def test_rejects_incomplete_or_inconsistent_inputs():
    with pytest.raises(ValueError, match='简介'):
        make_brief(data=None)
    with pytest.raises(ValueError, match='类型与资料卡不一致'):
        make_brief(category='博物馆')
    with pytest.raises(ValueError, match='名称｜具体说明'):
        parse_highlights('无说明')
    with pytest.raises(ValueError, match='不能重复'):
        parse_highlights('A｜说明\nA｜不同说明')
    with pytest.raises(ValueError, match='仅支持离线'):
        generate_drafts(make_brief(), mode='llm')


def app():
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'week2_app.py')).run()


def test_ui_choices_reach_copy_and_clear_pending_snapshot():
    a = app()
    a.button(key='generate_v2').click().run()
    original = a.text_area(key='caption_A').value
    a.selectbox(key='target_audience').select('亲子家庭').run()
    assert a.text_area(key='caption_A').value == original
    assert any('输入条件已改变' in i.value for i in a.info)
    a.button(key='generate_v2').click().run()
    assert '问孩子' in a.text_area(key='caption_A').value
    a.text_area(key='caption_A').set_value('手动改稿').run()
    a.selectbox(key='text_style').select('活泼').run()
    a.button(key='generate_v2').click().run()
    assert 'pending_brief' in a.session_state
    a.selectbox(key='copy_purpose').select('宣传科普').run()
    assert 'pending_brief' not in a.session_state
    assert a.text_area(key='caption_A').value == '手动改稿'
    a.button(key='generate_v2').click().run()
    a.button(key='replace_edits').click().run()
    assert '观察问题' in a.text_area(key='caption_A').value
    assert '先看' in a.text_area(key='caption_A').value
    assert not a.exception


def test_ui_custom_museum_event_validation_and_category_reset():
    a = app()
    a.selectbox(key='input_category').select('博物馆').run()
    assert not a.exception and a.button(key='generate_v2').disabled
    a.text_input(key='place').set_value('测试博物馆').run()
    a.text_area(key='custom_introduction').set_value('介绍本地植物的场所。').run()
    a.text_area(key='custom_highlights').set_value('叶片展｜展示三种叶片。').run()
    assert not a.button(key='generate_v2').disabled
    a.selectbox(key='copy_purpose').select('活动宣传').run()
    assert a.button(key='generate_v2').disabled
    for key, value in dict(name='植物日', date='周六上午', location='展厅', participation='预约').items():
        a.text_input(key='event_' + key).set_value(value).run()
    a.button(key='generate_v2').click().run()
    assert '植物日' in a.text_area(key='caption_A').value
    assert '用户提供活动信息' in json.dumps(a.session_state['week2_result'], ensure_ascii=False)
    a.selectbox(key='input_category').select('研学基地').run()
    assert a.text_area(key='custom_introduction').value == ''
    assert a.text_area(key='custom_highlights').value == ''
    assert a.button(key='generate_v2').disabled
    assert not a.exception
