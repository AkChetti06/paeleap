"""Platform presets, library contracts and non-destructive export checks."""
import json
from io import BytesIO
import pytest
from PIL import Image, ImageDraw
from engine import plan, caption_prompt, generate_caption_variants, render_slideshow
from platform_config import PLATFORM_CONFIG, FORMATS, TEMPLATE_LIBRARY, export_image
from test_workspaces import studio, navigate


@pytest.mark.parametrize('platform', PLATFORM_CONFIG)
@pytest.mark.parametrize('category', TEMPLATE_LIBRARY)
@pytest.mark.parametrize('language', ['English', '中文'])
def test_platform_template_contract(platform, category, language):
    p = plan('Place', category, lang=language, platform=platform,
             audience='Families', highlights=['Lake', 'Trees'])
    assert p['template_library'] == TEMPLATE_LIBRARY[category]
    assert p['aspect_ratio'] == PLATFORM_CONFIG[platform]['ratio']
    assert p['image_highlight'] == 'Lake'
    assert p['highlights'] == ['Lake', 'Trees']
    assert p['platform_format'] in PLATFORM_CONFIG[platform]['content_format']
    assert platform in caption_prompt(language, platform)
    assert 'Never invent' in caption_prompt(language, platform)
    assert p['export_settings']['dimensions'] == FORMATS[p['aspect_ratio']]


@pytest.mark.parametrize('ratio', FORMATS)
def test_export_preserves_entire_composition_and_source(ratio):
    original = Image.new('RGB', (240, 120), 'blue')
    draw = ImageDraw.Draw(original)
    draw.rectangle((0, 0, 20, 119), fill='red')
    draw.rectangle((219, 0, 239, 119), fill='green')
    before = original.tobytes()
    exported = export_image(original, ratio)
    assert exported.size == FORMATS[ratio]
    assert original.size == (240, 120) and original.tobytes() == before
    # Both edge landmarks survive, and the 2:1 source stays 2:1 inside the canvas.
    width, height = FORMATS[ratio]
    assert exported.getpixel((0, height//2)) == (255, 0, 0)
    assert exported.getpixel((width-1, height//2)) == (0, 128, 0)
    assert exported.getpixel((width//2, height//2)) == (0, 0, 255)
    buffer = BytesIO()
    exported.save(buffer, 'PNG')
    assert Image.open(BytesIO(buffer.getvalue())).size == FORMATS[ratio]


def test_invalid_presets_and_highlights():
    for kwargs in [dict(platform='unknown'), dict(aspect_ratio='2:1'), dict(highlights=['a']*4+['b','c','d'])]:
        with pytest.raises(ValueError):
            plan('Place', **kwargs)
    with pytest.raises(ValueError):
        export_image(Image.new('RGB', (2, 2)), 'bad')


def test_alternative_titles_preserve_variants(monkeypatch):
    import engine
    calls = []
    def generate(*args):
        calls.append(1)
        return dict(title=f'Title {len(calls)}', caption=f'Caption {len(calls)}', hashtags=['#a','#b','#c','#d'])
    monkeypatch.setattr(engine, 'generate_copy', generate)
    variants = generate_caption_variants(plan('Place', highlights=['Lake']))
    assert len(variants) == 3
    for item in variants:
        assert len(item['alternative_titles']) == 2
        assert item['title'] not in item['alternative_titles']


def test_platform_language_switch_retains_edits_and_presets(studio):
    app, calls = studio
    app.button(key='generate_caption').click().run()
    navigate(app, 'image')
    app.button(key='generate_image').click().run()
    original = app.session_state['result']['image']
    navigate(app, 'text')
    app.text_input(key='draft_0_title').set_value('My edited title').run()
    app.text_area(key='draft_0_caption').set_value('My edited caption').run()
    for platform, ratio in [('douyin', '9:16'), ('weibo', '1:1'), ('xiaohongshu', '3:4')]:
        app.selectbox(key='platform').select(platform).run()
        assert app.session_state['active_ratio'] == ratio
        for language in ['中文', 'English']:
            app.radio(key='language').set_value(language).run()
            assert not app.exception
            assert app.selectbox(key='platform').value == platform
            assert app.radio(key='workspace').value == 'text'
            assert app.text_input(key='draft_0_title').value == 'My edited title'
            assert app.text_area(key='draft_0_caption').value == 'My edited caption'
            assert app.session_state['result']['image'] is original
        payload = next(x.proto for x in app.get('download_button') if x.proto.label == '↓  Download JSON')
        assert payload.url
        assert any(f'{FORMATS[ratio][0]} × {FORMATS[ratio][1]}' in x.value for x in app.caption)
    assert calls == ['text', 'image']
    app.radio(key='preview_ratio').set_value('1:1').run()
    app.selectbox(key='platform').select('douyin').run()
    app.selectbox(key='platform').select('xiaohongshu').run()
    assert app.session_state['active_ratio'] == '3:4'


def test_missing_highlights_retains_previous_result(studio):
    app, calls = studio
    app.button(key='generate_caption').click().run()
    previous = app.session_state['result']['variants']
    app.text_input(key='highlights').set_value('').run()
    app.button(key='generate_caption').click().run()
    assert app.error and app.session_state['result']['variants'] == previous
    assert calls == ['text']


def test_platform_slideshow_dimensions():
    import imageio_ffmpeg
    import tempfile
    from pathlib import Path
    frames = [Image.new('RGB', (40, 20), color) for color in ('red', 'blue')]
    video = render_slideshow(frames, 1, aspect_ratio='9:16')
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'video.mp4'
        path.write_bytes(video)
        reader = imageio_ffmpeg.read_frames(str(path))
        assert next(reader)['size'] == (1080, 1920)
        reader.close()
