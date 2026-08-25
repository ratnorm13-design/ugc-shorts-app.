import streamlit as st
import yt_dlp
import os
import google.generativeai as genai

# --- PAGE CONFIG ---
st.set_page_config(page_title="Studio AI - UGC Shorts", page_icon="⚡")
st.title("⚡ UGC Shorts Studio AI")
st.caption("Auto-Adaptif Shorts Engine: Meracik Prompt Flow AI + SEO Pack Presisi!")

# --- API KEYS SETUP ---
groq_key = st.sidebar.text_input("Groq API Key", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

if gemini_key:
    genai.configure(api_key=gemini_key)

# --- INPUT METHOD ---
input_mode = st.radio(
    "Metode Input:",
    ("Paste Link Shorts / TikTok / Reels", "Input Topik / Ide Barumu")
)

video_path = "temp_video.mp4"
video_ready = False
user_topic = ""

if input_mode == "Paste Link Shorts / TikTok / Reels":
    url_input = st.text_input("Paste Link Video Viral (YouTube Shorts/TikTok/IG Reels):")
    if url_input and st.button("📥 Download & Bedah Video"):
        with st.spinner("Downloading & menganalisis video..."):
            try:
                ydl_opts = {
                    'format': 'best[ext=mp4]/best',
                    'outtmpl': video_path,
                    'overwrites': True,
                    'quiet': True,
                    'no_warnings': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'nocheckcertificate': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url_input])
                video_ready = True
                st.success("Video berhasil diunduh!")
            except Exception as e:
                st.error(f"Gagal download link: {e}")

else:
    user_topic = st.text_area("Tuliskan Topik / Judul / Deskripsi Singkat Ide Videomu:")
    if user_topic:
        video_ready = True

# --- SELECTBOX DURASI ---
durasi_pilihan = st.selectbox(
    "⏱️ Pilih Target Durasi Video:",
    options=["15 Detik (2 Scene @8s)", "30 Detik (4 Scene @8s)", "60 Detik (8 Scene @8s)"]
)

# --- GENERATE PROMPT ENGINE ---
if st.button("🚀 RACIK PROMPT SHORTS VIRAL"):
    if not gemini_key:
        st.error("⚠️ Masukkan Gemini API Key terlebih dahulu di sidebar!")
    elif not video_ready and not user_topic:
        st.error("⚠️ Silakan download video dari link atau isi ide topik terlebih dahulu!")
    else:
        with st.spinner("Gemini 3.6 Flash sedang meracik prompt 8 detik per scene..."):
            try:
                system_instruction = f"""
                Kamu adalah AI Prompt Generator ahli untuk Google Flow AI.
                Target durasi video: {durasi_pilihan}.
                
                ATURAN RACIK PROMPT PENTING:
                1. Buat setiap SCENE persis untuk durasi 8 DETIK per prompt.
                2. Instruksi gerakan HARUS bertahap, slow-motion, dan continuous movement agar hasil video di Flow AI mulus dan tidak patah-patah.
                3. Jika durasi 15s buat 2 Scene, jika 30s buat 4 Scene, jika 60s buat 8 Scene.
                4. Sertakan gaya animasi [3D Pixar-Dreamworks style animation, vibrant colors, bright sunny lighting].
                
                FORMAT OUTPUT:
                SCENE [Nomor]: (0-8 Detik)
                [PROMPT FLOW AI]: [Style] Deskripsi adegan gerakan halus...
                [ENDING FRAME STATE]: Deskripsi posisi akhir adegan.
                """

                # MODEL RESMI GEMINI 3.6 FLASH
                model = genai.GenerativeModel('gemini-3.6-flash')
                
                if input_mode == "Input Topik / Ide Barumu":
                    prompt_input = f"{system_instruction}\n\nBuatkan berdasarkan ide berikut:\n{user_topic}"
                    response = model.generate_content(prompt_input)
                else:
                    uploaded_file = genai.upload_file(video_path)
                    response = model.generate_content([uploaded_file, system_instruction])

                st.subheader("(Durasi Adaptif - 8s per Scene)")
                st.text_area("Copy Seluruh Scene Prompts:", value=response.text, height=400)
                st.success("Prompt berhasil diracik!")

            except Exception as e:
                st.error(f"Gagal meracik prompt: {e}")
