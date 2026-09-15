V5.12.9 — Deep Reference Ingestion + Structured Output Hardening

Fixes:
- Uses Gemini structured response.parsed when available instead of relying only on response.text.
- Strict subject item schema requires id, jenis, and deskripsi_visual.
- Adds a small multimodal readability gate before full analysis.
- Stores the probe subject roster as evidence; if the full analysis omits/invalidates subject_roster, the verified probe roster is reused without inventing subjects.
- Canonical inline video input uses Part.from_bytes().
- Inline fallback remains isolated from adaptive keyframes.
- Optional subject fields are normalized locally for downstream continuity.
- Preserves sequential Scene 1 -> screenshot bridge -> Scene 2 workflow and AI Engineer/Audit.

Verification:
- py_compile PASS
- AST parse PASS
- duplicate function scan PASS (0 duplicates)
- static feature checks PASS
- Not live-tested against the user's Gemini project/API, so no honest guarantee of zero runtime bugs is claimed.
