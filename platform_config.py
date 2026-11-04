"""Editable platform presets shared by still exports, slideshows and future video."""
from PIL import Image, ImageOps

FORMATS = {'3:4': (1080, 1440), '9:16': (1080, 1920), '1:1': (1080, 1080)}
PLATFORM_CONFIG = {
    'xiaohongshu': dict(labels={'English': 'Xiaohongshu', '中文': '小红书'}, ratio='3:4',
        content_format='editorial image post', caption_structure='Destination-led title, short discovery paragraphs, relevant hashtags',
        export=dict(format='PNG', composition='contain'), video=dict(mode='slideshow', preferred=False)),
    'douyin': dict(labels={'English': 'Douyin', '中文': '抖音'}, ratio='9:16',
        content_format='portrait video cover and short video', caption_structure='Brief opening hook, concise highlight beats, viewer question and relevant hashtags',
        export=dict(format='PNG', composition='contain'), video=dict(mode='slideshow', preferred=True)),
    'weibo': dict(labels={'English': 'Weibo', '中文': '微博'}, ratio='1:1',
        content_format='square image post', caption_structure='Concise destination update, highlight paragraphs and topical hashtags',
        export=dict(format='PNG', composition='contain'), video=dict(mode='slideshow', preferred=False)),
}


def export_image(image, ratio):
    """Fit the entire original within a neutral canvas: no crop or distortion."""
    if ratio not in FORMATS:
        raise ValueError('Unknown format / 未知图片比例')
    source = ImageOps.exif_transpose(image).convert('RGBA')
    if source.width < 1 or source.height < 1:
        raise ValueError('Empty image')
    fitted = ImageOps.contain(source, FORMATS[ratio], Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', FORMATS[ratio], '#f4f1eb')
    canvas.paste(fitted, ((canvas.width-fitted.width)//2, (canvas.height-fitted.height)//2), fitted)
    return canvas


TEMPLATE_LIBRARY = {
    'ancient_town': dict(name='Traditional Editorial / 人文纪实',
        title='[attraction] | [interest], observe [highlight count] details',
        sections=['Specific reason to visit', 'Supplied highlights: one observation each', 'Who it suits', 'Natural question'],
        image_order='Primary highlight first, then matching highlights in supplied order', hashtags='attraction, heritage, ancient town travel'),
    'natural_scenery': dict(name='Natural Fresh / 自然清新',
        title='[attraction] | [audience/interest] [theme] notes',
        sections=['Mood or audience', 'Specific supplied scenery', 'How to appreciate it', 'Practical reminder'],
        image_order='Main scenery, matching highlight images, reminder only if material exists', hashtags='attraction, scenery, nature'),
    'theme_park': dict(name='Vibrant Experience / 活力体验',
        title='[park] experiences: [highlight count] highlights for [audience]',
        sections=['Companion needs', 'Supplied experiences: what and for whom, only if known', 'Planning reminder', 'Preferred experience question'],
        image_order='Main experience, matching highlight images, reminder only if material exists', hashtags='attraction, park experience, supplied theme'),
}
