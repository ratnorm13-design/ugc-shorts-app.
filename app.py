import streamlit as st
import yt_dlp
import os
import json
from google import genai

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="STUDIO AI - Story Tracker UGC Engine", 
    page_icon="⚡", 
    layout="centered"
)

# --- CLEAN LIGHT MODE CSS (Background Putih, Teks Hitam, Aksen Merah/Biru) ---
st.markdown("""
<style>
    /* Background Utama Putih Bersih */
    .stApp {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    /* Header Utama */
    .main-header {
        text-align: center;
        padding: 1.5rem 1rem;
        background: #f1f5f9;
        border-radius: 12px;
        border: 2px solid #cbd5e1;
        margin-bottom: 1.5rem;
    }
    .main-title {
        font-size: 1.8rem;
        font-weight: 900;
        color: #dc2626 !important; /* Merah */
        margin-bottom: 0.3rem;
    }
    .sub-title {
        color: #1e293b !important;
        font-size: 0.85rem;
        font-weight: 700;
    }

    /* SEMUA TEKS, LABEL, DAN PARAGRAF DIJADIKAN HITAM JELAS */
    label, p, span, div, .stMarkdown, .stRadio label, .stTextInput label, .stSelectbox label, .stFileUploader label {
        color: #000000 !important;
        font-weight: 700 !important;
    }

    /* Sidebar Terang */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 2px solid #cbd5e1;
        min-width: 85vw !important;
    }

    /* Tombol Utama (Merah Menyala dengan Teks Putih) */
    div.stButton > button {
        width: 100%;
        background: #dc2626 !important; /* Merah */
        color: #ffffff !important;
        font-weight: 900 !important;
        border: 2px solid #000000 !important;
        padding: 0.8rem 1.5rem;
        border-radius: 10px;
        text-transform: uppercase;
        font-size: 1rem !important;
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
    }
    div.stButton > button:hover {
        background: #b91c1c !important;
    }

    /* Input, Textarea, & Selectbox (Background Putih, Border Hitam Tebal) */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background-color: #ffffff !important;
        border: 2px solid #000000 !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }

    /* Dropdown / Selectbox Menu Pop-over */
    div[data-baseweb="select"] ul, 
    ul[data-baseweb="menu"], 
    div[data-baseweb="popover"] {
        background-color: #ffffff !important;
        border: 2px solid #000000 !important;
    }
    
    li[data-baseweb="option"], 
    div[role="option"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-weight: 700 !important;
    }
    li[data-baseweb="option"]:hover {
        background-color: #2563eb !important; /* Biru saat di-hover */
        color: #ffffff !important;
    }

    /* Card Status Storyboard (Aksen Biru) */
    .story-card {
        background: #eff6ff;
        border: 2px solid #2563eb;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 12px;
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER SECTION ---
st.markdown("""
<div class="main-header">
    <div class="main-title">⚡ STUDIO AI UGC SHORTS</div>
    <div class="sub-title">Master Storyboard Tracker • Automatic Narrative Continuity Engine</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR CONFIGURATION ---
st.sidebar.markdown("### ⚙️ **SETTINGS & API**")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", placeholder="Paste Key di sini...")

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
        "Realistis / Photorealistic (8K Cinematic)",
        "2D Anime (Studio Ghibli 100% Traditional Hand-Drawn)",
        "3D Animation (Pixar / Dreamworks Style)",
        "Comic Book / Pop Art (Bold Lines & Halftone)",
        "Claymation (Stop Motion Style)"
    ]
)

target_durasi_label = st.sidebar.selectbox(
    "Target Total Durasi Video:",
    options=[
        "32 Detik (4 Scene)",
        "16 Detik (2 Scene)",
        "24 Detik (3 Scene)",
        "40 Detik (5 Scene)",
        "48 Detik (6 Scene)",
        "56 Detik (7 Scene)"
    ]
)

max_scenes = int(target_durasi_label.split("(")[1].split(" ")[0])

# --- SESSION STATE / DATABASE MEMORY ---
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.master_storyboard = ""
    st.session_state.current_story_context = ""

# --- TAHAP 1: BEDAH CERITA UTAMA & BUAT MASTER STORYBOARD ---
if st.session_state.step == 1:
    st.info(f"🎯 **Target Mode:** {target_durasi_label} (8 Detik per Scene)")
    
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
            st.success("✓ Video Referensi Siap Dibedah!")
    else:
        user_topic = st.text_area(
            "Deskripsikan Alur Cerita Keseluruhan:", 
            placeholder="Contoh: Babi naik motor antar paket sampai rumah kucing -> Babi santai di kursi dipukul wajan oleh kucing -> Babi dibakar/dipanggang -> Babi panggang disajikan di meja makan dimakan kucing..."
        )
        if user_topic:
            video_ready = True

    if st.button("🚀 ANALISIS CERITA & GENERATE MASTER STORYBOARD"):
        if not gemini_key or not client:
            st.error("⚠️ Masukkan Gemini API Key di sidebar!")
        elif not video_ready:
            st.error("⚠️ Masukkan ide cerita atau upload video!")
        else:
            with st.spinner("⚡ AI sedang membedah video & menyusun Master Peta Cerita..."):
                try:
                    storyboard_prompt = f"""
                    Kamu adalah Sutradara Senior. Bedah alur cerita dari input ini dan bagi menjadi TEPAT {max_scenes} SCENE BERURUTAN (masing-masing 8 detik).
                    GAYA VISUAL: {style_pilihan}.

                    Tugasmu:
                    1. Tentukan detail 'CHARACTER ANCHOR' (Karakter utama, baju, warna).
                    2. Buat ringkasan adegan berurutan dari awal sampai akhir cerita agar alurnya TIDAK BERULANG.
                    
                    FORMAT RESPONS HARUS BERIKUT:
                    [MASTER_STORYBOARD]
                    Scene 1: (Adegan awal pembuka)
                    Scene 2: (Adegan konflik/kejadian lanjutan)
                    Scene 3: (Adegan klimaks/aksi)
                    Scene 4: (Adegan penutup/ending)
                    [/MASTER_STORYBOARD]

                    [PROMPT_SCENE_1]
                    (Prompt AI lengkap 8 detik untuk Scene 1 dengan gaya {style_pilihan})
                    [/PROMPT_SCENE_1]

                    [VO_SCENE_1]
                    (Naskah Dubbing VO Scene 1 Indonesia)
                    [/VO_SCENE_1]
                    """

                    if input_mode == "✍️ Input Topik / Ide Cerita Baru":
                        full_input = f"{storyboard_prompt}\n\nIde Cerita User:\n{user_topic}"
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=full_input
                        )
                    else:
                        video_file = client.files.upload(file=video_path)
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=[video_file, storyboard_prompt]
                        )

                    raw_text = response.text

                    # Extract Storyboard
                    storyboard_text = raw_text.split("[MASTER_STORYBOARD]")[1].split("[/MASTER_STORYBOARD]")[0].strip() if "[MASTER_STORYBOARD]" in raw_text else "Gagal meracik storyboard."
                    prompt_s1 = raw_text.split("[PROMPT_SCENE_1]")[1].split("[/PROMPT_SCENE_1]")[0].strip() if "[PROMPT_SCENE_1]" in raw_text else raw_text
                    vo_s1 = raw_text.split("[VO_SCENE_1]")[1].split("[/VO_SCENE_1]")[0].strip() if "[VO_SCENE_1]" in raw_text else "Naskah VO Scene 1."

                    st.session_state.master_storyboard = storyboard_text
                    st.session_state.current_story_context = f"📌 MASTER STORYBOARD ALUR CERITA:\n{storyboard_text}\n\n"
                    st.session_state.current_story_context += f"=== SCENE 1 (00:00 - 00:08) ===\nPROMPT:\n{prompt_s1}\n\nVO SCRIPT:\n{vo_s1}"
                    
                    st.session_state.step = 2
                    st.rerun()

                except Exception as e:
                    st.error(f"Error: {e}")

# --- TAHAP 2 S/D SELESAI ---
elif 2 <= st.session_state.step <= max_scenes:
    st.subheader(f"🎬 Eksekusi Scene {st.session_state.step} dari {max_scenes}")

    st.markdown(f"""
    <div class="story-card">
        <b>📋 Master Storyboard Alur Cerita:</b><br>
        <pre style="white-space: pre-wrap; font-size: 0.85rem; color: #1e3a8a;">{st.session_state.master_storyboard}</pre>
    </div>
    """, unsafe_allow_html=True)

    st.info(f"📸 **Lock Frame System:** Upload **screenshot detik terakhir Scene {st.session_state.step - 1}** agar AI memadukan gambar fisik dengan Master Storyboard Scene {st.session_state.step}!")

    last_frame = st.file_uploader(
        f"Upload Screenshot Detik Terakhir Scene {st.session_state.step - 1}:", 
        type=["png", "jpg", "jpeg"]
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"🚀 GENERATE SCENE {st.session_state.step}"):
            if not client:
                st.error("API Key belum diset.")
            else:
                start_time = (st.session_state.step - 1) * 8
                end_time = st.session_state.step * 8
                
                with st.spinner(f"⚡ Menganalisis screenshot + Peta Alur Master Scene {st.session_state.step}..."):
                    try:
                        continuity_prompt = f"""
                        Kamu adalah Sutradara AI. Tugasmu adalah membuat PROMPT SCENE {st.session_state.step} berdurasi 8 detik.
                        GAYA VISUAL: {style_pilihan}.

                        SISTEM KONTINUITAS DUAL-LOCK:
                        1. ACUAN ALUR CERITA (MASTER STORYBOARD):
                           Cek alur cerita berikut ini, buat prompt KHUSUS UNTUK ADEGAN SCENE {st.session_state.step}:
                           {st.session_state.master_storyboard}
                        
                        2. ACUAN VISUAL FISIK:
                           Lihat gambar screenshot terlampir. Samakan persis wujud karakter (bentuk babi, kucing, warna kulit/bulu, dan pakaian) agar 100% konsisten visualnya.

                        PENTING: JANGAN mengulang adegan dari scene sebelumnya! Lanjutkan ke adegan berikutnya sesuai Master Storyboard di atas.

                        FORMAT RESPONS:
                        [PROMPT_SCENE]
                        (Prompt AI Video 8 detik untuk Scene {st.session_state.step})
                        [/PROMPT_SCENE]

                        [VO_SCENE]
                        (Naskah Dubbing VO Scene {st.session_state.step} Indonesia)
                        [/VO_SCENE]
                        """

                        if last_frame is not None:
                            frame_path = "temp_frame.jpg"
                            with open(frame_path, "wb") as f:
                                f.write(last_frame.read())
                            uploaded_img = client.files.upload(file=frame_path)
                            response = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=[uploaded_img, continuity_prompt]
                            )
                        else:
                            response = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=continuity_prompt
                            )

                        raw_text = response.text
                        p_scene = raw_text.split("[PROMPT_SCENE]")[1].split("[/PROMPT_SCENE]")[0].strip() if "[PROMPT_SCENE]" in raw_text else raw_text
                        vo_scene = raw_text.split("[VO_SCENE]")[1].split("[/VO_SCENE]")[0].strip() if "[VO_SCENE]" in raw_text else "Naskah VO."

                        st.session_state.current_story_context += f"\n\n=== SCENE {st.session_state.step} ({start_time:02d}:00 - {end_time:02d}:00) ===\nPROMPT:\n{p_scene}\n\nVO SCRIPT:\n{vo_scene}"
                        st.session_state.step += 1
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error: {e}")

    with col2:
        if st.button("🔄 RESET PROJECT"):
            st.session_state.step = 1
            st.session_state.master_storyboard = ""
            st.session_state.current_story_context = ""
            st.rerun()

    if st.session_state.current_story_context:
        st.markdown("---")
        st.subheader("📜 Live Output Master Feed")
        st.text_area("Script & Prompt Feed:", value=st.session_state.current_story_context, height=300)

elif st.session_state.step > max_scenes:
    st.balloons()
    st.success(f"🎉 **PROYEK SELESAI!** Seluruh {max_scenes} Scene ({max_scenes * 8} Detik) Berhasil Dibuat Berurutan Sesuai Cerita!")
    
    st.subheader("📋 Final Master Output (Siap Pakai untuk CapCut)")
    st.text_area("Copy Master Output:", value=st.session_state.current_story_context, height=450)

    if st.button("🚀 MULAI PROYEK BARU"):
        st.session_state.step = 1
        st.session_state.master_storyboard = ""
        st.session_state.current_story_context = ""
        st.rerun()
