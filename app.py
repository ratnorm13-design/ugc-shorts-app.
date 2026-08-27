import streamlit as st
import os
import json
import requests
from google import genai

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="STUDIO AI - Triple Engine UGC Remaker & SEO Viral", 
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
    <div class="main-title">⚡ STUDIO AI UGC REMAKER & SEO VIRAL</div>
    <div class="sub-title">Triple AI Engine (Gemini Vision + DeepSeek Logic + Qwen Flow & YouTube SEO)</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR API CONFIG ---
st.sidebar.markdown("### ⚙️ **TRIPLE ENGINE API KEYS**")
gemini_key = st.sidebar.text_input("1. Gemini API Key (Vision & Scan)", type="password")
openrouter_key = st.sidebar.text_input("2. OpenRouter API Key (DeepSeek & Qwen)", type="password")

client_gemini = None
if gemini_key:
    try:
        client_gemini = genai.Client(api_key=gemini_key.strip())
        st.sidebar.success("✓ Gemini Vision Connected")
    except Exception as e:
        st.sidebar.error(f"Gemini Key Error: {e}")

if openrouter_key:
    st.sidebar.success("✓ DeepSeek & Qwen Connected")

# --- HELPER FUNCTION FOR OPENROUTER (DEEPSEEK & QWEN) ---
def call_openrouter(model_name, system_prompt, user_prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openrouter_key.strip()}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    res_data = response.json()
    return res_data['choices'][0]['message']['content']

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

# --- TAHAP 1: TRIPLE AI COLLABORATION (RE-CONCEPT & UNIVERSAL OBJECT ANCHOR) ---
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
    modification_notes = st.text_input("💡 (Opsional) Ide Modifikasi Khusus:", placeholder="Misal: Ubah jadi komedi absurd, ganti karakter, dll...")

    if st.button("🚀 ANALISIS & PROSES TRIPLE AI ENGINE"):
        if not gemini_key or not openrouter_key:
            st.error("⚠️ Masukkan Gemini Key dan OpenRouter Key di sidebar!")
        elif not video_ready:
            st.error("⚠️ Masukkan data referensi terlebih dahulu!")
        else:
            with st.spinner("🤖 Gemini Vision membedai objek -> DeepSeek meracik alur -> Qwen mengunci objek & menyusun storyboard..."):
                try:
                    # STEP 1: Gemini Vision Bedah Subjek & Objek Utama
                    vision_summary = ""
                    if input_mode == "✍️ Input Teks Tepat Urutan Cerita":
                        vision_summary = user_topic
                    else:
                        gemini_vision_prompt = """
                        Bedah media ini secara rinci:
                        1. Siapa saja subjek/karakter utamanya (deskripsi fisik rinci).
                        2. Apa SAJA objek penting/properti yang dipegang, dipakai, atau ada di sekitarnya (HP, tablet, panci, makanan, mobil, senjata, dll).
                        3. Alur cerita dan aksi adegan dari awal sampai akhir.
                        """
                        if input_mode == "📁 Upload Beberapa Screenshot Urut (Multi-Frame)":
                            imgs = []
                            for idx, img_file in enumerate(multi_frames):
                                p = f"temp_{idx}.jpg"
                                with open(p, "wb") as f:
                                    f.write(img_file.read())
                                imgs.append(client_gemini.files.upload(file=p))
                            res_gem = client_gemini.models.generate_content(model='gemini-3.6-flash', contents=imgs + [gemini_vision_prompt])
                        else:
                            vid = client_gemini.files.upload(file=video_path)
                            res_gem = client_gemini.models.generate_content(model='gemini-3.6-flash', contents=[vid, gemini_vision_prompt])
                        vision_summary = res_gem.text

                    # STEP 2: DeepSeek Engine Meracik Cerita Baru (Anti-Plagiat)
                    deepseek_sys = "Kamu adalah DeepSeek Creative Director Engine. Tugasmu meracik ulang cerita agar ANTI PLAGIAT, tapi komedi/kejutan visualnya tetap pas."
                    deepseek_user = f"Berdasarkan bedahan visual ini:\n'{vision_summary}'\n\nModifikasi cerita menjadi konsep baru dengan instruksi: '{modification_notes}'. Pastikan cerita memiliki plot twist menarik."
                    deepseek_out = call_openrouter("deepseek/deepseek-r1-distill-llama-70b", deepseek_sys, deepseek_user)

                    # STEP 3: Qwen Engine Kunci Objek & Storyboard JSON
                    qwen_sys = "Kamu adalah Qwen Prompt Master. Kunci seluruh subjek dan objek penting agar tidak morphing/hilang di Google Flow AI!"
                    qwen_user = f"""
                    Berdasarkan racikan cerita DeepSeek ini:
                    {deepseek_out}

                    TUGAS KHUSUS:
                    1. Buat 'character_anchor' Bahasa Inggris yang MENGUNCI ciri fisik subjek DAN SEMUA OBJEK WAJIB yang dipegang/ada di scene (misal: 'holding a silver tablet computer continuously', 'wearing red helmet', dll).
                    2. Bagi cerita menjadi TEPAT {max_scenes} SCENE (8 detik per scene).

                    Format Output JSON Murni:
                    {{
                        "new_concept_summary": "Ringkasan konsep racikan baru",
                        "character_anchor": "Karakter + Objek Wajib yang dikunci ketat",
                        "scenes": [
                            {{"scene_num": 1, "description": "Deskripsi Scene 1", "prompt": "Google Flow Prompt 1", "vo": "Voiceover 1"}},
                            {{"scene_num": 2, "description": "Deskripsi Scene 2", "prompt": "Google Flow Prompt 2", "vo": "Voiceover 2"}}
                        ]
                    }}
                    """
                    qwen_out = call_openrouter("qwen/qwen-2.5-72b-instruct", qwen_sys, qwen_user)

                    clean_json = qwen_out.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(clean_json)

                    st.session_state.master_storyboard = parsed["scenes"]
                    st.session_state.character_anchor = parsed["character_anchor"]
                    st.session_state.original_summary = parsed.get("new_concept_summary", "Konsep Hasil Racikan Triple AI.")
                    
                    st.session_state.step = 2
                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal memproses Triple AI: {e}")

# --- TAHAP 2 S/D SELESAI: EKSEKUSI PROMPT GOOGLE FLOW AI (ANTI-MORPHING ENFORCER) ---
elif 2 <= st.session_state.step <= (max_scenes + 1):
    curr_idx = st.session_state.step - 2
    scene_number = curr_idx + 1

    st.subheader(f"🎬 Eksekusi Scene {scene_number} dari {max_scenes}")
    curr_scene = st.session_state.master_storyboard[curr_idx]

    st.markdown(f"""
    <div class="reconcept-card">
        <b>💡 Ide Konsep Modifikasi (DeepSeek Brain):</b><br>
        <span>{st.session_state.original_summary}</span>
    </div>
    <div class="story-card">
        <b>🎯 Target Adegan Scene {scene_number} (Qwen Storyboard):</b><br>
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
            if not gemini_key or not openrouter_key:
                st.error("API Key belum diset lengkap.")
            else:
                start_time = curr_idx * 8
                end_time = (curr_idx + 1) * 8
                
                with st.spinner(f"⚡ Qwen menyusun prompt ketat (Anti-Morphing Objek)..."):
                    try:
                        prompt_enforcer_sys = "Kamu adalah Qwen Prompt Specialist untuk Google Flow AI. Tugasmu menegaskan penguncian objek secara ekstrem."
                        prompt_enforcer_user = f"""
                        Buat prompt 8 detik Bahasa Inggris untuk Google Flow AI adegan: "{curr_scene['description']}".
                        Gaya Visual Target: {style_pilihan}.
                        
                        PERATURAN PENGUNCIAN SUBJEK & OBJEK (ANTI-MORPHING/ANTI-HILANG):
                        1. Anchor Utama: {st.session_state.character_anchor}
                        2. SEBUTKAN OBJEK YANG DIPEGANG/DIPAKAI SUBJEK SECARA SPESIFIK DI AWAL & AKHIR KALIMAT PROMPT.
                        3. Gunakan kata kunci penekan seperti: 'continuously holding the [object]', 'hands fixed on [object] throughout the shot', 'no morphing', 'object never disappears'.
                        4. Susun kalimat: [Main Subject & Held/Associated Objects] + [Action/Emotion] + [Environment & Lighting] + [Camera Style].

                        Format Respons:
                        [PROMPT_SCENE]
                        (Google Flow Prompt Bahasa Inggris Ketat Objek)
                        [/PROMPT_SCENE]

                        [VO_SCENE]
                        (Voiceover Bahasa Indonesia)
                        [/VO_SCENE]
                        """
                        res_text = call_openrouter("qwen/qwen-2.5-72b-instruct", prompt_enforcer_sys, prompt_enforcer_user)

                        p_scene = res_text.split("[PROMPT_SCENE]")[1].split("[/PROMPT_SCENE]")[0].strip() if "[PROMPT_SCENE]" in res_text else res_text
                        vo_scene = res_text.split("[VO_SCENE]")[1].split("[/VO_SCENE]")[0].strip() if "[VO_SCENE]" in res_text else "Naskah VO."

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

# --- TAHAP AKHIR: GENERATE AUTOMATIC YOUTUBE SEO (VIRAL PACK) ---
else:
    st.balloons()
    st.success(f"🎉 **PROYEK TRIPLE AI SELESAI!** Seluruh {max_scenes} Scene Siap Digenerate!")

    with st.spinner("🔥 DeepSeek & Qwen sedang meracik Judul Clickbait Viral + Deskripsi & Tag SEO YouTube..."):
        try:
            seo_sys = "Kamu adalah YouTube SEO Specialist & Content Strategist Viral."
            seo_user = f"""
            Berdasarkan konsep cerita dan naskah berikut:
            Konsep: {st.session_state.original_summary}
            Detail Context: {st.session_state.current_story_context}

            Buatkan YouTube Shorts/Video SEO Pack dalam Bahasa Indonesia yang bikin orang penasaran/lucu & tembus algoritma:
            1. 3 Opsi JUDUL VIRAL (Clickbait emosional, bikin penasaran/lucu, gunakan emoji).
            2. DESKRIPSI VIDEO (Singkat, menarik, menyelipkan kata kunci pencarian, call-to-action subscribe/like).
            3. TAG SEO HIGH-VOLUME (Kumpulan tag dipisahkan koma untuk dipaste ke kolom Tags YouTube Studio).
            4. HASHTAG VIRAL (5-8 Hashtag untuk di judul/deskripsi seperti #Shorts #Lucu dll).
            """
            youtube_seo_pack = call_openrouter("deepseek/deepseek-r1-distill-llama-70b", seo_sys, seo_user)
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
