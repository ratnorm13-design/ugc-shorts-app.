import streamlit as st
import os
import json
from google import genai

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="STUDIO AI - Google Flow AI UGC Engine", 
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
    .reconcept-card { background: #fef2f2; border: 2px solid #dc2626; border-radius: 10px; padding: 12px; margin-bottom: 12px; color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class="main-header">
    <div class="main-title">⚡ STUDIO AI UGC SHORTS</div>
    <div class="sub-title">Google Flow AI Optimized • Re-Conceptor</div>
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
st.sidebar.markdown("### 🎨 **VISUAL ENGINE (FLOW AI FOCUS)**")

style_pilihan = st.sidebar.selectbox(
    "Gaya Visual Target Google Flow:",
    options=[
        "3D Cinematic Animation (Pixar/Illumination style, soft lighting)",
        "Photorealistic 8K (Cinematic lighting, depth of field)",
        "2D Anime Style (Studio Ghibli aesthetic, hand-drawn look)",
        "Claymation Stop Motion (Textured clay, tactile look)"
    ]
)

target_durasi_label = st.sidebar.selectbox(
    "Target Total Durasi Video:",
    options=[
        "32 Detik (4 Scene)",
        "40 Detik (5 Scene)",
        "48 Detik (6 Scene)",
        "24 Detik (3 Scene)",
        "16 Detik (2 Scene)"
    ]
)

max_scenes = int(target_durasi_label.split("(")[1].split(" ")[0])

# --- STATE MANAGEMENT ---
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.master_storyboard = []
    st.session_state.character_anchor = ""
    st.session_state.original_summary = ""
    st.session_state.current_story_context = ""

# --- TAHAP 1: ANALISIS & OPTIMASI FLOW AI ---
if st.session_state.step == 1:
    st.info(f"🎯 **Target Mode:** {target_durasi_label} (8 Detik per Scene)")
    
    input_mode = st.radio(
        "Pilih Sumber Input Referensi:",
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
            "Tuliskan Urutan Cerita Referensi:", 
            placeholder="Scene 1: Kucing Oranye memasukkan bom ke mulut buaya...\nScene 2: Kucing membawa buaya dalam gerobak...\nScene 3: Babi naik motor datang..."
        )
        if user_topic:
            video_ready = True

    st.markdown("---")
    modification_notes = st.text_input("💡 (Opsional) Ide Modifikasi Khusus:", placeholder="Misal: Ubah jadi komedi sci-fi, atau ganti buaya jadi komodo...")

    if st.button("🚀 ANALISIS & GENERATE MASTER STORYBOARD"):
        if not gemini_key or not client:
            st.error("⚠️ Masukkan Gemini API Key di sidebar!")
        elif not video_ready:
            st.error("⚠️ Masukkan data/gambar/video referensi terlebih dahulu!")
        else:
            with st.spinner("⚡ Menganalisis & memecah scene secara berurutan..."):
                try:
                    reconcept_prompt = f"""
                    Kamu adalah Prompt Engineer Spesialis GOOGLE FLOW AI & Master Director.
                    
                    TUGAS UTAMA:
                    1. Bedah urutan adegan dari referensi dari awal sampai akhir.
                    2. Modifikasi cerita agar TIDAK PLAGIAT tapi tetap mempertahankan tempo lucu/menariknya. Catatan modifikasi: '{modification_notes}'.
                    3. Buat 'character_anchor' berupa deskripsi fisik rinci untuk Google Flow AI dalam Bahasa Inggris.
                    4. Bagi cerita secara presisi menjadi TEPAT {max_scenes} SCENE BERURUTAN (dari Scene 1 sampai Scene {max_scenes}).

                    STRUKTUR PROMPT KHUSUS GOOGLE FLOW AI:
                    - Gunakan Bahasa Inggris deskriptif yang lugas.
                    - Susun kalimat: [Main Subject & Visual Details] + [Action/Movement] + [Environment & Lighting] + [Camera Shot].

                    Format JSON Output persis berikut tanpa teks lain:
                    {{
                        "new_concept_summary": "Ringkasan konsep racikan baru",
                        "character_anchor": "Chubby orange tabby cat with round face. Fat pink pig wearing aviator goggles.",
                        "scenes": [
                            {{"scene_num": 1, "description": "Deskripsi adegan Scene 1", "prompt": "Google Flow Prompt Scene 1 (English)", "vo": "Voiceover Scene 1 (Indo)"}},
                            {{"scene_num": 2, "description": "Deskripsi adegan Scene 2", "prompt": "Google Flow Prompt Scene 2 (English)", "vo": "Voiceover Scene 2 (Indo)"}}
                        ]
                    }}
                    """

                    if input_mode == "✍️ Input Teks Tepat Urutan Cerita":
                        full_content = [f"{reconcept_prompt}\n\nTeks Cerita Referensi:\n{user_topic}"]
                    elif input_mode == "📁 Upload Beberapa Screenshot Urut (Multi-Frame)":
                        imgs = []
                        for idx, img_file in enumerate(multi_frames):
                            path = f"temp_frame_{idx}.jpg"
                            with open(path, "wb") as f:
                                f.write(img_file.read())
                            imgs.append(client.files.upload(file=path))
                        full_content = imgs + [reconcept_prompt]
                    else:
                        vid = client.files.upload(file=video_path)
                        full_content = [vid, reconcept_prompt]

                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=full_content
                    )

                    clean_json = response.text.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(clean_json)

                    st.session_state.master_storyboard = parsed["scenes"]
                    st.session_state.character_anchor = parsed["character_anchor"]
                    st.session_state.original_summary = parsed.get("new_concept_summary", "Konsep Baru Berhasil Diracik.")
                    
                    # MULAI DARI SCENE 1
                    st.session_state.step = 2  
                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal memproses prompt: {e}")

# --- EKSEKUSI BERTAHAP PER SCENE (MULAI DARI SCENE 1) ---
elif 2 <= st.session_state.step <= (max_scenes + 1):
    curr_idx = st.session_state.step - 2
    scene_number = curr_idx + 1

    st.subheader(f"🎬 Eksekusi Scene {scene_number} dari {max_scenes}")

    curr_scene = st.session_state.master_storyboard[curr_idx]

    st.markdown(f"""
    <div class="reconcept-card">
        <b>💡 Ide Konsep Modifikasi Terkunci:</b><br>
        <span>{st.session_state.original_summary}</span>
    </div>
    <div class="story-card">
        <b>🎯 Target Adegan Scene {scene_number} (Hasil Remake):</b><br>
        <span>{curr_scene['description']}</span>
    </div>
    """, unsafe_allow_html=True)

    if scene_number > 1:
        st.info(f"📸 **Lock Frame System:** Upload screenshot detik terakhir Scene {scene_number - 1} untuk Google Flow AI.")
        last_frame = st.file_uploader(
            f"Upload Screenshot Detik Terakhir Scene {scene_number - 1}:", 
            type=["png", "jpg", "jpeg"]
        )
    else:
        last_frame = None
        st.info("💡 Ini adalah Scene Pertama. Langsung klik tombol di bawah untuk menghasilkan prompt Google Flow AI.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"🚀 GENERATE PROMPT SCENE {scene_number}"):
            if not client:
                st.error("API Key belum diset.")
            else:
                start_time = curr_idx * 8
                end_time = (curr_idx + 1) * 8
                
                with st.spinner(f"⚡ Meracik Google Flow Prompt Scene {scene_number}..."):
                    try:
                        flow_prompt_rules = f"""
                        Kamu adalah Google Flow AI Prompt Optimizer.
                        Buat prompt 8 detik Bahasa Inggris untuk Google Flow AI berdasarkan adegan:
                        "{curr_scene['description']}"

                        GAYA VISUAL TARGET: {style_pilihan}.

                        ATURAN UTAMA GOOGLE FLOW AI:
                        1. Gunakan deskripsi fisik karakter ini secara konsisten:
                           {st.session_state.character_anchor}
                        2. Jika ada screenshot terlampir, sinkronkan pencahayaan, jenis lensa, dan tekstur subjek dengan screenshot tersebut.
                        3. Susun prompt agar Flow AI tidak bingung: sebutkan [Subject], [Action], [Environment], lalu [Camera/Style].

                        FORMAT RESPONS:
                        [PROMPT_SCENE]
                        (Google Flow AI Optimized English Prompt)
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
                                contents=[uploaded_img, flow_prompt_rules]
                            )
                        else:
                            res = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=flow_prompt_rules
                            )

                        raw_text = res.text
                        p_scene = raw_text.split("[PROMPT_SCENE]")[1].split("[/PROMPT_SCENE]")[0].strip() if "[PROMPT_SCENE]" in raw_text else raw_text
                        vo_scene = raw_text.split("[VO_SCENE]")[1].split("[/VO_SCENE]")[0].strip() if "[VO_SCENE]" in raw_text else "Naskah VO."

                        # Simpan ke feed
                        scene_feed = f"\n\n=== SCENE {scene_number} ({start_time:02d}:00 - {end_time:02d}:00) ===\nGOOGLE FLOW PROMPT:\n{p_scene}\n\nVO SCRIPT:\n{vo_scene}"
                        st.session_state.current_story_context += scene_feed
                        
                        # Naik ke scene berikutnya
                        st.session_state.step += 1
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error: {e}")

    with col2:
        if st.button("🔄 RESET PROJECT"):
            st.session_state.step = 1
            st.session_state.master_storyboard = []
            st.session_state.character_anchor = ""
            st.session_state.original_summary = ""
            st.session_state.current_story_context = ""
            st.rerun()

    if st.session_state.current_story_context:
        st.markdown("---")
        st.subheader("📜 Live Output Master Feed")
        st.text_area("Script & Flow Prompt Feed:", value=st.session_state.current_story_context, height=250)

else:
    st.balloons()
    st.success(f"🎉 **PROYEK GOOGLE FLOW SELESAI!** Seluruh {max_scenes} Scene Siap Digenerate!")
    
    st.subheader("📋 Final Master Output (Siap Paste ke Google Flow AI)")
    st.text_area("Copy Master Output:", value=st.session_state.current_story_context, height=450)

    if st.button("🚀 MULAI PROYEK BARU"):
        st.session_state.step = 1
        st.session_state.master_storyboard = []
        st.session_state.character_anchor = ""
        st.session_state.original_summary = ""
        st.session_state.current_story_context = ""
        st.rerun()
