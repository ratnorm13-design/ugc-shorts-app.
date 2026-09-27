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

# Model Gemini Flash terbaru untuk analisis multimodal cepat
MODEL_NAME = "gemini-2.5-flash"

# DNA Karakter Si Kumis dikunci total agar konsisten
SI_KUMIS_DNA = (
    "CHARACTER IP LOCK: 'Si Kumis'. "
    "A photorealistic white cat wearing stylish black sunglasses over its eyes, "
    "featuring a distinct black mustache-like fur mark directly under its pink nose. "
    "Has a small black fur patch on the top of its head between ears, pure white coat body, "
    "and maintains a cool, calm, deadpan poker-face expression. "
    "CRITICAL CONSTRAINTS: Identical white fur, black mustache mark, head patch, and sunglasses across every frame."
)

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
    """Mendaftarkan seluruh key session state di awal agar tidak ada KeyError saat rerun."""
    defaults = {
        "page": "home",
        "api_key": "",
        "aspect_ratio": ASPECT_RATIOS[0],
        "art_style": ART_STYLES[0],
        "analysis_data": {},
        "scene_frames": {},      # Menyimpan byte & preview dari frame terakhir tiap scene
        "scene_prompts": {},     # Menyimpan prompt rakitan Flow AI per scene
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
    """Pindah halaman aman tanpa bikin state korup."""
    st.session_state.page = page_name
    st.rerun()

def get_gemini_client():
    """Menginisialisasi SDK Client Gemini Google GenAI."""
    raw_key = (os.getenv("GEMINI_API_KEY") or st.session_state.get("api_key", "")).strip("`\"' \n\r\t")
    if not raw_key:
        st.error("Silakan masukkan Gemini API Key pada menu Sidebar terlebih dahulu.")
        return None
    try:
        return genai.Client(api_key=raw_key)
    except Exception as err:
        st.error(f"Koneksi ke Gemini API gagal: {err}")
        return None

def parse_json_safely(text_response: str):
    """Mengekstrak JSON dari teks AI walau ada markdown backtick."""
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
# 3. CORE LOGIC (ANALISIS & RAKIT PROMPT)
# ==========================================
def run_viral_adaptation():
    """Fungsi utama membedah video viral, menghitung durasi 8s, dan merancang komedi absurd."""
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

    sys_instruction = f"""
TUGAS UTAMA:
Analisis video viral ini secara mendalam dan buatkan skenario adaptasi komedi absurd untuk karakter 'Si Kumis'.

ATURAN STRUKTUR & DURASI (Wajib Ikuti):
1. ATURAN DURASI 8 DETIK: Estimasi durasi video asli dalam detik. Tambahkan durasi ekstra adegan komedi absurd agar TOTAL DURASI menjadi KELIPATAN 8 DETIK (Contoh: video asli 13 detik -> bulatkan/tambahkan jadi 16 detik = 2 Scene @ 8 detik. Jika video asli 22 detik -> bulatkan jadi 24 detik = 3 Scene @ 8 detik).
2. EKSTENSI ABSURD: Penambahan adegan di akhir cerita TIDAK BOLEH DATAR. Harus berisi puncak komedi/payoff yang makin kocak, ajaib, dan absurd melebihi video aslinya.
3. KARAKTER UTAMA: Ganti total subjek asli di video menjadi kucing 'Si Kumis' (kucing putih, kacamata hitam, tanda fur kumis hitam).
4. ANTI-COPYRIGHT: Modifikasi pencahayaan, tekstur, dan latar lingkungan agar unik dan tidak diclaim hak cipta.
5. AUDIO CUES (PEMICU SUARA NATIVE): Masukkan kata petunjuk suara secara eksplisit di deskripsi aksi (contoh: *loud crash sound*, *cat meow*, *glass shattering*, *engine revving*) agar AI pembuat video seperti Flow AI otomatis menghasilkan efek suara bawaan.

BERIKAN OUTPUT DALAM FORMAT JSON BERIKUT:
{{
  "original_duration_est": 13,
  "extended_total_duration": 16,
  "total_scenes": 2,
  "adaptation_strategy": "Penjelasan rinci (dalam Bahasa Indonesia) tentang alur komedi, pengubahan subjek, dan strategi latar belakang.",
  "scenes": [
    {{
      "scene_num": 1,
      "original_breakdown": "Bedah adegan video asli pada bagian ini dalam Bahasa Indonesia.",
      "modified_action_en": "Detailed English description of Si Kumis performing the absurd action for Scene 1, including native sound cues (e.g. *loud thud sound*).",
      "environment_en": "Detailed English description of the modified anti-copyright environment."
    }}
  ]
}}
"""
    with st.spinner("AI sedang menganalisis video, mengunci durasi 8 detik, & meracik komedi absurd..."):
        try:
            res = client.models.generate_content(
                model=MODEL_NAME,
                contents=[types.Content(role="user", parts=media_payload + [types.Part.from_text(text=sys_instruction)])],
                config=types.GenerateContentConfig(temperature=0.4, response_mime_type="application/json")
            )
            data = parse_json_safely(res.text)
            
            # Reset dan simpan data produksi baru
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
    """Merakit prompt lengkap untuk Flow AI per scene sesuai standar komplit."""
    data = st.session_state.analysis_data
    scenes = data.get("scenes", [])
    
    scene_data = next((s for s in scenes if s["scene_num"] == scene_num), None)
    if not scene_data:
        return False

    action_en = scene_data.get("modified_action_en", "")
    env_en = scene_data.get("environment_en", "")
    ratio_clean = st.session_state.aspect_ratio.split("—")[0].strip()
    style_clean = st.session_state.art_style.split("(")[0].strip()

    # Kontinuitas ketat
    if scene_num == 1:
        continuity_instruction = "MODE: Text-to-Video (T2V). Establish initial character pose, background, and lighting clearly."
    else:
        if (scene_num - 1) not in st.session_state.scene_frames:
            return "LOCKED"
        continuity_instruction = (
            "MODE: Image-to-Video (I2V). CONTINUITY LOCK: Match EXACTLY to the provided starting frame image. "
            "No jump cuts, no teleportation, no background shifting. Maintain identical physical trajectory and position."
        )

    # Format Prompt Baku dan Komplit untuk Flow AI
    prompt = f"""[SCENE DURATION]: 8 SECONDS
[ASPECT RATIO]: {ratio_clean}
[ART STYLE STRICT]: {style_clean}
[CHARACTER DNA LOCK]: {SI_KUMIS_DNA}
[ENVIRONMENT]: {env_en}
[ACTION & NATIVE AUDIO CUES]: {action_en}
[CONTINUITY & PHYSICS]: {continuity_instruction}
[CAMERA & MOTION]: Dynamic camera motion, fluid physics, cinematic UGC composition."""

    st.session_state.scene_prompts[scene_num] = prompt.strip()
    return True

def build_viral_seo():
    """Meracik paket SEO lengkap setelah seluruh scene dikonfirmasi selesai."""
    client = get_gemini_client()
    if not client:
        return False

    data = st.session_state.analysis_data
    sys_seo = f"""
Buatkan Paket SEO Komplit untuk video pendek komedi 'Si Kumis' berdasarkan alur berikut:
{json.dumps(data.get('scenes', []))}

Gunakan bahasa yang menarik, clickbait, dan ramah algoritma TikTok, Shorts, dan Reels.

OUTPUT JSON WAJIB:
{{
  "title": "Judul Shorts/TikTok clickbait absurd",
  "caption": "Caption TikTok interaktif + pemicu komentar + Hashtags viral (#SiKumis #KucingAbsurd dll)",
  "description": "Deskripsi SEO lengkap 2-3 kalimat untuk YouTube Shorts",
  "tags": "tag1, tag2, tag3, tag4, tag5, tag6, tag7, tag8"
}}
"""
    with st.spinner("Meracik Algoritma SEO TikTok & Shorts..."):
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
    st.caption("Ubah Video Viral Jadi Konten Komedi 'Si Kumis' — Otomatis 8 Detik/Scene, Audio Native, & Anti-Copyright")

    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Upload Video Referensi")
        st.file_uploader(
            "Upload Video Viral (Format MP4 / MOV / WEBM)",
            type=["mp4", "mov", "webm"],
            key="viral_video_file"
        )
        st.info("💡 **Petunjuk:** Upload video pendek yang viral. AI akan membaca alurnya, menghitung durasi, dan membuatkan versi Si Kumis yang lebih gokil.")

    with col2:
        st.subheader("2. Setting Parameter Output")
        st.selectbox("Rasio Aspect Ratio Video", ASPECT_RATIOS, key="aspect_ratio")
        st.selectbox("Gaya Visualisasi (Art Style)", ART_STYLES, key="art_style")
        st.success("✅ **Sistem Flow AI:** Setiap Scene dikunci durasinya **8 Detik** agar pas dengan standar generator AI modern.")

    st.markdown("---")
    st.button(
        "🚀 EKSTRAK & BEDAH VIDEO VIRAL",
        type="primary",
        use_container_width=True,
        on_click=run_viral_adaptation
    )

def view_analysis():
    data = st.session_state.analysis_data
    st.title("📋 Storyboard & Peta Bedah Skenario")
    st.caption("Hasil analisis AI: Perbandingan video asli vs Modifikasi Komedi Si Kumis")

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Durasi Video Asli", f"{data.get('original_duration_est', 0)} Detik")
    c2.metric("Durasi Modifikasi (Kelipatan 8s)", f"{data.get('extended_total_duration', 0)} Detik")
    c3.metric("Total Scene Produksi", f"{st.session_state.total_scenes} Scene")

    st.info(f"💡 **Strategi Komedi Absurd AI:**\n{data.get('adaptation_strategy', '')}")
    st.markdown("---")

    # Tampilan Komparasi Atas (Asli) vs Bawah (Modifikasi AI)
    st.subheader("🎬 Rincian Storyboard Per Scene")
    for scene in data.get("scenes", []):
        s_num = scene['scene_num']
        with st.container():
            st.markdown(f"#### 📍 Scene {s_num} (Durasi: 8 Detik)")
            
            # ATAS: Bedah Asli
            st.info(f"**🔍 Video Asli (Referensi):**\n{scene.get('original_breakdown', '')}")
            
            # BAWAH: Modifikasi AI
            st.warning(f"**🕶️ Modifikasi Si Kumis (Absurd & Audio Cues):**\n{scene.get('modified_action_en', '')}")
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
    st.caption(f"Setting Output: **{st.session_state.aspect_ratio.split('—')[0]}** | Gaya Visual: **{st.session_state.art_style.split('(')[0]}**")
    st.markdown("---")

    # VALIDASI GEMBOK KONTINUITAS (Scene 2+)
    if curr > 1 and (curr - 1) not in st.session_state.scene_frames:
        st.error(f"🛑 **GEMBOK KONTINUITAS AKTIF:** Lu wajib mengunggah screenshot Frame Terakhir dari Scene {curr-1} sebelum bisa membuat Scene {curr}.")
        st.info("Langkah: Selesaikan render Scene sebelumnya di Flow AI -> Screenshot detik terakhir -> Upload gambarnya di halaman Scene sebelumnya.")
        if st.button(f"← Kembali ke Scene {curr-1}"):
            st.session_state.current_scene -= 1
            st.rerun()
        return

    # Generate Prompt Jika Belum Ada
    if curr not in st.session_state.scene_prompts:
        generate_scene_prompt(curr)

    # TAMPILAN HASIL PROMPT
    if curr in st.session_state.scene_prompts:
        if curr == 1:
            st.success("🔥 **SCENE 1 (Text-to-Video):** Copy teks prompt di bawah ini langsung ke generator AI (Flow AI).")
        else:
            st.warning(f"🖼️ **SCENE {curr} (Image-to-Video):** Gunakan gambar frame terakhir Scene {curr-1} sebagai acuan awal, lalu masukan prompt di bawah.")

        # Tampilkan prompt rakitan lengkap
        st.code(st.session_state.scene_prompts[curr], language="markdown")

    st.markdown("---")

    # UPLOADER LAST FRAME (Khusus Scene sebelum Scene terakhir)
    if curr < total:
        st.subheader(f"📸 Upload Frame Terakhir Scene {curr}")
        st.caption("Upload screenshot detik terakhir dari video hasil render Scene ini untuk mengunci kontinyuitas Scene berikutnya.")

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

    # NAVIGASI PERPINDAHAN SCENE
    st.markdown("---")
    col_nav1, col_nav2 = st.columns(2)

    with col_nav1:
        if curr > 1:
            if st.button("← Kembali ke Scene Sebelumnya"):
                st.session_state.current_scene -= 1
                st.rerun()

    with col_nav2:
        if curr < total:
            # Tombol dikunci jika last frame belum diupload
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

    # SCENE TERAKHIR & TRIGGER SEO
    if curr == total:
        st.markdown("---")
        st.subheader("🏁 Konfirmasi Akhir Produksi Video")
        
        if not st.session_state.get("is_completed", False):
            st.info("Klik tombol di bawah ini jika lu sudah selesai merender seluruh scene video di Flow AI.")
            if st.button("✅ Ya, Seluruh Scene Video Selesai Dibuat", type="primary", use_container_width=True):
                st.session_state.is_completed = True
                st.rerun()
        else:
            st.success("🎉 Produksi Visual Selesai! Siapkan Paket SEO untuk Upload.")
            if st.button("🚀 GENERATE PAKET SEO VIRAL LENGKAP", type="primary", use_container_width=True):
                if build_viral_seo():
                    st.rerun()

            # Menampilkan Paket SEO
            if st.session_state.seo_package:
                seo = st.session_state.seo_package
                st.markdown("### 📊 Paket SEO Siap Pakai")
                st.text_input("📌 Judul Video Shorts / TikTok:", value=seo.get("title", ""))
                st.text_area("📱 Caption Interaktif TikTok & Reels:", value=seo.get("caption", ""), height=100)
                st.text_area("📝 Deskripsi Lengkap YouTube Shorts:", value=seo.get("description", ""), height=80)
                st.text_area("🏷️ Tags SEO (Copy-Paste):", value=seo.get("tags", ""), height=80)

# ==========================================
# 5. SIDEBAR NAVIGATION & ROUTING
# ==========================================
with st.sidebar:
    st.title("🕶️ Si Kumis IP Studio")
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

# Routing Halaman
if st.session_state.page == "home":
    view_home()
elif st.session_state.page == "analysis":
    view_analysis()
elif st.session_state.page == "scenes":
    view_scenes()
