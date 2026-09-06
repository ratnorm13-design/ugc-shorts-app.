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

Analisis reference yang diberikan dan buat tepat 3 konsep remix ORIGINAL.

WAJIB: seluruh nilai output analysis dan seluruh isi 3 konsep harus Bahasa Indonesia. Hanya nama field JSON yang boleh tetap menggunakan key Bahasa Inggris.

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

Kembalikan HANYA JSON valid. Semua nilai teks wajib Bahasa Indonesia:
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
Buat storyboard produksi untuk konsep video ORIGINAL ini.

WAJIB: seluruh isi storyboard harus dalam Bahasa Indonesia. Jangan gunakan Bahasa Inggris pada isi field storyboard.

Video final memiliki TEPAT {n} scene, sekitar 8 detik per scene.
Duration: {st.session_state.duration}
Aspect ratio: {st.session_state.aspect_ratio}
Visual style: {st.session_state.visual_style}

Concept:
{concept_text(concept)}

Creative instruction:
{st.session_state.custom_instruction}

ATURAN WAJIB:
- Jumlah scene HARUS tepat {n}. Jangan kurang dan jangan lebih.
- Nomor scene HARUS 1 sampai {n}.
- Setiap scene sekitar 8 detik.
- Semua field dan seluruh nilainya WAJIB Bahasa Indonesia.
- Scene 1 harus memiliki hook terkuat.
- Pertahankan hubungan sebab-akibat, urutan kejadian, dan progres cerita.
- Setiap scene harus bisa diproduksi secara visual.
- Subjek utama dan elemen berulang harus konsisten.
- Jelaskan kondisi akhir scene agar menjadi dasar scene berikutnya.
- Jangan menyalin karakter, shot, dialog, lokasi, atau desain khas reference secara identik.
- Scene terakhir harus memberikan payoff yang jelas.
- Jika durasi 16 detik, hasil WAJIB 2 scene: Scene 1 dan Scene 2.
- Jangan pernah membuat jumlah scene berdasarkan perkiraan sendiri; gunakan angka {n} yang diberikan aplikasi.

Kembalikan HANYA JSON valid. Nilai semua field harus Bahasa Indonesia:
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
    st.write(f"**Durasi:** {st.session_state.duration}  •  **Jumlah Scene:** {n}")

    if not st.session_state.storyboard:
        if st.button("🧩 GENERATE STORYBOARD", type="primary", use_container_width=True):
            run_storyboard()
        return

    for scene in st.session_state.storyboard:
        with st.expander(
            f"Scene {scene['scene']} • {scene.get('time', '')} • {scene.get('purpose', '')}"
        ):
            st.write("**Visual:**", scene.get("visual", ""))
            st.write("**Action:**", scene.get("action", ""))
            st.write("**Camera:**", scene.get("camera", ""))
            st.write("**Continuity:**", scene.get("continuity", ""))
            st.write("**Audio:**", scene.get("audio", ""))
            st.write("**Transition:**", scene.get("transition", ""))

    if st.button("🎥 LANJUT KE PROMPT SCENE", type="primary", use_container_width=True):
        go("scenes")


# ============================================================
# SCENE PROMPTS
# ============================================================

def previous_scene_info(index):
    if index <= 1:
        return "This is Scene 1. No previous scene."
    prev = st.session_state.storyboard[index - 2]
    return json.dumps(prev, ensure_ascii=False, indent=2)


def generate_scene_prompt(scene_number):
    client = get_client()
    if not client:
        return

    scenes = st.session_state.storyboard
    scene = scenes[scene_number - 1]
    concept = selected_concept()

    previous_frame = st.session_state.scene_frames.get(scene_number - 1)

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
prop placement, 
