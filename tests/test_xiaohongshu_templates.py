from PIL import Image
from streamlit.testing.v1 import AppTest
from template_engine import load_attraction, generate_drafts
from promotional_brief import build_detailed_brief, case_highlights, CASE_CATEGORIES
from xiaohongshu_templates import ordered_photos, photo_plan

def brief(name='乌镇西栅',primary=None,audience='一般游客'):
    d=load_attraction(name); h=case_highlights(d)
    return build_detailed_brief(name=d['name'],category=CASE_CATEGORIES[d['category']],style='简洁',purpose='种草推荐',audience=audience,highlights=h,selected=[x['label'] for x in h[:2]],primary=primary or h[0]['label'],data=d)

def test_all_three_templates_use_own_place_and_selected_facts():
    for name,tid in [('乌镇西栅','ancient_town'),('杭州西湖','nature'),('杭州宋城','theme_park')]:
        b=brief(name);r=generate_drafts(b)
        assert r['template_id']==tid
        assert len(r['versions'])==2
        assert '2个' in r['versions'][0]['title']
        for v in r['versions']:
            assert name in v['title']
            for h in b['highlights']:assert h['text'] in v['caption']
            assert '千岛湖' not in v['caption']
        assert [x['fact_id'] for x in r['content_outline']]==b['selected_fact_ids']

def test_primary_changes_title_paragraph_and_photo_order_without_duplication():
    b=brief(); photos=[dict(digest='b',fact_id='F03',name='cloth.png'),dict(digest='a',fact_id='F02',name='water.png')]
    assert [p['name'] for p in ordered_photos(b,photos)]==['water.png','cloth.png']
    b2=brief(primary='蓝印花布');r=generate_drafts(b2)
    assert '蓝印花布' in r['versions'][0]['title']
    assert r['versions'][0]['caption'].index('蓝印花布：')<r['versions'][0]['caption'].index('水乡风景：')
    assert photo_plan(b2,photos)[0]['name']=='cloth.png'
    assert len(ordered_photos(b,photos[:1]*3))==1
    assert ordered_photos(b,[dict(digest='x',fact_id='',name='unmatched.png')])==[]
    assert ordered_photos(b,[])==[]

def test_photo_state_survives_navigation_and_new_primary():
    a=AppTest.from_file('../app.py').run()
    a.button(key='generate_caption').click().run()
    a.session_state['result']['photos']=[dict(digest='a',fact_id='F02',name='water.png',image=Image.new('RGB',(8,8))),dict(digest='b',fact_id='F03',name='cloth.png',image=Image.new('RGB',(8,8)))]
    a.button(key='workflow_next').click().run()
    assert a.session_state['result']['template_id']=='ancient_town'
    assert a.radio(key='image_template').value=='heritage'
    a.button(key='workflow_next').click().run()
    assert a.selectbox(key='preview_photo').options==['1 / 2 · water.png','2 / 2 · cloth.png']
    a.button(key='workflow_back').click().run()
    assert len(a.session_state['result']['photos'])==2
    a.button(key='remove_photo').click().run()
    assert not a.session_state['result'].get('photos')
    assert not a.exception
