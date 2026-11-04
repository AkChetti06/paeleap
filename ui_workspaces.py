"""Presentation-only workspace navigation; stable IDs preserve shared state."""
import streamlit as st


def render_navigation(cn):
    labels = {'text': '文案', 'image': '图片', 'video': '视频'} if cn else {
        'text': 'Caption', 'image': 'Image', 'video': 'Video'}
    selected = st.session_state.get('durable_workspace', 'text')
    # Existing sessions may still have the removed Preview tab selected.
    if selected not in labels:
        selected = 'text'
        st.session_state['durable_workspace'] = selected
    st.session_state['workspace'] = selected
    def remember():
        st.session_state['durable_workspace'] = st.session_state['workspace']
    return st.radio('工作区' if cn else 'Workspace', list(labels),
                    format_func=labels.get, horizontal=True, width='stretch',
                    label_visibility='collapsed', key='workspace', on_change=remember)
