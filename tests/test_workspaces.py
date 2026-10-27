"""Combined offline flow, durable inputs and protection of edited previews."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

@pytest.fixture
def studio(monkeypatch):
    import engine
    def forbidden(*args, **kwargs):
        pytest.fail('Offline studio attempted a model API call')
    for name in ('generate_caption_variants', 'generate_cloudflare_image', 'render_slideshow'):
        monkeypatch.setattr(engine, name, forbidden)
    return AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()

def navigate(a, workspace):
    a.radio(key='workspace').set_value(workspace).run()
    assert not a.exception

def test_offline_generation_navigation_and_input_persistence(studio):
    a=studio
    assert a.radio(key='workspace').options == ['Caption','Image','Preview']
    assert not a.sidebar.radio
    a.selectbox(key='text_style').select('活泼').run()
    a.selectbox(key='target_audience').select('亲子家庭').run()
    a.button(key='generate_caption').click().run()
    v=a.session_state['result']['variants'][0]
    assert '问孩子' in v['caption'] and '先看' in v['caption']
    navigate(a,'image')
    assert a.button(key='generate_image').disabled
    navigate(a,'preview')
    assert a.text_area(key='draft_0_caption').value == v['caption']
    navigate(a,'text')
    assert a.selectbox(key='text_style').value == '活泼'
    assert a.selectbox(key='target_audience').value == '亲子家庭'
    a.radio(key='language').set_value('中文').run()
    assert a.radio(key='workspace').options == ['文案','图片','预览']
    assert a.selectbox(key='text_style').value == '活泼'

def test_preview_edits_survive_and_regeneration_requires_explicit_replace(studio):
    a=studio
    a.button(key='generate_caption').click().run()
    navigate(a,'preview')
    a.text_area(key='draft_0_caption').set_value('我的手动修改').run()
    navigate(a,'text')
    a.selectbox(key='copy_purpose').select('宣传科普').run()
    a.button(key='generate_caption').click().run()
    assert 'pending_offline_brief' in a.session_state
    a.button(key='keep_offline_edits').click().run()
    navigate(a,'preview')
    assert a.text_area(key='draft_0_caption').value == '我的手动修改'
    navigate(a,'text')
    a.button(key='generate_caption').click().run()
    a.selectbox(key='primary_focus').select('蓝印花布').run()
    assert 'pending_offline_brief' not in a.session_state
    a.button(key='generate_caption').click().run()
    a.button(key='replace_offline_edits').click().run()
    navigate(a,'preview')
    assert '观察问题' in a.text_area(key='draft_0_caption').value
    assert '蓝印花布' in a.text_input(key='draft_0_title').value

def test_custom_input_validation_and_workspace_preservation(studio):
    a=studio
    a.selectbox(key='input_category').select('博物馆').run()
    assert a.button(key='generate_caption').disabled
    a.text_input(key='place').set_value('测试博物馆').run()
    a.text_area(key='custom_introduction').set_value('本地植物展示。').run()
    a.text_area(key='custom_highlights').set_value('叶片展｜展示三种叶片。').run()
    navigate(a,'preview');navigate(a,'image');navigate(a,'text')
    assert a.text_input(key='place').value == '测试博物馆'
    a.button(key='generate_caption').click().run()
    v=a.session_state['result']['variants'][0]
    assert '展示三种叶片' in v['caption'] and '乌镇' not in v['caption']

def test_existing_credentials_do_not_enable_api_and_language_keeps_edits(studio):
    a=studio
    a.secrets.update(dict(TEXT_API_KEY='test-secret', CLOUDFLARE_API_TOKEN='test-secret'))
    a.button(key='generate_caption').click().run()
    navigate(a,'preview')
    a.text_input(key='draft_0_title').set_value('保留我的标题').run()
    for lang in ['中文','English']:
        a.radio(key='language').set_value(lang).run()
        assert a.text_input(key='draft_0_title').value == '保留我的标题'
        assert not a.exception
    assert 'test-secret' not in str(a.session_state['result'])
    navigate(a,'image')
    assert a.button(key='generate_image').disabled


def test_generation_failure_keeps_existing_preview(studio, monkeypatch):
    import offline_studio
    a=studio
    a.button(key='generate_caption').click().run()
    original=a.session_state['result']['variants']
    # Adapter builds output before replacing the saved result.
    def fail(*args, **kwargs):
        raise ValueError('local failure')
    monkeypatch.setattr(offline_studio,'generate_drafts',fail)
    a.button(key='generate_caption').click().run()
    assert a.session_state['result']['variants'] == original
    assert len(a.error)==1 and not a.exception

def test_next_back_workflow_requires_caption_and_keeps_preview(studio):
    a=studio
    assert a.button(key='workflow_next').disabled
    a.button(key='generate_caption').click().run()
    a.button(key='workflow_next').click().run()
    assert a.radio(key='workspace').value == 'image'
    assert a.button(key='generate_image').disabled
    a.button(key='workflow_next').click().run()
    assert a.radio(key='workspace').value == 'preview'
    assert '乌镇' in a.text_input(key='draft_0_title').value
    a.text_input(key='draft_0_title').set_value('我的最终标题').run()
    a.button(key='workflow_back').click().run()
    a.button(key='workflow_back').click().run()
    assert a.radio(key='workspace').value == 'text'
    a.button(key='workflow_next').click().run()
    a.button(key='workflow_next').click().run()
    assert a.text_input(key='draft_0_title').value == '我的最终标题'

def test_language_switch_translates_controls_and_preserves_choices(studio):
    a=studio
    assert a.selectbox(key='text_style').label == 'Writing tone'
    assert a.selectbox(key='text_style').options == ['Concise','Lively','Formal']
    a.selectbox(key='target_audience').select('亲子家庭').run()
    a.selectbox(key='text_style').select('活泼').run()
    for lang in ['中文', 'English', '中文']:
        a.radio(key='language').set_value(lang).run()
        assert a.radio(key='workspace').value == 'text'
        assert a.selectbox(key='target_audience').value == '亲子家庭'
        assert a.selectbox(key='text_style').value == '活泼'
        assert a.selectbox(key='text_style').label == ('文本风格' if lang=='中文' else 'Writing tone')
        assert not a.exception
    a.button(key='generate_caption').click().run()
    a.button(key='workflow_next').click().run()
    a.radio(key='language').set_value('English').run()
    assert a.radio(key='workspace').value == 'image'
    a.button(key='workflow_next').click().run()
    assert a.radio(key='workspace').value == 'preview'


def test_local_photo_validation():
    from io import BytesIO
    from PIL import Image
    from local_photo import decode_photo
    buffer=BytesIO()
    Image.new('RGB',(80,60),'#879384').save(buffer,format='PNG')
    assert decode_photo(buffer.getvalue()).size == (80,60)
    with pytest.raises(ValueError,match='Invalid photo'):
        decode_photo(b'not an image')
    with pytest.raises(ValueError,match='20 MB'):
        decode_photo(b'x'*(20*1024*1024+1))

def test_remove_photo_clears_preview_and_allows_replacement(studio):
    from PIL import Image
    a=studio
    a.button(key='generate_caption').click().run()
    result=a.session_state['result']
    result.update(image=Image.new('RGB',(10,10)), image_source='local_upload', image_plan={})
    a.session_state['result']=result
    a.session_state['photo_digest']='old'
    navigate(a,'image')
    a.button(key='remove_photo').click().run()
    assert a.session_state['result'].get('image') is None
    assert 'photo_digest' not in a.session_state
    assert a.session_state['photo_epoch']==1
    navigate(a,'preview')
    assert not a.exception
