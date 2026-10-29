"""Read-only workspace results and editable Preview, sharing durable draft keys."""
from html import escape
from io import BytesIO
from zipfile import ZipFile
from xiaohongshu_templates import ordered_photos
import streamlit as st
from image_brief import context_fingerprint
from image_workspace import selected_caption, STYLE_LABELS


def render_results(workspace, field, label, t, lang):
    result = st.session_state.get('result', {})
    variants = result.get('variants', [])
    image = result.get('image')
    photos = ordered_photos(result.get('text_plan',{}),result.get('photos',[]))
    text_plan = result.get('text_plan', result.get('plan', {}))
    image_plan = result.get('image_plan', result.get('plan', {}))
    if workspace == 'text':
        st.markdown('### ' + label('Caption results', '文案结果'))
    elif workspace == 'image':
        st.markdown('### ' + label('Image results', '图片结果'))
    else:
        st.markdown('### ' + label('Final Preview', '整体预览'))

    if workspace in ('text', 'preview') and variants:
        index = field(st.selectbox, 'caption_variant', 0,
                      label=label('Preferred variation', '首选文案版本'), options=list(range(len(variants))),
                      format_func=lambda i: label(f'Caption {i + 1}', f'文案 {i + 1}'))
    else:
        index = st.session_state.get('form_caption_variant', 0)
    with st.container(key='preview_stage' if workspace == 'preview' else 'workspace_results'):
        if workspace == 'preview' and (variants or image is not None):
            st.markdown('<div class="preview-label">' + label('REDNOTE · POST PREVIEW', '小红书 · 图文预览') + '</div>', unsafe_allow_html=True)
            attraction = text_plan.get('attraction') or image_plan.get('attraction', '')
            st.markdown('<div class="post-masthead"><span class="avatar">p.</span><div>' +
                        label('PAELEAP Travel Notes', 'PAELEAP 旅行手记') + '<small>' +
                        escape(attraction) + '</small></div></div>', unsafe_allow_html=True)
        if workspace in ('image', 'preview'):
            if photos:
                options=list(range(len(photos)))
                if st.session_state.get('preview_photo',0) not in options: st.session_state['preview_photo']=0
                photo_index=st.selectbox(label('Photo order','配图顺序'),options,
                    format_func=lambda i: str(i+1)+' / '+str(len(photos))+' · '+photos[i]['name'],key='preview_photo')
                image=photos[photo_index]['image']
            if image is not None:
                st.image(image, caption=label('Uploaded photo', '本地上传配图') if result.get('image_source') == 'local_upload' else t['image'], width='stretch')
            else:
                st.caption(label('No image yet; generation is disabled in this offline preview.', '暂无图片；当前离线预览未连接图片生成。'))
        if workspace in ('text', 'preview'):
            if variants:
                source = variants[index]
                if result.get('template_name'): st.caption(label('Template: ','模板：')+result['template_name'])
                if result.get('copy_source') == 'local_template_not_llm' and lang != '中文':
                    st.caption('Offline drafts currently remain in Chinese; switching interface language does not translate them.')
                elif text_plan.get('language') != lang:
                    st.warning(label('This draft keeps its original language. Generate Caption to create an English draft.',
                                     '此草稿保留原语言。点击生成文案以创建中文草稿。'))
                if workspace == 'preview':
                    title = field(st.text_input, f'draft_{index}_title', source['title'], label=label('Title', '标题'))
                    caption = field(st.text_area, f'draft_{index}_caption', source['caption'],
                                    label=label('Caption', '正文'), height=280)
                    hashtags = field(st.text_area, f'draft_{index}_hashtags', ' '.join(source['hashtags']),
                                     label=label('Hashtags', '话题标签'), height=85)
                else:
                    # Caption results always show immutable generated text, not Preview edits.
                    title, caption, hashtags = source['title'], source['caption'], ' '.join(source['hashtags'])
                    st.markdown('#### ' + escape(title))
                    st.text(caption)
                    st.text(hashtags)
                st.download_button(t['download_copy'], title + '\n\n' + caption + '\n\n' + hashtags,
                                   f'caption_{index + 1}.txt', key=f'download_{index}', width='stretch')
            else:
                st.caption(label('No caption yet. Generate one in Caption.', '暂无文案，请前往文案工作区生成。'))
        if workspace in ('image', 'preview') and image is not None:
            bio = BytesIO()
            image.save(bio, format='PNG')
            st.download_button(t['download_image'], bio.getvalue(), 'paeleap_visual.png', 'image/png', width='stretch')
            if len(photos)>1:
                bundle=BytesIO()
                with ZipFile(bundle,'w') as archive:
                    for number,p in enumerate(photos,1):
                        data=BytesIO();p['image'].save(data,format='PNG')
                        archive.writestr(f'{number:02d}.png',data.getvalue())
                st.download_button(label('Download ordered photos','按顺序下载全部配图'),bundle.getvalue(),'paeleap_photos.zip','application/zip',width='stretch')

        if workspace == 'image' and image is not None:
            with st.expander(t['prompt']):
                st.code(image_plan.get('image_prompt', ''), language='text')
        if workspace == 'preview' and (variants or image is not None):
            visual_brief = result.get('visual_brief')
            stale = bool(visual_brief and visual_brief['context_fingerprint'] != context_fingerprint(text_plan, selected_caption(st.session_state)))
            if visual_brief:
                st.caption(label('Image brief (not generated): ', '配图方案（未生成）：') + STYLE_LABELS[visual_brief['style_id']][0 if lang=='中文' else 1] + ' · ' + visual_brief['selections']['ratio'])
                if stale:
                    st.warning(label('Caption changed. Return to Image to refresh the brief.', '文案已修改，请返回图片页更新配图方案。'))
