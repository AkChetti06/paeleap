"""Presentation-only destination showcase; never invokes generation providers."""
from hashlib import md5
from html import escape
from urllib.parse import quote

SLIDES = (
    ('West Lake', '西湖', 'West Lake IMG 8756 hangzhou panorama.jpg', 'Bjoertvedt', 'by-sa/4.0'),
    ('Xixi Wetland', '西溪湿地', 'Xixi Wetland Park, Hangzhou, China.jpg', 'Yoshi Canopus', 'by-sa/3.0'),
    ('Leifeng Pagoda', '雷峰塔', 'Leifeng Pagoda 20191102.jpg', 'xiquinhosilva', 'by/2.0'),
)


def render_banner(t, lang):
    slides = []
    for index, (en, cn, filename, author, license_id) in enumerate(SLIDES):
        normalized = filename.replace(' ', '_')
        digest = md5(normalized.encode()).hexdigest()
        image = f'https://upload.wikimedia.org/wikipedia/commons/{digest[0]}/{digest[:2]}/{quote(normalized)}'
        source = 'https://commons.wikimedia.org/wiki/File:' + quote(normalized)
        name = cn if lang == '中文' else en
        slides.append(
            f'<figure class="gallery-slide gallery-slide-{index}">'
            f'<img src="{image}" alt="{escape(name)}" referrerpolicy="no-referrer">'
            f'<figcaption><b>{escape(name)}</b><span>{"杭州" if lang == "中文" else "HANGZHOU"} · {index+1:02d} / 03</span>'
            f'<small><a href="{source}" target="_blank" rel="noopener noreferrer">{escape(author)} · {"维基共享资源" if lang == "中文" else "Wikimedia Commons"}</a> · '
            f'<a href="https://creativecommons.org/licenses/{license_id}/" target="_blank" rel="noopener noreferrer">CC {license_id.upper()}</a>'
            f' · {"画面裁切" if lang == "中文" else "display cropped"}</small></figcaption></figure>'
        )
    return (f'<section class="tourism-gallery" aria-label="{"旅行灵感图库（非生成结果）" if lang == "中文" else "Travel inspiration gallery (not generated content)"}">'
            f'<div class="gallery-fallback">{"旅行灵感 · 摄影图片暂不可用" if lang == "中文" else "Travel inspiration · Photography temporarily unavailable"}</div>'
            f'{"".join(slides)}</section>')


def render_gallery(t, lang):
    """Rotate existing photographs in CSS; no timed reruns or generation requests."""
    import streamlit as st
    with st.container(key='gallery'):
        st.markdown(render_banner(t, lang), unsafe_allow_html=True)
        st.caption('旅行灵感 · 摄影参考，非生成结果' if lang == '中文' else 'TRAVEL INSPIRATION · Photography references, not generated results')
