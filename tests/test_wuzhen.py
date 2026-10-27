import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from template_engine import build_brief, generate_drafts, parse_drafts, attach_image, export_result
from engine import CaptionError


def test_unknown_attraction_stops_and_keywords_select_facts():
    with pytest.raises(ValueError, match='没有资料卡'):
        build_brief('不存在的古镇', '免费')
    p = build_brief('乌镇·西栅', '老邮局、免费游船、文化')
    assert p['primary_fact_id'] == 'F04'
    assert p['unused_keywords'] == ['免费游船']
    c = generate_drafts(p)
    assert '免费游船' not in json.dumps(c, ensure_ascii=False)
    assert '老邮局' in c['versions'][0]['title']
    p2 = build_brief('乌镇西栅', '蓝印花布')
    assert p2['primary_fact_id'] == 'F03'
    assert generate_drafts(p2)['versions'][0]['caption'] != c['versions'][0]['caption']


def test_two_distinct_versions_and_valid_source_ids():
    p = build_brief('乌镇西栅', '水乡、蓝印花布')
    c = generate_drafts(p)
    assert parse_drafts(json.dumps(c), p)['versions'] == c['versions']
    c['versions'][1]['used_fact_ids'] = ['FAKE']
    with pytest.raises(CaptionError):
        parse_drafts(json.dumps(c), p)
    c = generate_drafts(p)
    c['versions'][1]['caption'] = c['versions'][0]['caption']
    with pytest.raises(CaptionError):
        parse_drafts(json.dumps(c), p)


def test_missing_llm_credentials_does_not_fall_back():
    with pytest.raises(CaptionError, match='尚未配置'):
        generate_drafts(build_brief('乌镇西栅', ''), 'llm', {})


def test_image_failure_and_retry_preserve_copy_and_provenance():
    p = build_brief('乌镇西栅', '慢游')
    result = dict(brief=p, copy=generate_drafts(p), generated_at='test')
    def fail(*args):
        raise RuntimeError('secret-must-not-be-exposed')
    failed = attach_image(result, 'alibaba_wan', {}, image_generator=fail)
    assert failed['copy'] == result['copy'] and failed['image_error']
    assert 'secret-must-not-be-exposed' not in failed['image_error']
    success = attach_image(failed, 'alibaba_wan', {}, image_generator=lambda *a: ('image', 'alibaba_wan', None))
    assert success['image_error'] is None and success['copy'] == result['copy']
    edited = [{**v, 'title': '人工修改'} for v in result['copy']['versions']]
    exported = export_result(failed, edited)
    assert exported['post']['versions'][0]['title'] == '人工修改'
    assert exported['source_copy']['versions'][0]['title'] != '人工修改'
    assert exported['image_status'] == 'failed'


def test_model_receives_facts_and_v2_prompt(monkeypatch):
    import types
    import openai
    p = build_brief('乌镇西栅', '文化')
    capture = {}
    def create(**kwargs):
        capture.update(kwargs)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=json.dumps(generate_drafts(p))))])
    monkeypatch.setattr(openai, 'OpenAI', lambda **kw: types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create))))
    c = generate_drafts(p, 'llm', {'TEXT_API_KEY':'test', 'TEXT_BASE_URL':'https://example.test/v1'})
    assert c['copy_source'] == 'llm_generated_requires_review'
    assert '正文只面向游客' in capture['messages'][0]['content']
    payload = json.loads(capture['messages'][1]['content'])
    assert payload['facts'][2]['id'] == 'F03' and payload['facts'][2]['source'].startswith('https:')


def test_simple_ui_preserves_edits_and_never_calls_api(monkeypatch):
    from streamlit.testing.v1 import AppTest
    import template_engine
    def forbidden(*a, **k):
        raise AssertionError('External API must not be called')
    monkeypatch.setattr(template_engine, 'generate_with_fallback', forbidden)
    original = template_engine.generate_drafts
    def offline_only(brief, mode='offline', **kw):
        assert mode == 'offline'
        return original(brief, mode)
    monkeypatch.setattr(template_engine, 'generate_drafts', offline_only)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'week2_app.py')).run()
    assert not app.exception
    assert app.selectbox(key='text_style').value == '简洁'
    assert app.selectbox(key='copy_purpose').value == '种草推荐'
    app.button(key='generate_v2').click().run()
    assert not app.exception
    app.text_input(key='title_A').set_value('保留这个修改').run()
    app.text_area(key='caption_A').set_value('手动编辑正文').run()
    app.text_input(key='tags_A').set_value('#我的标签').run()
    app.radio(key='active_version').set_value('B').run()
    assert app.text_input(key='title_B').value
    app.button(key='use_title_B_1').click().run()
    assert app.text_input(key='title_B').value == app.session_state['week2_result']['copy']['suggested_titles'][1]
    app.radio(key='active_version').set_value('A').run()
    assert app.text_input(key='title_A').value == '保留这个修改'
    assert app.text_area(key='caption_A').value == '手动编辑正文'
    assert app.text_input(key='tags_A').value == '#我的标签'
    app.session_state['focus_choices'] = ['老邮局']
    app.text_area(key='keywords').set_value('').run()
    app.button(key='generate_v2').click().run()
    assert app.session_state['pending_brief']['primary_fact_id'] == 'F04'
    assert app.text_input(key='title_A').value == '保留这个修改'
    app.button(key='keep_edits').click().run()
    assert 'pending_brief' not in app.session_state
    app.button(key='generate_v2').click().run()
    app.button(key='replace_edits').click().run()
    assert not app.exception
    assert '老邮局' in app.text_input(key='title_A').value
    app.selectbox(key='example').select('其他场所（填写资料）').run()
    app.text_input(key='place').set_value('未知').run()
    assert app.button(key='generate_v2').disabled


def test_wan_payload_uses_valid_pixel_area_without_live_request(monkeypatch):
    import types
    api = pytest.importorskip('dashscope.aigc.image_generation')
    import engine
    from PIL import Image
    from io import BytesIO
    buf = BytesIO()
    Image.new('RGB', (16, 16)).save(buf, format='PNG')
    captured = {}
    def fake_call(**kw):
        captured.update(kw)
        return types.SimpleNamespace(status_code=200, output=types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=[{'image':'https://example.test/image.png'}]))]))
    monkeypatch.setattr(api.ImageGeneration, 'call', fake_call)
    monkeypatch.setattr(engine.requests, 'get', lambda *a, **kw: types.SimpleNamespace(content=buf.getvalue(), raise_for_status=lambda: None))
    engine.generate_wan_image({'image_prompt':'test'}, 'test-key', 'https://example.test/api/v1')
    w, h = map(int, captured['size'].split('*'))
    assert 1280 * 1280 <= w * h <= 1440 * 1440
    assert captured['n'] == 1


@pytest.mark.parametrize('name,keywords,category,primary,absent', [
    ('西湖', '白堤、慢游、免费游船', '自然风光', 'F04', ['染坊','老邮局','千古情']),
    ('杭州宋城', '主题街区、建筑、免费门票', '主题乐园', 'F04', ['染坊','苏堤','白堤']),
])
def test_additional_cases_use_their_own_facts(name, keywords, category, primary, absent):
    brief = build_brief(name, keywords)
    assert brief['category'] == category and brief['primary_fact_id'] == primary
    copy = generate_drafts(brief)
    assert copy['copy_source'] == 'local_template_not_llm'
    assert len(copy['versions']) == 2
    assert copy['versions'][0]['caption'] != copy['versions'][1]['caption']
    text = json.dumps(copy, ensure_ascii=False)
    assert all(word not in text for word in absent)
    assert brief['unused_keywords'] and brief['unused_keywords'][0] not in text
    assert parse_drafts(json.dumps(copy), brief)['versions'] == copy['versions']
    assert brief['attraction'] in brief['image_prompt']
    assert export_result(dict(brief=brief, copy=copy, generated_at='test'), copy['versions'])['prompt_version'] == brief['prompt_version']
    assert (Path(__file__).resolve().parents[1] / 'prompts' / (brief['prompt_version'] + '.txt')).exists()


def test_switching_cases_keeps_edits_and_updates_topics_and_versions():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'week2_app.py')).run()
    app.button(key='generate_v2').click().run()
    app.text_input(key='title_A').set_value('保留西栅标题').run()
    for name, topic, category in [('杭州西湖', '苏堤', '自然景观'), ('杭州宋城', '宋城千古情', '主题乐园')]:
        app.radio(key='active_version').set_value('A').run()
        app.selectbox(key='input_category').select(category).run()
        app.selectbox(key='example').select(name).run()
        assert not app.exception
        assert app.selectbox(key='example').value == name
        assert not any(w.key == 'place' for w in app.text_input)
        assert topic in app.session_state['focus_choices']
        # Merely selecting another case never overwrites the previous result.
        old_title = app.text_input(key='title_A').value
        app.button(key='generate_v2').click().run()
        assert app.text_input(key='title_A').value == old_title
        app.button(key='replace_edits').click().run()
        assert not app.exception and name in app.text_input(key='title_A').value
        app.radio(key='active_version').set_value('B').run()
        assert '读者引导版' in str(app.radio(key='active_version').options)
        app.text_input(key='title_B').set_value('我的' + name + '版本').run()
        app.radio(key='active_version').set_value('A').run()
        app.radio(key='active_version').set_value('B').run()
        assert app.text_input(key='title_B').value == '我的' + name + '版本'
