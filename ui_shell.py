"""Phase 1 application shell. Future sections are explicit, non-generating views."""
from html import escape
import streamlit as st

SECTIONS = {
    'create': ('Create', '创作', ':material/edit_square:'),
    'projects': ('My Projects', '我的项目', ':material/layers:'),
    'templates': ('Templates', '模板', ':material/grid_view:'),
    'inspiration': ('Inspiration', '灵感', ':material/image:'),
}


def choose_section(section):
    st.session_state['studio_section'] = section


def render_sidebar(cn):
    selected = st.session_state.setdefault('studio_section', 'create')
    with st.sidebar:
        st.markdown('<div class="sidebar-brand"><span class="brand-mark">p.</span><div><b>PAELEAP</b><small>STUDIO</small></div></div>', unsafe_allow_html=True)
        with st.container(key='shell_navigation'):
            for key, (en, zh, icon) in SECTIONS.items():
                st.button(zh if cn else en, icon=icon, key='nav_' + key,
                    type='primary' if selected == key else 'secondary', width='stretch',
                    on_click=choose_section, args=(key,))
        st.markdown('<div class="sidebar-phase">' + ('第一阶段 · 创作工作区' if cn else 'PHASE 1 · CREATE WORKSPACE') + '</div>', unsafe_allow_html=True)
    return selected


def render_heading(cn, section):
    title = '创建旅行内容' if cn else 'Create Travel Content'
    subtitle = ('为所选平台，将目的地转化为图文、图片和视频。' if cn else
                'Turn a destination into posts, images and videos for your selected platform.')
    if section != 'create':
        title = SECTIONS[section][1 if cn else 0]
        subtitle = '即将推出' if cn else 'Coming Soon'
    st.markdown('<div class="shell-heading" lang="' + ('zh-CN' if cn else 'en') + '"><h1>' +
        escape(title) + '</h1><p>' + escape(subtitle) + '</p></div>', unsafe_allow_html=True)


def render_coming_soon(section, cn):
    with st.container(key='coming_soon', border=True):
        st.markdown('### ' + ('即将推出' if cn else 'Coming Soon'))
        names = SECTIONS[section][1 if cn else 0]
        st.write((f'「{names}」将在后续阶段提供。第一阶段仅开放创作工作区。' if cn else
                  f'{names} will be available in a later phase. Only the Create workspace is available in Phase 1.'))
        st.button('返回创作' if cn else 'Back to Create', key='back_to_create', icon=':material/arrow_back:',
            on_click=choose_section, args=('create',), type='primary')
