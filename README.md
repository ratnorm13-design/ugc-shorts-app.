# UGC Remix Studio V5.17 RC

Reference → Readability → Evidence Audit → Ground Truth → Scene Contract → Prompt → Flow/Veo → Last-frame Bridge → Next Scene

## What changed from V5.16
- **No silent performance repair.** Every detected subject must have one complete `subject_emotion_profiles` entry from Gemini. Missing/duplicate/unknown profiles hard-fail analysis.
- **Strict Reference Fidelity.** `reference_fidelity` is schema-required and also semantically validated locally. Empty/generic fidelity text cannot become authoritative state.
- **Probe ↔ Full Analysis reconciliation** remains a hard gate.
- **Temporal ↔ keyframe evidence check** is enforced when timestamped keyframes are actually included in the analysis request.
- **Complete scene coverage gate** ensures every reference temporal beat is mapped to at least one target scene.
- Existing cross-scene END→START, causal, and contract→prompt gates remain.
- Removed silent subject/profile normalization that could hide incomplete Gemini analysis.
- Added one-shot H.264/AAC MP4 transcode fallback for media-processing failures.
- Added conservative 18 MB inline threshold to leave request overhead headroom.
- Added ffmpeg as a declared Linux dependency for Community Cloud.

## Validation performed
- Pre-flight tests were written **before** the V5.16 implementation to expose the known gaps.
- Python compile checks passed for all Python files.
- AST parse passed.
- Duplicate function scan passed.
- Deterministic validation-core tests passed.
- Golden regression tests passed for the known driver/front-passenger/dust/prop/late-reaction continuity case.
- Static release checks passed.
- ZIP manifest verified after packaging.

## Important
This is an RC build, not a claim of zero runtime defects. Live Gemini/Streamlit execution still depends on the deployed environment, API key, model availability, media codec, and provider limits.

Do not put API keys into source code. For deployment, use the platform's secret/environment-variable mechanism with `GEMINI_API_KEY`.
