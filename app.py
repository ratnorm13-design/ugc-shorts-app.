import streamlit as st
import json
import requests
from google import genai
from google.genai import types

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="STUDIO AI - Multi-Scene Flow AI Generator", 
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
    .config-card { background: #f8fafc; border: 2px solid #cbd5e1; border-radius: 10px; padding: 15px; margin-bottom: 20px; }
    .brainstorm-card { background: #fefce8; border: 2px solid #eab308; border-radius: 10px; padding: 12px; margin-bottom: 12px; color: #000000 !important; }
    .story-card { background: #eff6ff; border: 2px solid #2563eb; border-radius: 10px; padding: 12px; margin-bottom: 12px; color: #000000 !important; }
    .audio-card { background: #f0fdf4; border: 2px solid #16a34a; border-radius: 10px; padding: 12px; margin-bottom: 12px; color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class="main-header">
    <div class="main-title">🎬 GOOGLE FLOW MULTI-SCENE GENERATOR</div>
    <div class="sub-title">🔒 DYNAMIC DURATION (8s - 56s) | STRICT LOCK & AUDIO ENGINE</div>
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
    st.session_state.style_pilihan = ""
    st.session_state.max_scenes = 1

# --- TAHAP 1: KONFIGURASI PENGATURAN & PILIHAN DURASI ---
if st.session_state.step == 1:
    st.markdown("### 🎛️ **PENGATURAN VISUAL & PILIHAN DURASI VIDEO**")
    
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        style_pilihan = st.selectbox(
            "Gaya Visual Target Google Flow:",
            options=[
                "Photorealistic 8K Warzone Action (Cinematic lighting, dynamic texture)",
                "3D Cinematic Animation (Pixar style, vibrant color)",
                "2D Anime Action Style (Studio Ghibli aesthetic)",
                "Dark Cinematic Thriller / Action Mood"
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
    st.markdown("### 📥 **REFERENSI VIDEO & DRAFT ADEGAN**")
    
    accent_color = st.text_input("Warna Aksen Aksesori / Background:", value="Merah Terang / Red Headband & Black Tactical Vest")
    input_mode = st.radio("Upload Sumber Video Asli:", ("📁 Upload Video Asli (.mp4)", "📁 Upload Screenshots Frame Utuh", "✍️ Teks Deskripsi Scene"))
    
    video_ready = False
    user_topic = ""
    multi_frames = []
    video_path = "temp_orig_video.mp4"

    if input_mode == "📁 Upload Screenshots Frame Utuh":
        multi_frames = st.file_uploader("Upload Screenshots Frame Awal & Akhir Video Asli:", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        if multi_frames: video_ready = True
    elif input_mode == "📁 Upload Video Asli (.mp4)":
        uploaded_video = st.file_uploader("Upload Video Asli (.mp4):", type=["mp4", "mov", "avi"])
        if uploaded_video:
            with open(video_path, "wb") as f: f.write(uploaded_video.read())
            video_ready = True
    else:
        user_topic = st.text_area("Deskripsi Video Asli:", value="Kucing prajurit memakai ikat kepala merah dan rompi taktis berjalan memegang senapan di jalanan perang hancur.")
        if user_topic: video_ready = True

    extra_action_note = st.text_area("💡 Penyesuaian/Penambahan Adegan (Agar Kontinu Tanpa Freeze):", 
        value="Kucing melanjutkan langkah konstan, membidik senjata ke kanan dengan mata fokus, gerakan kontinu tanpa pause, derap langkah di puing & suara ledakan jernih.")

    if st.button(f"🔒 PROSES LOCK IDENTITY & SUSUN {max_scenes} SCENE ({max_scenes*8} DETIK)"):
        if not gemini_key or not openrouter_key:
            st.error("⚠️ Masukkan Gemini & OpenRouter Key di sidebar!")
        elif not video_ready:
            st.error("⚠️ Upload file atau masukkan teks referensi video asli!")
        else:
            with st.spinner(f"👁️ Mengunci Subjek Kucing Dewasa & Merancang {max_scenes} Scene..."):
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
                    Analisis video/gambar referensi ini.
                    KUNCI SUBJEK SECARA MUTLAK (STRICT CHARACTER LOCK):
                    1. Karakter Utama: Full-sized adult ginger tabby cat (Kucing dewasa berbulu oranye bergaris, BUKAN kitten/kucing kecil).
                    2. Aksesori Wajib: Bright RED HEADBAND tied firmly on forehead, BLACK TACTICAL VEST, holding M4 assault rifle.
                    3. Aksen / Modifikasi: {accent_color}.
                    
                    Rancang persis {max_scenes} SCENE (masing-masing 8 detik = Total {max_scenes*8} Detik).
                    Setiap pergantian scene HARUS menyambung MULUS tanpa ada gerakan berhenti/pause/freeze.
                    
                    Output JSON format:
                    CHARACTER_ANCHOR: [Deskripsi Kucing & Aksesori Terkunci]
                    SCENES: [Array of {max_scenes} scenes with 'scene_num', 'description', 'audio_fx_and_vo']
                    """
                    contents_list.append(lock_prompt)
                    
                    gemini_analysis = client_gemini.models.generate_content(model='gemini-3.6-flash', contents=contents_list).text

                    deepseek_prompt = f"""
                    Optimalkan storyboard total {max_scenes*8} detik ({max_scenes} Scene) berikut agar adegan mengalir kontinu tanpa jeda diam:
                    Hasil Analisis & Anchor Gemini:
                    {gemini_analysis}

                    Instruksi Ekstra User: {extra_action_note}
                    
                    Pastikan pergerakan kamera dan fisik berkesinambungan serta tambahkan petunjuk Audio/VO yang sangat jernih dan detail.
                    """
                    deepseek_ideas = call_deepseek(deepseek_prompt, openrouter_key)

                    final_struct_prompt = f"""
                    Berdasarkan Ide DeepSeek & Analisis Gemini:
                    {deepseek_ideas}
                    {gemini_analysis}

                    Outputkan persis {max_scenes} SCENE JSON Object untuk durasi total {max_scenes*8} detik!
                    """
                    response = client_gemini.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[final_struct_prompt],
                        config=types.GenerateContentConfig(
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
                    )

                    parsed = json.loads(response.text)
                    st.session_state.master_storyboard = parsed["scenes"]
                    st.session_state.character_anchor = parsed["character_anchor"]
                    st.session_state.step = 2
                    st.rerun()

                except Exception as e:
                    st.error(f"Error Penguncian Subjek: {e}")

# --- TAHAP 2 S/D SELESAI: GENERATE PROMPT PER SCENE ---
elif 2 <= st.session_state.step <= (st.session_state.max_scenes + 1):
    curr_idx = st.session_state.step - 2
    scene_number = curr_idx + 1

    st.subheader(f"🎬 Eksekusi Scene {scene_number} dari {st.session_state.max_scenes} (Detik {curr_idx*8} - {scene_number*8})")
    curr_scene = st.session_state.master_storyboard[curr_idx]

    st.markdown(f"""
    <div class="brainstorm-card">
        <b>🔒 STRICT IDENTITY ANCHOR (LOCKED):</b><br>{st.session_state.character_anchor}
    </div>
    <div class="story-card">
        <b>🎯 Visual Motion (No Freeze):</b> {curr_scene['description']}
    </div>
    <div class="audio-card">
        <b>🔊 High-Detail Audio & Voiceover Prompt:</b><br><i>"{curr_scene['audio_fx_and_vo']}"</i>
    </div>
    """, unsafe_allow_html=True)

    last_frame_file = None
    if scene_number > 1:
        st.markdown(f"### 📸 **Upload Screenshot Frame Detik Ke-{(scene_number-1)*8} (Akhir Scene {scene_number-1})**")
        last_frame_file = st.file_uploader(
            f"Upload screenshot detik terakhir dari Scene {scene_number-1} agar bentuk wajah, warna bulu, ikat kepala merah, & ukuran kucing 100% SAMA (Anti-Kitten & Anti-Morphing):",
            type=["png", "jpg", "jpeg"],
            key=f"uploader_scene_{scene_number}"
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"🚀 GENERATE PROMPT SCENE {scene_number}"):
            with st.spinner("⚡ Meracik prompt dengan penguncian ketat & audio detail..."):
                try:
                    prompt_contents = []
                    
                    if last_frame_file is not None:
                        temp_p = f"last_frame_s{scene_number}.jpg"
                        with open(temp_p, "wb") as f: f.write(last_frame_file.read())
                        prompt_contents.append(client_gemini.files.upload(file=temp_p))
                        prompt_contents.append("Visual Reference: Frame detik terakhir scene sebelumnya. KUNCI MUTLAK: Subjek WAJIB kucing dewasa yang sama, ikat kepala merah menyala (red headband) TETAP TERPASANG di dahi, rompi taktis hitam, tanpa perubahan rasio tubuh.")

                    prompt_spec = f"""
                    Buat prompt video 8 detik Bahasa Inggris untuk Google Flow AI (Veo/Omni Model).
                    Adegan Target: {curr_scene['description']}.
                    Audio/VO Target: {curr_scene['audio_fx_and_vo']}.
                    Visual Style: {st.session_state.style_pilihan}.
                    Anchor Terkunci: {st.session_state.character_anchor}.

                    PERINTAH MUTLAK PENGUNCIAN AI (MANDATORY INSTRUCTIONS):
                    1. CHARACTER IDENTITY LOCK: Write explicitly 'A full-sized adult ginger tabby cat with mature facial structure, wearing a bright red bandana/headband tied securely around its forehead, wearing a black tactical vest, holding a black rifle'.
                    2. ANTI-KITTEN MANDATE: Write 'STRICTLY NO KITTEN, NO PROPORTION SHRINKING, KEEP EXACT ADULT CAT FACIAL PROPORTIONS FROM REFERENCE'.
                    3. CONTINUOUS DYNAMIC MOTION (NO FREEZE): Write 'Continuous fluid movement, seamless tracking shot, unbroken action, no static freezing or motion pauses'.
                    4. AUDIO SPECIFICATION: Include explicit sound directives: 'Crisp studio voiceover audio, clear directional sound effect of footsteps on gravel, ambient wind blowing, distant explosions, cinematic immersive soundscape'.

                    Format Output:
                    [PROMPT_SCENE]
                    (Prompt Bahasa Inggris Lengkap)
                    [/PROMPT_SCENE]

                    [AUDIO_PROMPT]
                    (Prompt Khusus Sound FX & VO Google Flow)
                    [/AUDIO_PROMPT]
                    """
                    prompt_contents.append(prompt_spec)

                    res_gen = client_gemini.models.generate_content(model='gemini-3.6-flash', contents=prompt_contents)
                    res_text = res_gen.text
                    
                    p_scene = res_text.split("[PROMPT_SCENE]")[1].split("[/PROMPT_SCENE]")[0].strip() if "[PROMPT_SCENE]" in res_text else res_text
                    p_audio = res_text.split("[AUDIO_PROMPT]")[1].split("[/AUDIO_PROMPT]")[0].strip() if "[AUDIO_PROMPT]" in res_text else curr_scene['audio_fx_and_vo']

                    start_t = (scene_number - 1) * 8
                    end_t = scene_number * 8
                    scene_feed = f"\n\n=== SCENE {scene_number} ({start_t:02d}:00 - {end_t:02d}:00) ===\nGOOGLE FLOW VIDEO PROMPT:\n{p_scene}\n\nGOOGLE FLOW AUDIO / VO PROMPT:\n{p_audio}"
                    st.session_state.current_story_context += scene_feed
                    
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
            st.rerun()

    if st.session_state.current_story_context:
        st.markdown("---")
        st.subheader("📜 Live Output Master Feed")
        st.text_area("Hasil Script & Prompt Feed:", value=st.session_state.current_story_context, height=250)

else:
    st.balloons()
    st.success(f"🎉 **PROMPT MASTER TOTAL {st.session_state.max_scenes*8} DETIK SELESAI!**")
    st.subheader("📋 Salin Prompt Ini Langsung ke Google Flow AI:")
    st.text_area("Master Output Prompt:", value=st.session_state.current_story_context, height=400)
    
    if st.button("🔄 RESTART PROYEK BARU"):
        st.session_state.step = 1
        st.session_state.master_storyboard = []
        st.session_state.character_anchor = ""
        st.session_state.current_story_context = ""
        st.rerun()
