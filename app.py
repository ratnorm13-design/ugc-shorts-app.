import streamlit as st
import yt_dlp
import os
from google import genai

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="STUDIO AI - UGC Shorts Engine Bang Vtoyz", 
    page_icon="⚡", 
    layout="centered"
)

# --- ADVANCED MODERN CUSTOM CSS ---
st.markdown("""
<style>
    /* Dark Futuristic Background */
    .stApp {
        background: radial-gradient(circle at 50% -20%, #1e1b4b, #0f172a, #020617);
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        color: #f8fafc;
    }

    /* Header Styling */
    .main-header {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem 1rem;
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 2rem;
    }
    
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #a855f7 0%, #ec4899 50%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }

    .sub-title {
        color: #94a3b8;
        font-size: 0.95rem;
        font-weight: 400;
    }

    /* Sidebar Customization */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Glassmorphism Cards for Containers */
    div[data-testid="stVerticalBlock"] > div {
        border-radius: 16px;
    }

    /* Custom Modern Buttons */
    div.stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: #ffffff;
        font-weight: 700;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(168, 85, 247, 0.4);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(168, 85, 247, 0.6);
        background: linear-gradient(135deg, #4f46e5 0%, #9333ea 100%);
        color: #ffffff;
    }

    /* Custom Input Fields */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #a855f7 !important;
        box-shadow: 0 0 10px rgba(168, 85, 247, 0.5) !important;
    }

    /* Radio Buttons & Status Badges */
    .stAlert {
        border-radius: 12px;
        backdrop-filter: blur(10px);
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_allow_html=True)

# --- MODERN HEADER SECTION ---
st.markdown("""
<div class="main-header">
    <div class="main-title">⚡ STUDIO AI UGC SHORTS</div>
    <div class="sub-title">Next-Gen Multi-Brain Continuity Engine • Precision 8s Frame Lock</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR CONFIGURATION ---
st.sidebar.markdown("### ⚙️ **SETTINGS & API**")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", placeholder="Paste AQ Key di sini...")

client = None
if gemini_key:
    clean_key = gemini_key.strip().replace(" ", "_").replace("\n", "").replace("\r", "")
    try:
        client = genai.Client(api_key=clean_key)
        st.sidebar.success("✓ API Key Connected")
    except Exception as e:
        st.sidebar.error(f"Format Key Error: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 **VISUAL ENGINE**")

style_pilihan = st.sidebar.selectbox(
    "Gaya Visual Studio:",
    options=[
        "2D Anime (Studio Ghibli 100% Traditional Hand-Drawn Cel-Shaded Style)",
        "Realistis / Photorealistic (8K Cinematic)",
        "3D Animation (Pixar / Dreamworks Style)",
        "Comic Book / Pop Art (Bold Lines & Halftone)",
        "Claymation (Stop Motion Style)"
    ]
)

target_durasi_label = st.sidebar.selectbox(
    "Target Total Durasi Video:",
    options=[
        "16 Detik (2 Scene)",
        "24 Detik (3 Scene)",
        "32 Detik (4 Scene)",
        "40 Detik (5 Scene)",
        "48 Detik (6 Scene)",
        "56 Detik (7 Scene)"
    ]
)

max_scenes = int(target_durasi_label.split("(")[1].split(" ")[0])

# --- SESSION STATE ---
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.scene_history = []
    st.session_state.current_story_context = ""

# --- DASHBOARD CONTENT ---
if st.session_state.step == 1:
    st.info(f"🎯 **Target Mode Active:** {target_durasi_label} • Tepat 8 Detik / Scene")
    
    input_mode = st.radio(
        "Pilih Sumber Input Awal:",
        ("✍️ Input Topik / Ide Cerita Baru", "📁 Upload File Video Referensi")
    )

    video_path = "temp_video.mp4"
    video_ready = False
    user_topic = ""

    if input_mode == "📁 Upload File Video Referensi":
        uploaded_video = st.file_uploader("Upload Video Referensi (.mp4):", type=["mp4", "mov", "avi"])
        if uploaded_video is not None:
            with open(video_path, "wb") as f:
                f.write(uploaded_video.read())
            video_ready = True
            st.success("✓ Video Referensi Terisi!")
    else:
        user_topic = st.text_area("Deskripsikan Konsep / Ide Cerita Utama:", placeholder="Contoh: Kucing oren koki masak ramen bareng buaya kecil di dapur kayu...")
        if user_topic:
            video_ready = True

    if st.button("🚀 RACIK SCENE 1 (PROMPT FONDASI)"):
        if not gemini_key or not client:
            st.error("⚠️ Masukkan Gemini API Key di sidebar terlebih dahulu!")
        elif not video_ready:
            st.error("⚠️ Masukkan ide cerita atau upload video terlebih dahulu!")
        else:
            with st.spinner("⚡ AI sedang mengunci karakter & merancang Scene 1..."):
                try:
                    system_instruction = f"""
                    Kamu adalah Sutradara & Master Prompt Engineer AI profesional.
                    Tugasmu membuat SCENE 1 (Durasi tepat 8 detik) dari total {max_scenes} scene.
                    
                    GAYA VISUAL WAJIB: {style_pilihan}.
                    
                    Instruksi Khusus:
                    1. Buat 'CHARACTER ANCHOR' yang sangat mendalam (fisik, baju, warna, detail objek) di awal prompt scene.
                    2. Buat Prompt Scene 1 yang sinematik berdurasi 8 detik.
                    3. Buat Naskah Dubbing Voiceover (VO) Bahasa Indonesia berdurasi pas 8 detik.

                    FORMAT OUTPUT KETAT:
                    [SCENE_DESC]
                    (Detail Character Anchor & Prompt Scene 1 - 8 Detik)
                    [/SCENE_DESC]
                    [VO_SCRIPT]
                    (Naskah VO Scene 1)
                    [/VO_SCRIPT]
                    """

                    if input_mode == "✍️ Input Topik / Ide Cerita Baru":
                        full_prompt = f"{system_instruction}\n\nIde Cerita:\n{user_topic}"
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=full_prompt
                        )
                    else:
                        video_file = client.files.upload(file=video_path)
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=[video_file, system_instruction]
                        )

                    raw_text = response.text
                    st.session_state.current_story_context = f"=== SCENE 1 (00:00 - 00:08) ===\n" + raw_text
                    st.session_state.step = 2
                    st.rerun()

                except Exception as e:
                    st.error(f"Error: {e}")

elif 2 <= st.session_state.step <= max_scenes:
    st.subheader(f"🎬 Tahap {st.session_state.step} dari {max_scenes}: Continuity Chain")
    
    st.info(f"📸 **Lock Frame System:** Upload **screenshot detik terakhir Scene {st.session_state.step - 1}** agar wujud & posisi karakter 100% presisi!")

    with st.expander("📜 Lihat Master Script & Prompt Sebelumnya"):
        st.write(st.session_state.current_story_context)

    last_frame = st.file_uploader(
        f"Upload Screenshot Detik Terakhir Scene {st.session_state.step - 1}:", 
        type=["png", "jpg", "jpeg"]
    )
    
    next_action_note = st.text_input("Aksi / Kejadian Lanjutan (Opsional):", placeholder="Misal: Kucingnya kaget lalu buayanya keluar panci...")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"🚀 GENERATE SCENE {st.session_state.step}"):
            if not client:
                st.error("API Key belum terpasang.")
            else:
                start_time = (st.session_state.step - 1) * 8
                end_time = st.session_state.step * 8
                with st.spinner(f"⚡ Menganalisis frame visual & meracik Scene {st.session_state.step}..."):
                    try:
                        continuity_instruction = f"""
                        Kamu adalah Sutradara AI. Ini adalah kelanjutan Scene {st.session_state.step} dari {max_scenes} scene.
                        GAYA VISUAL WAJIB: {style_pilihan}.
                        
                        KONTINUITAS KETAT:
                        1. Analisis GAMBAR SCREENSHOT TERAKHIR yang dilampirkan. Pertahankan bentuk visual, karakter, baju, latar belakang, dan warna 100% konsisten (tanpa style drift).
                        2. Sambungkan adegan ke scene 8 detik berikutnya dengan pergerakan kamera yang mulus (bebas teleportasi).
                        
                        Aksi Tambahan: {next_action_note}

                        FORMAT OUTPUT:
                        [SCENE_DESC]
                        (Prompt Scene {st.session_state.step} 8 detik konsisten gambar)
                        [/SCENE_DESC]
                        [VO_SCRIPT]
                        (Naskah VO Scene {st.session_state.step})
                        [/VO_SCRIPT]
                        """

                        if last_frame is not None:
                            frame_path = "temp_frame.jpg"
                            with open(frame_path, "wb") as f:
                                f.write(last_frame.read())
                            uploaded_img = client.files.upload(file=frame_path)
                            response = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=[uploaded_img, continuity_instruction]
                            )
                        else:
                            response = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=continuity_instruction
                            )

                        raw_text = response.text
                        st.session_state.current_story_context += f"\n\n=== SCENE {st.session_state.step} ({start_time:02d}:00 - {end_time:02d}:00) ===\n" + raw_text
                        st.session_state.step += 1
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error: {e}")

    with col2:
        if st.button("🔄 RESET PROJECT"):
            st.session_state.step = 1
            st.session_state.scene_history = []
            st.session_state.current_story_context = ""
            st.rerun()

    if st.session_state.current_story_context:
        st.markdown("---")
        st.subheader("📜 Current Master Script")
        st.text_area("Live Script Feed:", value=st.session_state.current_story_context, height=300)

elif st.session_state.step > max_scenes:
    st.balloons()
    st.success(f"🎉 **PROJECT COMPLETE!** Semua {max_scenes} Scene ({max_scenes * 8} Detik) Selesai!")
    
    st.subheader("📋 Final Master Package (Siap Ekspor ke CapCut & AI Generator)")
    st.text_area("Copy Master Output:", value=st.session_state.current_story_context, height=450)

    if st.button("🚀 MULAI PROYEK BARU"):
        st.session_state.step = 1
        st.session_state.scene_history = []
        st.session_state.current_story_context = ""
        st.rerun()
