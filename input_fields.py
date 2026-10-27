"""Input fields only. No page configuration, columns, menu or output layout.

Integration contract: render_input_fields() -> serializable brief or None.
Generate with template_engine.generate_drafts(brief, mode='offline').
"""
import streamlit as st
from template_engine import list_attractions, load_attraction
from promotional_brief import (CATEGORIES, CASE_CATEGORIES, CATEGORY_GUIDANCE, STYLES,
    PURPOSES, AUDIENCES, STAGES, DURATIONS, case_highlights, parse_highlights, build_detailed_brief)

CUSTOM = '其他场所（填写资料）'
CASES = {c['name']: c for c in list_attractions()}


def _change_category():
    names = [n for n, c in CASES.items() if CASE_CATEGORIES[c['category']] == st.session_state['input_category']]
    st.session_state['example'] = names[0] if names else CUSTOM
    _change_example()


def _change_example():
    name = st.session_state['example']
    st.session_state['place'] = name if name in CASES else ''
    for key in ('focus_choices', 'primary_focus', 'input_case_signature', 'pending_brief'):
        st.session_state.pop(key, None)
    st.session_state['keywords'] = ''
    for key in ('custom_introduction', 'custom_highlights', 'event_name', 'event_date', 'event_location', 'event_participation'):
        st.session_state.pop(key, None)


def render_input_fields(language="中文"):
    from input_labels import LocalizedFields
    ui = LocalizedFields(language)
    st.session_state.setdefault('input_category', '古镇／历史街区')
    ui.selectbox('景区类型', CATEGORIES, key='input_category', on_change=_change_category)
    category = st.session_state['input_category']
    examples = [n for n, c in CASES.items() if CASE_CATEGORIES[c['category']] == category]
    examples.append(CUSTOM)
    if st.session_state.get('example') not in examples:
        st.session_state['example'] = examples[0]
        _change_example()
    ui.selectbox('你想推广哪里？', examples, key='example', on_change=_change_example)
    if st.session_state['example'] == CUSTOM:
        st.session_state.setdefault('place', '')
        name = ui.text_input('场所名称', key='place', max_chars=80, placeholder='填写景点或场所名称')
    else:
        name = st.session_state['example']
    data = None
    try:
        candidate = load_attraction(name)
        if CASE_CATEGORIES[candidate['category']] == category:
            data = candidate
        else:
            ui.warning('这个景点的已有资料属于' + CASE_CATEGORIES[candidate['category']] + '，请先切换景区类型。')
            return None
    except ValueError:
        pass
    introduction = ''
    highlights = []
    input_error = None
    if data:
        highlights = case_highlights(data)
    else:
        ui.info('这个场所暂无匹配资料，请补充简介与真实亮点。填写内容将直接用于离线文案，不会自动查询或核验。')
        introduction = ui.text_area('场所简介', key='custom_introduction', max_chars=600,
                                   placeholder='写清场所是什么、有哪些已确认的特色。')
        raw = ui.text_area('候选亮点：一行一个“名称｜具体说明”', key='custom_highlights',
                           placeholder='例如填写已确认的' + CATEGORY_GUIDANCE[category][0], max_chars=4300)
        try:
            highlights = parse_highlights(raw)
        except ValueError as exc:
            input_error = str(exc)
    style = ui.selectbox('文本风格', STYLES, key='text_style',
                         help='简洁：短句直述；活泼：轻松口语；严肃：稳重说明。')
    purpose = ui.selectbox('推文目的', PURPOSES, key='copy_purpose')
    audience = ui.selectbox('目标人群', AUDIENCES, key='target_audience')
    stage = '不限定'
    if audience == '学生／研学团体':
        stage = ui.selectbox('学习阶段（选填）', STAGES, key='learning_stage')
    duration = '不限定'
    if purpose == '游玩攻略':
        duration = ui.selectbox('计划游玩时长（选填）', DURATIONS, key='visit_duration',
                                help='用于建议取舍看点，不会据此编造路线或承诺游览耗时。')
    event = None
    if purpose == '活动宣传':
        ui.caption('活动文案需要以下四项信息；仅使用你填写的内容。')
        event = {key: ui.text_input(label, key='event_' + key, max_chars=300)
                 for key, label in [('name', '活动名称'), ('date', '活动日期／时间'),
                                    ('location', '活动地点'), ('participation', '参与方式')]}
    options = [h['label'] for h in highlights]
    signature = (data['name'] if data else name, category, tuple(options))
    if st.session_state.get('input_case_signature') != signature:
        st.session_state['focus_choices'] = options[:2]
        st.session_state.pop('primary_focus', None)
        st.session_state['input_case_signature'] = signature
    selected = ui.multiselect('本篇推广重点（选1至3项）', options, key='focus_choices', max_selections=3)
    if st.session_state.get('primary_focus') not in selected:
        st.session_state['primary_focus'] = selected[0] if selected else None
    primary = ui.selectbox('最想突出的一个重点', selected, key='primary_focus', disabled=not selected,
                           help='这个重点会进入标题和开头，其余选择作为支持内容。')
    supplement = ui.text_area('补充事实（选填）', key='keywords', max_chars=600,
                              help='会原样放入“补充信息”，请填真实信息，不要在此填写写作指令；语气与目的使用上面的选项。')
    if input_error:
        ui.warning(input_error)
        return None
    try:
        return build_detailed_brief(name=data['name'] if data else name, category=category,
            style=style, purpose=purpose, audience=audience, highlights=highlights,
            selected=selected, primary=primary, data=data, introduction=introduction,
            supplement=supplement, stage=stage, duration=duration, event=event)
    except ValueError as exc:
        ui.warning(str(exc))
        return None
