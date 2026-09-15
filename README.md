# UGC Remix Studio V5.13

Fix focused on reference-analysis validation:

- `temporal_breakdown` now uses a strict structured-output schema with `minItems: 1`.
- Each temporal beat requires core evidence fields: beat, time, start state, cause, action, end state, camera/character/motion/emotion state.
- Emotion performance profiles now use a stricter schema instead of a free-form object array.
- Missing/incomplete performance profiles remain continuity-safe local repair; this is informational, not an analysis failure.
- Readability state is cleared whenever reference analysis is invalidated, preventing stale probe subjects from leaking into a new project.
- Post-response validation rejects empty/incomplete temporal beats instead of letting a bad analysis enter the continuity pipeline.
- No extra Gemini repair request is added for temporal data, preserving quota.

The sequential workflow remains unchanged:
Scene 1 → generate → upload last-frame screenshot → Scene 2 → ...
