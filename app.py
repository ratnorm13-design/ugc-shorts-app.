import streamlit as st
import json
import requests
from google import genai
from google.genai import types

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="STUDIO AI - Gemini 3.6 & DeepSeek UGC Creator", 
    page_icon="🎬", 
    layout="centered"
)

# --- CLEAN LIGHT MODE STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff !important; color: #000000 !important; }
    .main-header { text-align: center; padding: 1.5rem 1rem; background: #f8fafc; border-radius: 12px; border: 2px solid #e2e8f0; margin-bottom: 1.5rem; }
    .main-title { font-size: 1.8rem; font-weight: 900; color: #0f172a !important; margin-bottom: 0.3rem; }
    .sub-title { color: #475569 !important; font-size: 0.85rem; font-weight: 700; }
    label, p, span, div, .stMarkdown, .stRadio label, .stTextInput label, .stSelectbox label, .stFileUploader label { color: #000000 !important; font-weight: 700 !important; }
    section[data-testid="stSidebar"] { background-color: #f1f5f9 !important; border-right: 2px solid #cbd5e1; min-width: 85vw !important; }
    div.stButton > button { width: 100%; background: #dc2626 !important; color: #ffffff !important; font-weight: 900 !important; border: 2px solid #000000 !important; padding: 0.8rem 1.5rem; border-radius: 10px; text-transform: uppercase; font-size: 1rem !important; }
    .stTextInput input, .stTextArea textarea, .stSelectbox select { background-color: #ffffff !important; border: 2px solid #000000 !important; color: #000000 !important; font-weight: 700 !important; border-radius: 8px !important; }
    .config-card { background: #f8fafc; border: 2px solid #cbd5e1; border-radius: 10px; padding: 15px; margin-bottom: 20px; }
    .brainstorm-card { background: #fefce8; border: 2px solid #eab308; border-radius: 10px; padding: 12px; margin-bottom: 12px; color: #000000 !important; }
    .story-card { background: #eff6ff; border: 2px solid #2563eb; border-radius: 10px; padding: 12px; margin-bottom: 12px; color: #000000 !important; }
    .seo-card { background: #f0fdf4; border: 2px solid #16a34a; border-radius: 10px; padding: 12px; margin-bottom: 12px; color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class="main-header">
    <div class="main-title">🎬 DUAL-ENGINE UGC CREATOR</div>
    <div class="sub-title">Powered by Gemini 3.6 Flash × DeepSeek R1 (Anti-Plagiarism & Strict Anchor Engine)</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR: HANYA API KEYS ---
st.sidebar.markdown("### 🔑 **API KEYS SETUP**")
gemini_key = st.sidebar.text_input("Gemini API Key:", type="password", placeholder="Paste Gemini API Key...")
openrouter_key = st.sidebar.text_input("OpenRouter Key (DeepSeek):", type="password", placeholder="Paste OpenRouter Key...")

client_gemini = None
if gemini_key:
    try:
        client_gemini = genai.Client(api_key=gemini_key.strip())
        st.sidebar.success("✓ Gemini 3.6 Connected")
    except Exception as e:
        st.sidebar.error(f"Gemini Key Error: {e}")

if openrouter_key:
    st.sidebar.success("✓ DeepSeek R1 Connected")

# HELPER: CALL DEEPSEEK VIA OPENROUTER
def call_deepseek(prompt_text, api_key):
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [{"role": "user", "content": prompt_text}]
    }
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=40)
        data = res.json()
        raw_content = data['choices'][0]['message']['content']
        if "</think>" in raw_content:
            raw_content = raw_content.split("</think>")[-1].strip()
        return raw_content
    except Exception as e:
        return f"DeepSeek Brainstorm Fallback: {e}"

# --- STATE MANAGEMENT ---
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.master_storyboard = []
    st.session_state.character_anchor = ""
    st.session_state.detected_genre = ""
    st.session_state.brainstorm_ideas = ""
    st.session_state.current_story_context = ""
    st.session_state.style_pilihan = ""
    st.session_state.max_scenes = 1

# --- TAHAP 1: KONFIGURASI MAIN SCREEN & BRAINSTORMING ---
if st.session_state.step == 1:
    st.markdown("### 🎨 **PENGATURAN VISUAL & DURASI VIDEO**")
    
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        style_pilihan = st.selectbox(
            "Gaya Visual Target Google Flow:",
            options=[
                "Photorealistic 8K (Cinematic camera, highly detailed textures)",
                "3D Cinematic Animation (Pixar style, soft illumination)",
                "2D Anime Style (Studio Ghibli aesthetic)",
                "Dark Cinematic Thriller / Horror Mood",
                "Claymation Stop Motion (Textured clay look)"
            ]
        )
    with col_cfg2:
        target_durasi_label = st.selectbox(
            "Target Total Durasi Video:",
            options=[
                "8 Detik (1 Scene)", 
                "16 Detik (2 Scene)", 
                "24 Detik (3 Scene)", 
                "32 Detik (4 Scene)", 
                "40 Detik (5 Scene)"
            ]
        )
    
    max_scenes = int(target_durasi_label.split("(")[1].split(" ")[0])
    
    st.session_state.style_pilihan = style_pilihan
    st.session_state.max_scenes = max_scenes

    st.markdown("---")
    st.markdown("### 📥 **SUMBER REFERENSI & ALUR CERITA**")
    
    input_mode = st.radio("Pilih Mode Referensi:", ("✍️ Teks Deskripsi Video", "📁 Upload Screenshots Urut", "📁 Upload Video (.mp4)"))
    
    video_ready = False
    user_topic = ""
    multi_frames = []
    video_path = "temp_video.mp4"

    if input_mode == "📁 Upload Screenshots Urut":
        multi_frames = st.file_uploader("Upload Urutan Gambar Referensi:", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        if multi_frames: video_ready = True
    elif input_mode == "📁 Upload Video (.mp4)":
        uploaded_video = st.file_uploader("Upload Video Referensi:", type=["mp4", "mov", "avi"])
        if uploaded_video:
            with open(video_path, "wb") as f: f.write(uploaded_video.read())
            video_ready = True
    else:
        user_topic = st.text_area("Deskripsi/Cerita Video Asli:", placeholder="Ketik adegan video asli di sini...")
        if user_topic: video_ready = True

    modification_notes = st.text_input("💡 Instruksi Tambahan Ide/Revisi Adegan Utama (Opsional):", placeholder="Misal: Ubah kostum kucing, ganti tempat di dapur, ending konyol...")

    if st.button("🤝 JALANKAN BRAINSTORMING DUAL-ENGINE (GEMINI 3.6 × DEEPSEEK)"):
        if not gemini_key or not openrouter_key:
            st.error("⚠️ Masukkan Gemini API Key DAN OpenRouter Key di sidebar!")
        elif not video_ready:
            st.error("⚠️ Masukkan bahan referensi awal terlebih dahulu!")
        else:
            with st.spinner("👁️ Gemini 3.6 mendeteksi visual asli & merancang elemen anti-plagiat..."):
                try:
                    # 1. Gemini 3.6 Analisis Visual & Rencana Variasi Unik
                    contents_list = []
                    if input_mode == "✍️ Teks Deskripsi Video":
                        contents_list.append(f"Video Text Reference:\n{user_topic}")
                    elif input_mode == "📁 Upload Screenshots Urut":
                        for idx, img in enumerate(multi_frames):
                            p = f"temp_{idx}.jpg"
                            with open(p, "wb") as f: f.write(img.read())
                            contents_list.append(client_gemini.files.upload(file=p))
                    else:
                        contents_list.append(client_gemini.files.upload(file=video_path))

                    analysis_prompt = """
                    Analisis referensi video ini secara mendalam. 
                    Tugas Utama (ANTI-PLAGIARISM RE-CREATION):
                    1. Tentukan Genre/Mood utama.
                    2. Rangkuman alur cerita asli.
                    3. BEDAKAN ELEMEN VISUAL DARI ASLINYA: Buatkan identitas unik baru untuk subjek (ubah kostum/baju, aksesoris, jenis/warna bulu/karakter jika memungkinkan, latar belakang/background baru, serta variasi gerakan adegan baru agar TIDAK 100% PERSIS VIDEO ASLI).
                    4. KUNCI KARAKTER BARU: Tentukan `character_anchor` baru dengan detail kostum/aksesoris/skala tubuh unik ini secara konsisten!
                    
                    Format output: GENRE: [genre] | ANCHOR: [anchor] | SUMMARY: [summary]
                    """
                    contents_list.append(analysis_prompt)
                    gemini_analysis = client_gemini.models.generate_content(model='gemini-3.6-flash', contents=contents_list).text

                    # 2. DeepSeek R1 Brainstorming & Variasi Adegan
                    st.toast("🧠 DeepSeek R1 meracik variasi adegan unik & plot twist anti-plagiat...")
                    deepseek_prompt = f"""
                    Hasil analisis & racikan variasi visual Gemini 3.6:
                    {gemini_analysis}
                    
                    Instruksi User: {modification_notes}

                    Sebagai Creative Director UGC Viral:
                    1. Rancang alur cerita BARU yang terinspirasi dari video asli tetapi memiliki variasi adegan, latar tempat, kostum/aksesoris unik, dan plot twist beda agar BEBAS PLAGIAT.
                    2. Kembangkan cerita menjadi pas TEPAT {max_scenes} SCENE (masing-masing 8 detik).
                    3. Pastikan humor/mood tetap kuat dan menarik audiens global & lokal.
                    """
                    deepseek_ideas = call_deepseek(deepseek_prompt, openrouter_key)
                    st.session_state.brainstorm_ideas = deepseek_ideas

                    # 3. Gemini 3.6 Final Structuring JSON
                    st.toast("⚡ Gemini 3.6 menyusun storyboard final & mengunci karakter unik...")
                    final_struct_prompt = f"""
                    Berdasarkan Ide Brainstorming DeepSeek:
                    {deepseek_ideas}

                    Dan Hasil Analisis Visual Gemini 3.6:
                    {gemini_analysis}

                    Susun storyboard final presisi menjadi persis {max_scenes} SCENE JSON Object!
                    """
                    response = client_gemini.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[final_struct_prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema={
                                "type": "OBJECT",
                                "properties": {
                                    "detected_genre": {"type": "STRING"},
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
                                "required": ["detected_genre", "character_anchor", "scenes"]
                            }
                        )
                    )

                    parsed = json.loads(response.text)
                    st.session_state.master_storyboard = parsed["scenes"]
                    st.session_state.character_anchor = parsed["character_anchor"]
                    st.session_state.detected_genre = parsed["detected_genre"]
                    
                    st.session_state.step = 2
                    st.rerun()

                except Exception as e:
                    st.error(f"Error Proses Dual-Engine: {e}")

# --- TAHAP 2 S/D SELESAI: GENERATE PROMPT PER SCENE + CONTINUATION UPLOADER ---
elif 2 <= st.session_state.step <= (st.session_state.max_scenes + 1):
    curr_idx = st.session_state.step - 2
    scene_number = curr_idx + 1

    st.subheader(f"🎬 Eksekusi Scene {scene_number} dari {st.session_state.max_scenes}")
    curr_scene = st.session_state.master_storyboard[curr_idx]

    st.markdown(f"""
    <div class="brainstorm-card">
        <b>🎭 Genre Terdeteksi:</b> {st.session_state.detected_genre.upper()}<br>
        <b>🎨 Gaya Visual:</b> {st.session_state.style_pilihan}<br>
        <b>🔒 Character & Anti-Plagiarism Anchor (Locked):</b> {st.session_state.character_anchor}
    </div>
    <div class="story-card">
        <b>🎯 Adegan Target Scene {scene_number}:</b><br>{curr_scene['description']}<br><br>
        <b>🗣️ Naskah Voiceover (VO):</b> <i>"{curr_scene['vo']}"</i>
    </div>
    """, unsafe_allow_html=True)

    # INSTRUKSI TAMBAHAN PER-SCENE (ADA DI SETIAP SCENE 1, 2, 3, DST.)
    scene_custom_instruction = st.text_input(
        f"💡 Instruksi Tambahan / Revisi Ide Khusus Scene {scene_number} (Opsional):",
        placeholder="Misal: Tambahkan kucing kaget pas piring jatuh, ubah sudut kamera zoom-in...",
        key=f"scene_custom_input_{scene_number}"
    )

    # UPLOADER SCREENSHOT DETIK TERAKHIR UNTUK SCENE 2 KE ATAS
    last_frame_file = None
    if scene_number > 1:
        st.markdown("### 📸 **Upload Screenshot Detik Terakhir Scene Sebelumnya**")
        last_frame_file = st.file_uploader(
            f"Upload screenshot hasil video Scene {scene_number - 1} agar wujud karakter & ukuran tubuh di Scene {scene_number} TETAP KONSISTEN (ANTI-MORPHING/ANTI-RESIZING):",
            type=["png", "jpg", "jpeg"],
            key=f"uploader_scene_{scene_number}"
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"🚀 GENERATE PROMPT SCENE {scene_number}"):
            if not gemini_key:
                st.error("API Key belum diset di sidebar.")
            else:
                with st.spinner("⚡ Gemini 3.6 meracik prompt visual anti-plagiat & mengunci detail..."):
                    try:
                        prompt_contents = []
                        
                        if last_frame_file is not None:
                            temp_frame_path = f"last_frame_s{scene_number}.jpg"
                            with open(temp_frame_path, "wb") as f:
                                f.write(last_frame_file.read())
                            prompt_contents.append(client_gemini.files.upload(file=temp_frame_path))
                            prompt_contents.append("Gambar ini adalah DETIK TERAKHIR dari scene sebelumnya. Lanjutkan adegan dari posisi, kostum, aksesoris, latar tempat, dan UKURAN TUBUH ini secara presisi tanpa ada yang menyusut/berubah bentuk.")

                        prompt_spec = f"""
                        Buatkan prompt video 8 detik Bahasa Inggris untuk Google Flow AI berdasarkan adegan ini: "{curr_scene['description']}".
                        Gaya Visual: {st.session_state.style_pilihan}.
                        Genre/Mood: {st.session_state.detected_genre}.
                        Penguncian Karakter & Objek Utama (Anti-Plagiarism Unik): {st.session_state.character_anchor}.
                        Instruksi Tambahan User Khusus Scene Ini: {scene_custom_instruction}

                        ATURAN KETAT MEMBUAT PROMPT UNIK & ANTI-PLAGIAT:
                        1. KUNCI KARAKTER & AKSEOSRIS: Pertahankan kostum, aksesoris, warna bulu/kulit, latar tempat, dan skala tubuh penuh dari karakter (strictly no size reduction/no mini version).
                        2. VARIATIF DARI VIDEO ASLI: Deskripsikan pergerakan kamera, ekspresi wajah baru, dan interaksi objek yang unik agar tampak sebagai video orisinil baru.
                        3. Sebutkan detail aksi 8 detik secara sinematik dan tajam.

                        Format output:
                        [PROMPT_SCENE]
                        (Prompt Bahasa Inggris)
                        [/PROMPT_SCENE]
                        """
                        prompt_contents.append(prompt_spec)

                        res_gen = client_gemini.models.generate_content(model='gemini-3.6-flash', contents=prompt_contents)
                        res_text = res_gen.text
                        p_scene = res_text.split("[PROMPT_SCENE]")[1].split("[/PROMPT_SCENE]")[0].strip() if "[PROMPT_SCENE]" in res_text else res_text

                        start_time = curr_idx * 8
                        end_time = (curr_idx + 1) * 8
                        scene_feed = f"\n\n=== SCENE {scene_number} ({start_time:02d}:00 - {end_time:02d}:00) ===\nGOOGLE FLOW PROMPT:\n{p_scene}\n\nVO SCRIPT:\n{curr_scene['vo']}"
                        st.session_state.current_story_context += scene_feed
                        
                        st.session_state.step += 1
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error Generate Prompt: {e}")

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

# --- TAHAP AKHIR: AUTOMATIC YOUTUBE SEO PACK (BILINGUAL 15 KEYWORDS) ---
else:
    st.balloons()
    st.success(f"🎉 **PROYEK SELESAI!** Seluruh {st.session_state.max_scenes} Scene Siap Digenerate!")

    with st.spinner("🔥 Gemini 3.6 meracik 15 Keyword SEO YouTube (Global & Lokal)..."):
        try:
            seo_prompt = f"""
            Berdasarkan alur video UGC bergenre '{st.session_state.detected_genre}' berikut:
            Context & Script: {st.session_state.current_story_context}

            Buatkan GLOBAL & LOCAL YOUTUBE SEO PACK (Bilingual: Bahasa Indonesia & English) yang memancing CTR tinggi:

            1. 3 Opsi JUDUL CLICKBAIT (Bahasa Indonesia & English) yang sesuai genre ({st.session_state.detected_genre}).
            2. DESKRIPSI VIDEO BILINGUAL (Singkat, SEO-friendly, menarik audiens global & lokal).
            3. EXACTLY 15 HIGH-VOLUME SEO KEYWORDS / TAGS (Campuran Bahasa Inggris & Bahasa Indonesia, dipisahkan dengan koma).
            4. HASHTAG VIRAL GLOBAL & LOKAL (8-10 hashtag populer).
            """
            seo_res = client_gemini.models.generate_content(model='gemini-3.6-flash', contents=seo_prompt)
            youtube_seo_pack = seo_res.text
        except Exception as e:
            youtube_seo_pack = f"Gagal generate SEO: {e}"

    st.markdown(f"""
    <div class="seo-card">
        <b>🚀 GLOBAL & LOKAL SEO PACK ({st.session_state.detected_genre.upper()}):</b><br>
        <pre style="white-space: pre-wrap; word-wrap: break-word; font-family: inherit;">{youtube_seo_pack}</pre>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📋 Master Prompt & Script Output")
    st.text_area("Copy Master Flow Prompts:", value=st.session_state.current_story_context, height=350)

    if st.button("🚀 MULAI PROYEK BARU"):
        st.session_state.step = 1
        st.session_state.master_storyboard = []
        st.session_state.character_anchor = ""
        st.session_state.current_story_context = ""
        st.re
