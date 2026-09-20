import streamlit as st
from google import genai
from google.genai import types
import config

st.set_page_config(
    page_title="GTA V Remixer & Scene Prompt Engine",
    page_icon="🎬",
    layout="wide"
)

MODEL_NAME = "gemini-3.6-flash"

# Inisialisasi State Session
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "scene_prompts" not in st.session_state:
    st.session_state.scene_prompts = {}
if "scene_frames" not in st.session_state:
    st.session_state.scene_frames = {}
if "user_scene_obstacles" not in st.session_state:
    st.session_state.user_scene_obstacles = {}

def get_client():
    api_key = st.sidebar.text_input("Gemini API Key:", type="password")
    if not api_key:
        st.info("Silakan masukkan API Key Gemini di sidebar sebelah kiri untuk memulai.")
        return None
    try:
        return genai.Client(api_key=api_key.strip())
    except Exception as e:
        st.error(f"Gagal inisialisasi API Key: {e}")
        return None

def scene_count():
    dur_choice = st.session_state.get("selected_duration", "16 detik (2 Scene - Shorts Standar)")
    val = config.DURATION_SCENES.get(dur_choice, 0)
    if val == 0:
        return st.session_state.get("detected_scenes", 2)
    return val

def analyze_reference(client, file_part=None, custom_notes: str = ""):
    prompt = f"""
Analyze this game/video footage reference or text request for creating a GTA V style obstacle parkour video.
Extract and return a valid JSON object with the following structure:
{{
  "remixed_mutation": {{
    "runner_baru": "Detailed character description",
    "boss_baru": "Detailed obstacle/doll target description",
    "map_environment": "Detailed background environment description",
    "prop_stand": "Detailed runway/platform surface description"
  }},
  "climax_action": "Description of chaotic multi-hit climax action for final scene",
  "storyboard_plan": [
    {{"scene": 1, "fokus_aksi": "Specific runner action for scene 1"}},
    {{"scene": 2, "fokus_aksi": "Specific runner action for scene 2"}}
  ]
}}
Additional Notes from User: {custom_notes}
Output JSON ONLY.
"""
    parts = [file_part] if file_part else []
    res_text = config.ask(client, prompt, parts=parts, json_mode=True, model_name=MODEL_NAME)
    return config.extract_json(res_text)

def generate_scene_prompt(scene_number: int) -> bool:
    client = get_client()
    if not client:
        return False

    analysis = st.session_state.analysis
    if not analysis:
        st.error("Data analisis belum tersedia.")
        return False

    mutation = analysis.get("remixed_mutation", {})
    storyboard = analysis.get("storyboard_plan", [])
    total_scenes = scene_count()
    is_final_scene = (scene_number == total_scenes)

    map_env = st.session_state.get("selected_map", config.MAP_OPTIONS[0])
    if map_env == "Auto (Ikuti Remix UGC)":
        map_env = mutation.get("map_environment", "Container Roofs High Above Ocean (Siang Bolong)")

    prop_stand = st.session_state.get("selected_prop_stand", config.PROP_STAND_OPTIONS[0])
    if prop_stand == "Auto (Ikuti Remix UGC)":
        prop_stand = mutation.get("prop_stand", "Container Roofs")

    climax_act = st.session_state.get("selected_climax_action", config.CLIMAX_ACTION_OPTIONS[0])
    if climax_act == "Auto (Ikuti Remix UGC)":
        climax_act = analysis.get("climax_action", "Double-hit combo and chaotic ragdoll collapse")

    scene_focus = "Melanjutkan aksi lari dan rangkaian rintangan di atas jalur."
    if storyboard and len(storyboard) >= scene_number:
        scene_focus = storyboard[scene_number - 1].get("fokus_aksi", scene_focus)

    custom_obstacle_instruction = st.session_state.user_scene_obstacles.get(scene_number, "")
    obstacle_inject_str = ""
    if custom_obstacle_instruction:
        obstacle_inject_str = f"SPECIAL SCENE OBSTACLE MECHANIC: {custom_obstacle_instruction}"

    prev_frame_context = ""
    if scene_number > 1 and (scene_number - 1) in st.session_state.scene_frames:
        prev_frame_context = f"STRICT CONTINUITY & SPATIAL LOCK: Scene {scene_number} MUST start precisely at the exact spatial coordinates where Scene {scene_number-1} ended."

    # REVISI LOGIKA PROMPT (ANTI SKOR UI + PERMANENT PHYSICS + RUNNER AMAN DI SCENE AWAL)
    if is_final_scene:
        action_rules = f"""
ULTIMATE CLIMAX & SACRIFICE FALL (FINAL SCENE {scene_number} ONLY):
- Runner ({mutation.get('runner_baru')}) executes final combo: {climax_act}.
- Runner strikes remaining targets on {prop_stand}.
- FINAL SACRIFICE FALL: Runner loses balance and FALLS OFF THE EDGE OF THE BUILDING/CONTAINER TOGETHER WITH TARGET DOLLS into free-fall ragdoll physics chaos toward {map_env}.
"""
    else:
        action_rules = f"""
STRICT RUNWAY CONTINUATION (SCENE {scene_number} OF {total_scenes}):
- RUNNER MUST REMAIN ON TOP OF THE ROOFTOP / CONTAINER / RUNWAY PLATFORM. DO NOT JUMP OR FALL OFF THE EDGE.
- Runner ({mutation.get('runner_baru')}) continues running forward on {prop_stand}, striking/kicking targets cleanly without falling off.
- Focus action for this scene: {scene_focus}.
"""

    prompt = f"""
Write ONE ultra-detailed AI video generation prompt in ENGLISH for Scene {scene_number} of {total_scenes} (approx. 8 seconds segment).

VISUAL STYLE & ENVIRONMENT:
- Render Style: {st.session_state.get('selected_style', config.STYLE_OPTIONS[0])}
- Aspect Ratio: {st.session_state.get('selected_aspect', config.ASPECT_OPTIONS[0])}
- MAP BACKGROUND: {map_env}
- PLATFORM SURFACE: {prop_stand}
- Bright daytime lighting, vivid sunny sky, high-contrast 3D game visuals.

CLEAN FOOTAGE & NO UI OVERLAY RULES (VERY IMPORTANT):
- NO score numbers (e.g. no '+130' or floating points), NO character name tags, NO floating health bars, NO game UI, NO animated pop-up graphics. Pure clean 3D game cinematic footage.

PERMANENT DESTRUCTIVE PHYSICS LAWS:
- Once an object, barrel, or target doll is struck and knocked down or knocked off the platform, IT MUST STAY DOWN OR FALL AWAY PERMANENTLY. Fallen barrels and dolls MUST NOT magically stand back up or reset position.

ASSETS & ENTITIES LOCK:
- Runner Character: {mutation.get('runner_baru')}
- Target Entities (Standing visibly on {prop_stand} from Frame 1, zero pop-in): {mutation.get('boss_baru')}

NAVIGATIONAL MECHANIC:
{obstacle_inject_str}

ACTION INSTRUCTIONS:
{action_rules}

CAMERA & AUDIO:
- Camera: Dynamic third-person trailing shot locked tightly behind the runner.
- Audio: Immersive impact sound effects, heavy footfalls, wind roar, dynamic ragdoll thuds.
{prev_frame_context}

RULES:
Output ONLY the final raw English prompt without markdown formatting or extra text.
"""
    with st.spinner(f"Menyusun Prompt Scene {scene_number}..."):
        try:
            res_prompt = config.ask(client, prompt, json_mode=False, model_name=MODEL_NAME)
            st.session_state.scene_prompts[scene_number] = res_prompt.strip()
            return True
        except Exception as exc:
            st.error(f"Gagal menyusun prompt Scene {scene_number}: {exc}")
            return False

# HEADER APLIKASI
st.title("🎬 GTA V Remixer & Scene Prompt Engine")
st.caption(f"Engine Version: {config.APP_VERSION}")

# SIDEBAR CONFIGURATION (100% PERSIS SEPERTI SEMULA, TERMASUK 10 PILIHAN LENGKAP)
st.sidebar.header("⚙️ Pengaturan Prompt & Scene")
st.session_state.selected_duration = st.sidebar.selectbox("Pilih Durasi Video:", list(config.DURATION_SCENES.keys()), index=1)
st.session_state.selected_style = st.sidebar.selectbox("Gaya Visual:", config.STYLE_OPTIONS)
st.session_state.selected_map = st.sidebar.selectbox("Pilih Map / Lingkungan:", config.MAP_OPTIONS)
st.session_state.selected_prop_stand = st.sidebar.selectbox("Tumpuan / Alas Panggung:", config.PROP_STAND_OPTIONS)
st.session_state.selected_climax_action = st.sidebar.selectbox("Aksi Klimaks (Scene Akhir):", config.CLIMAX_ACTION_OPTIONS)

st.sidebar.divider()
st.sidebar.subheader("📐 Aspect Ratio")
st.session_state.selected_aspect = st.sidebar.radio("Ukuran Format Video:", config.ASPECT_OPTIONS)

# TAB INTERFACE (100% PERSIS UI LAMA ANDA)
tab1, tab2, tab3 = st.tabs(["⚡ Fast Generator (Tanpa Media)", "🖼️ Remix Media (Upload Referensi)", "📋 Storyboard & Results"])

with tab1:
    st.subheader("1. Konfigurasi Karakter & Target")
    col1, col2 = st.columns(2)
    with col1:
        runner_choice = st.selectbox("Pilih Character / Runner Utama:", config.RUNNER_PRESETS)
        if runner_choice == "Custom / Ketik Sendiri":
            custom_runner = st.text_input("Deskripsi Runner Custom:", "Pocong melompat cepat memakai sepatu kets")
        else:
            custom_runner = runner_choice

    with col2:
        target_dolls = st.text_input("Target / Boneka Rintangan:", "Boneka Badut Warna-warni di atas drum bekas")

    st.subheader("2. Tambahkan Rintangan Khusus Per Scene")
    num_scenes = scene_count()
    for i in range(1, num_scenes + 1):
        obs_label = list(config.OBSTACLE_OPTIONS.keys())
        selected_obs = st.selectbox(f"Rintangan Khusus Scene {i}:", obs_label, key=f"obs_select_tab1_{i}")
        st.session_state.user_scene_obstacles[i] = config.OBSTACLE_OPTIONS[selected_obs]

    if st.button("🚀 Buat Prompt Semua Scene (Fast Mode)", type="primary"):
        client = get_client()
        if client:
            st.session_state.analysis = {
                "remixed_mutation": {
                    "runner_baru": custom_runner,
                    "boss_baru": target_dolls,
                    "map_environment": st.session_state.selected_map,
                    "prop_stand": st.session_state.selected_prop_stand
                },
                "climax_action": st.session_state.selected_climax_action,
                "storyboard_plan": [{"fokus_aksi": f"Runner beraksi melewati rintangan di scene {idx}"} for idx in range(1, num_scenes + 1)]
            }
            
            st.session_state.scene_prompts = {}
            for sc in range(1, num_scenes + 1):
                generate_scene_prompt(sc)
            st.success("Semua Prompt Scene Berhasil Dibuat! Cek Tab 'Storyboard & Results'.")

with tab2:
    st.subheader("Upload Gambar/Video Referensi")
    uploaded_file = st.file_uploader("Upload Tangkapan Layar / Video Game:", type=["jpg", "jpeg", "png", "mp4"])
    custom_notes = st.text_area("Catatan Tambahan untuk AI Remix:", "Buat pergerakan lebih ekstrem dan dinamis.")

    if st.button("🔍 Analisis & Remix Media", type="primary"):
        client = get_client()
        if client:
            file_part = None
            if uploaded_file:
                bytes_data = uploaded_file.getvalue()
                file_part = types.Part.from_bytes(data=bytes_data, mime_type=uploaded_file.type)
            
            with st.spinner("Menganalisis media & menyusun storyboard..."):
                try:
                    result = analyze_reference(client, file_part, custom_notes)
                    st.session_state.analysis = result
                    st.success("Analisis Berhasil!")
                except Exception as e:
                    st.error(f"Gagal melakukan analisis: {e}")

with tab3:
    st.subheader("📋 Dashboard Storyboard & Hasil Prompt")
    
    if st.session_state.analysis:
        st.write("### 🧬 Parameter Remix Terdeteksi:")
        st.json(st.session_state.analysis)

        st.divider()
        st.write("### 🎬 Prompt Per Scene untuk Video Generator:")

        total_sc = scene_count()
        for sc in range(1, total_sc + 1):
            with st.expander(f"📌 Scene {sc} of {total_sc} Prompt", expanded=True):
                if sc in st.session_state.scene_prompts:
                    st.code(st.session_state.scene_prompts[sc], language="text")
                else:
                    st.warning("Prompt belum dibuat.")
                
                if st.button(f"🔄 Regenerate Scene {sc}", key=f"regen_{sc}"):
                    generate_scene_prompt(sc)
                    st.rerun()

                st.subheader(f"🖼️ Reference Last Frame for Continuity Scene {sc}")
                uploaded_frame = st.file_uploader(f"Upload Tangkapan Akhir Video Scene {sc} (opsional):", type=["jpg", "png"], key=f"frame_up_{sc}")
                if uploaded_frame:
                    st.session_state.scene_frames[sc] = uploaded_frame.name
                    st.info(f"Frame Scene {sc} tersimpan untuk menjaga kontinuitas ke Scene {sc+1}.")
    else:
        st.info("Belum ada data prompt. Silakan buat melalui Tab 'Fast Generator' atau 'Remix Media'.")
