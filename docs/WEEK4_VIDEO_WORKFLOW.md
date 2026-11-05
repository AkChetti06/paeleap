# Week 4 — Video workspace update

Branch: `feature/week4-video-workflow`

## Available in this branch

- Start with the image already in the Image tab (generated image or uploaded photo).
- Choose **Use my photos** and add 1–5 photos in the desired order. The current image is frame one.
- For a generated cover only, choose **Generate extra images** to retain the existing Cloudflare two-image workflow.
- Set **Seconds per image** (1–10) and see the expected number of frames and total runtime.
- Create, preview and download a silent MP4 at the selected aspect ratio.
- Keep the previously successful video if rendering or image generation fails.
- Uploaded photo mode does not make image-generation API requests.

## Boundaries

This feature makes a slideshow, not AI-generated image-to-video animation. No Wan video API credentials or video model are configured by this change. Uploaded photos remain in server memory for the current Streamlit session; generated files may be saved to the existing output folder. Human review is still required for promotional content.

## Manual verification before merge

1. Run `python -m streamlit run app.py` on this feature branch.
2. Upload a cover through **Image > Use your own photo**; open Video.
3. Add one photo; choose two seconds per image. Create an MP4; verify it contains two frames and lasts about four seconds.
4. Repeat with five additional photos and a different ratio; download the MP4.
5. Generate an AI cover, then try **Generate extra images** with valid Cloudflare server credentials. Verify that this path uses the expected additional quota.
6. Reject a photo larger than 20 MB or exceptionally large pixel dimensions, and verify a previously generated video stays downloadable after a failed attempt.
7. Switch languages and preview ratios; verify labels, export shape, and saved-video notices.
8. Confirm Caption and Image controls retain their existing appearance and input outlines.

Do not merge or deploy until manual tests and user review pass.
