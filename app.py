import json
import re
import time
import os

import streamlit as st
from google import genai
from google.genai import types

# ==========================================
# 1. KONFIGURASI HALAMAN & MODEL UTAMA
# ==========================================
st.set_page_config(
    page_title="UGC Remix Studio v10.4 — Storyboard & Flow AI",
    page_icon="🎬",
    layout="wide"
)

# Model resmi yang stabil dan tersedia
MODEL_NAME = "gemini-3.6-flash"


# ==========================================
# 2. DEFINISI OPSI & PRESET DATA
# ==========================================
STYLE_OPTIONS = [
    "GTA V Modded Gameplay Style",
    "3D Animated Game Graphics",
    "Unreal Engine 5 Parkour Render",
    "Sinematik Realistis 3D",
]

RUNNER_PRESETS = [
    "Minecraft Creeper Style (Karakter makhluk hijau kotak khas Minecraft)",
    "Pocong Gesit (Hantu lokal berbalut kain kafan putih melompat absurd & kencang)",
    "Bebek Karet Raksasa (Mainan bebek mandi kuning licin membal dengan kaki robotik)",
    "Karakter Roblox / Blocky Noob (Karakter balok ikonik gaya voxel yang pecah pas kena pukul)",
    "Sktetelons / Tengkorak Gila (Karakter kerangka tulang hidup dengan ragdoll physics mantap)",
    "Fat Orange Cat (Kucing oranye gemuk berjaket hoodie)",
    "Funny Green Frog (Katak hijau nyeleneh berkacamata hitam)",
    "Custom / Ketik Sendiri"
]

TARGET_DOLL_OPTIONS = [
    "Giant Yellow Rubber Ducks (Bebek karet kuning raksasa elastis)",
    "Wooden Cargo Barrels (Tong kayu kargo besar)",
    "Crash Test Dummies (Boneka uji tabrak manekin kuning-hitam ikonik)",
    "Giant Teddy Bears (Boneka beruang cokelat empuk dengan bulu halus)",
    "Custom / Ketik Sendiri"
]

IDLE_MOTION_OPTIONS = [
    "Subtle Breathing & Wind Swaying (Bergoyang lembut tertiup angin & bernapas pasif)",
    "Anxious Trembling / Scared Wobble (Bergetar ketakutan oleng di atas pijakan)",
    "Frozen Stiff Stance (Diam kaku total sampai benturan fisik terjadi)",
    "Custom / Ketik Sendiri"
]

MAP_OPTIONS = [
    "Sky-High Cloud Ramp (Floating Infinite Cloud Void / Trek Blok Melayang di Awan)",
    "Maze Bank Tower Rooftop (Downtown Los Santos Skyscraper)",
    "Mount Chiliad Mega Ramp & Ridge (High Mountain Canyon)",
    "Pacific Ocean Docks & Shipping Containers (Sea Port)",
    "Neon City Cyberpunk Night (Glow Los Santos Nightlife)",
]

PROP_STAND_OPTIONS = [
    "Direct Concrete Rooftop / Solid Block Track",
    "Giant Yoga / Exercise Fitness Balls (Colored Balls)",
    "Wooden Cargo Barrels & Metal Oil Drums",
    "Floating Pool Inflatable Donuts",
]

CLIMAX_ACTION_OPTIONS = [
    "Auto (Ikuti Draft Storyboard)",
    "Epic Jump into Finish Portal",
    "Double Hit Combo + Sacrifice Fall",
    "Massive Obstacle Rain & Narrow Escape",
]

ASPECT_OPTIONS = ["9:16 — Shorts / Reels / TikTok", "16:9 — YouTube Long", "1:1 — Kotak"]


# ==========================================
# 3. INISIALISASI SESSION STATE
# ==========================================
DEFAULTS = {
    "page": "home",
    "api_key": "",
    "input_mode": "Referensi Video",
    "manual_scene_count": 10,
    "reference_file": None,
    "reference_text": "",
    "visual_style": STYLE_OPTIONS[0],
    "runner_choice": RUNNER_PRESETS[0],
    "custom_runner": "",
    "target_doll_choice": TARGET_DOLL_OPTIONS[0],
    "custom_target_doll": "",
    "idle_motion_choice": IDLE_MOTION_OPTIONS[0],
    "custom_idle_motion": "",
    "map_choice": MAP_OPTIONS[0],
    "prop_stand_choice": PROP_STAND_OPTIONS[0],
    "climax_action_choice": CLIMAX_ACTION_OPTIONS[0],
    "aspect_ratio": ASPECT_OPTIONS[0],
    "custom_instruction": "",
    "analysis": {},
    "storyboard_text": "",
    "entity_mapping": {},
    "scene_prompts": {},
    "scene_frames": {},
    "current_scene": 1,
    "detected_scenes": 0,
    "seo": {},
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================
# 4. FUNGSI UTILITAS & API GEMINI
# ==========================================
def go(page: str):
    st.session_state.page = page
    st.rerun()

def reset_remix_state():
    st.session_state.analysis = {}
    st.session_state.storyboard_text = ""
    st.session_state.entity_mapping = {}
    st.session_state.scene_prompts = {}
    st.session_state.scene_frames = {}
    st.session_state.current_scene = 1
    st.session_state.detected_scenes = 0
    st.session_state.seo = {}

def get_client():
    key = (os.getenv("GEMINI_API_KEY") or st.session_state.get("api_key", "")).strip()
    key = key.strip("`\"' \n\r\t")
    if not key:
        st.error("Masukkan Gemini API Key terlebih dahulu di Sidebar.")
        return None
    try:
        return genai.Client(api_key=key)
    except Exception as exc:
        st.error(f"Gagal koneksi Gemini API: {exc}")
        return None

def extract_json(text: str):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*
# ==========================================
# 4. FUNGSI UTILITAS & API GEMINI
# ==========================================
def go(page: str):
    st.session_state.page = page
    st.rerun()

def reset_remix_state():
    st.session_state.analysis = {}
    st.session_state.storyboard_text = ""
    st.session_state.entity_mapping = {}
    st.session_state.scene_prompts = {}
    st.session_state.scene_frames = {}
    st.session_state.current_scene = 1
    st.session_state.detected_scenes = 0
    st.session_state.seo = {}

def get_client():
    key = (os.getenv("GEMINI_API_KEY") or st.session_state.get("api_key", "")).strip()
    key = key.strip("`\"' \n\r\t")
    if not key:
        st.error("Masukkan Gemini API Key terlebih dahulu di Sidebar.")
        return None
    try:
        return genai.Client(api_key=key)
    except Exception as exc:
        st.error(f"Gagal koneksi Gemini API: {exc}")
        return None

def extract_json(text: str):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass
    starts = [p for p in (text.find("{"), text.find("[")) if p >= 0]
    if not starts:
        raise ValueError("Respons AI tidak berisi JSON yang valid.")
    start = min(starts)
    for end in range(len(text), start, -1):
        try:
            return json.loads(text[start:end].strip())
        except Exception:
            continue
    raise ValueError("Respons AI tidak dapat diparse sebagai JSON.")

def ask(client, prompt: str, parts=None, json_mode: bool = False) -> str:
    media_parts = list(parts or [])
    content_parts = media_parts + [types.Part.from_text(text=prompt)]
    contents = [types.Content(role="user", parts=content_parts)]

    config_kwargs = {"temperature": 0.2}
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            text = getattr(response, "text", None)
            if not text:
                raise RuntimeError("Gemini mengembalikan respons kosong.")
            return text
        except Exception as exc:
            if attempt == 2:
                raise RuntimeError(f"503 UNAVAILABLE atau Gagal terhubung ke Gemini: {exc}")
            time.sleep(1.5)


# ==========================================
# 5. CORE LOGIC (STORYBOARD, PROMPT, & SEO)
# ==========================================
def generate_draft_storyboard():
    reset_remix_state()
    client = get_client()
    if not client:
        return

    parts = []
    mode = st.session_state.input_mode

    # Setup mode (Referensi Video vs Manual)
    if mode == "Referensi Video":
        ref_file = st.session_state.get("ref_file_input")
        if ref_file is not None:
            try:
                data = ref_file.getvalue()
                mime = getattr(ref_file, "type", "video/mp4") or "video/mp4"
                parts.append(types.Part.from_bytes(data=data, mime_type=mime))
            except Exception as exc:
                st.warning(f"Gagal membaca video referensi: {exc}")
        if st.session_state.reference_text.strip():
            parts.append(types.Part.from_text(text=st.session_state.reference_text))
        
        target_calc = "1. AI WAJIB membaca DURASI ASLI video referensi dan tentukan jumlah scene (tiap scene 8 detik)."
    else:
        target_calc = f"1. Buat tepat {st.session_state.manual_scene_count} Scene (tiap scene 8 detik) dengan alur yang dinamis (Action Setup -> Escalation -> Climax)."
        if st.session_state.reference_text.strip():
            parts.append(types.Part.from_text(text=f"Skenario manual user: {st.session_state.reference_text}"))

    chosen_runner = st.session_state.custom_runner if st.session_state.runner_choice == "Custom / Ketik Sendiri" else st.session_state.runner_choice
    chosen_target = st.session_state.custom_target_doll if st.session_state.target_doll_choice == "Custom / Ketik Sendiri" else st.session_state.target_doll_choice

    prompt = f"""
Anda adalah AI Master Creative Director.
TUGAS: Buat Master Plan Storyboard untuk AI Video Generator (Flow AI).

{target_calc}

DATA MASTER (WAJIB DIPAKAI):
- Runner Utama: "{chosen_runner}"
- Rintangan/Target: "{chosen_target}"
- Lingkungan/Arena: "{st.session_state.map_choice}"
- Pijakan Trek: "{st.session_state.prop_stand_choice}"

ATURAN ALUR (NARRATIVE ARC):
- Scene 1 harus Setup (Karakter mulai berlari, establish environment).
- Scene Pertengahan harus bervariasi kameranya (Third Person, Side-Scrolling, Low Angle) dan rintangan makin intens.
- Scene Terakhir harus Climax.

HASILKAN JSON FORMAT BERIKUT (Dilarang ada entitas dari video asli, pakai Data Master!):
{{
  "calculated_scene_count": [ANGKA INT],
  "entity_mapping": {{
    "runner_remix": "{chosen_runner}",
    "target_remix": "{chosen_target}",
    "arena_remix": "{st.session_state.map_choice}"
  }},
  "storyboard_draft_text": "Tulis rencana lengkap Scene 1 sampai akhir di sini dengan format:\nScene 1: [Deskripsi Action & Kamera]\nScene 2: [Deskripsi Action & Kamera] dst. (Buat per baris agar rapi)"
}}
"""
    with st.spinner("Membuat Draft Master Storyboard & Angle Kamera..."):
        try:
            raw = ask(client, prompt, parts, json_mode=True)
            data = extract_json(raw)
            
            st.session_state.analysis = data
            st.session_state.detected_scenes = int(data.get("calculated_scene_count", st.session_state.manual_scene_count))
            st.session_state.entity_mapping = data.get("entity_mapping", {})
            st.session_state.storyboard_text = data.get("storyboard_draft_text", "")
            
            go("analysis")
        except Exception as exc:
            st.error(f"Gagal membuat draft: {exc}")

def generate_scene_prompt(scene_number: int, custom_tweak: str = ""):
    client = get_client()
    if not client:
        return False

    analysis = st.session_state.analysis
    total_scenes = st.session_state.detected_scenes
    
    chosen_runner = analysis.get('entity_mapping', {}).get('runner_remix', st.session_state.runner_choice)
    chosen_target = analysis.get('entity_mapping', {}).get('target_remix', st.session_state.target_doll_choice)
    chosen_arena = analysis.get('entity_mapping', {}).get('arena_remix', st.session_state.map_choice)

    # Dapatkan deskripsi spesifik scene ini dari storyboard yang sudah di-ACC
    storyboard_lines = st.session_state.storyboard_text.split('\n')
    scene_focus = f"Action for scene {scene_number}"
    for line in storyboard_lines:
        if line.lower().startswith(f"scene {scene_number}:") or line.lower().startswith(f"scene {scene_number} "):
            scene_focus = line
            break

    parts_list = []
    
    # Logika T2V vs I2V
    if scene_number == 1:
        mode_type = "T2V (Text-to-Video)"
        continuity_rule = f"[ENVIRONMENT & SETUP]: Set in {chosen_arena} with {st.session_state.prop_stand_choice}. Highly detailed establishing shot."
    else:
        mode_type = "I2V (Image-to-Video)"
        continuity_rule = "[SEAMLESS CONTINUATION]: DO NOT describe the environment from scratch. Use the exact background, lighting, and character appearance from the provided reference image. Focus ONLY on the continuing motion."
        
        # Ambil gambar frame sebelumnya dari Session State
        prev_scene_num = scene_number - 1
        if prev_scene_num in st.session_state.scene_frames and st.session_state.scene_frames[prev_scene_num]:
            frame_data = st.session_state.scene_frames[prev_scene_num]
            parts_list.append(types.Part.from_bytes(data=frame_data["bytes"], mime_type=frame_data["mime"]))
        else:
            return "ERROR_NO_FRAME"

    tweak_instruction = f"\n[USER TWEAK REQUEST]: {custom_tweak}" if custom_tweak else ""

    prompt = f"""
Write ONE ultra-detailed AI video generation prompt in ENGLISH for Google Flow AI / Veo.
Scene {scene_number} of {total_scenes}. Mode: {mode_type}.

FORMATTING RULE: Output EXACTLY in this categorized format without any other intro text.

[ACTION & CAMERA]: (Based on this storyboard: {scene_focus}. Keep camera dynamic).
{continuity_rule}
[PHYSICS LOCK - CRITICAL]: (The runner, {chosen_runner}, is running forward. THE RUNNER MUST REMAIN FIRMLY GROUNDED AND ATTACHED TO THE SOLID TRACK. Even if obstacles like {chosen_target} are falling or flying around, the track does NOT fall, and the runner does NOT fall).
[VISUAL STYLE]: ({st.session_state.visual_style}, {st.session_state.aspect_ratio}, high motion blur).
{tweak_instruction}
"""
    with st.spinner(f"Merakit Prompt Terstruktur Scene {scene_number} ({mode_type})..."):
        try:
            res_prompt = ask(client, prompt, parts=parts_list, json_mode=False)
            st.session_state.scene_prompts[scene_number] = res_prompt.strip()
            return "SUCCESS"
        except Exception as exc:
            return "ERROR_API"

def generate_seo_metadata():
    client = get_client()
    if not client:
        return False

    prompt = f"""
    Anda adalah Pakar SEO YouTube dan TikTok.
    Buatkan metadata viral untuk video AI yang baru saja dibuat.
    
    Data Video:
    - Karakter: {st.session_state.runner_choice}
    - Rintangan: {st.session_state.target_doll_choice}
    - Tema: {st.session_state.map_choice}
    - Total Durasi: {st.session_state.detected_scenes * 8} Detik
    - Alur Cerita: {st.session_state.storyboard_text}
    
    Hasilkan output dalam format JSON yang valid:
    {{
      "youtube_title": "Judul clickbait tapi relevan untuk YouTube",
      "tiktok_caption": "Caption pendek viral untuk TikTok/Reels dengan hashtag",
      "description": "Deskripsi YouTube 2 paragraf yang SEO friendly",
      "tags": "tag1, tag2, tag3, tag4, tag5, dst"
    }}
    """
    with st.spinner("Meracik Metadata SEO Viral..."):
        try:
            raw = ask(client, prompt, json_mode=True)
            st.session_state.seo = extract_json(raw)
            return True
        except Exception as exc:
            st.error(f"Gagal membuat SEO: {exc}")
            return False


# ==========================================
# 6. RENDER ANTARMUKA HALAMAN (VIEWS)
# ==========================================
def render_home():
# ==========================================
# 6. RENDER ANTARMUKA HALAMAN (VIEWS)
# ==========================================
def render_home():
    st.title("🎬 UGC Remix Studio v10.4 — Director's Desk")
    st.caption("Setup Master Data sebelum membuat Storyboard Video.")

    st.subheader("1. Pilih Mode Pembuatan")
    mode = st.radio("Jalur Produksi:", ["Referensi Video", "Manual (Tanpa Video)"], key="input_mode", horizontal=True)

    if mode == "Referensi Video":
        st.file_uploader("Upload Video Referensi (Shorts / Video Panjang)", type=["mp4", "mov", "webm"], key="ref_file_input")
        st.text_area("Instruksi Tambahan (Opsional)", key="reference_text", height=70)
    else:
        st.slider("Jumlah Scene yang Diinginkan (1 Scene = 8 Detik):", min_value=1, max_value=20, value=10, key="manual_scene_count")
        st.text_area("Ceritakan detail skenario / rintangan (Opsional):", key="reference_text", height=70)

    st.subheader("2. Setup Master Data (Global State)")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Pilih Karakter Utama (Runner):", RUNNER_PRESETS, key="runner_choice")
        if st.session_state.runner_choice == "Custom / Ketik Sendiri":
            st.text_input("Tulis Deskripsi Karakter Custom Kamu:", key="custom_runner")
            
        st.selectbox("Rintangan / Target Jatuh:", TARGET_DOLL_OPTIONS, key="target_doll_choice")
        if st.session_state.target_doll_choice == "Custom / Ketik Sendiri":
            st.text_input("Tulis Deskripsi Target Custom Kamu:", key="custom_target_doll")
            
    with col2:
        st.selectbox("Latar Lingkungan (Environment):", MAP_OPTIONS, key="map_choice")
        st.selectbox("Pijakan / Trek Jalan:", PROP_STAND_OPTIONS, key="prop_stand_choice")
        st.selectbox("Gaya Visual Render:", STYLE_OPTIONS, key="visual_style")
        st.selectbox("Rasio Aspek Video:", ASPECT_OPTIONS, key="aspect_ratio")

    st.markdown("---")
    st.button("🪄 BUAT DRAFT STORYBOARD SEKARANG", type="primary", use_container_width=True, on_click=generate_draft_storyboard)


def render_analysis():
    st.title("📋 Director's Table: ACC Storyboard")
    
    if not st.session_state.get("storyboard_text"):
        st.info("Silakan buat draft storyboard di Beranda terlebih dahulu.")
        return

    st.success(f"⏱️ AI Mengusulkan **{st.session_state.detected_scenes} Scene** (Total ~{st.session_state.detected_scenes * 8} Detik).")

    st.subheader("Grand Plan (Rencana Alur Video)")
    st.markdown("*Baca draft di bawah ini. Anda bisa mengubah teksnya secara manual jika angle kamera atau aksinya kurang pas sebelum masuk ke Studio.*")
    
    # Text area ini bisa diedit oleh user
    edited_storyboard = st.text_area(
        "Edit Storyboard Anda di sini:",
        value=st.session_state.storyboard_text,
        height=300
    )

    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Kembali Edit Master Data"):
            go("home")
    with col2:
        if st.button("✅ ACC STORYBOARD & MASUK STUDIO 🎬", type="primary", use_container_width=True):
            st.session_state.storyboard_text = edited_storyboard
            go("scenes")


def render_scenes():
    st.title("🎥 Production Studio (Scene Generator)")
    n = st.session_state.detected_scenes
    current = st.session_state.current_scene

    if n == 0:
        st.info("Kembali ke Beranda untuk membuat Storyboard terlebih dahulu.")
        return

    st.subheader(f"Adegan {current} dari {n}")

    # Info/Peringatan Mode
    if current == 1:
        st.info("🔥 **MODE: T2V (Text-to-Video)**\nCopy teks ini ke Flow AI **TANPA** memasukkan gambar apa pun. Biarkan AI membangun dunia pertamanya.")
    else:
        st.warning(f"🖼️ **MODE: I2V (Image-to-Video)**\nUpload screenshot Last Frame Scene {current-1} ke Flow AI, lalu copy paste teks ini sebagai prompt.")

    # Gatekeeper: Cek apakah user udah upload gambar dari scene sebelumnya
    if current > 1 and current - 1 not in st.session_state.scene_frames:
        st.error(f"🛑 STOP! Upload Gambar Last Frame dari Scene {current-1} di bawah untuk membuka gembok Scene ini.")
        if st.button("← Kembali ke Scene Sebelumnya", type="primary"):
            st.session_state.current_scene -= 1
            st.rerun()
        return

    # Generate Prompt dengan Error Handling 503
    if current not in st.session_state.scene_prompts:
        with st.spinner(f"Meracik Prompt AI (Physics Grounded) untuk Scene {current}..."):
            status = generate_scene_prompt(current)
            if status == "SUCCESS":
                st.rerun()
            elif status == "ERROR_NO_FRAME":
                st.error("Frame scene sebelumnya tidak ditemukan.")
                return
            else:
                st.error("Server Gemini sedang sibuk (503 Overload) atau mengalami kendala jaringan.")
                if st.button("🔄 Coba Generate Ulang Prompt Ini", type="primary"):
                    st.rerun()
                return

    # Tampilkan Prompt jika berhasil
    if current in st.session_state.scene_prompts:
        st.text_area(f"Salin Prompt Scene {current}:", value=st.session_state.scene_prompts[current], height=200)

        with st.expander("🔄 Kurang pas? Re-roll Prompt Scene Ini"):
            tweak_val = st.text_input("Ketik revisi (Misal: 'Buat kameranya dari bawah')", key=f"tweak_{current}")
            if st.button("Apply Tweak & Regenerate", key=f"btn_tweak_{current}"):
                generate_scene_prompt(current, custom_tweak=tweak_val)
                st.rerun()

        st.markdown("---")
        
        # Uploader (Gatekeeper) untuk persiapan scene selanjutnya
        if current < n:
            st.subheader(f"🖼️ Gatekeeper: Kunci Continuity (Upload Last Frame Scene {current})")
            st.caption("Setelah Anda render video di Flow AI, screenshot frame paling akhir, dan upload ke sini untuk membuka Scene selanjutnya.")
            
            uploaded_frame = st.file_uploader(f"Upload Image (PNG/JPG)", type=["png", "jpg", "jpeg"], key=f"frame_upload_{current}")
            if uploaded_frame:
                st.session_state.scene_frames[current] = {
                    "bytes": uploaded_frame.getvalue(),
                    "mime": getattr(uploaded_frame, "type", "image/png") or "image/png"
                }
                st.image(uploaded_frame, caption=f"Posisi Terkunci! Siap untuk Scene {current+1}", width=250)
            elif current in st.session_state.scene_frames:
                st.success("Frame Continuity sudah diamankan di memori aplikasi.")
        
        st.markdown("---")
        
        # Navigasi Bawah
        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if current > 1 and st.button("← Adegan Sebelumnya"):
                st.session_state.current_scene -= 1
                st.rerun()
        with col_nav2:
            if current < n:
                is_disabled = (current not in st.session_state.scene_frames)
                if st.button("Adegan Berikutnya →", type="primary", disabled=is_disabled):
                    st.session_state.current_scene += 1
                    st.rerun()
            elif current == n:
                st.success("🏁 Seluruh Blueprint Scene Selesai Dieksekusi! Video Anda siap digabung.")
                st.markdown("---")
                
                # BAGIAN POST-PRODUCTION & SEO
                st.subheader("🚀 Post-Production: Paket SEO Metadata")
                st.caption("Generate Judul, Deskripsi, dan Hashtag viral untuk video ini sebelum di-upload ke YouTube/TikTok.")
                
                if st.button("Generate SEO Viral 🪄", type="primary"):
                    generate_seo_metadata()
                    
                if st.session_state.seo:
                    seo = st.session_state.seo
                    st.text_input("📌 Judul YouTube:", value=seo.get("youtube_title", ""))
                    st.text_area("📱 Caption TikTok / Shorts:", value=seo.get("tiktok_caption", ""), height=100)
                    st.text_area("📝 Deskripsi Video:", value=seo.get("description", ""), height=150)
                    st.text_area("🏷️ Tags / Keywords:", value=seo.get("tags", ""), height=80)


# ==========================================
# 7. SIDEBAR CONTROLS & MAIN ROUTER
# ==========================================
with st.sidebar:
    st.title("⚙️ Studio Controls")
    st.text_input("Gemini API Key", key="api_key", type="password")
    st.markdown("---")
    st.markdown("**Navigasi Alur Studio:**")
    if st.button("1. 🏠 Director's Desk (Setup)", use_container_width=True):
        go("home")
    if st.button("2. 📋 ACC Storyboard", use_container_width=True):
        go("analysis")
    if st.button("3. 🎥 Production Studio", use_container_width=True):
        go("scenes")

# Routing Halaman Aktif
page = st.session_state.page
if page == "home":
    render_home()
elif page == "analysis":
    render_analysis()
elif page == "scenes":
    render_scenes()
