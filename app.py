import streamlit as st
import os
import json
from google import genai

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="STUDIO AI UGC MR. ZAGREST", 
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
    .seo-card { background: #f0fdf4; border: 2px solid #16a34a; border-radius: 10px; padding: 12px; margin-bottom: 12px; color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class="main-header">
    <div class="main-title">⚡ STUDIO AI UGC REMAKER & SEO</div>
    <div class="sub-title">Powered 100% by Gemini (Vision + Logic + Prompt & YouTube SEO Engine)</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR API CONFIG ---
st.sidebar.markdown("### ⚙️ **GEMINI API CONFIG**")
gemini_key = st.sidebar.text_input("Gemini API Key:", type="password", placeholder="Masukkan API Key Gemini lo di sini...")

client_gemini = None
if gemini_key:
    try:
        client_gemini = genai.Client(api_key=gemini_key.strip())
        st.sidebar.success("✓ Gemini Connected Successfully!")
    except Exception as e:
        st.sidebar.error(f"Gemini Key Error: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 **VISUAL ENGINE**")

style_pilihan = st.sidebar.selectbox(
    "Gaya Visual Target Google Flow:",
    options=[
        "3D Cinematic Animation (Pixar style, soft illumination)",
        "Photorealistic 8K (Cinematic camera, highly detailed textures)",
        "2D Anime Style (Studio Ghibli aesthetic)",
        "Claymation Stop Motion (Textured clay look)"
    ]
)

target_durasi_label = st.sidebar.selectbox(
    "Target Total Durasi Video:",
    options=[
        "16 Detik (2 Scene)",
        "24 Detik (3 Scene)",
        "32 Detik (4 Scene)",
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
    st.session_state.original_summary = ""
    st.session_state.current_story_context = ""

# --- TAHAP 1: GEMINI ANALISIS & STORYBOARD ---
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
        multi_frames = st.file_uploader("Upload Urutan Gambar Adegan:", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        if multi_frames:
            video_ready = True
    elif input_mode == "📁 Upload File Video Referensi":
        uploaded_video = st.file_uploader("Upload Video Referensi (.mp4):", type=["mp4", "mov", "avi"])
        if uploaded_video is not None:
            with open(video_path, "wb") as f:
                f.write(uploaded_video.read())
            video_ready = True
    else:
        user_topic = st.text_area("Tuliskan Urutan Cerita Referensi:", placeholder="Ketik urutan adegan dan objek penting di sini...")
        if user_topic:
            video_ready = True

    st.markdown("---")
    modification_notes = st.text_input("💡 (Opsional) Ide Modifikasi Khusus:", placeholder="Misal: Ubah jadi komedi absurd, ganti latar, dll...")

    if st.button("🚀 PROSES DENGAN GEMINI ENGINE"):
        if not gemini_key:
            st.error("⚠️ Masukkan Gemini API Key di sidebar terlebih dahulu!")
        elif not video_ready:
            st.error("⚠️ Masukkan data referensi terlebih dahulu!")
        else:
            with st.spinner("🤖 Gemini sedang membaca media, meracik cerita baru, dan menyusun storyboard JSON..."):
                try:
                    # STEP 1 & 2 & 3: Gemini menangani semuanya sekaligus secara cerdas
                    master_prompt = f"""
                    Kamu adalah Sutradara AI profesional & Prompt Engineer tingkat mahir untuk Google Flow AI.
                    Tugasmu adalah menganalisis input referensi, lalu meracik ulang cerita agar ANTI-PLAGIAT namun tetap mempertahankan kelucuan/daya tarik aslinya.
                    
                    Catatan Modifikasi Tambahan Dari User: '{modification_notes}'

                    INSTRUKSI UTAMA:
                    1. Identifikasi subjek/karakter utama dan SEMUA objek/properti penting yang dipegang/digunakan (misal: HP, makanan, helm, hewan, dll) agar nanti dikunci ketat.
                    2. Bagi cerita menjadi TEPAT {max_scenes} SCENE (masing-masing 8 detik).
                    3. Berikan output dalam format JSON MURNI tanpa teks pembuka/penutup, dengan struktur berikut:
                    {{
                        "new_concept_summary": "Ringkasan konsep cerita baru yang sudah dimodifikasi",
                        "character_anchor": "Deskripsi fisik subjek DAN objek wajib yang dipegang secara spesifik agar tidak berubah/hilang (anti-morphing)",
                        "scenes": [
                            {{"scene_num": 1, "description": "Deskripsi adegan Scene 1", "vo": "Naskah Voiceover Bahasa Indonesia Scene 1"}},
                            {{"scene_num": 2, "description": "Deskripsi adegan Scene 2", "vo": "Naskah Voiceover Bahasa Indonesia Scene 2"}}
                        ]
                    }}
                    """

                    if input_mode == "✍️ Input Teks Tepat Urutan Cerita":
                        contents = [f"Urutan Cerita Referensi:\n{user_topic}\n\n{master_prompt}"]
                    elif input_mode == "📁 Upload Beberapa Screenshot Urut (Multi-Frame)":
                        imgs = []
                        for idx, img_file in enumerate(multi_frames):
                            p = f"temp_{idx}.jpg"
                            with open(p, "wb") as f:
                                f.write(img_file.read())
                            imgs.append(client_gemini.files.upload(file=p))
                        contents = imgs + [master_prompt]
                    else:
                        vid = client_gemini.files.upload(file=video_path)
                        contents = [vid, master_prompt]

                    response = client_gemini.models.generate_content(model='gemini-2.5-flash', contents=contents)
                    raw_text = response.text

                    clean_json = raw_text.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(clean_json)

                    st.session_state.master_storyboard = parsed["scenes"]
                    st.session_state.character_anchor = parsed["character_anchor"]
                    st.session_state.original_summary = parsed.get("new_concept_summary", "Konsep Hasil Racikan Gemini.")
                    
                    st.session_state.step = 2
                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal memproses dengan Gemini: {e}")

# --- TAHAP 2 S/D SELESAI: EKSEKUSI PROMPT GOOGLE FLOW AI (ANTI-MORPHING) ---
elif 2 <= st.session_state.step <= (max_scenes + 1):
    curr_idx = st.session_state.step - 2
    scene_number = curr_idx + 1

    st.subheader(f"🎬 Eksekusi Scene {scene_number} dari {max_scenes}")
    curr_scene = st.session_state.master_storyboard[curr_idx]

    st.markdown(f"""
    <div class="reconcept-card">
        <b>💡 Ide Konsep Modifikasi (Gemini Brain):</b><br>
        <span>{st.session_state.original_summary}</span>
    </div>
    <div class="story-card">
        <b>🎯 Target Adegan Scene {scene_number}:</b><br>
        <span>{curr_scene['description']}</span>
    </div>
    """, unsafe_allow_html=True)

    if scene_number > 1:
        st.info(f"📸 **Lock Frame System:** Upload screenshot detik terakhir Scene {scene_number - 1} untuk Google Flow AI.")
        last_frame = st.file_uploader(f"Upload Screenshot Detik Terakhir Scene {scene_number - 1}:", type=["png", "jpg", "jpeg"])
    else:
        last_frame = None
        st.info("💡 Scene Pertama. Langsung generate prompt di bawah!")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"🚀 GENERATE PROMPT SCENE {scene_number}"):
            if not gemini_key:
                st.error("API Key belum diset.")
            else:
                start_time = curr_idx * 8
                end_time = (curr_idx + 1) * 8
                
                with st.spinner(f"⚡ Gemini menyusun prompt ketat (Anti-Morphing Objek)..."):
                    try:
                        prompt_spec_prompt = f"""
                        Buatlah prompt video 8 detik dalam Bahasa Inggris untuk Google Flow AI berdasarkan adegan ini: "{curr_scene['description']}".
                        Gaya Visual Target: {style_pilihan}.
                        
                        PERATURAN PENGUNCIAN OBJEK EKSTRIM (ANTI-MORPHING / ANTI-HILANG):
                        1. Karakter & Objek Anchor Utama yang wajib ada dan tidak boleh berubah: {st.session_state.character_anchor}
                        2. TEGASKAN DI PROMPT: Sebutkan objek yang dipegang/digunakan secara konsisten dari awal sampai akhir (misal: 'hands firmly holding the object continuously, no morphing, object never disappears').
                        3. Susunan kalimat: [Subject & Held Object] + [Action/Emotion] + [Environment & Lighting] + [Camera Style].

                        Berikan format output persis seperti ini:
                        [PROMPT_SCENE]
                        (Google Flow Prompt Bahasa Inggris)
                        [/PROMPT_SCENE]

                        [VO_SCENE]
                        {curr_scene['vo']}
                        [/VO_SCENE]
                        """
                        res_gen = client_gemini.models.generate_content(model='gemini-2.5-flash', contents=prompt_spec_prompt)
                        res_text = res_gen.text

                        p_scene = res_text.split("[PROMPT_SCENE]")[1].split("[/PROMPT_SCENE]")[0].strip() if "[PROMPT_SCENE]" in res_text else res_text
                        vo_scene = curr_scene['vo']

                        scene_feed = f"\n\n=== SCENE {scene_number} ({start_time:02d}:00 - {end_time:02d}:00) ===\nGOOGLE FLOW PROMPT:\n{p_scene}\n\nVO SCRIPT:\n{vo_scene}"
                        st.session_state.current_story_context += scene_feed
                        
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

# --- TAHAP AKHIR: AUTOMATIC YOUTUBE SEO PACK ---
else:
    st.balloons()
    st.success(f"🎉 **PROYEK SELESAI!** Seluruh {max_scenes} Scene Siap Digenerate!")

    with st.spinner("🔥 Gemini sedang meracik Judul Clickbait Viral + Deskripsi & Tag SEO YouTube..."):
        try:
            seo_prompt = f"""
            Berdasarkan konsep cerita dan naskah berikut:
            Konsep: {st.session_state.original_summary}
            Detail Context: {st.session_state.current_story_context}

            Buatkan YouTube Shorts/Video SEO Pack dalam Bahasa Indonesia yang sangat menarik, lucu/penasaran, dan ramah algoritma YouTube:
            1. 3 Opsi JUDUL VIRAL (Clickbait emosional, bikin penasaran, pakai emoji).
            2. DESKRIPSI VIDEO (Singkat, menarik, ada keyword SEO, dan call-to-action).
            3. TAG SEO HIGH-VOLUME (Kumpulan tag dipisahkan koma untuk dicopy-paste ke YouTube Studio).
            4. HASHTAG VIRAL (5-8 Hashtag untuk mempercepat FYP).
            """
            seo_res = client_gemini.models.generate_content(model='gemini-2.5-flash', contents=seo_prompt)
            youtube_seo_pack = seo_res.text
        except Exception as e:
            youtube_seo_pack = f"Gagal membuat Paket SEO: {e}"

    st.markdown(f"""
    <div class="seo-card">
        <b>🚀 PAKET SEO YOUTUBE VIRAL / FYP:</b><br>
        <pre style="white-space: pre-wrap; word-wrap: break-word; font-family: inherit;">{youtube_seo_pack}</pre>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📋 Final Master Prompt & Script Output")
    st.text_area("Copy Master Flow Prompts:", value=st.session_state.current_story_context, height=350)

    if st.button("🚀 MULAI PROYEK BARU"):
        st.session_state.step = 1
        st.session_state.master_storyboard = []
        st.session_state.character_anchor = ""
        st.session_state.original_summary = ""
        st.session_state.current_story_context = ""
        st.rerun()
