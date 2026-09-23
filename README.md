# UGC Remix Studio V15.1 FIXED

## What was fixed
- Gemini 3.8 Flash is now the primary model, with 3.7 / 3.6 / 3.5 Flash-Lite failover.
- A 503/UNAVAILABLE on one model no longer aborts the whole request after one retry; the router continues to the next model.
- Reference videos use the Gemini File API first, wait for `ACTIVE`, then use `Part.from_uri(..., media_processing="AGENTIC")` for temporal analysis.
- Inline video is retained only as a small-file fallback (<=20 MB).
- Video duration is grounded with `ffprobe` when a real video is uploaded; Gemini is not trusted to invent the file duration.
- API key can come from Streamlit Secrets, environment variable, or the sidebar field.
- Scene-specific extra instructions now exist on the actual Scene screen and apply only to that scene.
- Scenes and SEO are locked when the workflow is incomplete or the project configuration changed after analysis.
- The required sequential workflow remains: Scene 1 -> last-frame screenshot -> Scene 2 -> repeat.
- No Generate-All path.
- Deprecated sampling parameters and the legacy `google.generativeai` SDK are removed.

## Files
- `app.py` — application
- `requirements.txt` — Python dependencies
- `packages.txt` — system package (`ffmpeg` / `ffprobe`)
- `test_release_v15_1.py` — local static release gate
