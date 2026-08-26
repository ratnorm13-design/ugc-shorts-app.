import streamlit as st
import yt_dlp
import os
from google import genai

# --- PAGE CONFIG ---
st.set_page_config(page_title="Studio AI - UGC Shorts Engine", page_icon="⚡", layout="centered")
st.title("⚡ UGC Shorts Studio AI")
st.caption("Multi-Brain AI Engine (AQ-Key Supported): Bedah Video -> Refinement Diskusi -> Prompt Presisi!")

# --- API KEYS SETUP ---
gemini_key = st.sidebar.text_input("Gemini API Key (Wajib - Format AQ...)", type="password")

client = None
if gemini_key:
    clean_key = gemini_key.strip().replace(" ", "_").replace("\n", "").replace("\r", "")
    try:
        # Inisialisasi client baru yang support key AQ.
        client = genai.Client(api_key=clean_key)
    except Exception as e:
        st.sidebar.error(f"Format Key Error: {e}")

# --- INPUT METHOD ---
input_mode = st.radio(
    "Metode Input:",
    ("📁 Upload File Video (.mp4)", "✍️ Input Topik / Ide Barumu", "🔗 Paste Link Shorts/TikTok/IG")
)

video_path = "temp_video.mp4"
video_ready = False
user_topic = ""

if input_mode == "📁 Upload File Video (.mp4)":
    uploaded_video = st.file_uploader("Upload Video Viral dari HP/Laptopmu:", type=["mp4", "mov", "avi"])
    if uploaded_video is not None:
        with open(video_path, "wb") as f:
            f.write(uploaded_video.read())
        video_ready = True
        st.success("Video berhasil di-upload! Siap dibedah & dimodifikasi.")

elif input_mode == "✍️ Input Topik / Ide Barumu":
    user_topic = st.text_area("Tuliskan Topik / Judul / Deskripsi Singkat Ide Videomu:")
    if user_topic:
        video_ready = True

else:
    url_input = st.text_input("Paste Link Video Viral:")
    if url_input and st.button("📥 Download Video"):
        with st.spinner("Mengunduh video..."):
            try:
                ydl_opts = {
                    'format': 'best[ext=mp4]/best',
                    'outtmpl': video_path,
                    'overwrites': True,
                    'quiet': True,
                    'no_warnings': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url_input])
                video_ready = True
                st.success("Video berhasil diunduh!")
            except Exception as e:
                st.error("Gagal download via link karena terblokir. Disarankan pakai metode 'Upload File Video'!")

# --- SELECTBOX DURASI & STYLE VISUAL ---
durasi_pilihan = st.selectbox(
    "⏱️ Pilih Target Durasi Video:",
    options=["15 Detik (2 Scene @8s)", "30 Detik (4 Scene @8s)", "60 Detik (8 Scene @8s)"]
)

style_pilihan = st.selectbox(
    "🎨 Pilih Gaya Visual Video:",
    options=[
        "Realistis / Photorealistic (8K Cinematic)",
        "3D Animation (Pixar / Dreamworks Style)",
        "2D Anime (Studio Ghibli Aesthetic)",
        "Comic Book / Pop Art (Bold Lines & Halftone)",
        "Claymation (Stop Motion Style)"
    ]
)

# --- GENERATE PROMPT ENGINE ---
if st.button("🚀 RACIK PROMPT DUAL-BRAIN UNIK"):
    if not gemini_key or not client:
        st.error("⚠️ Masukkan Gemini API Key terlebih dahulu di sidebar!")
    elif not video_ready and not user_topic:
        st.error("⚠️ Masukkan input video atau topik terlebih dahulu!")
    else:
        with st.spinner("AI sedang membedah video & meracik versi unik..."):
            try:
                system_instruction = f"""
                Kamu adalah AI Director profesional untuk pembuatan prompt UGC Shorts.
                Tugasmu:
                1. Bedah isi input video atau topik.
                2. Buat alur cerita baru yang dimodifikasi minimal 30% agar bebas plagiat, tambahkan twist/komedi segar.
                3. Tetapkan 1 'CHARACTER ANCHOR' rinci (baju, rambut, umur, aksesoris) yang ditempel persis di awal setiap prompt scene.
                4. Buat scene berdurasi 8 detik per scene.

                SPESIFIKASI VIDEO:
                - Target durasi: {durasi_pilihan}.
                - Gaya Visual: {style_pilihan}.

                FORMAT OUTPUT MESTI TERPISAH KETAT:
                [PROMPT_SECTION]
                (Isi Character Anchor dan Prompt Scene Flow AI 8s per scene di sini)
                [/PROMPT_SECTION]

                [VO_SECTION]
                (Isi Naskah Dubbing Voiceover Bahasa Indonesia per scene untuk CapCut di sini)
                [/VO_SECTION]

                [SEO_SECTION]
                (Isi Judul Hook, Deskripsi, dan Hashtag di sini)
                [/SEO_SECTION]

                [TAGS_SECTION]
                (Isi kata kunci/tags dipisahkan koma di sini)
                [/TAGS_SECTION]
                """

                if input_mode == "✍️ Input Topik / Ide Barumu":
                    full_prompt = f"{system_instruction}\n\nIde User:\n{user_topic}"
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=full_prompt
                    )
                else:
                    # Upload file video langsung ke Gemini Files API menggunakan client baru
                    with st.spinner("Mengunggah video ke server Gemini..."):
                        video_file = client.files.upload(file=video_path)
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[video_file, system_instruction]
                    )

                raw_text = response.text

                # Parse Response per Section
                prompt_content = raw_text.split("[PROMPT_SECTION]")[1].split("[/PROMPT_SECTION]")[0].strip() if "[PROMPT_SECTION]" in raw_text else raw_text
                vo_content = raw_text.split("[VO_SECTION]")[1].split("[/VO_SECTION]")[0].strip() if "[VO_SECTION]" in raw_text else "Gagal memisahkan VO Script."
                seo_content = raw_text.split("[SEO_SECTION]")[1].split("[/SEO_SECTION]")[0].strip() if "[SEO_SECTION]" in raw_text else "Gagal memisahkan SEO Pack."
                tags_content = raw_text.split("[TAGS_SECTION]")[1].split("[/TAGS_SECTION]")[0].strip() if "[TAGS_SECTION]" in raw_text else "Gagal memisahkan Tags."

                st.success("Racikan Dual-Brain AI Berhasil Dibuat!")
                
                # TAMPILAN TAB
                tab1, tab2, tab3, tab4 = st.tabs(["🎬 Prompt Flow AI", "🎙️ VO Script CapCut", "🚀 SEO Pack", "🏷️ YouTube Tags"])
                
                with tab1:
                    st.subheader("Prompt Scene Flow AI (8s/Scene)")
                    st.text_area("Copy Prompt Flow AI:", value=prompt_content, height=400)
                
                with tab2:
                    st.subheader("Naskah Dubbing Voiceover")
                    st.text_area("Copy VO Script:", value=vo_content, height=300)
                    
                with tab3:
                    st.subheader("SEO Judul & Hashtag")
                    st.text_area("Copy SEO Pack:", value=seo_content, height=300)

                with tab4:
                    st.subheader("Keywords / Tags YouTube")
                    st.text_area("Copy Tags YouTube:", value=tags_content, height=200)

            except Exception as e:
                st.error(f"Gagal meracik prompt: {e}")
