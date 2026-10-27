"""UI snapshot support for caption-only output; engine interfaces stay unchanged."""
from datetime import datetime
import json
from pathlib import Path


def save_caption_output(root, p, variants, elapsed):
    folder = Path(root) / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    folder.mkdir(parents=True, exist_ok=False)
    manifest = dict(plan=p, variants=variants, elapsed_seconds=round(elapsed, 2), review_required=True)
    (folder / 'post.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf8')
    (folder / 'post.txt').write_text('\n\n---\n\n'.join(
        item['title'] + '\n\n' + item['caption'] + '\n\n' + ' '.join(item['hashtags'])
        for item in variants), encoding='utf8')
    return folder


def retain_legacy_plans(result):
    """Keep provenance when an already-open combined result is split for the first time."""
    legacy = result.pop('plan', None)
    if legacy is not None:
        if result.get('variants'):
            result.setdefault('text_plan', legacy)
        if result.get('image') is not None:
            result.setdefault('image_plan', legacy)
