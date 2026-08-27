import streamlit as st
import os
import json
from google import genai

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="STUDIO AI - Story Tracker UGC Engine by Vtoyz", 
    page_icon="⚡", 
    layout="centered"
)

# --- CLEAN LIGHT MODE CSS ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff !important; color: #000000 !important; }
    .main-header { text-align: center; padding: 1.5rem 1rem; background: #f1f5f9; border-radius: 12px; border: 2px solid #cbd5e1; margin-bottom: 1.5rem; }
    .main-title { font-size: 1.8rem; font-weight: 900; color: #dc2626 !important; margin-bottom: 0.3rem; }
    .sub-title { color: #1e293b !important; font-size: 0.85rem; font-weight: 700; }
    label, p, span, div, .stMarkdown, .stRadio label, .stTextInput label, .stSelectbox label, .stFileUploader label { color: #000000 !important; font-weight: 700 !important; }
    section[data-testid="stSidebar"] { background-color: #f8fafc !important; border-right: 2px solid #cbd5e1; min-width: 85vw !important; }
    div.stButton > button { width: 100%; background: #dc2626 !important; color: #ffffff !important; font-weight: 900 !important; border: 2px solid #000000 !important; padding: 0.8rem 1.5rem; border-radius: 10px; text-transform: uppercase; font-size: 1rem !important; }
    .stTextInput input, .stTextArea textarea, .stSelectbox select { background-color: #ffffff !important; border: 2px solid #000000 !important; color: #000000 !important; font-weight: 700 !important; border-radius: 8px !important; }
    .story-card { background: #eff6ff; border: 2px solid #2563eb; border-radius: 10px; padding: 12px; margin-bottom: 12px; color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class="main-header">
    <div class="main-title">⚡ STUDIO AI UGC SHORTS</div>
    <div class="sub-title">Master Storyboard Tracker • Character Anchor & Continuity Engine</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR CONFIG ---
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
        "48 Detik (6 Scene)"
    ]
)

max_scenes = int(target_durasi_label.split("(")[1].split(" ")[0])

# --- STATE MANAGEMENT ---
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.master_storyboard = []
    st.session_state.character_anchor = ""
    st.session_state.current_story_context = ""

# --- TAHAP 1: EKSTRAK KRONOLOGI + CHARACTER ANCHOR ---
if st.session_state.step == 1:
    st.info(f"🎯 **Target Mode:** {target_durasi_label} (8 Detik per Scene)")
    
    input_mode = st.radio(
        "Pilih Sumber Input Awal:",
        ("✍️ Input Teks Tepat Urutan Cerita", "📁 Upload Beberapa Screenshot Urut (Multi-Frame)", "📁 Upload File Video Referensi")
    )

    video_ready = False
    user_topic = ""
    multi_frames = []
    video_path = "temp_video.mp4"

    if input_mode == "📁 Upload Beberapa Screenshot Urut (Multi-Frame)":
        multi_frames = st.file_uploader("Upload Urutan Gambar Adegan (Frame 1, Frame 2, dst):", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        if multi_frames:
            video_ready = True
            st.success(f"✓ {len(multi_frames)} Frame Gambar Berhasil Diload!")
    elif input_mode == "📁 Upload File Video Referensi":
        uploaded_video = st.file_uploader("Upload Video Referensi (.mp4):", type=["mp4", "mov", "avi"])
        if uploaded_video is not None:
            with open(video_path, "wb") as f:
                f.write(uploaded_video.read())
            video_ready = True
            st.success("✓ Video Referensi Siap Dibedah!")
    else:
        user_topic = st.text_area(
            "Tuliskan Urutan Cerita (Wajib Pakai Nomor Kronologis):", 
            placeholder="Scene 1: Kucing Oranye memasukkan bom ke mulut buaya kecil...\nScene 2: Kucing membawa buaya dalam gerobak...\nScene 3: Babi naik motor datang..."
        )
        if user_topic:
            video_ready = True

    if st.button("🚀 ANALISIS CERITA & LOCK CHARACTER ANCHOR"):
        if not gemini_key or not client:
            st.error("⚠️ Masukkan Gemini API Key di sidebar!")
        elif not video_ready:
            st.error("⚠️ Masukkan data/gambar/video referensi terlebih dahulu!")
        else:
            with st.spinner("⚡ Otak Analisis sedang mengunci bentuk visual karakter & cerita..."):
                try:
                    strict_prompt = f"""
                    Kamu adalah Sutradara & AI Script Analyst Komputer. 
                    Tugas utama:
                    1. Buat 'character_anchor': Deskripsi fisik DETAIL & KAKU untuk setiap karakter utama (misal: Kucing Oranye gemuk berbulu realistis, Babi merah muda naik motor pakai helm penerbang, Buaya kecil).
                    2. Ekstrak urutan adegan SECARA KRONOLOGIS DETIK-DEMI-DETIK dari awal hingga akhir.

                    Bagi cerita menjadi TEPAT {max_scenes} SCENE BERURUTAN (Tiap scene 8 detik).
                    Gaya Visual: {style_pilihan}.

                    Format JSON Output persis berikut:
                    {{
                        "character_anchor": "Karakter Kucing: Kucing oranye gemuk berbulu halus realistis, mata cokelat. Karakter Babi: Babi pink chubby gemuk tanpa baju, pakai helm pilot cokelat tua dan kacamata vintage, mengendarai motor klasik merah.",
                        "scenes": [
                            {{"scene_num": 1, "description": "Deskripsi adegan 1", "prompt": "AI Video Prompt Scene 1", "vo": "Voiceover Scene 1"}},
                            {{"scene_num": 2, "description": "Deskripsi adegan 2", "prompt": "AI Video Prompt Scene 2", "vo": "Voiceover Scene 2"}}
                        ]
                    }}
                    """

                    if input_mode == "✍️ Input Teks Tepat Urutan Cerita":
                        full_content = [f"{strict_prompt}\n\nTeks Cerita:\n{user_topic}"]
                    elif input_mode == "📁 Upload Beberapa Screenshot Urut (Multi-Frame)":
                        imgs = []
                        for idx, img_file in enumerate(multi_frames):
                            path = f"temp_frame_{idx}.jpg"
                            with open(path, "wb") as f:
                                f.write(img_file.read())
                            imgs.append(client.files.upload(file=path))
                        full_content = imgs + [strict_prompt]
                    else:
                        vid = client.files.upload(file=video_path)
                        full_content = [vid, strict_prompt]

                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=full_content
                    )

                    clean_json = response.text.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(clean_json)

                    st.session_state.master_storyboard = parsed["scenes"]
                    st.session_state.character_anchor = parsed["character_anchor"]
                    
                    s1 = parsed["scenes"][0]
                    st.session_state.current_story_context = f"📌 CHARACTER ANCHOR (VISUAL LOCK):\n{parsed['character_anchor']}\n\n=== SCENE 1 (00:00 - 00:08) ===\nPROMPT:\n{s1['prompt']}\n\nVO SCRIPT:\n{s1['vo']}"
                    
                    st.session_state.step = 2
                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal membedah kronologi: {e}. Coba jalankan ulang!")

# --- TAHAP 2 S/D SELESAI: PROMPT GENERATION DENGAN DUAL LOCK ---
elif 2 <= st.session_state.step <= max_scenes:
    curr_idx = st.session_state.step - 1
    curr_scene = st.session_state.master_storyboard[curr_idx]

    st.subheader(f"🎬 Eksekusi Scene {st.session_state.step} dari {max_scenes}")

    st.markdown(f"""
    <div class="story-card">
        <b>🎯 Target Adegan Scene {st.session_state.step}:</b><br>
        <span>{curr_scene['description']}</span>
    </div>
    """, unsafe_allow_html=True)

    st.info(f"📸 **Lock Frame System:** Upload screenshot detik terakhir Scene {st.session_state.step - 1} (seperti foto Babi di atas motor).")

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
                start_time = curr_idx * 8
                end_time = (curr_idx + 1) * 8
                
                with st.spinner(f"⚡ Meracik Prompt Scene {st.session_state.step} dengan Character Anchor..."):
                    try:
                        continuity_prompt = f"""
                        Kamu adalah Sutradara AI Video profesional.
                        Buat prompt AI video 8 detik KHUSUS untuk adegan berikut:
                        "{curr_scene['description']}"

                        GAYA VISUAL: {style_pilihan}.

                        ATURAN KONSISTENSI KARAKTER (MANDATORY & STRICT):
                        1. Gunakan panduan visual karakter ini ke dalam deskripsi teks prompt secara mutlak:
                           {st.session_state.character_anchor}
                        2. Jika ada gambar terlampir (seperti screenshot babi), kunci gaya visual 3D/realistis, lingkungan, dan tekstur objek dari gambar tersebut.
                        3. Apabila karakter Kucing atau karakter lain baru muncul kembali di scene ini namun tidak ada di gambar terlampir, GUNAKAN DESKRIPSI TEKS DARI CHARACTER ANCHOR DI ATAS agar bentuknya TIDAK BERUBAH MENJADI KARTUN LAIN!

                        FORMAT RESPONS:
                        [PROMPT_SCENE]
                        (Prompt AI Video 8 detik yang lengkap mengunci detail fisik karakter)
                        [/PROMPT_SCENE]

                        [VO_SCENE]
                        (Naskah Voiceover Bahasa Indonesia)
                        [/VO_SCENE]
                        """

                        if last_frame is not None:
                            frame_path = "temp_frame_step.jpg"
                            with open(frame_path, "wb") as f:
                                f.write(last_frame.read())
                            uploaded_img = client.files.upload(file=frame_path)
                            res = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=[uploaded_img, continuity_prompt]
                            )
                        else:
                            res = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=continuity_prompt
                            )

                        raw_text = res.text
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
            st.session_state.master_storyboard = []
            st.session_state.character_anchor = ""
            st.session_state.current_story_context = ""
            st.rerun()

    if st.session_state.current_story_context:
        st.markdown("---")
        st.subheader("📜 Live Output Master Feed")
        st.text_area("Script & Prompt Feed:", value=st.session_state.current_story_context, height=300)

elif st.session_state.step > max_scenes:
    st.balloons()
    st.success(f"🎉 **PROYEK SELESAI!** Seluruh {max_scenes} Scene Berhasil Dieksekusi!")
    
    st.subheader("📋 Final Master Output (Siap Pakai untuk CapCut / Generator Video)")
    st.text_area("Copy Master Output:", value=st.session_state.current_story_context, height=450)

    if st.button("🚀 MULAI PROYEK BARU"):
        st.session_state.step = 1
        st.session_state.master_storyboard = []
        st.session_state.character_anchor = ""
        st.session_state.current_story_context = ""
        st.rerun()
