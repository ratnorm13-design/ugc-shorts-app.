import streamlit as st
import yt_dlp
import os
import google.generativeai as genai

# --- PAGE CONFIG ---
st.set_page_config(page_title="Studio AI - UGC Shorts Engine", page_icon="⚡", layout="centered")
st.title("⚡ UGC Shorts Studio AI")
st.caption("Self-Refining AI Engine: Bedah Video -> Diskusi Internal -> Prompt Presisi & Unik!")

# --- API KEYS SETUP ---
gemini_key = st.sidebar.text_input("Gemini API Key (Wajib)", type="password")

if gemini_key:
    genai.configure(api_key=gemini_key)

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
if st.button("🚀 RACIK PROMPT UNIK & PRESISI"):
    if not gemini_key:
        st.error("⚠️ Masukkan Gemini API Key terlebih dahulu di sidebar!")
    elif not video_ready and not user_topic:
        st.error("⚠️ Masukkan input video atau topik terlebih dahulu!")
    else:
        with st.spinner("Gemini sedang membedah video, melakukan revisi internal, & meracik versi uniknya..."):
            try:
                system_instruction = f"""
                Kamu bertindak sebagai DUA PERAN SEKALIGUS:
                1. [ANALIS VISUAL]: Bedah isi video/topik ini dan buat draf awal.
                2. [SENIOR AI DIRECTOR & PROMPT EDITOR]: Review draf tersebut, modifikasi alur ceritanya minimal 30% agar BEBAS PLAGIAT (tambahkan twist/komedi segar), pertajam instruksi gerakan 8 detik per scene agar tidak patah, dan KUNCI 'Character Anchor' agar tidak berubah wajah/baju.

                DETAIL SPESIFIKASI:
                - Target durasi video: {durasi_pilihan}.
                - Gaya Visual Pilihan: {style_pilihan}.
                
                ATURAN OUTPUT:
                1. Tentukan 1 'CHARACTER ANCHOR' (deskripsi fisik rinci seperti warna baju, gaya rambut, rentang umur, dan atribut wajib).
                2. Tempelkan Gaya Visual '{style_pilihan}' dan 'CHARACTER ANCHOR' tersebut persis sama di awal SETIAP prompt scene.
                3. Setiap SCENE wajib berdurasi 8 DETIK per prompt dengan instruksi gerakan bertahap, slow-motion, dan continuous movement.
                4. Untuk Scene 2 dan seterusnya, sertakan catatan agar pengguna meng-upload screenshot detik ke-8 dari scene sebelumnya sebagai referensi Image-to-Video.
                5. Buatkan Voiceover (VO) Script Bahasa Indonesia yang pas timing-nya per scene untuk CapCut.
                6. Buatkan SEO Pack (Judul Hook, Deskripsi, Hashtag).
                7. Buatkan Kata Kunci / Keywords YouTube (Tags) dipisahkan dengan koma.

                FORMAT OUTPUT MESTI TERPISAH:
                [PROMPT_SECTION]
                (Isi Character Anchor dan Prompt Scene Flow AI 8s per scene di sini)
                [/PROMPT_SECTION]

                [VO_SECTION]
                (Isi Naskah Dubbing Voiceover per scene untuk CapCut di sini)
                [/VO_SECTION]

                [SEO_SECTION]
                (Isi Judul Hook, Deskripsi, dan Hashtag di sini)
                [/SEO_SECTION]

                [TAGS_SECTION]
                (Isi kata kunci/tags dipisahkan koma di sini)
                [/TAGS_SECTION]
                """

                model = genai.GenerativeModel('gemini-3.6-flash')
                
                input_payload = []
                if input_mode == "✍️ Input Topik / Ide Barumu":
                    prompt_input = f"{system_instruction}\n\nIde User:\n{user_topic}"
                    input_payload.append(prompt_input)
                else:
                    uploaded_file = genai.upload_file(video_path)
                    prompt_input = f"{system_instruction}\n\nAnalisis video terlampir. Lakukan bedah visual + revisi director internal untuk menghasilkan versi MODIFIKASI UNIK yang presisi dan bebas plagiat."
                    input_payload = [uploaded_file, prompt_input]

                response = model.generate_content(input_payload)
                raw_text = response.text

                # Parse Response per Section
                prompt_content = raw_text.split("[PROMPT_SECTION]")[1].split("[/PROMPT_SECTION]")[0].strip() if "[PROMPT_SECTION]" in raw_text else raw_text
                vo_content = raw_text.split("[VO_SECTION]")[1].split("[/VO_SECTION]")[0].strip() if "[VO_SECTION]" in raw_text else "Gagal memisahkan VO Script."
                seo_content = raw_text.split("[SEO_SECTION]")[1].split("[/SEO_SECTION]")[0].strip() if "[SEO_SECTION]" in raw_text else "Gagal memisahkan SEO Pack."
                tags_content = raw_text.split("[TAGS_SECTION]")[1].split("[/TAGS_SECTION]")[0].strip() if "[TAGS_SECTION]" in raw_text else "Gagal memisahkan Tags."

                st.success("Racikan Modifikasi Unik & Presisi Berhasil Dibuat!")
                
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
