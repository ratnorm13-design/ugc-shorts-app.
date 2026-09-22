
import json
import math
import os
import re
import time
from typing import Any

import streamlit as st
from google import genai
from google.genai import types

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="UGC Remix Studio V15",
    page_icon="🎬",
    layout="wide",
)

APP_VERSION = "15.0 — Gemini GenAI SDK + Safe Model Fallback + Sequential Scene Gate"

# Gemini 3.7 Flash is a valid current model ID. 3.6 and 2.5 are
# compatibility fallbacks for projects where the primary model is unavailable.
MODEL_CANDIDATES = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-2.5-flash",
]

MAX_FILE_SIZE_MB = 15
MAX_SUPPORTED_SECONDS = 300

DURATION_SCENES = {
    "Auto (sesuai durasi referensi)": 0,
    "8 detik (1 scene)": 1,
    "16 detik (2 scene)": 2,
    "24 detik (3 scene)": 3,
    "32 detik (4 scene)": 4,
    "40 detik (5 scene)": 5,
    "48 detik (6 scene)": 6,
    "56 detik (7 scene)": 7,
    "1 menit (8 scene)": 8,
    "1.5 menit (12 scene)": 12,
    "2 menit (15 scene)": 15,
    "2.5 menit (19 scene)": 19,
    "3 menit (23 scene)": 23,
    "3.5 menit (27 scene)": 27,
    "4 menit (30 scene)": 30,
    "4.5 menit (34 scene)": 34,
    "5 menit (38 scene)": 38,
}

STYLE_OPTIONS = [
    "3D stylized game graphics",
    "Unreal Engine inspired cinematic 3D",
    "Realistic cinematic 3D",
    "Stylized comedy game",
]

CAMERA_OPTIONS = [
    "Dynamic third-person tracking",
    "Smooth side tracking",
    "Low-angle action tracking",
    "Slow cinematic push-in",
]

RUNNER_PRESETS = [
    "Custom / ketik sendiri",
    "Pocong-style fictional white-wrapped ghost character",
    "Giant rubber duck game character",
    "Blocky voxel game character",
    "Goofy skeleton ragdoll character",
    "Funny orange cat in a hoodie",
    "Funny green frog with sunglasses",
    "Inflatable dinosaur game costume",
    "Gingerbread game character",
]

TARGET_IDLE_PRESETS = [
    "Auto / random mix",
    "Goofy dance and body sway",
    "Nervous trembling and hand waving",
    "Confident taunting gesture",
    "Static statue-like pose",
]

TARGET_DOLL_PRESETS = [
    "Auto / unique comedic ragdolls",
    "Yellow capsule bean creatures with round goggles",
    "Armless astronaut bean creatures",
    "Cute jelly-bean game dolls",
    "Colorful antenna alien dolls",
    "Funny porcelain toilet-head game entities",
    "Fuzzy blue monster plush dolls",
    "Plastic block mini-figures",
    "Green ogre-like creature dolls",
    "Oversized yellow rubber duckies",
    "Goofy skeleton ragdolls",
]

MAP_OPTIONS = [
    "Auto (follow remix)",
    "Downtown skyscraper rooftop",
    "Mountain canyon mega ramp",
    "Shipping-container harbor",
    "Floating cloud game arena",
    "Desert airfield game arena",
    "Coastal boardwalk game map",
    "Military-base inspired fictional game map",
    "Red-rock canyon bridge",
    "Neon cyberpunk city at night",
    "Fictional lava-themed game arena",
]

PROP_STAND_OPTIONS = [
    "Auto (follow remix)",
    "Flat concrete platform",
    "Large colorful fitness balls",
    "Wooden cargo props and barrels",
    "Stacked rubber tires",
    "Springy launch pads",
    "Translucent ice-like pillars",
    "Rotating wooden logs",
    "Concrete construction blocks",
    "Inflatable rings",
    "Spring platforms",
]

CLIMAX_ACTION_OPTIONS = [
    "Auto (follow remix)",
    "Multi-target comedy impact followed by a harmless ragdoll tumble",
    "Jumping kick with domino-style ragdoll collapse",
    "Spinning slapstick impact and exaggerated ragdoll bounce",
    "Double impact followed by a cartoon bounce",
    "Fast combo followed by a harmless off-platform ragdoll tumble",
    "Comedic tackle into a soft physics tumble",
    "Sliding sweep with exaggerated ragdoll reaction",
]

# Fictional game obstacles only.
OBSTACLE_OPTIONS = {
    "None / flat game track": "",
    "Moving foam blocks": "FICTIONAL GAME OBSTACLE: Soft moving foam blocks slide across the lane.",
    "Rotating padded rollers": "FICTIONAL GAME OBSTACLE: Large padded rollers rotate across the lane.",
    "Bouncy gate panels": "FICTIONAL GAME OBSTACLE: Springy gate panels bounce open and closed.",
    "Breakaway game tiles": "FICTIONAL GAME OBSTACLE: Lightweight game tiles visually pop apart after contact.",
    "Wind tunnel game zone": "FICTIONAL GAME OBSTACLE: A stylized wind zone pushes the character sideways.",
    "Colorful spinning hoops": "FICTIONAL GAME OBSTACLE: Large colorful hoops rotate slowly across the path.",
}

MANEUVER_OPTIONS = [
    "Auto / standard run",
    "Near-miss stumble and recovery",
    "Wall-run and bounce",
    "Low slide under a soft obstacle",
    "Spring-pad launch and flip",
    "Rail balance over a game platform",
    "Quick taunt emote while running",
    "Zipline-style game traversal",
    "Duck under a soft moving prop",
    "Speed-pad acceleration",
    "Precision vault across game pillars",
]

ASPECT_OPTIONS = [
    "9:16 — Shorts / Reels / TikTok",
    "16:9 — YouTube Long",
    "1:1 — Square",
]

DEFAULTS = {
    "page": "home",
    "api_key": "",
    "reference_bytes": None,
    "reference_name": "",
    "reference_mime": "",
    "reference_text": "",
    "visual_style": STYLE_OPTIONS[0],
    "selected_camera": CAMERA_OPTIONS[0],
    "runner_choice": RUNNER_PRESETS[1],
    "target_idle_choice": TARGET_IDLE_PRESETS[0],
    "target_doll_choice": TARGET_DOLL_PRESETS[0],
    "custom_runner": "",
    "selected_map": MAP_OPTIONS[0],
    "selected_prop_stand": PROP_STAND_OPTIONS[0],
    "selected_climax_action": CLIMAX_ACTION_OPTIONS[0],
    "aspect_ratio": ASPECT_OPTIONS[0],
    "duration": "Auto (sesuai durasi referensi)",
    "custom_instruction": "",
    "user_scene_obstacles": {},
    "user_scene_maneuvers": {},
    "analysis": {},
    "storyboard": [],
    "scene_prompts": {},
    "scene_frames": {},
    "scene_frame_signatures": {},
    "current_scene": 1,
    "detected_scenes": 1,
    "detected_duration_seconds": None,
    "duration_extension": {},
    "seo": {},
    "active_model": None,
    "last_api_error": "",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def go(page_name: str) -> None:
    st.session_state.page = page_name
    st.rerun()


def reset_project() -> None:
    for key, value in DEFAULTS.items():
        st.session_state[key] = value
    st.rerun()


# ============================================================
# JSON / VALIDATION HELPERS
# ============================================================
def extract_json(text: str) -> Any:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    starts = [p for p in (text.find("{"), text.find("[")) if p >= 0]
    if not starts:
        raise ValueError("Respons Gemini tidak berisi JSON.")

    start = min(starts)
    for end in range(len(text), start, -1):
        try:
            return json.loads(text[start:end].strip())
        except json.JSONDecodeError:
            continue

    raise ValueError("Respons Gemini tidak dapat diparse sebagai JSON.")


def validate_analysis(data: Any) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Analisis harus berupa JSON object.")

    duration = data.get("video_duration_seconds")
    if not isinstance(duration, (int, float)):
        raise ValueError("video_duration_seconds tidak valid.")
    if duration <= 0 or duration > MAX_SUPPORTED_SECONDS:
        raise ValueError(
            f"Durasi referensi harus >0 dan <= {MAX_SUPPORTED_SECONDS} detik."
        )

    original = data.get("original_reference")
    mutation = data.get("remixed_mutation")
    storyboard = data.get("storyboard_plan")

    if not isinstance(original, dict):
        raise ValueError("original_reference tidak valid.")
    if not isinstance(mutation, dict):
        raise ValueError("remixed_mutation tidak valid.")
    if not isinstance(storyboard, list):
        raise ValueError("storyboard_plan harus berupa list.")

    normalized_storyboard = []
    for index, item in enumerate(storyboard, start=1):
        if not isinstance(item, dict):
            continue
        focus = str(item.get("fokus_aksi", "")).strip()
        if focus:
            normalized_storyboard.append(
                {"scene": index, "fokus_aksi": focus}
            )

    if not normalized_storyboard:
        raise ValueError("Gemini tidak menghasilkan storyboard yang bisa dipakai.")

    data["storyboard_plan"] = normalized_storyboard
    return data


def validate_prompt_text(prompt: str) -> str:
    prompt = (prompt or "").strip()
    if not prompt:
        raise ValueError("Prompt scene kosong.")
    return prompt[:2000].rstrip()


# ============================================================
# GEMINI CLIENT / MODEL ROUTING
# ============================================================
def get_client() -> genai.Client:
    key = (
        os.getenv("GEMINI_API_KEY")
        or st.session_state.get("api_key", "")
    ).strip().strip("`\"' ")

    if not key:
        raise RuntimeError(
            "Gemini API Key belum diisi. Masukkan Auth/API key di sidebar."
        )

    try:
        return genai.Client(api_key=key)
    except Exception as exc:
        raise RuntimeError(f"Gagal membuat Gemini client: {exc}") from exc


def _error_text(exc: Exception) -> str:
    return str(exc).strip() or exc.__class__.__name__


def _is_model_unavailable(message: str) -> bool:
    upper = message.upper()
    return (
        "NOT_FOUND" in upper
        or "MODEL_NOT_FOUND" in upper
        or "404" in upper
        or "NOT SUPPORTED" in upper
    )


def _is_quota_error(message: str) -> bool:
    upper = message.upper()
    return (
        "RESOURCE_EXHAUSTED" in upper
        or "QUOTA" in upper
        or "429" in upper
    )


def _is_auth_error(message: str) -> bool:
    upper = message.upper()
    return (
        "API_KEY_INVALID" in upper
        or "INVALID_API_KEY" in upper
        or "UNAUTHENTICATED" in upper
        or "PERMISSION_DENIED" in upper
        or "401" in upper
    )


def _is_invalid_request(message: str) -> bool:
    upper = message.upper()
    return (
        "INVALID_ARGUMENT" in upper
        or "400" in upper
        or "FAILED_PRECONDITION" in upper
    )


def ask(
    prompt: str,
    parts: list | None = None,
    json_mode: bool = False,
) -> str:
    """
    Current Google GenAI SDK request path.

    There is intentionally no response_schema here. The app uses JSON MIME
    output plus local validation so it cannot hit the previous nested
    additional_properties schema serialization problem.
    """
    client = get_client()

    content_parts = list(parts or [])
    content_parts.append(types.Part.from_text(text=prompt))
    contents = types.Content(
        role="user",
        parts=content_parts,
    )

    config_kwargs: dict[str, Any] = {}
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"

    last_error = None

    for model_name in MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs),
            )

            st.session_state.active_model = model_name

            text = getattr(response, "text", None)
            if text and text.strip():
                return text.strip()

            raise RuntimeError("Gemini mengembalikan respons kosong.")

        except Exception as exc:
            last_error = exc
            message = _error_text(exc)
            st.session_state.last_api_error = message

            if _is_auth_error(message):
                raise RuntimeError(
                    "Autentikasi Gemini gagal. Periksa key/project yang dipakai."
                ) from exc

            if _is_quota_error(message):
                raise RuntimeError(
                    "Kuota/rate limit Gemini tercapai. "
                    "Kode tidak melakukan retry otomatis agar kuota tidak terbakar."
                ) from exc

            if _is_invalid_request(message):
                raise RuntimeError(
                    f"Gemini menolak request (400/invalid argument): {message}"
                ) from exc

            if _is_model_unavailable(message):
                continue

            upper = message.upper()
            transient = any(
                token in upper
                for token in ("500", "502", "503", "504", "UNAVAILABLE", "INTERNAL")
            )
            if transient:
                time.sleep(2)
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(**config_kwargs),
                    )
                    st.session_state.active_model = model_name
                    text = getattr(response, "text", None)
                    if text and text.strip():
                        return text.strip()
                except Exception as retry_exc:
                    last_error = retry_exc
                    retry_message = _error_text(retry_exc)
                    if _is_quota_error(retry_message):
                        raise RuntimeError(
                            "Kuota/rate limit Gemini tercapai setelah retry."
                        ) from retry_exc
                    if _is_model_unavailable(retry_message):
                        continue
                    raise RuntimeError(
                        f"Gemini gagal: {retry_message}"
                    ) from retry_exc

            raise RuntimeError(f"Gemini gagal: {message}") from exc

    raise RuntimeError(
        "Tidak ada model Gemini yang tersedia untuk project ini. "
        f"Model yang dicoba: {MODEL_CANDIDATES}. "
        f"Error terakhir: {_error_text(last_error) if last_error else 'unknown'}"
    )


# ============================================================
# VIDEO INPUT
# ============================================================
def build_video_part() -> list:
    data = st.session_state.get("reference_bytes")
    if not data:
        return []

    mime = st.session_state.get("reference_mime") or "video/mp4"

    if len(data) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(
            f"Video terlalu besar. Maksimum aplikasi {MAX_FILE_SIZE_MB} MB."
        )

    return [
        types.Part.from_bytes(
            data=data,
            mime_type=mime,
        )
    ]


def get_reference_parts() -> list:
    parts = build_video_part()
    if parts:
        return parts

    text = st.session_state.get("reference_text", "").strip()
    if text:
        return [types.Part.from_text(text=text)]

    return []


# ============================================================
# APP LOGIC
# ============================================================
def choose_target_duration(seconds: float) -> tuple[str, int]:
    for label, scene_count_value in DURATION_SCENES.items():
        if scene_count_value <= 0:
            continue
        target = scene_count_value * 8
        # The 5-minute/38-scene project setting is intentionally kept as
        # the user's scene-grid convention; 38 x 8 = 304 seconds.
        if target + 0.25 >= seconds:
            return label, target
    return "5 menit (38 scene)", 304


def scene_count() -> int:
    configured = DURATION_SCENES.get(st.session_state.duration, 0)
    if configured > 0:
        return configured
    return max(1, min(int(st.session_state.detected_scenes), 38))


def get_active_config() -> dict:
    analysis = st.session_state.get("analysis", {})
    mutation = analysis.get("remixed_mutation", {})

    runner = st.session_state.get("runner_choice", RUNNER_PRESETS[1])
    if runner == "Custom / ketik sendiri":
        runner = (
            st.session_state.get("custom_runner", "").strip()
            or "unique funny game character"
        )

    target = st.session_state.get("target_doll_choice", TARGET_DOLL_PRESETS[0])

    map_env = st.session_state.get("selected_map", MAP_OPTIONS[0])
    if map_env == MAP_OPTIONS[0]:
        map_env = mutation.get(
            "map_environment",
            "vivid fictional 3D game arena",
        )

    prop = st.session_state.get(
        "selected_prop_stand",
        PROP_STAND_OPTIONS[0],
    )
    if prop == PROP_STAND_OPTIONS[0]:
        prop = mutation.get(
            "prop_stand",
            "flat game platform",
        )

    climax = st.session_state.get(
        "selected_climax_action",
        CLIMAX_ACTION_OPTIONS[0],
    )
    if climax == CLIMAX_ACTION_OPTIONS[0]:
        climax = analysis.get(
            "climax_action",
            "harmless comedic ragdoll tumble",
        )

    return {
        "runner": runner,
        "target": target,
        "idle": st.session_state.get("target_idle_choice", TARGET_IDLE_PRESETS[0]),
        "map": map_env,
        "prop": prop,
        "climax": climax,
        "camera": st.session_state.get("selected_camera", CAMERA_OPTIONS[0]),
        "style": st.session_state.get("visual_style", STYLE_OPTIONS[0]),
        "aspect": st.session_state.get("aspect_ratio", ASPECT_OPTIONS[0]),
    }


def run_analysis() -> None:
    parts = get_reference_parts()
    if not parts:
        st.warning("Upload video atau isi deskripsi referensi terlebih dahulu.")
        return

    cfg = get_active_config()

    prompt = f"""
You are a multimodal creative director and continuity supervisor for
fictional 3D game-comedy videos.

Analyze the supplied reference only as creative structure:
- timing and pacing
- camera movement
- spatial layout
- cause -> action -> reaction
- comedic payoff

Do not copy protected characters, logos, dialogue, or exact visual identity.
Use the user's selected remix choices as the new creative identity.

USER SETTINGS:
Visual style: {cfg["style"]}
Camera: {cfg["camera"]}
Runner: {cfg["runner"]}
Target: {cfg["target"]}
Target idle: {cfg["idle"]}
Map: {cfg["map"]}
Platform: {cfg["prop"]}
Climax: {cfg["climax"]}
Aspect ratio: {cfg["aspect"]}

Return JSON only:
{{
  "video_duration_seconds": 16,
  "original_reference": {{
    "runner_asli": "...",
    "boss_asli": "...",
    "track_asli": "..."
  }},
  "remixed_mutation": {{
    "runner_baru": "...",
    "boss_baru": "...",
    "target_idle_behavior": "...",
    "camera_movement": "...",
    "track_baru": "...",
    "map_environment": "...",
    "prop_stand": "...",
    "visual_anchor_token": "..."
  }},
  "storyboard_plan": [
    {{"scene": 1, "fokus_aksi": "..."}}
  ],
  "climax_action": "..."
}}

Important:
- video_duration_seconds must be numeric.
- storyboard_plan must contain usable action summaries.
- Keep actions fictional and game-like.
- Never invent unsupported details when describing the original reference.
"""

    with st.spinner("Menganalisis referensi dengan Gemini..."):
        try:
            raw = ask(prompt, parts=parts, json_mode=True)
            data = validate_analysis(extract_json(raw))

            raw_seconds = float(data["video_duration_seconds"])
            if raw_seconds > MAX_SUPPORTED_SECONDS:
                raise ValueError(
                    f"Referensi {raw_seconds:.1f} detik melebihi batas "
                    f"{MAX_SUPPORTED_SECONDS} detik."
                )

            st.session_state.detected_duration_seconds = raw_seconds

            if DURATION_SCENES.get(st.session_state.duration, 0) == 0:
                label, target_seconds = choose_target_duration(raw_seconds)
                st.session_state.detected_scenes = max(
                    1,
                    min(math.ceil(target_seconds / 8), 38),
                )
                st.session_state.duration_extension = {
                    "reference_seconds": round(raw_seconds, 2),
                    "target_seconds": target_seconds,
                    "target_duration": label,
                    "added_seconds": round(
                        max(0, target_seconds - raw_seconds),
                        2,
                    ),
                }

            target = scene_count()
            storyboard = data.get("storyboard_plan", [])

            # Ensure every requested scene has an action line. This is a
            # local deterministic guard, not a second Gemini request.
            if len(storyboard) < target:
                for number in range(len(storyboard) + 1, target + 1):
                    storyboard.append(
                        {
                            "scene": number,
                            "fokus_aksi": (
                                "Continue from the previous scene end state "
                                "while preserving spatial continuity."
                            ),
                        }
                    )

            data["storyboard_plan"] = storyboard[:target]

            st.session_state.analysis = data
            st.session_state.storyboard = data["storyboard_plan"]
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}
            st.session_state.scene_frame_signatures = {}
            st.session_state.current_scene = 1
            st.session_state.seo = {}
            st.session_state.page = "analysis"
            st.rerun()

        except Exception as exc:
            st.error(f"Analisis gagal: {exc}")


def _frame_signature(uploaded_file) -> str:
    import hashlib
    return hashlib.sha256(uploaded_file.getvalue()).hexdigest()


def _has_valid_previous_frame(scene_number: int) -> bool:
    if scene_number <= 1:
        return True
    return bool(
        st.session_state.scene_frames.get(scene_number - 1)
        and st.session_state.scene_frame_signatures.get(scene_number - 1)
    )


def generate_scene_prompt(scene_number: int) -> bool:
    total = scene_count()

    if scene_number < 1 or scene_number > total:
        st.error("Nomor scene tidak valid.")
        return False

    if scene_number > 1 and not _has_valid_previous_frame(scene_number):
        st.warning(
            f"Scene {scene_number} belum terbuka. Upload last frame "
            f"Scene {scene_number - 1} terlebih dahulu."
        )
        return False

    cfg = get_active_config()
    storyboard = st.session_state.get("storyboard", [])

    previous_frame_parts = []
    continuity_instruction = "This is Scene 1. Establish the opening state clearly."

    if scene_number > 1:
        previous_frame = st.session_state.scene_frames[scene_number - 1]
        previous_bytes = previous_frame.getvalue()
        previous_mime = getattr(previous_frame, "type", "image/png") or "image/png"

        previous_frame_parts.append(
            types.Part.from_bytes(
                data=previous_bytes,
                mime_type=previous_mime,
            )
        )

        continuity_instruction = f"""
A real last-frame screenshot from Scene {scene_number - 1} is attached.
Treat it as the VISUAL BRIDGE.

Preserve exactly what is visible at the beginning of Scene {scene_number}:
- character identity and clothing
- relative character positions
- platform geometry
- visible props
- camera side/orientation
- lighting/time of day
- state changes already visible

Do not teleport objects, swap sides, or reset the environment.
"""

    focus = ""
    if len(storyboard) >= scene_number:
        focus = storyboard[scene_number - 1].get("fokus_aksi", "")

    obstacle = st.session_state.user_scene_obstacles.get(scene_number, "")
    maneuver = st.session_state.user_scene_maneuvers.get(scene_number, "")

    final_note = ""
    if scene_number == total:
        final_note = f"""
FINAL SCENE:
Climax concept: {cfg["climax"]}.
Keep the ending fictional, exaggerated, and clearly game-like.
"""

    prompt = f"""
Write ONE compact English prompt for a fictional 3D game-comedy video.
Maximum 130 words.

{continuity_instruction}

LOCKED PARAMETERS:
Style: {cfg["style"]}
Aspect ratio: {cfg["aspect"]}
Runner: {cfg["runner"]}
Target entities: {cfg["target"]}
Target idle: {cfg["idle"]}
Map: {cfg["map"]}
Platform: {cfg["prop"]}
Camera: {cfg["camera"]}

SCENE {scene_number}/{total}:
Action focus: {focus}
Obstacle: {obstacle or "none"}
Maneuver: {maneuver or "standard run"}
{final_note}

CONTINUITY RULE:
The scene must start from the exact state shown in the attached bridge image
when a bridge image exists. Preserve cause-and-effect and spatial geography.

OUTPUT ONLY THE FINAL ENGLISH VIDEO PROMPT.
"""

    try:
        result = ask(
            prompt,
            parts=previous_frame_parts,
            json_mode=False,
        )
        st.session_state.scene_prompts[scene_number] = validate_prompt_text(result)
        return True
    except Exception as exc:
        st.error(f"Prompt Scene {scene_number} gagal: {exc}")
        return False


# ============================================================
# UI
# ============================================================
def render_home() -> None:
    st.title("🎬 UGC Remix Studio V15")
    st.caption(APP_VERSION)

    st.header("1. Reference")
    uploaded = st.file_uploader(
        f"Upload video reference (maks {MAX_FILE_SIZE_MB} MB)",
        type=["mp4", "mov", "webm", "m4v"],
        key="ref_file_input",
    )

    if uploaded is not None:
        data = uploaded.getvalue()
        if len(data) > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.error(f"File terlalu besar. Maksimum {MAX_FILE_SIZE_MB} MB.")
        else:
            st.session_state.reference_bytes = data
            st.session_state.reference_name = uploaded.name
            st.session_state.reference_mime = uploaded.type or "video/mp4"
            st.success(
                f"Reference siap: {uploaded.name} "
                f"({len(data) / 1024 / 1024:.1f} MB)"
            )

    st.text_area(
        "Atau deskripsi reference",
        key="reference_text",
        height=90,
    )

    st.header("2. Remix Identity")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.selectbox("Runner", RUNNER_PRESETS, key="runner_choice")
        if st.session_state.runner_choice == "Custom / ketik sendiri":
            st.text_input("Deskripsi runner", key="custom_runner")

    with c2:
        st.selectbox("Target ragdoll", TARGET_DOLL_PRESETS, key="target_doll_choice")

    with c3:
        st.selectbox("Target idle", TARGET_IDLE_PRESETS, key="target_idle_choice")

    st.header("3. Environment")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.selectbox("Map", MAP_OPTIONS, key="selected_map")

    with c2:
        st.selectbox("Platform", PROP_STAND_OPTIONS, key="selected_prop_stand")

    with c3:
        st.selectbox("Climax", CLIMAX_ACTION_OPTIONS, key="selected_climax_action")

    st.header("4. Visual / Duration")
    c1, c2 = st.columns(2)

    with c1:
        st.selectbox("Visual style", STYLE_OPTIONS, key="visual_style")
        st.selectbox("Camera", CAMERA_OPTIONS, key="selected_camera")
        st.selectbox("Aspect ratio", ASPECT_OPTIONS, key="aspect_ratio")

    with c2:
        st.selectbox("Target duration", list(DURATION_SCENES.keys()), key="duration")
        st.text_area("Instruksi tambahan", key="custom_instruction", height=100)

    st.header("5. Per-scene settings")
    configured = (
        DURATION_SCENES.get(st.session_state.duration, 0)
        or st.session_state.detected_scenes
    )
    target_seconds = configured * 8
    duration_note = " — grid proyek 38 scene = 304 detik" if configured == 38 else ""
    st.write(f"Total scene settings: **{configured}** ({target_seconds} detik target{duration_note})")

    for i in range(1, configured + 1):
        a, b = st.columns(2)

        with a:
            chosen = st.selectbox(
                f"Scene {i} obstacle",
                list(OBSTACLE_OPTIONS.keys()),
                key=f"obstacle_{i}",
            )
            st.session_state.user_scene_obstacles[i] = OBSTACLE_OPTIONS[chosen]

        with b:
            chosen = st.selectbox(
                f"Scene {i} maneuver",
                MANEUVER_OPTIONS,
                key=f"maneuver_{i}",
            )
            st.session_state.user_scene_maneuvers[i] = chosen

    st.divider()

    if st.button("🔍 ANALYZE + AUTO REMIX", type="primary", use_container_width=True):
        run_analysis()


def render_analysis() -> None:
    st.title("🔍 Reference Analysis")
    analysis = st.session_state.get("analysis", {})

    if not analysis:
        st.info("Belum ada hasil analisis.")
        return

    st.success(
        f"Model aktif: **{st.session_state.get('active_model') or '-'}**"
    )

    duration = st.session_state.get("detected_duration_seconds")
    if duration:
        st.write(f"Reference duration: **{duration:.1f} detik**")

    extension = st.session_state.get("duration_extension", {})
    if extension.get("added_seconds", 0) > 0:
        st.info(
            f"Target diperluas ke {extension['target_seconds']} detik "
            f"agar pas dengan grid 8 detik. Tambahan: "
            f"{extension['added_seconds']} detik."
        )

    orig = analysis.get("original_reference", {})
    remix = analysis.get("remixed_mutation", {})

    a, b = st.columns(2)

    with a:
        st.subheader("Reference")
        st.write("Runner:", orig.get("runner_asli", "-"))
        st.write("Target:", orig.get("boss_asli", "-"))
        st.write("Track:", orig.get("track_asli", "-"))

    with b:
        st.subheader("Remix")
        st.write("Runner:", remix.get("runner_baru", "-"))
        st.write("Target:", remix.get("boss_baru", "-"))
        st.write("Camera:", remix.get("camera_movement", "-"))

    st.subheader("Storyboard")
    for item in analysis.get("storyboard_plan", []):
        st.write(
            f"**Scene {item.get('scene', '?')}** — "
            f"{item.get('fokus_aksi', '-')}"
        )

    if st.button("➡️ Buka Scene 1", type="primary", use_container_width=True):
        st.session_state.current_scene = 1
        go("scenes")


def render_scenes() -> None:
    total = scene_count()
    current = st.session_state.current_scene

    st.title("🎥 Sequential Flow / Veo Prompt Generator")
    st.write(f"### Scene {current} / {total}")

    if current > 1:
        st.info(
            "Visual Bridge aktif: screenshot last frame scene sebelumnya "
            "menjadi input continuity scene ini."
        )

    if current not in st.session_state.scene_prompts:
        if st.button(
            f"Generate Prompt Scene {current}",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner(f"Generating Scene {current}..."):
                if generate_scene_prompt(current):
                    st.rerun()

    if current in st.session_state.scene_prompts:
        st.text_area(
            "Prompt untuk Flow/Veo",
            value=st.session_state.scene_prompts[current],
            height=220,
        )

        st.subheader("Visual Bridge")
        st.caption(
            "Setelah video scene ini dibuat di Flow/Veo, upload screenshot "
            "last frame-nya. Screenshot ini wajib sebelum scene berikutnya."
        )

        uploaded_frame = st.file_uploader(
            f"Upload Last Frame Scene {current}",
            type=["png", "jpg", "jpeg", "webp"],
            key=f"frame_upload_{current}",
        )

        if uploaded_frame is not None:
            signature = _frame_signature(uploaded_frame)
            st.session_state.scene_frames[current] = uploaded_frame
            st.session_state.scene_frame_signatures[current] = signature
            st.success(
                f"Last frame Scene {current} tersimpan "
                f"(bridge signature {signature[:12]}...)."
            )

        st.divider()

        previous_col, next_col = st.columns(2)

        with previous_col:
            if current > 1 and st.button(
                "← Scene sebelumnya",
                use_container_width=True,
            ):
                st.session_state.current_scene -= 1
                st.rerun()

        with next_col:
            if current < total:
                bridge_ready = bool(
                    st.session_state.scene_frames.get(current)
                    and st.session_state.scene_frame_signatures.get(current)
                )

                if st.button(
                    "Scene berikutnya →",
                    type="primary",
                    disabled=not bridge_ready,
                    use_container_width=True,
                ):
                    st.session_state.current_scene += 1
                    st.rerun()

                if not bridge_ready:
                    st.warning(
                        "Scene berikutnya dikunci. Upload last frame "
                        "scene ini terlebih dahulu."
                    )
            else:
                st.success(
                    "Semua scene selesai. Generate metadata SEO setelah "
                    "memeriksa prompt akhir."
                )

    if current == total and current in st.session_state.scene_prompts:
        st.divider()
        if st.button("🚀 Generate SEO", type="primary", use_container_width=True):
            generate_seo()


def generate_seo() -> None:
    analysis = st.session_state.get("analysis", {})

    prompt = f"""
Create SEO metadata for this fictional 3D game-comedy video.

Return JSON only:
{{
  "titles": ["title 1", "title 2", "title 3"],
  "description": "...",
  "hashtags": ["#...", "..."],
  "tags": ["...", "..."]
}}

Keep it family-friendly and original.
Do not use copyrighted character names or trademark-heavy bait.

STORY DATA:
{json.dumps(analysis, ensure_ascii=False)}
"""

    try:
        raw = ask(prompt, json_mode=True)
        data = extract_json(raw)
        if not isinstance(data, dict):
            raise ValueError("SEO response bukan object.")
        st.session_state.seo = data
    except Exception as exc:
        st.error(f"SEO gagal: {exc}")


def render_seo() -> None:
    st.title("🚀 SEO Center")
    data = st.session_state.get("seo", {})

    if data:
        st.json(data)
    else:
        st.info("SEO belum dibuat.")


# ============================================================
# SIDEBAR / ROUTING
# ============================================================
with st.sidebar:
    st.title("🧭 Navigation")
    st.caption(f"Version {APP_VERSION}")

    st.text_input("Gemini API Key", key="api_key", type="password")

    if st.button("🏠 Home", use_container_width=True):
        go("home")

    if st.button("🔍 Analysis", use_container_width=True):
        go("analysis")

    if st.button("🎥 Scenes", use_container_width=True):
        go("scenes")

    if st.button("🚀 SEO", use_container_width=True):
        go("seo")

    st.divider()

    if st.button("♻️ Reset Project", use_container_width=True):
        reset_project()


page = st.session_state.get("page", "home")

if page == "home":
    render_home()
elif page == "analysis":
    render_analysis()
elif page == "scenes":
    render_scenes()
elif page == "seo":
    render_seo()
else:
    render_home()
