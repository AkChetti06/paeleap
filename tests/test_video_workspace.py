"""Video tab state, explicit generation, failures and reusable slideshow cover."""
import pytest
from test_workspaces import studio, navigate


def test_empty_video_tab_never_calls_providers(studio):
    app, calls = studio
    navigate(app, 'video')
    assert app.radio(key='workspace').options == ['Caption', 'Image', 'Video']
    assert not any(x.key == 'generate_video' for x in app.button)
    assert any('Image tab' in x.value for x in app.info)
    assert not any(x.label in ('Short video', '短视频') for x in app.expander)
    app.radio(key='language').set_value('中文').run()
    assert not app.exception
    assert app.radio(key='workspace').options == ['文案', '图片', '视频']
    assert app.radio(key='workspace').value == 'video'
    assert any('图片' in x.value for x in app.info)
    assert calls == []


def test_video_reuses_cover_and_tabs_keep_edits(studio):
    app, calls = studio
    app.text_input(key='audience').set_value('Friends').run()
    app.text_input(key='keywords').set_value('Keep keywords').run()
    app.button(key='generate_caption').click().run()
    app.text_input(key='draft_0_title').set_value('Keep edited title').run()
    app.text_area(key='draft_0_caption').set_value('Keep edited caption').run()
    navigate(app, 'image')
    app.selectbox(key='visual_style_choice').select('cyberpunk_neon').run()
    app.button(key='generate_image').click().run()
    cover = app.session_state['result']['image']
    navigate(app, 'video')
    assert calls == ['text', 'image']
    assert len([x for x in app.button if x.key == 'generate_video']) == 1
    assert not any(x.label in ('Short video', '短视频') for x in app.expander)
    app.radio(key='language').set_value('中文').run()
    assert app.button(key='generate_video').label == '生成短视频'
    app.button(key='generate_video').click().run()
    assert not app.exception
    assert calls == ['text', 'image', 'image', 'image', 'video']
    result = app.session_state['result']
    assert result['image'] is cover
    assert result['video'] == b'video'
    assert app.get('video')
    assert len([x for x in app.get('download_button') if x.proto.label == '下载视频']) == 1
    assert not app.text_area  # Video is the relevant output, copy stays saved.
    app.radio(key='preview_ratio').set_value('1:1').run()
    assert app.get('video') and any('原始格式' in x.value for x in app.info)
    for workspace in ('text', 'image', 'video', 'text'):
        navigate(app, workspace)
    assert app.text_input(key='audience').value == 'Friends'
    assert app.text_input(key='keywords').value == 'Keep keywords'
    assert app.text_input(key='draft_0_title').value == 'Keep edited title'
    assert app.text_area(key='draft_0_caption').value == 'Keep edited caption'
    assert app.session_state['form_visual_style_choice'] == 'cyberpunk_neon'
    assert app.session_state['result']['video'] == b'video'
    assert not any(x.key == 'generate_video' for x in app.button)
    assert not app.get('video')
    assert calls == ['text', 'image', 'image', 'image', 'video']


@pytest.mark.parametrize('failure', ['image', 'render'])
def test_failed_video_generation_retains_success(studio, monkeypatch, failure):
    import engine
    app, calls = studio
    navigate(app, 'image')
    app.button(key='generate_image').click().run()
    navigate(app, 'video')
    app.button(key='generate_video').click().run()
    assert not app.exception
    before = app.session_state['result']['video']
    cover = app.session_state['result']['image']
    def fail(*args, **kwargs):
        raise engine.VideoError('private-provider-diagnostic')
    monkeypatch.setattr(engine, 'generate_cloudflare_image' if failure == 'image' else 'render_slideshow', fail)
    app.button(key='generate_video').click().run()
    assert not app.exception and len(app.error) == 1
    assert 'private-provider-diagnostic' not in app.error[0].value
    assert app.session_state['result']['video'] == before
    assert app.session_state['result']['image'] is cover
    assert app.get('video')


def test_uploaded_photo_keeps_existing_video_backend_boundary(studio):
    from PIL import Image
    app, calls = studio
    photo = Image.new('RGB', (20, 30))
    app.session_state['result'] = dict(image=photo, image_plan=dict(source='uploaded_photo'))
    navigate(app, 'video')
    assert app.button(key='generate_video').disabled
    assert any('Image tab' in x.value for x in app.info)
    assert app.session_state['result']['image'] is photo
    assert calls == []
