import streamlit as st
import os
import json
import requests
from google import genai

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="STUDIO AI - Triple Engine Creative Director", 
    page_icon="🔥", 
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
    <div class="main-title">🔥 TRIPLE ENGINE BRAINSTORMING UGC</div>
    <div class="sub-title">Gemini (Vision) 🤝 DeepSeek (Creative Plot Twist) 🤝 Qwen (Flow Prompt & SEO)</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR API CONFIG ---
st.sidebar.markdown("### ⚙️ **API KEYS SETUP**")
gemini_key = st.sidebar.text_input("1. Gemini API Key", type="password")
openrouter_key = st.sidebar.text_input("2. OpenRouter API Key (DeepSeek & Qwen)", type="password")

client_gemini = None
if gemini_key:
    try:
        client_gemini = genai.Client(api_key=gemini_key.strip())
        st.sidebar.success("✓ Gemini Connected")
    except Exception as e:
        st.sidebar.error(f"Gemini Key Error: {e}")

if openrouter_key:
    st.sidebar.success("✓ DeepSeek & Qwen Connected")

# --- HELPER OPENROUTER CALL ---
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

# --- TAHAP 1: TRIPLE AI BRAINSTORMING DISCUSSIONS ---
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
    modification_notes = st.text_input("💡 (Opsional) Arahkan Genre Komedi/Cerita:", placeholder="Misal: Bikin lebih kocak absurd, ending ngakak, dsb...")

    if st.button("🚀 RACIK CERITA SUPER KOCAK (TRIPLE AI DISCUSSIONS)"):
        if not gemini_key or not openrouter_key:
            st.error("⚠️ Lengkapi Gemini Key dan OpenRouter Key di sidebar!")
        elif not video_ready:
            st.error("⚠️ Masukkan video/gambar referensi dulu!")
        else:
            with st.spinner("🔥 ENGINE 1 (Gemini): Membedah visual & potensi adegan kocak..."):
                try:
                    # 1. GEMINI VISION BEDAH VIDEO & KUNCI OBJEK
                    if input_mode == "✍️ Input Teks Cerita/Adegan Video":
                        vision_summary = user_topic
                    else:
                        gemini_vision_prompt = """
                        Bedah video/gambar ini secara rinci:
                        1. Apa elemen komedi/kelucuan/keunikan utama dari video ini?
                        2. Identifikasi subjek utama DAN semua objek yang dipegang/digunakan (HP, panci, helm, dll).
                        3. Sebutkan adegan kunci yang buat penonton penasaran/kocak.
                        """
                        if input_mode == "📁 Upload Beberapa Screenshot Urut":
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

                    # 2. DEEPSEEK BRAINSTORMING: MERACIK ADEGAN TAMBAHAN BIAR JAUH LEBIH NENDANG
                    st.toast("🔥 ENGINE 2 (DeepSeek): Meracik adegan tambahan & plot twist kocak...")
                    deepseek_sys = "Kamu adalah DeepSeek Head Comedy Director. Tugasmu membuat video rujukan menjadi JAUH LEBIH LUCU, PENASARAN, DAN MENARIK dari video aslinya!"
                    deepseek_user = f"""
                    Hasil bedahan Gemini dari video ori:
                    {vision_summary}

                    Catatan Tambahan User: {modification_notes}
                    Target Durasi: {max_scenes} Scene (Total {max_scenes * 8} detik).

                    TUGASMU:
                    1. Ambil inti lucu dari video ori, lalu TAMBAHKAN adegan komedi/plot twist baru agar durasi {max_scenes * 8} detik terisi sempurna!
                    2. Jika video asli pendek (misal 10 detik), tambahkan adegan reaksi kocak, kejadian tidak terduga, atau klimaks yang bikin audiens ngakak/kaget.
                    3. Buat skenario ini jauh lebih seru dari video aslinya.
                    """
                    deepseek_out = call_openrouter("deepseek/deepseek-r1-distill-llama-70b", deepseek_sys, deepseek_user)

                    # 3. QWEN MASTERMIND: MENYUSUN STORYBOARD & MEMBUNGKUS OBJEK ANTI-MORPHING
                    st.toast("🔥 ENGINE 3 (Qwen): Mengunci objek & menyusun Prompt Google Flow...")
                    qwen_sys = "Kamu adalah Qwen Prompt Mastermind. Format racikan DeepSeek & Gemini menjadi JSON Storyboard presisi."
                    qwen_user = f"""
                    Berdasarkan racikan komedi DeepSeek ini:
                    {deepseek_out}

                    TUGAS QWEN:
                    1. Susun 'character_anchor' Bahasa Inggris yang mengunci ciri fisik subjek DAN objek wajib yang dipegang (misal: 'firmly holding a yellow frypan throughout, no morphing').
                    2. Buatkan persis {max_scenes} SCENE (8 detik per scene).
                    3. Buatkan Naskah Voiceover (VO) Bahasa Indonesia yang sangat kocak, santai, dan pas dengan ritme adegan.

                    Format Output JSON Murni:
                    {{
                        "new_concept_summary": "Ringkasan konsep komedi racikan baru",
                        "character_anchor": "Karakter + Objek Wajib yang dikunci ketat",
                        "scenes": [
                            {{"scene_num": 1, "description": "Deskripsi adegan kocak Scene 1", "vo": "VO Bahasa Indonesia Scene 1"}},
                            {{"scene_num": 2, "description": "Deskripsi adegan kocak Scene 2", "vo": "VO Bahasa Indonesia Scene 2"}}
                        ]
                    }}
                    """
                    qwen_out = call_openrouter("qwen/qwen-2.5-72b-instruct", qwen_sys, qwen_user)

                    clean_json = qwen_out.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(clean_json)

                    st.session_state.master_storyboard = parsed["scenes"]
                    st.session_state.character_anchor = parsed["character_anchor"]
                    st.session_state.original_summary = parsed.get("new_concept_summary", "Konsep Komedi Racikan Triple AI.")
                    
                    st.session_state.step = 2
                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal memproses Triple AI: {e}")

# --- TAHAP 2 S/D SELESAI: GENERATE PROMPT KETAT (ANTI-MORPHING) ---
elif 2 <= st.session_state.step <= (max_scenes + 1):
    curr_idx = st.session_state.step - 2
    scene_number = curr_idx + 1

    st.subheader(f"🎬 Eksekusi Scene {scene_number} dari {max_scenes}")
    curr_scene = st.session_state.master_storyboard[curr_idx]

    st.markdown(f"""
    <div class="reconcept-card">
        <b>💡 Hasil Racikan Komedi 3 AI (Jauh Lebih Nendang):</b><br>
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
            if not gemini_key or not openrouter_key:
                st.error("API Key belum diset lengkap.")
            else:
                start_time = curr_idx * 8
                end_time = (curr_idx + 1) * 8
                
                with st.spinner(f"⚡ Qwen menyusun prompt visual 8 detik untuk Google Flow..."):
                    try:
                        prompt_enforcer_sys = "Kamu adalah Qwen Prompt Specialist. Buat prompt visual 8 detik super detail untuk Google Flow AI."
                        prompt_enforcer_user = f"""
                        Buat prompt Bahasa Inggris 8 detik adegan: "{curr_scene['description']}".
                        Gaya Visual: {style_pilihan}.
                        
                        KUNCI OBJEK & SUBJEK (ANTI-MORPHING):
                        - Anchor Utama: {st.session_state.character_anchor}
                        - TEGASKAN BAHWA SUBJEK DAN OBJEK TERSEBUT KONSISTEN DIPEGANG/DIBAWA DARI AWAL DETIK SAMPAI AKHIR DETIK.
                        - Tambahkan instruksi kamera (cinematic panning, zoom, lighting).

                        Format Output:
                        [PROMPT_SCENE]
                        (Google Flow Prompt Bahasa Inggris)
                        [/PROMPT_SCENE]
                        """
                        res_text = call_openrouter("qwen/qwen-2.5-72b-instruct", prompt_enforcer_sys, prompt_enforcer_user)
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

# --- TAHAP AKHIR: AUTOMATIC YOUTUBE SEO (PACK VIRAL) ---
else:
    st.balloons()
    st.success(f"🎉 **RACIKAN 3 AI SELESAI!** Seluruh {max_scenes} Scene Siap Digenerate!")

    with st.spinner("🔥 DeepSeek & Qwen meracik Judul Clickbait Viral + Deskripsi & Tag SEO..."):
        try:
            seo_sys = "Kamu adalah YouTube Content Strategist Spesialis Video Viral & FYP."
            seo_user = f"""
            Berdasarkan ide racikan video super kocak ini:
            Konsep: {st.session_state.original_summary}
            Detail Script: {st.session_state.current_story_context}

            Buatkan SEO Pack YouTube Shorts dalam Bahasa Indonesia:
            1. 3 Opsi JUDUL CLICKBAIT VIRAL (Lucu, Bikin Penasaran, Emosional + Emoji).
            2. DESKRIPSI YOUTUBE (Menarik, singkat, menyelipkan keyword SEO).
            3. TAG SEO HIGH-VOLUME (Dipisahkan koma, siap paste ke YouTube Studio).
            4. HASHTAG VIRAL (5-8 hashtag populer).
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

    st.subheader("📋 Final Master Output")
    st.text_area("Copy Master Flow Prompts & Script:", value=st.session_state.current_story_context, height=350)

    if st.button("🚀 MULAI PROYEK BARU"):
        st.session_state.step = 1
        st.session_state.master_storyboard = []
        st.session_state.character_anchor = ""
        st.session_state.original_summary = ""
        st.session_state.current_story_context = ""
        st.rerun()
