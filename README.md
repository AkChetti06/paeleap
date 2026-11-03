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

Cloudflare is now supported alongside Hugging Face, Alibaba Wan and the offline demo.

1. Create/sign into [Cloudflare](https://dash.cloudflare.com/). Open **Workers AI** and choose **Use REST API**. Create the **Workers AI API Token** and copy your **Account ID**. Follow [Cloudflare's guide](https://developers.cloudflare.com/workers-ai/get-started/rest-api/).
2. In Terminal inside this project: `cp .env.example .env` (skip if `.env` already exists), then `open -e .env` on macOS.
3. Add `CLOUDFLARE_ACCOUNT_ID=...` and `CLOUDFLARE_API_TOKEN=...`; save. Don't publish `.env`.
4. Install with `python -m pip install -r requirements.txt` and start with `python -m streamlit run app.py`.
5. Choose **Cloudflare Workers AI** in the image engine menu and create a post.

The app uses `@cf/black-forest-labs/flux-1-schnell`, with four diffusion steps. Its API returns a Base64 image in JSON. Free tier currently has a **10,000 neurons/day shared allowance**, not unlimited generations; eligibility, capacity and account restrictions still apply. Verify current terms at https://developers.cloudflare.com/workers-ai/platform/pricing/.

### Provider status and fallback
The new **Provider configuration** expander reports whether credentials are **present**, not whether accounts have credit or API access. The **Automatic fallback** selector defaults to **No fallback**, so no alternative provider is invoked without your consent. You can explicitly select another configured provider. This may consume paid credits. Offline demo remains a non-AI placeholder and is never automatically substituted after a failed live request. Do not present it as generated output.

### Troubleshooting
- HTTP 401/403: check account ID and Workers AI token permission.
- HTTP 402: billing/credit restriction; review dashboard.
- HTTP 429: request rate or daily quota limit; try later.
- Hugging Face HTTP 402: your inference credits have run out; select Cloudflare instead.
- If the provider reports a problem but your current post preview persists, that preview is the **previous successful output**.

The project remains a **Week 2 mini-project prototype**, not a verified travel-guide publisher. Generated imagery is labeled illustrative, and location claims require review. Live API requests could not be tested without user credentials.

## Week 2 refinement — v4 (20 October 2026)

- Offline captions now use the **audience** and optional **story angle** inputs, instead of ignoring them. Their output is explicitly a *template*, not an AI caption.
- After generation, the **title, caption and hashtags are editable** in the preview; text and JSON downloads include the edited version. `source_copy` in the JSON preserves the original generator output for comparison.
- Selecting LLM caption mode **without credentials gives an explicit configuration error**, not an unannounced template fallback.
- Added tests for personalized offline copy and missing-credential handling (10 passing unit tests).
- Existing external image providers remain available but were **not tested against live accounts** in this environment; local tests mock API responses.
- The project is still a **Week 2 one-post mini-project**, not a production-ready publisher.

### How to demo for Week 2

1. Install requirements; create `.env` locally using `.env.example` (do not share it).
2. Start `python -m streamlit run app.py`.
3. Select 杭州西湖, set the audience and a story angle. Start with offline image and caption modes.
4. Generate the draft, edit it in the right pane, and download the text and JSON.
5. Optionally select an image provider **only if a token/quota has been configured**; record API success or failure in the report.
6. Use the resulting screenshot, saved manifest, and your own manual review observations in your Week 2 mini-project report.

### Remaining limitations

The app does not verify attraction facts or publish to Xiaohongshu. Demo images are visibly marked placeholders. Changing copy in the browser updates downloads, but not the original `outputs/` snapshot, which remains useful for documenting the initial generation. Visual/manual scoring is subjective, and provider tests are mocked rather than live.

## v5 UI changes (Week 2)
- Removed the provider-configuration and Week 1 evidence accordions and the two explanatory captions under generation controls.
- Studio/Preview headings no longer use numeric prefixes.
- Visual direction is suggested based on selected attraction/category and remains fully overridable. Changing the attraction, category or story angle updates the suggestion; ordinary reruns and audience changes preserve manual style choice.
- The generated image and always-editable title, caption and hashtags display together. There is no edit button. Downloads reflect edits.
- The image remains a clearly identified demo placeholder or illustrative AI-generated concept (not a verified photograph).
# paeleap


## Week 2 generation improvements

- Chinese AI captions request a concrete, truthful title, natural short paragraphs, useful viewing suggestions, and 4–6 relevant unique hashtags. The brief is context, not verified factual evidence; no live facts are retrieved.
- Both caption languages share strict JSON validation. Missing credentials, failed requests and invalid responses raise errors without template substitution. Offline templates remain an explicit selection.
- Style recommendations consider category, destination and night/family story angles. Manual selection stays available.
- `.env` loads explicitly from the application folder without overriding existing environment variables. Credentials are never included in post downloads; raw SDK/server error bodies are not shown. `.streamlit/secrets.toml` is ignored as well.
- Cloudflare FLUX.1-schnell REST integration matches the [official model contract](https://developers.cloudflare.com/workers-ai/models/flux-1-schnell/): bearer authentication, prompt up to 2048 characters, four steps, Base64 image output. This model does not expose width/height parameters in that contract; a requested portrait composition is not a guaranteed output aspect ratio.
- Automated tests cover mocked API responses, caption validation, safe errors, recommendations and bilingual editable UI behavior. Streamlit 1.50 AppTest requires a test-only radio adapter for its single segmented language widget; the production UI keeps the segmented control.
- Live Cloudflare, Hugging Face, Alibaba Wan and text-model calls have not been exercised. Test success does not establish account permissions, credits, model availability or generated-content quality.

## Editorial UI reference

The Streamlit interface follows the supplied desktop/mobile Figma screenshots: ivory `#f8f6f1`, sand `#eae4d9`, clay `#a34f30`, charcoal `#33332f`, sage `#879384`, Cormorant Garamond headings, DM Sans body and Noto Sans SC Chinese text. Presentation is isolated in `studio.css`; generation functions and `.env` handling are unchanged. Native controls remain keyboard accessible and title, caption and hashtags stay directly editable. Existing destination presets, manual style selection, fallback controls, exports and evaluation remain available.

Streamlit differences: native fields use focus/blur submission rather than true contenteditable text; long titles scroll within their single-line field. Native widgets, column stacking and image dimensions prevent pixel-identical desktop/mobile layout. Font loading needs Google Fonts access, with local serif/sans fallbacks. Actual image dimensions are preserved rather than cropping to the reference's 4:5 frame. The photographed lake is reference artwork, not a bundled generated result. Caption download is retained instead of claiming a clipboard copy succeeded. No fabricated percentage progress, cancellation, clipboard/download-success toast or image-only retry is added: those reference states would require additional application behavior. Native loading/error feedback and previous-result preservation remain in place. CSS uses Streamlit widget hooks, which may need review after framework upgrades.

## Consistent light appearance

`.streamlit/config.toml` sets the default light theme and matches the editorial ivory, sand, charcoal and clay palette. `studio.css` explicitly pairs widget text with light backgrounds, including dropdown portals, editable post fields, download buttons and expanders, and declares `color-scheme: only light` for native browser controls. The banner keeps its existing white photo credits and charcoal headings. No generation, credential-loading or secret-storage behavior changes.

Start Streamlit from the repository root so it discovers `.streamlit/config.toml`. Reboot the Community Cloud app after merging if the theme is not picked up. Existing browser theme preferences can differ from the default; select the custom app theme if needed. Browser extensions that forcibly recolor pages are outside the app's control. Verification includes the full automated suite and a local browser check with `--theme.base dark` deliberately overriding the base; OS-level dark preference emulation was not available in the browser tooling.

## Local Wuzhen iteration — 21 October 2026

Run `streamlit run week2_app.py --server.address 127.0.0.1 --server.port 8502` from the repository folder.
The original `app.py` is retained for comparison; the new entry point reuses its styles and image-provider engine.

- `data/wuzhen_xizha.json`: source URLs, fact IDs, aliases and information boundaries.
- `prompts/ancient_town_v2.txt`: reviewed Ancient Town V2 model instructions.
- `template_engine.py`: keyword matching, independent two-version copy and image state, validated model response and provenance export.
- The main form takes only a place name and keywords. Unknown places stop with a missing-data message. Unsupported keywords are shown for review and are not inserted into offline copy.
- Default is explicitly labelled offline rule-based preview (not AI output). LLM mode requires configuration and a separate opt-in. No live accounts were used during local development.
- Images are requested separately. An image failure cannot delete successful copy or edits. A changed brief is marked stale until regenerated.
- TXT exports contain publishable copy only; JSON includes original copy, edited copy, the fact sheet and source labels. Downloads are the durable record; browser session state is not permanent storage.
- Natural scenery and theme park rules are shown as planned structure only. This iteration enables the Wuzhen ancient-town case, not all three categories or video generation.
- UI language for this focused local entry point is Chinese. The original bilingual entry point remains available.

### Beginner workflow refinement

`week2_app.py` now exposes place + selectable focus topics, friendly version names, one-click title suggestions and a selected-version TXT download. Each version retains independent edits when switching. Regeneration explicitly offers to keep edits or replace both versions. Technical prompts and JSON export are confined to the developer-record expander. This local entry point is offline-only and does not load keys or invoke text/image APIs; image status is clearly shown as not connected. The original provider engine remains available for a later integration stage.
