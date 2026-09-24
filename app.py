import json
import re
import time
import os

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="UGC Remix Studio — Ultimate 3D Parkour Engine v9.3",
    page_icon="🎬",
    layout="wide"
)

MODEL_NAME = "gemini-3.6-flash"
APP_VERSION = "9.3 — Ultimate 1:1 Roadmap, Dynamic Maps, Prop Stands & Custom Climax Action Engine"

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

MAP_OPTIONS = [
    "Auto (Ikuti Remix UGC)",
    "Maze Bank Tower Rooftop (Downtown Los Santos Skyscraper)",
    "Mount Chiliad Mega Ramp & Ridge (High Mountain Canyon)",
    "Pacific Ocean Docks & Shipping Containers (Sea Port)",
    "Sky-High Cloud Ramp (Floating Infinite Cloud Void)",
    "Alamo Sea Desert Airfield Ramp (Sandy Shores Valley)",
    "Del Perro Pier Coastal Boardwalk (Beach Ferris Wheel View)",
    "Fort Zancudo Military Airbase Overhead (Jet Base View)",
    "Zancudo River Canyon Bridge (Red Rock River)",
    "Neon City Cyberpunk Night (Glow Los Santos Nightlife)",
    "Lava Volcano Caldera Arena (Active Volcano Lava Pit)"
]

PROP_STAND_OPTIONS = [
    "Auto (Ikuti Remix UGC)",
    "Direct Concrete Rooftop / Flat Container Surface",
    "Giant Yoga / Exercise Fitness Balls (Colored Balls)",
    "Wooden Cargo Barrels & Metal Oil Drums",
    "Stacked Rubber Tires & Wheels",
    "Vertical Trampoline Impulse Pads",
    "Glass Ice Cubes & Translucent Pillars",
    "Rotating Wooden Cylinder Log Rollers",
    "High Concrete Construction Blocks",
    "Floating Pool Inflatable Donuts",
    "Steel Spring Coil Platforms"
]

CLIMAX_ACTION_OPTIONS = [
    "Auto (Ikuti Remix UGC)",
    "Double Hit Combo + Sacrifice Fall (Runner hits 2 targets & falls off edge together)",
    "Flying Knee Jump Kick + Domino Ragdoll Collapse",
    "360 Spinning Backfist + Abyss Drag Drop",
    "Double Dropkick + Explosion Bounce Sacrifice Fall",
    "Superman Punch & Barrel Destruction + Full Ragdoll Fall",
    "Tackle & Hug Fall (Kamikaze Drag off the cliff)",
    "High-Velocity Running Sweep Kick + Terpelanting Off-Limit",
    "Consecutive Punch-Kick Combo (3 Hits) + Edge Slurry Fall",
    "Trampoline Launch Overhead Smash + Surface Collapse Fall",
    "Sliding Tackle Multi-Target Clear + Edge Overshoot Fall"
]

OBSTACLE_OPTIONS = {
    "None / Lari Datar": "",
    "⛓️ Swinging Giant Pendulums & Hammers": "ENVIRONMENT MECHANIC: Giant swinging pendulums and massive hammers obstruct the path; runner must weave and dodge around them skillfully.",
    "🔥 Flamethrower & Fire Jet Gates": "ENVIRONMENT MECHANIC: Periodic intense fire jets shoot up from the platform surface; runner timing must be precise.",
    "🌀 Rotating Spike Rollers": "ENVIRONMENT MECHANIC: Fast-spinning spiked cylinders block the middle path; runner must leap over them cleanly.",
    "💣 Explosive Red Barrels": "ENVIRONMENT MECHANIC: Highly unstable red explosive barrels line the edges; accidental contact triggers physics blast.",
    "🪓 Oscillating Guillotine Blades": "ENVIRONMENT MECHANIC: Massive razor-sharp guillotine blades drop up and down rapidly across the lane.",
    "🧱 Crushing Hydraulic Pistons": "ENVIRONMENT MECHANIC: Heavy concrete hydraulic blocks punch horizontally across the runner's path.",
    "🌉 Narrow Crumbling Bridge / Glass Tiles": "ENVIRONMENT MECHANIC: Fragile glass tiles and crumbling concrete blocks shatter 1 second after being stepped on.",
    "⚡ Electrified Fence & Laser Barriers": "ENVIRONMENT MECHANIC: High-voltage flickering electric laser barriers force the runner to slide or jump high.",
    "🌀 High-Speed Wind Turbine Fans": "ENVIRONMENT MECHANIC: Industrial wind turbine fans blow strong lateral gusts threatening to push runner off the edge.",
    "🪜 Sky-High Spiral Metal Ladder": "MANDATORY NAVIGATIONAL ACTION: Runner rapidly climbs a steep spiral metal ladder hovering high over open space to reach the elevated container platform."
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
    "map_choice": MAP_OPTIONS[0],
    "prop_stand_choice": PROP_STAND_OPTIONS[0],
    "climax_action_choice": CLIMAX_ACTION_OPTIONS[0],
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

    chosen_map = st.session_state.map_choice
    chosen_stand = st.session_state.prop_stand_choice
    chosen_climax = st.session_state.climax_action_choice

    prompt = f"""
Anda adalah AI Master Creative Director khusus konten viral 3D Game / Parkour / Obstacle Challenge di TikTok & YouTube Shorts.

TUGAS UTAMA (ROADMAP CLONING 1:1 & MULTI-ACTION DENSITY):
1. Bedah video referensi secara menyeluruh. Kloning persis struktur jalur rintangan dan ritme waktunya secara 1:1.
2. PERMANENT OBJECT PERSISTENCE & MULTI-ACTION: Setiap platform/pijakan di sepanjang jalur **wajib terisi objek/boneka target sejak frame pertama (zero pop-in)**. Dalam durasi 1 scene (~8 detik), rancang agar runner melakukan **minimal 2 aksi berturut-turut** (contoh: menendang boneka pertama, lalu maju cepat untuk memukul boneka kedua di pijakan berikutnya).
3. INTEGRASI SETTINGAN USER:
   - Runner Utama: "{chosen_runner}"
   - Arena/Map Location: "{chosen_map}"
   - Target Prop Stand/Pijakan Target: "{chosen_stand}"
   - Aksi Klimaks Penutup (Climax Action): "{chosen_climax}"
4. Pastikan jalur lari terkunci rapat di atas arena tempat berlari dan transisi antar-aksi berjalan mulus.

PENGATURAN VISUAL:
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
    "boss_baru": "Deretan boneka/target ragdoll unik yang berdiri berurutan di atas {chosen_stand} sejak awal dan aktif bergerak",
    "track_baru": "Lintasan arena {chosen_map} dengan target di atas {chosen_stand} yang berderet rapi tanpa ada pijakan kosong",
    "visual_anchor_token": "Deskripsi ketat kosmetik karakter pilihan user agar konsisten",
    "alasan_remix": "Alasan modifikasi"
  }},
  "storyboard_plan": [
    {{"scene": 1, "fokus_aksi": "Runner berlari di arena {chosen_map}, melakukan aksi ganda pada target di atas {chosen_stand}."}},
    {{"scene": 2, "fokus_aksi": "Melanjutkan rintangan berikutnya dengan deretan boneka aktif selanjutnya."}},
    {{"scene": 3, "fokus_aksi": "Klimaks aksi penutupan: {chosen_climax}"}}
  ],
  "climax_action": "{chosen_climax}",
  "spatial_layout": "Third-person dynamic tracking shot in {chosen_map} with persistent target objects on {chosen_stand}"
}}
"""
    with st.spinner("Membedah roadmap 1:1 & menyusun skema multi-action arena..."):
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

    scene_focus = "Melanjutkan aksi lari dan rangkaian rintangan di atas jalur."
    if storyboard and len(storyboard) >= scene_number:
        scene_focus = storyboard[scene_number - 1].get("fokus_aksi", scene_focus)

    # PEMBACAAN RINTANGAN OPSIONAL USER PER SCENE
    custom_obstacle_instruction = st.session_state.user_scene_obstacles.get(scene_number, "")
    obstacle_inject_str = ""
    if custom_obstacle_instruction:
        obstacle_inject_str = f"SPECIAL SCENE OBSTACLE MECHANIC: {custom_obstacle_instruction}"

    # KONTEKS ARENA & STAND OBJEK
    map_context = f"MAP LOCATION ARENA: {st.session_state.map_choice}" if st.session_state.map_choice != "Auto (Ikuti Remix UGC)" else ""
    stand_context = f"TARGET PROP STAND: Targets are elevated/standing directly on {st.session_state.prop_stand_choice}" if st.session_state.prop_stand_choice != "Auto (Ikuti Remix UGC)" else ""
    climax_override = f"MANDATORY CLIMAX ENDING ACTION: {st.session_state.climax_action_choice}" if st.session_state.climax_action_choice != "Auto (Ikuti Remix UGC)" else "CLIMAX DUAL-ACTION PAYOFF: The runner executes a powerful double-hit combo on the remaining active targets with ragdoll physics explosion."

    prev_frame_context = ""
    if scene_number > 1 and (scene_number - 1) in st.session_state.scene_frames:
        prev_frame_context = f"STRICT CONTINUITY & SPATIAL LOCK: Scene {scene_number} MUST start precisely at the exact spatial coordinates and surface level where Scene {scene_number-1} ended. Zero teleportation, seamless continuation."

    if scene_number == 1:
        camera_desc = "Dynamic third-person trailing camera locked tightly behind the runner, keeping all surfaces and targets clearly visible."
        action_desc = f"""
CRITICAL MULTI-ACTION & PERMANENT OBJECT RULES FOR SCENE 1:
1. PERSISTENT GRID OBJECTS (NO EMPTY PLATFORMS): Every single platform surface along the path is pre-populated with active, living target dolls/dummies ({mutation.get('boss_baru')}) standing fully visible right from frame one (zero pop-in, zero empty spaces).
2. DUAL-ACTION PACING (2 ACTIONS IN 8 SECONDS): Within this 8-second clip, the runner ({mutation.get('runner_baru')}) must execute TWO distinct interactions sequentially: 
   - Action A: Sprint and kick/hit the first target doll off the platform edge.
   - Action B: Immediately take a few fast strides forward to punch or kick the second target doll standing on the next consecutive platform surface.
3. SURFACE CONFINEMENT: The runner's feet stay locked strictly to the run surface path.
"""
    elif is_final_scene:
        camera_desc = "Dramatic close-up tracking zoom, shifting into cinematic slow-motion on final impact."
        action_desc = f"{climax_override} Trigger exaggerated ragdoll physics and dynamic camera focus."
    else:
        camera_desc = "High-octane sweeping third-person tracking shot across the obstacle course."
        action_desc = f"ROADMAP CONTINUATION: {scene_focus}. Multiple target entities are fully populated and active across all platforms from the start."

    audio_cues = "Immersive game audio: heavy footfalls, consecutive impact thuds, roaring wind/environment ambient, and dynamic ragdoll physics sound cues."

    prompt = f"""
Write ONE ultra-detailed AI video generation prompt in ENGLISH for Scene {scene_number} of {total_scenes} (approx. 8 seconds segment).

ENVIRONMENT, ARENA & AESTHETICS:
- {map_context}
- Bright daytime lighting, vivid sunny sky, clear atmosphere, high-contrast colorful 3D game aesthetics (Unreal Engine / GTA V mod style). NO dark or gloomy environments.

ASSETS, STANDS & PERMANENT ENTITIES LOCK:
- Style: {st.session_state.visual_style}
- Aspect Ratio: {st.session_state.aspect_ratio}
- Runner Character: {mutation.get('visual_anchor_token')}
- Target Props & Stands: {stand_context}
- Target Entities (Multiple active dolls/dummies standing permanently on every stand surface from frame one, zero empty spaces): {mutation.get('boss_baru')}
- Environment Path: {mutation.get('track_baru')}

NAVIGATIONAL ACTION & OBSTACLE OVERRIDE:
{obstacle_inject_str}

PHYSICS & MULTI-ACTION LAWS (MANDATORY):
- Action Flow: {action_desc}
- Camera: {camera_desc}
- Audio: {audio_cues}
{prev_frame_context}

RULES:
Output ONLY the final raw English prompt without any markdown formatting, bullet points, or extra text.
"""
    with st.spinner(f"Menyusun Ulang Prompt Scene {scene_number}..."):
        try:
            res_prompt = ask(client, prompt, json_mode=False)
            st.session_state.scene_prompts[scene_number] = res_prompt.strip()
            return True
        except Exception as exc:
            st.error(f"Gagal menyusun prompt: {exc}")
            return False
def render_home():
    st.title("🎬 UGC Remix Studio v9.3")
    st.caption("Engine Otomasi Konten 3D Game & Parkour Challenge dengan Dynamic Map, Custom Props Stand & Climax Action Engine.")

    st.subheader("1. Referensi Video / Skenario")
    st.file_uploader("Upload Video Referensi (Shorts atau Long Video)", type=["mp4", "mov", "webm"], key="ref_file_input")

    st.caption("Atau tulis deskripsi referensi manual jika tidak ada video:")
    st.text_area("Deskripsi Referensi Manual", key="reference_text", height=80, placeholder="Contoh: Video lari menendang dua boneka berurutan di atas platform...")

    st.subheader("2. Pilihan Karakter Runner Utama")
    st.selectbox("Pilih Preset Karakter Runner:", RUNNER_PRESETS, key="runner_choice")
    if st.session_state.runner_choice == "Custom / Ketik Sendiri":
        st.text_input("Tulis Deskripsi Karakter Bebas Kamu:", key="custom_runner", placeholder="Misal: Karakter anomali unik...")

    st.subheader("3. Modifikasi Map Arena, Target Stand & Aksi Klimaks (Variasi Tidak Monoton)")
    col_map1, col_map2, col_map3 = st.columns(3)
    with col_map1:
        st.selectbox("Pilih Map Arena / Latar Place:", MAP_OPTIONS, key="map_choice")
    with col_map2:
        st.selectbox("Pilih Pijakan Target / Prop Stand:", PROP_STAND_OPTIONS, key="prop_stand_choice")
    with col_map3:
        st.selectbox("Pilih Gaya Aksi Klimaks Penutup:", CLIMAX_ACTION_OPTIONS, key="climax_action_choice")

    st.subheader("4. Pengaturan Visual, Rasio Aspek & Target Durasi")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Gaya Visual", STYLE_OPTIONS, key="visual_style")
        st.selectbox("Rasio Aspek Video", ASPECT_OPTIONS, key="aspect_ratio")
    with col2:
        st.selectbox("Target Durasi & Jumlah Scene", list(DURATION_SCENES.keys()), key="duration")
        st.text_area("Instruksi Tambahan (Opsional)", key="custom_instruction", height=80, placeholder="Misal: Buat jarak antar boneka lebih dekat...")

    st.markdown("---")
    st.subheader("🧭 Navigasi & Rintangan Ekstrem Per-Scene (Opsional)")
    st.caption("Pilih rintangan khusus pada scene yang kamu inginkan. Jika dibiarkan 'None / Lari Datar', runner berlari normal.")

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

    st.success(f"⏱️ Total Target Durasi & Scene: **{scene_count()} Scene** (~{scene_count() * 8} detik total durasi video)")

    st.subheader("💡 Perbandingan Mutasi Roadmap 1:1 (Anti Plagiarisme)")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📌 Asli (Video Referensi)")
        st.write(f"**Runner Asli:** {orig.get('runner_asli', '-')}")
        st.write(f"**Boss/Ragdoll Asli:** {orig.get('boss_asli', '-')}")
        st.write(f"**Lintasan Asli:** {orig.get('track_asli', '-')}")

    with col2:
        st.markdown("### 🚀 Hasil Remix AI (Multi-Action & Custom Arena)")
        st.write(f"**Runner Baru:** `{remix.get('runner_baru', '-')}`")
        st.write(f"**Target & Stand Baru:** `{remix.get('boss_baru', '-')}`")
        st.write(f"**Arena/Map Baru:** `{remix.get('track_baru', '-')}`")

    st.info(f"🔒 **Visual Anchor Token:** `{remix.get('visual_anchor_token', '-')}`")
    st.warning(f"💥 **Aksi Klimaks:** {analysis.get('climax_action', '-')}")

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

    st.write(f"### Adegan {current} dari {n}" + (" 💥 (SCENE KLIMAKS AKSI GANDA & RAGDOLL CHAOS)" if current == n else " ⚡ (FAST-PACED DUAL ACTION)"))

    if current not in st.session_state.scene_prompts:
        if st.button(f"Generate Prompt Scene {current}", type="primary"):
            generate_scene_prompt(current)
            st.rerun()

    if current in st.session_state.scene_prompts:
        st.text_area("Prompt AI Video (Copy-Paste ke Google Veo / Kling / Luma):", value=st.session_state.scene_prompts[current], height=180)

        st.subheader("🖼️ Last Frame Bridge (Estafet Frame / Anti-Jump Continuity)")
        st.caption("UPLOAD SCREENSHOT FRAME TERAKHIR dari video hasil Scene ini agar Scene berikutnya presisi tanpa loncatan posisi.")
        uploaded_frame = st.file_uploader(f"Upload Last Frame Scene {current}", type=["png", "jpg", "jpeg"], key=f"frame_{current}")
        if uploaded_frame:
            st.session_state.scene_frames[current] = uploaded_frame
            st.success(f"Frame Scene {current} tersimpan! Prompt Scene {current+1} terkunci pada koordinat ini.")

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
    st.title("🚀 SEO & Metadata Engine (Algoritma YouTube / TikTok)")
    st.caption("Menghasilkan Judul CTR tinggi, Deskripsi tertarget, dan **18 Tags Global Unik** tanpa duplikat.")

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
