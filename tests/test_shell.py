"""Phase 1 sidebar boundaries and durable Create state across section navigation."""
import pytest
from test_workspaces import studio, navigate


@pytest.mark.parametrize('section,title', [('projects','My Projects'), ('templates','Templates'), ('inspiration','Inspiration')])
def test_future_sections_are_honest_coming_soon_views(studio, section, title):
    app, calls = studio
    assert [x.label for x in app.sidebar.button] == ['Create', 'My Projects', 'Templates', 'Inspiration']
    app.text_input(key='keywords').set_value('Keep my brief').run()
    app.button(key='nav_' + section).click().run()
    assert not app.exception
    assert app.session_state['studio_section'] == section
    assert any('Coming Soon' in x.value for x in app.markdown)
    assert any(title in x.value for x in app.markdown)
    assert not any(x.key.startswith('generate_') for x in app.button)
    assert not app.get('file_uploader')
    app.button(key='back_to_create').click().run()
    assert not app.exception
    assert app.text_input(key='keywords').value == 'Keep my brief'
    assert calls == []


def test_navigation_and_language_keep_generated_outputs_and_edits(studio):
    app, calls = studio
    app.selectbox(key='destination').select('custom').run()
    app.text_input(key='attraction').set_value('Custom attraction').run()
    app.text_input(key='audience').set_value('My readers').run()
    app.text_input(key='creative_angle').set_value('Architecture').run()
    app.button(key='generate_caption').click().run()
    app.selectbox(key='caption_variant').select(1).run()
    app.text_input(key='draft_1_title').set_value('Edited title').run()
    app.text_area(key='draft_1_caption').set_value('Edited caption').run()
    app.text_area(key='draft_1_hashtags').set_value('#mine').run()
    navigate(app, 'image')
    app.selectbox(key='visual_style_choice').select('cyberpunk_neon').run()
    app.button(key='generate_image').click().run()
    image = app.session_state['result']['image']
    navigate(app, 'video')
    app.button(key='generate_video').click().run()
    app.selectbox(key='platform').select('douyin').run()
    app.radio(key='preview_ratio').set_value('1:1').run()
    saved_calls = list(calls)
    for section in ('projects','templates','inspiration'):
        app.button(key='nav_' + section).click().run()
        app.radio(key='language').set_value('中文').run()
        assert not app.exception
        assert [x.label for x in app.sidebar.button] == ['创作','我的项目','模板','灵感']
        assert any('即将推出' in x.value for x in app.markdown)
        app.button(key='nav_create').click().run()
        assert not app.exception
        assert app.radio(key='workspace').value == 'video'
        assert app.selectbox(key='platform').value == 'douyin'
        assert app.radio(key='preview_ratio').value == '1:1'
        assert app.session_state['result']['image'] is image
        assert app.session_state['result']['video'] == b'video'
    navigate(app, 'text')
    assert app.text_input(key='attraction').value == 'Custom attraction'
    assert app.text_input(key='audience').value == 'My readers'
    assert app.text_input(key='creative_angle').value == 'Architecture'
    assert app.selectbox(key='caption_variant').value == 1
    assert app.text_input(key='draft_1_title').value == 'Edited title'
    assert app.text_area(key='draft_1_caption').value == 'Edited caption'
    assert app.text_area(key='draft_1_hashtags').value == '#mine'
    assert calls == saved_calls


def test_phase_one_copy_and_brand(studio):
    app, _ = studio
    markup = '\n'.join(x.value for x in app.markdown if not x.value.startswith('<style>'))
    assert 'Create Travel Content' in markup
    assert 'Turn a destination into posts, images and videos for your selected platform.' in markup
    assert 'Choose what you want to create.' in '\n'.join(x.value for x in app.caption)
    assert 'Review and edit your content before exporting.' in '\n'.join(x.value for x in app.caption)
    sidebar = '\n'.join(x.value for x in app.sidebar.markdown)
    assert 'PAELEAP' in sidebar and 'STUDIO' in sidebar and '>p.</span>' in sidebar
