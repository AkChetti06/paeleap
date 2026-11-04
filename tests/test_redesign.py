"""The redesigned shared canvas retains the existing independent generation flow."""
from test_workspaces import studio, navigate


def test_live_canvas_shows_both_outputs_in_every_workspace(studio):
    app, calls = studio
    app.button(key='generate_caption').click().run()
    navigate(app, 'image')
    app.button(key='generate_image').click().run()
    navigate(app, 'text')
    app.text_input(key='draft_0_title').set_value('My reviewed title').run()
    app.text_area(key='draft_0_caption').set_value('My reviewed caption').run()
    app.text_area(key='draft_0_hashtags').set_value('#reviewed').run()
    for workspace in ('text', 'image'):
        navigate(app, workspace)
        assert app.text_input(key='draft_0_title').value == 'My reviewed title'
        assert app.text_area(key='draft_0_caption').value == 'My reviewed caption'
        assert app.text_area(key='draft_0_hashtags').value == '#reviewed'
        assert app.get('imgs')
        downloads = [x.proto.label for x in app.get('download_button')]
        assert '↓  Save caption' in downloads
        assert '↓  Download image' in downloads
        assert '↓  Download JSON' in downloads
    navigate(app, 'text')
    assert app.text_input(key='draft_0_title').value == 'My reviewed title'
    assert calls == ['text', 'image']


def test_preview_ratio_buttons_reset_on_platform_change(studio):
    app, calls = studio
    assert not app.get('popover')
    assert app.radio(key='preview_ratio').options == [
        '3:4 — 1080 × 1440', '9:16 — 1080 × 1920', '1:1 — 1080 × 1080']
    app.radio(key='preview_ratio').set_value('1:1').run()
    assert app.session_state['active_ratio'] == '1:1'
    app.selectbox(key='platform').select('douyin').run()
    assert app.radio(key='preview_ratio').value == '9:16'
    app.radio(key='preview_ratio').set_value('3:4').run()
    app.radio(key='language').set_value('中文').run()
    assert not app.exception
    assert app.radio(key='preview_ratio').value == '3:4'
    app.selectbox(key='platform').select('xiaohongshu').run()
    assert app.session_state['active_ratio'] == '3:4'
    app.radio(key='preview_ratio').set_value('1:1').run()
    navigate(app, 'image')
    navigate(app, 'text')
    assert app.radio(key='preview_ratio').value == '1:1'
    app.run()
    assert app.radio(key='preview_ratio').value == '1:1'
    assert calls == []


def test_inspiration_is_at_top_and_keeps_licenses(studio):
    app, _ = studio
    assert not any('Destination inspiration' in x.label for x in app.expander)
    markup = next(x.value for x in app.markdown if '<section class="tourism-gallery"' in x.value)
    assert markup.count('creativecommons.org/licenses/') == 3
    assert 'Wikimedia Commons' in markup and 'tabindex="0"' in markup
    blocks = [x.value for x in app.markdown]
    assert any('Create Travel Content' in x for x in blocks)
    assert not any('A place. A perspective.' in x for x in blocks)


def test_ratio_switch_updates_preview_and_download_without_generation(studio, monkeypatch):
    from io import BytesIO
    import json
    from PIL import Image
    import streamlit as st
    from platform_config import FORMATS
    app, calls = studio
    app.button(key='generate_caption').click().run()
    navigate(app, 'image')
    app.button(key='generate_image').click().run()
    navigate(app, 'text')
    app.text_input(key='draft_0_title').set_value('Keep my title').run()
    app.text_area(key='draft_0_caption').set_value('Keep my caption').run()
    app.text_area(key='draft_0_hashtags').set_value('#keep').run()
    source = app.session_state['result']['image']
    original_pixels = source.tobytes()
    source_variants = app.session_state['result']['variants']
    exports, previews = {}, []
    real_download, real_image = st.download_button, st.image

    def download(label, data, file_name=None, *args, **kwargs):
        if file_name:
            exports[file_name] = data
        return real_download(label, data, file_name, *args, **kwargs)

    def image(data, *args, **kwargs):
        previews.append(data.size)
        return real_image(data, *args, **kwargs)

    monkeypatch.setattr(st, 'download_button', download)
    monkeypatch.setattr(st, 'image', image)
    for ratio, dimensions in FORMATS.items():
        previews.clear()
        app.radio(key='preview_ratio').set_value(ratio).run()
        assert not app.exception
        assert app.session_state['active_ratio'] == ratio
        assert previews[0] == dimensions
        filename = f'paeleap_xiaohongshu_{ratio.replace(":", "x")}.png'
        assert Image.open(BytesIO(exports[filename])).size == dimensions
        exported = json.loads(exports['paeleap_post.json'])
        assert exported['export_settings']['aspect_ratio'] == ratio
        assert exported['export_settings']['dimensions'] == list(dimensions)
        assert exported['variants'][0]['title'] == 'Keep my title'
        assert exported['variants'][0]['caption'] == 'Keep my caption'
        assert exported['variants'][0]['hashtags'] == ['#keep']
        assert app.session_state['result']['image'] is source
        assert source.tobytes() == original_pixels
        assert app.session_state['result']['variants'] == source_variants
        for language in ('中文', 'English'):
            app.radio(key='language').set_value(language).run()
            assert not app.exception
            assert app.radio(key='preview_ratio').value == ratio
        assert calls == ['text', 'image']


def test_removed_preview_tab_migrates_open_sessions(studio):
    app, calls = studio
    app.button(key='generate_caption').click().run()
    app.text_input(key='draft_0_title').set_value('Existing session edit').run()
    app.session_state['durable_workspace'] = 'preview'
    app.run()
    assert not app.exception
    assert app.radio(key='workspace').options == ['Caption', 'Image', 'Video']
    assert app.radio(key='workspace').value == 'text'
    assert app.text_input(key='draft_0_title').value == 'Existing session edit'
    assert calls == ['text']


def test_visual_direction_only_in_image_and_survives_caption_edits(studio):
    app, calls = studio
    assert not any(x.key == 'visual_style_choice' for x in app.selectbox)
    navigate(app, 'image')
    assert len(app.selectbox(key='visual_style_choice').options) == 4
    app.selectbox(key='visual_style_choice').select('cyberpunk_neon').run()
    navigate(app, 'text')
    assert not any(x.key == 'visual_style_choice' for x in app.selectbox)
    app.radio(key='language').set_value('中文').run()
    app.button(key='generate_caption').click().run()
    assert not app.exception
    assert app.session_state['form_visual_style_choice'] == 'cyberpunk_neon'
    navigate(app, 'image')
    assert app.selectbox(key='visual_style_choice').value == 'cyberpunk_neon'
    assert calls == ['text']


def test_one_destination_field_and_custom_name(studio):
    app, calls = studio
    assert not any(x.key == 'attraction' for x in app.text_input)
    app.selectbox(key='destination').select('songcheng').run()
    assert app.session_state['form_attraction'] == 'Songcheng, Hangzhou'
    assert not any(x.key == 'attraction' for x in app.text_input)
    app.selectbox(key='destination').select('custom').run()
    app.text_input(key='attraction').set_value('My own attraction').run()
    app.radio(key='language').set_value('中文').run()
    navigate(app, 'image')
    navigate(app, 'video')
    navigate(app, 'text')
    assert not app.exception
    assert app.text_input(key='attraction').value == 'My own attraction'
    app.selectbox(key='destination').select('west_lake').run()
    assert not any(x.key == 'attraction' for x in app.text_input)
    assert app.session_state['form_attraction'] == '杭州西湖'
    assert calls == []


def test_previous_manually_edited_destination_is_preserved(studio):
    app, _ = studio
    app.session_state['form_attraction'] = 'Previously edited place'
    app.session_state['name_is_preset'] = False
    app.run()
    assert not app.exception
    assert app.selectbox(key='destination').value == 'custom'
    assert app.text_input(key='attraction').value == 'Previously edited place'
