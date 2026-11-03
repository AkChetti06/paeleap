# Creator Studio UI verification

Date: 3 November 2026. Branch: `feature/week4-image-to-video`.

## Scope and preservation

The redesign changes `app.py`, `studio.css`, `ui_results.py` and `ui_banner.py`.
It adds `tests/test_redesign.py` and updates the README. Pre-existing uncommitted
platform, template, state and backend work was retained. No reset, commit, push
or merge was performed. The generation engine and provider contracts were not
changed for this redesign.

The desktop workspace uses 42/58 columns, white surfaces, grouped controls and
one shared post canvas. Mobile stacks controls above the canvas. Caption and
Image generation stay independent; Preview retains all editing controls. Current
edits are reflected in every workspace and its downloads. Formats remain
platform presets with per-platform overrides in a compact popover. The optional
200px gallery retains all three original image-source and Creative Commons links.

## Automated checks

`python -m pytest -q`: **67 passed**. The existing environment emits one urllib3
LibreSSL compatibility warning. The suite covers bilingual form state, platform
and template presets, image dimensions and composition, caption variants and
edits, provider failures, original-result retention, downloads, and real local
FFmpeg slideshow encoding/decoding. New tests cover the shared post canvas,
per-platform format popover state, and optional gallery licensing links.

`git diff --check`: passed.

## Rendered browser checks

An isolated headless Google Chrome session opened the actual Streamlit app on
127.0.0.1. Empty-state screenshots and layout measurements covered 1440, 1280,
1024, 768, 430 and 375px in English and Chinese. Populated previews were checked
at 1440, 768, 430 and 375px in both languages. The populated session used a
separate temporary QA harness with local fixture imagery and mocked generation;
it did not call a paid provider or change repository source to inject demo data.

Verified:

- Desktop columns share a top alignment and use white surfaces; mobile stacks.
- Plus Jakarta Sans / Noto Sans SC font stacks are applied, with system fallbacks.
- The platform selector retains native keyboard focus and arrow-key selection.
- Language and platform switches preserve edited titles and the current image.
- Final checks found no visible input, button or image overflow and no page errors.
- A real downloaded JSON file retained the edited title and platform metadata.
- A real downloaded PNG reopened at 1080 × 1440 for the Xiaohongshu preset.
- English and Chinese caption actions updated the shared preview using mocks.
- Mobile header click interception and fixed-width image-container clipping
  found during screenshot review were corrected and rechecked.

## Remaining manual review

- Review the visual balance on the mentor's actual laptop and a physical phone,
  including Safari and touch keyboard behavior; Chrome emulation is not a device.
- Confirm web-font loading and optional Wikimedia photography on the presentation
  network. The interface includes font fallbacks and a photography fallback.
- Live caption/image provider permissions, quota and output quality were not
  exercised. The existing real local slideshow tests pass; browser generation
  used mocks to avoid credit usage.

Run the production interface from the repository with:

```sh
source .venv/bin/activate
streamlit run app.py
```

## Targeted gallery and ratio-control follow-up

The destination reel is restored directly below the header using `ui_banner.py`,
its original three photographs, attribution links and 15-second automatic cycle.
All three photographs loaded in browser checks, and the active slide changed
automatically. Mobile attribution receives enough height to wrap.

The format dropdown/popover is removed. Exactly three native single-choice radio
segments now appear at the top of Live Preview: 3:4, 9:16 and 1:1 with their pixel
dimensions. Platform changes reset the active ratio to the new platform default;
manual overrides persist through language switches, workspace changes and reruns.
Preview and export fit the complete original into the selected canvas with padding.
No generation API calls are made by ratio changes; caption edits remain intact.

Verification: **68 tests passed**, including UI capture of preview images and actual
PNG/JSON download data for each ratio. Headless Chrome checked all three ratios at
1440, 768 and 375px in English/Chinese with no page errors. Downloaded PNGs were
reopened and confirmed as 1080 × 1440, 1080 × 1920 and 1080 × 1080 at every width.
Desktop preview dimensions were 360 × 480, 360 × 640 and 360 × 360 respectively;
mobile previews scaled proportionally to their available width. Generation was
mocked for browser preview checks; the production providers were not invoked.

## Video tab integration

Content Brief now has Caption / Image / Video (文案 / 图片 / 视频), with the
existing neutral selected-state design and three equal-width segments. Video
controls are rendered only in Content Brief's Video tab; no Short video expander
remains. Live Preview displays the saved video and its MP4 download in Video,
while the existing caption/image canvas stays available in the other tabs.

The slideshow services are unchanged. Explicit generation reuses the saved cover
and requests only the two additional frames. Missing images produce guidance
without an API call. The existing uploaded-photo limitation is retained. Failure
keeps the previous successful video and image; tab/language switches preserve
brief inputs, caption edits and outputs.

Validation: **75 tests passed**; `git diff --check` passed. Added regressions for
empty-video behavior, exact tab labels, bilingual controls, saved cover reuse,
MP4 downloads, format changes, edit persistence and image/render failures. Chrome
checks at 1440 and 375px found equal segment widths in both languages and no page
errors. A local run with mocked image generation exercised the real FFmpeg
renderer; its downloaded MP4 decoded as 1080 × 1440, duration 9.0 seconds. Browser
checks waited for Streamlit reruns before asserting saved edits. No paid provider
requests were made during verification.
