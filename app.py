import json
import streamlit as st
from engine import (
    APP_VERSION, MAX_FILE_SIZE_MB, DURATION_SCENES, STYLE_OPTIONS, CAMERA_OPTIONS,
    RUNNER_PRESETS, TARGET_IDLE_PRESETS, TARGET_DOLL_PRESETS, MAP_OPTIONS,
    PROP_STAND_OPTIONS, CLIMAX_ACTION_OPTIONS, MANEUVER_OPTIONS, OBSTACLE_OPTIONS,
    ASPECT_OPTIONS, ask, extract_json, scene_count, get_client, run_analysis,
    generate_scene_prompt
)

# ==========================================
# 1. PAGE CONFIG & STATE INITIALIZATION
# ==========================================
st.set_page_config(page_title="UGC Remix Studio v14.2", page_icon="🎬", layout="wide")

DEFAULTS = {
    "page": "home",
    "api_key": "",
    "reference_file": None,
    "reference_text": "",
    "visual_style": STYLE_OPTIONS[0],
    "selected_camera": CAMERA_OPTIONS[0],
    "runner_choice": RUNNER_PRESETS[1],
    "target_idle_choice": TARGET_IDLE_PRESETS[0],
    "target_doll_choice": TARGET_DOLL_PRESETS[0],
    "custom_runner": "",
    "selected_map": MAP_OPTIONS[0],
    "selected_prop_stand": PROP_STAND_OPTIONS[0],
    "selected_climax_action": CLIMAX_ACTION_OPTIONS[0],
    "aspect_ratio": ASPECT_OPTIONS[0],
    "duration": "Auto (Sesuai Durasi & Video Referensi)",
    "custom_instruction": "",
    "user_scene_obstacles": {},
    "user_scene_maneuvers": {},
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

# ==========================================
# 2. UI VIEWS
# ==========================================
def render_home():
    st.title("🎬 UGC Remix Studio v14.2")
    st.caption(f"Engine Otomasi Konten 3D Game Challenge ({APP_VERSION}).")

    st.subheader("1. Referensi Video / Skenario")
    st.file_uploader(f"Upload Video Referensi (Maks {MAX_FILE_SIZE_MB}MB)", type=["mp4", "mov", "webm"], key="ref_file_input")
    st.text_area("Deskripsi Referensi Manual", key="reference_text", height=80, placeholder="Contoh: Video lari menendang dua boneka berurutan...")

    st.subheader("2. Pilihan Karakter Runner & Target Ragdoll (Copyright-Safe)")
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        st.selectbox("🏃 Pilih Preset Karakter Runner:", RUNNER_PRESETS, key="runner_choice")
        if st.session_state.runner_choice == "Custom / Ketik Sendiri":
            st.text_input("Tulis Deskripsi Karakter Bebas Kamu:", key="custom_runner", placeholder="Misal: Karakter anomali unik...")
    with col_k2:
        st.selectbox("🎯 Pilih Karakter Target / Ragdoll (Copyright-Safe):", TARGET_DOLL_PRESETS, key="target_doll_choice")
    with col_k3:
        st.selectbox("🎭 Gaya Gerakan Idle Target (Sebelum Ditendang):", TARGET_IDLE_PRESETS, key="target_idle_choice")

    st.subheader("3. Modifikasi Manual Map, Dudukan & Aksi Klimaks")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.selectbox("🗺️ Map Environment Background:", MAP_OPTIONS, key="selected_map")
    with col_m2:
        st.selectbox("🎯 Dudukan / Pijakan Target:", PROP_STAND_OPTIONS, key="selected_prop_stand")
    with col_m3:
        st.selectbox("💥 Aksi Klimaks & Physics Chaos:", CLIMAX_ACTION_OPTIONS, key="selected_climax_action")

    st.subheader("4. Pengaturan Visual, Pergerakan Kamera, Rasio Aspek & Target Durasi")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("🎨 Gaya Visual", STYLE_OPTIONS, key="visual_style")
        st.selectbox("📷 Pergerakan Kamera (Flow AI Camera):", CAMERA_OPTIONS, key="selected_camera")
        st.selectbox("📐 Rasio Aspek Video", ASPECT_OPTIONS, key="aspect_ratio")
    with col2:
        st.selectbox("⏱️ Target Durasi & Jumlah Scene", list(DURATION_SCENES.keys()), key="duration")
        st.text_area("📝 Instruksi Tambahan (Opsional)", key="custom_instruction", height=80, placeholder="Misal: Buat jarak antar boneka lebih dekat...")

    st.markdown("---")
    st.subheader("🧭 Navigasi Rintangan & Manuver Parkour Konyol Per-Scene")
    calculated_scenes = DURATION_SCENES.get(st.session_state.duration, 0) or st.session_state.get("detected_scenes", 4)
    st.write(f"**Total Dynamic Scene Settings:** {calculated_scenes} Scene ({calculated_scenes * 8} Detik Total)")

    for i in range(1, calculated_scenes + 1):
        st.markdown(f"**📍 Pengaturan Scene {i}:**")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            chosen_obs = st.selectbox(f"Scene {i} Rintangan Track:", options=list(OBSTACLE_OPTIONS.keys()), index=0, key=f"obstacle_select_scene_{i}")
            st.session_state.user_scene_obstacles[i] = OBSTACLE_OPTIONS[chosen_obs]
        with col_s2:
            chosen_man = st.selectbox(f"Scene {i} Manuver Parkour Konyol:", options=MANEUVER_OPTIONS, index=0, key=f"maneuver_select_scene_{i}")
            st.session_state.user_scene_maneuvers[i] = chosen_man

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
        st.markdown("### 🚀 Hasil Remix AI (Flow AI No-Edit Optimized)")
        st.write(f"**Runner Baru:** `{remix.get('runner_baru', '-')}`")
        st.write(f"**Target Baru (Safe):** `{remix.get('boss_baru', '-')}`")
        st.write(f"**Gaya Idle Target:** `{remix.get('target_idle_behavior', '-')}`")
        st.write(f"**Gaya Kamera:** `{remix.get('camera_movement', '-')}`")
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
    st.title("🎥 Flow AI Video Prompt Generator (Ready to Copy-Paste)")
    n = scene_count()
    current = st.session_state.current_scene

    st.write(f"### Adegan {current} dari {n}" + (" 💥 (SCENE KLIMAKS COMBO & SACRIFICE FALL)" if current == n else " ⚡ (FAST-PACED DUAL ACTION & FOOTING LOCK)"))

    if current not in st.session_state.scene_prompts:
        col_g1, col_g2 = st.columns([1, 1])
        with col_g1:
            if st.button(f"Generate Prompt Scene {current}", type="primary", use_container_width=True):
                with st.spinner(f"Menyusun Prompt Scene {current}..."):
                    if generate_scene_prompt(current):
                        st.rerun()
        with col_g2:
            if st.button("⚡ Generate ALL Scenes Sekaligus", use_container_width=True):
                progress = st.progress(0)
                for s in range(1, n + 1):
                    with st.spinner(f"Menyusun Prompt Scene {s} dari {n}..."):
                        generate_scene_prompt(s)
                    progress.progress(s / n)
                st.rerun()

    if current in st.session_state.scene_prompts:
        st.text_area("Prompt AI Video (Langsung Copy-Paste ke Flow AI):", value=st.session_state.scene_prompts[current], height=220)

        st.subheader("🖼️ Last Frame Bridge (Estafet Frame / Anti-Jump Continuity)")
        uploaded_frame = st.file_uploader(f"Upload Last Frame Scene {current} (Otomatis Dibedah AI untuk Prompt Scene {current + 1})", type=["png", "jpg", "jpeg"], key=f"frame_{current}")
        if uploaded_frame:
            st.session_state.scene_frames[current] = uploaded_frame
            st.success(f"Frame Scene {current} tersimpan & aktif sebagai visual bridge ke Scene berikutnya!")

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
            st.subheader("🎯 Finalisasi & SEO Generator (Otomatis + Hashtag Relevan)")

            if st.button("🚀 Generate Judul, Deskripsi CTA, Hashtag & 18 Tags Unik", type="primary", use_container_width=True):
                client = get_client()
                if client:
                    prompt = f"""
Bertindaklah sebagai Pakar Algoritma YouTube & TikTok.
Berdasarkan data remix UGC berikut: {json.dumps(st.session_state.analysis, ensure_ascii=False)}

Buatkan format SEO lengkap dalam bentuk JSON terstruktur dengan ketentuan:
1. "judul": [3 Pilihan Judul singkat, memancing curiosity gap, & CTR tinggi],
2. "deskripsi": "Deskripsi cerita singkat mengandung kata kunci natural + WAJIB ADA CALL TO ACTION (CTA) ajakan untuk Komen, Like, Subscribe, dan Nyalakan Lonceng",
3. "hashtags": [8 Hashtag viral & relevan dipisah spasi, contoh: #UGC #3DParkour #FYP],
4. "tags": [Tepat 18 Tags SEO unik berbahasa Inggris tanpa duplikat]
"""
                    with st.spinner("Meracik Judul, CTA, Hashtag Viral, dan 18 Tags SEO Unik via Gemini AI..."):
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

                st.markdown("#### 0️⃣ Hashtag Relevan:")
                hashtags = seo_data.get("hashtags", [])
                if isinstance(hashtags, list):
                    st.code(" ".join(hashtags))
                else:
                    st.code(str(hashtags))

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

# ==========================================
# 3. SIDEBAR & ROUTER EXECUTION
# ==========================================
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
