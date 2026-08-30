import streamlit as st
import json
import requests
import time
from google import genai
from google.genai import types

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="UNIVERSAL GOOGLE FLOW GENERATOR", 
    page_icon="🎬", 
    layout="centered"
)

# --- STYLING CLEAN ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff !important; color: #000000 !important; }
    .main-header { text-align: center; padding: 1.5rem 1rem; background: #f8fafc; border-radius: 12px; border: 2px solid #e2e8f0; margin-bottom: 1.5rem; }
    .main-title { font-size: 1.8rem; font-weight: 900; color: #0f172a !important; margin-bottom: 0.3rem; }
    .sub-title { color: #dc2626 !important; font-size: 0.85rem; font-weight: 800; }
    label, p, span, div, .stMarkdown, .stRadio label, .stTextInput label, .stSelectbox label { color: #000000 !important; font-weight: 700 !important; }
    div.stButton > button { width: 100%; background: #dc2626 !important; color: #ffffff !important; font-weight: 900 !important; border: 2px solid #000000 !important; padding: 0.8rem 1.5rem; border-radius: 10px; text-transform: uppercase; font-size: 1rem !important; }
    .stTextInput input, .stTextArea textarea, .stSelectbox select { background-color: #ffffff !important; border: 2px solid #000000 !important; color: #000000 !important; font-weight: 700 !important; border-radius: 8px !important; }
    .brainstorm-card { background: #fefce8; border: 2px solid #eab308; border-radius: 10px; padding: 12px; margin-bottom: 12px; color: #000000 !important; }
    .story-card { background: #eff6ff; border: 2px solid #2563eb; border-radius: 10px; padding: 12px; margin-bottom: 12px; color: #000000 !important; }
    .audio-card { background: #f0fdf4; border: 2px solid #16a34a; border-radius: 10px; padding: 12px; margin-bottom: 12px; color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class="main-header">
    <div class="main-title">🎬 GOOGLE FLOW AI ENGINE (ULTIMATE OBJECT LOCK)</div>
    <div class="sub-title">STRICT OBJECT PERMANENCE | NO MORPHING | YOUTUBE SHORTS BILINGUAL SEO</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR API KEYS ---
st.sidebar.markdown("### 🔑 **API KEYS**")
gemini_key = st.sidebar.text_input("Gemini API Key:", type="password", placeholder="Paste Gemini Key...")
openrouter_key = st.sidebar.text_input("OpenRouter Key (DeepSeek):", type="password", placeholder="Paste OpenRouter Key...")

client_gemini = None
if gemini_key:
    try:
        client_gemini = genai.Client(api_key=gemini_key.strip())
        st.sidebar.success("✓ Gemini Connected")
    except Exception as e:
        st.sidebar.error(f"Gemini Error: {e}")

if openrouter_key:
    st.sidebar.success("✓ DeepSeek Connected")

# --- HELPER FUNCTION ---
def safe_gemini_generate(client, contents, config=None, retries=4):
    for attempt in range(retries):
        try:
            if config:
                return client.models.generate_content(model='gemini-3.6-flash', contents=contents, config=config)
            return client.models.generate_content(model='gemini-3.6-flash', contents=contents)
        except Exception as e:
            if ("503" in str(e) or "high demand" in str(e).lower() or "UNAVAILABLE" in str(e)) and attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            else:
                raise e

def call_deepseek(prompt_text, api_key):
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    payload = {"model": "deepseek/deepseek-r1:free", "messages": [{"role": "user", "content": prompt_text}]}
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=40)
        data = res.json()
        raw_content = data['choices'][0]['message']['content']
        if "</think>" in raw_content:
            raw_content = raw_content.split("</think>")[-1].strip()
        return raw_content
    except Exception as e:
        return f"Fallback: {e}"

# --- STATE MANAGEMENT ---
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.master_storyboard = []
    st.session_state.character_anchor = ""
    st.session_state.current_story_context = ""
    st.session_state.seo_package = ""
    st.session_state.style_pilihan = ""
    st.session_state.max_scenes = 1

# --- TAHAP 1 ---
if st.session_state.step == 1:
    st.markdown("### ⚙️ **PENGATURAN VISUAL & DURASI VIDEO**")
    
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        style_pilihan = st.selectbox(
            "Gaya Visual Target Google Flow:",
            options=[
                "Original / Auto-Detect from Source Video",
                "Photorealistic 8K Cinematic (Real Life)",
                "3D Animation Style (Pixar / Unreal Engine 5)",
                "2D Anime / Manga Style",
                "Cyberpunk / Sci-Fi Mood",
                "Dark Action Thriller Cinematic"
            ]
        )
    with col_cfg2:
        target_durasi_label = st.selectbox(
            "Pilih Target Total Durasi Video:",
            options=[
                "8 Detik (1 Scene)", 
                "16 Detik (2 Scene)", 
                "24 Detik (3 Scene)", 
                "32 Detik (4 Scene)", 
                "40 Detik (5 Scene)",
                "48 Detik (6 Scene)",
                "56 Detik (7 Scene)"
            ]
        )
    
    max_scenes = int(target_durasi_label.split("(")[1].split(" ")[0])
    st.session_state.style_pilihan = style_pilihan
    st.session_state.max_scenes = max_scenes

    st.markdown("---")
    st.markdown("### 📥 **INPUT REFERENSI VIDEO ASLI**")
    
    input_mode = st.radio("Upload Sumber Video Asli:", ("📁 Upload Video Asli (.mp4)", "📁 Upload Screenshots Frame Utuh", "✍️ Teks Deskripsi Scene"))
    
    video_ready = False
    user_topic = ""
    multi_frames = []
    video_path = "temp_orig_video.mp4"

    if input_mode == "📁 Upload Screenshots Frame Utuh":
        multi_frames = st.file_uploader("Upload Screenshots Frame Video Asli:", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        if multi_frames: video_ready = True
    elif input_mode == "📁 Upload Video Asli (.mp4)":
        uploaded_video = st.file_uploader("Upload Video Asli (.mp4):", type=["mp4", "mov", "avi"])
        if uploaded_video:
            with open(video_path, "wb") as f: f.write(uploaded_video.read())
            video_ready = True
    else:
        user_topic = st.text_area("Deskripsi Adegan Video Asli:", placeholder="Tuliskan subjek dan adegan video asli di sini...")
        if user_topic: video_ready = True

    extra_action_note = st.text_area("💡 Penyesuaian/Penambahan Adegan Khusus (Opsional):", 
        placeholder="Kosongkan jika ingin AI Gemini & DeepSeek otomatis yang meracik kelanjutan adegan...")

    if st.button("🔒 PROSES AUTO-LOCK IDENTITY & OBJECT PERMANENCE"):
        if not gemini_key or not openrouter_key:
            st.error("⚠️ Masukkan Gemini & OpenRouter Key di sidebar!")
        elif not video_ready:
            st.error("⚠️ Upload file atau masukkan teks referensi video asli!")
        else:
            with st.spinner("👁️ Menganalisis Subjek & Kunci Objek Fizikal..."):
                try:
                    contents_list = []
                    if input_mode == "✍️ Teks Deskripsi Scene":
                        contents_list.append(f"Video Context:\n{user_topic}")
                    elif input_mode == "📁 Upload Screenshots Frame Utuh":
                        for idx, img in enumerate(multi_frames):
                            p = f"temp_frame_{idx}.jpg"
                            with open(p, "wb") as f: f.write(img.read())
                            contents_list.append(client_gemini.files.upload(file=p))
                    else:
                        contents_list.append(client_gemini.files.upload(file=video_path))

                    lock_prompt = f"""
                    Analisis video/gambar referensi ini secara presisi.
                    TUGAS PENGUNCIAN MUTLAK (STRICT OBJECT PERMANENCE & ANCHOR):
                    1. Identifikasi Subjek Utama (detail fisik, wajah, pakaian, bentuk tubuh).
                    2. Identifikasi SELURUH OBJEK/PROPERTI FISIK yang dipegang atau berada di dekat subjek (misal: dompet, botol, tas, mainan, dll).
                    3. KUNCI AURA & EMOSI UTAMA.
                    
                    Rancang persis {max_scenes} SCENE berkesinambungan. Semua objek fisik yang dipegang WAJIB TETAP ADA dan TIDAK BOLEH MENYUSUT, LENYAP, ATAU BERUBAH BENTUK di scene manapun!
                    
                    Output JSON format:
                    CHARACTER_ANCHOR: [Deskripsi Subjek + Kunci Seluruh Objek Fizikal Terikat + Aura Emosi]
                    SCENES: [Array of {max_scenes} scenes with 'scene_num', 'description', 'audio_fx_and_vo']
                    """
                    contents_list.append(lock_prompt)
                    
                    gemini_res = safe_gemini_generate(client_gemini, contents_list)
                    gemini_analysis = gemini_res.text

                    deepseek_prompt = f"""
                    Tingkatkan kualitas narasi dan sinematik berdasarkan analisis Gemini:
                    {gemini_analysis}

                    Catatan Tambahan: {extra_action_note if extra_action_note else 'Bebas'}
                    ATURAN MUTLAK DEEPSEEK: Pastikan pergerakan subjek memperhitungkan keberadaan objek fisik agar objek TIDAK MENYUSUT ATAU MENGHILANG saat gerakan dilakukan!
                    """
                    deepseek_ideas = call_deepseek(deepseek_prompt, openrouter_key)

                    final_struct_prompt = f"""
                    Gabungkan hasil DeepSeek & Gemini menjadi JSON valid.
                    Hasil Gemini: {gemini_analysis}
                    Hasil DeepSeek: {deepseek_ideas}

                    Outputkan persis {max_scenes} SCENE JSON Object!
                    """
                    
                    config_json = types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema={
                            "type": "OBJECT",
                            "properties": {
                                "character_anchor": {"type": "STRING"},
                                "scenes": {
                                    "type": "ARRAY",
                                    "items": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "scene_num": {"type": "INTEGER"},
                                            "description": {"type": "STRING"},
                                            "audio_fx_and_vo": {"type": "STRING"}
                                        },
                                        "required": ["scene_num", "description", "audio_fx_and_vo"]
                                    }
                                }
                            },
                            "required": ["character_anchor", "scenes"]
                        }
                    )
                    
                    response = safe_gemini_generate(client_gemini, [final_struct_prompt], config=config_json)
                    parsed = json.loads(response.text)
                    st.session_state.master_storyboard = parsed["scenes"]
                    st.session_state.character_anchor = parsed["character_anchor"]
                    st.session_state.step = 2
                    st.rerun()

                except Exception as e:
                    st.error(f"Error Penguncian Subjek: {e}")

# --- TAHAP 2 S/D SELESAI ---
elif 2 <= st.session_state.step <= (st.session_state.max_scenes + 1):
    curr_idx = st.session_state.step - 2
    scene_number = curr_idx + 1

    st.subheader(f"🎬 Eksekusi Scene {scene_number} dari {st.session_state.max_scenes}")
    curr_scene = st.session_state.master_storyboard[curr_idx]

    st.markdown(f"""
    <div class="brainstorm-card">
        <b>🔒 AUTO IDENTITY & OBJECT LOCK ANCHOR:</b><br>{st.session_state.character_anchor}
    </div>
    <div class="story-card">
        <b>🎯 Visual Motion & Expression:</b> {curr_scene['description']}
    </div>
    <div class="audio-card">
        <b>🔊 High-Detail Audio & Voiceover Prompt:</b><br><i>"{curr_scene['audio_fx_and_vo']}"</i>
    </div>
    """, unsafe_allow_html=True)

    last_frame_file = None
    if scene_number > 1:
        st.markdown(f"### 📸 **Upload Screenshot Frame Scene {scene_number-1}**")
        last_frame_file = st.file_uploader(
            "Upload screenshot detik terakhir scene sebelumnya:",
            type=["png", "jpg", "jpeg"],
            key=f"uploader_scene_{scene_number}"
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"🚀 GENERATE PROMPT SCENE {scene_number}"):
            with st.spinner("⚡ Meracik prompt visual & pengunci objek mutlak..."):
                try:
                    prompt_contents = []
                    
                    if last_frame_file is not None:
                        temp_p = f"last_frame_s{scene_number}.jpg"
                        with open(temp_p, "wb") as f: f.write(last_frame_file.read())
                        prompt_contents.append(client_gemini.files.upload(file=temp_p))
                        prompt_contents.append("Visual Reference: Frame detik terakhir scene sebelumnya. KUNCI MUTLAK: Subjek, pakaian, dan SEMUA OBJEK yang dipegang WAJIB 100% KONSISTEN Tanpa Berubah/Hilang.")

                    prompt_spec = f"""
                    Buat prompt video 8 detik Bahasa Inggris untuk Google Flow AI (Veo/Omni Model).
                    Adegan Target: {curr_scene['description']}.
                    Audio/VO Target: {curr_scene['audio_fx_and_vo']}.
                    Visual Style Target: {st.session_state.style_pilihan}.
                    Anchor Subjek & Objek Terkunci: {st.session_state.character_anchor}.

                    INTRUKSI KETAT PENGUNCIAN OBJEK (STRICT OBJECT PERMANENCE RULES):
                    1. CRITICAL OBJECT PERMANENCE REQUIREMENT: All physical items/props held by or positioned near the subject MUST REMAIN CONSTANTLY VISIBLE AND PHYSICALLY PRESENT THROUGHOUT THE ENTIRE 8 SECONDS.
                    2. NO SHAPE-SHIFTING OR MORPHING: Items MUST NOT fade out, shrink, disappear, alter form, or morph into other objects during movements or gestures.
                    3. ANATOMY & MOTION ACCURACY: Maintain physical realistic behavior. If subject reaches out one hand/paw, ensure the other hand/body CONTINUES TO SECURELY HOLD THE OBJECT in full view.
                    4. CONTINUOUS DYNAMIC MOTION: Fluid movement, no freeze, dramatic mood expression.
                    5. AUDIO DETAILED: High detailed Sound Effects & Voiceover prompt.

                    Format Output:
                    [PROMPT_SCENE]
                    (Prompt Bahasa Inggris Lengkap)
                    [/PROMPT_SCENE]

                    [AUDIO_PROMPT]
                    (Prompt Audio SFX & VO Google Flow)
                    [/AUDIO_PROMPT]
                    """
                    prompt_contents.append(prompt_spec)

                    res_gen = safe_gemini_generate(client_gemini, prompt_contents)
                    res_text = res_gen.text
                    
                    p_scene = res_text.split("[PROMPT_SCENE]")[1].split("[/PROMPT_SCENE]")[0].strip() if "[PROMPT_SCENE]" in res_text else res_text
                    p_audio = res_text.split("[AUDIO_PROMPT]")[1].split("[/AUDIO_PROMPT]")[0].strip() if "[AUDIO_PROMPT]" in res_text else curr_scene['audio_fx_and_vo']

                    start_t = (scene_number - 1) * 8
                    end_t = scene_number * 8
                    scene_feed = f"\n\n=== SCENE {scene_number} ({start_t:02d}:00 - {end_t:02d}:00) ===\nGOOGLE FLOW VIDEO PROMPT:\n{p_scene}\n\nGOOGLE FLOW AUDIO / VO PROMPT:\n{p_audio}"
                    st.session_state.current_story_context += scene_feed

                    if scene_number == st.session_state.max_scenes:
                        seo_prompt = f"""
                        Berdasarkan adegan video berikut:
                        Anchor Subjek & Aura: {st.session_state.character_anchor}
                        Script Adegan: {st.session_state.current_story_context}

                        Rancang PAKET SEO KHUSUS YOUTUBE SHORTS (Bilingual Vertical Stack: English di atas, Indonesia di bawah).
                        Sediakan:
                        - 3 Judul Shorts Bilingual (Clickbait Positif / High CTR)
                        - Deskripsi Shorts Bilingual
                        - 12-15 Hashtags Shorts Viral (Global + Indonesia)
                        - 15-20 Tags SEO / Keywords
                        """
                        seo_res = safe_gemini_generate(client_gemini, [seo_prompt])
                        st.session_state.seo_package = seo_res.text

                    st.session_state.step += 1
                    st.rerun()

                except Exception as e:
                    st.error(f"Error Prompt Generation: {e}")

    with col2:
        if st.button("🔄 RESET PROYEK"):
            st.session_state.step = 1
            st.session_state.master_storyboard = []
            st.session_state.character_anchor = ""
            st.session_state.current_story_context = ""
            st.session_state.seo_package = ""
            st.rerun()

    if st.session_state.current_story_context:
        st.markdown("---")
        st.subheader("📜 Live Output Master Feed")
        st.text_area("Hasil Script & Prompt Feed:", value=st.session_state.current_story_context, height=250)

else:
    st.balloons()
    st.success("🎉 **PROMPT MASTER & PAKET YOUTUBE SHORTS SEO SELESAI!**")
    
    st.markdown("### 🎬 **1. MASTER PROMPT GOOGLE FLOW**")
    st.text_area("Master Video & Audio Prompt:", value=st.session_state.current_story_context, height=350)
    
    st.markdown("### 🔴 **2. PAKET SEO YOUTUBE SHORTS**")
    st.text_area("Paket SEO Shorts:", value=st.session_state.seo_package, height=450)
    
    if st.button("🔄 RESTART PROYEK BARU"):
        st.session_state.step = 1
        st.session_state.master_storyboard = []
        st.session_state.character_anchor = ""
        st.session_state.current_story_context = ""
        st.session_state.seo_package = ""
        st.rerun()
