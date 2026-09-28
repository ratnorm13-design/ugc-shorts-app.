import json
import re
import os
import streamlit as st
from google import genai
from google.genai import types

# ==========================================
# 1. KONFIGURASI HALAMAN & GLOBAL VARIABEL
# ==========================================
st.set_page_config(
    page_title="Si Kumis IP Studio",
    page_icon="🕶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

AVAILABLE_MODELS = {
    "Gemini 3.8 Flash (Terbaru & Paling Cerdas)": "gemini-3.8-flash",
    "Gemini 3.7 Flash (Stabil & Cepat)": "gemini-3.7-flash",
    "Gemini 3.6 Flash (Versi Klasik/Alternatif)": "gemini-3.6-flash"
}

ASPECT_RATIOS = [
    "9:16 — TikTok / Reels / Shorts",
    "16:9 — YouTube Long Form",
    "1:1 — Square / Feeds"
]

ART_STYLES = [
    "Photorealistic / Ultra-Realistic (4K, real life footage)",
    "Studio Ghibli (Classic 2D animation, pastel aesthetic)",
    "3D Animation (Pixar / Illumination Style, smooth renders)",
    "Modern Anime (Dynamic 2D cel-shaded, sharp lines)",
    "Claymation / Stop-Motion (Tactile clay textures, Shaun the Sheep style)",
    "Retro VHS / Camcorder (Grit, 90s amateur UGC aesthetic)",
    "Cinematic Film (Dramatic lighting, anamorphic bokeh)",
    "CCTV / Dashcam Footage (Security angle, caught-on-camera vibe)"
]

# ==========================================
# 2. STATE MANAGEMENT
# ==========================================
def init_state():
    defaults = {
        "page": "home",
        "api_key": "",
        "selected_model_label": list(AVAILABLE_MODELS.keys())[0],
        "aspect_ratio": ASPECT_RATIOS[0],
        "art_style": ART_STYLES[0],
        "custom_subjects": "", # State baru untuk karakter kustom
        "analysis_data": {},
        "scene_frames": {},
        "scene_prompts": {},
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
        client = genai.Client(api_key=raw_key)
        model_label = st.session_state.get("selected_model_label", list(AVAILABLE_MODELS.keys())[0])
        model_endpoint = AVAILABLE_MODELS.get(model_label, "gemini-3.8-flash")
        return client, model_endpoint
    except Exception as err:
        st.error(f"Koneksi ke Gemini API gagal: {err}")
        return None, None

def parse_json_safely(text_response: str):
    clean_text = re.sub(r"^```(?:json)?\s*", "", text_response.strip(), flags=re.I)
    clean_text = re.sub(r"\s*```$", "", clean_text)
    try:
        return json.loads(clean_text)
    except Exception:
        start_pos = clean_text.find("{")
        end_pos = clean_text.rfind("}") + 1
        if start_pos != -1 and end_pos > start_pos:
            return json.loads(clean_text[start_pos:end_pos])
        raise ValueError("Gagal membaca struktur data JSON dari respons AI.")

# ==========================================
# 3. CORE LOGIC DENGAN PENGUNCIAN SUBJEK ABSOLUT
# ==========================================
def run_viral_adaptation():
    client, model_name = get_gemini_client_and_model()
    if not client or not model_name:
        return

    file_upload = st.session_state.get("viral_video_file")
    if not file_upload:
        st.error("Silakan upload file video referensi terlebih dahulu.")
        return

    try:
        file_bytes = file_upload.getvalue()
        mime_type = getattr(file_upload, "type", "video/mp4") or "video/mp4"
        media_payload = [types.Part.from_bytes(data=file_bytes, mime_type=mime_type)]
    except Exception as err:
        st.error(f"Gagal memuat berkas video: {err}")
        return

    custom_instructions = st.session_state.get("custom_subjects", "").strip()
    custom_rule = f"Ubah karakter pendukung sesuai instruksi berikut: '{custom_instructions}'." if custom_instructions else "Pertahankan karakter pendukung asli dari video (atau modifikasi natural) namun pastikan mereka tidak tiba-tiba hilang."

    sys_instruction = f"""
TUGAS UTAMA: Analisis video referensi secara presisi 1:1. 

ATURAN KETAT (CRITICAL OBJECT PERMANENCE):
1. SUBJEK UTAMA: Ubah subjek sentral menjadi kucing 'Si Kumis' (kucing putih, fur kumis hitam di bawah hidung, bercak hitam di kepala).
2. SUBJEK PENDUKUNG & KONTINUITAS ABSOLUT: {custom_rule} Lakukan SENSUS subjek (misal: jika ada bebek, anjing, atau hewan lain). Semua subjek yang muncul di Scene 1 WAJIB dilacak dan ditulis kembali di Scene berikutnya. Objek tidak boleh tiba-tiba menghilang atau muncul tanpa alasan fisik yang logis (seperti benda yang bergerak ke luar frame).
3. PROP TRACKING: Lacak barang yang dipegang/dipakai. Catat perubahan state (jatuh, dilepas, dipakai). 
4. BACKGROUND: Modifikasi latar belakang tipis-tipis secara natural, hindari copyright.
5. AUDIO & EMOSI: Ekstrak ekspresi (marah, kaget) dan sfx (suara benturan, kaca, dsb).

BERIKAN OUTPUT DALAM FORMAT JSON BERIKUT:
{{
  "original_duration_est": 10,
  "total_scenes": 2,
  "adaptation_strategy": "Penjelasan pelacakan properti dan penjagaan subjek pendukung agar tidak gaib.",
  "scenes": [
    {{
      "scene_num": 1,
      "original_breakdown": "Deskripsi asli.",
      "modified_action_en": "English description of Si Kumis action. MUST EXPLICITLY LIST ALL secondary subjects present (e.g. 'A bulldog in passenger seat, a duck on the roof'). Include prop status and exact expressions.",
      "environment_en": "English background."
    }}
  ]
}}
"""
    with st.spinner(f"AI sedang melakukan sensus objek dan membedah video menggunakan {model_name}..."):
        try:
            res = client.models.generate_content(
                model=model_name,
                contents=[types.Content(role="user", parts=media_payload + [types.Part.from_text(text=sys_instruction)])],
                config=types.GenerateContentConfig(temperature=0.3, response_mime_type="application/json")
            )
            data = parse_json_safely(res.text)
            
            st.session_state.update({
                "analysis_data": data,
                "total_scenes": int(data.get("total_scenes", 1)),
                "current_scene": 1,
                "scene_prompts": {},
                "scene_frames": {},
                "seo_package": {},
                "is_completed": False
            })
            navigate_to("analysis")
        except Exception as err:
            st.error(f"Terjadi kesalahan saat pemrosesan AI: {err}")

def generate_scene_prompt(scene_num: int):
    data = st.session_state.analysis_data
    scenes = data.get("scenes", [])
    
    scene_data = next((s for s in scenes if s["scene_num"] == scene_num), None)
    if not scene_data:
        return False

    action_en = scene_data.get("modified_action_en", "")
    env_en = scene_data.get("environment_en", "")
    ratio_clean = st.session_state.aspect_ratio.split("—")[0].strip()
    style_clean = st.session_state.art_style.split("(")[0].strip()

    if scene_num == 1:
        continuity_instruction = "MODE: Text-to-Video (T2V). Establish initial setup, ensure ALL specified secondary subjects and props are visible."
    else:
        if (scene_num - 1) not in st.session_state.scene_frames:
            return "LOCKED"
        continuity_instruction = (
            "MODE: Image-to-Video (I2V). STRICT CONTINUITY LOCK: Match starting frame precisely. "
            "DO NOT DROP ANY SECONDARY CHARACTERS. If a duck/dog/item was in the previous frame, it MUST remain in the exact same position unless explicitly interacting."
        )

    prompt = f"""[ASPECT RATIO]: {ratio_clean}
[ART STYLE STRICT]: {style_clean}
[CHARACTER DNA]: Photorealistic white cat, distinct black mustache-like fur mark under pink nose, black fur patch on head.
[ENVIRONMENT]: {env_en}
[1:1 ACTION, SECONDARY SUBJECT CENSUS & PROP STATUS]: {action_en}
[CONTINUITY LOCK]: {continuity_instruction}
[CAMERA & MOTION]: 1:1 match with reference video motion physics, UGC style."""

    st.session_state.scene_prompts[scene_num] = prompt.strip()
    return True

# ... (Fungsi build_viral_seo() tetap sama seperti sebelumnya) ...
def build_viral_seo():
    client, model_name = get_gemini_client_and_model()
    if not client or not model_name:
        return False

    data = st.session_state.analysis_data
    sys_seo = f"""
Buatkan Paket SEO Komplit untuk video komedi 'Si Kumis' berdasarkan alur berikut:
{json.dumps(data.get('scenes', []))}

OUTPUT JSON WAJIB:
{{
  "title": "Judul Shorts/TikTok clickbait",
  "caption": "Caption interaktif TikTok + Hashtags (#SiKumis)",
  "description": "Deskripsi SEO",
  "tags": "tag1, tag2, tag3"
}}
"""
    with st.spinner("Meracik Algoritma SEO..."):
        try:
            res = client.models.generate_content(
                model=model_name,
                contents=sys_seo,
                config=types.GenerateContentConfig(temperature=0.3, response_mime_type="application/json")
            )
            st.session_state.seo_package = parse_json_safely(res.text)
            return True
        except Exception as err:
            st.error(f"Gagal membuat paket SEO: {err}")
            return False

# ==========================================
# 4. TAMPILAN ANTARMUKA (UI VIEWS)
# ==========================================
def view_home():
    st.title("🕶️ Si Kumis IP Studio")
    st.caption("Alur 1:1, Ekspresi Akurat, & Object Permanence Lock")

    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Upload Video Referensi")
        st.file_uploader(
            "Upload Video Viral (Format MP4 / MOV / WEBM)",
            type=["mp4", "mov", "webm"],
            key="viral_video_file"
        )
        st.info("💡 AI akan mencatat sensus subjek (termasuk hewan pendukung) agar tidak tiba-tiba hilang seperti kasus bebek.")

    with col2:
        st.subheader("2. Setting Parameter Output")
        st.selectbox("Pilih Varian Model Gemini", list(AVAILABLE_MODELS.keys()), key="selected_model_label")
        st.selectbox("Rasio Aspect Ratio Video", ASPECT_RATIOS, key="aspect_ratio")
        st.selectbox("Gaya Visualisasi (Art Style)", ART_STYLES, key="art_style")
        
        # FITUR BARU: Kolom Instruksi Tambahan
        st.text_area(
            "Kustomisasi Karakter Pendukung (Opsional)",
            placeholder="Contoh: Ganti subjek 2 menjadi kucing British Shorthair abu-abu. Pastikan ada bebek di atas mobil.",
            key="custom_subjects",
            help="Instruksikan AI untuk mengganti atau mengunci karakter sekunder."
        )

    st.markdown("---")
    st.button(
        "🚀 EKSTRAK & BEDAH VIDEO 1:1",
        type="primary",
        use_container_width=True,
        on_click=run_viral_adaptation
    )

def view_analysis():
    data = st.session_state.analysis_data
    st.title("📋 Storyboard & Peta Bedah Skenario")
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.metric("Durasi Video Asli", f"{data.get('original_duration_est', 0)} Detik")
    c2.metric("Total Scene Produksi", f"{st.session_state.total_scenes} Scene")

    st.info(f"💡 **Strategi Penyesuaian & Sensus Objek:**\n{data.get('adaptation_strategy', '')}")
    st.markdown("---")

    for scene in data.get("scenes", []):
        s_num = scene['scene_num']
        with st.container():
            st.markdown(f"#### 📍 Scene {s_num}")
            st.info(f"**🔍 Video Asli:**\n{scene.get('original_breakdown', '')}")
            st.warning(f"**🕶️ Adaptasi Si Kumis:**\n{scene.get('modified_action_en', '')}")
            st.markdown("---")

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        if st.button("← Batal / Ulangi"):
            navigate_to("home")
    with col_btn2:
        if st.button("✅ KUNCI SCENE & MASUK STUDIO PRODUKSI", type="primary", use_container_width=True):
            navigate_to("scenes")

def view_scenes():
    curr = st.session_state.current_scene
    total = st.session_state.total_scenes
    if total == 0:
        return navigate_to("home")

    st.title(f"🎥 Studio Produksi — Scene {curr} dari {total}")
    st.markdown("---")

    if curr > 1 and (curr - 1) not in st.session_state.scene_frames:
        st.error(f"🛑 **GEMBOK KONTINUITAS AKTIF:** Upload screenshot Frame Terakhir dari Scene {curr-1}.")
        if st.button(f"← Kembali ke Scene {curr-1}"):
            st.session_state.current_scene -= 1
            st.rerun()
        return

    if curr not in st.session_state.scene_prompts:
        generate_scene_prompt(curr)

    if curr in st.session_state.scene_prompts:
        if curr == 1:
            st.success("🔥 **SCENE 1 (Text-to-Video):** Salin prompt ke Flow AI.")
        else:
            st.warning(f"🖼️ **SCENE {curr} (Image-to-Video):** Gunakan frame terakhir Scene {curr-1}.")

        st.text_area(
            label=f"Prompt Scene {curr}",
            value=st.session_state.scene_prompts[curr],
            height=150,
            key=f"txt_prompt_{curr}"
        )

    st.markdown("---")

    if curr < total:
        st.subheader(f"📸 Upload Frame Terakhir Scene {curr}")
        f_up = st.file_uploader(
            f"Pilih Gambar Last Frame Scene {curr} (PNG/JPG)",
            type=["png", "jpg", "jpeg"],
            key=f"fup_{curr}"
        )

        if f_up:
            st.session_state.scene_frames[curr] = {"bytes": f_up.getvalue(), "name": f_up.name}
            st.success(f"✔️ Frame Tersimpan!")
            st.image(f_up, width=280)
        elif curr in st.session_state.scene_frames:
            st.success(f"✔️ Frame Tersimpan.")

    st.markdown("---")
    col_nav1, col_nav2 = st.columns(2)

    with col_nav1:
        if curr > 1:
            if st.button("← Kembali ke Scene Sebelumnya"):
                st.session_state.current_scene -= 1
                st.rerun()

    with col_nav2:
        if curr < total:
            is_locked = curr not in st.session_state.scene_frames
            if st.button("Lanjut ke Scene Berikutnya →", type="primary", disabled=is_locked, use_container_width=True):
                st.session_state.current_scene += 1
                st.rerun()

    if curr == total:
        st.markdown("---")
        if not st.session_state.get("is_completed", False):
            if st.button("✅ Ya, Produksi Selesai", type="primary", use_container_width=True):
                st.session_state.is_completed = True
                st.rerun()
        else:
            st.success("🎉 Produksi Selesai!")
            if st.button("🚀 GENERATE PAKET SEO VIRAL", type="primary", use_container_width=True):
                if build_viral_seo():
                    st.rerun()

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
        init_state()
        st.rerun()
    if st.session_state.total_scenes > 0:
        st.markdown("---")
        if st.button("📋 Peta Storyboard", use_container_width=True): navigate_to("analysis")
        if st.button("🎬 Studio Produksi", use_container_width=True): navigate_to("scenes")

if st.session_state.page == "home": view_home()
elif st.session_state.page == "analysis": view_analysis()
elif st.session_state.page == "scenes": view_scenes()
