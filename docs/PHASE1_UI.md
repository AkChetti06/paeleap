# Phase 1 — Studio UI foundation

Branch: `feature/studio-redesign`.

## Scope

The existing Streamlit application now has a native fixed 216px sidebar with
PAELEAP's terracotta `p.` mark and Create, My Projects, Templates and Inspiration.
Create is the only implemented workspace. The other sections explicitly say
Coming Soon and provide a working return action. They do not generate content or
claim to offer storage, browsing or template management.

The Create header uses the requested English copy and its Simplified Chinese
translation. The original three-photo automatic gallery, crossfade timing and
licensing links remain. Beneath it, two matching surfaces contain Content Brief
and Live Preview. Caption, Image and Video retain their existing independent
workflows. Visual direction stays in Image; a named destination is selected once,
with a name input available for custom attractions.

Live Preview now places platform selection in its header, preserves all three
ratio controls, and shows imagery beside directly editable title, caption and
hashtags. Mobile stacks the workspace and post columns and uses the native
sidebar drawer. Caption variants, alternate titles, original images, current
exports, video playback/download and quality review remain available.

## Files

- `.streamlit/config.toml`: native main/sidebar palette, font and border settings.
- `studio.css`: consolidated shell, compact control, gallery and preview geometry.
- `ui_shell.py`: branding, sidebar routing, bilingual headings and Coming Soon views.
- `app.py`: shell integration; existing generation calls and durable input keys retained.
- `ui_results.py`: post composition, platform placement and export presentation.
- `ui_video.py`: modern width argument only; existing video behavior retained.
- `tests/`: adapted UI assertions plus new shell/navigation state regressions.

No backend API, provider settings, image-export math or generation logic was
rewritten. Existing source drafts and originals remain separate from edited
export data. Navigation state is independent of durable `form_*` values and
results, so visiting Coming Soon sections does not erase drafts.

## Validation

The pre-change suite passed 77 tests. The updated suite passes 83 tests, including
all prior generation/provider error cases, local FFmpeg encoding/decoding, and
new checks for bilingual sidebar navigation, explicit Coming Soon states and
retention of caption edits, custom destination, brief inputs, style, image, video,
selected platform and ratio. `pip check` reports no broken requirements.

Desktop/mobile browser review is complete in English and Simplified Chinese at
1440, 1280, 768 and 375px, covering both empty and populated previews. Checked
collapsed/open mobile navigation, all Coming Soon views, image upload, mocked
caption/image generation, preserved edits, platform/ratio changes and real
PNG/JSON/MP4 downloads. The selected 9:16 PNG and MP4 decoded at 1080 × 1920;
the video duration was 9 seconds. The local FFmpeg renderer was exercised with
mocked images; live generation providers were not called.

Visual review corrected blank radio-label bars, native toolbar overlap and
reserved space beside the collapsed sidebar. Runtime review also caught and
corrected a native Streamlit font-URL restriction: the native font source now
contains one family, while CSS loads the Chinese fallback. A new regression
test validates native session-theme serialization, which AppTest alone does
not exercise. No horizontal overflow or browser page errors remained in the
final layout checks.

Physical-device/Safari review and live provider availability remain manual
checks. These do not block the Phase 1 implementation.

## Run

```sh
source .venv/bin/activate
streamlit run app.py
```

Templates, Inspiration and My Projects are reserved for later phases. No commit,
push or merge is part of this work.
