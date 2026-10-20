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
            f'<figure class="destination-slide slide-{index}">'
            f'<img src="{image}" alt="{escape(en + " / " + cn)}" referrerpolicy="no-referrer">'
            f'<figcaption><b>{escape(name)}</b><span>HANGZHOU / 杭州 · {index+1:02d} / 03</span>'
            f'<small><a href="{source}" target="_blank" rel="noopener noreferrer">{escape(author)} · Wikimedia Commons</a> · '
            f'<a href="https://creativecommons.org/licenses/{license_id}/" target="_blank" rel="noopener noreferrer">CC {license_id.upper()}</a>'
            f' · {"画面裁切" if lang == "中文" else "display cropped"}</small></figcaption></figure>'
        )
    pause = '暂停轮播' if lang == '中文' else 'Pause slideshow'
    return (f'<section class="hero destination-hero" aria-label="Hangzhou destination showcase">'
            f'<input class="carousel-pause" type="checkbox" id="pause-destinations">'
            f'<label class="carousel-control" for="pause-destinations">Ⅱ {pause}</label>'
            f'<div class="destination-images">{"".join(slides)}</div>'
            f'<div class="hero-copy"><div class="hero-label">{escape(t["eyebrow"])}</div>'
            f'<div class="hero-title">{escape(t["headline"])}</div>'
            f'<div class="hero-sub">{escape(t["subhead"])}</div></div></section>')
