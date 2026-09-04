import json
import re
import streamlit as st
from google import genai
from google.genai import types

# ============================================================
# PAGE CONFIG & CSS STYLING
# ============================================================
st.set_page_config(
    page_title="UGC Remix Studio",
    page_icon="🎬",
    layout="wide"
)

MODEL_NAME = "gemini-2.5-flash"

DURATIONS = {
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

st.markdown("""
<style>
.stApp { background-color: #0d1117; color: #f0f6fc; }
.block-container { max-width: 1400px; padding-top: 2rem; }
.hero { padding: 32px; border-radius: 16px; background: linear-gradient(135deg, #1f293d 0%, #111827 100%); border: 1px solid #3b82f6; margin-bottom: 25px; }
.hero h1 { color: #ffffff !important; font-size: 38px; font-weight: 800; margin-bottom: 10px; }
.hero p { color: #e2e8f0 !important; font-size: 16px; line-height: 1.6; }
.card, .metric-card, .concept-card, .selected-card { background: #161b22; border: 1px solid #30363d; border-radius: 14px; padding: 20px; margin-bottom: 16px; color: #f0f6fc; }
.card h3, .metric-card h3, .concept-card h2, .selected-card h2 { color: #ffffff !important; margin-top: 0; }
.muted { color: #cbd5e1 !important; font-size: 14px; line-height: 1.6; }
.badge, .eyebrow, .metric-label, .concept-number { display: inline-block; padding: 6px 14px; border-radius: 20px; background: #2563eb; color: #ffffff !important; font-size: 13px; font-weight: 700; margin-bottom: 12px; }
.workflow { min-height: 120px; background: #161b22; border: 1px solid #3b82f6; border-radius: 12px; padding: 16px; }
.workflow-number { color: #60a5fa; font-weight: 800; font-size: 14px; }
.workflow-title { color: #ffffff !important; font-weight: 700; font-size: 16px; margin-top: 6px; }
.workflow-text { color: #cbd5e1 !important; font-size: 13px; margin-top: 6px; line-height: 1.4; }
.concept-section { margin-top: 12px; font-size: 14px; color: #e2e8f0; }
.concept-section strong { color: #60a5fa; display: block; margin-bottom: 2px; }
div[data-baseweb="select"] > div { background-color: #1f2937 !important; color: #ffffff !important; }
.stTextArea textarea, .stTextInput input { background-color: #1f2937 !important; color: #ffffff !important; border: 1px solid #4b5563 !important; }
label { color: #f3f4f6 !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE INITIALIZATION & HELPERS
# ============================================================
def init_session_state():
    defaults = {
        "page": "home", "api_key": "", "analysis": None, "concepts": [],
        "selected_concept": None, "selected_concept_index": 0, "storyboard": None,
        "current_scene": 1, "scene_prompts": {}, "scene_screenshots": {},
        "seo_package": None, "content_type": "General", "visual_style": "Realistic cinematic",
        "aspect_ratio": "9:16 — Shorts / Reels / TikTok", "duration": "8 seconds",
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
    if client is None: raise ValueError("Gemini API key belum dimasukkan.")
    config = types.GenerateContentConfig(temperature=temperature, max_output_tokens=max_output_tokens)
    if json_mode: config.response_mime_type = "application/json"
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt, config=config)
    if not response or not response.text: raise ValueError("Gemini tidak memberikan respon.")
    if json_mode:
        result = clean_json(response.text)
        if result is None: raise ValueError("JSON tidak valid.")
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
# SIDEBAR NAVIGATION
# ============================================================
with st.sidebar:
    st.markdown('<div style="font-size:22px;font-weight:800;color:#ffffff;">🎬 UGC Remix Studio</div>', unsafe_allow_html=True)
    st.divider()
    st.session_state.api_key = st.text_input("Gemini API Key", value=st.session_state.api_key, type="password")
    st.divider()
    if st.button("🏠 Home", use_container_width=True): st.session_state.page = "home"; st.rerun()
    if st.button("🧠 AI Remix", use_container_width=True): st.session_state.page = "remix"; st.rerun()
    if st.button("🎞️ Storyboard", use_container_width=True): st.session_state.page = "storyboard"; st.rerun()
    if st.button("🎬 Scene Generator", use_container_width=True): st.session_state.page = "scenes"; st.rerun()
    if st.button("🚀 Finish & SEO", use_container_width=True): st.session_state.page = "seo"; st.rerun()
    st.divider()
    if st.button("🗑️ Reset Project", use_container_width=True): reset_project(); st.rerun()
        # ============================================================
# PAGE 1: HOME
# ============================================================
def render_home():
    st.markdown('<div class="hero"><div class="badge">V2 • UNIVERSAL CONTENT ENGINE</div><h1>Turn Any Reference Into An Original Video</h1><p>Upload a reference video, screenshots, or describe an idea. AI analyzes the entertainment structure, creates original remix concepts, builds the storyboard, and prepares scene-by-scene prompts for Google Flow / Veo.</p></div>', unsafe_allow_html=True)

    st.markdown("### ⚡ Workflow")
    cols = st.columns(5)
    workflow = [
        ("01", "Reference", "Video, screenshot, or text."),
        ("02", "Analyze", "Understand hook and story."),
        ("03", "Auto Remix", "Create 3 original concepts."),
        ("04", "Storyboard", "Build all scenes."),
        ("05", "Flow Prompt", "Generate prompts for Flow/Veo.")
    ]
    for col, item in zip(cols, workflow):
        number, title, description = item
        with col:
            st.markdown(f'<div class="workflow"><div class="workflow-number">{number}</div><div class="workflow-title">{title}</div><div class="workflow-text">{description}</div></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown("### 🎥 Reference")

    reference_type = st.radio("Pilih sumber reference", ["Video", "Screenshots", "Text / Idea"], horizontal=True)
    video_file = None
    image_files = []
    reference_text = ""

    if reference_type == "Video":
        video_file = st.file_uploader("Upload reference video", type=["mp4", "mov", "webm", "avi", "mkv"])
    elif reference_type == "Screenshots":
        image_files = st.file_uploader("Upload screenshots", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
    else:
        reference_text = st.text_area("Jelaskan reference / ide kamu", height=140, placeholder="Contoh: Seorang karakter mencoba membuka kotak misterius...")

    st.markdown("### 🎨 Creative Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.visual_style = st.selectbox("Visual Style", ["Realistic cinematic", "Stylized 3D animation", "Cute cartoon", "Photorealistic comedy", "Cinematic live action", "Anime-inspired original", "Dark cinematic", "Fast viral social video"])
    with col2:
        st.session_state.aspect_ratio = st.selectbox("Aspect Ratio", ["9:16 — Shorts / Reels / TikTok", "16:9 — YouTube Long Form", "1:1 — Square"])

    st.session_state.duration = st.selectbox("Video Duration", list(DURATIONS.keys()))
    st.session_state.scene_count = DURATIONS[st.session_state.duration]
    st.info(f"⏱️ {st.session_state.duration} = {st.session_state.scene_count} scene (sekitar 8 detik per scene)")

    st.session_state.custom_instruction = st.text_area("User Creative Instruction", height=100, placeholder="Contoh: Buat lebih lucu, pacing cepat, ending punya twist...")

    st.write("")
    if st.button("🚀 ANALYZE + AUTO REMIX", type="primary", use_container_width=True):
        if not st.session_state.api_key:
            st.error("Masukkan Gemini API Key terlebih dahulu di sidebar.")
            return

        client = get_client(st.session_state.api_key)
        if client is None:
            st.error("Gemini API key tidak valid.")
            return

        reference_description = reference_text if reference_type == "Text / Idea" else "User uploaded media reference"

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
            with st.spinner("🧠 AI menganalisis..."):
                result = generate_ai(client, prompt, json_mode=True)
            st.session_state.analysis = result.get("analysis", {})
            st.session_state.concepts = result.get("concepts", [])
            st.session_state.content_type = st.session_state.analysis.get("content_type", "General")
            st.session_state.page = "remix"
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# ============================================================
# PAGE 2: AI REMIX
# ============================================================
def render_remix():
    st.markdown('<div class="hero"><div class="eyebrow">STEP 02 • AI REMIX ENGINE</div><h1>Choose Your Remix</h1></div>', unsafe_allow_html=True)
    analysis = st.session_state.get("analysis")
    concepts = st.session_state.get("concepts", [])

    if not analysis or not concepts:
        st.warning("Belum ada hasil analisis.")
        if st.button("← BACK TO HOME"): st.session_state.page = "home"; st.rerun()
        return

    cols = st.columns(min(3, len(concepts)))
    for idx, concept in enumerate(concepts[:3]):
        with cols[idx]:
            st.markdown(f'<div class="concept-card"><div class="concept-number">CONCEPT {idx + 1}</div><h2>{concept.get("title", "")}</h2><p>{concept.get("concept", "")}</p></div>', unsafe_allow_html=True)
            if st.button(f"USE CONCEPT {idx + 1}", key=f"use_concept_{idx}", use_container_width=True, type="primary"):
                st.session_state.selected_concept = concept
                st.session_state.selected_concept_index = idx
                st.session_state.storyboard = None
                st.session_state.page = "storyboard"
                st.rerun()
                # ============================================================
# PAGE 3: STORYBOARD
# ============================================================
def render_storyboard():
    st.markdown('<div class="hero"><div class="eyebrow">STEP 03 • STORYBOARD</div><h1>Build The Story</h1></div>', unsafe_allow_html=True)

    selected = st.session_state.get("selected_concept")
    if not selected:
        st.warning("Belum ada konsep yang dipilih.")
        if st.button("← GO TO AI REMIX"):
            st.session_state.page = "remix"
            st.rerun()
        return

    scene_count = int(st.session_state.get("scene_count", 1))
    duration_label = st.session_state.get("duration", "8 seconds")

    st.markdown(f'<div class="selected-card"><h2>{selected.get("title", "Untitled")}</h2><p>{selected.get("concept", "")}</p></div>', unsafe_allow_html=True)

    if not st.session_state.get("storyboard"):
        if st.button("⚡ GENERATE STORYBOARD", type="primary", use_container_width=True):
            client = get_client(st.session_state.api_key)
            if client is None:
                st.error("Masukkan Gemini API Key terlebih dahulu.")
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
            with st.spinner(f"Building {scene_count}-scene storyboard..."):
                try:
                    result = generate_ai(client, storyboard_prompt, json_mode=True, max_output_tokens=12000)
                    if result and "storyboard" in result:
                        st.session_state.storyboard = result["storyboard"][:scene_count]
                        st.session_state.current_scene = 1
                        st.session_state.scene_prompts = {}
                        st.session_state.scene_screenshots = {}
                        st.success("Storyboard berhasil dibuat!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    storyboard = st.session_state.get("storyboard")
    if storyboard:
        for scene in storyboard:
            sn = scene.get("scene_number", "?")
            with st.expander(f"SCENE {sn} • {scene.get('timecode', '')}", expanded=(sn == 1)):
                st.write(f"**Visual:** {scene.get('visual', '')}")
                st.write(f"**Action:** {scene.get('action', '')}")
                st.write(f"**Camera:** {scene.get('camera', '')}")

        st.markdown("---")
        if st.button("CONTINUE TO SCENE GENERATOR →", type="primary", use_container_width=True):
            st.session_state.current_scene = 1
            st.session_state.page = "scenes"
            st.rerun()

# ============================================================
# PAGE 4: SCENE GENERATOR
# ============================================================
def render_scenes():
    st.markdown('<div class="hero"><div class="eyebrow">STEP 04 • FLOW / VEO PROMPT ENGINE</div><h1>Generate Your Scenes</h1></div>', unsafe_allow_html=True)

    storyboard = st.session_state.get("storyboard", [])
    if not storyboard:
        st.warning("Storyboard belum tersedia.")
        if st.button("← BACK TO STORYBOARD"):
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
    st.markdown(f"### 🎬 SCENE {current_scene}")
    st.write(f"**Visual:** {scene.get('visual', '')}")
    st.write(f"**Action:** {scene.get('action', '')}")

    existing_prompt = st.session_state.get("scene_prompts", {}).get(current_scene)
    if existing_prompt:
        st.success("Prompt scene ini berhasil dibuat!")
        st.text_area("Copy prompt ini ke Google Flow:", value=existing_prompt, height=180)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 REGENERATE PROMPT", use_container_width=True):
                del st.session_state.scene_prompts[current_scene]
                st.rerun()
        with c2:
            if current_scene < total_scenes:
                if st.button("NEXT SCENE →", type="primary", use_container_width=True):
                    st.session_state.current_scene += 1
                    st.rerun()
            else:
                if st.button("FINISH & SEO →", type="primary", use_container_width=True):
                    st.session_state.page = "seo"
                    st.rerun()
    else:
        if st.button(f"⚡ GENERATE SCENE {current_scene} PROMPT", type="primary", use_container_width=True):
            client = get_client(st.session_state.api_key)
            if client is None:
                st.error("Masukkan Gemini API Key terlebih dahulu.")
                return

            flow_prompt = f"""
Create ONE production-ready video prompt for Google Flow / Veo based on this scene:
Style: {st.session_state.visual_style} | Aspect Ratio: {st.session_state.aspect_ratio}
Visual: {scene.get('visual', '')} | Action: {scene.get('action', '')} | Camera: {scene.get('camera', '')}

Write ONE detailed paragraph in English. Output ONLY the raw prompt text.
"""
            with st.spinner("Generating Flow prompt..."):
                try:
                    prompt_res = generate_ai(client, flow_prompt, json_mode=False)
                    st.session_state.scene_prompts[current_scene] = prompt_res.strip()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ============================================================
# PAGE 5: FINISH & SEO
# ============================================================
def render_seo():
    st.markdown('<div class="hero"><div class="eyebrow">STEP 05 • PUBLISHING</div><h1>SEO & Publishing Pack</h1></div>', unsafe_allow_html=True)
    selected = st.session_state.get("selected_concept", {})

    if not st.session_state.get("seo_package"):
        if st.button("🚀 GENERATE SEO PACKAGE", type="primary", use_container_width=True):
            client = get_client(st.session_state.api_key)
            if client is None:
                st.error("Masukkan Gemini API Key terlebih dahulu.")
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
            with st.spinner("Generating SEO package..."):
                try:
                    st.session_state.seo_package = generate_ai(client, seo_prompt, json_mode=True)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    seo = st.session_state.get("seo_package")
    if seo:
        st.markdown("### 🏆 TITLES")
        for idx, title in enumerate(seo.get("titles", []), start=1):
            st.text_input(f"Title {idx}", value=title, key=f"title_{idx}")

        st.markdown("### 📝 DESCRIPTION")
        st.text_area("Description", value=seo.get("description", ""), height=120)

        st.markdown("### 🔍 HASHTAGS")
        st.text_input("Hashtags", value=" ".join(seo.get("hashtags", [])))

        st.markdown("---")
        st.success("🎉 Project Complete!")
        if st.button("🆕 NEW PROJECT", type="primary", use_container_width=True):
            reset_project()
            st.rerun()

# ============================================================
# MAIN ROUTER
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
