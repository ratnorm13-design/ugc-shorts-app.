import streamlit as st
import yt_dlp
import os
import google.generativeai as genai
from groq import Groq

# --- PAGE CONFIG ---
st.set_page_config(page_title="Studio AI - UGC Shorts Engine", page_icon="⚡", layout="centered")
st.title("⚡ UGC Shorts Studio AI")
st.caption("Auto-Adaptif Shorts Engine: Prompt Flow AI + VO CapCut Script + SEO Pack Presisi!")

# --- API KEYS SETUP ---
groq_key = st.sidebar.text_input("Groq API Key (Untuk Transkrip Audio)", type="password")
gemini_key = st.sidebar.text_input("Gemini API Key (Wajib)", type="password")

if gemini_key:
    genai.configure(api_key=gemini_key)

# --- INPUT METHOD ---
input_mode = st.radio(
    "Metode Input:",
    ("Paste Link Shorts / TikTok / Reels", "Input Topik / Ide Barumu")
)

video_path = "temp_video.mp4"
audio_path = "temp_audio.m4a"
video_ready = False
user_topic = ""
transcript_text = ""

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
                
                # Ekstrak Audio untuk Groq (Jika Key Ada)
                if groq_key:
                    st.info("Mengakses Groq Whisper untuk ekstraksi percakapan audio...")
                    audio_opts = {
                        'format': 'm4a/bestaudio/best',
                        'outtmpl': audio_path,
                        'overwrites': True,
                        'quiet': True,
                    }
                    with yt_dlp.YoutubeDL(audio_opts) as ydl_audio:
                        ydl_audio.download([url_input])
                    
                    client_groq = Groq(api_key=groq_key)
                    with open(audio_path, "rb") as file:
                        transcription = client_groq.audio.transcriptions.create(
                            file=(audio_path, file.read()),
                            model="whisper-large-v3",
                            response_format="text",
                            language="id"
                        )
                    transcript_text = str(transcription)
                    st.success("Audio berhasil ditranskrip oleh Groq!")

                video_ready = True
                st.success("Video berhasil diunduh & siap diracik!")
            except Exception as e:
                st.error(f"Gagal memproses video: {e}")

else:
    user_topic = st.text_area("Tuliskan Topik / Judul / Deskripsi Singkat Ide Videomu:")
    if user_topic:
        video_ready = True

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
        "Claymation (Stop Motion Style)"
    ]
)

# --- GENERATE PROMPT ENGINE ---
if st.button("🚀 RACIK PROMPT SHORTS VIRAL"):
    if not gemini_key:
        st.error("⚠️ Masukkan Gemini API Key terlebih dahulu di sidebar!")
    elif not video_ready and not user_topic:
        st.error("⚠️ Silakan download video dari link atau isi ide topik terlebih dahulu!")
    else:
        with st.spinner("Gemini 3.6 Flash sedang meracik prompt, VO Script, dan SEO Pack..."):
            try:
                system_instruction = f"""
                Kamu adalah AI Prompt Generator dan Content Creator profesional khusus Shorts/TikTok.
                Target durasi video: {durasi_pilihan}.
                Gaya Visual Pilihan: {style_pilihan}.
                
                ATURAN KONSISTENSI & OUTCOME:
                1. Tentukan 1 'CHARACTER ANCHOR' (deskripsi fisik rinci seperti warna baju, gaya rambut, rentang umur, dan atribut wajib).
                2. Tempelkan Gaya Visual '{style_pilihan}' dan 'CHARACTER ANCHOR' tersebut persis sama di awal SETIAP prompt scene.
                3. Setiap SCENE wajib berdurasi 8 DETIK per prompt dengan instruksi gerakan bertahap, slow-motion, dan continuous movement.
                4. Untuk Scene 2 dan seterusnya, beri instruksi agar pengguna meng-upload screenshot detik ke-8 dari scene sebelumnya sebagai referensi Image-to-Video.
                5. Buatkan Voiceover (VO) Script Bahasa Indonesia yang pas timing-nya per scene untuk CapCut.
                6. Buatkan SEO Pack berisi Judul Hook Viral, Deskripsi, dan Hashtag.

                PISAHKAN JAWABANMU DENGAN FORMAT TAG BERIKUT:
                [PROMPT_SECTION]
                (Isi Character Anchor dan Prompt Scene Flow AI 8s per scene di sini)
                [/PROMPT_SECTION]

                [VO_SECTION]
                (Isi Naskah Dubbing Voiceover per scene untuk CapCut di sini)
                [/VO_SECTION]

                [SEO_SECTION]
                (Isi Judul Hook, Deskripsi, dan Hashtag di sini)
                [/SEO_SECTION]
                """

                model = genai.GenerativeModel('gemini-3.6-flash')
                
                input_payload = []
                if input_mode == "Input Topik / Ide Barumu":
                    prompt_input = f"{system_instruction}\n\nIde User:\n{user_topic}"
                    input_payload.append(prompt_input)
                else:
                    uploaded_file = genai.upload_file(video_path)
                    prompt_input = f"{system_instruction}\n\nHasil Transkrip Audio Groq:\n{transcript_text}"
                    input_payload = [uploaded_file, prompt_input]

                response = model.generate_content(input_payload)
                raw_text = response.text

                # Parse Response per Section
                prompt_content = raw_text.split("[PROMPT_SECTION]")[1].split("[/PROMPT_SECTION]")[0].strip() if "[PROMPT_SECTION]" in raw_text else raw_text
                vo_content = raw_text.split("[VO_SECTION]")[1].split("[/VO_SECTION]")[0].strip() if "[VO_SECTION]" in raw_text else "Gagal memisahkan VO Script."
                seo_content = raw_text.split("[SEO_SECTION]")[1].split("[/SEO_SECTION]")[0].strip() if "[SEO_SECTION]" in raw_text else "Gagal memisahkan SEO Pack."

                st.success("Racikan Berhasil Dibuat!")
                
                # TAMPILAN BERDASARKAN TAB (LEBIH RAPI & MENGHINDARI SALAH COPY)
                tab1, tab2, tab3 = st.tabs(["🎬 Prompt Flow AI", "🎙️ VO Script CapCut", "🚀 SEO Pack"])
                
                with tab1:
                    st.subheader("Prompt Scene Flow AI (8s/Scene)")
                    st.text_area("Copy Prompt Flow AI:", value=prompt_content, height=400)
                
                with tab2:
                    st.subheader("Naskah Dubbing Voiceover")
                    st.text_area("Copy VO Script:", value=vo_content, height=300)
                    
                with tab3:
                    st.subheader("SEO Judul & Hashtag")
                    st.text_area("Copy SEO Pack:", value=seo_content, height=300)

            except Exception as e:
                st.error(f"Gagal meracik prompt: {e}")
