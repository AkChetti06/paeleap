"""Bilingual tourism studio. Credentials and API calls remain server-side."""
import json
import os
import time
from html import escape
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageOps

import streamlit as st
from dotenv import load_dotenv
from ui_banner import render_gallery
from ui_workspaces import render_navigation
from ui_results import render_results, render_preview_header
from ui_video import render_video_controls
from ui_shell import render_sidebar, render_heading, render_coming_soon
from platform_config import PLATFORM_CONFIG, FORMATS, TEMPLATE_LIBRARY
from studio_state import save_caption_output, retain_legacy_plans
from engine import (CATEGORY_CONFIG, DESTINATIONS, STYLES, plan, recommend_style,
                    generate_caption_variants, generate_cloudflare_image,
                    save_output, safe_error)

load_dotenv(dotenv_path=Path(__file__).resolve().parent / '.env', override=False)
st.set_page_config(page_title='PAELEAP | Creator Studio', page_icon='✦', layout='wide', initial_sidebar_state='auto')

COPY = {'English': {'eyebrow': 'A LITTLE WANDER. A GREAT STORY.',
             'headline': 'Turn places into stories.',
             'subhead': 'Your next travel post, thoughtfully written and beautifully imagined.',
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
             'generate': 'Generate Caption',
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
        'subhead': '从一个地名开始，用 AI 创作有温度的旅行内容。',
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
        'generate': '生成文案',
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


def change_platform():
    # A platform change always starts from that platform's recommended format.
    default = PLATFORM_CONFIG[st.session_state['form_platform']]['ratio']
    st.session_state['form_preview_ratio'] = default
    st.session_state['active_ratio'] = default


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
st.html('<style>' + (Path(__file__).parent / 'studio.css').read_text() + '</style>')
header_cn = st.session_state.get('language', 'English') == '中文'
section = render_sidebar(header_cn)
header = st.container(key='studio_header')
bar_left, bar_right = header.columns([0.86, 0.14], vertical_alignment='center')
with bar_left:
    render_heading(header_cn, section)
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


if section != 'create':
    render_coming_soon(section, cn)
    st.stop()

render_gallery(t, lang)
with st.container(key='creator_grid'):
    controls, preview = st.columns([0.5, 0.5], gap='large')
# Render the preview selector first so this run's generation and video use its value.
results_panel = preview.container(key='results_panel')
with results_panel:
    platform, ratio = render_preview_header(field, label, lang, change_platform)
with controls:
    st.markdown('## :material/description: ' + label('Content Brief', '创作简报'))
    workspace = render_navigation(cn)
    if 'result' in st.session_state:
        retain_legacy_plans(st.session_state['result'])
    clicked = False
    if workspace == 'text':
        with st.container(key='brief_card'):
            with st.container(key='brief_destination'):
                st.markdown('<div class="brief-section">' + label('Destination', '目的地') + '</div>', unsafe_allow_html=True)
                # Preserve names edited in older sessions when migrating to one selector.
                if not st.session_state.get('name_is_preset', True) and st.session_state.get('form_destination', 'west_lake') in DESTINATIONS:
                    st.session_state['form_destination'] = 'custom'
                destination = field(st.selectbox, 'destination', 'west_lake', callback=use_preset,
                    label=t['destination'], label_visibility='collapsed', options=[*DESTINATIONS, 'custom'],
                    format_func=lambda value: DESTINATIONS[value]['labels'][lang] if value in DESTINATIONS else t['custom'],
                    help=t['destination_help'])
                if destination == 'custom':
                    attraction = field(st.text_input, 'attraction', '', callback=edited_name,
                        label=t['name'], placeholder=label('Enter an attraction name', '请输入景点名称'), max_chars=100)
                else:
                    attraction = DESTINATIONS[destination]['labels'][lang]
                    st.session_state['form_attraction'] = attraction
            with st.container(key='brief_category'):
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
            with st.container(key='brief_creative'):
                st.markdown('<div class="brief-section">' + label('Creative direction', '创作方向') + '</div>', unsafe_allow_html=True)
                style = st.session_state.get('form_visual_style_choice', recommendation)
                audience_column, angle_column = st.columns(2)
                with audience_column:
                    audience = field(st.text_input, 'audience', t['audience_default'], callback=edited_audience,
                        label=t['audience'], max_chars=100)
                with angle_column:
                    angle = field(st.text_input, 'creative_angle', '', label=t['angle'],
                        placeholder=t['angle_placeholder'], max_chars=180)
            with st.container(key='brief_details'):
                st.markdown('<div class="brief-section">' + label('Content details', '内容重点') + '</div>', unsafe_allow_html=True)
                highlights_text = field(st.text_input, 'highlights', '', label=label('Key highlights (1–3)', '核心看点（1–3个）'), placeholder=label('Separate highlights with a semicolon', '请用分号分隔看点'), help=label('Enter one to three highlights, separated by ;', '请输入1–3个看点，用；分隔'), max_chars=302)
                st.caption(TEMPLATE_LIBRARY[category]['name'])
                keywords = field(st.text_input, 'keywords', '', label=label('Keywords (optional)', '关键词（可选）'),
                    placeholder=label('e.g. waterside, quiet textures', '例如：水岸、宁静质感'), max_chars=180)
            st.divider()
            clicked = st.button(t['generate'], key='generate_caption', type='primary', width='stretch', disabled=not attraction.strip())

    if workspace == 'image':
        # A style chosen before opening the text brief is a deliberate user choice.
        st.session_state.setdefault('style_context', (
            st.session_state.get('form_destination', 'west_lake') if st.session_state.get('name_is_preset', True)
            else st.session_state.get('form_attraction', ''),
            st.session_state.get('form_category', 'natural_scenery'),
            st.session_state.get('form_creative_angle', '')))
        with st.container(key='image_controls'):
            st.markdown('<div class="brief-section">' + label('Visual direction', '视觉方向') + '</div>', unsafe_allow_html=True)
            st.caption(label('Use the destination and highlights from your caption brief.', '沿用文案简报中的目的地和核心看点。'))
            style = field(st.selectbox, 'visual_style_choice', recommend_style(
                st.session_state.get('form_attraction', DESTINATIONS['west_lake']['labels'][lang]),
                st.session_state.get('form_category', 'natural_scenery'),
                st.session_state.get('form_creative_angle', '')), label=t['style'],
                options=list(STYLES), format_func=lambda value: STYLES[value]['labels'][lang])
            with st.expander(label('Use your own photo', '使用自己的照片')):
                upload = st.file_uploader(label('Photo (PNG, JPEG, WebP)', '照片（PNG、JPEG、WebP）'), type=['png', 'jpg', 'jpeg', 'webp'])
                supplied = [h.strip() for h in st.session_state.get('form_highlights', '').replace('；', ';').split(';') if h.strip()]
                if st.session_state.get('form_photo_highlight') not in (supplied or ['']):
                    st.session_state['form_photo_highlight'] = supplied[0] if supplied else ''
                match = field(st.selectbox, 'photo_highlight', supplied[0] if supplied else '',
                    label=label('Corresponding highlight', '对应看点'), options=supplied or [''])
                if st.button(label('Use photo', '使用照片'), disabled=upload is None, key='use_photo'):
                    try:
                        if upload.size > 20_000_000:
                            raise ValueError('Photo must be under 20 MB')
                        photo = ImageOps.exif_transpose(Image.open(BytesIO(upload.getvalue())))
                        photo.load()
                        previous = st.session_state.get('result', {})
                        photo_plan = dict(attraction=st.session_state.get('form_attraction', ''),
                            image_highlight=match, platform=platform, aspect_ratio=ratio, source='uploaded_photo')
                        st.session_state['result'] = {**previous, 'image': photo.copy(), 'image_plan': photo_plan,
                            'image_backend': 'uploaded_photo', 'video': None}
                    except Exception as exc:
                        st.error(safe_error(exc, lang))
            clicked = st.button(label('Generate Image', '生成图片'), type='primary', key='generate_image',
                                width='stretch',
                                disabled=not st.session_state.get('form_attraction', DESTINATIONS['west_lake']['labels'][lang]).strip())
        attraction = st.session_state.get('form_attraction', DESTINATIONS['west_lake']['labels'][lang])
        category = st.session_state.get('form_category', 'natural_scenery')
        keywords = st.session_state.get('form_keywords', '')
        audience = st.session_state.get('form_audience', t['audience_default'])
        angle = st.session_state.get('form_creative_angle', '')

    if clicked:
        try:
            highlights = [h.strip() for h in st.session_state.get('form_highlights', '').replace('；', ';').split(';') if h.strip()]
            if workspace == 'text' and not 1 <= len(highlights) <= 3:
                raise ValueError(label('Enter one to three key highlights.', '请输入1–3个核心看点。'))
            p = plan(attraction, category, keywords, lang, style=style, audience=audience, visit_reason=angle, platform=platform, aspect_ratio=ratio, highlights=highlights)
            with st.spinner(label('Generating caption…', '正在生成文案…') if workspace == 'text' else label('Generating image…', '正在生成图片…')):
                start = time.monotonic()
                previous = st.session_state.get('result', {})
                if workspace == 'text':
                    variants = generate_caption_variants(p, setting('TEXT_API_KEY'), setting('TEXT_BASE_URL'),
                                                         setting('TEXT_MODEL', 'qwen-plus'), lang)
                    elapsed = time.monotonic() - start
                    folder = save_caption_output('outputs', p, variants, elapsed)
                    st.session_state['result'] = {**previous, 'text_plan': p,
                        'variants': variants, 'text_elapsed': elapsed, 'text_folder': str(folder)}
                    st.session_state['form_caption_variant'] = 0
                    for index, item in enumerate(variants):
                        alternatives = item.get('alternative_titles', [v['title'] for j, v in enumerate(variants) if j != index][:2])
                        for n, suggestion in enumerate(alternatives):
                            st.session_state[f'form_draft_{index}_alternative_{n}'] = suggestion
                        for part in ('title', 'caption', 'hashtags'):
                            value = ' '.join(item[part]) if part == 'hashtags' else item[part]
                            st.session_state[f'form_draft_{index}_{part}'] = value
                else:
                    image = generate_cloudflare_image(p, setting('CLOUDFLARE_ACCOUNT_ID'), setting('CLOUDFLARE_API_TOKEN'))
                    elapsed = time.monotonic() - start
                    folder = save_output('outputs', p, previous.get('variants', []), image, elapsed)
                    st.session_state['result'] = {**previous, 'image_plan': p, 'image': image,
                        'image_backend': 'cloudflare', 'image_elapsed': elapsed, 'folder': str(folder), 'video': None}
        except Exception as exc:
            st.error(safe_error(exc, lang))
            if 'result' in st.session_state:
                st.warning(label('The previous successful draft is retained.', '已保留上次成功生成的草稿。'))

    if workspace == 'video':
        render_video_controls(label, lang, platform, ratio, setting)

with preview:
    with results_panel:
        render_results(workspace, field, label, t, lang)
        if 'result' in st.session_state:
            with st.expander(t['review']):
                st.caption(t['review_note'])
                fields = ['metric1', 'metric2', 'metric3', 'metric4', 'metric5']
                values = [field(st.slider, f'score_{i}', 3, label=t[key], min_value=1, max_value=5) for i, key in enumerate(fields)]
                score = sum(value * weight for value, weight in zip(values, [.25, .25, .2, .15, .15])) * 20
                st.metric(t['score'], f'{score:.0f}/100')
                st.download_button(t['eval_download'], json.dumps(dict(weighted_score=score,
                    ratings=dict(zip(fields, values)), backend='cloudflare', image_test_valid=st.session_state['result'].get('image') is not None), ensure_ascii=False, indent=2), 'review.json')


st.markdown('<div class="footer"><span>PAELEAP STUDIO / ' + label('MADE FOR EXPLORING', '为探索而生') + '</span><span>' + escape(t['notice']) + '</span></div>', unsafe_allow_html=True)
