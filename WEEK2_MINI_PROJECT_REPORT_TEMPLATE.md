# C1 — Week 2 Mini-Project Report (Draft Template)

## Objective
Generate a promotional image, a three-frame slideshow and three editable Xiaohongshu caption variants from a tourism brief.

## Selected location and creative brief
- Attraction: [enter]
- Optional keywords: [enter]
- Category: [古镇 / Ancient Town, 自然风光 / Natural Scenery, or 主题乐园 / Theme Park]
- Output language: [English or Chinese]
- Recommended / selected visual direction and category palette: [enter from downloaded brief]

## Prototype method
The Streamlit prototype uses one recommended visual direction, palette and template per category, with manual visual direction selection retained. Cloudflare Workers AI is the sole image provider. The existing OpenAI-compatible text API generates three distinct caption variants. Local FFmpeg assembles the cover and two additional generated images into a silent 9-second slideshow. No alternate image provider or automatic template substitution is used.

## Evidence to add from an actual run
- Screenshot of the brief and previews: [insert]
- Generated and edited captions: [insert actual output]
- Downloaded PNG, MP4 and JSON: [attach]
- API model and run duration, if tested: [enter; do not include credentials]
- Language/category checks: [enter]
- Generation failures or rendering limitations: [enter]

## Manual review
Assess visual quality, landmark accuracy, style consistency, cost efficiency and integration with the app's weighted review rubric. Verify travel claims against authorized sources. Label generated visuals as illustrative, not actual photographs or evidence of a visit.

## Limitations and next steps
Shared art direction encourages visual consistency but cannot guarantee identical scenery across generated images. The video is a slideshow, not generated motion. Facts and model-generated captions need human review. Local tests do not establish live API access, quota or content quality. Community Cloud storage is ephemeral; download results.

## Test record
- Automated tests: [record current `python -m pytest -q` result]
- Real local FFmpeg encode/decode test: [record result]
- Live API integration: [record actual result or not verified]
- Human content assessment: [record actual review or pending]
