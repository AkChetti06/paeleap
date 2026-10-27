"""Adapter from detailed offline briefs to the combined studio's result contract."""
import streamlit as st
from template_engine import generate_drafts

INPUT_KEYS = ('input_category', 'example', 'place', 'focus_choices', 'primary_focus',
              'input_case_signature', 'keywords', 'text_style', 'copy_purpose',
              'target_audience', 'learning_stage', 'visit_duration', 'custom_introduction',
              'custom_highlights', 'event_name', 'event_date', 'event_location', 'event_participation')


def preserve_inputs():
    # Detach input widget state from cleanup while another workspace is visible.
    for key in INPUT_KEYS:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]


def has_draft_edits(result):
    for i, variant in enumerate(result.get('variants', [])):
        for part in ('title', 'caption', 'hashtags'):
            original = ' '.join(variant[part]) if part == 'hashtags' else variant[part]
            if st.session_state.get(f'form_draft_{i}_{part}', original) != original:
                return True
    return False


def create_offline_preview(brief):
    copy = generate_drafts(brief, mode='offline')
    variants = [{**v, 'hashtags': copy['hashtags']} for v in copy['versions']]
    previous = st.session_state.get('result', {})
    if previous.get('text_plan') and previous['text_plan'].get('attraction') != brief['attraction']:
        # Avoid carrying a different place's photo or custom subject into the next draft.
        for key in ('image', 'image_source', 'image_plan', 'visual_brief'):
            previous.pop(key, None)
        for key in ('photo_digest', 'form_image_subject', 'portrait_reference', 'portrait_bytes'):
            st.session_state.pop(key, None)
        st.session_state['photo_epoch'] = st.session_state.get('photo_epoch', 0) + 1
    st.session_state['result'] = {**previous,
        'text_plan': {**brief, 'language': '中文'}, 'variants': variants,
        'copy_source': copy['copy_source']}
    st.session_state['form_caption_variant'] = 0
    for i, variant in enumerate(variants):
        for part in ('title', 'caption', 'hashtags'):
            st.session_state[f'form_draft_{i}_{part}'] = ' '.join(variant[part]) if part == 'hashtags' else variant[part]
    st.session_state.pop('pending_offline_brief', None)
