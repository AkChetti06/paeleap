"""Local-only photo validation and state. No generation or external requests."""
from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError
import streamlit as st


def decode_photo(data):
    if len(data) > 20 * 1024 * 1024:
        raise ValueError('Photo exceeds 20 MB')
    try:
        with Image.open(BytesIO(data)) as source:
            if source.width * source.height > 25_000_000:
                raise ValueError('Photo exceeds 25 megapixels')
            source.load()
            return ImageOps.exif_transpose(source).convert('RGB')
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError('Invalid photo') from exc


def clear_photo_if_removed(widget_key):
    if st.session_state.get(widget_key) is None:
        for key in ('image', 'image_source', 'image_plan'):
            st.session_state.get('result', {}).pop(key, None)
        st.session_state.pop('photo_digest', None)


def remove_photo():
    for key in ('image', 'image_source', 'image_plan'):
        st.session_state.get('result', {}).pop(key, None)
    st.session_state.pop('photo_digest', None)
    st.session_state['photo_epoch'] = st.session_state.get('photo_epoch', 0) + 1
