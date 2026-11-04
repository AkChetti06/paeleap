"""Check the actual Streamlit theme resolution without reading credentials."""
import json
import os
from pathlib import Path
import subprocess
import sys


def test_project_light_theme_is_resolved_by_streamlit():
    root = Path(__file__).resolve().parents[1]
    keys = ('base', 'primaryColor', 'backgroundColor', 'secondaryBackgroundColor', 'textColor')
    script = ('import json; from streamlit import config; '
              'print(json.dumps({k: config.get_option("theme." + k) for k in ' + repr(keys) + '}))')
    env = {k: v for k, v in os.environ.items() if not k.startswith('STREAMLIT_THEME_')}
    result = subprocess.run([sys.executable, '-c', script], cwd=root, env=env,
                            capture_output=True, text=True, check=True)
    actual = json.loads(result.stdout)
    assert actual == dict(zip(keys, ('light', '#A45132', '#F7F5F0', '#FFFEFC', '#292C27')))


def test_custom_surfaces_follow_streamlit_theme():
    root = Path(__file__).resolve().parents[1]
    css = (root / 'studio.css').read_text()
    assert ':root:has(.studio-theme-dark)' in css
    assert '--charcoal:#f1eee7' in css and '--surface:#22241f' in css
    assert 'color-scheme:only light' not in css
    assert '@media(max-width:760px)' in css
    assert '--sidebar:#435644' in css
    assert '.st-key-shell_navigation button[kind="primary"]' in css
    assert 'segmented_controlActive' not in css


def test_dark_mode_marker(monkeypatch):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    import dotenv
    monkeypatch.setattr(dotenv, 'load_dotenv', lambda **kw: None)
    original = st.get_option
    monkeypatch.setattr(st, 'get_option', lambda key: 'dark' if key == 'theme.base' else original(key))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
    assert not app.exception
    assert any('<span class="studio-theme-dark"' in block.value for block in app.markdown)


def test_native_session_theme_serializes_fonts_and_sidebar():
    """AppTest does not exercise native new-session theme/font parsing."""
    from streamlit.proto.NewSession_pb2 import CustomThemeConfig
    from streamlit.runtime.app_session import _populate_theme_msg
    theme = CustomThemeConfig()
    _populate_theme_msg(theme)
    _populate_theme_msg(theme.sidebar, 'theme.sidebar')
    assert theme.primary_color == '#A45132'
    assert theme.sidebar.background_color == '#435644'
