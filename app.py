import json
import re
import time
import os

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="UGC Remix Studio — Ultimate 3D Parkour Engine v9.2", page_icon="🎬", layout="wide")

MODEL_NAME = "gemini-3.6-flash"
APP_VERSION = "9.2 — Ultimate 1:1 Roadmap, Permanent Multi-Container Entities & Object Persistence"

DURATION_SCENES = {
    "Auto (Sesuai Durasi & Video Referensi)": 0,
    "8 detik (1 Scene - Shorts Kilat)": 1,
    "16 detik (2 Scene - Shorts Standar)": 2,
    "24 detik (3 Scene)": 3,
    "32 detik (4 Scene)": 4,
    "40 detik (5 Scene)": 5,
    "60 detik (8 Scene - 1 Menit Long)": 8,
    "120 detik (15 Scene - 2 Menit Long)": 15,
    "180 detik (22 Scene - 3 Menit Long Full Challenge)": 22,
}

STYLE_OPTIONS = [
    "GTA V Modded Gameplay Style",
    "3D Animated Game Graphics",
    "Unreal Engine 5 Parkour Render",
    "Sinematik Realistis 3D",
]

# REVISI 1: KARAKTER UTAMA BARU (100% SAFE COPYRIGHT & KOCAK)
RUNNER_PRESETS = [
    "Custom / Ketik Sendiri",
    "Pocong Gesit (Hantu lokal berbalut kain kafan putih melompat absurd & kencang)",
    "Bebek Karet Raksasa (Mainan bebek mandi kuning licin membal dengan kaki robotik)",
    "Karakter Roblox / Blocky Noob (Karakter balok ikonik gaya voxel yang pecah pas kena pukul)",
    "Sktetelons / Tengkorak Gila (Karakter kerangka tulang hidup dengan ragdoll physics mantap)",
    "Fat Orange Cat (Kucing oranye gemuk berjaket hoodie)",
    "Funny Green Frog (Katak hijau nyeleneh berkacamata hitam)",
    "Blocky Voxel Man (Karakter balok gaya retro game independen)",
    "Inflatable Dinosaur (Kostum dinosaurus tiup warna hijau)",
    "Minecraft Creeper Style (Karakter makhluk hijau kotak khas Minecraft)",
    "Gingerbread Cookie (Manusia kue jahe hidup)",
    "Minecraft Blocky Zombie (Karakter mayat hidup kotak-kotak ala Minecraft)",
    "Tung Tung Sahur (Karakter anomali ikonik meme sahur yang absurd)",
    "Tralalero Tralala (Karakter absurd ala hiu bermata lebar berkaki sneakers)",
    "Udindindun (Karakter khas Italian brainrot yang konyol dan nyeleneh)"
]

# KAMUS OPTIONS RINTANGAN & NAVIGASI DINAMIS (SIAP DISUNTIKKAN KE PROMPT VEO)
OBSTACLE_OPTIONS = {
    "None / Lari Datar": "",
    "🪜 Steep Staircase (Naik Tangga Besi)": "MANDATORY NAVIGATIONAL ACTION: Runner approaches and rapidly climbs up a steep metal staircase/ladder to reach a higher elevated container platform.",
    "🛝 Glass Pipe Slide (Meluncur Perosotan)": "MANDATORY NAVIGATIONAL ACTION: Runner slides down a transparent glass pipe/slide at high speed before landing gracefully.",
    "🎯 Bounce Pad / Trampolin (Pelontar Vertikal)": "MANDATORY NAVIGATIONAL ACTION: Runner steps onto a high-impulse launch pad and bounces high up into the air to the next platform.",
    "🌉 Thin Steel Beam (Jembatan Besi Sempit)": "MANDATORY NAVIGATIONAL ACTION: Runner carefully sprints across a narrow steel beam balancing high over open water.",
    "🪢 Zipline / Swing Rope (Bergelayut Tali)": "MANDATORY NAVIGATIONAL ACTION: Runner leaps off the edge, grabs an overhead zip-line/rope, and swings across a massive gap.",
    "⛓️ Swinging Pendulum (Menghindari Palu)": "ENVIRONMENT MECHANIC: Giant swinging pendulums obstruct the path; runner must weave and dodge around them skillfully."
}

ASPECT_OPTIONS = ["9:16 — Shorts / Reels / TikTok", "16:9 — YouTube Long", "1:1 — Kotak"]

DEFAULTS = {
    "page": "home",
    "api_key": "",
    "reference_file": None,
    "reference_text": "",
    "visual_style": STYLE_OPTIONS[0],
    "runner_choice": RUNNER_PRESETS[1],
    "custom_runner": "",
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


def extract_json(text: str):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass

    starts = [p for p in (text.find("{"), text.find("[")) if p >= 0]
    if not starts:
        raise ValueError("Respons AI tidak berisi JSON yang valid.")
    start = min(starts)
    for end in range(len(text), start, -1):
        try:
            return json.loads(text[start:end].strip())
        except Exception:
            continue
    raise ValueError("Respons AI tidak dapat diparse sebagai JSON.")


def ask(client, prompt: str, parts=None, json_mode: bool = False) -> str:
    media_parts = list(parts or [])
    content_parts = media_parts + [types.Part.from_text(text=prompt)]
    contents = [types.Content(role="user", parts=content_parts)]

    config_kwargs = {"temperature": 0.4}
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            text = getattr(response, "text", None)
            if not text:
                raise RuntimeError("Gemini mengembalikan respons kosong.")
            return text
        except Exception as exc:
            if attempt == 2:
                raise RuntimeError(f"Gagal terhubung ke Gemini: {exc}")
            time.sleep(1.5)
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
2. PERMANENT OBJECT PERSISTENCE & MULTI-ACTION: Setiap kotak kontainer di sepanjang jalur **wajib terisi objek/boneka target sejak frame pertama (zero pop-in)**. Dalam durasi 1 scene (~8 detik), rancang agar runner melakukan **minimal 2 aksi berturut-turut** (contoh: menendang boneka pertama di kontainer awal, lalu langsung maju beberapa langkah untuk memukul/menendang boneka kedua yang berdiri sejajar di depannya sebelum berbelok).
3. Rancang mutasi karakter runner utama menjadi: "{chosen_runner}", serta sesuaikan target boss/ragdoll dengan opsi yang aman hak cipta (copyright-safe).
4. Pastikan jalur lari terkunci di atas kontainer (tidak terjun ke laut), dan ada transisi belokan yang mulus setelah aksi ganda selesai.

PENGATURAN:
- Style Visual: {st.session_state.visual_style} (Pencahayaan terang benderang siang hari bolong / noon daylight, langit biru cerah, warna kontras tinggi)
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
    "boss_baru": "Deretan boneka/target ragdoll unik yang berdiri berurutan di setiap kontainer sejak awal dan aktif bergerak",
    "track_baru": "Lintasan kontainer 1:1 dengan boneka ganda yang berderet rapi tanpa ada kontainer kosong",
    "visual_anchor_token": "Deskripsi ketat kosmetik karakter pilihan user agar konsisten",
    "alasan_remix": "Alasan modifikasi"
  }},
  "storyboard_plan": [
    {{"scene": 1, "fokus_aksi": "Runner berlari, melakukan aksi ganda: menendang boneka pertama di kontainer awal, lalu langsung maju cepat untuk memukul boneka kedua di kontainer berikutnya sebelum berbelok tajam."}},
    {{"scene": 2, "fokus_aksi": "Melanjutkan rintangan berikutnya dengan deretan boneka aktif selanjutnya."}},
    {{"scene": 3, "fokus_aksi": "Klimaks aksi ganda penutupan dan efek fisika ragdoll massal."}}
  ],
  "climax_action": "Aksi ganda menendang dan memukul dua boneka berurutan dengan efek fisika domino",
  "spatial_layout": "Third-person dynamic tracking shot with persistent multi-object placement on every container surface"
}}
"""
    with st.spinner("Membedah roadmap 1:1 & menyusun skema multi-action boneka permanen..."):
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

    scene_focus = "Melanjutkan aksi lari dan rangkaian rintangan di atas jalur kontainer."
    if storyboard and len(storyboard) >= scene_number:
        scene_focus = storyboard[scene_number - 1].get("fokus_aksi", scene_focus)

    # PEMBACAAN RINTANGAN OPSIONAL USER PER SCENE
    custom_obstacle_instruction = st.session_state.user_scene_obstacles.get(scene_number, "")
    obstacle_inject_str = ""
    if custom_obstacle_instruction:
        obstacle_inject_str = f"SPECIAL SCENE OBSTACLE MECHANIC: {custom_obstacle_instruction}"

    prev_frame_context = ""
    if scene_number > 1 and (scene_number - 1) in st.session_state.scene_frames:
        prev_frame_context = f"STRICT CONTINUITY & SPATIAL LOCK: Scene {scene_number} MUST start precisely at the exact spatial coordinates and container surface level where Scene {scene_number-1} ended. Zero teleportation, seamless continuation."

    if scene_number == 1:
        camera_desc = "Dynamic third-person trailing camera locked tightly behind the runner, keeping all container surfaces clearly visible."
        action_desc = f"""
CRITICAL MULTI-ACTION & PERMANENT OBJECT RULES FOR SCENE 1:
1. PERSISTENT GRID OBJECTS (NO EMPTY CONTAINERS): Every single metal container along the path is pre-populated with active, living target dolls/dummies ({mutation.get('boss_baru')}) standing fully visible right from frame one (zero pop-in, zero empty spaces).
2. DUAL-ACTION PACING (2 ACTIONS IN 8 SECONDS): Within this 8-second clip, the runner ({mutation.get('runner_baru')}) must execute TWO distinct interactions sequentially: 
   - Action A: Sprint and kick the first target doll off the container edge.
   - Action B: Immediately take a few fast strides forward to punch or kick the second target doll standing on the next consecutive container before executing a sharp right turn.
3. SURFACE CONFINEMENT: The runner's feet stay locked to the container tops. No falling into the water.
"""
    elif is_final_scene:
        camera_desc = "Dramatic close-up tracking zoom, shifting into cinematic slow-motion on final impact."
        action_desc = f"CLIMAX DUAL-ACTION PAYOFF: The runner reaches the final section, executing a powerful double-hit combo on the remaining active targets, triggering an exaggerated chain-reaction ragdoll physics explosion with comedic sound cues."
    else:
        camera_desc = "High-octane sweeping third-person tracking shot across the obstacle course."
        action_desc = f"ROADMAP CONTINUATION: {scene_focus}. Multiple target entities are fully populated and active across all containers from the start."

    audio_cues = "Immersive game audio: heavy footfalls on corrugated metal, consecutive impact thuds, roaring ocean wind, and dynamic ragdoll physics sound cues."

    prompt = f"""
Write ONE ultra-detailed AI video generation prompt in ENGLISH for Scene {scene_number} of {total_scenes} (approx. 8 seconds segment).

ENVIRONMENT & AESTHETICS:
- Bright daytime lighting, vivid sunny sky, clear blue atmosphere with soft white clouds, high-contrast colorful 3D game aesthetics (Unreal Engine / GTA V mod style). NO dark or gloomy environments.

ASSETS & PERMANENT ENTITIES LOCK:
- Style: {st.session_state.visual_style}
- Aspect Ratio: {st.session_state.aspect_ratio}
- Runner Character: {mutation.get('visual_anchor_token')}
- Target Entities (Multiple active dolls/dummies standing permanently on every container from frame one, zero empty containers): {mutation.get('boss_baru')}
- Environment Path: {mutation.get('track_baru')}

NAVIGATIONAL ACTION OVERRIDE:
{obstacle_inject_str}

PHYSICS & MULTI-ACTION LAWS (MANDATORY):
- Multi-action density: The 8-second video must contain TWO distinct hits/kicks in sequence (e.g., kicking the first doll, then immediately punching/kicking the second doll placed closely ahead).
- Surface confinement: Runner stays strictly on container roofs or specified obstacle path, executing a sharp right turn transition after the second action. No falling into the water.
- Camera: {camera_desc}
- Audio: {audio_cues}
{prev_frame_context}

RULES:
Output ONLY the final raw English prompt without any markdown formatting, bullet points, or extra text.
"""
    with st.spinner(f"Menyusun Ulang Multi-Action & Boneka Permanen Scene {scene_number}..."):
        try:
            res_prompt = ask(client, prompt, json_mode=False)
            st.session_state.scene_prompts[scene_number] = res_prompt.strip()
            return True
        except Exception as exc:
            st.error(f"Gagal menyusun prompt: {exc}")
            return False


def render_home():
    st.title("🎬 UGC Remix Studio v9.2")
    st.caption("Engine Otomasi Konten 3D Game & Parkour Challenge dengan Multi-Action Density & Permanent Multi-Container Entities.")

    st.subheader("1. Referensi Video / Skenario")
    st.file_uploader("Upload Video Referensi (Shorts atau Long Video)", type=["mp4", "mov", "webm"], key="ref_file_input")

    st.caption("Atau tulis deskripsi referensi manual jika tidak ada video:")
    st.text_area("Deskripsi Referensi Manual", key="reference_text", height=80, placeholder="Contoh: Video lari menendang dua boneka berurutan di kontainer...")

    st.subheader("2. Pilihan Karakter Runner Utama (Bebas Copyright & Brainrot)")
    st.selectbox("Pilih Preset Karakter Runner:", RUNNER_PRESETS, key="runner_choice")
    if st.session_state.runner_choice == "Custom / Ketik Sendiri":
        st.text_input("Tulis Deskripsi Karakter Bebas Kamu:", key="custom_runner", placeholder="Misal: Karakter anomali unik...")

    st.subheader("3. Pengaturan Visual, Rasio Aspek & Target Durasi")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Gaya Visual", STYLE_OPTIONS, key="visual_style")
        st.selectbox("Rasio Aspek Video", ASPECT_OPTIONS, key="aspect_ratio")
    with col2:
        st.selectbox("Target Durasi & Jumlah Scene", list(DURATION_SCENES.keys()), key="duration")
        st.text_area("Instruksi Tambahan (Opsional)", key="custom_instruction", height=80, placeholder="Misal: Buat jarak antar boneka lebih dekat...")

    # INTEGRASI FITUR DINAMIS DROPDOWN RINTANGAN PER-SCENE (OPSIONAL)
    st.markdown("---")
    st.subheader("🧭 Navigasi & Rintangan Jalur Per-Scene (Opsional)")
    st.caption("Pilih rintangan khusus hanya pada scene yang kamu inginkan. Jika dibiarkan 'None / Lari Datar', runner hanya lari biasa di atas kontainer.")

    calculated_scenes = DURATION_SCENES.get(st.session_state.duration, 0)
    if calculated_scenes == 0:
        calculated_scenes = st.session_state.get("detected_scenes", 4)

    st.write(f"**Total Dynamic Scene Settings:** {calculated_scenes} Scene ({calculated_scenes * 8} Detik Total)")

    cols = st.columns(2)
    for i in range(1, calculated_scenes + 1):
        col_idx = (i - 1) % 2
        with cols[col_idx]:
            chosen_obs = st.selectbox(
                f"Scene {i} Obstacle:",
                options=list(OBSTACLE_OPTIONS.keys()),
                index=0,
                key=f"obstacle_select_scene_{i}"
            )
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

    st.success(f"⏱️ Total Target Durasi & Scene: **{scene_count()} Scene** (~{scene_count() * 8} detik total durasi video dengan aksi ganda)")

    st.subheader("💡 Perbandingan Mutasi Roadmap 1:1 (Anti Plagiarisme)")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📌 Asli (Video Referensi)")
        st.write(f"**Runner Asli:** {orig.get('runner_asli', '-')}")
        st.write(f"**Boss/Ragdoll Asli:** {orig.get('boss_asli', '-')}")
        st.write(f"**Lintasan Asli:** {orig.get('track_asli', '-')}")

    with col2:
        st.markdown("### 🚀 Hasil Remix AI (Multi-Action & Permanent Objects)")
        st.write(f"**Runner Baru:** `{remix.get('runner_baru', '-')}`")
        st.write(f"**Target Baru:** `{remix.get('boss_baru', '-')}`")
        st.write(f"**Lintasan Baru:** `{remix.get('track_baru', '-')}`")

    st.info(f"🔒 **Visual Anchor Token (Anti Karakter Berubah):** `{remix.get('visual_anchor_token', '-')}`")
    st.warning(f"💥 **Aksi Klimaks & Fisika Ragdoll:** {analysis.get('climax_action', '-')}")

    if storyboard:
        st.subheader("📋 Storyboard Terstruktur (Per 8 Detik dengan Aksi Ganda)")
        for item in storyboard:
            st.write(f"• **Scene {item.get('scene', 1)}:** {item.get('fokus_aksi', '-')}")

    if st.button("LANJUT KELOLA PROMPT ADEGAN", type="primary", use_container_width=True):
        go("scenes")


# REVISI 2 & 3: INTEGRASI RENDER SEO DINAMIS DI MAIN BODY PADA SCENE TERAKHIR
def render_scenes():
    st.title("🎥 AI Video Prompt Generator (Multi-Action & Persistent Grid)")
    n = scene_count()
    current = st.session_state.current_scene

    st.write(f"### Adegan {current} dari {n}" + (" 💥 (SCENE KLIMAKS AKSI GANDA & RAGDOLL CHAOS)" if current == n else " ⚡ (FAST-PACED DUAL ACTION)"))

    if current not in st.session_state.scene_prompts:
        if st.button(f"Generate Prompt Scene {current}", type="primary"):
            generate_scene_prompt(current)
            st.rerun()

    if current in st.session_state.scene_prompts:
        st.text_area("Prompt AI Video (Copy-Paste ke Google Flow / Kling / Luma):", value=st.session_state.scene_prompts[current], height=160)

        st.subheader("🖼️ Last Frame Bridge (Estafet Frame / Anti-Jump Continuity)")
        st.caption("UPLOAD SCREENSHOT FRAME TERAKHIR dari video hasil Scene ini. Ini wajib di-upload agar Scene berikutnya tidak mengalami loncatan posisi.")
        uploaded_frame = st.file_uploader(f"Upload Last Frame Scene {current}", type=["png", "jpg", "jpeg"], key=f"frame_{current}")
        if uploaded_frame:
            st.session_state.scene_frames[current] = uploaded_frame
            st.success(f"Frame Scene {current} tersimpan! Prompt Scene {current+1} terkunci pada koordinat posisi ini.")

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

        
        # JIKA BERADA DI SCENE TERAKHIR (DINAMIS SIKAP BERAPAPUN TOTAL SCENE-NYA), TAMPILKAN TOMBOL SEO DI MAIN BODY
        if current == n:
            st.markdown("---")
            st.subheader("🎯 Finalisasi & SEO Generator (Otomatis)")
            st.write("Seluruh scene telah selesai dirancang. Klik tombol di bawah ini untuk meracik Judul, Deskripsi CTA, dan 18 Tags SEO global.")

            if st.button("🚀 Generate Judul, Hashtag & 18 Tags Unik", type="primary", use_container_width=True):
                client = get_client()
                if client:
                    prompt = f"""
Bertindaklah sebagai Pakar Algoritma YouTube & TikTok.
Berdasarkan data remix UGC berikut: {json.dumps(st.session_state.analysis, ensure_ascii=False)}

Buatkan format SEO lengkap dalam bentuk JSON terstruktur dengan ketentuan:
1. "judul": [3 Pilihan Judul singkat, memancing curiosity gap, & CTR tinggi],
2. "deskripsi": "Deskripsi cerita singkat mengandung kata kunci natural + WAJIB ADA CALL TO ACTION (CTA) ajakan untuk Komen seberapa seru videonya, Like, Subscribe, dan Bunyikan Lonceng Notifikasi",
3. "tags": [Tepat 18 Tags SEO unik berbahasa Inggris tanpa duplikat]
"""
                    with st.spinner("Meracik Judul, CTA, dan 18 Tags SEO Unik via Gemini AI..."):
                        try:
                            raw_seo = ask(client, prompt, json_mode=True)
                            st.session_state.seo = extract_json(raw_seo)
                            st.success("✨ Metadata & SEO Berhasil Digenerate!")
                        except Exception as exc:
                            st.error(f"Gagal generate SEO: {exc}")

            # RENDER HASIL SEO JIKA SUDAH ADA DATA
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


# RENDER APABILA DI-AKSES MANUAL VIA SIDEBAR / PAGE ROUTER
def render_seo():
    st.title("🚀 SEO & Metadata Engine (Algoritma YouTube / TikTok)")
    st.caption("Menghasilkan Judul pemancing CTR, Deskripsi tertarget, Hashtag multi-tier, dan **18 Tags Global Unik** tanpa duplikat.")

    if st.button("Generate Judul, Hashtag & 18 Tags Unik", type="primary"):
        client = get_client()
        if client:
            prompt = f"""
Bertindaklah sebagai Pakar Algoritma YouTube & TikTok.
Berdasarkan data remix UGC berikut: {json.dumps(st.session_state.analysis, ensure_ascii=False)}

Buatkan format SEO lengkap dalam bentuk JSON terstruktur dengan ketentuan:
1. "judul": [3 Pilihan Judul singkat, memancing curiosity gap, & CTR tinggi],
2. "deskripsi": "Deskripsi cerita singkat mengandung kata kunci natural + WAJIB ADA CALL TO ACTION (CTA) ajakan untuk Komen seberapa seru videonya, Like, Subscribe, dan Bunyikan Lonceng Notifikasi",
3. "tags": [Tepat 18 Tags SEO unik berbahasa Inggris tanpa duplikat]
"""
            with st.spinner("Generating SEO..."):
                try:
                    raw_seo = ask(client, prompt, json_mode=True)
                    st.session_state.seo = extract_json(raw_seo)
                    st.success("Berhasil!")
                except Exception as exc:
                    st.error(f"Gagal: {exc}")

    seo_data = st.session_state.get("seo", {})
    if seo_data:
        st.json(seo_data)


# SIDEBAR & MAIN NAVIGATION ROUTER
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


# PAGE ROUTING
page = st.session_state.page
if page == "home":
    render_home()
elif page == "analysis":
    render_analysis()
elif page == "scenes":
    render_scenes()
elif page == "seo":
    render_seo()
