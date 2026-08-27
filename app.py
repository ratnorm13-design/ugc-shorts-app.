import streamlit as st
import json
from google import genai
from google.genai import types

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="STUDIO AI - Gemini 3.6 UGC Remaker & SEO", 
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
    <div class="sub-title">Powered by Gemini 3.6 Flash (Vision + Comedy Logic + SEO Engine)</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR CONFIG ---
st.sidebar.markdown("### ⚙️ **GEMINI API KEY SETUP**")
gemini_key = st.sidebar.text_input("Gemini API Key:", type="password", placeholder="Masukkan API Key Gemini lo di sini...")

client_gemini = None
if gemini_key:
    try:
        client_gemini = genai.Client(api_key=gemini_key.strip())
        st.sidebar.success("✓ Gemini 3.6 Flash Connected")
    except Exception as e:
        st.sidebar.error(f"Gemini Key Error: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 **VISUAL & DURASI**")

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

# --- TAHAP 1: GEMINI 3.6 FLASH ANALISIS & RACIK CERITA ---
if st.session_state.step == 1:
    st.info(f"🎯 **Target Mode:** {target_durasi_label} (Masing-masing 8 Detik)")
    
    input_mode = st.radio(
        "Pilih Sumber Input Referensi:",
        ("✍️ Input Teks Cerita/Adegan Video", "📁 Upload Beberapa Screenshot Urut", "📁 Upload File Video Referensi")
    )

    video_ready = False
    user_topic = ""
    multi_frames = []
    video_path = "temp_video.mp4"

    if input_mode == "📁 Upload Beberapa Screenshot Urut":
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
        user_topic = st.text_area("Tuliskan Cerita Video Asli:", placeholder="Ketik adegan video asli di sini...")
        if user_topic:
            video_ready = True

    st.markdown("---")
    modification_notes = st.text_input("💡 (Opsional) Arahkan Genre Komedi/Cerita:", placeholder="Misal: Buat endingnya komedi absurd, ganti karakter utama, dll...")

    if st.button("🚀 RACIK CERITA SUPER KOCAK & PROMPT"):
        if not gemini_key:
            st.error("⚠️ Masukkan Gemini API Key di sidebar terlebih dahulu!")
        elif not video_ready:
            st.error("⚠️ Masukkan data referensi terlebih dahulu!")
        else:
            with st.spinner("🤖 Gemini 3.6 Flash sedang membedah video & meracik adegan komedi nendang..."):
                try:
                    contents_list = []
                    
                    if input_mode == "✍️ Input Teks Cerita/Adegan Video":
                        contents_list.append(f"Video Reference Text:\n{user_topic}")
                    elif input_mode == "📁 Upload Beberapa Screenshot Urut":
                        for idx, img_file in enumerate(multi_frames):
                            p = f"temp_{idx}.jpg"
                            with open(p, "wb") as f:
                                f.write(img_file.read())
                            contents_list.append(client_gemini.files.upload(file=p))
                    else:
                        vid = client_gemini.files.upload(file=video_path)
                        contents_list.append(vid)

                    system_instruction = f"""
                    Kamu adalah Produser Video Viral & Scriptwriter Komedi Handal.
                    Tugasmu adalah menganalisis media referensi lalu meraciknya menjadi video UGC baru yang JAUH LEBIH LUCU, PENASARAN, DAN NENDANG dibanding video aslinya.

                    INSTRUKSI UTAMA:
                    1. Identifikasi subjek utama DAN semua objek penting yang dipegang/digunakan (HP, helm, panci, barang viral, dll). Kunci objek ini di `character_anchor` agar TIDAK LENTUR / HILANG / MORPHING!
                    2. Jika video asli pendek, TAMBAHKAN adegan komedi/plot twist tak terduga agar durasi pas menjadi TEPAT {max_scenes} SCENE (8 detik per scene, total {max_scenes * 8} detik).
                    3. Buatkan Naskah Voiceover Bahasa Indonesia yang lucu, santai, dan pas ritmenya.
                    4. Catatan user: '{modification_notes}'.
                    """

                    contents_list.append(system_instruction)

                    # Memakai Gemini 3.6 Flash dengan Structured JSON Output
                    response = client_gemini.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=contents_list,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema={
                                "type": "OBJECT",
                                "properties": {
                                    "new_concept_summary": {"type": "STRING"},
                                    "character_anchor": {"type": "STRING"},
                                    "scenes": {
                                        "type": "ARRAY",
                                        "items": {
                                            "type": "OBJECT",
                                            "properties": {
                                                "scene_num": {"type": "INTEGER"},
                                                "description": {"type": "STRING"},
                                                "vo": {"type": "STRING"}
                                            },
                                            "required": ["scene_num", "description", "vo"]
                                        }
                                    }
                                },
                                "required": ["new_concept_summary", "character_anchor", "scenes"]
                            }
                        )
                    )

                    parsed = json.loads(response.text)

                    st.session_state.master_storyboard = parsed["scenes"]
                    st.session_state.character_anchor = parsed["character_anchor"]
                    st.session_state.original_summary = parsed.get("new_concept_summary", "Konsep Komedi Gemini 3.6.")
                    
                    st.session_state.step = 2
                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal memproses dengan Gemini 3.6 Flash: {e}")

# --- TAHAP 2 S/D SELESAI: GENERATE PROMPT KETAT (ANTI-MORPHING) ---
elif 2 <= st.session_state.step <= (max_scenes + 1):
    curr_idx = st.session_state.step - 2
    scene_number = curr_idx + 1

    st.subheader(f"🎬 Eksekusi Scene {scene_number} dari {max_scenes}")
    curr_scene = st.session_state.master_storyboard[curr_idx]

    st.markdown(f"""
    <div class="reconcept-card">
        <b>💡 Konsep Komedi Racikan Gemini 3.6:</b><br>
        <span>{st.session_state.original_summary}</span>
    </div>
    <div class="story-card">
        <b>🎯 Target Adegan Scene {scene_number}:</b><br>
        <span>{curr_scene['description']}</span><br><br>
        <b>🗣️ Voiceover Kocak:</b> <i>"{curr_scene['vo']}"</i>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"🚀 GENERATE PROMPT SCENE {scene_number}"):
            if not gemini_key:
                st.error("API Key belum diset.")
            else:
                start_time = curr_idx * 8
                end_time = (curr_idx + 1) * 8
                
                with st.spinner(f"⚡ Gemini 3.6 menyusun prompt visual 8 detik untuk Google Flow..."):
                    try:
                        prompt_spec_prompt = f"""
                        Buatlah prompt video 8 detik dalam Bahasa Inggris untuk Google Flow AI berdasarkan adegan ini: "{curr_scene['description']}".
                        Gaya Visual Target: {style_pilihan}.
                        
                        PERATURAN PENGUNCIAN OBJEK EKSTRIM (ANTI-MORPHING / ANTI-HILANG):
                        1. Karakter & Objek Anchor Utama yang wajib ada dan tidak boleh berubah: {st.session_state.character_anchor}
                        2. TEGASKAN DI PROMPT: Sebutkan objek yang dipegang/digunakan secara konsisten dari awal sampai akhir (misal: 'hands firmly holding [object] continuously, no morphing, object never disappears').
                        3. Format kalimat: [Subject & Held Object] + [Action/Emotion] + [Environment & Lighting] + [Camera Style].

                        Berikan format output persis seperti ini:
                        [PROMPT_SCENE]
                        (Google Flow Prompt Bahasa Inggris)
                        [/PROMPT_SCENE]
                        """
                        res_gen = client_gemini.models.generate_content(model='gemini-3.6-flash', contents=prompt_spec_prompt)
                        res_text = res_gen.text

                        p_scene = res_text.split("[PROMPT_SCENE]")[1].split("[/PROMPT_SCENE]")[0].strip() if "[PROMPT_SCENE]" in res_text else res_text

                        scene_feed = f"\n\n=== SCENE {scene_number} ({start_time:02d}:00 - {end_time:02d}:00) ===\nGOOGLE FLOW PROMPT:\n{p_scene}\n\nVO SCRIPT:\n{curr_scene['vo']}"
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
        st.subheader("📜 Live Output Feed")
        st.text_area("Script & Flow Prompt Feed:", value=st.session_state.current_story_context, height=250)

# --- TAHAP AKHIR: AUTOMATIC YOUTUBE SEO PACK ---
else:
    st.balloons()
    st.success(f"🎉 **PROYEK SELESAI!** Seluruh {max_scenes} Scene Siap Digenerate!")

    with st.spinner("🔥 Gemini 3.6 meracik Judul Clickbait Viral + Deskripsi & Tag SEO YouTube..."):
        try:
            seo_prompt = f"""
            Berdasarkan konsep cerita dan naskah komedi berikut:
            Konsep: {st.session_state.original_summary}
            Detail Script: {st.session_state.current_story_context}

            Buatkan SEO Pack YouTube Shorts dalam Bahasa Indonesia yang sangat memancing emosi/penasaran/lucu & tembus algoritma:
            1. 3 Opsi JUDUL CLICKBAIT VIRAL (Lucu/Penasaran, pakai emoji menarik).
            2. DESKRIPSI VIDEO (Singkat, menarik, menyisipkan kata kunci pencarian SEO, dan mengajak subscribe/like).
            3. TAG SEO HIGH-VOLUME (Kumpulan kata kunci dipisahkan koma untuk dipaste langsung ke kolom Tags YouTube Studio).
            4. HASHTAG VIRAL (5-8 hashtag populer seperti #Shorts #Lucu #Viral).
            """
            seo_res = client_gemini.models.generate_content(model='gemini-3.6-flash', contents=seo_prompt)
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
