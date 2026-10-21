# PAELEAP Xiaohongshu Post Generator

Streamlit tourism studio with editable bilingual captions, Cloudflare concept imagery and a local slideshow video. It does not verify travel facts or publish posts.

## Run locally

Use Python 3.11 or 3.12 and run from this repository:

```sh
python -m pip install -r requirements.txt
cp .env.example .env
# Fill in .env locally; never commit credentials.
python -m streamlit run app.py
```

Required server settings (environment variables take precedence over Streamlit secrets):

- `CLOUDFLARE_ACCOUNT_ID`: the 32-character account ID.
- `CLOUDFLARE_API_TOKEN`: token with Workers AI access for that account.
- `TEXT_API_KEY`, `TEXT_BASE_URL`: the existing OpenAI-compatible chat-completions integration.
- `TEXT_MODEL`: text model name, default `qwen-plus`.

Cloudflare credentials never enter widgets, prompts, downloads or result state. Provider response bodies and SDK exception details are not displayed. `.env` and `.streamlit/secrets.toml` are git-ignored. Do not paste credentials into attraction names or keywords.

## Operator workflow

1. Select EN or 中文 with the visible language control.
2. Choose a destination or enter your own attraction. Select a category and visual direction, and optionally set the audience, creative angle and keywords.
3. Generate an image and three caption variants; edit each title, caption and hashtags in its tab. Download a caption, PNG or JSON containing all edited variants.
4. Optionally create a short video. This reuses the cover, requests two more images from Cloudflare and assembles a silent 9-second portrait slideshow. Download the MP4.
5. Review imagery, captions and factual claims before publishing. The optional quality review and export remain available.

The EN | 中文 control uses a native single-choice radio styled as adjacent segments, so there is always one active language. Stable destination, category and style IDs and durable form state preserve selections across translated labels and reruns. Predefined destination names and untouched audience defaults translate; user-entered text is never translated. A language change preserves existing caption edits and shows a reminder to regenerate. New outputs use the selected language; existing drafts retain their original language. Keywords are unverified context, not factual evidence. Captions prohibit invented visits, prices, hours, events and routes. Human review is still needed because model compliance cannot be guaranteed. Missing credentials, invalid text JSON or repeated variants produce errors; no placeholder or template is substituted. Successful drafts survive generation failures.

## Category recommendations

| Category | Internal style | Palette | Template focus |
| --- | --- | --- | --- |
| 古镇 / Ancient Town | Traditional Editorial | Warm ochre, muted terracotta, ink gray | Respectful heritage illustration |
| 自然风光 / Natural Scenery | Cinematic Landscape | Sage green, lake blue, soft ivory | Serene landscape illustration |
| 主题乐园 / Theme Park | Vibrant & Playful | Coral red, sunny yellow, sky blue | Playful illustration without invented rides or mascots |

`CATEGORY_CONFIG` in `engine.py` is the single source for category labels, validation, recommended style, palette and template. All four original visual directions remain manually selectable, including Cyberpunk Neon. Each style has an English and Simplified Chinese display name. Category templates and palettes remain category-specific when a style is overridden. There is no image-provider fallback. `app.py` handles UI and server settings; `engine.py` owns generation, response validation, rendering and output snapshots; `studio.css` and `ui_banner.py` handle presentation. The original editorial panels, category cards, responsive columns, banner, typography and light palette remain. Dark mode uses paired foregrounds and surfaces inferred from Streamlit context, with the configured theme as a first-render fallback.

## Video prerequisites and limits

`imageio-ffmpeg>=0.6,<0.7` supplies a local FFmpeg executable on supported wheel platforms, including standard Linux Community Cloud environments. The renderer needs a working H.264 (`libx264`) encoder, writable temporary storage and enough CPU to encode 720×960 at 24 fps. It uses one encoder thread and a 120-second timeout; temporary images are cleaned up. If your platform has no bundled executable, install FFmpeg and set server-side `IMAGEIO_FFMPEG_EXE` to its absolute path. No MoviePy or system package is required on platforms with a bundled binary.

The slideshow is image sequencing, not generative scene motion; there is no audio. Video generation makes two additional image API calls and consumes extra quota. Shared category style, palette and scene context encourage consistency, but separate images can differ in geometry or content. The original PNG retains its returned dimensions; the video fits images into a portrait canvas without stretching or cropping.

The configured [Cloudflare FLUX.1-schnell model](https://developers.cloudflare.com/workers-ai/models/flux-1-schnell/) accepts prompt and steps and returns a Base64 image. This integration uses four steps. Its contract does not provide text generation, video generation, seed locking, reference-image consistency controls or width/height selection. Portrait composition in the prompt is not an aspect-ratio guarantee. Captions continue to use the separate text API. No claims of live API verification or free/unlimited usage are made.

## Testing and deployment checklist

- Install dependencies and run `python -m pytest -q` (mocked provider contracts, language/UI edits, errors, category mapping and real local MP4 encoding/decoding).
- Run `python -m pip check` and start Streamlit locally; check narrow/wide layouts and both themes.
- In Streamlit Community Cloud, choose `app.py`, Python 3.11/3.12 and repository `requirements.txt`.
- Add the required settings to **App settings → Secrets**, using TOML strings, e.g. `TEXT_MODEL = "qwen-plus"`. Never commit the real secrets file.
- Reboot after dependency/secrets changes. Test one generation in each language, all three categories, editing/downloads and the video button using your configured accounts.
- Check account permissions, quota, generated-content accuracy and MP4 playback. Live image/text services require credentials and are not exercised by unit tests.

Original generation snapshots are written to `outputs/`; edits are reflected in downloads, while source variants remain in JSON. Community Cloud storage is ephemeral: download results before a restart. Image and caption generation are committed together only on success. A failed video keeps the image and captions available; retrying video makes fresh image calls.
