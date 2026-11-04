"""Editable post canvas and exports; source drafts and images remain untouched."""
import json
from io import BytesIO
import streamlit as st
from ui_video import render_video_preview
from platform_config import PLATFORM_CONFIG, FORMATS, export_image


def render_preview_header(field, label, lang, change_platform):
    heading, platform_slot = st.columns([0.58, 0.42], vertical_alignment='center')
    with heading:
        st.markdown('## :material/visibility: ' + label('Live Preview', '内容预览'))
    with platform_slot:
        platform = field(st.selectbox, 'platform', 'xiaohongshu', callback=change_platform,
            label=label('Platform', '发布平台'), label_visibility='collapsed',
            options=list(PLATFORM_CONFIG), format_func=lambda key: PLATFORM_CONFIG[key]['labels'][lang])
    st.caption(label('Review and edit your content before exporting.', '导出前，请检查并编辑内容。'))
    default = st.session_state.get('active_ratio', PLATFORM_CONFIG[platform]['ratio'])
    ratio = field(st.radio, 'preview_ratio', st.session_state.get('form_preview_ratio', default),
        label=label('Aspect ratio', '画幅比例'), options=list(FORMATS), horizontal=True, width='stretch',
        format_func=lambda key: f'{key} — {FORMATS[key][0]} × {FORMATS[key][1]}')
    st.session_state['active_ratio'] = ratio
    return platform, ratio


def edited_variants(variants):
    """Serialize durable edits even while another workspace or section is visible."""
    edited = []
    for i, source in enumerate(variants):
        item = {**source}
        for part in ('title', 'caption', 'hashtags'):
            default = ' '.join(source[part]) if part == 'hashtags' else source[part]
            value = st.session_state.get(f'form_draft_{i}_{part}', default)
            item[part] = value.split() if part == 'hashtags' else value
        alternatives = source.get('alternative_titles', [v['title'] for j, v in enumerate(variants) if j != i][:2])
        item['alternative_titles'] = [st.session_state.get(f'form_draft_{i}_alternative_{n}', title)
                                      for n, title in enumerate(alternatives)]
        item['edited_after_generation'] = any(item[k] != source[k] for k in ('title', 'caption', 'hashtags'))
        edited.append(item)
    return edited


def render_results(workspace, field, label, t, lang):
    platform = st.session_state.get('form_platform', 'xiaohongshu')
    ratio = st.session_state['active_ratio']
    if workspace == 'video':
        render_video_preview(label, platform, ratio)
        return
    result = st.session_state.get('result', {})
    variants, image = result.get('variants', []), result.get('image')
    text_plan = result.get('text_plan', result.get('plan', {}))
    image_plan = result.get('image_plan', result.get('plan', {}))
    with st.container(key='preview_stage'):
        if not variants and image is None:
            st.markdown('<div class="preview-empty" role="status"><h4>' + label('Nothing to preview yet', '暂无可预览内容') +
                '</h4><p>' + label('Generate a caption, image or video to see it here.', '生成文案、图片或视频后，即可在此预览。') + '</p></div>', unsafe_allow_html=True)
            return
        index = field(st.selectbox, 'caption_variant', 0, label=label('Preferred variation', '首选文案版本'),
            options=list(range(len(variants))), label_visibility='collapsed',
            format_func=lambda i: label(f'Caption {i + 1}', f'文案 {i + 1}')) if variants else 0
        if variants and text_plan.get('language') != lang:
            st.warning(label('This draft keeps its original language. Generate Caption to create an English draft.',
                             '此草稿保留原语言。点击生成文案以创建中文草稿。'))
        if variants and text_plan.get('platform', 'xiaohongshu') != platform:
            st.caption(label('Draft retained. Generate a new caption to adapt its wording to this platform.', '已保留草稿；重新生成文案可适配当前平台。'))
        with st.container(key='post_composer'):
            visual, copy = st.columns([0.43, 0.57], gap='small')
        with visual:
            if image is not None:
                with st.container(key='composition_' + ratio.replace(':', '_')):
                    st.image(export_image(image, ratio), width='stretch')
                st.caption(f'{ratio} · {FORMATS[ratio][0]} × {FORMATS[ratio][1]}')
                st.caption(label('Uploaded photo', '上传照片') if image_plan.get('source') == 'uploaded_photo' else t['image'])
            else:
                st.markdown('<div class="preview-missing preview-missing-image">' + label('No image yet. Generate one in Image.', '暂无图片，请前往图片工作区生成。') + '</div>', unsafe_allow_html=True)
        caption_download = None
        with copy:
            if variants:
                source = variants[index]
                title = field(st.text_input, f'draft_{index}_title', source['title'], label=label('Title', '标题'))
                caption = field(st.text_area, f'draft_{index}_caption', source['caption'], label=label('Caption', '正文'), height=180)
                hashtags = field(st.text_area, f'draft_{index}_hashtags', ' '.join(source['hashtags']), label=label('Hashtags', '话题标签'), height=80)
                caption_download = title + '\n\n' + caption + '\n\n' + hashtags
            else:
                st.markdown('<div class="preview-missing preview-missing-caption">' + label('No caption yet. Generate one in Caption.', '暂无文案，请前往文案工作区生成。') + '</div>', unsafe_allow_html=True)
        with st.container(key='export_actions'):
            slots = st.columns(3 if image is not None and caption_download is not None else 2, gap='small')
        if caption_download is not None:
            with slots[0]:
                st.download_button(t['download_copy'], caption_download, f'caption_{index + 1}.txt', key=f'download_{index}', width='stretch')
        if image is not None:
            data = BytesIO()
            export_image(image, ratio).save(data, format='PNG')
            with slots[1 if caption_download is not None else 0]:
                st.download_button(t['download_image'], data.getvalue(), f'paeleap_{platform}_{ratio.replace(":", "x")}.png', 'image/png', width='stretch')
        with slots[-1]:
            st.download_button(t['download_json'], json.dumps(dict(platform=platform,
                export_settings=dict(aspect_ratio=ratio, dimensions=FORMATS[ratio], composition='contain'),
                plan=text_plan or image_plan, text_plan=text_plan, image_plan=image_plan,
                variants=edited_variants(variants), source_variants=variants, selected_variant=index,
                backend=result.get('image_backend', 'cloudflare') if image is not None else None, review_required=True),
                ensure_ascii=False, indent=2), 'paeleap_post.json', 'application/json', width='stretch')
        if variants:
            alternatives = variants[index].get('alternative_titles', [v['title'] for j, v in enumerate(variants) if j != index][:2])
            with st.expander(label('Two alternative titles', '两个备选标题')):
                for n, suggestion in enumerate(alternatives):
                    field(st.text_input, f'draft_{index}_alternative_{n}', suggestion, label=label(f'Title suggestion {n+1}', f'备选标题 {n+1}'))
        if image is not None:
            with st.expander(label('Original image & composition', '原图与构图')):
                st.image(image, width='stretch')
                st.caption(label('The full original is preserved. Exports use padding without cropping or stretching.', '完整保留原图；导出按需留边，不裁切、不拉伸。'))
                if image_plan.get('image_highlight'):
                    st.caption(label('Image highlight: ', '图片对应看点：') + image_plan['image_highlight'])
                original = BytesIO()
                image.save(original, format='PNG')
                st.download_button(label('Download original', '下载原图'), original.getvalue(), 'paeleap_original.png', 'image/png')
            if workspace == 'image':
                with st.expander(t['prompt']):
                    st.code(image_plan.get('image_prompt', ''), language='text')
