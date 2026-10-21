"""Bilingual tourism studio. Credentials and API calls remain server-side."""
import json
import os
import time
from html import escape
from io import BytesIO
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from ui_banner import render_banner
from engine import (CATEGORY_CONFIG, DESTINATIONS, STYLES, plan, recommend_style,
                    generate_caption_variants, generate_cloudflare_image, video_plans,
                    render_slideshow, save_output, safe_error)

load_dotenv(dotenv_path=Path(__file__).resolve().parent / '.env', override=False)
st.set_page_config(page_title='PAELEAP | Creator Studio', page_icon='✦', layout='wide', initial_sidebar_state='collapsed')

COPY = {'English': {'eyebrow': 'A LITTLE WANDER. A GREAT STORY.',
             'headline': 'Turn places into stories.',
             'subhead': 'Your next RedNote travel post, thoughtfully written and beautifully imagined.',
             'workspace': 'Start with a place',
             'workspace_sub': 'Set the scene. We’ll help you find the story.',
             'preview': 'Your story, taking shape',
             'preview_sub': 'Edit the title, caption or hashtags directly. No extra steps, just your own '
                            'voice.',
             'destination': 'Destination',
             'destination_help': 'Choose a researched location or enter your own.',
             'custom': 'Custom destination',
             'name': 'Tourist attraction',
             'scene': 'Category',
             'style': 'Visual direction',
             'recommend': 'Suggested for this attraction',
             'style_custom': 'You can choose any other style.',
             'audience': 'Target audience',
             'audience_default': 'First-time visitors',
             'angle': 'Creative angle',
             'angle_placeholder': 'e.g. a peaceful lakeside afternoon',
             'generate': 'Generate post ✦',
             'generate_busy': 'Creating your story…',
             'no_result': 'Your next escape, imagined.',
             'no_result_sub': 'Add a place and choose your direction. Your image and story will appear here.',
             'tag1': 'DISCOVER',
             'tag2': 'CREATE',
             'tag3': 'REFINE',
             'notice': 'Research-based concept only. Generated images are illustrative, not on-location '
                       'photographs; review claims before publishing.',
             'image': 'AI concept image — not a real photograph',
             'download_image': '↓  Download image',
             'download_copy': '↓  Save caption',
             'download_json': '↓  Download JSON',
             'review': 'Quality review',
             'review_note': 'Review landmark accuracy, travel claims and any generated text before '
                            'publishing. Images and video are illustrative concepts.',
             'score': 'Weighted review score',
             'metric1': 'Visual quality · 25%',
             'metric2': 'Landmark accuracy · 25%',
             'metric3': 'Style consistency · 20%',
             'metric4': 'Cost efficiency · 15%',
             'metric5': 'Integration · 15%',
             'eval_download': '↓  Export review'},
 '中文': {'eyebrow': '灵感始于远方，故事由你书写',
        'headline': '让每个目的地，都有好故事。',
        'subhead': '从一个地名开始，用 AI 创作有温度的小红书旅行图文。',
        'workspace': '从一个目的地开始',
        'workspace_sub': '告诉我们你的灵感，其余交给创作。',
        'preview': '故事，正在发生',
        'preview_sub': '直接编辑标题、正文与话题标签，让文字更像你。',
        'destination': '目的地',
        'destination_help': '选择已研究的景点，或输入自定义景点。',
        'custom': '自定义景点',
        'name': '景点名称',
        'scene': '景点类别',
        'style': '视觉风格',
        'recommend': '根据景点类型推荐',
        'style_custom': '也可以自由选择其他风格。',
        'audience': '目标受众',
        'audience_default': '首次到访游客',
        'angle': '创作角度',
        'angle_placeholder': '例如：悠闲的湖边午后',
        'generate': '生成图文 ✦',
        'generate_busy': '正在创作旅行故事…',
        'no_result': '想象下一次出发。',
        'no_result_sub': '添加景点，选择创作方向，你的图片与故事将在这里出现。',
        'tag1': '发现',
        'tag2': '创作',
        'tag3': '优化',
        'notice': '本原型仅用于研究测试；生成图片不是现场实拍，发布前必须人工核实事实。',
        'image': 'AI 概念图片 — 非现场实拍',
        'download_image': '↓  下载图片',
        'download_copy': '↓  下载文案',
        'download_json': '↓  下载 JSON',
        'review': '内容质量检查',
        'review_note': '发布前请检查地标外观、旅行信息及生成文字。图片和视频均为概念示意。',
        'score': '加权评估分数',
        'metric1': '视觉质量 · 25%',
        'metric2': '地标准确性 · 25%',
        'metric3': '风格一致性 · 20%',
        'metric4': '成本效率 · 15%',
        'metric5': '集成性能 · 15%',
        'eval_download': '↓  导出评估'}}


def setting(name, default=''):
    """Read only server-side configuration; never put credentials in widget state."""
    if os.getenv(name):
        return os.environ[name]
    try:
        return str(st.secrets.get(name, default))
    except FileNotFoundError:
        return default


def changed(name, callback=None):
    st.session_state['form_' + name] = st.session_state[name]
    if callback:
        callback()


def field(widget, name, default, callback=None, **kwargs):
    """Durable form values survive label/format changes and Streamlit widget cleanup."""
    storage = 'form_' + name
    st.session_state.setdefault(storage, default)
    st.session_state[name] = st.session_state[storage]
    return widget(key=name, on_change=changed, args=(name, callback), **kwargs)


def use_preset():
    destination = st.session_state['form_destination']
    item = DESTINATIONS.get(destination)
    lang = st.session_state.get('language', 'English')
    st.session_state['form_attraction'] = item['labels'][lang] if item else ''
    st.session_state['name_is_preset'] = bool(item)
    if item and item['category']:
        st.session_state['form_category'] = item['category']


def edited_name():
    st.session_state['name_is_preset'] = False


def edited_audience():
    st.session_state['audience_is_default'] = False


def change_language():
    lang = st.session_state['language']
    destination = st.session_state.get('form_destination', 'west_lake')
    if st.session_state.get('name_is_preset', True) and destination in DESTINATIONS:
        st.session_state['form_attraction'] = DESTINATIONS[destination]['labels'][lang]
    if st.session_state.get('audience_is_default', True):
        st.session_state['form_audience'] = COPY[lang]['audience_default']


theme_type = getattr(getattr(st.context, 'theme', None), 'type', None) or st.get_option('theme.base') or 'light'
if theme_type == 'dark':
    st.markdown('<span class="studio-theme-dark" aria-hidden="true" style="display:none"></span>', unsafe_allow_html=True)
st.markdown('<style>' + (Path(__file__).parent / 'studio.css').read_text() + '</style>', unsafe_allow_html=True)
bar_left, bar_right = st.columns([5, 1.3], vertical_alignment='center')
with bar_left:
    st.markdown('<div class="brand"><span>＊</span> PAELEAP STUDIO</div>', unsafe_allow_html=True)
with bar_right:
    # A native single-choice radio styled as segments cannot be toggled into an empty state.
    lang = st.radio('EN | 中文',
        ['English', '中文'], format_func=lambda value: 'EN' if value == 'English' else '中文',
        horizontal=True, key='language', label_visibility='collapsed', on_change=change_language)
COPY['English']['prompt'] = 'Image prompt'
COPY['中文']['prompt'] = '图片提示词'
t = COPY[lang]
cn = lang == '中文'


def label(en, zh):
    return zh if cn else en


st.markdown(render_banner(t, lang), unsafe_allow_html=True)
left, right = st.columns([0.84, 1.16], gap='large')
with left:
    st.markdown(f'<div class="heading-box"><div class="panel-title"><span>01</span>{escape(t["workspace"])}</div><div class="panel-sub">{escape(t["workspace_sub"])}</div></div>', unsafe_allow_html=True)
    with st.container(border=True, key='brief_card'):
        destination = field(st.selectbox, 'destination', 'west_lake', callback=use_preset,
            label=t['destination'], options=[*DESTINATIONS, 'custom'],
            format_func=lambda value: DESTINATIONS[value]['labels'][lang] if value in DESTINATIONS else t['custom'],
            help=t['destination_help'])
        attraction = field(st.text_input, 'attraction', DESTINATIONS['west_lake']['labels'][lang],
            callback=edited_name, label=t['name'], placeholder=label('e.g. West Lake, Hangzhou', '例如：杭州西湖'), max_chars=100)
        category = field(st.radio, 'category', 'natural_scenery', label=t['scene'],
            options=list(CATEGORY_CONFIG), format_func=lambda value: CATEGORY_CONFIG[value]['labels'][lang], horizontal=True)
        angle_value = st.session_state.get('form_creative_angle', '')
        recommendation = recommend_style(attraction, category, angle_value)
        # Only meaningful brief changes update the suggestion. Translation is not a brief change.
        name_context = destination if st.session_state.get('name_is_preset', True) else attraction
        context = (name_context, category, angle_value)
        if st.session_state.get('style_context') != context:
            st.session_state['form_visual_style_choice'] = recommendation
            st.session_state['style_context'] = context
        st.caption(f'✦ {t["recommend"]}: **{STYLES[recommendation]["labels"][lang]}** · {t["style_custom"]}')
        style = field(st.selectbox, 'visual_style_choice', recommendation, label=t['style'],
            options=list(STYLES), format_func=lambda value: STYLES[value]['labels'][lang])
        audience = field(st.text_input, 'audience', t['audience_default'], callback=edited_audience,
            label=t['audience'], max_chars=100)
        angle = field(st.text_input, 'creative_angle', '', label=t['angle'],
            placeholder=t['angle_placeholder'], max_chars=180)
        keywords = field(st.text_input, 'keywords', '', label=label('Keywords (optional)', '关键词（可选）'),
            placeholder=label('e.g. waterside, quiet textures', '例如：水岸、宁静质感'), max_chars=180)
        st.markdown('<div style="height:2px"></div>', unsafe_allow_html=True)
        st.divider()
        clicked = st.button(t['generate'], type='primary', use_container_width=True, disabled=not attraction.strip())
        st.caption(label('One image, three caption variants, and an optional short video.', '一次生成封面与三个文案版本，还可制作短视频。'))
    st.markdown('<div class="human-note">＊ &nbsp; ' + label(
        'A starting point, never a substitute for you.<small>Make the words your own. Edit directly in the preview.</small>',
        'AI 提供灵感，你保留自己的声音。<small>直接编辑预览中的标题与正文，分享你的创作想法。</small>') + '</div>', unsafe_allow_html=True)

if clicked:
    try:
        p = plan(attraction, category, keywords, lang, style=style, audience=audience, visit_reason=angle)
        with st.spinner(t['generate_busy']):
            start = time.monotonic()
            variants = generate_caption_variants(p, setting('TEXT_API_KEY'), setting('TEXT_BASE_URL'),
                                                 setting('TEXT_MODEL', 'qwen-plus'), lang)
            image = generate_cloudflare_image(p, setting('CLOUDFLARE_ACCOUNT_ID'), setting('CLOUDFLARE_API_TOKEN'))
            elapsed = time.monotonic() - start
            folder = save_output('outputs', p, variants, image, elapsed)
            st.session_state['result'] = dict(plan=p, variants=variants, image=image, folder=str(folder), elapsed=elapsed, video=None)
            for index, item in enumerate(variants):
                for part in ('title', 'caption', 'hashtags'):
                    value = ' '.join(item[part]) if part == 'hashtags' else item[part]
                    st.session_state[f'form_draft_{index}_{part}'] = value
    except Exception as exc:
        st.error(safe_error(exc, lang))
        if 'result' in st.session_state:
            st.warning(label('The previous successful draft is retained.', '已保留上次成功生成的草稿。'))

with right:
    st.markdown(f'<div class="heading-box"><div class="panel-title"><span>02</span>{escape(t["preview"])}</div><div class="panel-sub">{escape(t["preview_sub"])}</div></div>', unsafe_allow_html=True)
    with st.container(border=False, key='preview_stage'):
        st.markdown('<div class="preview-label">' + label('REDNOTE · POST PREVIEW', '小红书 · 图文预览') + '</div>', unsafe_allow_html=True)
        if 'result' not in st.session_state:
            st.markdown(f'<div class="preview-placeholder"><div class="placeholder-symbol">✧</div><strong>{escape(t["no_result"])}</strong><div>{escape(t["no_result_sub"])}</div><div class="step-line"><span class="step-pill">{escape(t["tag1"])}</span><span class="step-pill">{escape(t["tag2"])}</span><span class="step-pill">{escape(t["tag3"])}</span></div></div>', unsafe_allow_html=True)
        else:
            result = st.session_state['result']
            p = result['plan']
            st.markdown('<div class="post-masthead"><span class="avatar">p.</span><div>' + label('PAELEAP Travel Notes', 'PAELEAP 旅行手记') + '<small>' + escape(p['attraction']) + '</small></div><span class="post-menu">···</span></div>', unsafe_allow_html=True)
            st.image(result['image'], caption=t['image'], use_container_width=True)
            st.caption(label('Draft language: ', '草稿语言：') + ({'English': 'English', '中文': 'Chinese'}[p['language']] if not cn else {'English': '英语', '中文': '中文'}[p['language']]))
            if p['language'] != lang:
                st.warning(label('Generate again for English captions. Existing edits keep their original language.', '请重新生成中文文案。已有编辑保留原语言。'))
            edited = []
            for index, tab in enumerate(st.tabs([label(f'Caption {i}', f'文案 {i}') for i in range(1, 4)])):
                with tab:
                    title = field(st.text_input, f'draft_{index}_title', '', label=label('Title', '标题'), label_visibility='collapsed')
                    caption = field(st.text_area, f'draft_{index}_caption', '', label=label('Caption', '正文'), height=280, label_visibility='collapsed')
                    hashtags = field(st.text_area, f'draft_{index}_hashtags', '', label=label('Hashtags', '话题标签'), height=85, label_visibility='collapsed')
                    source = result['variants'][index]
                    item = {**source, 'title': title, 'caption': caption, 'hashtags': hashtags.split()}
                    item['edited_after_generation'] = any(item[key] != source[key] for key in ('title', 'caption', 'hashtags'))
                    edited.append(item)
                    st.download_button(t['download_copy'], title + '\n\n' + caption + '\n\n' + hashtags,
                        f'caption_{index+1}.txt', key=f'download_{index}', use_container_width=True)
            st.caption(label(f'{result["elapsed"]:.1f}s · Image generated with Cloudflare · AI caption draft',
                             f'{result["elapsed"]:.1f}秒 · Cloudflare 生成图片 · AI 文案草稿'))
            bio = BytesIO()
            result['image'].save(bio, format='PNG')
            st.download_button(t['download_image'], bio.getvalue(), 'paeleap_visual.png', 'image/png', use_container_width=True)
            st.download_button(t['download_json'], json.dumps(dict(plan=p, variants=edited, source_variants=result['variants'],
                backend='cloudflare', review_required=True), ensure_ascii=False, indent=2), 'paeleap_post.json', 'application/json', use_container_width=True)
            with st.expander(t['prompt']):
                st.code(p['image_prompt'], language='text')
            st.caption(label('Video reuses the cover and generates two more Cloudflare images, using additional quota.', '视频复用封面，另生成两张 Cloudflare 图片，会使用额外额度。'))
            if st.button(label('Create short video', '生成短视频'), key='generate_video'):
                try:
                    with st.spinner(label('Creating two images and rendering video…', '正在生成两张图片并渲染视频…')):
                        frames = [result['image']]
                        for frame_plan in video_plans(p)[1:]:
                            frames.append(generate_cloudflare_image(frame_plan, setting('CLOUDFLARE_ACCOUNT_ID'), setting('CLOUDFLARE_API_TOKEN')))
                        video = render_slideshow(frames)
                        (Path(result['folder']) / 'slideshow.mp4').write_bytes(video)
                        result['video'] = video
                except Exception as exc:
                    st.error(safe_error(exc, lang))
            if result['video']:
                st.video(result['video'])
                st.download_button(label('Download video', '下载视频'), result['video'], 'paeleap_slideshow.mp4', 'video/mp4')

st.markdown('<div class="footer"><span>PAELEAP STUDIO / ' + label('MADE FOR EXPLORING', '为探索而生') + '</span><span>' + escape(t['notice']) + '</span></div>', unsafe_allow_html=True)
if 'result' in st.session_state:
    with st.expander(t['review']):
        st.caption(t['review_note'])
        fields = ['metric1', 'metric2', 'metric3', 'metric4', 'metric5']
        values = [field(st.slider, f'score_{i}', 3, label=t[key], min_value=1, max_value=5) for i, key in enumerate(fields)]
        score = sum(value * weight for value, weight in zip(values, [.25, .25, .2, .15, .15])) * 20
        st.metric(t['score'], f'{score:.0f}/100')
        st.download_button(t['eval_download'], json.dumps(dict(weighted_score=score,
            ratings=dict(zip(fields, values)), backend='cloudflare', image_test_valid=True), ensure_ascii=False, indent=2), 'review.json')
