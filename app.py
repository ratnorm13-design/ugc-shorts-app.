import json
import re
import time
import os
import streamlit as st
from google import genai
from google.genai import types

# ==========================================
# 1. KONFIGURASI HALAMAN & ENGINE GEMINI
# ==========================================
st.set_page_config(
    page_title="Si Kumis IP Studio — Viral Cat UGC Pipeline",
    page_icon="🕶️",
    layout="wide"
)

MODEL_NAME = "gemini-3.6-flash"

# ==========================================
# 2. BRAND CHARACTER DNA ("SI KUMIS")
# ==========================================
# Terkunci presisi sesuai foto referensi (Si Kumis: Kucing putih, kacamata hitam, & mark kumis)
DEFAULT_BRAND_CAT_DNA = (
    "CHARACTER IP LOCK: 'Si Kumis'. "
    "A photorealistic white cat wearing stylish black sunglasses over its eyes, "
    "featuring a distinct black mustache-like fur mark directly under its pink nose. "
    "Has a small black fur patch on the top of its head between ears, pure white coat body, "
    "and maintains a cool, calm, deadpan poker-face expression. "
    "CRITICAL CONSTRAINTS: Maintain identical white fur, black mustache mark, head patch, "
    "and black sunglasses across every single video frame without changing facial structure."
)

ENVIRONMENT_PRESETS = [
    "Rollercoaster Seat at Amusement Park",
    "Cozy Living Room with Hardwood Floor & Plush Rug",
    "Modern Luxury Kitchen Countertop & Island",
    "Supermarket Grocery Aisle & Shelves",
    "Busy Outdoor Cafe Patio with Sidewalk",
    "Custom / Ketik Lokasi Sendiri"
]

CAMERA_STYLE_PRESETS = [
    "Front POV Camera on Rollercoaster / Ride",
    "iPhone Front-Camera Casual UGC Video (Vertical 9:16)",
    "Handheld Dynamic UGC Tracking Shot with Subtle Camera Shake",
    "Floor-Level Pet Cam Angle",
    "Cinematic Low-Angle Following Shot"
]

ASPECT_RATIOS = ["9:16 — TikTok / Reels / Shorts", "16:9 — YouTube Long", "1:1 — Square"]

# ==========================================
# 3. INITIALIZE SESSION STATE
# ==========================================
DEFAULTS = {
    "page": "home",
    "api_key": "",
    "input_mode": "Upload Video Viral",
    "manual_scene_count": 4,
    "brand_dna": DEFAULT_BRAND_CAT_DNA,
    "env_choice": ENVIRONMENT_PRESETS[0],
    "custom_env": "",
    "camera_choice": CAMERA_STYLE_PRESETS[0],
    "aspect_ratio": ASPECT_RATIOS[0],
    "user_notes": "",
    "analysis_data": {},
    "storyboard_text": "",
    "scene_prompts": {},
    "scene_frames": {},
    "current_scene": 1,
    "total_scenes": 0,
    "seo_package": {}
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ==========================================
# 4. HELPER & API UTILITIES
# ==========================================
def navigate_to(page_name: str):
    st.session_state.page = page_name
    st.rerun()

def reset_project_state():
    st.session_state.analysis_data = {}
    st.session_state.storyboard_text = ""
    st.session_state.scene_prompts = {}
    st.session_state.scene_frames = {}
    st.session_state.current_scene = 1
    st.session_state.total_scenes = 0
    st.session_state.seo_package = {}

def get_gemini_client():
    raw_key = (os.getenv("GEMINI_API_KEY") or st.session_state.get("api_key", "")).strip("`\"' \n\r\t")
    if not raw_key:
        st.error("Masukkan Gemini API Key di Sidebar terlebih dahulu.")
        return None
    try:
        return genai.Client(api_key=raw_key)
    except Exception as err:
        st.error(f"Gagal koneksi Gemini Client: {err}")
        return None

def clean_and_parse_json(text_response: str):
    clean_text = re.sub(r"^```(?:json)?\s*", "", text_response.strip(), flags=re.I)
    clean_text = re.sub(r"\s*```$", "", clean_text)
    try:
        return json.loads(clean_text)
    except Exception:
        pass
    starts = [p for p in (clean_text.find("{"), clean_text.find("[")) if p >= 0]
    if not starts:
        raise ValueError("AI tidak mengembalikan JSON yang valid.")
    start_pos = min(starts)
    for end_pos in range(len(clean_text), start_pos, -1):
        try:
            return json.loads(clean_text[start_pos:end_pos].strip())
        except Exception:
            continue
    raise ValueError("Gagal parsing JSON dari AI.")

def call_gemini_api(client, prompt: str, media_parts=None, is_json: bool = False) -> str:
    contents = []
    if media_parts:
        contents.extend(media_parts)
    contents.append(types.Part.from_text(text=prompt))

    config = {"temperature": 0.2}
    if is_json:
        config["response_mime_type"] = "application/json"

    for attempt in range(3):
        try:
            res = client.models.generate_content(
                model=MODEL_NAME,
                contents=[types.Content(role="user", parts=contents)],
                config=types.GenerateContentConfig(**config)
            )
            if not res.text:
                raise RuntimeError("Respons dari Gemini kosong.")
            return res.text
        except Exception as err:
            if attempt == 2:
                raise RuntimeError(f"Gagal menghubungi Gemini API: {err}")
            time.sleep(1.5)

# ==========================================
# 5. CORE AI LOGIC (VISION ANALYSIS & REMIX)
# ==========================================
def process_video_and_generate_storyboard():
    reset_project_state()
    client = get_gemini_client()
    if not client:
        return

    media_payload = []
    mode = st.session_state.input_mode
    chosen_env = st.session_state.custom_env if st.session_state.env_choice == "Custom / Ketik Lokasi Sendiri" else st.session_state.env_choice

    if mode == "Upload Video Viral":
        uploaded_file = st.session_state.get("viral_video_file")
        if not uploaded_file:
            st.error("Wajib mengunggah video viral untuk dianalisis Vision AI.")
            return
        
        try:
            file_bytes = uploaded_file.getvalue()
            mime_type = getattr(uploaded_file, "type", "video/mp4") or "video/mp4"
            media_payload.append(types.Part.from_bytes(data=file_bytes, mime_type=mime_type))
        except Exception as err:
            st.error(f"Gagal membaca video: {err}")
            return

        instruction_context = f"""
TUGAS ADAPTASI KONSISTENSI KARAKTER 'SI KUMIS':
1. Bedah video viral ini:
   - Temukan Viral Hook (0-3 detik) utama.
   - Analisis tempo, gerakan fisik, dan momen komedinya.
2. Adaptasikan SELURUH aksi utama menjadi aksi karakter 'Si Kumis':
   - CHARACTER DNA: "{st.session_state.brand_dna}"
   - LATAR LINGKUNGAN: "{chosen_env}"
3. Hitung durasi dan bagi menjadi beberapa Scene (~5-8 detik per scene).
"""
    else:
        instruction_context = f"""
TUGAS STORYBOARD MANUAL UNTUK 'SI KUMIS':
1. Buat {st.session_state.manual_scene_count} Scene video komedi (~5-8 detik per scene).
2. Skenario: "{st.session_state.user_notes}"
3. Karakter Utama: "{st.session_state.brand_dna}"
4. Latar Lingkungan: "{chosen_env}"
"""

    prompt = f"""
{instruction_context}

Struktur alur komedi UGC:
- Scene 1: Hook kaget/santai penuh gaya (0-3s).
- Scene Pertengahan: Eskalasi aksi Si Kumis yang santai vs kaget/absurd.
- Scene Terakhir: Climax / Payoff komedi.

OUTPUT WAJIB FORMAT JSON VALID:
{{
  "viral_hook_analysis": "Penjelasan singkat adaptasi video viral ke Karakter Si Kumis",
  "calculated_scene_count": [JUMLAH_SCENE_INT],
  "storyboard_draft_text": "Scene 1: [Deskripsi Aksi Si Kumis, Kamera, & Timing]\nScene 2: [Deskripsi Aksi Lanjutan] ..."
}}
"""

    with st.spinner("Vision AI sedang mengadaptasi video ke Karakter Si Kumis..."):
        try:
            raw_response = call_gemini_api(client, prompt, media_payload, is_json=True)
            parsed = clean_and_parse_json(raw_response)

            st.session_state.analysis_data = parsed
            st.session_state.total_scenes = int(parsed.get("calculated_scene_count", st.session_state.manual_scene_count))
            st.session_state.storyboard_text = parsed.get("storyboard_draft_text", "")

            navigate_to("analysis")
        except Exception as err:
            st.error(f"Gagal memproses analisis video: {err}")

def generate_single_scene_prompt(scene_num: int, custom_revision: str = ""):
    client = get_gemini_client()
    if not client:
        return "ERROR_API"

    total = st.session_state.total_scenes
    chosen_env = st.session_state.custom_env if st.session_state.env_choice == "Custom / Ketik Lokasi Sendiri" else st.session_state.env_choice

    storyboard_lines = st.session_state.storyboard_text.split("\n")
    current_action_desc = f"Action for Scene {scene_num}"
    for line in storyboard_lines:
        if f"scene {scene_num}" in line.lower():
            current_action_desc = line
            break

    media_parts = []
    if scene_num == 1:
        mode_label = "T2V (Text-to-Video)"
        continuity_instruction = f"[P3 - ENVIRONMENT]: Located at {chosen_env}. High quality UGC video frame."
    else:
        mode_label = "I2V (Image-to-Video)"
        continuity_instruction = "[P1 - CONTINUITY BRIDGE]: DO NOT alter Si Kumis's sunglasses, white fur, or mustache mark. Seamlessly continue physical movement from the last frame image."
        
        prev_num = scene_num - 1
        if prev_num in st.session_state.scene_frames and st.session_state.scene_frames[prev_num]:
            f_data = st.session_state.scene_frames[prev_num]
            media_parts.append(types.Part.from_bytes(data=f_data["bytes"], mime_type=f_data["mime"]))
        else:
            return "ERROR_NO_PREVIOUS_FRAME"

    revision_str = f"\n[USER REVISION]: {custom_revision}" if custom_revision else ""

    prompt = f"""
Write ONE single-paragraph AI Video Prompt in ENGLISH for Google Veo / Flow AI / Kling.
Scene {scene_num} of {total}. Mode: {mode_label}.

STRICT P0-P5 STRUCTURE IN A SINGLE CONTINUOUS PARAGRAPH:
[P0 - CHARACTER DNA LOCK]: {st.session_state.brand_dna}.
[P1 - ACTION & MOVEMENT]: {current_action_desc}. {continuity_instruction}
[P2 - MICRO BEHAVIOR]: Cool calm composure, slight tail movement, whiskers twitching, signature black sunglasses and mustache mark perfectly visible.
[P3 - ENVIRONMENT]: Positioned in {chosen_env}.
[P4 - CAMERA WORK]: {st.session_state.camera_choice}.
[P5 - VISUAL STYLE]: Photorealistic 4K UGC TikTok Reels video style, natural lighting, {st.session_state.aspect_ratio}.
{revision_str}

OUTPUT ONLY THE FINAL PROMPT PARAGRAPH TEXT WITHOUT ANY LABELS, HEADINGS, OR PREAMBLE.
"""

    with st.spinner(f"Merakit Prompt Scene {scene_num} (Kunci Si Kumis)..."):
        try:
            result = call_gemini_api(client, prompt, media_parts, is_json=False)
            st.session_state.scene_prompts[scene_num] = result.strip()
            return "SUCCESS"
        except Exception:
            return "ERROR_API"

def generate_viral_seo():
    client = get_gemini_client()
    if not client:
        return False

    prompt = f"""
Anda adalah Strategis SEO Konten Viral TikTok & Shorts.
Buatkan paket SEO berdasarkan petualangan karakter 'Si Kumis':

Storyboard:
{st.session_state.storyboard_text}

Karakter DNA: {st.session_state.brand_dna}

Hasilkan JSON valid:
{{
  "youtube_title": "Judul YouTube Shorts viral & clickbait tentang Si Kumis",
  "tiktok_caption": "Caption TikTok/Reels lucu + hashtag viral (#sikumis #catsoftiktok #funnycat #ugc)",
  "description": "Deskripsi singkat 2 paragraf ramah SEO",
  "tags": "si kumis, cool cat, sunglasses cat, funny cat, viral cat video, ugc cat"
}}
"""
    with st.spinner("Membuat Paket SEO Viral Si Kumis..."):
        try:
            raw = call_gemini_api(client, prompt, is_json=True)
            st.session_state.seo_package = clean_and_parse_json(raw)
            return True
        except Exception as err:
            st.error(f"Gagal generate SEO: {err}")
            return False

# ==========================================
# 6. VIEWS / ANTARMUKA TAMPILAN
# ==========================================
def render_home():
    st.title("🕶️ Si Kumis IP Studio — UGC Pipeline")
    st.caption("Konversi Video Viral Menjadi Konten Konsisten Karakter Utama 'Si Kumis'")

    st.subheader("1. Sumber Referensi Video Viral")
    mode = st.radio("Metode Input:", ["Upload Video Viral", "Manual / Teks Skenario"], key="input_mode", horizontal=True)

    if mode == "Upload Video Viral":
        st.file_uploader("Unggah Video Viral Referensi (.mp4, .mov, .webm)", type=["mp4", "mov", "webm"], key="viral_video_file")
        st.text_area("Catatan Khusus (Opsional)", key="user_notes", height=70, placeholder="Misal: Si Kumis tetap tenang memakai kacamata meski wahana meluncur kencang")
    else:
        st.slider("Target Jumlah Scene (1 Scene = ~5-8 Detik):", min_value=1, max_value=12, value=4, key="manual_scene_count")
        st.text_area("Tuliskan Skenario Komedi Kamu:", key="user_notes", height=100, placeholder="Misal: Si Kumis naik rollercoaster dengan tenang sambil memakai kacamata hitam...")

    st.subheader("2. Pengaturan Visual & Kamera")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Latar Lingkungan:", ENVIRONMENT_PRESETS, key="env_choice")
        if st.session_state.env_choice == "Custom / Ketik Lokasi Sendiri":
            st.text_input("Deskripsi Lokasi Custom:", key="custom_env")

    with col2:
        st.selectbox("Gaya Kamera UGC:", CAMERA_STYLE_PRESETS, key="camera_choice")
        st.selectbox("Rasio Format Video:", ASPECT_RATIOS, key="aspect_ratio")

    with st.expander("🧬 Character DNA 'Si Kumis' (Locked)"):
        st.caption("Deskripsi visual terkunci agar ekspresi, bulu putih, kacamata hitam, dan kumis tidak berubah saat dirender.")
        st.text_area("Master Prompt DNA Si Kumis:", key="brand_dna", height=100)

    st.markdown("---")
    st.button("🚀 TRANSFORMATSIKAN KE SI KUMIS", type="primary", use_container_width=True, on_click=process_video_and_generate_storyboard)

def render_analysis():
    st.title("📋 Vision AI Analysis — Adaptasi Si Kumis")

    if not st.session_state.get("storyboard_text"):
        st.info("Silakan unggah video dan buat storyboard di halaman utama.")
        return

    if "viral_hook_analysis" in st.session_state.analysis_data:
        st.success(f"💡 **Analisis Adaptasi Si Kumis:** {st.session_state.analysis_data['viral_hook_analysis']}")

    st.subheader(f"Draft Storyboard ({st.session_state.total_scenes} Scene)")
    st.caption("Atur alur cerita sebelum AI merakit prompt video.")

    edited = st.text_area("Edit Storyboard per Scene:", value=st.session_state.storyboard_text, height=280)

    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Kembali Edit Input"):
            navigate_to("home")
    with col2:
        if st.button("✅ ACC STORYBOARD & GENERATE PROMPT 🎬", type="primary", use_container_width=True):
            st.session_state.storyboard_text = edited
            navigate_to("scenes")

def render_scenes():
    st.title("🎥 Production Studio (Prompter Si Kumis)")
    total = st.session_state.total_scenes
    curr = st.session_state.current_scene

    if total == 0:
        st.info("Kembali ke Beranda untuk memulai proyek.")
        return

    st.subheader(f"Proses Scene {curr} dari {total}")

    if curr == 1:
        st.info("🔥 **MODE: T2V (Text-to-Video)**\nCopy prompt di bawah ke generator video (Veo/Kling/Runway) TANPA gambar rujukan.")
    else:
        st.warning(f"🖼️ **MODE: I2V (Image-to-Video)**\nUpload screenshot Last Frame dari Scene {curr-1} untuk mengunci wajah dan fitur Si Kumis.")

    # Gatekeeper Check
    if curr > 1 and (curr - 1) not in st.session_state.scene_frames:
        st.error(f"🛑 Gembok Terkunci! Wajib mengunggah gambar Last Frame Scene {curr-1} di bawah ini untuk membuka Scene {curr}.")
        if st.button("← Kembali ke Scene Sebelumnya"):
            st.session_state.current_scene -= 1
            st.rerun()
        return

    # Auto Generate Prompt if not present
    if curr not in st.session_state.scene_prompts:
        status = generate_single_scene_prompt(curr)
        if status == "SUCCESS":
            st.rerun()
        elif status == "ERROR_NO_PREVIOUS_FRAME":
            st.error("Frame scene sebelumnya belum tersedia.")
            return
        else:
            st.error("Gagal terhubung ke Gemini API.")
            if st.button("🔄 Coba Generate Ulang"):
                st.rerun()
            return

    # Display Prompt
    if curr in st.session_state.scene_prompts:
        st.text_area(f"Salin Prompt Scene {curr} (Dikunci ke Si Kumis):", value=st.session_state.scene_prompts[curr], height=180)

        with st.expander("🛠️ Re-roll / Tweak Scene Ini"):
            rev_input = st.text_input("Masukan revisi (Misal: 'Buat Si Kumis menengok ke samping')", key=f"rev_{curr}")
            if st.button("Apply Revision", key=f"btn_rev_{curr}"):
                generate_single_scene_prompt(curr, custom_revision=rev_input)
                st.rerun()

        st.markdown("---")

        # Continuity Frame Uploader
        if curr < total:
            st.subheader(f"🖼️ Upload Last Frame Scene {curr}")
            st.caption("Screenshot detik terakhir dari hasil render AI Video Generator lalu unggah di sini.")
            
            uploaded_frame = st.file_uploader(f"Upload Last Frame Scene {curr} (.png, .jpg)", type=["png", "jpg", "jpeg"], key=f"frame_file_{curr}")
            if uploaded_frame:
                st.session_state.scene_frames[curr] = {
                    "bytes": uploaded_frame.getvalue(),
                    "mime": getattr(uploaded_frame, "type", "image/png") or "image/png"
                }
                st.image(uploaded_frame, caption=f"Frame Kontinuitas Si Kumis Scene {curr} Terkunci!", width=240)
            elif curr in st.session_state.scene_frames:
                st.success("Gambar Kontinuitas Tersimpan.")

        st.markdown("---")

        # Navigation Controls
        nav_col1, nav_col2 = st.columns(2)
        with nav_col1:
            if curr > 1 and st.button("← Scene Sebelumnya"):
                st.session_state.current_scene -= 1
                st.rerun()
        with nav_col2:
            if curr < total:
                is_disabled = (curr not in st.session_state.scene_frames)
                if st.button("Scene Berikutnya →", type="primary", disabled=is_disabled):
                    st.session_state.current_scene += 1
                    st.rerun()
            elif curr == total:
                st.success("🎉 Seluruh Blueprint Prompt Si Kumis Selesai Dibuat!")
                st.markdown("---")

                st.subheader("🚀 Paket SEO Viral Si Kumis")
                if st.button("Generate SEO Package 🪄", type="primary"):
                    if generate_viral_seo():
                        st.rerun()

                if st.session_state.seo_package:
                    seo = st.session_state.seo_package
                    st.text_input("📌 Judul YouTube Shorts:", value=seo.get("youtube_title", ""))
                    st.text_area("📱 Caption TikTok / Reels:", value=seo.get("tiktok_caption", ""), height=90)
                    st.text_area("📝 Deskripsi Video:", value=seo.get("description", ""), height=130)
                    st.text_area("🏷️ Tags / Keywords:", value=seo.get("tags", ""), height=70)

# ==========================================
# 7. ROUTING & SIDEBAR
# ==========================================
with st.sidebar:
    st.title("🕶️ Si Kumis IP Studio")
    st.text_input("Gemini API Key", key="api_key", type="password")
    st.caption(f"Engine: `{MODEL_NAME}`")
    st.divider()
    st.markdown("**Tahapan Aplikasi:**")
    if st.button("1. 🏠 Beranda & Input", use_container_width=True):
        navigate_to("home")
    if st.button("2. 📋 Storyboard", use_container_width=True):
        navigate_to("analysis")
    if st.button("3. 🎥 Prompt Studio", use_container_width=True):
        navigate_to("scenes")

# Main Page Routing
current_page = st.session_state.page
if current_page == "home":
    render_home()
