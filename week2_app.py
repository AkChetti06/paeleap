"""Beginner-friendly local preview. This entry point never calls an external API."""
import json
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st
from engine import safe_error
from ui_banner import render_banner
from template_engine import build_brief, generate_drafts, export_result, list_attractions, load_attraction

ROOT = Path(__file__).resolve().parent
CASES = {case['name']: case for case in list_attractions()}


def choose_example():
    data = CASES[st.session_state['example']]
    st.session_state['place'] = data['name']
    st.session_state['focus_choices'] = data['default_choices']
    st.session_state['keywords'] = ''
    st.session_state['topic_case'] = data['name']
    st.session_state.pop('pending_brief', None)


def edited_versions(result):
    return [{**v, 'title': st.session_state.get('title_' + v['id'], v['title']),
             'caption': st.session_state.get('caption_' + v['id'], v['caption']),
             'hashtags': st.session_state.get('tags_' + v['id'], ' '.join(result['copy']['hashtags'])).split()}
            for v in result['copy']['versions']]


def has_edits(result):
    original = result['copy']
    return any(v['title'] != source['title'] or v['caption'] != source['caption'] or v['hashtags'] != original['hashtags']
               for v, source in zip(edited_versions(result), original['versions']))


def create_preview(brief):
    copy = generate_drafts(brief, mode='offline')
    st.session_state['week2_result'] = {'brief': brief, 'copy': copy, 'image': None,
                                      'image_backend': None, 'image_error': None,
                                      'generated_at': datetime.now(timezone.utc).isoformat()}
    for v in copy['versions']:
        st.session_state['title_' + v['id']] = v['title']
        st.session_state['caption_' + v['id']] = v['caption']
        st.session_state['tags_' + v['id']] = ' '.join(copy['hashtags'])
    st.session_state['active_version'] = 'A'
    st.session_state.pop('pending_brief', None)


def use_title(vid, title):
    st.session_state['title_' + vid] = title


def cancel_regeneration():
    st.session_state.pop('pending_brief', None)


st.set_page_config(page_title='PAELEAP | 景区推广内容', page_icon='✦', layout='wide')
st.markdown('<style>' + (ROOT / 'studio.css').read_text(encoding='utf-8') + '\n' + (ROOT / 'week2.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)
st.markdown('<div class="brand"><span>＊</span> PAELEAP STUDIO</div>', unsafe_allow_html=True)
hero = render_banner({'eyebrow': '', 'headline': '轻松写好景区推广文案',
                      'subhead': '填写景区名称，选几个想介绍的重点，再挑一版喜欢的文案。'}, '中文')
hero = hero.replace('<div class="hero-label"></div>', '').replace(
    '<div class="hero-title">轻松写好景区推广文案</div>', '<h1 class="hero-title"><span>轻松写好</span><span>景区推广文案</span></h1>')
st.markdown(hero, unsafe_allow_html=True)
st.caption('可体验古镇、自然风光、主题乐园三类文案预览；图片功能尚未连接。')
# Detach saved editor values from widget cleanup when the other version is shown.
if 'week2_result' in st.session_state:
    for saved in st.session_state['week2_result']['copy']['versions']:
        for field in ('title_', 'caption_', 'tags_'):
            key = field + saved['id']
            if key in st.session_state:
                st.session_state[key] = st.session_state[key]
left, right = st.columns([0.84, 1.16], gap='large')
with left:
    st.markdown('<div class="heading-box"><h2 class="panel-title">1. 告诉我们你想介绍什么</h2></div>', unsafe_allow_html=True)
    with st.container(border=True, key='simple_brief'):
        st.selectbox('选择一个示例景点', list(CASES), format_func=lambda name: name + ' · ' + CASES[name]['category'],
                     key='example', on_change=choose_example)
        st.session_state.setdefault('place', '乌镇西栅')
        name = st.text_input('你想推广哪里？', key='place', placeholder='例如：乌镇西栅')
        try:
            data = load_attraction(name)
        except ValueError:
            data = CASES[st.session_state['example']]
        if st.session_state.get('topic_case') != data['name']:
            st.session_state['focus_choices'] = data['default_choices']
            st.session_state['topic_case'] = data['name']
        chosen = st.pills('这次想重点介绍什么？', list(data['ui_choices']), selection_mode='multi', key='focus_choices')
        st.caption('可以多选，也可以直接使用默认内容。')
        extra = st.text_input('还有其他重点吗？（选填）', key='keywords', placeholder='例如：建筑、纹样')
        keywords = '、'.join([data['ui_choices'][x] for x in chosen if x in data['ui_choices']] + ([extra.strip()] if extra.strip() else []))
        brief = None
        try:
            brief = build_brief(name, keywords)
        except ValueError:
            st.warning('暂时还没有这个景点的资料，请选择上方三个示例之一。')
        if brief:
            st.caption('✓ 已为你匹配' + brief['category'] + '风格')
            if brief['unused_keywords']:
                st.warning('这些内容暂时缺少资料，预览中不会加入：' + '、'.join(brief['unused_keywords']))
        result = st.session_state.get('week2_result')
        preview = st.button('预览两版文案' if not result else '重新预览两版文案', type='primary',
                            disabled=brief is None, key='generate_v2', use_container_width=True)
        st.caption('这是离线演示，文案来自预设内容，不调用 AI 接口。')
        if preview:
            if result and has_edits(result):
                st.session_state['pending_brief'] = brief
            else:
                try:
                    create_preview(brief)
                except Exception as exc:
                    st.error(safe_error(exc))
        pending = st.session_state.get('pending_brief')
        if pending:
            st.warning('你修改过文案。重新预览会替换两版内容，建议先保存喜欢的版本。')
            keep, replace = st.columns(2)
            keep.button('保留我的修改', on_click=cancel_regeneration, key='keep_edits', use_container_width=True)
            replace.button('替换并重新预览', on_click=create_preview, args=(pending,), key='replace_edits', use_container_width=True)
    if brief:
        with st.expander('查看景点资料来源'):
            st.caption('资料整理于 ' + brief['reviewed_on'] + '；价格、开放时间等信息请另查最新公告。')
            for fact in brief['facts']:
                st.markdown(f"{fact['text']} [查看来源]({fact['source']})")

with right:
    result = st.session_state.get('week2_result')
    st.markdown('<div class="heading-box"><h2 class="panel-title">2. 选择、修改并保存</h2></div>', unsafe_allow_html=True)
    if not result:
        st.markdown('<div class="simple-empty"><span>✧</span><strong>你的下一篇推广文案，从这里开始</strong><p>选好左侧的介绍重点，点击「预览两版文案」。</p><small>轻松分享版 · 适合自然推荐<br>另一种角度 · 根据景点类型展示具体看点</small></div>', unsafe_allow_html=True)
    else:
        stale = brief is None or brief != result['brief']
        if stale:
            st.info('介绍重点已改变。右侧仍保留之前的文案，点击左侧“重新预览”即可更新。')
        st.caption('这篇文案介绍：' + result['brief']['attraction'] + ' · 演示内容，可直接修改')
        vid = st.radio('选择文案风格', ['A', 'B'], format_func=lambda x: result['brief']['version_labels'][x],
                       horizontal=True, key='active_version', label_visibility='collapsed')
        st.caption(result['brief']['version_descriptions'][vid])
        with st.container(border=True, key='simple_post'):
            st.caption('小红书 · 文案预览')
            st.text_input('标题', key='title_' + vid)
            with st.expander('换个标题试试'):
                st.caption('点击一个标题即可应用，正文会保留。')
                for i, title in enumerate(result['copy']['suggested_titles']):
                    st.button(title, key=f'use_title_{vid}_{i}', on_click=use_title, args=(vid, title), use_container_width=True)
            st.text_area('正文', key='caption_' + vid, height=330)
            st.text_input('话题标签', key='tags_' + vid)
            st.caption('可以直接修改，发布前请确认内容符合实际。')
        edited = edited_versions(result)
        selected = next(v for v in edited if v['id'] == vid)
        text = selected['title'] + '\n\n' + selected['caption'] + '\n\n' + ' '.join(selected['hashtags'])
        st.download_button('保存这篇文案', text, {'古镇':'wuzhen','自然风光':'west_lake','主题乐园':'songcheng'}[result['brief']['category']] + '_' + vid + '.txt', mime='text/plain',
                           type='primary', key='save_selected', use_container_width=True)
        st.caption('保存当前的' + result['brief']['version_labels'][vid] + '，包含你的修改；不会自动发布。')
        with st.expander('配图 · 尚未连接'):
            st.write('图片功能接通后，将根据同一组景点信息和介绍重点生成配图。现在可以先修改并保存文案。')
        with st.expander('内容检查提示'):
            unused = result['brief']['unused_keywords']
            if unused:
                st.write('本次未加入：' + '、'.join(unused) + '，因为景点资料尚未支持。')
            st.write('请检查景点名称和具体描述。补充票价、活动或营业服务时，需要核对最新官方信息。')

with st.expander('开发记录（项目汇报用）'):
    st.caption('已接通乌镇西栅、杭州西湖、杭州宋城三个预设文案案例；不是任意景点的AI生成。图片、视频和接口调用尚未接入。')
    if result:
        export = export_result(result, edited_versions(result))
        export['post']['hashtags_by_version'] = {v['id']: v['hashtags'] for v in edited_versions(result)}
        export['selected_version'] = st.session_state.get('active_version', 'A')
        st.download_button('下载过程记录 JSON', json.dumps(export, ensure_ascii=False, indent=2), 'paeleap_record.json', mime='application/json')
    with st.expander('当前模板与提示词'):
        prompt_version = (brief or build_brief(data['name'], ''))['prompt_version']
        st.code((ROOT / 'prompts' / (prompt_version + '.txt')).read_text(encoding='utf-8'), language=None)
