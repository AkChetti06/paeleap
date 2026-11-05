"""Video workspace: build local slideshows from generated or user-provided images.

This does not synthesize motion with an AI video model. Never silently call a paid
provider when the user selects their own photos.
"""
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

import engine
from platform_config import PLATFORM_CONFIG, FORMATS, export_image


_MAX_PHOTO_BYTES = 20_000_000
_MAX_PHOTOS = 5


def _read_photos(uploads):
    """Decode safe, bounded copies; never alter the uploaded originals."""
    photos = []
    for upload in uploads:
        if upload.size > _MAX_PHOTO_BYTES:
            raise ValueError('Each photo must be under 20 MB / 每张照片不能超过 20 MB。')
        try:
            with Image.open(BytesIO(upload.getvalue())) as source:
                if source.width * source.height > 40_000_000:
                    raise ValueError('Photo dimensions are too large / 照片尺寸过大。')
                photo = ImageOps.exif_transpose(source).convert('RGB')
                photo.load()
        except (OSError, UnidentifiedImageError) as exc:
            raise ValueError('Could not read the photo / 无法读取照片。') from exc
        photos.append(photo)
    return photos


def render_video_controls(label, lang, platform, ratio, setting):
    result = st.session_state.get('result', {})
    with st.container(key='video_controls'):
        st.markdown('<div class="brief-section">' + label('Create a short video', '创作短视频') + '</div>', unsafe_allow_html=True)
        if result.get('image') is None:
            st.info(label('Go to the Image tab to generate an image or upload a photo first.',
                          '请先前往「图片」标签生成图片或上传照片。'))
            return

        p = result.get('image_plan', result.get('plan', {}))
        st.caption(f"{PLATFORM_CONFIG[platform]['labels'][lang]} · {ratio} · {FORMATS[ratio][0]} × {FORMATS[ratio][1]}")
        st.caption(label('Create a silent MP4 slideshow. This is not an AI animated video.',
                         '制作无声 MP4 幻灯视频；此功能不生成 AI 动画。'))
        uploaded_cover = p.get('source') == 'uploaded_photo'
        modes = ['photos'] if uploaded_cover else ['photos', 'cloudflare']
        mode = st.radio(label('Video source', '视频素材来源'), modes, horizontal=True,
            format_func=lambda key: label('Use my photos', '使用我的照片') if key == 'photos'
                else label('Generate extra images', '生成更多图片'),
            key='video_source')
        additional = []
        if mode == 'photos':
            additional = st.file_uploader(label('Add 1–5 more photos (PNG, JPEG or WebP)', '添加 1–5 张照片（PNG、JPEG 或 WebP）'),
                type=['png', 'jpg', 'jpeg', 'webp'], accept_multiple_files=True, key='video_extra_photos')
            st.caption(label('Your current cover is the first frame. Extra photos stay in the order selected; no AI image calls are made.',
                             '当前封面为首帧；其余照片按选择顺序播放，不调用 AI 图片接口。'))
            if len(additional) > _MAX_PHOTOS:
                st.warning(label('Choose no more than five additional photos.', '最多只能选择五张额外照片。'))
        else:
            st.caption(label('Creates two extra Cloudflare concept images and uses additional API quota.',
                             '通过 Cloudflare 生成两张额外概念图，会消耗额外 API 额度。'))

        seconds = st.slider(label('Seconds per image', '每张图片展示秒数'),
                            min_value=1, max_value=10, value=3, key='video_seconds')
        count = 1 + (len(additional) if mode == 'photos' else 2)
        st.caption(label(f'{count} frames · {count * seconds} seconds · silent MP4',
                         f'{count} 帧 · {count * seconds} 秒 · 无声 MP4'))
        invalid_photos = mode == 'photos' and not 1 <= len(additional) <= _MAX_PHOTOS
        if st.button(label('Create short video', '生成短视频'), key='generate_video',
                     type='primary', disabled=invalid_photos, width='stretch'):
            try:
                with st.spinner(label('Rendering video…', '正在渲染视频…')):
                    frames = [result['image']]
                    if mode == 'photos':
                        frames.extend(_read_photos(additional))
                    else:
                        frames.extend(engine.generate_cloudflare_image(
                            frame_plan, setting('CLOUDFLARE_ACCOUNT_ID'), setting('CLOUDFLARE_API_TOKEN'))
                            for frame_plan in engine.video_plans(p)[1:])
                    video = engine.render_slideshow(frames, seconds_per_image=seconds, aspect_ratio=ratio)
                    if result.get('folder'):
                        (Path(result['folder']) / 'slideshow.mp4').write_bytes(video)
                    result['video'] = video
                    result['video_format'] = (platform, ratio)
                    result['video_details'] = dict(mode=mode, frames=len(frames),
                                                   duration_seconds=len(frames) * seconds)
                    st.success(label('Video created. Download it from the preview.', '视频已生成，请在预览区下载。'))
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
        details = result.get('video_details', {})
        if details:
            st.caption(label(f"{details['frames']} frames · {details['duration_seconds']} seconds",
                             f"{details['frames']} 帧 · {details['duration_seconds']} 秒"))
        st.download_button(label('Download video', '下载视频'), result['video'], 'paeleap_slideshow.mp4', 'video/mp4')
    elif result.get('image') is not None:
        st.caption(label('Your existing cover · create a video using the controls on the left.', '现有封面 · 使用左侧控件生成视频。'))
        with st.container(key='composition_' + ratio.replace(':', '_')):
            st.image(export_image(result['image'], ratio), width='stretch')
    else:
        st.info(label('No video yet. Start with an image in the Image tab.', '暂无视频，请先在「图片」标签准备图片。'))
