# UGC Remix Studio V15 FIXED

## Main fixes
- Migrated from `google.generativeai` to the current `google-genai` SDK.
- Uses valid Gemini model IDs with controlled fallback.
- Removed deprecated sampling configuration.
- Uses `types.Part.from_bytes()` for video/image input.
- JSON mode uses MIME enforcement + local validation instead of nested response schemas.
- Quota/auth/400 errors stop immediately; no quota-burning retry loop.
- Scene generation is sequential: Scene N -> last-frame screenshot -> Scene N+1.
- "Generate ALL Scenes" was removed.
- Next Scene stays locked until the previous last frame is uploaded.
