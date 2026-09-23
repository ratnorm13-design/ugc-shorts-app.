# GTA V Parkour Remix Studio — V14.1

This build is a reconstructed V14.1 hardening release for the user's GTA V parkour/gameplay-reference workflow.

## Core workflow

REFERENCE → ANALYZE + AUTO REMIX → ANALYSIS → STORYBOARD → PROMPT SCENE → FLOW/VEO → LAST FRAME → NEXT SCENE → SEO

## Important fixes

- No hard-coded Milo/kitten/Tale Of Paw identity.
- Subject identity is reference-derived.
- Analysis state is fingerprinted; changing reference/style/aspect/duration/instructions invalidates downstream artifacts.
- Scene N is blocked until the previous scene's final-frame bridge is uploaded and validated.
- Scene prompts are fingerprinted against their inputs.
- Reference Ground Truth, temporal beats, spatial layout, camera, motion/physics, action-critical props, emotion/performance, hook, and payoff remain part of the continuity pipeline.
- Deprecated Gemini sampling temperature was removed.
- Python 3.11-safe version-string formatting is used.

## Deployment

Use `requirements.txt` at the repository root and `packages.txt` for ffmpeg. Do not keep a competing `requirement.txt` file in the same deployment root.

## Testing performed here

- Python syntax compilation: PASS.
- Static workflow symbol checks: PASS.
- Hard-coded Milo/kitten/Tale Of Paw scan: PASS.
- Live Streamlit browser execution was not available in this environment because Streamlit itself is not installed in the execution sandbox.

The generated prompts are intended for fictional in-game gameplay/traversal content; they are not instructions for real-world stunts.
