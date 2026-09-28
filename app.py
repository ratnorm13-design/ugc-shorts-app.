import json
import re
import os
import logging
import streamlit as st
from google import genai
from google.genai import types

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# ==========================================
# 0. KELAS ARSITEKTUR KONTINUITAS (RAG PIPELINE)
# ==========================================
class GlobalStoryboardManager:
    """Mengelola Peta Spasial dan Skenario Induk agar AI tidak amnesia antar scene."""
    def __init__(self, state_file_path="storyboard_state.json"):
        self.state_file_path = state_file_path
        self.storyboard_state = {
            "global_camera_lock": "(Static interior dashcam POV, fixed wide angle, zero camera movement:1.5)",
            "environment": "Car interior, daytime, blurred motion outside windows",
            "spatial_map": {}, 
            "scene_flow": []   
        }
        self.load_state()

    def load_state(self):
        try:
            with open(self.state_file_path, 'r') as f:
                self.storyboard_state = json.load(f)
            logging.info("Skenario Induk di-load.")
        except FileNotFoundError:
            logging.info("Membuat Skenario Induk baru...")

    def save_state(self):
        with open(self.state_file_path, 'w') as f:
            json.dump(self.storyboard_state, f, indent=4)

    def set_master_data(self, data):
        """Menyimpan hasil analisis pertama dari Gemini ke dalam state spasial."""
        self.storyboard_state["environment"] = data.get("environment", self.storyboard_state["environment"])
        self.storyboard_state["global_camera_lock"] = data.get("global_camera_lock", self.storyboard_state["global_camera_lock"])
        self.storyboard_state["spatial_map"] = data.get("spatial_map", {})
        self.storyboard_state["scene_flow"] = data.get("scene_flow", [])
        self.save_state()

    def inject_custom_subject(self, custom_instructions):
        """Memodifikasi deskripsi objek berdasarkan instruksi user tanpa mengubah kordinat."""
        if not custom_instructions: return
        # Ini disederhanakan: Idealnya kita minta Gemini parse instruksi ini ke ID subjek,
        # Namun di sini kita simpan instruksi global untuk ditambahkan ke prompt builder
        self.storyboard_state["custom_overrides"] = custom_instructions
        self.save_state()

class FlowAIPromptGenerator:
    """Merakit Prompt dengan syntax khusus Flow AI (Segmented + Weighting)."""
    def __init__(self, storyboard_state):
        self.storyboard = storyboard_state
        self.negative_prompt = (
            "(morphing subjects, changing seats, changing camera angle, "
            "teleporting subjects, camera panning, zooming, character swap, "
            "inconsistent clothing, bad anatomy, missing limbs:1.8)"
        )

    def generate_scene_prompt(self, scene_id, aspect_ratio, art_style, previous_frame_locked=False):
        current_scene = next((s for s in self.storyboard["scene_flow"] if str(s["scene_id"]) == str(scene_id)), None)
        if not current_scene:
            return "Error: Scene data missing.", ""

        prompt_parts = []
        # Setup Meta
        prompt_parts.append(f"**[ASPECT RATIO]**: {aspect_ratio}")
        prompt_parts.append(f"**[ART STYLE]**: {art_style}")
        prompt_parts.append(f"**[CAMERA & SHOT]**: {self.storyboard.get('global_camera_lock')}")
        prompt_parts.append(f"**[SETTING]**: {self.storyboard.get('environment')} | Action: {current_scene.get('global_action', '')}")
        
        if previous_frame_locked:
            prompt_parts.append("**[CONTINUITY LOCK]**: (Image-to-Video mode). STRICT 1:1 MATCH with starting frame. DO NOT MOVE SUBJECT POSITIONS.")

        # Overrides dari kustomisasi user (Fase 2)
        custom_override = self.storyboard.get("custom_overrides", "")
        if custom_override:
            prompt_parts.append(f"**[CHARACTER OVERRIDES]**: {custom_override} (Maintain original seat positions!).")

        # Rangkai Subjek berdasarkan Peta Spasial (Posisi Terkunci)
        for subj_id, subj_data in self.storyboard.get("spatial_map", {}).items():
            desc = subj_data.get("description", "")
            pos = subj_data.get("position", "")
            action = current_scene.get("subject_actions", {}).get(subj_id, subj_data.get("action_baseline", ""))
            prompt_parts.append(f"**{pos}**: ({desc}:1.2). Action: {action}.")

        return "\n".join(prompt_parts), self.negative_prompt

# ==========================================
# 1. KONFIGURASI HALAMAN & GLOBAL VARIABEL
# ==========================================
st.set_page_config(
    page_title="Si Kumis IP Studio - Enhanced RAG",
    page_icon="🕶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

AVAILABLE_MODELS = {
    "Gemini 3.8 Flash (Terbaru & Paling Cerdas)": "gemini-3.8-flash",
    "Gemini 3.7 Flash (Stabil & Cepat)": "gemini-3.7-flash",
    "Gemini 3.6 Flash (Versi Klasik/Alternatif)": "gemini-3.6-flash"
}

ASPECT_RATIOS = ["9:16 — TikTok / Reels / Shorts", "16:9 — YouTube Long Form", "1:1 — Square / Feeds"]
ART_STYLES = [
    "Photorealistic / Ultra-Realistic (4K, real life footage)",
    "Studio Ghibli (Classic 2D animation)",
    "3D Animation (Pixar style)",
    "Cinematic Film (Dramatic lighting, anamorphic bokeh)",
    "CCTV / Dashcam Footage (Security angle)"
]

# Init Storyboard Manager
storyboard_manager = GlobalStoryboardManager()

def init_state():
    defaults = {
        "page": "home",
        "api_key": "",
        "selected_model_label": list(AVAILABLE_MODELS.keys())[0],
        "aspect_ratio": ASPECT_RATIOS[0],
        "art_style": ART_STYLES[0],
        "custom_subjects": "", 
        "analysis_data": {},
        "scene_frames": {},
        "current_scene": 1,
        "total_scenes": 0,
        "seo_package": {},
        "is_completed": False
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()

def navigate_to(page_name: str):
    st.session_state.page = page_name
    st.rerun()

def get_gemini_client_and_model():
    raw_key = (os.getenv("GEMINI_API_KEY") or st.session_state.get("api_key", "")).strip("`\"' \n\r\t")
    if not raw_key:
        st.error("Silakan masukkan Gemini API Key pada Sidebar terlebih dahulu.")
        return None, None
    try:
        return genai.Client(api_key=raw_key), AVAILABLE_MODELS.get(st.session_state.selected_model_label, "gemini-3.8-flash")
    except Exception as err:
        st.error(f"Koneksi ke Gemini API gagal: {err}")
        return None, None

def parse_json_safely(text_response: str):
    clean_text = re.sub(r"^```(?:json)?\s*", "", text_response.strip(), flags=re.I)
    clean_text = re.sub(r"\s*```$", "", clean_text)
    try: return json.loads(clean_text)
    except Exception:
        start_pos = clean_text.find("{")
        end_pos = clean_text.rfind("}") + 1
        if start_pos != -1 and end_pos > start_pos:
            return json.loads(clean_text[start_pos:end_pos])
        raise ValueError("Gagal membaca struktur data JSON dari respons AI.")

# ==========================================
# 2. CORE LOGIC DENGAN PENGUNCIAN SUBJEK ABSOLUT
# ==========================================
def run_viral_adaptation():
    client, model_name = get_gemini_client_and_model()
    if not client: return

    file_upload = st.session_state.get("viral_video_file")
    if not file_upload:
        st.error("Silakan upload file video referensi terlebih dahulu.")
        return

    media_payload = [types.Part.from_bytes(data=file_upload.getvalue(), mime_type=file_upload.type or "video/mp4")]

    sys_instruction = """
TUGAS UTAMA: Analisis video referensi dan buat SPATIAL MAP (Peta Koordinat) absolut untuk mencegah subjek hilang/berpindah tempat di AI Video Generator.

ATURAN:
1. Identifikasi jumlah scene.
2. Buat "spatial_map" berisi semua subjek (kucing, anjing, orang, objek). Kunci posisi mereka dengan bracket, contoh: [DRIVER SEAT - FOREGROUND LEFT].
3. Modifikasi subjek utama menjadi "Si Kumis" (White cat, black mustache fur mark, black head patch).
4. Buat alur "scene_flow", jabarkan aksi fisik masing-masing subjek per scene, terutama saat momen inersia (mengerem, menabrak, dll).
5. Kamera WAJIB statis (Dashcam angle).

OUTPUT JSON WAJIB:
{
  "total_scenes": 2,
  "environment": "Car interior, moving road outside",
  "global_camera_lock": "(Static interior dashcam POV, fixed wide angle, zero camera movement:1.5)",
  "spatial_map": {
    "subject_1": {"description": "Photorealistic white cat with black mustache patch", "position": "[DRIVER SEAT - FOREGROUND LEFT]", "action_baseline": "Driving holding steering wheel"},
    "subject_2": {"description": "Orange cat", "position": "[PASSENGER SEAT - FOREGROUND RIGHT]", "action_baseline": "Sitting still"}
  },
  "scene_flow": [
    {
      "scene_id": 1,
      "global_action": "Driving calmly",
      "subject_actions": {"subject_1": "Focusing on road", "subject_2": "Looking around relaxed"}
    },
    {
      "scene_id": 2,
      "global_action": "Sudden hard braking",
      "subject_actions": {"subject_1": "Slamming brakes, eyes wide open in extreme shock", "subject_2": "Flying forward dramatically due to inertia, mouth open screaming"}
    }
  ]
}
"""
    with st.spinner("Membangun Global Storyboard & Spatial Map..."):
        try:
            res = client.models.generate_content(
                model=model_name,
                contents=[types.Content(role="user", parts=media_payload + [types.Part.from_text(text=sys_instruction)])],
                config=types.GenerateContentConfig(temperature=0.2, response_mime_type="application/json")
            )
            data = parse_json_safely(res.text)
            
            # SIMPAN KE DATABASE LOKAL (Memori AI)
            storyboard_manager.set_master_data(data)
            storyboard_manager.inject_custom_subject(st.session_state.get("custom_subjects", ""))
            
            st.session_state.update({
                "analysis_data": data,
                "total_scenes": int(data.get("total_scenes", 1)),
                "current_scene": 1,
                "scene_frames": {},
                "seo_package": {},
                "is_completed": False
            })
            navigate_to("analysis")
        except Exception as err:
            st.error(f"Terjadi kesalahan saat pemrosesan AI: {err}")

def build_viral_seo():
    client, model_name = get_gemini_client_and_model()
    if not client: return False
    
    # SEO menggunakan memori storyboard yang solid
    sys_seo = f"""
Buatkan Paket SEO Komplit untuk video komedi 'Si Kumis' berdasarkan storyboard berikut:
{json.dumps(storyboard_manager.storyboard_state)}

OUTPUT JSON WAJIB:
{{ "title": "Judul clickbait", "caption": "Caption TikTok + Hashtags", "description": "Deskripsi SEO", "tags": "tag1, tag2" }}
"""
    with st.spinner("Meracik Algoritma SEO..."):
        try:
            res = client.models.generate_content(
                model=model_name, contents=sys_seo,
                config=types.GenerateContentConfig(temperature=0.3, response_mime_type="application/json")
            )
            st.session_state.seo_package = parse_json_safely(res.text)
            return True
        except Exception as err:
            st.error(f"Gagal membuat paket SEO: {err}")
            return False

# ==========================================
# 3. TAMPILAN ANTARMUKA (UI VIEWS)
# ==========================================
def view_home():
    st.title("🕶️ Si Kumis IP Studio - Flow AI Optimized")
    st.caption("Peta Spasial Absolut & Kontinuitas Objek (RAG Pipeline)")
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Upload Referensi (Hook Physics)")
        st.file_uploader("Video/Image Referensi (MP4/JPG)", type=["mp4", "mov", "webm", "jpg", "png"], key="viral_video_file")
        st.info("💡 Sistem akan mengunci titik kordinat (Spatial Map) tiap subjek dari file ini.")

    with col2:
        st.subheader("2. Setting Parameter")
        st.selectbox("Model Gemini", list(AVAILABLE_MODELS.keys()), key="selected_model_label")
        st.selectbox("Aspect Ratio", ASPECT_RATIOS, key="aspect_ratio")
        st.selectbox("Art Style", ART_STYLES, key="art_style")
        st.text_area("Kustomisasi Subjek (Fase 2)", placeholder="Cth: Ubah Subject 2 jadi Anjing Bulldog berjaket. (Sistem akan mempertahankan posisinya saat ngerem)", key="custom_subjects")

    st.markdown("---")
    st.button("🚀 EKSTRAK & KUNCI SPATIAL MAP", type="primary", use_container_width=True, on_click=run_viral_adaptation)

def view_analysis():
    state = storyboard_manager.storyboard_state
    st.title("📋 Master Storyboard & Peta Spasial")
    st.markdown("---")
    st.success(f"**Camera Anchor:** {state.get('global_camera_lock')}")
    
    st.markdown("### 📍 Posisi Objek Terkunci (Spatial Map)")
    for s_id, s_data in state.get("spatial_map", {}).items():
        st.info(f"**{s_id.upper()}** letak di `{s_data.get('position')}`\n- Visual: {s_data.get('description')}")
        
    st.markdown("### 🎬 Alur Emosi & Fisika")
    for scene in state.get("scene_flow", []):
        st.warning(f"**Scene {scene['scene_id']} - {scene['global_action']}**")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Batal / Ulangi"): navigate_to("home")
    with col2:
        if st.button("✅ LANJUT KE STUDIO PRODUKSI", type="primary", use_container_width=True): navigate_to("scenes")

def view_scenes():
    curr = st.session_state.current_scene
    total = st.session_state.total_scenes
    if total == 0: return navigate_to("home")

    st.title(f"🎥 Studio Produksi — Scene {curr} / {total}")
    st.markdown("---")

    prev_locked = curr > 1
    if prev_locked and (curr - 1) not in st.session_state.scene_frames:
        st.error(f"🛑 **GEMBOK KONTINUITAS AKTIF:** Wajib upload Last Frame dari Scene {curr-1} sebagai referensi Image-to-Video di Flow AI.")
        if st.button(f"← Kembali ke Scene {curr-1}"):
            st.session_state.current_scene -= 1
            st.rerun()
        return

    # MENGGUNAKAN FLOW AI PROMPT GENERATOR
    prompt_builder = FlowAIPromptGenerator(storyboard_manager.storyboard_state)
    ratio_clean = st.session_state.aspect_ratio.split("—")[0].strip()
    style_clean = st.session_state.art_style.split("(")[0].strip()
    
    pos_prompt, neg_prompt = prompt_builder.generate_scene_prompt(curr, ratio_clean, style_clean, prev_locked)

    st.success(f"**COPY PROMPT INI KE FLOW AI / KLING UNTUK SCENE {curr}:**")
    st.text_area("POSITIVE PROMPT (Segmented)", value=pos_prompt, height=250, key=f"pos_{curr}")
    st.text_area("NEGATIVE PROMPT (Pagar Gaib)", value=neg_prompt, height=80, key=f"neg_{curr}")

    st.markdown("---")
    if curr < total:
        st.subheader(f"📸 Upload Frame Terakhir Output Flow AI (Scene {curr})")
        st.caption("Gambar ini akan digunakan AI sebagai jangkar konsistensi wajah & baju di scene berikutnya.")
        f_up = st.file_uploader("Upload JPG/PNG Output Scene ini", type=["png", "jpg", "jpeg"], key=f"fup_{curr}")

        if f_up:
            st.session_state.scene_frames[curr] = {"bytes": f_up.getvalue()}
            st.success("✔️ Frame Kontinuitas Tersimpan!")
            st.image(f_up, width=280)
        elif curr in st.session_state.scene_frames:
            st.success("✔️ Frame Kontinuitas Tersimpan.")

    st.markdown("---")
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if curr > 1 and st.button("← Scene Sebelumnya"):
            st.session_state.current_scene -= 1
            st.rerun()
    with col_nav2:
        if curr < total:
            is_locked = curr not in st.session_state.scene_frames
            if st.button("Lanjut Scene Berikutnya →", type="primary", disabled=is_locked, use_container_width=True):
                st.session_state.current_scene += 1
                st.rerun()

    if curr == total:
        st.markdown("---")
        if not st.session_state.get("is_completed", False):
            if st.button("✅ Selesaikan Proyek", type="primary", use_container_width=True):
                st.session_state.is_completed = True
                st.rerun()
        else:
            st.success("🎉 Seluruh Prompt Video Selesai!")
            if st.button("🚀 GENERATE PAKET SEO VIRAL", type="primary", use_container_width=True):
                if build_viral_seo(): st.rerun()
            if st.session_state.seo_package:
                seo = st.session_state.seo_package
                st.text_input("📌 Judul:", value=seo.get("title", ""))
                st.text_area("📱 Caption:", value=seo.get("caption", ""), height=80)
                st.text_area("📝 Deskripsi:", value=seo.get("description", ""), height=80)
                st.text_area("🏷️ Tags:", value=seo.get("tags", ""), height=60)

with st.sidebar:
    st.title("🕶️ Si Kumis Studio")
    st.text_input("Gemini API Key", key="api_key", type="password")
    st.markdown("---")
    if st.button("🏠 Mulai Proyek Baru", use_container_width=True):
        st.session_state.clear()
        # Bersihkan memori JSON lama
        if os.path.exists("storyboard_state.json"): os.remove("storyboard_state.json")
        init_state()
        st.rerun()
    if st.session_state.total_scenes > 0:
        st.markdown("---")
        if st.button("📋 Peta Storyboard", use_container_width=True): navigate_to("analysis")
        if st.button("🎬 Studio Produksi", use_container_width=True): navigate_to("scenes")

if st.session_state.page == "home": view_home()
elif st.session_state.page == "analysis": view_analysis()
elif st.session_state.page == "scenes": view_scenes()
