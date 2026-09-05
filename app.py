import json
import re
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
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


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

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=0.8,
        ),
    )

    return response.text or ""


# ============================================================
# GEMINI FILE UPLOAD
# ============================================================

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

        if not mime_type:
            name = uploaded_file.name.lower()

            if name.endswith(".mp4"):
                mime_type = "video/mp4"

            elif name.endswith(".mov"):
                mime_type = "video/quicktime"

            elif name.endswith(".webm"):
                mime_type = "video/webm"

            elif name.endswith(".avi"):
                mime_type = "video/x-msvideo"

            elif name.endswith(".mkv"):
                mime_type = "video/x-matroska"

            elif name.endswith(".png"):
                mime_type = "image/png"

            elif name.endswith(".jpg"):
                mime_type = "image/jpeg"

            elif name.endswith(".jpeg"):
                mime_type = "image/jpeg"

            elif name.endswith(".webp"):
                mime_type = "image/webp"

        return client.files.upload(
            file=uploaded_file,
            config={
                "display_name": uploaded_file.name,
                "mime_type": mime_type,
            },
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

    return [remote] if remote else []


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
            str(x)
            for x in value
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
        "Reference → Remix → Storyboard → "
        "Flow/Veo Prompts"
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
        "🎬 Turn Any Reference Into "
        "an Original Video Blueprint"
    )

    st.write(
        "Upload video referensi, screenshot, "
        "atau ide. AI akan menganalisis struktur "
        "hiburan, membuat 3 konsep remix original, "
        "lalu membuat storyboard untuk Flow/Veo."
    )

    st.subheader("1. Reference")

    ref_type = st.radio(
        "Pilih sumber reference",
        REFERENCE_OPTIONS,
        horizontal=True,
        key="reference_type",
    )

    if ref_type == "Video":

        st.session_state.reference_file = (
            st.file_uploader(
                "Upload reference video",
                type=[
                    "mp4",
                    "mov",
                    "webm",
                    "avi",
                    "mkv",
                ],
                help=(
                    "Maksimum mengikuti batas "
                    "upload Streamlit/hosting."
                ),
            )
        )

        st.session_state.reference_files = []

    elif ref_type == "Screenshots":

        st.session_state.reference_files = (
            st.file_uploader(
                "Upload screenshots",
                type=[
                    "png",
                    "jpg",
                    "jpeg",
                    "webp",
                ],
                accept_multiple_files=True,
            )
        )

        st.session_state.reference_file = None

    else:

        st.session_state.reference_text = (
            st.text_area(
                "Jelaskan reference / ide",
                value=(
                    st.session_state
                    .reference_text
                ),
                height=180,
                placeholder=(
                    "Contoh: video komedi "
                    "tentang kucing yang mencoba "
                    "melakukan sesuatu lalu terjadi "
                    "kejutan lucu..."
                ),
            )
        )

        st.session_state.reference_file = None
        st.session_state.reference_files = []

    st.subheader("2. Creative Settings")

    c1, c2 = st.columns(2)

    with c1:

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

    with c2:

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
                "Contoh: lebih lucu, "
                "lebih cepat, family-friendly, "
                "ending lebih kuat..."
            ),
        )

    count = scene_count()

    st.info(
        f"Durasi {st.session_state.duration} "
        f"= {count} scene. "
        "Setiap scene sekitar 8 detik."
    )

    st.subheader("3. Originality Guard")

    st.checkbox(
        "Aktifkan originality + transformation guard",
        value=True,
        key="originality_guard",
    )

    st.write(
        "AI mempertahankan struktur hiburan "
        "seperti hook, cause/effect, emotional "
        "goal, escalation, payoff, dan pacing."
    )

    st.write(
        "Subjek utama dari reference tetap "
        "dipertahankan jika masih relevan. "
        "AI tidak boleh mengganti kucing menjadi "
        "robot hanya demi membuatnya berbeda."
    )

    st.write(
        "Yang ditransformasi terutama execution: "
        "setting, properti, aksi, kamera, "
        "lighting, visual design, dialog, "
        "sound design, dan detail cerita."
    )

    if st.button(
        "🚀 ANALYZE + AUTO REMIX",
        type="primary",
        use_container_width=True,
    ):
        run_analysis()


# ============================================================
# ANALYSIS + REMIX
# ============================================================

def run_analysis():

    client = get_client()

    if not client:
        return

    ref_type = st.session_state.reference_type

    prompt = f"""
You are the creative director of an
original-content video production system.

Analyze the supplied reference and create
exactly 3 ORIGINAL remix concepts.

IMPORTANT LANGUAGE RULE:
- Write ALL analysis, concepts, explanations,
  story ideas, and metadata in BAHASA INDONESIA.
- English is NOT allowed in the analysis,
  concept descriptions, or story ideas.
- English will only be used later when generating
  the final Google Flow / Veo production prompt.

IMPORTANT REFERENCE RULE:
- Identify the main subject/character from the
  reference.
- Preserve the same MAIN SUBJECT when possible.
- If the reference clearly contains a cat,
  keep a cat as the main subject.
- Do NOT randomly replace the main subject
  with a robot, human, alien, or another animal.
- The goal is to remix the STORY and EXECUTION,
  not randomly replace the central subject.

REFERENCE TRANSFORMATION:
- Preserve high-level entertainment logic:
  hook, cause/effect, emotional goal,
  escalation, payoff, and pacing.
- Do NOT copy recognizable characters,
  brands, logos, watermarks, exact dialogue,
  distinctive costumes, exact shots, or
  distinctive creator/studio identity.
- Change execution substantially while keeping
  the main subject consistent.
- Change setting, props, action details,
  camera language, lighting, visual design,
  dialogue wording, and sound design.
- Each concept must be independently usable
  from 8 seconds up to 3 minutes.

SAFETY:
- Do not create instructions for dangerous
  electrical activity.
- If the reference involves electricity,
  plugs, sockets, wires, fire, or similar hazards,
  convert the dangerous object/action into a
  clearly fake, unplugged, toy, prop, or harmless
  fictional version.
- The story should remain funny and entertaining
  without showing a real dangerous interaction.

SETTINGS:

Reference type:
{ref_type}

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

Return ONLY valid JSON.

The JSON content itself must be in
BAHASA INDONESIA.

FORMAT:

{{
  "analysis": {{
    "source_summary": "...",
    "main_subject": "...",
    "niche": "...",
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
      "main_subjects": [
        "..."
      ],
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
      "main_subjects": [
        "..."
      ],
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
      "main_subjects": [
        "..."
      ],
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

    if (
        ref_type == "Video"
        and st.session_state.reference_file
    ):
        parts = file_part(
            client,
            st.session_state.reference_file,
        )

    elif ref_type == "Screenshots":

        for f in st.session_state.reference_files:
            parts.extend(
                file_part(
                    client,
                    f,
                )
            )

    elif ref_type == "Text / idea":

        parts.append(
            "\nUSER REFERENCE TEXT:\n"
            + st.session_state.reference_text
        )

    if (
        ref_type == "Video"
        and not parts
    ):
        st.warning(
            "Upload reference video dulu."
        )
        return

    if (
        ref_type == "Screenshots"
        and not parts
    ):
        st.warning(
            "Upload minimal satu screenshot dulu."
        )
        return

    if (
        ref_type == "Text / idea"
        and not st.session_state.reference_text.strip()
    ):
        st.warning(
            "Masukkan reference / ide dulu."
        )
        return

    with st.spinner(
        "AI sedang menganalisis reference "
        "dan membuat 3 remix..."
    ):

        try:

            data = extract_json(
                text_response(
                    client,
                    prompt,
                    parts,
                )
            )

            concepts = data.get(
                "concepts",
                [],
            )

            if len(concepts) != 3:
                raise ValueError(
                    "AI tidak mengembalikan "
                    "tepat 3 konsep."
                )

            st.session_state.analysis = (
                data.get(
                    "analysis",
                    {},
                )
            )

            st.session_state.concepts = concepts

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
# CONCEPTS
# ============================================================

def render_concepts():

    st.title(
        "💡 AI Analysis + Auto Remix"
    )

    if not st.session_state.concepts:

        st.info(
            "Belum ada konsep. "
            "Mulai dari Home."
        )

        return

    analysis = st.session_state.analysis

    with st.expander(
        "🧠 Reference Analysis",
        expanded=True,
    ):

        st.write(
            "**Subjek utama:**",
            safe_text(
                analysis.get(
                    "main_subject"
                )
            ),
        )

        st.write(
            "**Niche:**",
            safe_text(
                analysis.get("niche")
            ),
        )

        st.write(
            "**Hook:**",
            safe_text(
                analysis.get("hook")
            ),
        )

        st.write(
            "**Cause / Effect:**",
            safe_text(
                analysis.get(
                    "cause_effect"
                )
            ),
        )

        st.write(
            "**Emotional Goal:**",
            safe_text(
                analysis.get(
                    "emotional_goal"
                )
            ),
        )

        st.write(
            "**Pacing:**",
            safe_text(
                analysis.get(
                    "pacing_logic"
                )
            ),
        )

        st.write(
            "**Payoff:**",
            safe_text(
                analysis.get("payoff")
            ),
        )

    st.subheader(
        "Pilih 1 dari 3 Konsep Original"
    )

    cols = st.columns(3)

    for i, concept in enumerate(
        st.session_state.concepts
    ):

        with cols[i]:

            st.markdown(
                f"### {i + 1}. "
                f"{concept.get('title', 'Untitled')}"
            )

            st.write(
                concept.get(
                    "one_line_pitch",
                    "",
                )
            )

            st.write(
                "**Subjek:**",
                safe_text(
                    concept.get(
                        "main_subjects"
                    )
                ),
            )

            st.write(
                "**Niche:**",
                concept.get(
                    "niche",
                    "",
                ),
            )

            st.write(
                "**Hook:**",
                concept.get(
                    "hook",
                    "",
                ),
            )

            "setting",
                    "",
                ),
            )

            st.write(
                "**Payoff:**",
                concept.get(
                    "ending_payoff",
                    "",
                ),
            )

            if st.button(
                f"USE CONCEPT {i + 1}",
                key=f"use_concept_{i}",
                use_container_width=True,
                type=(
                    "primary"
                    if i == 0
                    else "secondary"
                ),
            ):

                st.session_state.selected_concept = concept
                st.session_state.selected_concept_index = i
                st.session_state.storyboard = []
                st.session_state.scene_prompts = {}
                st.session_state.scene_frames = {}
                st.session_state.current_scene = 1

                go("storyboard")
                # ============================================================
# STORYBOARD
# ============================================================

def run_storyboard():

    client = get_client()

    if not client:
        return

    concept = selected_concept()
    n = scene_count()

    prompt = f"""
You are creating a production storyboard for an ORIGINAL
video concept.

LANGUAGE RULE:
- Write the entire storyboard in BAHASA INDONESIA.
- Do NOT write the storyboard in English.
- English is reserved ONLY for the final Google Flow/Veo
  generation prompt.

MAIN SUBJECT RULE:
- Keep the main subject from the selected concept consistent
  across every scene.
- If the concept uses a cat, keep the main subject as a cat.
- Do NOT randomly change the cat into a robot, human,
  another animal, or unrelated creature.
- Maintain consistent appearance, identity, behavior,
  and important props.

SAFETY RULE:
- Never instruct a person or animal to interact with live
  electricity or dangerous equipment.
- If the story contains electricity, plugs, sockets, wires,
  fire, or similar hazards, transform them into clearly fake,
  unplugged, toy, harmless, or fictional props.
- Keep the entertainment logic while removing the real hazard.

VIDEO SETTINGS:

Duration:
{st.session_state.duration}

Exactly {n} scenes.

Each scene is approximately 8 seconds.

Aspect ratio:
{st.session_state.aspect_ratio}

Visual style:
{st.session_state.visual_style}

Creative instruction:
{st.session_state.custom_instruction}

SELECTED CONCEPT:

{concept_text(concept)}

STORYBOARD REQUIREMENTS:

- Exactly {n} scenes.
- Number scenes from 1 to {n}.
- Scene 1 must have the strongest hook.
- Maintain clear cause and effect.
- Build escalation naturally.
- Every scene must have a clear purpose.
- Keep the main subject visually consistent.
- Keep important props and environment consistent.
- Each scene must be visually producible.
- Define continuity information for the next scene.
- The final scene must deliver a satisfying payoff.
- Do not copy exact shots, dialogue, locations,
  characters, brands, logos, or distinctive styles
  from the reference.

Return ONLY valid JSON.

The JSON content must be entirely in BAHASA INDONESIA.

FORMAT:

{{
  "scenes": [
    {{
      "scene": 1,
      "time": "00:00-00:08",
      "purpose": "...",
      "visual": "...",
      "action": "...",
      "camera": "...",
      "continuity": "...",
      "audio": "...",
      "transition": "..."
    }}
  ]
}}
"""

    with st.spinner(
        f"Membuat storyboard {n} scene..."
    ):

        try:

            data = extract_json(
                text_response(
                    client,
                    prompt,
                )
            )

            scenes = data.get(
                "scenes",
                [],
            )

            if len(scenes) != n:

                raise ValueError(
                    f"Storyboard harus {n} scene, "
                    f"AI menghasilkan {len(scenes)}."
                )

            for idx, scene in enumerate(
                scenes,
                start=1,
            ):

                scene["scene"] = idx

                scene.setdefault(
                    "time",
                    f"{(idx - 1) * 8:02d}-"
                    f"{idx * 8:02d}",
                )

            st.session_state.storyboard = scenes
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}
            st.session_state.current_scene = 1

            go("storyboard")

        except Exception as e:

            st.error(
                f"Gagal membuat storyboard: {e}"
            )


def render_storyboard():

    st.title("🧩 Storyboard")

    concept = selected_concept()

    if not concept:

        st.info(
            "Pilih konsep dulu."
        )

        return

    st.success(
        f"Concept "
        f"{st.session_state.selected_concept_index + 1}: "
        f"{concept.get('title', '')}"
    )

    n = scene_count()

    st.write(
        f"**Durasi:** {st.session_state.duration} "
        f"• **Jumlah scene:** {n}"
    )

    if not st.session_state.storyboard:

        if st.button(
            "🧩 GENERATE STORYBOARD",
            type="primary",
            use_container_width=True,
        ):

            run_storyboard()

        return

    for scene in st.session_state.storyboard:

        with st.expander(
            f"Scene {scene['scene']} "
            f"• {scene.get('time', '')} "
            f"• {scene.get('purpose', '')}"
        ):

            st.write(
                "**Visual:**",
                scene.get(
                    "visual",
                    "",
                ),
            )

            st.write(
                "**Action:**",
                scene.get(
                    "action",
                    "",
                ),
            )

            st.write(
                "**Camera:**",
                scene.get(
                    "camera",
                    "",
                ),
            )

            st.write(
                "**Continuity:**",
                scene.get(
                    "continuity",
                    "",
                ),
            )

            st.write(
                "**Audio:**",
                scene.get(
                    "audio",
                    "",
                ),
            )

            st.write(
                "**Transition:**",
                scene.get(
                    "transition",
                    "",
                ),
            )

    if st.button(
        "🎥 CONTINUE TO SCENE PROMPTS",
        type="primary",
        use_container_width=True,
    ):

        go("scenes")


# ============================================================
# SCENE PROMPTS
# ============================================================

def previous_scene_info(index):

    if index <= 1:

        return (
            "Scene 1. Tidak ada scene sebelumnya."
        )

    prev = st.session_state.storyboard[
        index - 2
    ]

    return json.dumps(
        prev,
        ensure_ascii=False,
        indent=2,
    )


def generate_scene_prompt(
    scene_number,
):

    client = get_client()

    if not client:
        return

    scenes = st.session_state.storyboard

    scene = scenes[
        scene_number - 1
    ]

    concept = selected_concept()

    previous_frame = (
        st.session_state.scene_frames.get(
            scene_number - 1
        )
    )

    prompt = f"""
You are writing ONE production-ready
Google Flow / Veo video-generation prompt.

IMPORTANT LANGUAGE RULE:
- Write ONLY the final generation prompt
  in ENGLISH.
- Do NOT output Indonesian.
- Do NOT output JSON.
- Do NOT output headings.
- Do NOT output bullet points.
- Write exactly ONE detailed paragraph.

Create the prompt for:

Scene {scene_number} of {len(scenes)}

PROJECT:

Concept:
{concept.get('title', '')}

Visual style:
{st.session_state.visual_style}

Aspect ratio:
{st.session_state.aspect_ratio}

Total duration:
{st.session_state.duration}

MAIN SUBJECT:

{safe_text(
    concept.get(
        "main_subjects",
        ""
    )
)}

The main subject must remain consistent
with the selected concept.

If the main subject is a cat,
it must remain a cat.

Never randomly transform the main subject
into a robot, human, alien, or another creature.

CURRENT STORYBOARD SCENE:

{json.dumps(
    scene,
    ensure_ascii=False,
    indent=2,
)}

PREVIOUS SCENE:

{previous_scene_info(scene_number)}

CONTINUITY:

If a previous scene last-frame image is supplied,
use it ONLY to preserve continuity.

Preserve:
- subject identity
- subject appearance
- wardrobe or accessories when applicable
- prop placement
- environment
- lighting direction
- camera geography
- motion state
- important visual details

Do not copy unrelated copyrighted or
distinctive elements from any reference.

ORIGINALITY:

- Preserve the story logic.
- Use original execution.
- Do not reproduce copyrighted characters.
- Do not reproduce brands or logos.
- Do not reproduce exact dialogue.
- Do not reproduce exact shots.
- Do not reproduce distinctive costumes.
- Do not reproduce a recognizable creator
  or studio style.
- Do not introduce random characters.
- Do not introduce random props.

SAFETY:

Do not show or instruct real dangerous
electrical interaction.

If the scene involves a plug, socket,
wire, electricity, or similar object,
make it clearly fake, unplugged,
toy-like, harmless, or fictional.

Do not show an animal or person performing
a dangerous electrical action.

PROMPT MUST INCLUDE:

- detailed subject appearance
- environment
- exact action
- facial/body performance
- camera framing
- camera movement
- lens feel
- depth of field
- lighting
- color mood
- realistic physics and motion
- sound effects
- ambience
- dialogue only if necessary
- clean transition-ready ending

The result must be directly usable
inside Google Flow/Veo.
"""

    parts = []

    if previous_frame:

        parts.extend(
            file_part(
                client,
                previous_frame,
            )
        )

    with st.spinner(
        f"Membuat prompt Flow/Veo "
        f"Scene {scene_number}..."
    ):

        try:

            result = text_response(
                client,
                prompt,
                parts,
            ).strip()

            if not result:

                raise ValueError(
                    "AI mengembalikan prompt kosong."
                )

            st.session_state.scene_prompts[
                scene_number
            ] = result

        except Exception as e:

            st.error(
                f"Gagal membuat prompt scene: {e}"
            )


def render_scenes():

    st.title(
        "🎥 Scene-by-Scene Flow/Veo Prompts"
    )

    scenes = st.session_state.storyboard

    if not scenes:

        st.info(
            "Storyboard belum dibuat."
        )

        return

    n = len(scenes)

    current = max(
        1,
        min(
            st.session_state.current_scene,
            n,
        ),
    )

    st.session_state.current_scene = current

    st.progress(
        current / n
    )

    st.write(
        f"**Scene {current} / {n}**"
    )

    # FIX PENTING:
    # current adalah nomor scene 1-based,
    # sedangkan list Python dimulai dari 0.
    scene = scenes[
        current - 1
    ]

    st.subheader(
        f"Scene {current} "
        f"• {scene.get('time', '')}"
    )

    st.write(
        "**Purpose:**",
        scene.get(
            "purpose",
            "",
        ),
    )

    st.write(
        "**Visual:**",
        scene.get(
            "visual",
            "",
        ),
    )

    st.write(
        "**Action:**",
        scene.get(
            "action",
            "",
        ),
    )

    st.write(
        "**Camera:**",
        scene.get(
            "camera",
            "",
        ),
    )

    st.write(
        "**Continuity:**",
        scene.get(
            "continuity",
            "",
        ),
    )

    st.write(
        "**Audio:**",
        scene.get(
            "audio",
            "",
        ),
    )

    # --------------------------------------------------------
    # LAST FRAME
    # --------------------------------------------------------

    if current > 1:

        st.subheader(
            "🖼️ Continuity Frame"
        )

        st.caption(
            "Setelah membuat video scene "
            "sebelumnya di Google Flow/Veo, "
            "ambil screenshot frame terakhirnya "
            "dan upload di sini."
        )

        frame = st.file_uploader(
            f"Upload last frame Scene {current - 1}",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
            ],
            key=f"frame_upload_{current}",
        )

        if frame:

            st.session_state.scene_frames[
                current - 1
            ] = frame

            st.success(
                f"Last frame Scene "
                f"{current - 1} tersimpan."
            )

    st.divider()

    # --------------------------------------------------------
    # GENERATE PROMPT
    # --------------------------------------------------------

    if (
        current
        not in st.session_state.scene_prompts
    ):

        if st.button(
            f"✨ GENERATE PROMPT SCENE {current}",
            type="primary",
            use_container_width=True,
        ):

            generate_scene_prompt(
                current
            )

            st.rerun()

    else:

        st.subheader(
            "📋 Google Flow / Veo Prompt"
        )

        st.text_area(
            "Prompt — copy ke Google Flow/Veo",
            value=(
                st.session_state
                .scene_prompts[current]
            ),
            height=360,
            key=f"prompt_view_{current}",
        )

        if st.button(
            "🔄 REGENERATE THIS PROMPT",
            use_container_width=True,
        ):

            del st.session_state.scene_prompts[
                current
            ]

            generate_scene_prompt(
                current
            )

            st.rerun()

        c1, c2 = st.columns(2)

        with c1:

            if current > 1:

                if st.button(
                    "⬅️ PREVIOUS SCENE",
                    use_container_width=True,
                ):

                    st.session_state.current_scene = (
                        current - 1
                    )

                    st.rerun()

        with c2:

            if current < n:

                if st.button(
                    "NEXT SCENE ➡️",
                    type="primary",
                    use_container_width=True,
                ):

                    st.session_state.current_scene = (
                        current + 1
                    )

                    st.rerun()

            else:

                if st.button(
                    "🔎 FINISH → SEO",
                    type="primary",
                    use_container_width=True,
                ):

                    go("seo")

    st.divider()

    # --------------------------------------------------------
    # JUMP TO SCENE
    # --------------------------------------------------------

    choices = list(
        range(
            1,
            n + 1,
        )
    )

    selected = st.selectbox(
        "Jump to scene",
        choices,
        index=current - 1,
        key="scene_jump",
    )

    if selected != current:

        st.session_state.current_scene = (
            selected
        )

        st.rerun()


# ============================================================
# YOUTUBE SEO
# ============================================================

def run_seo():

    client = get_client()

    if not client:
        return

    concept = selected_concept()

    prompts_done = len(
        st.session_state.scene_prompts
    )

    n = len(
        st.session_state.storyboard
    )

    prompt = f"""
Create a YouTube SEO package for this
ORIGINAL video.

LANGUAGE RULE:
- Write everything in BAHASA INDONESIA.

CONCEPT:

{concept_text(concept)}

Duration:
{st.session_state.duration}

Aspect ratio:
{st.session_state.aspect_ratio}

Scenes:
{n}

Completed Flow/Veo prompts:
{prompts_done}/{n}

Return ONLY valid JSON:

{{
  "titles": [
    "...",
    "...",
    "..."
  ],
  "description": "...",
  "keywords": [
    "...",
    "..."
  ],
  "hashtags": [
    "...",
    "..."
  ],
  "thumbnail_text": "...",
  "thumbnail_concept": "...",
  "pinned_comment": "...",
  "cta": "..."
}}

RULES:

- Titles should be clickable but honest.
- Description should describe the actual
  original concept.
- Keywords should be relevant.
- Hashtags should be relevant.
- Do not claim the video is copied.
- Do not mention the reference video.
- Avoid copyrighted character names.
- Avoid misleading claims.
"""

    with st.spinner(
        "Membuat paket YouTube SEO..."
    ):

        try:

            st.session_state.seo = (
                extract_json(
                    text_response(
                        client,
                        prompt,
                    )
                )
            )

        except Exception as e:

            st.error(
                f"Gagal membuat SEO: {e}"
            )


def render_seo():

    st.title(
        "🔎 YouTube SEO"
    )

    if not selected_concept():

        st.info(
            "Pilih konsep dulu."
        )

        return

    n = len(
        st.session_state.storyboard
    )

    done = len(
        st.session_state.scene_prompts
    )

    if n and done < n:

        st.warning(
            f"Baru {done}/{n} scene prompt selesai. "
            "SEO tetap bisa dibuat, tetapi lebih baik "
            "selesaikan semua scene."
        )

    if not st.session_state.seo:

        if st.button(
            "🚀 GENERATE SEO PACKAGE",
            type="primary",
            use_container_width=True,
        ):

            run_seo()

            st.rerun()

        return

    seo = st.session_state.seo

    titles = seo.get(
        "titles",
        [],
    )

    st.subheader(
        "🎯 Titles"
    )

    for i, title in enumerate(
        titles
    ):

        st.text_input(
            f"Title {i + 1}",
            value=str(title),
            key=f"seo_title_{i}",
        )

    st.subheader(
        "📝 Description"
    )

    st.text_area(
        "Description",
        value=safe_text(
            seo.get(
                "description"
            )
        ),
        height=220,
        key="seo_description",
    )

    c1, c2 = st.columns(2)

    with c1:

        st.subheader(
            "🔑 Keywords"
        )

        st.text_area(
            "Keywords",
            value=", ".join(
                str(x)
                for x in seo.get(
                    "keywords",
                    [],
                )
            ),
            height=120,
            key="seo_keywords",
        )

    with c2:

        st.subheader(
            "#️⃣ Hashtags"
        )

        st.text_area(
            "Hashtags",
            value=" ".join(
                str(x)
                for x in seo.get(
                    "hashtags",
                    [],
                )
            ),
            height=120,
            key="seo_hashtags",
        )

    st.subheader(
        "🖼️ Thumbnail"
    )

    st.text_input(
        "Thumbnail Text",
        value=safe_text(
            seo.get(
                "thumbnail_text"
            )
        ),
        key="thumbnail_text",
    )

    st.text_area(
        "Thumbnail Concept",
        value=safe_text(
            seo.get(
                "thumbnail_concept"
            )
        ),
        height=120,
        key="thumbnail_concept",
    )

    st.subheader(
        "💬 Pinned Comment"
    )

    st.text_area(
        "Pinned Comment",
        value=safe_text(
            seo.get(
                "pinned_comment"
            )
        ),
        height=120,
        key="pinned_comment",
    )

    st.subheader(
        "📣 CTA"
    )

    st.text_area(
        "Call To Action",
        value=safe_text(
            seo.get(
                "cta"
            )
        ),
        height=100,
        key="seo_cta",
    )

    st.success(
        "🎉 Project workflow selesai."
    )

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "🎥 BACK TO SCENES",
            use_container_width=True,
        ):

            go("scenes")

    with c2:

        if st.button(
            "🆕 NEW PROJECT",
            type="primary",
            use_container_width=True,
        ):

            reset_project()

            st.rerun()


# ============================================================
# ROUTER
# ============================================================

if st.session_state.page == "home":

    render_home()

elif st.session_state.page == "concepts":

    render_concepts()

elif st.session_state.page == "storyboard":

    render_storyboard()

elif st.session_state.page == "scenes":

    render_scenes()

elif st.session_state.page == "seo":

    render_seo()
