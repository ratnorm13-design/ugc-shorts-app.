import json
import re
import streamlit as st
from google import genai
from google.genai import types

# ============================================================
# KONFIGURASI HALAMAN & CSS STYLING
# ============================================================
st.set_page_config(
    page_title="UGC Remix Studio",
    page_icon="🎬",
    layout="wide"
)

MODEL_NAME = "gemini-3.6-flash"

DURATIONS = {
    "8 detik": 1,
    "16 detik": 2,
    "24 detik": 3,
    "32 detik": 4,
    "40 detik": 5,
    "48 detik": 6,
    "56 detik": 7,
    "1 menit": 8,
    "1.5 menit": 12,
    "2 menit": 15,
    "2.5 menit": 19,
    "3 menit": 23,
}

st.markdown("""
<style>
/* Tampilan Kontras Tinggi & Jelas */
.stApp { background-color: #0e1117; color: #ffffff; }
.block-container { max-width: 1400px; padding-top: 2rem; }

/* Banner Utama */
.hero { 
    padding: 28px; 
    border-radius: 12px; 
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
    border: 1px solid #38bdf8; 
    margin-bottom: 20px; 
}
.hero h1 { color: #ffffff !important; font-size: 32px; font-weight: 800; margin-bottom: 8px; }
.hero p { color: #f1f5f9 !important; font-size: 15px; line-height: 1.5; }

/* Kartu & Container */
.card, .metric-card, .concept-card, .selected-card { 
    background: #1e293b; 
    border: 1px solid #475569; 
    border-radius: 10px; 
    padding: 18px; 
    margin-bottom: 14px; 
    color: #ffffff; 
}
.card h3, .metric-card h3, .concept-card h2, .selected-card h2 { color: #38bdf8 !important; margin-top: 0; }

/* Label & Badge Kontras Tinggi */
.badge, .eyebrow, .metric-label, .concept-number { 
    display: inline-block; 
    padding: 4px 12px; 
    border-radius: 6px; 
    background: #0284c7; 
    color: #ffffff !important; 
    font-size: 12px; 
    font-weight: 700; 
    margin-bottom: 10px; 
}

/* Langkah Workflow */
.workflow { 
    min-height: 110px; 
    background: #1e293b; 
    border: 1px solid #38bdf8; 
    border-radius: 10px; 
    padding: 14px; 
}
.workflow-number { color: #38bdf8; font-weight: 800; font-size: 14px; }
.workflow-title { color: #ffffff !important; font-weight: 700; font-size: 15px; margin-top: 4px; }
.workflow-text { color: #e2e8f0 !important; font-size: 12px; margin-top: 4px; line-height: 1.4; }

/* Form Input & Teks Jelas */
div[data-baseweb="select"] > div { background-color: #0f172a !important; color: #ffffff !important; border: 1px solid #64748b !important; }
.stTextArea textarea, .stTextInput input { background-color: #0f172a !important; color: #ffffff !important; border: 1px solid #64748b !important; }
label { color: #ffffff !important; font-weight: 600 !important; font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# INISIALISASI SESSION STATE & HELPER
# ============================================================
def init_session_state():
    defaults = {
        "page": "home", "api_key": "", "analysis": None, "concepts": [],
        "selected_concept": None, "selected_concept_index": 0, "storyboard": None,
        "current_scene": 1, "scene_prompts": {}, "scene_screenshots": {},
        "seo_package": None, "content_type": "Umum", "visual_style": "Sinematik Realistis",
        "aspect_ratio": "9:16 — Shorts / Reels / TikTok", "duration": "8 detik",
        "scene_count": 1, "custom_instruction": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

def get_client(api_key):
    if not api_key: return None
    try: return genai.Client(api_key=api_key.strip())
    except Exception: return None

def clean_json(text):
    if not text: return None
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try: return json.loads(text)
    except Exception: pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try: return json.loads(match.group(0))
        except Exception: pass
    return None

def generate_ai(client, prompt, json_mode=False, temperature=0.7, max_output_tokens=8000):
    if client is None: raise ValueError("Kunci API Gemini belum dimasukkan.")
    config = types.GenerateContentConfig(temperature=temperature, max_output_tokens=max_output_tokens)
    if json_mode: config.response_mime_type = "application/json"
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt, config=config)
    if not response or not response.text: raise ValueError("Gemini tidak memberikan respon.")
    if json_mode:
        result = clean_json(response.text)
        if result is None: raise ValueError("Format JSON tidak valid.")
        return result
    return response.text

def reset_project():
    for k in ["analysis", "concepts", "selected_concept", "selected_concept_index", "storyboard", "current_scene", "scene_prompts", "scene_screenshots", "seo_package"]:
        if k == "concepts": st.session_state[k] = []
        elif k in ["scene_prompts", "scene_screenshots"]: st.session_state[k] = {}
        elif k == "current_scene": st.session_state[k] = 1
        elif k == "selected_concept_index": st.session_state[k] = 0
        else: st.session_state[k] = None
    st.session_state.page = "home"

# ============================================================
# NAVIGASI SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown('<div style="font-size:22px;font-weight:800;color:#38bdf8;">🎬 UGC Remix Studio</div>', unsafe_allow_html=True)
    st.divider()
    st.session_state.api_key = st.text_input("Kunci API Gemini (API Key)", value=st.session_state.api_key, type="password")
    st.divider()
    if st.button("🏠 Beranda", use_container_width=True): st.session_state.page = "home"; st.rerun()
    if st.button("🧠 AI Remix", use_container_width=True): st.session_state.page = "remix"; st.rerun()
    if st.button("🎞️ Papan Cerita (Storyboard)", use_container_width=True): st.session_state.page = "storyboard"; st.rerun()
    if st.button("🎬 Pembuat Adegan (Scene)", use_container_width=True): st.session_state.page = "scenes"; st.rerun()
    if st.button("🚀 Selesai & Paket SEO", use_container_width=True): st.session_state.page = "seo"; st.rerun()
    st.divider()
    if st.button("🗑️ Reset / Hapus Proyek", use_container_width=True): reset_project(); st.rerun()
        # ============================================================
# HALAMAN 1: BERANDA
# ============================================================
def render_home():
    st.markdown('<div class="hero"><div class="badge">V2 • MESIN KONTEN UNIVERSAL</div><h1>Ubah Referensi Apa Pun Menjadi Video Orisinal</h1><p>Unggah video referensi, tangkapan layar, atau tuliskan ide. AI akan menganalisis struktur hiburan, membuat konsep remix orisinal, menyusun papan cerita (storyboard), dan menyiapkan prompt per adegan untuk Google Flow / Veo.</p></div>', unsafe_allow_html=True)

    st.markdown("### ⚡ Alur Kerja")
    cols = st.columns(5)
    workflow = [
        ("01", "Referensi", "Video, gambar, atau teks."),
        ("02", "Analisis", "Pahami hook dan cerita."),
        ("03", "Auto Remix", "Buat 3 konsep orisinal."),
        ("04", "Storyboard", "Susun semua adegan."),
        ("05", "Prompt Flow", "Hasil prompt Flow/Veo.")
    ]
    for col, item in zip(cols, workflow):
        number, title, description = item
        with col:
            st.markdown(f'<div class="workflow"><div class="workflow-number">{number}</div><div class="workflow-title">{title}</div><div class="workflow-text">{description}</div></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown("### 🎥 Sumber Referensi")

    reference_type = st.radio("Pilih bentuk referensi", ["Video", "Tangkapan Layar (Gambar)", "Teks / Ide"], horizontal=True)
    video_file = None
    image_files = []
    reference_text = ""

    if reference_type == "Video":
        video_file = st.file_uploader("Unggah video referensi", type=["mp4", "mov", "webm", "avi", "mkv"])
    elif reference_type == "Tangkapan Layar (Gambar)":
        image_files = st.file_uploader("Unggah tangkapan layar", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
    else:
        reference_text = st.text_area("Jelaskan referensi atau ide kamu", height=140, placeholder="Contoh: Seorang karakter mencoba membuka kotak misterius di tengah hutan...")

    st.markdown("### 🎨 Pengaturan Kreatif")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.visual_style = st.selectbox("Gaya Visual", ["Sinematik Realistis", "Animasi 3D", "Kartun Lucu", "Komedi Fotorealistis", "Aksi Langsung Sinematik", "Gaya Anime Orisinal", "Sinematik Gelap", "Video Viral Cepat"])
    with col2:
        st.session_state.aspect_ratio = st.selectbox("Rasio Layar", ["9:16 — Shorts / Reels / TikTok", "16:9 — YouTube Long Form", "1:1 — Persegi / Square"])

    st.session_state.duration = st.selectbox("Durasi Video", list(DURATIONS.keys()))
    st.session_state.scene_count = DURATIONS[st.session_state.duration]
    st.info(f"⏱️ {st.session_state.duration} = {st.session_state.scene_count} adegan/scene (sekitar 8 detik per scene)")

    st.session_state.custom_instruction = st.text_area("Instruksi Kreatif Tambahan", height=100, placeholder="Contoh: Buat lebih lucu, tempo cepat, ending ada kejutan/twist...")

    st.write("")
    if st.button("🚀 ANALISIS + AUTO REMIX", type="primary", use_container_width=True):
        if not st.session_state.api_key:
            st.error("Masukkan Kunci API Gemini terlebih dahulu di menu samping (sidebar).")
            return

        client = get_client(st.session_state.api_key)
        if client is None:
            st.error("Kunci API Gemini tidak valid.")
            return

        reference_description = reference_text if reference_type == "Teks / Ide" else "Referensi media diunggah oleh pengguna"

        prompt = f"""
You are a universal AI video creative director. Analyze the reference and create three ORIGINAL remix concepts.
Visual style: {st.session_state.visual_style} | Aspect ratio: {st.session_state.aspect_ratio} | Duration: {st.session_state.duration} | Scenes: {st.session_state.scene_count}
User instruction: {st.session_state.custom_instruction} | Reference: {reference_description}

Return ONLY valid JSON:
{{
  "analysis": {{"content_type": "Format", "core_idea": "Core concept", "summary": "Breakdown", "hook": "Hook description", "emotional_goal": "Goal", "payoff": "Ending", "pacing": "Pacing"}},
  "concepts": [
    {{"title": "Concept 1", "concept": "Original concept details", "hook": "Hook", "setting": "Environment", "visual_direction": "Style notes", "why_it_works": "Reasoning"}},
    {{"title": "Concept 2", "concept": "Original concept details", "hook": "Hook", "setting": "Environment", "visual_direction": "Style notes", "why_it_works": "Reasoning"}},
    {{"title": "Concept 3", "concept": "Original concept details", "hook": "Hook", "setting": "Environment", "visual_direction": "Style notes", "why_it_works": "Reasoning"}}
  ]
}}
"""
        try:
            with st.spinner("🧠 AI sedang menganalisis ide..."):
                result = generate_ai(client, prompt, json_mode=True)
            st.session_state.analysis = result.get("analysis", {})
            st.session_state.concepts = result.get("concepts", [])
            st.session_state.content_type = st.session_state.analysis.get("content_type", "Umum")
            st.session_state.page = "remix"
            st.rerun()
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

# ============================================================
# HALAMAN 2: AI REMIX
# ============================================================
def render_remix():
    st.markdown('<div class="hero"><div class="eyebrow">LANGKAH 02 • MESIN AI REMIX</div><h1>Pilih Konsep Remix Kamu</h1></div>', unsafe_allow_html=True)
    analysis = st.session_state.get("analysis")
    concepts = st.session_state.get("concepts", [])

    if not analysis or not concepts:
        st.warning("Belum ada hasil analisis. Silakan masukkan ide di Beranda.")
        if st.button("← KEMBALI KE BERANDA"): st.session_state.page = "home"; st.rerun()
        return

    cols = st.columns(min(3, len(concepts)))
    for idx, concept in enumerate(concepts[:3]):
        with cols[idx]:
            st.markdown(f'<div class="concept-card"><div class="concept-number">KONSEP {idx + 1}</div><h2>{concept.get("title", "")}</h2><p>{concept.get("concept", "")}</p></div>', unsafe_allow_html=True)
            if st.button(f"PAKAI KONSEP {idx + 1}", key=f"use_concept_{idx}", use_container_width=True, type="primary"):
                st.session_state.selected_concept = concept
                st.session_state.selected_concept_index = idx
                st.session_state.storyboard = None
                st.session_state.page = "storyboard"
                st.rerun()
                # ============================================================
# HALAMAN 3: PAPAN CERITA (STORYBOARD)
# ============================================================
def render_storyboard():
    st.markdown('<div class="hero"><div class="eyebrow">LANGKAH 03 • STORYBOARD</div><h1>Susun Alur Cerita</h1></div>', unsafe_allow_html=True)

    selected = st.session_state.get("selected_concept")
    if not selected:
        st.warning("Belum ada konsep yang dipilih.")
        if st.button("← KEMBALI KE AI REMIX"):
            st.session_state.page = "remix"
            st.rerun()
        return

    scene_count = int(st.session_state.get("scene_count", 1))
    duration_label = st.session_state.get("duration", "8 detik")

    st.markdown(f'<div class="selected-card"><h2>{selected.get("title", "Tanpa Judul")}</h2><p>{selected.get("concept", "")}</p></div>', unsafe_allow_html=True)

    if not st.session_state.get("storyboard"):
        if st.button("⚡ BUAT PAPAN CERITA (STORYBOARD)", type="primary", use_container_width=True):
            client = get_client(st.session_state.api_key)
            if client is None:
                st.error("Masukkan Kunci API Gemini terlebih dahulu.")
                return

            storyboard_prompt = f"""
Create an ORIGINAL storyboard based on this concept:
Duration: {duration_label} | Scenes: {scene_count}
Concept: {json.dumps(selected, ensure_ascii=False)}
Instruction: {st.session_state.get('custom_instruction', '')}

Create EXACTLY {scene_count} scenes. Return ONLY valid JSON:
{{
  "storyboard": [
    {{
      "scene_number": 1,
      "timecode": "00:00-00:08",
      "purpose": "Purpose",
      "visual": "Visual details",
      "action": "Actions",
      "camera": "Camera shot",
      "audio": "Audio SFX"
    }}
  ]
}}
"""
            with st.spinner(f"Menyusun {scene_count} adegan papan cerita..."):
                try:
                    result = generate_ai(client, storyboard_prompt, json_mode=True, max_output_tokens=12000)
                    if result and "storyboard" in result:
                        st.session_state.storyboard = result["storyboard"][:scene_count]
                        st.session_state.current_scene = 1
                        st.session_state.scene_prompts = {}
                        st.session_state.scene_screenshots = {}
                        st.success("Papan cerita berhasil dibuat!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

    storyboard = st.session_state.get("storyboard")
    if storyboard:
        for scene in storyboard:
            sn = scene.get("scene_number", "?")
            with st.expander(f"ADEGAN / SCENE {sn} • {scene.get('timecode', '')}", expanded=(sn == 1)):
                st.write(f"**Visual:** {scene.get('visual', '')}")
                st.write(f"**Aksi (Action):** {scene.get('action', '')}")
                st.write(f"**Kamera:** {scene.get('camera', '')}")

        st.markdown("---")
        if st.button("LANJUT KE PEMBUAT ADEGAN (SCENE GENERATOR) →", type="primary", use_container_width=True):
            st.session_state.current_scene = 1
            st.session_state.page = "scenes"
            st.rerun()

# ============================================================
# HALAMAN 4: PEMBUAT ADEGAN (SCENE GENERATOR)
# ============================================================
def render_scenes():
    st.markdown('<div class="hero"><div class="eyebrow">LANGKAH 04 • PROMPT GOOGLE FLOW / VEO</div><h1>Buat Prompt Adegan Video</h1></div>', unsafe_allow_html=True)

    storyboard = st.session_state.get("storyboard", [])
    if not storyboard:
        st.warning("Papan cerita belum tersedia.")
        if st.button("← KEMBALI KE STORYBOARD"):
            st.session_state.page = "storyboard"
            st.rerun()
        return

    total_scenes = len(storyboard)
    current_scene = max(1, min(st.session_state.get("current_scene", 1), total_scenes))
    st.session_state.current_scene = current_scene

    nav_cols = st.columns(min(8, total_scenes))
    for i in range(total_scenes):
        s_num = i + 1
        with nav_cols[i % min(8, total_scenes)]:
            has_p = s_num in st.session_state.get("scene_prompts", {})
            btn_type = "primary" if s_num == current_scene else "secondary"
            label = f"✓ S{s_num}" if has_p else f"S{s_num}"
            if st.button(label, key=f"scene_nav_{s_num}", use_container_width=True, type=btn_type):
                st.session_state.current_scene = s_num
                st.rerun()

    scene = storyboard[current_scene - 1]
    st.markdown(f"### 🎬 ADEGAN / SCENE {current_scene}")
    st.write(f"**Visual:** {scene.get('visual', '')}")
    st.write(f"**Aksi:** {scene.get('action', '')}")

    existing_prompt = st.session_state.get("scene_prompts", {}).get(current_scene)
    if existing_prompt:
        st.success("Prompt Bahasa Inggris untuk Google Flow berhasil dibuat!")
        st.text_area("Salin prompt ini ke Google Flow / Veo:", value=existing_prompt, height=180)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 BUAT ULANG PROMPT", use_container_width=True):
                del st.session_state.scene_prompts[current_scene]
                st.rerun()
        with c2:
            if current_scene < total_scenes:
                if st.button("ADEGAN SELANJUTNYA →", type="primary", use_container_width=True):
                    st.session_state.current_scene += 1
                    st.rerun()
            else:
                if st.button("SELESAI & PAKET SEO →", type="primary", use_container_width=True):
                    st.session_state.page = "seo"
                    st.rerun()
    else:
        if st.button(f"⚡ GENERATE PROMPT FLOW UNTUK SCENE {current_scene}", type="primary", use_container_width=True):
            client = get_client(st.session_state.api_key)
            if client is None:
                st.error("Masukkan Kunci API Gemini terlebih dahulu.")
                return

            flow_prompt = f"""
Create ONE production-ready video prompt for Google Flow / Veo based on this scene:
Style: {st.session_state.visual_style} | Aspect Ratio: {st.session_state.aspect_ratio}
Visual: {scene.get('visual', '')} | Action: {scene.get('action', '')} | Camera: {scene.get('camera', '')}

Write ONE detailed paragraph in English. Output ONLY the raw prompt text.
"""
            with st.spinner("Membuat prompt Google Flow (Bahasa Inggris)..."):
                try:
                    prompt_res = generate_ai(client, flow_prompt, json_mode=False)
                    st.session_state.scene_prompts[current_scene] = prompt_res.strip()
                    st.rerun()
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

# ============================================================
# HALAMAN 5: SELESAI & PAKET SEO
# ============================================================
def render_seo():
    st.markdown('<div class="hero"><div class="eyebrow">LANGKAH 05 • PUBLIKASI</div><h1>Paket SEO & Publikasi</h1></div>', unsafe_allow_html=True)
    selected = st.session_state.get("selected_concept", {})

    if not st.session_state.get("seo_package"):
        if st.button("🚀 BUAT PAKET SEO KONTEN", type="primary", use_container_width=True):
            client = get_client(st.session_state.api_key)
            if client is None:
                st.error("Masukkan Kunci API Gemini terlebih dahulu.")
                return

            seo_prompt = f"""
Create a complete YouTube SEO pack for this concept:
Title: {selected.get('title', '')} | Concept: {selected.get('concept', '')}

Return ONLY valid JSON:
{{
  "titles": ["Title 1", "Title 2", "Title 3"],
  "description": "YouTube description...",
  "keywords": ["keyword1", "keyword2"],
  "hashtags": ["#tag1", "#tag2"],
  "thumbnail_text": "Text on thumbnail",
  "pinned_comment": "Comment"
}}
"""
            with st.spinner("Menyusun judul, deskripsi, dan tag SEO..."):
                try:
                    st.session_state.seo_package = generate_ai(client, seo_prompt, json_mode=True)
                    st.rerun()
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

    seo = st.session_state.get("seo_package")
    if seo:
        st.markdown("### 🏆 REKOMENDASI JUDUL")
        for idx, title in enumerate(seo.get("titles", []), start=1):
            st.text_input(f"Opsi Judul {idx}", value=title, key=f"title_{idx}")

        st.markdown("### 📝 DESKRIPSI VIDEO")
        st.text_area("Deskripsi", value=seo.get("description", ""), height=120)

        st.markdown("### 🔍 HASHTAG")
        st.text_input("Hashtag", value=" ".join(seo.get("hashtags", [])))

        st.markdown("---")
        st.success("🎉 Proyek Selesai!")
        if st.button("🆕 BUAT PROYEK BARU", type="primary", use_container_width=True):
            reset_project()
            st.rerun()

# ============================================================
# ROUTER UTAMA
# ============================================================
page_map = {
    "home": render_home,
    "remix": render_remix,
    "storyboard": render_storyboard,
    "scenes": render_scenes,
    "seo": render_seo
}

render_func = page_map.get(st.session_state.page, render_home)
render_func()
