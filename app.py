import json
import re
import time
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

# Menggunakan model Gemini 3.6 sesuai permintaan untuk API key berawalan 'AQ'
MODEL_NAME = "gemini-3.6"

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
# 2. STATE MANAGEMENT (MENCEGAH KEYERROR)
# ==========================================
def init_state():
    defaults = {
        "page": "home",
        "api_key": "",
        "aspect_ratio": ASPECT_RATIOS[0],
        "art_style": ART_STYLES[0],
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

def get_gemini_client():
    raw_key = (os.getenv("GEMINI_API_KEY") or st.session_state.get("api_key", "")).strip("`\"' \n\r\t")
    if not raw_key:
        st.error("Silakan masukkan Gemini API Key pada Sidebar terlebih dahulu.")
        return None
    try:
        return genai.Client(api_key=raw_key)
    except Exception as err:
        st.error(f"Koneksi ke Gemini API gagal: {err}")
        return None

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
# 3. CORE LOGIC (ANALISIS 1:1 & PROP TRACKING)
# ==========================================
def run_viral_adaptation():
    client = get_gemini_client()
    if not client:
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

    sys_instruction = """
TUGAS UTAMA: Analisis video referensi ini secara presisi 1:1. Alur, gerakan kamera, dan ekspresi emosi (marah, kesal, ketawa, kaget) harus disamakan plek ketiplek dengan aslinya tanpa modifikasi alur cerita.

ATURAN KETAT:
1. SUBJEK UTAMA: Ubah subjek manusia/hewan di video asli menjadi kucing 'Si Kumis' (kucing putih, tanda fur kumis hitam di bawah hidung, bercak hitam di kepala).
2. EKSPRESI & EMOSI: Catat detail ekspresi mikro subjek (misal: mata melotot kaget, nyengir kesal, tertawa, atau marah) agar akurat per scene.
3. PROP & OBJECT TRACKING (Sangat Penting): Lacak barang yang dipegang/dipakai (misal kacamata hitam, HP, dll). Jika di scene tertentu barang itu lepas, jatuh, atau hilang, catat statusnya dengan tegas agar di scene berikutnya barang tersebut TIDAK BOLEH tiba-tiba muncul kembali (no magic respawn).
4. BACKGROUND & ANTI-COPYRIGHT: Modifikasi latar belakang tipis-tipis secara natural (misal: ganti jenis pohon, struktur bangunan, atau tekstur jalan) agar visualnya berbeda dari video asli tetapi tetap sinkron dengan suasananya.
5. AUDIO CUES: Sertakan pemicu suara native (misal: *glass shattering*, *thud sound*, *cat angry meow*) di setiap scene.

BERIKAN OUTPUT DALAM FORMAT JSON BERIKUT:
{
  "original_duration_est": 10,
  "total_scenes": 2,
  "adaptation_strategy": "Penjelasan singkat penyesuaian latar belakang dan pelacakan properti.",
  "scenes": [
    {
      "scene_num": 1,
      "original_breakdown": "Deskripsi adegan, ekspresi emosi, dan status properti di scene ini (Bahasa Indonesia).",
      "modified_action_en": "English description of Si Kumis 1:1 action, precise expression, exact prop status (e.g. wearing sunglasses and holding phone, or glasses dropped), with native audio cues.",
      "environment_en": "English description of modified anti-copyright background."
    }
  ]
}
"""
    with st.spinner("AI sedang membedah video 1:1, ekspresi, & status properti..."):
        try:
            res = client.models.generate_content(
                model=MODEL_NAME,
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
            st.error(f"Terjadi kesalahan saat pemrosesan video oleh AI: {err}")

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
        continuity_instruction = "MODE: Text-to-Video (T2V). Establish initial setup, exact expressions, and prop states."
    else:
        if (scene_num - 1) not in st.session_state.scene_frames:
            return "LOCKED"
        continuity_instruction = (
            "MODE: Image-to-Video (I2V). STRICT CONTINUITY: Match starting frame precisely. "
            "Maintain exact prop states (do not respawn dropped items). Keep identical physical layout and lighting trajectory."
        )

    prompt = f"""[ASPECT RATIO]: {ratio_clean}
[ART STYLE STRICT]: {style_clean}
[CHARACTER DNA]: Photorealistic white cat, distinct black mustache-like fur mark under pink nose, black fur patch on head.
[ENVIRONMENT]: {env_en}
[1:1 ACTION, EXACT EXPRESSION & PROP STATUS]: {action_en}
[CONTINUITY LOCK]: {continuity_instruction}
[CAMERA & MOTION]: 1:1 match with reference video motion physics, UGC style."""

    st.session_state.scene_prompts[scene_num] = prompt.strip()
    return True

def build_viral_seo():
    client = get_gemini_client()
    if not client:
        return False

    data = st.session_state.analysis_data
    sys_seo = f"""
Buatkan Paket SEO Komplit untuk video komedi 'Si Kumis' berdasarkan alur berikut:
{json.dumps(data.get('scenes', []))}

OUTPUT JSON WAJIB:
{{
  "title": "Judul Shorts/TikTok clickbait",
  "caption": "Caption interaktif TikTok + Hashtags (#SiKumis #KucingAbsurd)",
  "description": "Deskripsi SEO YouTube Shorts",
  "tags": "tag1, tag2, tag3, tag4, tag5"
}}
"""
    with st.spinner("Meracik Algoritma SEO..."):
        try:
            res = client.models.generate_content(
                model=MODEL_NAME,
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
    st.caption("Ubah Video Viral Jadi Konten 'Si Kumis' — Alur 1:1, Ekspresi Akurat, & Prop Tracking Anti-Gaib")

    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Upload Video Referensi")
        st.file_uploader(
            "Upload Video Viral (Format MP4 / MOV / WEBM)",
            type=["mp4", "mov", "webm"],
            key="viral_video_file"
        )
        st.info("💡 AI akan menduplikasi alur dan ekspresi asli persis 1:1, mencatat status properti agar barang tidak tiba-tiba muncul kembali, serta merubah background secara natural.")

    with col2:
        st.subheader("2. Setting Parameter Output")
        st.selectbox("Rasio Aspect Ratio Video", ASPECT_RATIOS, key="aspect_ratio")
        st.selectbox("Gaya Visualisasi (Art Style)", ART_STYLES, key="art_style")
        st.success("✅ **Model Gemini 3.6 Aktif:** Siap memproses detail adegan tingkat tinggi.")

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
    st.caption("Perbandingan video referensi asli vs Adaptasi Kontrol Properti Si Kumis")

    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.metric("Durasi Video Asli", f"{data.get('original_duration_est', 0)} Detik")
    c2.metric("Total Scene Produksi", f"{st.session_state.total_scenes} Scene")

    st.info(f"💡 **Strategi Penyesuaian Latar & Properti:**\n{data.get('adaptation_strategy', '')}")
    st.markdown("---")

    st.subheader("🎬 Rincian Storyboard Per Scene")
    for scene in data.get("scenes", []):
        s_num = scene['scene_num']
        with st.container():
            st.markdown(f"#### 📍 Scene {s_num}")
            st.info(f"**🔍 Video Asli & Ekspresi:**\n{scene.get('original_breakdown', '')}")
            st.warning(f"**🕶️ Adaptasi Si Kumis (Prop & Audio Cues):**\n{scene.get('modified_action_en', '')}")
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
    st.caption(f"Rasio: **{st.session_state.aspect_ratio.split('—')[0]}** | Gaya: **{st.session_state.art_style.split('(')[0]}**")
    st.markdown("---")

    if curr > 1 and (curr - 1) not in st.session_state.scene_frames:
        st.error(f"🛑 **GEMBOK KONTINUITAS AKTIF:** Upload screenshot Frame Terakhir dari Scene {curr-1} terlebih dahulu.")
        if st.button(f"← Kembali ke Scene {curr-1}"):
            st.session_state.current_scene -= 1
            st.rerun()
        return

    if curr not in st.session_state.scene_prompts:
        generate_scene_prompt(curr)

    if curr in st.session_state.scene_prompts:
        if curr == 1:
            st.success("🔥 **SCENE 1 (Text-to-Video):** Salin prompt di bawah ini ke Flow AI.")
        else:
            st.warning(f"🖼️ **SCENE {curr} (Image-to-Video):** Gunakan frame terakhir Scene {curr-1} sebagai gambar referensi awal.")

        # TAMPILAN PROMPT MENGGUNAKAN TEKS BIASA + TOMBOL COPY OTOMATIS OLEH STREAMLIT
        st.markdown("**📝 Prompt Generator AI:**")
        st.text_area(
            label=f"Prompt Scene {curr}",
            value=st.session_state.scene_prompts[curr],
            height=150,
            key=f"txt_prompt_{curr}",
            help="Gunakan tombol salin di sudut kotak teks ini untuk menyalin prompt ke clipboard."
        )

    st.markdown("---")

    if curr < total:
        st.subheader(f"📸 Upload Frame Terakhir Scene {curr}")
        st.caption("Upload screenshot detik terakhir dari video hasil render Scene ini untuk mengunci kontinyuitas dan status properti.")

        f_up = st.file_uploader(
            f"Pilih Gambar Last Frame Scene {curr} (PNG/JPG)",
            type=["png", "jpg", "jpeg"],
            key=f"fup_{curr}"
        )

        if f_up:
            st.session_state.scene_frames[curr] = {
                "bytes": f_up.getvalue(),
                "name": f_up.name
            }
            st.success(f"✔️ Frame Terakhir Scene {curr} Berhasil Disimpan!")
            st.image(f_up, width=280, caption=f"Last Frame Scene {curr}")
        elif curr in st.session_state.scene_frames:
            st.success(f"✔️ Frame Terakhir Scene {curr} Sudah Tersimpan.")

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
            if st.button(
                f"Lanjut ke Scene {curr+1} →",
                type="primary",
                disabled=is_locked,
                use_container_width=True
            ):
                st.session_state.current_scene += 1
                st.rerun()
            if is_locked:
                st.caption("🔒 *Upload frame terakhir di atas untuk membuka tombol Lanjut.*")

    if curr == total:
        st.markdown("---")
        st.subheader("🏁 Konfirmasi Akhir Produksi Video")
        
        if not st.session_state.get("is_completed", False):
            if st.button("✅ Ya, Seluruh Scene Video Selesai Dibuat", type="primary", use_container_width=True):
                st.session_state.is_completed = True
                st.rerun()
        else:
            st.success("🎉 Produksi Visual Selesai! Siapkan Paket SEO.")
            if st.button("🚀 GENERATE PAKET SEO VIRAL LENGKAP", type="primary", use_container_width=True):
                if build_viral_seo():
                    st.rerun()

            if st.session_state.seo_package:
                seo = st.session_state.seo_package
                st.markdown("### 📊 Paket SEO Siap Pakai")
                st.text_input("📌 Judul Video Shorts / TikTok:", value=seo.get("title", ""))
                st.text_area("📱 Caption Interaktif TikTok & Reels:", value=seo.get("caption", ""), height=100)
                st.text_area("📝 Deskripsi Lengkap YouTube Shorts:", value=seo.get("description", ""), height=80)
                st.text_area("🏷️ Tags SEO:", value=seo.get("tags", ""), height=80)

# ==========================================
# 5. SIDEBAR NAVIGATION & ROUTING
# ==========================================
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
        st.markdown("**Navigasi Cepat Proyek:**")
        if st.button("📋 Peta Storyboard", use_container_width=True):
            navigate_to("analysis")
        if st.button("🎬 Studio Produksi", use_container_width=True):
            navigate_to("scenes")

if st.session_state.page == "home":
    view_home()
elif st.session_state.page == "analysis":
    view_analysis()
elif st.session_state.page == "scenes":
    view_scenes()
