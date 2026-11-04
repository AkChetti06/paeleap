"""Video workspace presentation; reuse the existing image and slideshow services."""
from pathlib import Path
import streamlit as st
import engine
from platform_config import PLATFORM_CONFIG, FORMATS, export_image


def render_video_controls(label, lang, platform, ratio, setting):
    result = st.session_state.get('result', {})
    with st.container(key='video_controls'):
        st.markdown('<div class="brief-section">' + label('Create a short video', '创作短视频') + '</div>', unsafe_allow_html=True)
        if result.get('image') is None:
            st.info(label('Go to the Image tab to generate an image or upload a photo first. No images are generated automatically.',
                          '请先前往「图片」标签生成图片或上传照片。系统不会自动生成图片。'))
            return
        p = result.get('image_plan', result.get('plan', {}))
        st.caption(label('Reuses your existing cover and generates two additional Cloudflare images, using additional quota.',
                         '复用现有封面，另生成两张 Cloudflare 图片，会使用额外额度。'))
        st.caption(f"{PLATFORM_CONFIG[platform]['labels'][lang]} · {ratio} · {FORMATS[ratio][0]} × {FORMATS[ratio][1]}")
        uploaded = p.get('source') == 'uploaded_photo'
        if uploaded:
            st.info(label('The existing AI slideshow needs a generated concept image. Generate one in the Image tab; your uploaded photo is preserved until you replace it.',
                          '现有 AI 幻灯视频需要生成的概念图片。请在「图片」标签生成概念图；替换前会保留上传的照片。'))
        if st.button(label('Create short video', '生成短视频'), key='generate_video', type='primary', disabled=uploaded):
            try:
                with st.spinner(label('Creating two images and rendering video…', '正在生成两张图片并渲染视频…')):
                    frames = [result['image']]
                    for frame_plan in engine.video_plans(p)[1:]:
                        frames.append(engine.generate_cloudflare_image(frame_plan, setting('CLOUDFLARE_ACCOUNT_ID'), setting('CLOUDFLARE_API_TOKEN')))
                    video = engine.render_slideshow([export_image(frame, ratio) for frame in frames], aspect_ratio=ratio)
                    if result.get('folder'):
                        (Path(result['folder']) / 'slideshow.mp4').write_bytes(video)
                    result['video'] = video
                    result['video_format'] = (platform, ratio)
            except Exception as exc:
                st.error(engine.safe_error(exc, lang))
                if result.get('video'):
                    st.caption(label('Your previous video is retained.', '已保留上次生成的视频。'))


def render_video_preview(label, platform, ratio):
    result = st.session_state.get('result', {})
    if result.get('video'):
        if result.get('video_format', (platform, ratio)) != (platform, ratio):
            st.info(label('Showing your saved video in its original format. Create a new video to apply the current platform and ratio.',
                          '当前显示已保存视频的原始格式。重新生成视频可应用当前平台和画幅。'))
        st.video(result['video'])
        st.download_button(label('Download video', '下载视频'), result['video'], 'paeleap_slideshow.mp4', 'video/mp4')
    elif result.get('image') is not None:
        st.caption(label('Your existing cover · create a video using the controls on the left.', '现有封面 · 使用左侧控件生成视频。'))
        with st.container(key='composition_' + ratio.replace(':', '_')):
            st.image(export_image(result['image'], ratio), width='stretch')
    else:
        st.info(label('No video yet. Start with an image in the Image tab.', '暂无视频，请先在「图片」标签准备图片。'))
