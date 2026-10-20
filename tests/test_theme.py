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
    assert actual == dict(zip(keys, ('light', '#a34f30', '#f8f6f1', '#eae4d9', '#33332f')))
