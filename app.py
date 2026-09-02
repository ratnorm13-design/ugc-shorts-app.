import json
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError
import requests
import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="UNIVERSAL GOOGLE FLOW GENERATOR",
    page_icon="🎬",
    layout="centered",
)

# --- STYLING CLEAN ---
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

# --- HEADER ---
st.markdown(
    """
<div class="main-header">
    <div class="main-title">🎬 UNIVERSAL GOOGLE FLOW ENGINE (ALL NICHE)</div>
    <div class="sub-title">SUPER FAST ENGINE | SEO + AEO + GEO + AIO OPTIMIZED</div>
</div>
""",
    unsafe_allow_html=True,
)

# --- SIDEBAR API KEYS ---
st.sidebar.markdown("### 🔑 **API KEYS**")
gemini_key = st.sidebar.text_input(
    "Gemini API Key:", type="password", placeholder="Paste Gemini Key..."
)
openrouter_key = st.sidebar.text_input(
    "OpenRouter Key (DeepSeek):",
    type="password",
    placeholder="Paste OpenRouter Key...",
)

client_gemini = None
if gemini_key:
  try:
    client_gemini = genai.Client(api_key=gemini_key.strip())
    st.sidebar.success("✓ Gemini Connected")
  except Exception as e:
    st.sidebar.error(f"Gemini Error: {e}")

if openrouter_key:
  st.sidebar.success("✓ DeepSeek Connected")


# --- HELPER FUNCTIONS DENGAN AUTO-RETRY & DELAY ANTI-LIMIT ---
def safe_gemini_generate(client, contents, config=None, retries=3):
  """Fungsi fleksibel yang dilengkapi dengan penanganan limit (retry/delay)"""
  for attempt in range(retries):
    try:
      if config:
        return client.models.generate_content(
            model="gemini-3.6-flash", contents=contents, config=config
        )
      return client.models.generate_content(
          model="gemini-3.6-flash", contents=contents
      )
    except APIError as e:
      if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
        if attempt < retries - 1:
          time.sleep(5 * (attempt + 1))
          continue
      raise e


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
            "Dark Action Thriller Cinematic",
        ],
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
            "56 Detik (7 Scene)",
            "1 Menit (8 Scene)",
            "1.5 Menit (12 Scene)",
            "2 Menit (15 Scene)",
            "2.5 Menit (19 Scene)",
            "3 Menit (23 Scene)",
        ],
    )

  max_scenes = int(target_durasi_label.split("(")[1].split(" ")[0])
  st.session_state.style_pilihan = style_pilihan
  st.session_state.max_scenes = max_scenes

  st.markdown("---")
  st.markdown(
      "### 📥 **INPUT REFERENSI VIDEO ASLI (UNIVERSAL ALL-NICHE)**"
  )

  # --- PENAMBAHAN OPSI '📜 Teks Transkrip Video' DI SINI ---
  input_mode = st.radio(
      "Pilih Format Input Referensi:",
      (
          "📜 Teks Transkrip Video",
          "📁 Upload Video Asli (.mp4)",
          "📁 Upload Screenshots Frame Utuh",
          "✍️ Teks Deskripsi Scene / Ringkasan",
      ),
  )

  video_ready = False
  user_topic = ""
  multi_frames = []
  video_path = "temp_orig_video.mp4"

  if input_mode == "📜 Teks Transkrip Video":
    user_topic = st.text_area(
        "Paste Transkrip Video di Sini:",
        placeholder=(
            "Paste seluruh teks transkrip dari YouTube di sini... (AI akan"
            " otomatis merombak visualnya agar 100% beda & bebas plagiat)"
        ),
        height=200,
    )
    if user_topic.strip():
      video_ready = True
  elif input_mode == "✍️ Teks Deskripsi Scene / Ringkasan":
    user_topic = st.text_area(
        "Deskripsi Adegan Video Asli:",
        placeholder="Tuliskan subjek dan adegan video asli di sini...",
    )
    if user_topic.strip():
      video_ready = True
  elif input_mode == "📁 Upload Screenshots Frame Utuh":
    multi_frames = st.file_uploader(
        "Upload Screenshots Frame Video Asli:",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    if multi_frames:
      video_ready = True
  else:
    uploaded_video = st.file_uploader(
        "Upload Video Asli (.mp4):", type=["mp4", "mov", "avi"]
    )
    if uploaded_video:
      with open(video_path, "wb") as f:
        f.write(uploaded_video.read())
      video_ready = True

  extra_action_note_t1 = st.text_area(
      "💡 Penyesuaian/Penambahan Modifikasi Utama (Opsional / Biarkan AI"
      " Berkreasi Otomatis):",
      placeholder=(
          "Contoh: Ubah latar tempat ke kota masa depan dan buat karakter utama"
          " berupa robot, tapi ikuti alur narasi dari transkrip."
      ),
  )

  if st.button("🔒 PROSES AUTO-LOCK IDENTITY & SMART ALGORITHM ENGINE"):
    if not gemini_key or not openrouter_key:
      st.error("⚠️ Masukkan Gemini & OpenRouter Key di sidebar!")
    elif not video_ready:
      st.error("⚠️ Masukkan transkrip/file/deskripsi referensi video!")
    else:
      with st.spinner("⚡ Meracik Kilat SEO/AEO/GEO & Pengunci Visual..."):
        try:
          contents_list = []
          if input_mode in [
              "📜 Teks Transkrip Video",
              "✍️ Teks Deskripsi Scene / Ringkasan",
          ]:
            contents_list.append(f"Transcript / Story Context:\n{user_topic}")
          elif input_mode == "📁 Upload Screenshots Frame Utuh":
            for idx, img in enumerate(multi_frames):
              p = f"temp_frame_{idx}.jpg"
              with open(p, "wb") as f:
                f.write(img.read())
              contents_list.append(client_gemini.files.upload(file=p))
          else:
            up_file = client_gemini.files.upload(file=video_path)
            while up_file.state.name == "PROCESSING":
              time.sleep(1)
              up_file = client_gemini.files.get(name=up_file.name)
            contents_list.append(up_file)

          user_custom_instruction = (
              extra_action_note_t1.strip()
              if extra_action_note_t1.strip()
              else "KOSONG (AI WAJIB BIKIN UNIK OTOMATIS)"
          )

          lock_prompt = f"""
                    Analisis referensi / transkrip ini.
                    Modifikasi User: "{user_custom_instruction}"
                    
                    RULES UTAMA (ANTI-PLAGIAT):
                    1. Re-imagine visual & karakter agar BERBEDA TOTAL dari video asli, tetapi pertahankan esensi/alur narasinya.
                    2. Kunci karakter & objek fisik unik ke CHARACTER_ANCHOR.
                    3. Scene 1 miliki AEO Hook (0-3 detik).
                    4. Voiceover ikuti struktur GEO (Ramah rekomendasi AI Search).
                    
                    Output JSON persis {max_scenes} SCENE:
                    CHARACTER_ANCHOR: [Subjek Unik Baru + Kunci Objek Fizikal]
                    SCENES: [Array {max_scenes} scenes dengan 'scene_num', 'description', 'audio_fx_and_vo']
                    """
          contents_list.append(lock_prompt)

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
                                  "audio_fx_and_vo": {"type": "STRING"},
                              },
                              "required": [
                                  "scene_num",
                                  "description",
                                  "audio_fx_and_vo",
                              ],
                          },
                      },
                  },
                  "required": ["character_anchor", "scenes"],
              },
          )

          response = safe_gemini_generate(
              client_gemini, contents_list, config=config_json
          )
          parsed = json.loads(response.text)

          st.session_state.master_storyboard = parsed["scenes"]
          st.session_state.character_anchor = parsed["character_anchor"]
          st.session_state.step = 2
          st.rerun()

        except Exception as e:
          st.error(f"Error Fast Engine: {e}")

# --- TAHAP 2 S/D SELESAI ---
elif 2 <= st.session_state.step <= (st.session_state.max_scenes + 1):
  curr_idx = st.session_state.step - 2
  scene_number = curr_idx + 1

  st.subheader(
      f"🎬 Eksekusi Scene {scene_number} dari {st.session_state.max_scenes}"
  )
  curr_scene = st.session_state.master_storyboard[curr_idx]

  st.markdown(
      f"""
    <div class="brainstorm-card">
        <b>🔒 AUTO IDENTITY & MODIFIED OBJECT LOCK ANCHOR:</b><br>{st.session_state.character_anchor}
    </div>
    <div class="story-card">
        <b>🎯 Visual Motion & Expression:</b> {curr_scene['description']}
    </div>
    <div class="audio-card">
        <b>🔊 High-Detail Audio & Voiceover Prompt (GEO/AEO Structured):</b><br><i>"{curr_scene['audio_fx_and_vo']}"</i>
    </div>
    """,
      unsafe_allow_html=True,
  )

  if st.session_state.current_story_context:
    st.markdown("### 📜 **HASIL PROMPT SCENE SEBELUMNYA:**")
    st.text_area(
        "Live Master Feed:",
        value=st.session_state.current_story_context,
        height=180,
        disabled=True,
    )

  custom_scene_note = st.text_area(
      f"💡 Penyesuaian/Penambahan Adegan Khusus Scene {scene_number} (Opsional"
      " / Biarkan AI Berkreasi):",
      placeholder=(
          "Kosongkan jika ingin AI yang menentukan penyesuaian scene"
          f" {scene_number}..."
      ),
      key=f"custom_note_scene_{scene_number}",
  )

  last_frame_file = None
  if scene_number > 1:
    st.markdown(
        f"### 📸 **Upload Screenshot Frame Scene {scene_number-1}**"
    )
    last_frame_file = st.file_uploader(
        "Upload screenshot detik terakhir scene sebelumnya:",
        type=["png", "jpg", "jpeg"],
        key=f"uploader_scene_{scene_number}",
    )

  col1, col2 = st.columns(2)
  with col1:
    if st.button(f"🚀 GENERATE PROMPT SCENE {scene_number}"):
      with st.spinner(f"⚡ Meracik Kilat Prompt Scene {scene_number}..."):
        try:
          prompt_contents = []
          if last_frame_file is not None:
            temp_p = f"last_frame_s{scene_number}.jpg"
            with open(temp_p, "wb") as f:
              f.write(last_frame_file.read())
            prompt_contents.append(client_gemini.files.upload(file=temp_p))

          scene_note_text = (
              custom_scene_note.strip()
              if custom_scene_note.strip()
              else "KOSONG (AI Bebas Berkreasi)"
          )

          prompt_spec = f"""
                    Buat prompt video 8 detik Bahasa Inggris untuk Google Flow AI (Veo Model).
                    Adegan Target: {curr_scene['description']}.
                    Catatan Modifikasi: {scene_note_text}.
                    Audio Target: {curr_scene['audio_fx_and_vo']}.
                    Style: {st.session_state.style_pilihan}.
                    Anchor: {st.session_state.character_anchor}.

                    CRITICAL RULES:
                    1. STRICT OBJECT PERMANENCE: Physical objects MUST NOT disappear or morph.
                    2. CONTINUOUS DYNAMIC MOTION.
                    3. AEO/GEO speech structure.

                    Format Output:
                    [PROMPT_SCENE]
                    (Prompt Inggris Visual)
                    [/PROMPT_SCENE]
                    [AUDIO_PROMPT]
                    (Prompt Audio SFX VO)
                    [/AUDIO_PROMPT]
                    """
          prompt_contents.append(prompt_spec)

          res_gen = safe_gemini_generate(client_gemini, prompt_contents)
          res_text = res_gen.text

          p_scene = (
              res_text.split("[PROMPT_SCENE]")[1]
              .split("[/PROMPT_SCENE]")[0]
              .strip()
              if "[PROMPT_SCENE]" in res_text
              else res_text
          )
          p_audio = (
              res_text.split("[AUDIO_PROMPT]")[1]
              .split("[/AUDIO_PROMPT]")[0]
              .strip()
              if "[AUDIO_PROMPT]" in res_text
              else curr_scene["audio_fx_and_vo"]
          )

          start_t = (scene_number - 1) * 8
          end_t = scene_number * 8
          scene_feed = (
              f"\n\n=== SCENE {scene_number} ({start_t:02d}:00 -"
              f" {end_t:02d}:00) ===\nGOOGLE FLOW VIDEO PROMPT:\n{p_scene}\n\nGOOGLE"
              f" FLOW AUDIO / VO PROMPT:\n{p_audio}"
          )
          st.session_state.current_story_context += scene_feed

          if scene_number == st.session_state.max_scenes:
            seo_prompt = f"""
                        Buatkan Paket SEO/AEO/GEO YouTube dari script long-form ini:
                        {st.session_state.current_story_context}

                        Format:
                        - 3 Judul Video Bilingual (High CTR)
                        - Deskripsi Lengkap Video (AEO & GEO friendly)
                        - 12-15 Hashtags Relevant
                        - 15-20 Tags SEO (DILARANG PAKAI TANDA KUTIP DUA ATAU SATU SAMA SEKALI, HANYA KATA DIPISAH KOMMA)
                        """
            seo_res = safe_gemini_generate(client_gemini, [seo_prompt])
            st.session_state.seo_package = seo_res.text.replace(
                '"', ""
            ).replace("'", "")

          st.session_state.step += 1

          # Delay 3 detik agar aman dari Rate Limit Free Tier
          time.sleep(3)

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

else:
  st.balloons()
  st.success("🎉 **PROMPT MASTER & PAKET SEO/AEO/GEO YOUTUBE SELESAI!**")

  st.markdown("### 🎬 **1. MASTER PROMPT GOOGLE FLOW (ALL SCENES)**")
  st.text_area(
      "Master Video & Audio Prompt:",
      value=st.session_state.current_story_context,
      height=350,
  )

  st.markdown(
      "### 🔴 **2. PAKET METADATA YOUTUBE (SEO + AEO + GEO OPTIMIZED)**"
  )
  st.text_area(
      "Paket SEO/AEO/GEO Video (Tanpa Kutip di Tags):",
      value=st.session_state.seo_package,
      height=450,
  )

  if st.button("🔄 RESTART PROYEK BARU"):
    st.session_state.step = 1
    st.session_state.master_storyboard = []
    st.session_state.character_anchor = ""
    st.session_state.current_story_context = ""
    st.session_state.seo_package = ""
    st.rerun()
