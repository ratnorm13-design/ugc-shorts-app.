import streamlit as st
import os
import cv2
import yt_dlp
from groq import Groq
from google import genai
from google.genai import types

st.set_page_config(page_title="UGC Shorts Studio AI", page_icon="⚡", layout="wide")

st.title("⚡ UGC Shorts Studio AI")
st.caption("Auto-Adaptif Shorts Engine: Meracik Prompt Flow AI + SEO Pack Presisi Sesuai Durasi Link!")

# --- SIDEBAR: CONFIG & API KEYS ---
with st.sidebar:
    st.header("⚙️ Pengaturan & API Keys")
    groq_key = st.text_input("Groq API Key", type="password")
    gemini_key = st.text_input("Gemini API Key", type="password")
    
    st.markdown("---")
    content_type = st.selectbox(
        "🎭 Target & Vibe Konten",
        ["Pemuda / Gen Z (Relatable, Meme, Plot Twist)", "Anak-Anak (Ceria, Ekspresif, Warna Bright)", "Lagu / Musik Shorts Viral"]
    )
    character_style = st.selectbox(
        "👤 Style Visual Karakter",
        ["Anak Muda Cowok Casual (Gen Z)", "Anak Muda Cewek Casual (Gen Z)", "Karakter Kartun / 3D Animated Lucu"]
    )

# --- MAIN INPUT ---
input_mode = st.radio("Metode Input:", ["Paste Link Shorts / TikTok / Reels", "Input Topik / Ide Barumu"], horizontal=True)

video_path = "temp_video.mp4"
audio_path = "temp_audio.m4a"
video_ready = False
user_topic = ""

if input_mode == "Paste Link Shorts / TikTok / Reels":
    url_input = st.text_input("Paste Link Video Viral (YouTube Shorts/TikTok/IG Reels):")
    if url_input and st.button("📥 Download & Bedah Video"):
        with st.spinner("Downloading & menganalisis durasi video..."):
            try:
                ydl_opts = {
                    'format': 'worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst',
                    'outtmpl': video_path,
                    'overwrites': True
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url_input])
                video_ready = True
            except Exception as e:
                st.error(f"Gagal download link: {e}")
else:
    user_topic = st.text_area("Tuliskan Ide / Topik Shorts:", "Contoh: Ekspresi kaget pas nemu makanan unik")
    if user_topic:
        video_ready = True

# --- PROCESS ENGINE ---
if video_ready and st.button("🚀 RACIK PROMPT SHORTS VIRAL", type="primary"):
    if not groq_key or not gemini_key:
        st.error("⚠️ Masukkan Groq Key dan Gemini Key di menu Sidebar terlebih dahulu!")
    else:
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()

            transcript_text = "N/A"
            captured_images = []

            if input_mode == "Paste Link Shorts / TikTok / Reels" and os.path.exists(video_path):
                status_text.text("1/3 Extract Visual & Frame Video...")
                progress_bar.progress(30)
                cap = cv2.VideoCapture(video_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
                frames_to_capture = [int(total_frames * 0.15), int(total_frames * 0.5), int(total_frames * 0.85)]
                for idx, frame_num in enumerate(frames_to_capture):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                    ret, frame = cap.read()
                    if ret:
                        frame_jpg = f"frame_{idx}.jpg"
                        cv2.imwrite(frame_jpg, frame)
                        captured_images.append(frame_jpg)
                cap.release()

                os.system(f"ffmpeg -y -i {video_path} -vn -acodec copy {audio_path}")
                if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                    try:
                        groq_client = Groq(api_key=groq_key)
                        with open(audio_path, "rb") as file:
                            transcribe = groq_client.audio.transcriptions.create(
                                file=(file.name, file.read()), model="whisper-large-v3"
                            )
                        transcript_text = transcribe.text
                    except: pass
            else:
                progress_bar.progress(30)
                transcript_text = f"Ide Konten dari User: {user_topic}"

            status_text.text("2/3 AI Meracik Prompt Shorts Adaptif...")
            progress_bar.progress(70)

            gemini_client = genai.Client(api_key=gemini_key)

            system_instruction = f"""
            Kamu adalah AI Specialist Shorts/TikTok Viral untuk Audiens Anak-Anak & Pemuda.
            Gaya Konten: {content_type}
            Karakter Utama: {character_style}

            ATURAN DURASI & SCENE (ADAPTIF SHORTS):
            1. Analisis ritme dan durasi dari video/transkrip referensi yang diberikan.
            2. Pecah alur video menjadi urutan Scene (Scene 1, Scene 2, dst) yang PRESISI MENYESUAIKAN durasi video asli. 
               - Jika video asli pendek (misal ~15 detik) -> Buat 2-3 Scene.
               - Jika video asli sedang (misal ~30-60 detik) -> Buat 4-6 Scene.
            3. Pastikan transisi antar dua scene menyambung rapi dengan format: 'STARTING FROM [PREVIOUS SCENE ENDING STATE]'.
            4. Gunakan Bahasa Inggris teknis untuk Prompt Flow AI, dan Bahasa Indonesia santai/lucu untuk Voiceover/Lirik.

            Format Output Wajib Rapi:

            === GLOBAL CHARACTER & VISUAL ANCHOR ===
            [Deskripsi fisik detail karakter & style visual yang wajib dipaste di tiap prompt Flow AI]

            === SCRIPT / VOICEOVER FULL ===
            [Tulis teks naskah / narasi voiceover penuh untuk dibaca / direkam]

            === FLOW AI SHORTS SCENE PROMPTS ===
            [Daftar Scene berurutan sesuai durasi asli]
            Format Per Scene:
            SCENE X:
            [PROMPT FLOW AI]: [Master Anchor] + [Aksi & Visual Scene]
            [ENDING FRAME STATE]: [Posisi & ekspresi karakter di akhir scene]

            === SEO PACK VIRAL ===
            [TITLE COVER]: [Judul Menarik / Hook Teks]
            [CAPTION SEO]: [Caption Youtube/TikTok memancing interaksi]
            [HASHTAGS & TAGS]: [Hashtags & Kata Kunci SEO]
            """

            contents_payload = [f"Input Data/Transkrip Video Asli: {transcript_text}"]
            for img_path in captured_images:
                with open(img_path, "rb") as img_file:
                    contents_payload.append(types.Part.from_bytes(data=img_file.read(), mime_type="image/jpeg"))

            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents_payload,
                config=types.GenerateContentConfig(system_instruction=system_instruction)
            )

            result_text = response.text

            status_text.text("3/3 Selesai!")
            progress_bar.progress(100)
            status_text.empty()
            progress_bar.empty()
            st.success("🎉 Prompt Shorts Berhasil Dibuat!")

            tab1, tab2, tab3 = st.tabs(["🎬 Multi-Scene Prompts", "🎙️ Naskah / Voiceover", "🚀 SEO Pack Viral"])

            with tab1:
                st.subheader("📌 Flow AI Scene Sequence (Durasi Adaptif)")
                if "=== FLOW AI SHORTS SCENE PROMPTS ===" in result_text:
                    scene_content = result_text.split("=== FLOW AI SHORTS SCENE PROMPTS ===")[1].split("=== SEO PACK VIRAL ===")[0]
                    st.text_area("Copy Seluruh Scene Prompts:", value=scene_content, height=450)

            with tab2:
                st.subheader("🎙️ Naskah Suara / Voiceover Script")
                if "=== SCRIPT / VOICEOVER FULL ===" in result_text:
                    script_content = result_text.split("=== SCRIPT / VOICEOVER FULL ===")[1].split("=== FLOW AI SHORTS SCENE PROMPTS ===")[0]
                    st.text_area("Copy Script Suara:", value=script_content, height=300)

            with tab3:
                st.subheader("📈 Social Media SEO Pack")
                if "=== SEO PACK VIRAL ===" in result_text:
                    seo_content = result_text.split("=== SEO PACK VIRAL ===")[1]
                    st.text_area("Copy Title, Caption & Tags:", value=seo_content, height=250)

            for img in captured_images:
                if os.path.exists(img): os.remove(img)
            if os.path.exists(video_path): os.remove(video_path)
            if os.path.exists(audio_path): os.remove(audio_path)

        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {str(e)}")
