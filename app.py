"""Bilingual tourism studio. Credentials and API calls remain server-side."""
import json
import os
import time
from html import escape
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from ui_banner import render_gallery
from ui_workspaces import render_navigation
from ui_results import render_results
from local_photo import decode_photo, clear_photo_if_removed, remove_photo
from input_fields import render_input_fields
from offline_studio import preserve_inputs, has_draft_edits, create_offline_preview
from studio_state import save_caption_output, retain_legacy_plans
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
st.markdown('<style>' + (Path(__file__).parent / 'studio.css').read_text() + (Path(__file__).parent / 'workflow.css').read_text() + '</style>', unsafe_allow_html=True)
bar_left, bar_right = st.columns([5, 1.3], vertical_alignment='center')
with bar_left:
    header_cn = st.session_state.get('language', 'English') == '中文'
    subtitle = '创作值得分享的视觉故事。' if header_cn else 'Create visual stories worth sharing.'
    st.markdown('<div class="studio-header"><div class="brand"><span>＊</span> PAELEAP STUDIO</div>'
                f'<div class="brand-subtitle">{subtitle}</div></div>', unsafe_allow_html=True)
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


render_gallery(t, lang)
if 'next_workspace' in st.session_state:
    st.session_state['workspace'] = st.session_state.pop('next_workspace')
st.session_state['workspace'] = st.session_state.get('workspace', 'text')
workspace = render_navigation(cn)
if 'result' in st.session_state:
    retain_legacy_plans(st.session_state['result'])
preserve_inputs()
if workspace == 'text':
    st.markdown(f'<div class="heading-box"><div class="panel-title"><span>01</span>{escape(t["workspace"])}</div><div class="panel-sub">{escape(t["workspace_sub"])}</div></div>', unsafe_allow_html=True)
    input_column, result_column = st.columns([1.05, 1], gap='medium')
    # Reserve one shared action row below both panels. Populate it as each
    # action becomes available, without placing buttons in separate rows.
    with st.container(key='caption_actions'):
        generate_column, photo_column = st.columns([1.05, 1], gap='medium')
    with input_column:
        with st.container(border=True, key='brief_card'):
            st.caption(label('Offline preview: captions remain in Chinese. No AI API calls.', '离线预览：选项会影响文案，不调用 AI 接口。'))
            brief = render_input_fields(lang)
        if st.session_state.get('pending_offline_brief') != brief:
            st.session_state.pop('pending_offline_brief', None)
        previous = st.session_state.get('result', {})
        if previous.get('text_plan') and brief != {k: v for k, v in previous['text_plan'].items() if k != 'language'}:
            st.info(label('Inputs changed. Generate again to update the saved draft.', '输入已改变，当前结果仍保留旧文案；点击生成更新。'))
        if generate_column.button(t['generate'], key='generate_caption', type='primary', width='stretch', disabled=brief is None):
            if has_draft_edits(previous):
                st.session_state['pending_offline_brief'] = brief
            else:
                try:
                    create_offline_preview(brief)
                except Exception as exc:
                    st.error(safe_error(exc, lang))
        if st.session_state.get('pending_offline_brief'):
            st.warning(label('You edited the preview. Replace those edits with new drafts?', '预览中有手动修改，重新生成会替换这些修改。'))
            keep, replace = st.columns(2)
            if keep.button(label('Keep edits', '保留修改'), key='keep_offline_edits'):
                st.session_state.pop('pending_offline_brief', None)
                st.rerun()
            if replace.button(label('Replace and generate', '替换并生成'), key='replace_offline_edits'):
                try:
                    create_offline_preview(st.session_state['pending_offline_brief'])
                    st.rerun()
                except Exception as exc:
                    st.error(safe_error(exc, lang))
    with result_column:
        with st.container(border=True, key="copy_results_card"):
            render_results(workspace, field, label, t, lang)

if workspace == 'image':
    with st.container(border=True):
        st.markdown('### ' + label('Choose your photo', '选择配图'))
        field(st.selectbox, 'visual_style_choice', 'cinematic_landscape', label=t['style'],
              options=list(STYLES), format_func=lambda value: STYLES[value]['labels'][lang])
        st.caption(label('Image generation is not connected in this offline preview.', '当前为离线预览，图片生成暂未连接。'))
        photo_key = f"local_photo_{st.session_state.get('photo_epoch', 0)}"
        photo = st.file_uploader(label('Upload a photo (optional)', '上传配图（选填）'), type=['png', 'jpg', 'jpeg', 'webp'], key=photo_key, max_upload_size=20, on_change=clear_photo_if_removed, args=(photo_key,))
        if photo is not None:
            import hashlib
            digest = hashlib.sha256(photo.getvalue()).hexdigest()
            if digest != st.session_state.get('photo_digest'):
                try:
                    uploaded_image = decode_photo(photo.getvalue())
                    st.session_state.setdefault('result', {})['image'] = uploaded_image.convert('RGB')
                    st.session_state['result']['image_source'] = 'local_upload'
                    st.session_state['result']['image_plan'] = {'attraction': st.session_state['result'].get('text_plan', {}).get('attraction', '')}
                    st.session_state['photo_digest'] = digest
                except ValueError:
                    st.error(label('Unable to read this image. Please choose another file.', '无法读取这张图片，请选择其他文件。'))
        if st.session_state.get('result', {}).get('image') is not None:
            st.image(st.session_state['result']['image'], width=320, caption=label('Your uploaded photo', '已上传的配图'))
            st.caption(label('Photo ready. Continue to preview.', '配图已保存，可以进入预览。'))
            st.button(label('Remove photo', '移除配图'), key='remove_photo', on_click=remove_photo)

        st.button(label('Generate Image', '生成图片'), type='primary', key='generate_image', disabled=True, width='stretch')

if workspace == 'preview':
    with st.container(border=False):
        render_results(workspace, field, label, t, lang)

def go_to(step):
    st.session_state['next_workspace'] = step

has_copy = bool(st.session_state.get('result', {}).get('variants'))
if workspace == 'text':
    photo_column.button(label('Next: Photo →', '下一步：配图 →'), key='workflow_next', disabled=not has_copy, on_click=go_to, args=('image',), type='primary', width='stretch')
else:
    with st.container(key='workflow_actions'):
        back_col, next_col = st.columns(2)
        with back_col:
            st.button(label('← Back', '← 上一步'), key='workflow_back', on_click=go_to, args=('text' if workspace == 'image' else 'image',), width='stretch')
        with next_col:
            if workspace == 'image':
                st.button((label('Next: Preview →', '下一步：预览 →') if st.session_state.get('result', {}).get('image') is not None else label('Continue without image →', '暂不配图，下一步：预览 →')), key='workflow_next', disabled=not has_copy, on_click=go_to, args=('preview',), type='primary', width='stretch')
            else:
                st.caption(label('Edit and download your finished draft above.', '在上方确认、修改并下载文案，完成本次创作。'))
st.markdown('<div class="footer"><span>PAELEAP STUDIO / ' + label('MADE FOR EXPLORING', '为探索而生') + '</span><span>' + escape(t['notice']) + '</span></div>', unsafe_allow_html=True)