"""Live caption/image canvas and selected Video playback."""
import json
from html import escape
from io import BytesIO
import streamlit as st
from ui_video import render_video_preview
from platform_config import PLATFORM_CONFIG, FORMATS, export_image


def render_preview_header(field, label, lang):
    """Keep one durable ratio selection, independent of translated widget labels."""
    platform = st.session_state.get('form_platform', 'xiaohongshu')
    default = st.session_state.get('active_ratio', PLATFORM_CONFIG[platform]['ratio'])
    ratio = st.session_state.get('form_preview_ratio', default)
    platform_label = PLATFORM_CONFIG[platform]['labels'][lang]
    st.markdown('<div class="preview-toolbar"><h2>' + label('Live preview', '内容预览') +
        '</h2><span class="preview-badge">' + escape(platform_label) + '</span></div>', unsafe_allow_html=True)
    ratio = field(st.radio, 'preview_ratio', ratio, label=label('Aspect ratio', '画幅比例'),
        options=list(FORMATS), horizontal=True,
        format_func=lambda key: f'{key} — {FORMATS[key][0]} × {FORMATS[key][1]}')
    st.session_state['active_ratio'] = ratio
    return ratio


def render_results(workspace, field, label, t, lang):
    if workspace == 'video':
        render_video_preview(label, st.session_state.get('form_platform', 'xiaohongshu'), st.session_state['active_ratio'])
        return
    caption_download = None
    result = st.session_state.get('result', {})
    variants = result.get('variants', [])
    image = result.get('image')
    platform = st.session_state.get('form_platform', 'xiaohongshu')
    ratio = st.session_state.get('active_ratio', PLATFORM_CONFIG[platform]['ratio'])
    platform_label = PLATFORM_CONFIG[platform]['labels'][lang]
    composed = export_image(image, ratio) if image is not None else None
    text_plan = result.get('text_plan', result.get('plan', {}))
    image_plan = result.get('image_plan', result.get('plan', {}))
    st.caption(label('Edit your title, caption and hashtags here.', '在此直接编辑标题、正文和话题标签。'))

    if variants:
        index = field(st.selectbox, 'caption_variant', 0,
                      label=label('Preferred variation', '首选文案版本'), options=list(range(len(variants))),
                      format_func=lambda i: label(f'Caption {i + 1}', f'文案 {i + 1}'))
    else:
        index = st.session_state.get('form_caption_variant', 0)
    with st.container(key='preview_stage'):
        if not variants and image is None:
            st.markdown('<div class="preview-empty" role="status"><h4>' +
                        label('Nothing to preview yet', '暂无可预览内容') + '</h4><p>' +
                        label('Generate a caption and image to see your post here.',
                              '生成文案和图片，即可在此预览你的图文。') + '</p></div>', unsafe_allow_html=True)
            return
        if variants or image is not None:
            st.markdown('<div class="preview-label">' + escape(platform_label) + ' · ' + label('POST PREVIEW', '内容预览') + '</div>', unsafe_allow_html=True)
            attraction = text_plan.get('attraction') or image_plan.get('attraction', '')
            st.markdown('<div class="post-masthead"><span class="avatar">p.</span><div>' +
                        label('PAELEAP Travel Notes', 'PAELEAP 旅行手记') + '<small>' +
                        escape(attraction) + '</small></div></div>', unsafe_allow_html=True)
        if image is not None:
            with st.container(key='composition_' + ratio.replace(':', '_')):
                st.image(composed, width='stretch')
            st.caption(f'{platform_label} · {ratio} · {FORMATS[ratio][0]} × {FORMATS[ratio][1]} · ' + (label('Uploaded photo', '上传照片') if image_plan.get('source') == 'uploaded_photo' else t['image']))
            st.caption(label('Full composition preserved · original available below', '完整保留画面 · 可下载原图'))
            highlight = image_plan.get('image_highlight')
            if highlight:
                st.caption(label('Image highlight: ', '图片对应看点：') + highlight)
        else:
            st.markdown('<div class="preview-missing preview-missing-image">' +
                        label('No image yet. Generate one in Image.', '暂无图片，请前往图片工作区生成。') +
                        '</div>', unsafe_allow_html=True)
        if variants:
            source = variants[index]
            if text_plan.get('language') != lang:
                st.warning(label('This draft keeps its original language. Generate Caption to create an English draft.',
                                 '此草稿保留原语言。点击生成文案以创建中文草稿。'))
            alternatives = source.get('alternative_titles', [v['title'] for i, v in enumerate(variants) if i != index][:2])
            if alternatives:
                with st.expander(label('Two alternative titles', '两个备选标题')):
                    for n, suggestion in enumerate(alternatives):
                        field(st.text_input, f'draft_{index}_alternative_{n}', suggestion, label=label(f'Title suggestion {n+1}', f'备选标题 {n+1}'))
            if text_plan.get('platform', 'xiaohongshu') != platform:
                st.caption(label('Draft retained. Generate a new caption to adapt its wording to this platform.', '已保留草稿；重新生成文案可适配当前平台。'))
            title = field(st.text_input, f'draft_{index}_title', source['title'], label=label('Title', '标题'))
            caption = field(st.text_area, f'draft_{index}_caption', source['caption'],
                            label=label('Caption', '正文'), height=280)
            hashtags = field(st.text_area, f'draft_{index}_hashtags', ' '.join(source['hashtags']),
                             label=label('Hashtags', '话题标签'), height=85)
            caption_download = title + '\n\n' + caption + '\n\n' + hashtags
        else:
            st.markdown('<div class="preview-missing preview-missing-caption">' +
                        label('No caption yet. Generate one in Caption.', '暂无文案，请前往文案工作区生成。') +
                        '</div>', unsafe_allow_html=True)
        with st.container(key='export_actions'):
            export_columns = st.columns(3 if image is not None and caption_download is not None else 2)
        if caption_download is not None:
            with export_columns[0]:
                st.download_button(t['download_copy'], caption_download, f'caption_{index + 1}.txt',
                    key=f'download_{index}', use_container_width=True)
        if image is not None:
            bio = BytesIO()
            composed.save(bio, format='PNG')
            with export_columns[1 if caption_download is not None else 0]:
                st.download_button(t['download_image'], bio.getvalue(), f'paeleap_{platform}_{ratio.replace(":", "x")}.png', 'image/png', use_container_width=True)
        if image is not None:
            with st.expander(label('Original image', '原始图片')):
                st.image(image, width='stretch')
                original = BytesIO()
                image.save(original, format='PNG')
                st.download_button(label('Download original', '下载原图'), original.getvalue(), 'paeleap_original.png', 'image/png')
        if workspace == 'image' and image is not None:
            with st.expander(t['prompt']):
                st.code(image_plan.get('image_prompt', ''), language='text')
        if variants or image is not None:
            edited = []
            for i, source in enumerate(variants):
                item = {**source}
                for part in ('title', 'caption', 'hashtags'):
                    default = ' '.join(source[part]) if part == 'hashtags' else source[part]
                    value = st.session_state.get(f'form_draft_{i}_{part}', default)
                    item[part] = value.split() if part == 'hashtags' else value
                item['alternative_titles'] = [st.session_state.get(f'form_draft_{i}_alternative_{n}', title) for n, title in enumerate(source.get('alternative_titles', [v['title'] for j, v in enumerate(variants) if j != i][:2]))]
                item['edited_after_generation'] = any(item[k] != source[k] for k in ('title', 'caption', 'hashtags'))
                edited.append(item)
            with export_columns[-1]:
                st.download_button(t['download_json'], json.dumps(dict(
                    platform=platform, export_settings=dict(aspect_ratio=ratio, dimensions=FORMATS[ratio], composition='contain'),
                    plan=text_plan or image_plan, text_plan=text_plan, image_plan=image_plan,
                    variants=edited, source_variants=variants, selected_variant=index,
                    backend=result.get('image_backend', 'cloudflare') if image is not None else None, review_required=True),
                    ensure_ascii=False, indent=2), 'paeleap_post.json', 'application/json', use_container_width=True)
