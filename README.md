# UGC Reference Studio v5.12.5

This build is based on v5.12.4 and keeps the existing continuity/visual-bridge architecture while hardening project state.

## Workflow
1. Home: reference + project settings.
2. ANALYZE + AUTO REMIX.
3. Analysis review.
4. Storyboard: create the current scene contract.
5. Explicit `BUAT PROMPT SCENE N` handoff.
6. Generate the video in Flow/Veo.
7. Upload the last-frame screenshot as the visual bridge.
8. Validate bridge and unlock the next scene.
9. Repeat until all scenes are complete.
10. SEO unlocks only after the full sequential scene workflow.

## State hardening
- A deterministic project signature is captured after analysis.
- Changing reference, visual style, aspect ratio, duration, or global instruction after analysis invalidates downstream artifacts.
- Scene/storyboard/prompt/SEO generation is blocked until ANALYZE + AUTO REMIX is run again.
- Scene prompt fingerprints continue to protect against stale prompts.
- Screenshot bridge replacement invalidates downstream scene artifacts.

## Runtime
- Python 3.11 is compatible with the pinned dependencies.
- Streamlit Community Cloud should use `requirements.txt` at repository root.
- `packages.txt` is included for ffmpeg if the repository also needs ffmpeg tooling.
