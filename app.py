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

REFERENCE_OPTIONS = ["Video", "Screenshots", "Text / idea"]


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
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass

    starts = [text.find("{"), text.find("[")]
    starts = [x for x in starts if x >= 0]
    if not starts:
        raise ValueError("Respons AI tidak berisi JSON yang valid.")

    start = min(starts)
    for end in range(len(text), start, -1):
        candidate = text[start:end].strip()
        try:
            return json.loads(candidate)
        except Exception:
            continue

    raise ValueError("Tidak bisa membaca JSON dari respons AI.")


def text_response(client, prompt, parts=None):
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


def upload_to_gemini(client, uploaded_file):
    if uploaded_file is None:
        return None
    try:
        return client.files.upload(
            file=uploaded_file,
            config={"display_name": uploaded_file.name},
        )
    except Exception as e:
        st.warning(f"File tidak bisa dikirim ke Gemini: {e}")
        return None


def file_part(client, uploaded_file):
    remote = upload_to_gemini(client, uploaded_file)
    return [remote] if remote else []


def scene_count():
    return DURATION_SCENES[st.session_state.duration]


def selected_concept():
    return st.session_state.selected_concept or {}


def concept_text(concept):
    return json.dumps(concept, ensure_ascii=False, indent=2)


def safe_text(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(x) for x in value)
    return str(value)


def go(page):
    st.session_state.page = page
    st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("🎬 UGC Remix Studio")
    st.caption("Reference → Remix → Storyboard → Flow/Veo Prompts")

    st.text_input(
        "Gemini API Key",
        type="password",
        key="api_key",
        placeholder="AIza...",
    )

    st.divider()

    if st.button("🏠 Home", use_container_width=True):
        go("home")
    if st.button("💡 Concepts", use_container_width=True):
        go("concepts")
    if st.button("🧩 Storyboard", use_container_width=True):
        go("storyboard")
    if st.button("🎥 Scene Prompts", use_container_width=True):
        go("scenes")
    if st.button("🔎 YouTube SEO", use_container_width=True):
        go("seo")

    st.divider()

    if st.button("🆕 New Project", use_container_width=True):
        reset_project()
        st.rerun()


# ============================================================
# HOME
# ============================================================

def render_home():
    st.title("🎬 Turn Any Reference Into an Original Video Blueprint")
    st.write(
        "Upload a reference video, screenshots, or an idea. "
        "AI analyzes the entertainment logic, creates 3 original remix concepts, "
        "then builds a scene-by-scene workflow for Google Flow/Veo."
    )

    st.subheader("1. Reference")

    ref_type = st.radio(
        "Pilih sumber reference",
        REFERENCE_OPTIONS,
        horizontal=True,
        key="reference_type",
    )

    if ref_type == "Video":
        st.session_state.reference_file = st.file_uploader(
            "Upload reference video",
            type=["mp4", "mov", "webm", "avi", "mkv"],
            help="Maksimum mengikuti batas upload Streamlit/hosting.",
        )
        st.session_state.reference_files = []

    elif ref_type == "Screenshots":
        st.session_state.reference_files = st.file_uploader(
            "Upload screenshots",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
        )
        st.session_state.reference_file = None

    else:
        st.session_state.reference_text = st.text_area(
            "Jelaskan reference / ide",
            value=st.session_state.reference_text,
            height=180,
            placeholder="Contoh: video komedi tentang seseorang mencoba sesuatu lalu terjadi kejutan lucu...",
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
            placeholder="Contoh: lebih lucu, lebih cepat, family-friendly, ending lebih kuat...",
        )

    count = scene_count()
    st.info(
        f"Durasi {st.session_state.duration} = {count} scene. "
        "Setiap scene dirancang sekitar 8 detik."
    )

    st.subheader("3. Originality Guard")
    st.checkbox(
        "Aktifkan originality + transformation guard",
        value=True,
        key="originality_guard",
    )

    st.write(
        "AI akan mempertahankan hook, cause/effect, emotional goal, payoff, "
        "dan pacing logic, tetapi mengubah execution: karakter/subjek, "
        "penampilan, pakaian, warna, properti, setting, aksi, kamera, lighting, "
        "visual design, dialog, dan sound design."
    )

    if st.button("🚀 ANALYZE + AUTO REMIX", type="primary", use_container_width=True):
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
You are the creative director of an original-content video production system.

Analyze the supplied reference and create exactly 3 ORIGINAL remix concepts.

IMPORTANT:
- The reference only supplies high-level entertainment logic.
- Preserve useful structure such as hook, cause/effect, emotional goal,
  escalation, payoff, and pacing logic.
- Do NOT copy recognizable characters, brands, exact dialogue, distinctive
  costumes, exact shots, exact locations, logos, watermarks, or a creator/studio's
  distinctive style.
- Substantially transform the execution.
- Make each concept independently usable for any duration from 8 seconds to 3 minutes.
- Keep the result suitable for mainstream YouTube unless the user explicitly asks otherwise.
- The app will later turn the chosen concept into 1–23 scenes and Flow/Veo prompts.

Settings:
Reference type: {ref_type}
Visual style: {st.session_state.visual_style}
Aspect ratio: {st.session_state.aspect_ratio}
Duration: {st.session_state.duration}
Scene count: {scene_count()}
Creative instruction: {st.session_state.custom_instruction}

Return ONLY valid JSON:
{{
  "analysis": {{
    "source_summary": "...",
    "niche": "...",
    "hook": "...",
    "cause_effect": "...",
    "emotional_goal": "...",
    "pacing_logic": "...",
    "payoff": "...",
    "key_visual_mechanics": ["...", "..."],
    "transformation_notes": ["...", "..."]
  }},
  "concepts": [
    {{
      "title": "...",
      "one_line_pitch": "...",
      "niche": "...",
      "hook": "...",
      "story_arc": "...",
      "main_subjects": ["..."],
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
      "hook": "...",
      "story_arc": "...",
      "main_subjects": ["..."],
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
      "hook": "...",
      "story_arc": "...",
      "main_subjects": ["..."],
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

    if ref_type == "Video" and st.session_state.reference_file:
        parts = file_part(client, st.session_state.reference_file)
    elif ref_type == "Screenshots":
        for f in st.session_state.reference_files:
            parts.extend(file_part(client, f))
    elif ref_type == "Text / idea":
        parts.append(
            f"\nUSER REFERENCE TEXT:\n{st.session_state.reference_text}"
        )

    if ref_type == "Video" and not parts:
        st.warning("Upload reference video dulu.")
        return
    if ref_type == "Screenshots" and not parts:
        st.warning("Upload minimal satu screenshot dulu.")
        return
    if ref_type == "Text / idea" and not st.session_state.reference_text.strip():
        st.warning("Masukkan reference / ide dulu.")
        return

    with st.spinner("AI sedang menganalisis reference dan membuat 3 remix..."):
        try:
            data = extract_json(text_response(client, prompt, parts))
            concepts = data.get("concepts", [])
            if len(concepts) != 3:
                raise ValueError("AI tidak mengembalikan tepat 3 konsep.")

            st.session_state.analysis = data.get("analysis", {})
            st.session_state.concepts = concepts
            st.session_state.selected_concept = None
            st.session_state.selected_concept_index = None
            st.session_state.storyboard = []
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}
            st.session_state.current_scene = 1
            go("concepts")
        except Exception as e:
            st.error(f"Gagal membuat remix: {e}")


def render_concepts():
    st.title("💡 AI Analysis + Auto Remix")

    if not st.session_state.concepts:
        st.info("Belum ada konsep. Mulai dari Home.")
        return

    analysis = st.session_state.analysis

    with st.expander("🧠 Reference Analysis", expanded=True):
        st.write("**Niche:**", safe_text(analysis.get("niche")))
        st.write("**Hook:**", safe_text(analysis.get("hook")))
        st.write("**Cause / Effect:**", safe_text(analysis.get("cause_effect")))
        st.write("**Emotional Goal:**", safe_text(analysis.get("emotional_goal")))
        st.write("**Pacing:**", safe_text(analysis.get("pacing_logic")))
        st.write("**Payoff:**", safe_text(analysis.get("payoff")))

    st.subheader("Choose 1 of 3 Original Concepts")

    cols = st.columns(3)

    for i, concept in enumerate(st.session_state.concepts):
        with cols[i]:
            st.markdown(f"### {i + 1}. {concept.get('title', 'Untitled')}")
            st.write(concept.get("one_line_pitch", ""))
            st.write("**Niche:**", concept.get("niche", ""))
            st.write("**Hook:**", concept.get("hook", ""))
            st.write("**Setting:**", concept.get("setting", ""))
            st.write("**Payoff:**", concept.get("ending_payoff", ""))

            if st.button(
                f"USE CONCEPT {i + 1}",
                key=f"use_concept_{i}",
                use_container_width=True,
                type="primary" if i == 0 else "secondary",
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
Create a production storyboard for this ORIGINAL video concept.

The final video has exactly {n} scenes, about 8 seconds per scene.
Duration: {st.session_state.duration}
Aspect ratio: {st.session_state.aspect_ratio}
Visual style: {st.session_state.visual_style}

Concept:
{concept_text(concept)}

Creative instruction:
{st.session_state.custom_instruction}

Requirements:
- Exactly {n} scenes. Number them 1 through {n}.
- Every scene must have a clear purpose.
- Scene 1 must contain the strongest hook.
- Maintain logical cause/effect and escalating progression.
- Every scene must be visually producible.
- Keep recurring subjects visually consistent.
- Define continuity details that the next scene can inherit.
- Do not copy the original reference's exact characters, shots, dialogue,
  location, or distinctive design.
- Make the final scene deliver a clear payoff.

Return ONLY valid JSON:
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

    with st.spinner(f"Building {n}-scene storyboard..."):
        try:
            data = extract_json(text_response(client, prompt))
            scenes = data.get("scenes", [])
            if len(scenes) != n:
                raise ValueError(
                    f"Storyboard harus {n} scene, AI menghasilkan {len(scenes)}."
                )
            for idx, scene in enumerate(scenes, start=1):
                scene["scene"] = idx
                scene.setdefault("time", f"{(idx-1)*8:02d}-{idx*8:02d}")
            st.session_state.storyboard = scenes
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}
            st.session_state.current_scene = 1
            go("storyboard")
        except Exception as e:
            st.error(f"Gagal membuat storyboard: {e}")


def render_storyboard():
    st.title("🧩 Storyboard")

    concept = selected_concept()
    if not concept:
        st.info("Pilih konsep dulu.")
        return

    st.success(
        f"Concept {st.session_state.selected_concept_index + 1}: "
        f"{concept.get('title', '')}"
    )

    n = scene_count()
    st.write(f"**Duration:** {st.session_state.duration}  •  **Scenes:** {n}")

    if not st.session_state.storyboard:
        if st.button(
            "🧩 GENERATE STORYBOARD",
            type="primary",
            use_container_width=True
        ):
            run_storyboard()
        return

    for scene in st.session_state.storyboard:
        with st.expander(
            f"Scene {scene['scene']} • {scene.get('time', '')} • "
            f"{scene.get('purpose', '')}"
        ):
            st.write("**Visual:**", scene.get("visual", ""))
            st.write("**Action:**", scene.get("action", ""))
            st.write("**Camera:**", scene.get("camera", ""))
            st.write("**Continuity:**", scene.get("continuity", ""))
            st.write("**Audio:**", scene.get("audio", ""))
            st.write("**Transition:**", scene.get("transition", ""))

    if st.button(
        "🎥 CONTINUE TO SCENE PROMPTS",
        type="primary",
        use_container_width=True
    ):
        go("scenes")


# ============================================================
# SCENE PROMPTS
# ============================================================

def previous_scene_info(index):
    if index <= 1:
        return "This is Scene 1. No previous scene."

    prev = st.session_state.storyboard[index - 2]

    return json.dumps(
        prev,
        ensure_ascii=False,
        indent=2
    )


def generate_scene_prompt(scene_number):
    client = get_client()

    if not client:
        return

    scenes = st.session_state.storyboard
    scene = scenes[scene_number - 1]
    concept = selected_concept()

    previous_frame = st.session_state.scene_frames.get(
        scene_number - 1
    )

    prompt = f"""
You are writing one production-ready Google Flow / Veo video prompt.

Create the prompt for Scene {scene_number} of {len(scenes)}.

Project:
Concept: {concept.get('title', '')}
Visual style: {st.session_state.visual_style}
Aspect ratio: {st.session_state.aspect_ratio}
Total duration: {st.session_state.duration}

Current storyboard scene:
{json.dumps(scene, ensure_ascii=False, indent=2)}

Previous scene:
{previous_scene_info(scene_number)}

Previous scene last-frame image is supplied when available.
Use it ONLY to preserve visual continuity: subject identity, wardrobe,
prop placement, environment, lighting direction, camera geography, and
motion state. Do not copy unrelated details from any reference.

Originality rules:
- Do not reproduce copyrighted characters, brands, logos, exact dialogue,
  exact shots, distinctive costumes, or recognizable creator/studio style.
- Preserve story logic while using original execution.
- Keep recurring characters/subjects consistent across scenes.
- Do not introduce random new characters or props without narrative reason.

Write ONE detailed paragraph only. No JSON. No headings. No bullet points.

Include:
subject appearance, environment, exact action, facial/body performance,
camera framing and movement, lens/depth of field, lighting, color mood,
physics/motion, sound effects/ambience, dialogue only if needed,
and a clean transition-ready ending.

The prompt must be directly usable in Google Flow/Veo.
"""

    parts = []

    if previous_frame:
        parts.extend(
            file_part(
                client,
                previous_frame
            )
        )

    with st.spinner(
        f"Generating Flow/Veo prompt for Scene {scene_number}..."
    ):
        try:
            result = text_response(
                client,
                prompt,
                parts
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
    st.title("🎥 Scene-by-Scene Flow/Veo Prompts")

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
            n
        )
    )

    st.session_state.current_scene = current

    st.progress(
        current / n
    )

    st.write(
        f"**Scene {current} / {n}**"
    )

    scene = scenes[current - 1]

    st.subheader(
        f"Scene {current} • {scene.get('time', '')}"
    )

    st.write(
        "**Purpose:**",
        scene.get("purpose", "")
    )

    st.write(
        "**Visual:**",
        scene.get("visual", "")
    )

    st.write(
        "**Action:**",
        scene.get("action", "")
    )

    st.write(
        "**Camera:**",
        scene.get("camera", "")
    )

    st.write(
        "**Continuity:**",
        scene.get("continuity", "")
    )

    st.write(
        "**Audio:**",
        scene.get("audio", "")
    )

    if current > 1:

        st.subheader(
            "🖼️ Continuity Frame"
        )

        st.caption(
            "Setelah membuat video Scene sebelumnya di Flow/Veo, "
            "upload screenshot frame terakhirnya di sini."
        )

        frame = st.file_uploader(
            f"Upload last frame Scene {current - 1}",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp"
            ],
            key=f"frame_upload_{current}",
        )

        if frame:

            st.session_state.scene_frames[
                current - 1
            ] = frame

            st.success(
                f"Last frame Scene {current - 1} tersimpan."
            )

    st.divider()

    if current not in st.session_state.scene_prompts:

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
            "📋 Flow / Veo Prompt"
        )

        st.text_area(
            "Prompt — copy this into Google Flow/Veo",
            value=st.session_state.scene_prompts[
                current
            ],
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
                    use_container_width=True
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
                    use_container_width=True
                ):

                    st.session_state.current_scene = (
                        current + 1
                    )

                    st.rerun()

            else:

                if st.button(
                    "🔎 FINISH → SEO",
                    type="primary",
                    use_container_width=True
                ):

                    go("seo")

    st.divider()

    choices = list(
        range(
            1,
            n + 1
        )
    )

    selected = st.selectbox(
        "Jump to scene",
        choices,
        index=current - 1,
        key="scene_jump",
    )

    if selected != current:

        st.session_state.current_scene = selected

        st.rerun()


# ============================================================
# SEO
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
Create a YouTube SEO package for this ORIGINAL video.

Concept:
{concept_text(concept)}

Duration: {st.session_state.duration}
Aspect ratio: {st.session_state.aspect_ratio}
Scenes: {n}
Completed Flow/Veo prompts: {prompts_done}/{n}

Return ONLY valid JSON:
{{
  "titles": ["...", "...", "..."],
  "description": "...",
  "keywords": ["...", "..."],
  "hashtags": ["...", "..."],
  "thumbnail_text": "...",
  "thumbnail_concept": "...",
  "pinned_comment": "...",
  "cta": "..."
}}

Rules:
- Titles should be clickable but honest.
- Description should describe the actual original concept.
- Keywords should be relevant and natural.
- Do not mention or imply that the video is a copy of a reference.
- Avoid copyrighted character/brand names unless they are genuinely part
  of the user's own original concept.
"""

    with st.spinner(
        "Generating YouTube SEO package..."
    ):

        try:

            st.session_state.seo = extract_json(
                text_response(
                    client,
                    prompt
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
            "SEO tetap bisa dibuat, tetapi lebih baik selesaikan semua scene."
        )

    if not st.session_state.seo:

        if st.button(
            "🚀 GENERATE SEO PACKAGE",
            type="primary",
            use_container_width=True
        ):

            run_seo()

            st.rerun()

        return

    seo = st.session_state.seo

    titles = seo.get(
        "titles",
        []
    )

    st.subheader(
        "🎯 Titles"
    )

    for i, title in enumerate(titles):

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
            seo.get("description")
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
                    []
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
                    []
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
            seo.get("thumbnail_text")
        ),
        key="thumbnail_text",
    )

    st.text_area(
        "Thumbnail Concept",
        value=safe_text(
            seo.get("thumbnail_concept")
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
            seo.get("pinned_comment")
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
            seo.get("cta")
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
            use_container_width=True
        ):

            go("scenes")

    with c2:

        if st.button(
            "🆕 NEW PROJECT",
            type="primary",
            use_container_width=True
        ):

            reset_project()

            st.rerun()


# ============================================================
# UPLOAD MIME TYPE FIX
# ============================================================

def upload_to_gemini(client, uploaded_file):

    if uploaded_file is None:
        return None

    try:

        mime_type = getattr(
            uploaded_file,
            "type",
            None
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

            elif (
                name.endswith(".jpg")
                or name.endswith(".jpeg")
            ):
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
