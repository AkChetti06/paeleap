"""Independent generation and partial previews, with no live API requests."""
from pathlib import Path

import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest


@pytest.fixture
def studio(monkeypatch, tmp_path):
    import dotenv
    import engine
    import studio_state
    monkeypatch.setattr(dotenv, 'load_dotenv', lambda **kw: None)
    calls = []
    def captions(p, *args):
        calls.append('text')
        return [dict(title=f'{p["language"]} {i}', caption=f'Draft {len(calls)}', hashtags=['#travel']) for i in range(3)]
    def image(*args):
        calls.append('image')
        return Image.new('RGB', (16, 20), color=(len(calls), 0, 0))
    def video(*args):
        calls.append('video')
        return b'video'
    monkeypatch.setattr(engine, 'generate_caption_variants', captions)
    monkeypatch.setattr(engine, 'generate_cloudflare_image', image)
    monkeypatch.setattr(engine, 'render_slideshow', video)
    monkeypatch.setattr(engine, 'save_output', lambda *args: tmp_path)
    monkeypatch.setattr(studio_state, 'save_caption_output', lambda *args: tmp_path)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
    return app, calls


def navigate(app, workspace):
    app.radio(key='workspace').set_value(workspace).run()
    assert not app.exception


def test_independent_generations_and_preview_edits(studio):
    app, calls = studio
    assert app.radio(key='workspace').options == ['Caption', 'Image', 'Preview']
    assert not app.sidebar.radio
    assert not any(button.key in ('gallery_next', 'gallery_previous') for button in app.button)
    gallery = next(block.value for block in app.markdown if '<section class="tourism-gallery"' in block.value)
    assert gallery.count('<figure ') == 3
    app.text_input(key='keywords').set_value('Quiet afternoon').run()
    app.text_input(key='audience').set_value('Families').run()
    app.button(key='generate_caption').click().run()
    assert not app.exception and calls == ['text']
    assert not app.text_area
    assert not app.session_state['result'].get('image')
    original = app.session_state['result']['variants'][0].copy()
    app.selectbox(key='caption_variant').select(1).run()
    navigate(app, 'preview')
    assert app.text_input(key='draft_1_title').value == 'English 1'
    assert any('No image yet' in block.value for block in app.caption)
    app.text_input(key='draft_1_title').set_value('My title').run()
    app.text_area(key='draft_1_caption').set_value('My caption').run()
    app.text_area(key='draft_1_hashtags').set_value('#mine').run()
    navigate(app, 'text')
    assert not app.text_area
    assert app.session_state['result']['variants'][0] == original
    assert app.session_state['result']['variants'][1]['title'] == 'English 1'
    assert app.text_input(key='keywords').value == 'Quiet afternoon'
    navigate(app, 'image')
    assert not app.text_area
    app.selectbox(key='visual_style_choice').select('cyberpunk_neon').run()
    app.button(key='generate_image').click().run()
    assert not app.exception and calls == ['text', 'image']
    first_image = app.session_state['result']['image']
    navigate(app, 'preview')
    assert app.text_input(key='draft_1_title').value == 'My title'
    assert app.text_area(key='draft_1_caption').value == 'My caption'
    assert app.text_area(key='draft_1_hashtags').value == '#mine'
    assert any('<div class="post-masthead">' in block.value for block in app.markdown)
    navigate(app, 'image')
    app.button(key='generate_image').click().run()
    assert calls == ['text', 'image', 'image']
    assert app.session_state['result']['image'] is not first_image
    latest_image = app.session_state['result']['image']
    navigate(app, 'preview')
    assert app.text_input(key='draft_1_title').value == 'My title'
    navigate(app, 'text')
    app.radio(key='language').set_value('中文').run()
    assert app.radio(key='workspace').options == ['文案', '图片', '预览']
    app.button(key='generate_caption').click().run()
    assert calls == ['text', 'image', 'image', 'text']
    navigate(app, 'preview')
    assert app.text_input(key='draft_0_title').value == '中文 0'
    assert app.session_state['result']['image'] is latest_image
    for workspace in ('image', 'text', 'preview'):
        navigate(app, workspace)
    assert calls == ['text', 'image', 'image', 'text']
    assert app.session_state['form_visual_style_choice'] == 'cyberpunk_neon'


def test_image_first_and_failed_regeneration(studio, monkeypatch):
    import engine
    app, calls = studio
    navigate(app, 'preview')
    assert not app.text_area
    navigate(app, 'image')
    app.button(key='generate_image').click().run()
    assert not app.exception and calls == ['image']
    image = app.session_state['result']['image']
    navigate(app, 'preview')
    assert not app.text_input
    assert any('No caption yet' in block.value for block in app.caption)
    navigate(app, 'text')
    app.button(key='generate_caption').click().run()
    navigate(app, 'preview')
    app.text_input(key='draft_0_title').set_value('Retained edit').run()
    def fail(*args):
        raise engine.CaptionError('Text service unavailable')
    monkeypatch.setattr(engine, 'generate_caption_variants', fail)
    navigate(app, 'text')
    app.button(key='generate_caption').click().run()
    assert len(app.error) == 1
    navigate(app, 'preview')
    assert app.text_input(key='draft_0_title').value == 'Retained edit'
    assert app.session_state['result']['image'] is image
    def image_fail(*args):
        raise engine.ImageProviderError('Cloudflare', 'network', 'test')
    monkeypatch.setattr(engine, 'generate_cloudflare_image', image_fail)
    navigate(app, 'image')
    app.button(key='generate_image').click().run()
    assert len(app.error) == 1
    assert app.session_state['result']['image'] is image
    assert calls == ['image', 'text']


def test_open_legacy_result_keeps_edits_and_provenance(studio):
    import engine
    app, calls = studio
    legacy_plan = engine.plan('Original attraction')
    app.session_state['result'] = dict(plan=legacy_plan,
        variants=[dict(title='Original', caption='Generated', hashtags=['#original'])],
        image=Image.new('RGB', (16, 20)), video=None)
    app.session_state['form_draft_0_title'] = 'Existing edit'
    navigate(app, 'preview')
    assert app.text_input(key='draft_0_title').value == 'Existing edit'
    assert app.session_state['result']['text_plan'] == legacy_plan
    assert app.session_state['result']['image_plan'] == legacy_plan
    navigate(app, 'image')
    app.button(key='generate_image').click().run()
    navigate(app, 'preview')
    assert app.text_input(key='draft_0_title').value == 'Existing edit'
    assert app.session_state['result']['text_plan'] == legacy_plan
    assert calls == ['image']
