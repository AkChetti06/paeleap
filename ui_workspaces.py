"""Presentation-only workspace navigation; stable IDs preserve shared state."""
import streamlit as st


def render_navigation(cn):
    labels = {'text': '文案', 'image': '图片', 'preview': '预览'} if cn else {
        'text': 'Caption', 'image': 'Image', 'preview': 'Preview'}
    return st.radio('工作区' if cn else 'Workspace', list(labels),
                    format_func=labels.get, horizontal=True, width='stretch',
                    label_visibility='collapsed', key='workspace')
