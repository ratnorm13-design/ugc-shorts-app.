# UGC Remix Studio V5.15 RC

Reference → Analyze → Storyboard → Scene 1 → last-frame screenshot bridge → Scene 2 → ...

## What changed in V5.15 RC
- Preserves the sequential screenshot-bridge workflow.
- Adds deterministic evidence validation without extra Gemini requests.
- Readability-probe subject roster is reconciled against full analysis.
- Temporal breakdown is cross-checked for ordering, completeness, and duration.
- Reference fidelity fields are checked for substantive content.
- Scene coverage is checked against deterministic source beats.
- Scene cause/action/fidelity integrity is gated before a contract becomes authoritative.
- Scene N END STATE is reconciled against Scene N+1 START STATE.
- Performance fallback gets provenance: MODEL_VERIFIED / LOCAL_FALLBACK.
- Contract → prompt contradiction checks run before accepting a prompt.
- Structured-output responses prefer SDK `response.parsed` when available.
- Existing quota protection and sequential bridge gates remain intact.

## Deploy
Use `app.py` as the Streamlit entry point.

Do not paste Gemini API keys into source code. Prefer a deployment secret named `GEMINI_API_KEY`.

## Validation performed on this build
- Python compile: PASS
- AST parse: PASS
- Duplicate function-name scan: PASS
- Deterministic validation-core tests: PASS
- ZIP manifest check: required runtime files present

## Important limitation
This is a Release Candidate, not a claim of zero runtime defects. Live Gemini/Flow/Veo behavior still depends on the deployed Google project, API key, model availability, uploaded media, and provider limits.
