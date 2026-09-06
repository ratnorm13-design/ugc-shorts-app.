import json
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
    page_title="UGC Remix Studio",
    page_icon="🎬",
    layout="wide",
)

MODEL_NAME = "gemini-3.6-flash"

DURATION_SCENES = {
    "8 seconds": 1,
    "16 seconds": 2,
    "24 seconds": 3,
    "32 seconds": 4,
    "40 seconds": 5,
    "48 seconds": 6,
    "56 seconds": 7,
    "1 minute": 8,
    "1.5 minutes": 12,
    "2 minutes": 15,
    "2.5 minutes": 19,
    "3 minutes": 23,
}

STYLE_OPTIONS = [
    "Realistic cinematic",
    "3D animation",
    "2D animation",
    "Stylized comedy",
    "Cute family-friendly",
    "Documentary / realistic",
    "Action cinematic",
    "Custom",
]

ASPECT_OPTIONS = [
    "9:16 — Shorts / Reels / TikTok",
    "16:9 — YouTube",
    "1:1 — Square",
]

REFERENCE_OPTIONS = [
    "Video",
    "Screenshots",
    "Text / idea",
]


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "page": "home",
    "api_key": "",

    "reference_type": "Video",
    "reference_file": None,
    "reference_files": [],
    "reference_text": "",

    "visual_style": "Realistic cinematic",
    "aspect_ratio": "9:16 — Shorts / Reels / TikTok",
    "duration": "8 seconds",
    "custom_instruction": "",

    "originality_guard": True,

    "analysis": {},
    "concepts": [],
    "selected_concept": None,
    "selected_concept_index": None,

    "storyboard": [],
    "scene_prompts": {},
    "scene_frames": {},
    "current_scene": 1,

    "seo": {},
}


for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPERS
# ============================================================

def reset_project():
    st.session_state.page = "home"

    st.session_state.reference_file = None
    st.session_state.reference_files = []
    st.session_state.reference_text = ""

    st.session_state.analysis = {}
    st.session_state.concepts = []
    st.session_state.selected_concept = None
    st.session_state.selected_concept_index = None

    st.session_state.storyboard = []
    st.session_state.scene_prompts = {}
    st.session_state.scene_frames = {}
    st.session_state.current_scene = 1

    st.session_state.seo = {}


def get_client():
    key = st.session_state.api_key.strip()

    if not key:
        st.error("Masukkan Gemini API Key di sidebar dulu.")
        return None

    try:
        return genai.Client(api_key=key)
    except Exception as e:
        st.error(f"Gagal membuat Gemini client: {e}")
        return None


def extract_json(text: str) -> Any:
    text = text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.I,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    try:
        return json.loads(text)
    except Exception:
        pass

    starts = [
        text.find("{"),
        text.find("["),
    ]

    starts = [
        x for x in starts
        if x >= 0
    ]

    if not starts:
        raise ValueError(
            "Respons AI tidak berisi JSON yang valid."
        )

    start = min(starts)

    for end in range(
        len(text),
        start,
        -1,
    ):
        candidate = text[start:end].strip()

        try:
            return json.loads(candidate)
        except Exception:
            continue

    raise ValueError(
        "Tidak bisa membaca JSON dari respons AI."
    )


def text_response(
    client,
    prompt,
    parts=None,
):
    contents = [prompt]

    if parts:
        contents.extend(parts)

    last_error = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                ),
            )

            return response.text or ""

        except Exception as e:
            last_error = e

            if (
                "503" in str(e)
                or "UNAVAILABLE" in str(e)
            ):
                time.sleep(
                    3 * (attempt + 1)
                )
                continue

            raise e

    raise RuntimeError(
        "Gemini sedang sibuk setelah 3 percobaan. "
        "Coba tekan tombol lagi beberapa saat kemudian.\n\n"
        f"Error: {last_error}"
    )


def upload_to_gemini(
    client,
    uploaded_file,
):
    if uploaded_file is None:
        return None

    try:
        mime_type = getattr(
            uploaded_file,
            "type",
            None,
        )

        config = {
            "display_name": uploaded_file.name,
        }

        if mime_type:
            config["mime_type"] = mime_type

        return client.files.upload(
            file=uploaded_file,
            config=config,
        )

    except Exception as e:
        st.warning(
            f"File tidak bisa dikirim ke Gemini: {e}"
        )
        return None


def file_part(
    client,
    uploaded_file,
):
    remote = upload_to_gemini(
        client,
        uploaded_file,
    )

    if not remote:
        return []

    try:
        return [
            types.Part.from_uri(
                file_uri=remote.uri,
                mime_type=remote.mime_type,
            )
        ]
    except Exception:
        return [remote]


def scene_count():
    return DURATION_SCENES[
        st.session_state.duration
    ]


def selected_concept():
    return (
        st.session_state.selected_concept
        or {}
    )


def concept_text(concept):
    return json.dumps(
        concept,
        ensure_ascii=False,
        indent=2,
    )


def safe_text(value):
    if value is None:
        return ""

    if isinstance(value, list):
        return ", ".join(
            str(x) for x in value
        )

    return str(value)


def go(page):
    st.session_state.page = page
    st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("🎬 UGC Remix Studio")

    st.caption(
        "Reference → Remix → Storyboard → Flow/Veo Prompts"
    )

    st.text_input(
        "Gemini API Key",
        type="password",
        key="api_key",
        placeholder="AIza...",
    )

    st.divider()

    if st.button(
        "🏠 Home",
        use_container_width=True,
    ):
        go("home")

    if st.button(
        "💡 Concepts",
        use_container_width=True,
    ):
        go("concepts")

    if st.button(
        "🧩 Storyboard",
        use_container_width=True,
    ):
        go("storyboard")

    if st.button(
        "🎥 Scene Prompts",
        use_container_width=True,
    ):
        go("scenes")

    if st.button(
        "🔎 YouTube SEO",
        use_container_width=True,
    ):
        go("seo")

    st.divider()

    if st.button(
        "🆕 New Project",
        use_container_width=True,
    ):
        reset_project()
        st.rerun()


# ============================================================
# HOME
# ============================================================

def render_home():

    st.title(
        "🎬 Turn Any Reference Into an Original Video Blueprint"
    )

    st.write(
        "Upload a reference video, screenshots, "
        "or an idea. AI analyzes the entertainment "
        "logic, creates 3 original remix concepts, "
        "then builds a scene-by-scene workflow "
        "for Google Flow/Veo."
    )

    st.subheader("1. Reference")

    reference_type = st.radio(
        "Pilih sumber reference",
        REFERENCE_OPTIONS,
        horizontal=True,
        key="reference_type",
    )

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    if reference_type == "Video":

        video = st.file_uploader(
            "Upload reference video",
            type=[
                "mp4",
                "mov",
                "webm",
                "avi",
                "mkv",
            ],
            key="reference_video_widget",
            help=(
                "Upload video yang ingin dianalisis."
            ),
        )

        st.session_state.reference_file = video
        st.session_state.reference_files = []

    # --------------------------------------------------------
    # SCREENSHOTS
    # --------------------------------------------------------

    elif reference_type == "Screenshots":

        screenshots = st.file_uploader(
            "Upload screenshots",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
            ],
            accept_multiple_files=True,
            key="reference_screenshots_widget",
        )

        st.session_state.reference_files = screenshots
        st.session_state.reference_file = None

    # --------------------------------------------------------
    # TEXT / IDEA
    # --------------------------------------------------------

    else:

        reference_text = st.text_area(
            "Jelaskan reference / ide",
            value=st.session_state.reference_text,
            height=180,
            placeholder=(
                "Contoh: video komedi tentang "
                "seekor kucing melakukan sesuatu "
                "lalu terjadi kejutan lucu..."
            ),
            key="reference_text_widget",
        )

        st.session_state.reference_text = (
            reference_text
        )

        st.session_state.reference_file = None
        st.session_state.reference_files = []

    # --------------------------------------------------------
    # CREATIVE SETTINGS
    # --------------------------------------------------------

    st.subheader("2. Creative Settings")

    col1, col2 = st.columns(2)

    with col1:

        st.selectbox(
            "Visual Style",
            STYLE_OPTIONS,
            key="visual_style",
        )

        st.selectbox(
            "Aspect Ratio",
            ASPECT_OPTIONS,
            key="aspect_ratio",
        )

    with col2:

        st.selectbox(
            "Video Duration",
            list(DURATION_SCENES.keys()),
            key="duration",
        )

        st.text_area(
            "Creative Instruction",
            key="custom_instruction",
            height=110,
            placeholder=(
                "Contoh: lebih lucu, lebih cepat, "
                "family-friendly, ending lebih kuat..."
            ),
        )

    count = scene_count()

    st.info(
        f"Durasi {st.session_state.duration} "
        f"= {count} scene. "
        "Setiap scene dirancang sekitar 8 detik."
    )

    # --------------------------------------------------------
    # ORIGINALITY + SAFETY
    # --------------------------------------------------------

    st.subheader("3. Originality & Safety Guard")

    st.checkbox(
        "Aktifkan originality + transformation guard",
        value=True,
        key="originality_guard",
    )

    st.write(
        "AI mempertahankan inti hiburan seperti "
        "hook, cause/effect, timing, emotional goal, "
        "dan payoff. Namun execution dibuat berbeda "
        "melalui visual design, setting, wardrobe, "
        "props, camera, lighting, dialogue, dan "
        "sound design."
    )

    st.caption(
        "Jika reference mengandung aksi berbahaya, "
        "elemen berbahaya akan diubah menjadi versi "
        "aman/fake/non-functional tanpa memberikan "
        "instruksi melakukan aksi berbahaya."
    )

    # --------------------------------------------------------
    # ANALYZE
    # --------------------------------------------------------

    if st.button(
        "🚀 ANALYZE + AUTO REMIX",
        type="primary",
        use_container_width=True,
    ):
        run_analysis()


# ============================================================
# ANALYSIS + AUTO REMIX
# ============================================================

def run_analysis():

    client = get_client()

    if not client:
        return

    reference_type = (
        st.session_state.reference_type
    )

    prompt = f"""
You are the creative director of an
original-content video production system.

Analyze the supplied reference and create
exactly 3 ORIGINAL remix concepts.

IMPORTANT:

- Preserve the main subject/type when it is
  important to the reference. For example, if
  the reference centers on a cat, keep the
  main subject a cat rather than randomly
  replacing it with a robot or unrelated creature.

- Preserve the core comedic or dramatic
  sequence when that sequence is what makes
  the reference entertaining.

- Preserve useful high-level structure:
  hook, cause/effect, escalation, emotional
  goal, payoff, timing, and pacing logic.

- Do NOT copy recognizable characters,
  brands, logos, watermarks, exact dialogue,
  distinctive costumes, exact shots,
  or distinctive creator/studio identity.

- Do not reproduce copyrighted material
  verbatim.

- Make the final execution sufficiently
  original through visual and production
  details.

- If the reference contains dangerous
  activity, do NOT reproduce instructions
  for performing it. Convert the dangerous
  element into an obviously fake, unplugged,
  toy, simulated, or otherwise harmless
  version while keeping the narrative logic.

- Keep the result family-friendly and suitable
  for mainstream YouTube.

- The chosen concept will later become
  exactly 1–23 scenes depending on duration.

Settings:

Reference type:
{reference_type}

Visual style:
{st.session_state.visual_style}

Aspect ratio:
{st.session_state.aspect_ratio}

Duration:
{st.session_state.duration}

Scene count:
{scene_count()}

Creative instruction:
{st.session_state.custom_instruction}

Return ONLY valid JSON:

{{
  "analysis": {{
    "source_summary": "...",
    "niche": "...",
    "main_subject": "...",
    "hook": "...",
    "cause_effect": "...",
    "emotional_goal": "...",
    "pacing_logic": "...",
    "payoff": "...",
    "key_visual_mechanics": [
      "...",
      "..."
    ],
    "transformation_notes": [
      "...",
      "..."
    ]
  }},

  "concepts": [
    {{
      "title": "...",
      "one_line_pitch": "...",
      "niche": "...",
      "main_subjects": ["..."],
      "hook": "...",
      "story_arc": "...",
      "setting": "...",
      "visual_direction": "...",
      "comedy_or_drama_engine": "...",
      "ending_payoff": "...",
      "why_it_is_original": "..."
    }},

    {{
      "title": "...",
      "one_line_pitch": "...",
      "niche": "...",
      "main_subjects": ["..."],
      "hook": "...",
      "story_arc": "...",
      "setting": "...",
      "visual_direction": "...",
      "comedy_or_drama_engine": "...",
      "ending_payoff": "...",
      "why_it_is_original": "..."
    }},

    {{
      "title": "...",
      "one_line_pitch": "...",
      "niche": "...",
      "main_subjects": ["..."],
      "hook": "...",
      "story_arc": "...",
      "setting": "...",
      "visual_direction": "...",
      "comedy_or_drama_engine": "...",
      "ending_payoff": "...",
      "why_it_is_original": "..."
    }}
  ]
}}
"""

    parts = []

    # --------------------------------------------------------
    # VIDEO REFERENCE
    # --------------------------------------------------------

    if (
        reference_type == "Video"
        and st.session_state.reference_file
    ):
        parts = file_part(
            client,
            st.session_state.reference_file,
        )

    # --------------------------------------------------------
    # SCREENSHOT REFERENCES
    # --------------------------------------------------------

    elif reference_type == "Screenshots":

        for uploaded_file in (
            st.session_state.reference_files
        ):
            parts.extend(
                file_part(
                    client,
                    uploaded_file,
                )
            )

    # --------------------------------------------------------
    # TEXT REFERENCE
    # --------------------------------------------------------

    elif reference_type == "Text / idea":

        text = (
            st.session_state.reference_text
            .strip()
        )

        if text:
            parts.append(
                f"""
USER REFERENCE TEXT:

{text}
"""
            )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if (
        reference_type == "Video"
        and not parts
    ):
        st.warning(
            "Upload reference video dulu."
        )
        return

    if (
        reference_type == "Screenshots"
        and not parts
    ):
        st.warning(
            "Upload minimal satu screenshot dulu."
        )
        return

    if (
        reference_type == "Text / idea"
        and not st.session_state.reference_text.strip()
    ):
        st.warning(
            "Masukkan reference / ide dulu."
        )
        return

    # --------------------------------------------------------
    # GEMINI ANALYSIS
    # --------------------------------------------------------

    with st.spinner(
        "AI sedang menganalisis reference "
        "dan membuat 3 remix..."
    ):

        try:

            raw_response = text_response(
                client,
                prompt,
                parts,
            )

            data = extract_json(
                raw_response
            )

            concepts = data.get(
                "concepts",
                [],
            )

            if len(concepts) != 3:
                raise ValueError(
                    "AI tidak mengembalikan tepat 3 konsep."
                )

            st.session_state.analysis = (
                data.get(
                    "analysis",
                    {},
                )
            )

            st.session_state.concepts = (
                concepts
            )

            st.session_state.selected_concept = None
            st.session_state.selected_concept_index = None

            st.session_state.storyboard = []
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}
            st.session_state.current_scene = 1

            go("concepts")

        except Exception as e:

            st.error(
                f"Gagal membuat remix: {e}"
            )


# ============================================================
# END PART 1
# ============================================================
# PART 2 — CONCEPTS + STORYBOARD
# ============================================================


# ============================================================
# CONCEPTS PAGE
# ============================================================

def render_concepts():

    st.title("💡 AI Remix Concepts")

    if not st.session_state.concepts:
        st.info(
            "Belum ada konsep. Kembali ke Home dan jalankan "
            "AI Analyzer + Auto Remix terlebih dahulu."
        )

        if st.button(
            "← Kembali ke Home",
            use_container_width=True,
        ):
            go("home")

        return

    # --------------------------------------------------------
    # ANALYSIS SUMMARY
    # --------------------------------------------------------

    analysis = st.session_state.analysis

    if analysis:

        with st.expander(
            "🔍 AI Analysis — Reference Breakdown",
            expanded=True,
        ):

            col1, col2 = st.columns(2)

            with col1:
                st.write(
                    "**Source Summary**"
                )
                st.write(
                    safe_text(
                        analysis.get(
                            "source_summary"
                        )
                    )
                )

                st.write(
                    "**Niche**"
                )
                st.write(
                    safe_text(
                        analysis.get(
                            "niche"
                        )
                    )
                )

                st.write(
                    "**Main Subject**"
                )
                st.write(
                    safe_text(
                        analysis.get(
                            "main_subject"
                        )
                    )
                )

                st.write(
                    "**Hook**"
                )
                st.write(
                    safe_text(
                        analysis.get(
                            "hook"
                        )
                    )
                )

            with col2:
                st.write(
                    "**Cause / Effect**"
                )
                st.write(
                    safe_text(
                        analysis.get(
                            "cause_effect"
                        )
                    )
                )

                st.write(
                    "**Emotional Goal**"
                )
                st.write(
                    safe_text(
                        analysis.get(
                            "emotional_goal"
                        )
                    )
                )

                st.write(
                    "**Pacing Logic**"
                )
                st.write(
                    safe_text(
                        analysis.get(
                            "pacing_logic"
                        )
                    )
                )

                st.write(
                    "**Payoff**"
                )
                st.write(
                    safe_text(
                        analysis.get(
                            "payoff"
                        )
                    )
                )

            mechanics = analysis.get(
                "key_visual_mechanics",
                [],
            )

            if mechanics:
                st.write(
                    "**Key Visual Mechanics**"
                )

                for item in mechanics:
                    st.write(
                        f"• {item}"
                    )

            transformations = analysis.get(
                "transformation_notes",
                [],
            )

            if transformations:
                st.write(
                    "**Transformation Notes**"
                )

                for item in transformations:
                    st.write(
                        f"• {item}"
                    )

    st.divider()

    st.subheader(
        "🎯 Pilih 1 dari 3 konsep"
    )

    st.caption(
        "AI membuat tepat 3 konsep. Pilih satu konsep "
        "untuk dilanjutkan menjadi storyboard."
    )

    concepts = st.session_state.concepts

    for index, concept in enumerate(
        concepts
    ):

        title = safe_text(
            concept.get(
                "title",
                f"Concept {index + 1}",
            )
        )

        pitch = safe_text(
            concept.get(
                "one_line_pitch",
                "",
            )
        )

        with st.container(
            border=True
        ):

            st.markdown(
                f"### {index + 1}. {title}"
            )

            if pitch:
                st.write(
                    f"**Pitch:** {pitch}"
                )

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    "**Niche**"
                )
                st.write(
                    safe_text(
                        concept.get(
                            "niche"
                        )
                    )
                )

                st.write(
                    "**Main Subject**"
                )
                st.write(
                    safe_text(
                        concept.get(
                            "main_subjects"
                        )
                    )
                )

                st.write(
                    "**Hook**"
                )
                st.write(
                    safe_text(
                        concept.get(
                            "hook"
                        )
                    )
                )

                st.write(
                    "**Story Arc**"
                )
                st.write(
                    safe_text(
                        concept.get(
                            "story_arc"
                        )
                    )
                )

            with col2:

                st.write(
                    "**Setting**"
                )
                st.write(
                    safe_text(
                        concept.get(
                            "setting"
                        )
                    )
                )

                st.write(
                    "**Visual Direction**"
                )
                st.write(
                    safe_text(
                        concept.get(
                            "visual_direction"
                        )
                    )
                )

                st.write(
                    "**Comedy / Drama Engine**"
                )
                st.write(
                    safe_text(
                        concept.get(
                            "comedy_or_drama_engine"
                        )
                    )
                )

                st.write(
                    "**Ending Payoff**"
                )
                st.write(
                    safe_text(
                        concept.get(
                            "ending_payoff"
                        )
                    )
                )

            st.write(
                "**Why It Is Original**"
            )
            st.write(
                safe_text(
                    concept.get(
                        "why_it_is_original"
                    )
                )
            )

            if st.button(
                f"✅ Pilih Concept {index + 1}",
                key=f"select_concept_{index}",
                type="primary",
                use_container_width=True,
            ):

                st.session_state.selected_concept = (
                    concept
                )

                st.session_state.selected_concept_index = (
                    index
                )

                st.session_state.storyboard = []
                st.session_state.scene_prompts = {}
                st.session_state.scene_frames = {}
                st.session_state.current_scene = 1

                go("storyboard")


# ============================================================
# STORYBOARD GENERATION
# ============================================================

def generate_storyboard():

    client = get_client()

    if not client:
        return

    concept = selected_concept()

    if not concept:
        st.warning(
            "Pilih konsep terlebih dahulu."
        )
        return

    total_scenes = scene_count()

    prompt = f"""
You are a professional storyboard director.

Create a complete storyboard for the selected
original video concept.

The video duration is:
{st.session_state.duration}

The exact number of scenes MUST be:
{total_scenes}

Each scene is approximately 8 seconds.

IMPORTANT SCENE RULES:

1. Return EXACTLY {total_scenes} scenes.
2. Scene numbers must start at 1.
3. Scene numbers must end at {total_scenes}.
4. Do not skip scene numbers.
5. Do not add extra scenes.
6. Preserve the selected concept's core story.
7. Preserve the main subject identity throughout.
8. Keep important actions logically continuous.
9. Every scene must connect naturally to the next.
10. Scene {total_scenes} must contain the final payoff.
11. Keep the sequence entertaining and easy to
    understand without relying on text.
12. Do not copy exact shots from the reference.
13. Do not use recognizable copyrighted characters,
    logos, brands, or exact dialogue.
14. Keep the production family-friendly.
15. If a dangerous action exists, convert only the
    dangerous element into a clearly safe,
    fake, simulated, toy, unplugged, or
    non-functional version.

CONTINUITY IS VERY IMPORTANT.

For every scene, explicitly define:

- What the subject is doing.
- Where the subject is.
- Where important props are.
- The subject's position.
- The subject's movement direction.
- The camera position.
- The camera movement.
- The visual state at the END of the scene.
- What must continue into the NEXT scene.

Do not randomly teleport subjects or props.

Selected concept:

{concept_text(concept)}

Visual style:
{st.session_state.visual_style}

Aspect ratio:
{st.session_state.aspect_ratio}

Creative instruction:
{st.session_state.custom_instruction}

Return ONLY valid JSON:

{{
  "storyboard": [
    {{
      "scene": 1,
      "duration_seconds": 8,
      "purpose": "...",
      "visual": "...",
      "action": "...",
      "camera": "...",
      "subject_state": "...",
      "prop_state": "...",
      "end_state": "...",
      "next_scene_continuity": "...",
      "audio": "...",
      "transition": "..."
    }}
  ]
}}
"""

    with st.spinner(
        f"Membuat storyboard {total_scenes} scene..."
    ):

        try:

            raw_response = text_response(
                client,
                prompt,
            )

            data = extract_json(
                raw_response
            )

            storyboard = data.get(
                "storyboard",
                [],
            )

            if len(storyboard) != total_scenes:
                raise ValueError(
                    f"Storyboard harus berisi tepat "
                    f"{total_scenes} scene, tetapi AI "
                    f"menghasilkan {len(storyboard)}."
                )

            # ------------------------------------------------
            # NORMALIZE SCENE NUMBERS
            # ------------------------------------------------

            normalized = []

            for index, scene in enumerate(
                storyboard
            ):

                scene = dict(scene)

                scene["scene"] = index + 1

                if not scene.get(
                    "duration_seconds"
                ):
                    scene[
                        "duration_seconds"
                    ] = 8

                normalized.append(
                    scene
                )

            st.session_state.storyboard = (
                normalized
            )

            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}
            st.session_state.current_scene = 1

            st.success(
                f"Storyboard berhasil dibuat: "
                f"{total_scenes} scene."
            )

        except Exception as e:

            st.error(
                f"Gagal membuat storyboard: {e}"
            )


# ============================================================
# ACTION CONTINUITY ENGINE
# ============================================================

def build_action_continuity(
    scene_number,
):

    storyboard = (
        st.session_state.storyboard
    )

    if not storyboard:
        return ""

    current_index = scene_number - 1

    if current_index < 0:
        current_index = 0

    if current_index >= len(
        storyboard
    ):
        current_index = (
            len(storyboard) - 1
        )

    current_scene = storyboard[
        current_index
    ]

    previous_scene = None

    if current_index > 0:
        previous_scene = storyboard[
            current_index - 1
        ]

    previous_text = ""

    if previous_scene:

        previous_text = f"""
PREVIOUS SCENE STATE:

Subject:
{safe_text(previous_scene.get("subject_state"))}

Props:
{safe_text(previous_scene.get("prop_state"))}

Ending state:
{safe_text(previous_scene.get("end_state"))}

Required continuity:
{safe_text(previous_scene.get("next_scene_continuity"))}
"""

    current_text = f"""
CURRENT SCENE:

Scene number:
{scene_number}

Purpose:
{safe_text(current_scene.get("purpose"))}

Visual:
{safe_text(current_scene.get("visual"))}

Action:
{safe_text(current_scene.get("action"))}

Camera:
{safe_text(current_scene.get("camera"))}

Subject state:
{safe_text(current_scene.get("subject_state"))}

Prop state:
{safe_text(current_scene.get("prop_state"))}

Ending state:
{safe_text(current_scene.get("end_state"))}
"""

    return f"""
ACTION CONTINUITY ENGINE

{previous_text}

{current_text}

CONTINUITY REQUIREMENTS:

- Start the current scene from the logical
  physical state established by the previous scene.
- Keep the same main subject identity.
- Keep wardrobe / appearance consistent.
- Keep important props consistent.
- Keep the environment geographically consistent.
- Continue movement direction logically.
- Do not teleport the subject.
- Do not randomly change prop positions.
- Do not reset the scene.
- Preserve the intended action and comedic timing.
- If the previous scene ended during an action,
  continue that action naturally.
- The final frame of the current scene must create
  a logical starting point for the next scene.
"""


# ============================================================
# STORYBOARD PAGE
# ============================================================

def render_storyboard():

    st.title("🧩 Storyboard")

    concept = selected_concept()

    if not concept:

        st.info(
            "Belum ada konsep yang dipilih."
        )

        if st.button(
            "← Kembali ke Concepts",
            use_container_width=True,
        ):
            go("concepts")

        return

    st.subheader(
        "Selected Concept"
    )

    st.markdown(
        f"### {safe_text(concept.get('title'))}"
    )

    st.write(
        safe_text(
            concept.get(
                "one_line_pitch"
            )
        )
    )

    st.divider()

    total_scenes = scene_count()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Duration",
            st.session_state.duration,
        )

    with col2:
        st.metric(
            "Scenes",
            total_scenes,
        )

    with col3:
        st.metric(
            "Scene Length",
            "≈ 8 sec",
        )

    st.info(
        f"Storyboard akan dibuat menjadi "
        f"tepat {total_scenes} scene."
    )

    if st.button(
        "🧩 GENERATE STORYBOARD",
        type="primary",
        use_container_width=True,
    ):
        generate_storyboard()

    if not st.session_state.storyboard:
        return

    st.divider()

    st.subheader(
        f"📋 {len(st.session_state.storyboard)} Scenes"
    )

    for scene in (
        st.session_state.storyboard
    ):

        number = scene.get(
            "scene",
            0,
        )

        title = (
            f"Scene {number}"
        )

        with st.expander(
            title,
            expanded=False,
        ):

            st.write(
                f"**Purpose:** "
                f"{safe_text(scene.get('purpose'))}"
            )

            st.write(
                f"**Visual:** "
                f"{safe_text(scene.get('visual'))}"
            )

            st.write(
                f"**Action:** "
                f"{safe_text(scene.get('action'))}"
            )

            st.write(
                f"**Camera:** "
                f"{safe_text(scene.get('camera'))}"
            )

            st.write(
                f"**Subject State:** "
                f"{safe_text(scene.get('subject_state'))}"
            )

            st.write(
                f"**Prop State:** "
                f"{safe_text(scene.get('prop_state'))}"
            )

            st.write(
                f"**End State:** "
                f"{safe_text(scene.get('end_state'))}"
            )

            st.write(
                f"**Next Scene Continuity:** "
                f"{safe_text(scene.get('next_scene_continuity'))}"
            )

            st.write(
                f"**Audio:** "
                f"{safe_text(scene.get('audio'))}"
            )

            st.write(
                f"**Transition:** "
                f"{safe_text(scene.get('transition'))}"
            )

    st.divider()

    if st.button(
        "➡️ Lanjut ke Scene Generator",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.current_scene = 1
        go("scenes")


# ============================================================
# END PART 2
# ============================================================
# PART 3 — SCENE GENERATOR + SEO + ROUTER
# ============================================================


# ============================================================
# SCENE PROMPT GENERATOR
# ============================================================

def generate_scene_prompt(scene_number):

    client = get_client()

    if not client:
        return

    storyboard = st.session_state.storyboard

    if not storyboard:
        st.warning(
            "Storyboard belum dibuat."
        )
        return

    if scene_number < 1:
        scene_number = 1

    if scene_number > len(storyboard):
        scene_number = len(storyboard)

    scene = storyboard[
        scene_number - 1
    ]

    concept = selected_concept()

    continuity = build_action_continuity(
        scene_number
    )

    previous_frame_note = ""

    if scene_number > 1:

        previous_frame_note = """
A LAST-FRAME SCREENSHOT FROM THE PREVIOUS
SCENE MAY BE PROVIDED.

If it is provided, treat that image as the
PRIMARY VISUAL CONTINUITY ANCHOR.

The current scene MUST begin from the
visual state shown in that screenshot.

Preserve:
- same main subject identity
- same appearance
- same wardrobe / markings
- same important props
- same environment
- same spatial geography
- same lighting direction
- same camera-side geography
- same physical position
- same ongoing motion state

Do NOT treat the screenshot as a new reference
to redesign.

Continue directly from it.

Do NOT reset the scene.
Do NOT teleport the subject.
Do NOT randomly replace props.
Do NOT change the main subject.

The current scene may develop the action
forward, but its opening visual state must
logically continue from the uploaded frame.
"""

    else:

        previous_frame_note = """
This is Scene 1.

There is no previous scene screenshot.

Establish the main subject, environment,
props, visual style, camera geography and
starting physical state clearly so later
scenes can maintain continuity.
"""

    prompt = f"""
You are an expert prompt engineer for
Google Flow / Veo video generation.

Create ONE production-ready video prompt
for Scene {scene_number}.

The final prompt MUST be written in ENGLISH.

The rest of this application uses Indonesian,
but the final Flow/Veo execution prompt must
be English.

SELECTED CONCEPT:

{concept_text(concept)}

PROJECT SETTINGS:

Visual style:
{st.session_state.visual_style}

Aspect ratio:
{st.session_state.aspect_ratio}

Duration:
{st.session_state.duration}

Current scene:
{scene_number} of {len(storyboard)}

STORYBOARD SCENE:

Purpose:
{safe_text(scene.get("purpose"))}

Visual:
{safe_text(scene.get("visual"))}

Action:
{safe_text(scene.get("action"))}

Camera:
{safe_text(scene.get("camera"))}

Subject state:
{safe_text(scene.get("subject_state"))}

Prop state:
{safe_text(scene.get("prop_state"))}

End state:
{safe_text(scene.get("end_state"))}

Next scene continuity:
{safe_text(scene.get("next_scene_continuity"))}

Audio:
{safe_text(scene.get("audio"))}

Transition:
{safe_text(scene.get("transition"))}

ACTION CONTINUITY:

{continuity}

{previous_frame_note}

ORIGINALITY RULES:

- Keep the main subject/type consistent with
  the selected concept and reference logic.
- Preserve the intended core action and
  comedic/dramatic timing.
- Do not randomly replace the main subject.
- Do not copy recognizable characters.
- Do not include logos, brands or watermarks.
- Do not reproduce exact dialogue from a
  copyrighted reference.
- Use original visual execution.
- Use original camera execution.
- Use original lighting and production details.
- Keep the content family-friendly.
- Do not imitate a living creator's distinctive
  style.
- Do not recreate an exact shot-for-shot copy.

SAFETY:

If the scene contains an inherently dangerous
action, do NOT provide instructions that teach
a person or animal how to perform that action.

Instead, change ONLY the dangerous element into
an obviously fake, simulated, unplugged, toy,
non-functional, or otherwise harmless version.

Keep the surrounding narrative logic and
comedic timing intact.

PROMPT QUALITY:

Describe:
- subject
- appearance
- environment
- important props
- action
- physical movement
- camera
- framing
- lens feel
- lighting
- atmosphere
- facial/body expression where relevant
- timing
- sound design
- ending visual state

Make the prompt practical for a video model.

Do not add explanations before or after it.

Return ONLY the final English video prompt.
"""

    parts = []

    # --------------------------------------------------------
    # PREVIOUS SCENE LAST-FRAME
    # --------------------------------------------------------

    if scene_number > 1:

        previous_frame = (
            st.session_state.scene_frames.get(
                scene_number - 1
            )
        )

        if previous_frame:

            parts.extend(
                file_part(
                    client,
                    previous_frame,
                )
            )

    # --------------------------------------------------------
    # GENERATE
    # --------------------------------------------------------

    with st.spinner(
        f"Generating Flow/Veo prompt for Scene "
        f"{scene_number}..."
    ):

        try:

            result = text_response(
                client,
                prompt,
                parts,
            )

            result = result.strip()

            if not result:
                raise ValueError(
                    "Gemini mengembalikan prompt kosong."
                )

            st.session_state.scene_prompts[
                scene_number
            ] = result

            st.success(
                f"Prompt Scene {scene_number} berhasil dibuat."
            )

        except Exception as e:

            st.error(
                f"Gagal membuat prompt Scene "
                f"{scene_number}: {e}"
            )


# ============================================================
# SCENE GENERATOR PAGE
# ============================================================

def render_scenes():

    st.title(
        "🎥 Scene Generator"
    )

    storyboard = (
        st.session_state.storyboard
    )

    if not storyboard:

        st.info(
            "Storyboard belum tersedia."
        )

        if st.button(
            "← Kembali ke Storyboard",
            use_container_width=True,
        ):
            go("storyboard")

        return

    total_scenes = len(
        storyboard
    )

    current = st.session_state.current_scene

    if current < 1:
        current = 1

    if current > total_scenes:
        current = total_scenes

    st.session_state.current_scene = current

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Current Scene",
            f"{current}/{total_scenes}",
        )

    with col2:
        st.metric(
            "Duration",
            st.session_state.duration,
        )

    with col3:
        st.metric(
            "Scene Length",
            "≈ 8 sec",
        )

    st.progress(
        current / total_scenes
    )

    st.divider()

    # --------------------------------------------------------
    # CURRENT STORYBOARD
    # --------------------------------------------------------

    scene = storyboard[
        current - 1
    ]

    st.subheader(
        f"🎬 Scene {current}"
    )

    with st.container(
        border=True
    ):

        st.write(
            f"**Purpose:** "
            f"{safe_text(scene.get('purpose'))}"
        )

        st.write(
            f"**Visual:** "
            f"{safe_text(scene.get('visual'))}"
        )

        st.write(
            f"**Action:** "
            f"{safe_text(scene.get('action'))}"
        )

        st.write(
            f"**Camera:** "
            f"{safe_text(scene.get('camera'))}"
        )

        st.write(
            f"**Subject State:** "
            f"{safe_text(scene.get('subject_state'))}"
        )

        st.write(
            f"**Prop State:** "
            f"{safe_text(scene.get('prop_state'))}"
        )

        st.write(
            f"**End State:** "
            f"{safe_text(scene.get('end_state'))}"
        )

        st.write(
            f"**Continuity:** "
            f"{safe_text(scene.get('next_scene_continuity'))}"
        )

    # --------------------------------------------------------
    # PREVIOUS FRAME
    # --------------------------------------------------------

    if current > 1:

        st.subheader(
            "🖼️ Previous Scene Last Frame"
        )

        st.caption(
            "Upload screenshot/frame terakhir dari "
            f"Scene {current - 1}. Frame ini digunakan "
            "sebagai continuity anchor untuk Scene "
            f"{current}."
        )

        uploaded_previous_frame = st.file_uploader(
            f"Upload last frame Scene {current - 1}",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
            ],
            key=f"scene_frame_{current - 1}",
        )

        if uploaded_previous_frame:

            st.session_state.scene_frames[
                current - 1
            ] = uploaded_previous_frame

            st.success(
                f"Last frame Scene {current - 1} siap "
                f"digunakan untuk Scene {current}."
            )

    else:

        st.info(
            "Scene 1 adalah titik awal video. "
            "Tidak perlu upload previous frame."
        )

    # --------------------------------------------------------
    # GENERATE BUTTON
    # --------------------------------------------------------

    st.divider()

    if st.button(
        f"✨ GENERATE PROMPT SCENE {current}",
        type="primary",
        use_container_width=True,
    ):

        if current > 1:

            if not st.session_state.scene_frames.get(
                current - 1
            ):

                st.warning(
                    f"Upload last frame Scene "
                    f"{current - 1} terlebih dahulu "
                    f"agar continuity Scene {current} "
                    "terjaga."
                )

                return

        generate_scene_prompt(
            current
        )

    # --------------------------------------------------------
    # GENERATED PROMPT
    # --------------------------------------------------------

    generated = (
        st.session_state.scene_prompts.get(
            current
        )
    )

    if generated:

        st.subheader(
            "📋 Final Flow / Veo Prompt"
        )

        st.text_area(
            "English prompt",
            value=generated,
            height=420,
            key=f"scene_prompt_display_{current}",
        )

        st.caption(
            "Copy prompt ini ke Google Flow/Veo "
            "untuk membuat scene."
        )

    # --------------------------------------------------------
    # NAVIGATION
    # --------------------------------------------------------

    st.divider()

    nav1, nav2, nav3 = st.columns(3)

    with nav1:

        if st.button(
            "⬅️ Previous",
            disabled=(current <= 1),
            use_container_width=True,
        ):

            st.session_state.current_scene = (
                current - 1
            )

            st.rerun()

    with nav2:

        if st.button(
            "🧩 Storyboard",
            use_container_width=True,
        ):

            go("storyboard")

    with nav3:

        if st.button(
            "Next ➡️",
            disabled=(current >= total_scenes),
            use_container_width=True,
        ):

            st.session_state.current_scene = (
                current + 1
            )

            st.rerun()

    # --------------------------------------------------------
    # SCENE STATUS
    # --------------------------------------------------------

    st.divider()

    generated_count = len(
        st.session_state.scene_prompts
    )

    frame_count = len(
        st.session_state.scene_frames
    )

    st.write(
        f"**Progress:** {generated_count}/{total_scenes} "
        f"scene prompts generated."
    )

    st.write(
        f"**Continuity frames:** {frame_count}/"
        f"{max(total_scenes - 1, 0)} uploaded."
    )


# ============================================================
# SEO GENERATOR
# ============================================================

def generate_seo():

    client = get_client()

    if not client:
        return

    concept = selected_concept()

    if not concept:
        st.warning(
            "Pilih konsep terlebih dahulu."
        )
        return

    prompt = f"""
You are a YouTube SEO strategist.

Create SEO metadata for an original,
family-friendly video based on this concept.

Concept:

{concept_text(concept)}

Duration:
{st.session_state.duration}

Aspect ratio:
{st.session_state.aspect_ratio}

Visual style:
{st.session_state.visual_style}

Requirements:

- Create a strong but natural YouTube title.
- Do not use misleading clickbait.
- Do not copy the reference title.
- Create a concise description.
- Create relevant search keywords.
- Create relevant hashtags.
- Keep everything original.
- Keep it suitable for mainstream YouTube.

Return ONLY valid JSON:

{{
  "title": "...",
  "description": "...",
  "keywords": [
    "...",
    "...",
    "...",
    "..."
  ],
  "hashtags": [
    "...",
    "...",
    "..."
  ]
}}
"""

    with st.spinner(
        "Generating YouTube SEO..."
    ):

        try:

            raw = text_response(
                client,
                prompt,
            )

            data = extract_json(
                raw
            )

            st.session_state.seo = data

            st.success(
                "SEO berhasil dibuat."
            )

        except Exception as e:

            st.error(
                f"Gagal membuat SEO: {e}"
            )


# ============================================================
# SEO PAGE
# ============================================================

def render_seo():

    st.title(
        "🔎 YouTube SEO"
    )

    if not selected_concept():

        st.info(
            "Pilih konsep terlebih dahulu."
        )

        if st.button(
            "← Ke Concepts",
            use_container_width=True,
        ):
            go("concepts")

        return

    concept = selected_concept()

    st.write(
        f"**Concept:** "
        f"{safe_text(concept.get('title'))}"
    )

    if st.button(
        "🚀 GENERATE SEO",
        type="primary",
        use_container_width=True,
    ):

        generate_seo()

    seo = st.session_state.seo

    if not seo:
        return

    st.divider()

    st.subheader(
        "📌 Title"
    )

    st.text_area(
        "YouTube Title",
        value=safe_text(
            seo.get("title")
        ),
        height=80,
        key="seo_title_display",
    )

    st.subheader(
        "📝 Description"
    )

    st.text_area(
        "YouTube Description",
        value=safe_text(
            seo.get("description")
        ),
        height=220,
        key="seo_description_display",
    )

    st.subheader(
        "🔑 Keywords"
    )

    keywords = seo.get(
        "keywords",
        [],
    )

    st.text_area(
        "Keywords",
        value=", ".join(
            str(x) for x in keywords
        ),
        height=100,
        key="seo_keywords_display",
    )

    st.subheader(
        "#️⃣ Hashtags"
    )

    hashtags = seo.get(
        "hashtags",
        [],
    )

    st.text_area(
        "Hashtags",
        value=" ".join(
            str(x) for x in hashtags
        ),
        height=80,
        key="seo_hashtags_display",
    )


# ============================================================
# PAGE ROUTER
# ============================================================

page = st.session_state.page

if page == "home":

    render_home()

elif page == "concepts":

    render_concepts()

elif page == "storyboard":

    render_storyboard()

elif page == "scenes":

    render_scenes()

elif page == "seo":

    render_seo()

else:

    st.session_state.page = "home"

    render_home()


# ============================================================
# END PART 3
