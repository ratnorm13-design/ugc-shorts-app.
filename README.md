# UGC Remix Studio V5.12.8

Fixes V5.12.7 reference-analysis failure:

1. When Gemini Files API returns FAILED, the short-video inline fallback is now explicitly marked as `reference_input_mode="inline"`.
2. Inline fallback no longer appends adaptive keyframes, preventing an accidental oversized/duplicated inline request.
3. Gemini `subject_roster` is normalized defensively when the model returns a JSON wrapper such as `{ "subjects": [...] }` or a single subject object.
4. No new subject is fabricated. Entries without an ID are ignored; if no valid subject list remains, the app fails with a clear diagnostic instead of silently continuing.
5. Existing sequential Scene 1 -> last-frame screenshot bridge -> Scene 2 workflow and AI Engineer core are preserved.

Static verification: Python compile PASS.
Not live-tested against the user's Gemini project/API key.
