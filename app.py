import json
import math
import os
import time
import streamlit as st
from PIL import Image
import google.generativeai as genai

# ==========================================
# 1. PAGE CONFIG & CONSTANTS
# ==========================================
st.set_page_config(page_title="UGC Remix Studio v14.3", page_icon="🎬", layout="wide")

PRIMARY_MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash"]
APP_VERSION = "14.3 — Clean & Secured Edition"

DURATION_SCENES = {
    "Auto (Sesuai Durasi & Video Referensi)": 0,
    "8 detik (1 Scene - Shorts Kilat)": 1,
    "16 detik (2 Scene - Shorts Standar)": 2,
    "24 detik (3 Scene)": 3,
    "32 detik (4 Scene - Standar UGC)": 4,
    "40 detik (5 Scene)": 5,
    "48 detik (6 Scene)": 6,
    "56 detik (7 Scene)": 7,
    "64 detik (8 Scene - Long Form)": 8,
}

STYLE_OPTIONS = [
    "GTA V Modded Gameplay Style", 
    "3D Animated Game Graphics", 
    "Unreal Engine 5 Parkour Render",
    "Photorealistic Cinematic Action"
]

CAMERA_OPTIONS = [
    "Auto / Dynamic Tracking", 
    "Slow Cinematic Zoom-In", 
    "Smooth Side Panning Shot",
    "FPV Drone Chase Cam",
    "Low Angle Action Shot"
]

# --- 10 RUNNER PRESETS LENGKAP ---
RUNNER_PRESETS = [
    "1. Pocong Gesit", 
    "2. Minecraft Creeper", 
    "3. Bebek Karet Raksasa", 
    "4. Fat Orange Cat", 
    "5. Huggy Wuggy", 
    "6. Skibidi Toilet", 
    "7. Spiderman Kocak", 
    "8. San Andreas CJ", 
    "9. Ultraman Sunset", 
    "10. Custom / Ketik Sendiri"
]

# --- 10 TARGET DOLL PRESETS LENGKAP ---
TARGET_DOLL_PRESETS = [
    "Auto / Random Mix", 
    "1. Kapsul Kuning (Minion)", 
    "2. Skibidi Toilet", 
    "3. Noob Roblox", 
    "4. Pepe the Frog", 
    "5. Red Impostor (Among Us)", 
    "6. Monster Bulu Biru (Huggy Wuggy)", 
    "7. Freddy Fazbear", 
    "8. Siren Head", 
    "9. Grimace", 
    "10. Tengkorak Gila"
]

# --- 10 TARGET IDLE PRESETS LENGKAP ---
TARGET_IDLE_PRESETS = [
    "Auto / Random Mix", 
    "1. 🕺 Joget & Konyol", 
    "2. 😱 Panik & Ketakutan", 
    "3. 😎 Sombong & Ngeledek (Chest Slap, Taunting)", 
    "4. 😴 Tertidur Pulas", 
    "5. 🦾 Pose Binaraga / Flexing", 
    "6. 🧘 Meditasi Melayang", 
    "7. 😭 Menangis Meraung", 
    "8. 🎯 Main HP Santai", 
    "9. 🍔 Makan Burger Jumbo", 
    "10. 🧱 Berdiri Kaku Patung"
]

# --- 10 MAP OPTIONS LENGKAP ---
MAP_OPTIONS = [
    "Auto (Ikuti Remix UGC)", 
    "1. Maze Bank Tower Rooftop", 
    "2. Mount Chiliad Mega Ramp & Ridge", 
    "3. Neon Cyberpunk Sky Track", 
    "4. Volcano Magma Ridge", 
    "5. Container Harbor Terminal",
    "6. Desert Grand Canyon Cliff",
    "7. Floating Cloud Castle",
    "8. Abandoned Subway Tunnel",
    "9. Snow Mountain Ski Slope",
    "10. Cyber City Neon Alley"
]

# --- 10 PROP STAND OPTIONS LENGKAP ---
PROP_STAND_OPTIONS = [
    "Auto (Ikuti Remix UGC)", 
    "1. Direct Concrete Rooftop", 
    "2. Giant Yoga / Exercise Balls", 
    "3. Wooden Crate Stack", 
    "4. Floating Metal Platform", 
    "5. Trampoline Pad",
    "6. Glass Transparent Bridge",
    "7. Spiked Pillar Platform",
    "8. Moving Conveyor Belt",
    "9. Hanging Swing Rope",
    "10. Inflatable Castle Bouncer"
]

# --- 10 CLIMAX ACTION OPTIONS LENGKAP ---
CLIMAX_ACTION_OPTIONS = [
    "Auto (Ikuti Remix UGC)", 
    "1. Double Hit Combo + Sacrifice Fall", 
    "2. Flying Dropkick + Mega Explode", 
    "3. 360 Spinning Backfist + Abyss Drag Drop", 
    "4. Meteor Slam + Destruction Finish", 
    "5. Suplex Over Ledge",
    "6. Rocket Launcher Push",
    "7. Sliding Sweep Kick + Fall",
    "8. Giant Hammer Smash",
    "9. Tackle & Roll Off Cliff",
    "10. Roundhouse Kick KO"
]

ASPECT_OPTIONS = [
    "9:16 — Shorts / Reels / TikTok", 
    "16:9 — YouTube Long", 
    "1:1 — Kotak"
]

# --- 10 OBSTACLE OPTIONS LENGKAP ---
OBSTACLE_OPTIONS = {
    "None / Lari Datar": "",
    "1. 💣 Explosive Red Barrels": "ENVIRONMENT MECHANIC: Highly unstable red explosive barrels line the edges.",
    "2. 🌀 Rotating Spike Rollers": "ENVIRONMENT MECHANIC: Fast-spinning spiked cylinders block the middle path.",
    "3. ⚡ Laser Beams & Death Rays": "ENVIRONMENT MECHANIC: Pulsing red laser grids sweeping across the floor.",
    "4. 🔨 Falling Anvils & Giant Crates": "ENVIRONMENT MECHANIC: Massive wooden crates dropping from above.",
    "5. 🪓 Swinging Pendulum Axes": "ENVIRONMENT MECHANIC: Giant rusted axe blades swinging back and forth.",
    "6. 🧱 Moving Wall Pushers": "ENVIRONMENT MECHANIC: Hydraulic concrete blocks extending outward from sides.",
    "7. 🔥 Lava Pit & Gap Jump": "ENVIRONMENT MECHANIC: Wide open molten lava gap requiring precision jump.",
    "8. ⚡ Electric Grid Floor": "ENVIRONMENT MECHANIC: Electrified metal plates sparking continuously.",
    "9. 🧊 Slippery Ice Slide Tracks": "ENVIRONMENT MECHANIC: Frozen glass-like ramp causing loss of friction.",
    "10. 🎯 Giant Trampoline Bounce Pads": "ENVIRONMENT MECHANIC: High-rebound elastic launchpads built into floor."
}

# --- 10 MANEUVER OPTIONS LENGKAP ---
MANEUVER_OPTIONS = [
    "Auto / Lari Standar (Otomatis Penyesuaian AI)",
    "1. ⚠️ Terpeleset Hampir Jatuh (Near-Miss Clutch & Recovery)",
    "2. 🚀 Melambung Trampolin (Trampoline Vault & Smash)",
    "3. 🛹 Sliding Kolosial (Sliding Under Obstacle)",
    "4. 🧗 Wall-Run & Loncatan Tinggi (Wall-Run Flips)",
    "5. 🔄 Backflip Evade & Counter",
    "6. 💨 Dash Kencang & Rocket Boost",
    "7. 💥 Double Jump & Ground Slam",
    "8. 🤸 Parkour Roll Landing",
    "9. 🛡️ Deflect & Shield Dodge",
    "10. 🏃 Extreme Sprint & Obstacle Vault"
]

MANEUVER_PROMPT_MAP = {
    "Auto / Lari Standar (Otomatis Penyesuaian AI)": "",
    "1. ⚠️ Terpeleset Hampir Jatuh (Near-Miss Clutch & Recovery)": "MANEUVER ACTION: Runner stumbles clumsily near the edge but barely catches the ledge and recovers.",
    "2. 🚀 Melambung Trampolin (Trampoline Vault & Smash)": "MANEUVER ACTION: Runner hits a glowing launch pad, soaring high into the air with a power stomp.",
    "3. 🛹 Sliding Kolosial (Sliding Under Obstacle)": "MANEUVER ACTION: Fast baseball slide directly underneath low-clearance hazards.",
    "4. 🧗 Wall-Run & Loncatan Tinggi (Wall-Run Flips)": "MANEUVER ACTION: Sprinting horizontally along vertical side-walls to bypass open voids.",
    "5. 🔄 Backflip Evade & Counter": "MANEUVER ACTION: Mid-air backward somersault dodging incoming hazards gracefully.",
    "6. 💨 Dash Kencang & Rocket Boost": "MANEUVER ACTION: Sudden speed burst leaving motion blur trails behind.",
    "7. 💥 Double Jump & Ground Slam": "MANEUVER ACTION: Double-leap in mid-air followed by a hard heavy landing impact.",
    "8. 🤸 Parkour Roll Landing": "MANEUVER ACTION: High leap landing smoothly into a forward momentum shoulder roll.",
    "9. 🛡️ Deflect & Shield Dodge": "MANEUVER ACTION: Blocking incoming hazard impact with arm guards before pushing forward.",
    "10. 🏃 Extreme Sprint & Obstacle Vault": "MANEUVER ACTION: Full speed sprint vaulting over obstacles using a single arm press."
}

# ==========================================
# 2. STATE INITIALIZATION & PASSWORD GATE
# ==========================================
DEFAULTS = {
    "page": "home", "api_key": "",
    "visual_style": STYLE_OPTIONS[0], "selected_camera": CAMERA_OPTIONS[0],
    "runner_choice": RUNNER_PRESETS[0], "target_idle_choice": TARGET_IDLE_PRESETS[0],
    "target_doll_choice": TARGET_DOLL_PRESETS[0], "custom_runner": "",
    "selected_map": MAP_OPTIONS[0], "selected_prop_stand": PROP_STAND_OPTIONS[0],
    "selected_climax_action": CLIMAX_ACTION_OPTIONS[0], "aspect_ratio": ASPECT_OPTIONS[0],
    "duration": "32 detik (4 Scene - Standar UGC)",
    "user_scene_obstacles": {}, "user_scene_maneuvers": {}, "analysis": {},
    "scene_prompts": {}, "scene_frames": {}, "seo": {}
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

def check_password():
    """Keamanan Khusus Pribadi"""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔒 Akses Terbatas (Private UGC Studio)")
        st.caption("Aplikasi ini dikunci untuk penggunaan pribadi. Masukkan Master Password.")
        
        PASSWORD_LOKAL = st.secrets.get("APP_PASSWORD", "ugc123")
        
        user_input = st.text_input("Master Password:", type="password")
        if st.button("🔑 Masuk", type="primary"):
            if user_input == PASSWORD_LOKAL:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Password salah.")
        return False
    return True

def go(page_name: str):
    st.session_state.page = page_name
    st.rerun()

# ==========================================
# 3. HELPER FUNCTIONS & API LOGIC
# ==========================================
def extract_json(text: str):
    text = (text or "").strip()
    starts = [p for p in (text.find("{"), text.find("[")) if p >= 0]
    if not starts:
        raise ValueError("Respons AI tidak berisi JSON.")
    start = min(starts)
    for end in range(len(text), start, -1):
        try:
            return json.loads(text[start:end].strip())
        except Exception:
            continue
    raise ValueError("Gagal memproses JSON.")

def configure_api():
    key = st.session_state.get("api_key", "").strip() or os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return False
    genai.configure(api_key=key)
    return True

def ask(prompt: str, parts=None, json_mode: bool = False) -> str:
    if not configure_api():
        raise RuntimeError("API Key belum terkonfigurasi.")

    contents = list(parts or []) + [prompt]
    gen_config = {"temperature": 0.3}
    if json_mode:
        gen_config["response_mime_type"] = "application/json"

    error_logs = []
    for model_candidate in PRIMARY_MODELS:
        try:
            model = genai.GenerativeModel(model_name=model_candidate, generation_config=gen_config)
            response = model.generate_content(contents)
            text = getattr(response, "text", None)
            if text and text.strip():
                return text
        except Exception as exc:
            err_str = str(exc)
            if "429" in err_str or "quota" in err_str.lower():
                raise RuntimeError("⚠️ Kuota API per menit habis (429 Rate Limit). Tunggu 30-45 detik.")
            error_logs.append(f"[{model_candidate}]: {exc}")
            time.sleep(1)

    raise RuntimeError(f"Gagal API: {' | '.join(error_logs)}")

def scene_count() -> int:
    val = DURATION_SCENES.get(st.session_state.duration, 0)
    if val > 0:
        return val
    return st.session_state.get("detected_scenes", 4)

def get_active_config():
    runner = st.session_state.custom_runner if st.session_state.runner_choice == "10. Custom / Ketik Sendiri" else st.session_state.runner_choice
    return {
        "runner": runner, "target_doll": st.session_state.target_doll_choice,
        "map_env": st.session_state.selected_map, "prop_stand": st.session_state.selected_prop_stand,
        "climax_act": st.session_state.selected_climax_action, "style": st.session_state.visual_style,
        "camera": st.session_state.selected_camera, "idle_style": st.session_state.target_idle_choice
    }

def run_analysis():
    cfg = get_active_config()
    target_scenes = scene_count()

    prompt = f"""
Buatkan plan video {target_scenes} adegan berbasis 3D Parkour Obstacle.
Runner: {cfg['runner']}, Target: {cfg['target_doll']}, Map: {cfg['map_env']}, Climax: {cfg['climax_act']}.
Hasilkan JSON: {{"video_duration_seconds": {target_scenes * 8}, "storyboard_plan": [{{"scene": 1, "fokus_aksi": "..."}}]}}
"""
    with st.spinner("Meracik Roadmap..."):
        try:
            raw = ask(prompt, json_mode=True)
            data = extract_json(raw)
            st.session_state.analysis = data
            raw_seconds = data.get("video_duration_seconds", target_scenes * 8)
            st.session_state.detected_scenes = target_scenes if DURATION_SCENES.get(st.session_state.duration, 0) != 0 else max(1, math.ceil(raw_seconds / 8))
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}
            go("analysis")
        except Exception as exc:
            st.error(f"Analisis gagal: {exc}")

def generate_scene_prompt(scene_number: int):
    cfg = get_active_config()
    prompt_parts = []
    prev_scene = scene_number - 1
    
    if prev_scene > 0 and prev_scene in st.session_state.scene_frames:
        try:
            img_data = st.session_state.scene_frames[prev_scene]
            if isinstance(img_data, Image.Image):
                prompt_parts.append(img_data)
            else:
                img_data.seek(0)
                prompt_parts.append(Image.open(img_data).convert("RGB"))
            frame_context = f"VISUAL CONTINUITY: Match character, clothes, color scheme, and environment identical to Scene {prev_scene} image."
        except Exception:
            frame_context = ""
    else:
        frame_context = ""

    obs = OBSTACLE_OPTIONS.get(st.session_state.user_scene_obstacles.get(scene_number, ""), "")
    maneuver = MANEUVER_PROMPT_MAP.get(st.session_state.user_scene_maneuvers.get(scene_number, ""), "")
    is_final = (scene_number == scene_count())
    
    act_desc = f"CLIMAX FINISH: {cfg['climax_act']}." if is_final else f"Runner advances along obstacle course toward {cfg['target_doll']} on {cfg['prop_stand']}."

    prompt = f"""
System Directive: Convert parameters into ONE concise English prompt (<80 words) for Flow AI.
{frame_context}
Style: {cfg['style']}, 9:16 vertical ratio. Map: {cfg['map_env']}. Camera: {cfg['camera']}.
Character: {cfg['runner']} vs {cfg['target_doll']}.
{obs} {maneuver}
ACTION: {act_desc}
OUTPUT FORMAT: Provide ONLY the final prompt text.
"""
    try:
        res = ask(prompt, parts=prompt_parts, json_mode=False)
        st.session_state.scene_prompts[scene_number] = res.strip()
        return True
    except Exception as exc:
        st.error(f"Gagal menyusun Prompt Scene {scene_number}: {exc}")
        return False
# ==========================================
# 4. UI PAGES RENDERING
# ==========================================
def render_sidebar():
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.caption(APP_VERSION)
        
        st.session_state.api_key = st.text_input("Gemini API Key", value=st.session_state.api_key, type="password")
        st.markdown("---")
        st.subheader("🧭 Navigasi Modul")
        
        if st.button("🏠 Setup Konfigurasi", use_container_width=True): go("home")
        if st.button("🗺️ Roadmap Analysis", use_container_width=True): go("analysis")
        if st.button("🎬 Scene Prompt Studio", use_container_width=True): go("scenes")
        if st.button("🚀 SEO & Metadata", use_container_width=True): go("seo")

        st.markdown("---")
        if st.button("🔄 Reset Project", type="secondary", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k != "authenticated": del st.session_state[k]
            st.rerun()

def render_home():
    st.title("🎬 Setup Engine Parameter")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.duration = st.selectbox("Durasi Video (Jml Scene)", list(DURATION_SCENES.keys()), index=4)
        st.session_state.visual_style = st.selectbox("Visual Style", STYLE_OPTIONS)
        st.session_state.selected_camera = st.selectbox("Camera Movement", CAMERA_OPTIONS)
        st.session_state.aspect_ratio = st.selectbox("Aspect Ratio", ASPECT_OPTIONS)
        
    with col2:
        st.session_state.runner_choice = st.selectbox("Karakter Utama (Runner)", RUNNER_PRESETS)
        if st.session_state.runner_choice == "10. Custom / Ketik Sendiri":
            st.session_state.custom_runner = st.text_input("Nama Karakter Custom:", value=st.session_state.custom_runner)
            
        st.session_state.target_doll_choice = st.selectbox("Karakter Target", TARGET_DOLL_PRESETS)
        st.session_state.target_idle_choice = st.selectbox("Gaya Idle Target", TARGET_IDLE_PRESETS)
        st.session_state.selected_map = st.selectbox("Arena / Map", MAP_OPTIONS)
        st.session_state.selected_prop_stand = st.selectbox("Dudukan Target", PROP_STAND_OPTIONS)
        st.session_state.selected_climax_action = st.selectbox("Klimaks Akhir", CLIMAX_ACTION_OPTIONS)

    st.markdown("---")
    if st.button("🚀 Mulai Analisis & Racik Roadmap", type="primary", use_container_width=True):
        run_analysis()

def render_analysis():
    st.title("🗺️ Roadmap Analysis & Storyboard")
    if not st.session_state.analysis:
        st.warning("Belum ada analisis. Silakan jalankan dari menu Setup.")
        if st.button("Kembali ke Setup"): go("home")
        return

    st.json(st.session_state.analysis)
    st.markdown("---")
    if st.button("🎬 Lanjut ke Scene Prompt Studio", type="primary", use_container_width=True):
        go("scenes")

def render_scenes():
    total_scenes = scene_count()
    st.title("🎬 Scene Prompt Studio")
    st.caption("Racik prompt presisi per adegan dengan dukungan continuity screenshot.")

    scene_options = [f"Scene {i}" for i in range(1, total_scenes + 1)]
    selected_scene_str = st.selectbox("Pilih Scene Yang Ingin Digenerate:", scene_options)
    sc_num = int(selected_scene_str.replace("Scene ", ""))

    st.markdown(f"### 📍 Mengedit & Generate Prompt: Scene {sc_num} dari {total_scenes}")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("🛠️ Modifier Scene")
        st.session_state.user_scene_obstacles[sc_num] = st.selectbox(
            f"⚡ Rintangan Khusus (Scene {sc_num})", 
            list(OBSTACLE_OPTIONS.keys()), index=0
        )
        st.session_state.user_scene_maneuvers[sc_num] = st.selectbox(
            f"🏃 Gerakan/Aksi Khusus (Scene {sc_num})", 
            MANEUVER_OPTIONS, index=0
        )

        if sc_num > 1:
            prev = sc_num - 1
            st.markdown(f"#### 🖼️ Screenshot Referensi Scene {prev} (Continuity)")
            uploaded_frame = st.file_uploader(f"Drop screenshot hasil render Scene {prev}:", type=["jpg", "png", "webp"], key=f"uploader_{sc_num}")
            if uploaded_frame:
                img_copy = Image.open(uploaded_frame).copy().convert("RGB")
                st.session_state.scene_frames[prev] = img_copy
                st.image(img_copy, caption=f"Frame Acuan Scene {prev}", width=250)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"✨ Generate Prompt Scene {sc_num}", type="primary", use_container_width=True):
            generate_scene_prompt(sc_num)

    with col2:
        st.subheader("📝 Hasil Prompt Flow AI")
        if sc_num in st.session_state.scene_prompts:
            st.success(f"Prompt Scene {sc_num} Berhasil Dibuat!")
            st.code(st.session_state.scene_prompts[sc_num], language="text")
        else:
            st.info("Klik tombol 'Generate Prompt' di samping untuk meracik prompt.")

        st.markdown("---")
        st.markdown("#### 📂 Ringkasan Prompt Semua Scene")
        for i in range(1, total_scenes + 1):
            if i in st.session_state.scene_prompts:
                with st.expander(f"Scene {i} Prompt"):
                    st.code(st.session_state.scene_prompts[i], language="text")

def render_seo():
    st.title("🚀 SEO & Metadata Generator")
    if not st.session_state.seo:
        cfg = get_active_config()
        with st.spinner("Meracik SEO Metadata..."):
            try:
                raw = ask(f"Buatkan JSON SEO TikTok/Shorts (judul_clickbait, hashtags, deskripsi). Karakter: {cfg['runner']}, Map: {cfg['map_env']}", json_mode=True)
                st.session_state.seo = extract_json(raw)
                st.rerun()
            except Exception as exc:
                st.error(f"Gagal generate SEO: {exc}")
                return

    st.json(st.session_state.seo)

# ==========================================
# 5. MAIN ROUTING & EXECUTION
# ==========================================
def main():
    if not check_password():
        st.stop()

    render_sidebar()

    page = st.session_state.get("page", "home")
    if page == "home": render_home()
    elif page == "analysis": render_analysis()
    elif page == "scenes": render_scenes()
    elif page == "seo": render_seo()

if __name__ == "__main__":
    main()
