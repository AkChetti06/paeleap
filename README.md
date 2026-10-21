# Paeleap C1 — Week 2 Tourism Promotion Mini-Project

Based on the three Week 1 documents: tourist attraction and API research, curated 20 Xiaohongshu reference posts (7 scenic / 7 museum / 6 study-tour), and visual-task classification. **The curated sample is not a platform-wide viral ranking.**

## What this does
Enter an attraction name → choose content task and visual style → generate a proposed image prompt → generate one Chinese promotional title, caption, and hashtags → optionally call **Wan 2.6 text-to-image** → display, score manually, and download a post. The interface works completely offline with an **explicitly marked placeholder**, and supports real cloud image generation after setup.

## Run

```bash
cd paeleap-c1-week2
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env    # Windows: copy .env.example .env
streamlit run app.py
```

Open the URL shown by Streamlit. The default runs without an API key but produces **no AI image**; do not show the placeholder as generated output.

## Real Alibaba Wan setup
1. Obtain a Model Studio API key and a workspace-specific endpoint from **the same region**. China (Beijing) and Singapore keys/endpoints are not interchangeable.
2. In `.env`, set `DASHSCOPE_API_KEY`, `DASHSCOPE_BASE_URL` and optionally `IMAGE_MODEL=wan2.6-t2i`.
3. Switch image mode to **Alibaba Wan 真实生成** in the sidebar. The app calls `dashscope.aigc.image_generation.ImageGeneration.call`, then downloads the returned temporary image URL. Each successful call may incur charges.
4. Check your region's model availability, dimensions, price and quota in the console before running. Do not commit your `.env` file.

Source: [Alibaba Wan T2I API reference](https://www.alibabacloud.com/help/en/model-studio/text-to-image-v2-api-reference).

## Optional LLM captions
Set `TEXT_API_KEY`, `TEXT_BASE_URL` (full OpenAI-compatible **/v1** base path), and `TEXT_MODEL`. Select **LLM API 生成**. LLM mode requires a configured text provider and reports errors explicitly; it never substitutes an offline template. Captions must be reviewed for factual accuracy before publishing.

## Constraints and report
- Week 2: **one promotional post**, not a full style-template library (Week 3), image-to-video (Week 4), or full post generator (Week 5).
- Follow **reason → sequence → evidence**, but never falsely claim an AI image is real evidence.
- Stored outputs: `outputs/<timestamp>/visual.png`, `post.json`, and `post.txt`.
- Evaluate quality, landmark accuracy, style consistency, cost efficiency, and integration on your Week 1 25/25/20/15/15 rubric. These are user-assigned scores, not benchmark results.
- `python -m pytest -q` runs unit tests (no API charges).

## Suggested Week 2 report headings
Objective · Week 1 evidence used · Prototype architecture · API configuration · Screenshots/results · Evaluation and limitations · Week 3 transition.

**Important**: demo fallback uses generic guidance, not validated visit times, transit, exhibit availability or precise routes. Generated images are illustrative only; place-specific claims and any planned publication require human review and authorized factual material.

## Version 2 — bilingual studio + free testing

The updated UI includes a full **English / 中文** language toggle, polished creator-studio styling, and caption generation in the selected language. Switching the language does not automatically translate an earlier generated result: click Generate again to produce a new caption.

### Free real image generation (Hugging Face)

1. Create a Hugging Face account: https://huggingface.co/join
2. Create an access token at https://huggingface.co/settings/tokens with Inference Providers permission.
3. Copy `.env.example` to `.env`, set `HF_TOKEN=...` and restart Streamlit.
4. Select **Hugging Face · free starter credits** as your image engine.
5. If the default `HF_IMAGE_MODEL` is unavailable, pick a currently hosted text-to-image model at https://huggingface.co/models?pipeline_tag=text-to-image and update the environment variable.

**Important:** Hugging Face free accounts currently receive **US$0.10 in monthly inference credits**, subject to change. There is no guarantee the chosen image model will fit your credit balance or be available in your region. The demo option remains entirely free and works without any API key, but is explicitly a non-AI placeholder. Alibaba Wan remains available for later model testing.

The prototype does not automatically publish on Xiaohongshu or present invented itineraries and AI concept visuals as genuine travel photos. Generated copy should be reviewed against current official site information.


## Version 3: Cloudflare Workers AI

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
