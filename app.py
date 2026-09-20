import json
import os
import streamlit as st
from google import genai
from google.genai import types

from config import (
    MODEL_NAME, APP_VERSION, DURATION_SCENES, STYLE_OPTIONS,
    RUNNER_PRESETS, MAP_OPTIONS, PROP_STAND_OPTIONS, CLIMAX_ACTION_OPTIONS,
    OBSTACLE_OPTIONS, ASPECT_OPTIONS, extract_json, ask
)

st.set_page_config(page_title="UGC Remix Studio v10.0", page_icon="🎬", layout="wide")

DEFAULTS = {
    "page": "home",
    "api_key": "",
    "reference_file": None,
    "reference_text": "",
    "visual_style": STYLE_OPTIONS[0],
    "runner_choice": RUNNER_PRESETS[1],
    "custom_runner": "",
    "selected_map": MAP_OPTIONS[0],
    "selected_prop_stand": PROP_STAND_OPTIONS[0],
    "selected_climax_action": CLIMAX_ACTION_OPTIONS[0],
    "aspect_ratio": ASPECT_OPTIONS[0],
    "duration": "Auto (Sesuai Durasi & Video Referensi)",
    "custom_instruction": "",
    "user_scene_obstacles": {},
    "analysis": {},
    "storyboard": [],
    "scene_prompts": {},
    "scene_frames": {},
    "current_scene": 1,
    "detected_scenes": 4,
    "seo": {},
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

def go(page: str):
    st.session_state.page = page
    st.rerun()

def scene_count() -> int:
    val = DURATION_SCENES.get(st.session_state.duration, 0)
    if val == 0:
        return st.session_state.detected_scenes
    return val

def get_client():
    key = (os.getenv("GEMINI_API_KEY") or st.session_state.get("api_key", "")).strip()
    key = key.strip("`\"' ")
    if not key:
        st.error("Masukkan Gemini API Key terlebih dahulu di Sidebar.")
        return None
    try:
        return genai.Client(api_key=key)
    except Exception as exc:
        st.error(f"Gagal membuat koneksi Gemini API: {exc}")
        return None

def reference_parts(client, file_uploader_obj):
    if file_uploader_obj is not None:
        try:
            data = file_uploader_obj.getvalue()
            mime = getattr(file_uploader_obj, "type", None) or "video/mp4"
            return [types.Part.from_bytes(data=data, mime_type=mime)]
        except Exception as exc:
            st.warning(f"Gagal membaca file video, beralih ke analisis teks: {exc}")
            return []
    if st.session_state.reference_text.strip():
        return [types.Part.from_text(text=st.session_state.reference_text)]
    return []

def run_analysis():
    client = get_client()
    if not client:
        return

    ref_file = st.session_state.get("ref_file_input")
    parts = reference_parts(client, ref_file)
    if not parts and not st.session_state.reference_text.strip():
        st.warning("Masukkan atau upload video/skenario referensi terlebih dahulu.")
        return

    chosen_runner = st.session_state.runner_choice
    if chosen_runner == "Custom / Ketik Sendiri":
        chosen_runner = st.session_state.custom_runner or "Unique funny custom character"

    prompt = f"""
Anda adalah AI Master Creative Director khusus konten viral 3D Game / Parkour / Obstacle Challenge di TikTok & YouTube Shorts.

TUGAS UTAMA (ROADMAP CLONING 1:1 & MULTI-ACTION DENSITY):
1. Bedah video referensi secara menyeluruh. Kloning persis struktur jalur kontainer dan ritme waktunya secara 1:1.
2. PERMANENT OBJECT PERSISTENCE & MULTI-ACTION: Setiap kotak/pijakan di sepanjang jalur wajib terisi objek/boneka target sejak frame pertama (zero pop-in). Dalam durasi 1 scene (~8 detik), rancang agar runner melakukan minimal 2 aksi berturut-turut.
3. Rancang mutasi karakter runner utama menjadi: "{chosen_runner}", serta sesuaikan target boss/ragdoll dengan opsi copyright-safe.
4. Sediakan skenario klimaks dramatis di mana runner dan target mengalami ragdoll chaos.

PENGATURAN MANUAL OVERRIDE (JIKA DISUAP):
- Map Environment Override: {st.session_state.selected_map}
- Target Prop Stand Override: {st.session_state.selected_prop_stand}
- Climax Action Override: {st.session_state.selected_climax_action}
- Style Visual: {st.session_state.visual_style}
- Rasio Aspek Video: {st.session_state.aspect_ratio}
- Instruksi Tambahan User: {st.session_state.custom_instruction}

HASILKAN JSON SANGAT RINGKAS DAN PRESISI:
{{
  "video_duration_seconds": 24,
  "calculated_scene_count": {scene_count()},
  "original_reference": {{
    "runner_asli": "Karakter utama di referensi",
    "boss_asli": "Karakter/Ragdoll target di ujung",
    "track_asli": "Jenis rintangan & jalur di referensi"
  }},
  "remixed_mutation": {{
    "runner_baru": "{chosen_runner}",
    "boss_baru": "Deretan boneka/target ragdoll unik yang berdiri berurutan di atas pijakan sejak awal",
    "track_baru": "Lintasan kontainer/pijakan 1:1 dengan boneka ganda tanpa ada area kosong",
    "map_environment": "{st.session_state.selected_map if st.session_state.selected_map != 'Auto (Ikuti Remix UGC)' else 'Dynamic 3D Game Map'}",
    "prop_stand": "{st.session_state.selected_prop_stand if st.session_state.selected_prop_stand != 'Auto (Ikuti Remix UGC)' else 'Standard Flat Surface'}",
    "visual_anchor_token": "Deskripsi ketat kosmetik karakter pilihan user agar konsisten",
    "alasan_remix": "Alasan modifikasi"
  }},
  "storyboard_plan": [
    {{"scene": 1, "fokus_aksi": "Runner berlari cepat di atas lintasan, melakukan aksi ganda menendang/memukul dua target berurutan secara presisi."}},
    {{"scene": 2, "fokus_aksi": "Melanjutkan navigasi rintangan berikutnya dengan target aktif selanjutnya."}},
    {{"scene": 3, "fokus_aksi": "Klimaks aksi ganda penutupan, hantaman beruntun, dan runner ikut terjun jatuh bebas (ragdoll sacrifice fall)."}}
  ],
  "climax_action": "{st.session_state.selected_climax_action if st.session_state.selected_climax_action != 'Auto (Ikuti Remix UGC)' else 'Multi-hit combo with sacrifice fall'}",
  "spatial_layout": "Third-person tracking shot with zero pop-in persistent object coordinates"
}}
"""
    with st.spinner("Membedah roadmap 1:1 & menyusun skema multi-action & zero pop-in..."):
        try:
            raw = ask(client, prompt, parts, json_mode=True)
            data = extract_json(raw)
            st.session_state.analysis = data
            st.session_state.storyboard = data.get("storyboard_plan", [])
            
            if DURATION_SCENES.get(st.session_state.duration, 0) == 0:
                calc_scenes = data.get("calculated_scene_count", len(st.session_state.storyboard) or 3)
                st.session_state.detected_scenes = max(1, min(calc_scenes, 50))
            else:
                st.session_state.detected_scenes = scene_count()
            
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}
            st.session_state.current_scene = 1
            go("analysis")
        except Exception as exc:
            st.error(f"Analisis gagal: {exc}")

def generate_scene_prompt(scene_number: int) -> bool:
    client = get_client()
    if not client:
        return False

    analysis = st.session_state.analysis
    mutation = analysis.get("remixed_mutation", {})
    storyboard = analysis.get("storyboard_plan", [])
    total_scenes = scene_count()
    is_final_scene = (scene_number == total_scenes)

    map_env = st.session_state.selected_map
    if map_env == "Auto (Ikuti Remix UGC)":
        map_env = mutation.get("map_environment", "Vivid 3D Game Environment")

    prop_stand = st.session_state.selected_prop_stand
    if prop_stand == "Auto (Ikuti Remix UGC)":
        prop_stand = mutation.get("prop_stand", "Container Roofs")

    climax_act = st.session_state.selected_climax_action
    if climax_act == "Auto (Ikuti Remix UGC)":
        climax_act = analysis.get("climax_action", "Double-hit combo and chaotic ragdoll collapse")

    scene_focus = "Melanjutkan aksi lari dan rangkaian rintangan di atas jalur."
    if storyboard and len(storyboard) >= scene_number:
        scene_focus = storyboard[scene_number - 1].get("fokus_aksi", scene_focus)

    custom_obstacle_instruction = st.session_state.user_scene_obstacles.get(scene_number, "")
    obstacle_inject_str = ""
    if custom_obstacle_instruction:
        obstacle_inject_str = f"SPECIAL SCENE OBSTACLE MECHANIC: {custom_obstacle_instruction}"

    prev_frame_context = ""
    if scene_number > 1 and (scene_number - 1) in st.session_state.scene_frames:
        prev_frame_context = f"STRICT CONTINUITY & SPATIAL LOCK: Scene {scene_number} MUST start precisely at the exact spatial coordinates where Scene {scene_number-1} ended."

    if scene_number == 1:
        camera_desc = "Dynamic third-person trailing camera locked tightly behind the runner."
        action_desc = f"""
CRITICAL MULTI-ACTION & ZERO POP-IN RULES FOR SCENE 1:
1. PERSISTENT GRID OBJECTS (ZERO POP-IN): Every platform ({prop_stand}) is pre-populated with active target dolls ({mutation.get('boss_baru')}) standing fully visible right from Frame 1 (zero pop-in).
2. DUAL-ACTION PACING (2 ACTIONS IN 8 SECONDS): Runner ({mutation.get('runner_baru')}) executes TWO interactions sequentially: 
   - Action A: Sprint and kick/punch the first target doll off the edge.
   - Action B: Immediately advance to strike the second target doll on the next consecutive prop.
"""
    elif is_final_scene:
        camera_desc = "Dramatic close-up tracking zoom, shifting into cinematic slow-motion on impact."
        action_desc = f"""
ULTIMATE MULTI-ACTION CLIMAX & SACRIFICE FALL:
- Final Combo Executed: {climax_act}.
- Physics Chaos: Runner ({mutation.get('runner_baru')}) executes an explosive multi-hit combo on remaining target dolls ({mutation.get('boss_baru')}) standing on {prop_stand}.
- Sacrifice Fall (MUST HAPPEN): Runner loses balance and SACRIFICES / FALLS OFF THE EDGE TOGETHER WITH TARGET DOLLS, tumbling into a free-fall ragdoll physics chaos toward {map_env}.
"""
    else:
        camera_desc = "High-octane sweeping third-person tracking shot across the obstacle course."
        action_desc = f"ROADMAP CONTINUATION: {scene_focus}. Target entities are permanently populated on {prop_stand} from Frame 1."

    audio_cues = "Immersive game audio: heavy footfalls, impact thuds, roaring wind, comedic screams, and dynamic ragdoll sound cues."

    prompt = f"""
Write ONE ultra-detailed AI video generation prompt in ENGLISH for Scene {scene_number} of {total_scenes} (approx. 8 seconds segment).

ZERO POP-IN & ENVIRONMENT LOCK:
- MAP BACKGROUND: {map_env} (Bright daytime lighting, vivid sunny sky, high-contrast colorful 3D game aesthetics).
- SPATIAL CONTINUITY LOCK: All background elements, platforms ({prop_stand}), obstacles, and target dolls MUST exist permanently on screen from Frame 1 (zero pop-in).

ASSETS & ENTITIES:
- Style: {st.session_state.visual_style}
- Aspect Ratio: {st.session_state.aspect_ratio}
- Runner Character: {mutation.get('visual_anchor_token')}
- Target Entities (Standing permanently on {prop_stand} from Frame 1): {mutation.get('boss_baru')}
- Environment Path: {mutation.get('track_baru')}

NAVIGATIONAL ACTION OVERRIDE:
{obstacle_inject_str}

ACTION & PHYSICS LAWS:
{action_desc}
- Camera: {camera_desc}
- Audio: {audio_cues}
{prev_frame_context}

RULES:
Output ONLY the final raw English prompt without markdown formatting or extra text.
"""
    with st.spinner(f"Menyusun Prompt Scene {scene_number}..."):
        try:
            res_prompt = ask(client, prompt, json_mode=False)
            st.session_state.scene_prompts[scene_number] = res_prompt.strip()
            return True
        except Exception as exc:
            st.error(f"Gagal menyusun prompt: {exc}")
            return False

def render_home():
    st.title("🎬 UGC Remix Studio v10.0")
    st.caption("Engine Otomasi Konten 3D Game Challenge dengan Multi-Action Climax, Prop Overrides & Zero Pop-In Rules.")

    st.subheader("1. Referensi Video / Skenario")
    st.file_uploader("Upload Video Referensi (Shorts atau Long Video)", type=["mp4", "mov", "webm"], key="ref_file_input")
    st.text_area("Deskripsi Referensi Manual", key="reference_text", height=80, placeholder="Contoh: Video lari menendang dua boneka berurutan...")

    st.subheader("2. Pilihan Karakter Runner Utama")
    st.selectbox("Pilih Preset Karakter Runner:", RUNNER_PRESETS, key="runner_choice")
    if st.session_state.runner_choice == "Custom / Ketik Sendiri":
        st.text_input("Tulis Deskripsi Karakter Bebas Kamu:", key="custom_runner", placeholder="Misal: Karakter anomali unik...")

    st.subheader("3. Modifikasi Manual Map, Dudukan & Aksi Klimaks (Opsional)")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.selectbox("🗺️ Map Environment Background:", MAP_OPTIONS, key="selected_map")
    with col_m2:
        st.selectbox("🎯 Dudukan / Pijakan Target:", PROP_STAND_OPTIONS, key="selected_prop_stand")
    with col_m3:
        st.selectbox("💥 Aksi Klimaks & Physics Chaos:", CLIMAX_ACTION_OPTIONS, key="selected_climax_action")

    st.subheader("4. Pengaturan Visual, Rasio Aspek & Target Durasi")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Gaya Visual", STYLE_OPTIONS, key="visual_style")
        st.selectbox("Rasio Aspek Video", ASPECT_OPTIONS, key="aspect_ratio")
    with col2:
        st.selectbox("Target Durasi & Jumlah Scene", list(DURATION_SCENES.keys()), key="duration")
        st.text_area("Instruksi Tambahan (Opsional)", key="custom_instruction", height=80, placeholder="Misal: Buat jarak antar boneka lebih dekat...")

    st.markdown("---")
    st.subheader("🧭 Navigasi & Rintangan Jalur Per-Scene (Bikin Deg-degan)")
    calculated_scenes = DURATION_SCENES.get(st.session_state.duration, 0) or st.session_state.get("detected_scenes", 4)
    st.write(f"**Total Dynamic Scene Settings:** {calculated_scenes} Scene ({calculated_scenes * 8} Detik Total)")

    cols = st.columns(2)
    for i in range(1, calculated_scenes + 1):
        col_idx = (i - 1) % 2
        with cols[col_idx]:
            chosen_obs = st.selectbox(f"Scene {i} Obstacle:", options=list(OBSTACLE_OPTIONS.keys()), index=0, key=f"obstacle_select_scene_{i}")
            st.session_state.user_scene_obstacles[i] = OBSTACLE_OPTIONS[chosen_obs]

    st.markdown("---")
    if st.button("PROSES & REMIX REFERENSI", type="primary", use_container_width=True):
        run_analysis()

def render_analysis():
    st.title("🔍 Hasil Roadmap De-duplication & Storyboard Mapping")
    analysis = st.session_state.get("analysis", {})
    if not analysis:
        st.info("Belum ada data analisis. Silakan upload referensi di Beranda.")
        return

    orig = analysis.get("original_reference", {})
    remix = analysis.get("remixed_mutation", {})
    storyboard = analysis.get("storyboard_plan", [])

    st.success(f"⏱️ Total Target Durasi & Scene: **{scene_count()} Scene** (~{scene_count() * 8} detik total durasi video)")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📌 Asli (Video Referensi)")
        st.write(f"**Runner Asli:** {orig.get('runner_asli', '-')}")
        st.write(f"**Boss/Ragdoll Asli:** {orig.get('boss_asli', '-')}")
        st.write(f"**Lintasan Asli:** {orig.get('track_asli', '-')}")

    with col2:
        st.markdown("### 🚀 Hasil Remix AI (Multi-Action & Zero Pop-In)")
        st.write(f"**Runner Baru:** `{remix.get('runner_baru', '-')}`")
        st.write(f"**Target Baru:** `{remix.get('boss_baru', '-')}`")
        st.write(f"**Map Background:** `{remix.get('map_environment', '-')}`")
        st.write(f"**Dudukan Prop:** `{remix.get('prop_stand', '-')}`")

    st.info(f"🔒 **Visual Anchor Token:** `{remix.get('visual_anchor_token', '-')}`")
    st.warning(f"💥 **Aksi Klimaks & Physics Chaos:** {analysis.get('climax_action', '-')}")

    if storyboard:
        st.subheader("📋 Storyboard Terstruktur (Per 8 Detik)")
        for item in storyboard:
            st.write(f"• **Scene {item.get('scene', 1)}:** {item.get('fokus_aksi', '-')}")

    if st.button("LANJUT KELOLA PROMPT ADEGAN", type="primary", use_container_width=True):
        go("scenes")

def render_scenes():
    st.title("🎥 AI Video Prompt Generator (Multi-Action & Persistent Grid)")
    n = scene_count()
    current = st.session_state.current_scene

    st.write(f"### Adegan {current} dari {n}" + (" 💥 (SCENE KLIMAKS COMBO & SACRIFICE FALL)" if current == n else " ⚡ (FAST-PACED DUAL ACTION)"))

    if current not in st.session_state.scene_prompts:
        if st.button(f"Generate Prompt Scene {current}", type="primary"):
            generate_scene_prompt(current)
            st.rerun()

    if current in st.session_state.scene_prompts:
        st.text_area("Prompt AI Video (Copy-Paste ke Google Flow / Kling / Luma):", value=st.session_state.scene_prompts[current], height=180)

        st.subheader("🖼️ Last Frame Bridge (Estafet Frame / Anti-Jump Continuity)")
        uploaded_frame = st.file_uploader(f"Upload Last Frame Scene {current}", type=["png", "jpg", "jpeg"], key=f"frame_{current}")
        if uploaded_frame:
            st.session_state.scene_frames[current] = uploaded_frame
            st.success(f"Frame Scene {current} tersimpan!")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if current > 1 and st.button("← Adegan Sebelumnya"):
                st.session_state.current_scene -= 1
                st.rerun()
        with col2:
            if current < n and st.button("Adegan Berikutnya →", type="primary"):
                st.session_state.current_scene += 1
                st.rerun()

        if current == n:
            st.markdown("---")
            st.subheader("🎯 Finalisasi & SEO Generator (Otomatis)")

            if st.button("🚀 Generate Judul, Hashtag & 18 Tags Unik", type="primary", use_container_width=True):
                client = get_client()
                if client:
                    prompt = f"""
Bertindaklah sebagai Pakar Algoritma YouTube & TikTok.
Berdasarkan data remix UGC berikut: {json.dumps(st.session_state.analysis, ensure_ascii=False)}

Buatkan format SEO lengkap dalam bentuk JSON terstruktur dengan ketentuan:
1. "judul": [3 Pilihan Judul singkat, memancing curiosity gap, & CTR tinggi],
2. "deskripsi": "Deskripsi cerita singkat mengandung kata kunci natural + WAJIB ADA CALL TO ACTION (CTA) ajakan untuk Komen, Like, Subscribe, dan Nyalakan Lonceng",
3. "tags": [Tepat 18 Tags SEO unik berbahasa Inggris tanpa duplikat]
"""
                    with st.spinner("Meracik Judul, CTA, dan 18 Tags SEO Unik via Gemini AI..."):
                        try:
                            raw_seo = ask(client, prompt, json_mode=True)
                            st.session_state.seo = extract_json(raw_seo)
                            st.success("✨ Metadata & SEO Berhasil Digenerate!")
                        except Exception as exc:
                            st.error(f"Gagal generate SEO: {exc}")

            seo_data = st.session_state.get("seo", {})
            if seo_data:
                st.markdown("#### 📝 Pilihan Judul Viral (CTR Tinggi):")
                titles = seo_data.get("judul", [])
                if isinstance(titles, list):
                    for idx, t in enumerate(titles, 1):
                        st.code(f"{idx}. {t}")
                else:
                    st.code(str(titles))

                st.markdown("#### 📄 Deskripsi & CTA:")
                st.text(seo_data.get("deskripsi", ""))

                st.markdown("#### 🏷️ 18 Tags Global Unik:")
                tags_list = seo_data.get("tags", [])
                if isinstance(tags_list, list):
                    st.code(", ".join(tags_list))
                else:
                    st.code(str(tags_list))

def render_seo():
    st.title("🚀 SEO & Metadata Engine")
    seo_data = st.session_state.get("seo", {})
    if seo_data:
        st.json(seo_data)
    else:
        st.info("Selesaikan prompt scene terlebih dahulu untuk menggenerate SEO.")

# SIDEBAR ROUTER
with st.sidebar:
    st.title("🧭 Navigasi Studio")
    st.text_input("Gemini API Key", key="api_key", type="password", help="Masukkan API Key Google Gemini Anda di sini.")
    st.markdown("---")
    if st.button("🏠 Beranda / Input Referensi", use_container_width=True):
        go("home")
    if st.button("🔍 Hasil Analysis Roadmap", use_container_width=True):
        go("analysis")
    if st.button("🎥 Prompt Generator per Scene", use_container_width=True):
        go("scenes")
    if st.button("🚀 Metadata & SEO Center", use_container_width=True):
        go("seo")

# PAGE ROUTER EXECUTION
page = st.session_state.page
if page == "home":
    render_home()
elif page == "analysis":
    render_analysis()
elif page == "scenes":
    render_scenes()
elif page == "seo":
    render_seo()
