import json
import re
import time
import os

import streamlit as st
from google import genai
from google.genai import types

# ==========================================
# 1. KONFIGURASI HALAMAN & MODEL UTAMA
# ==========================================
st.set_page_config(
    page_title="UGC Remix Studio v10.3 — Complete Entity, Physics & SEO Engine",
    page_icon="🎬",
    layout="wide"
)

# Model resmi yang stabil dan tersedia
MODEL_NAME = "gemini-3.6-flash"


# ==========================================
# 2. DEFINISI OPSI & PRESET DATA
# ==========================================
DURATION_SCENES = {
    "Auto (Sesuai Durasi & Video Referensi)": 0,
    "8 detik (1 Scene - Shorts Kilat)": 1,
    "16 detik (2 Scene - Shorts Standar)": 2,
    "24 detik (3 Scene)": 3,
    "32 detik (4 Scene)": 4,
    "40 detik (5 Scene)": 5,
    "60 detik (8 Scene - 1 Menit Long)": 8,
    "120 detik (15 Scene - 2 Menit Long)": 15,
    "180 detik (22 Scene - 3 Menit Full Challenge)": 22,
}

STYLE_OPTIONS = [
    "GTA V Modded Gameplay Style",
    "3D Animated Game Graphics",
    "Unreal Engine 5 Parkour Render",
    "Sinematik Realistis 3D",
]

RUNNER_PRESETS = [
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
    "Udindindun (Karakter khas Italian brainrot yang konyol dan nyeleneh)",
    "Custom / Ketik Sendiri"
]

TARGET_DOLL_OPTIONS = [
    "Crash Test Dummies (Boneka uji tabrak manekin kuning-hitam ikonik)",
    "Giant Yellow Rubber Ducks (Bebek karet kuning raksasa elastis)",
    "Giant Teddy Bears (Boneka beruang cokelat empuk dengan bulu halus)",
    "Skeleton Ragdolls (Deretan tengkorak hidup bertumpuk pasif)",
    "Zombie Horde Mannequins (Boneka manekin gaya zombie kaku)",
    "Roblox / Blocky Mannequins (Boneka manekin balok gaya voxel)",
    "Inflatable Air Tube Men (Boneka tiup meliuk-liuk angin)",
    "Colorful Yoga Fitness Dolls (Boneka manekin karet elastis)",
    "Custom / Ketik Sendiri"
]

IDLE_MOTION_OPTIONS = [
    "Subtle Breathing & Wind Swaying (Bergoyang lembut tertiup angin & bernapas pasif)",
    "Anxious Trembling / Scared Wobble (Bergetar ketakutan oleng di atas pijakan)",
    "Ragdoll Balancing / Unstable Wobble (Oleng hampir jatuh mencari keseimbangan)",
    "Micro-Jitter & Glitch Stance (Getaran mikro kaku pasif khas modding game)",
    "Playful Slow Wiggling (Berdansa/bergoyang santai pelan)",
    "Frozen Stiff Stance (Diam kaku total sampai benturan fisik terjadi)",
    "Custom / Ketik Sendiri"
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


# ==========================================
# 3. INISIALISASI SESSION STATE
# ==========================================
DEFAULTS = {
    "page": "home",
    "api_key": "",
    "reference_file": None,
    "reference_text": "",
    "visual_style": STYLE_OPTIONS[0],
    "runner_choice": RUNNER_PRESETS[0],
    "custom_runner": "",
    "target_doll_choice": TARGET_DOLL_OPTIONS[0],
    "custom_target_doll": "",
    "idle_motion_choice": IDLE_MOTION_OPTIONS[0],
    "custom_idle_motion": "",
    "map_choice": MAP_OPTIONS[0],
    "prop_stand_choice": PROP_STAND_OPTIONS[0],
    "climax_action_choice": CLIMAX_ACTION_OPTIONS[0],
    "aspect_ratio": ASPECT_OPTIONS[0],
    "duration": "Auto (Sesuai Durasi & Video Referensi)",
    "custom_instruction": "",
    "user_scene_obstacles": {},
    "analysis": {},
    "storyboard": [],
    "entity_mapping": {},
    "scene_prompts": {},
    "scene_frames": {},
    "current_scene": 1,
    "detected_scenes": 0,
    "seo": {},
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================
# 4. FUNGSI UTILITAS & API GEMINI
# ==========================================
def go(page: str):
    st.session_state.page = page
    st.rerun()

def reset_remix_state():
    st.session_state.analysis = {}
    st.session_state.storyboard = []
    st.session_state.entity_mapping = {}
    st.session_state.scene_prompts = {}
    st.session_state.scene_frames = {}
    st.session_state.current_scene = 1
    st.session_state.detected_scenes = 0
    st.session_state.seo = {}

def scene_count() -> int:
    val = DURATION_SCENES.get(st.session_state.duration, 0)
    if val == 0:
        return st.session_state.get("detected_scenes", 1) if st.session_state.get("detected_scenes", 0) > 0 else 0
    return val

def get_client():
    key = (os.getenv("GEMINI_API_KEY") or st.session_state.get("api_key", "")).strip()
    key = key.strip("`\"' \n\r\t") # Pembersihan menyeluruh karakter aneh/kutip
    if not key:
        st.error("Masukkan Gemini API Key terlebih dahulu di Sidebar.")
        return None
    try:
        return genai.Client(api_key=key)
    except Exception as exc:
        st.error(f"Gagal koneksi Gemini API: {exc}")
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

    config_kwargs = {"temperature": 0.2}
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


# ==========================================
# 5. CORE LOGIC (ANALYSIS, PROMPTS, & SEO)
# ==========================================
def run_analysis():
    reset_remix_state()
    client = get_client()
    if not client:
        return

    ref_file = st.session_state.get("ref_file_input")
    parts = []
    if ref_file is not None:
        try:
            data = ref_file.getvalue()
            mime = getattr(ref_file, "type", "video/mp4") or "video/mp4"
            parts.append(types.Part.from_bytes(data=data, mime_type=mime))
        except Exception as exc:
            st.warning(f"Gagal membaca video referensi: {exc}")

    if st.session_state.reference_text.strip():
        parts.append(types.Part.from_text(text=st.session_state.reference_text))

    chosen_runner = st.session_state.runner_choice
    if chosen_runner == "Custom / Ketik Sendiri":
        chosen_runner = st.session_state.custom_runner or "Custom Parkour Runner"

    chosen_target = st.session_state.target_doll_choice
    if chosen_target == "Custom / Ketik Sendiri":
        chosen_target = st.session_state.custom_target_doll or "Custom Target Doll"

    chosen_idle = st.session_state.idle_motion_choice
    if chosen_idle == "Custom / Ketik Sendiri":
        chosen_idle = st.session_state.custom_idle_motion or "Custom Idle Motion"

    is_auto = (DURATION_SCENES.get(st.session_state.duration, 0) == 0)
    target_calc = """
1. AI WAJIB membaca DURASI ASLI video referensi.
2. Hitung jumlah scene: CEIL(Durasi_Detik / 8). Contoh mutlak: 17 detik -> 3 Scene (Total 24 detik).
""" if is_auto else f"1. Buat tepat {DURATION_SCENES.get(st.session_state.duration)} Scene (Total {DURATION_SCENES.get(st.session_state.duration)*8} detik)."

    prompt = f"""
Anda adalah AI Master Creative Director untuk UGC Flow Jacking. 
TUGAS: Analisis video/teks referensi terlampir, lalu rombak TOTAL visualnya agar tidak terdeteksi plagiat, namun RITME aksinya dipertahankan.

{target_calc}

ATURAN FLOW JACKING & ENTITY MAPPING (MUTLAK):
1. Petakan elemen asli, lalu GANTI TOTAL dengan parameter user. DILARANG membawa entitas asli ke dalam cerita baru!
   - Runner Baru: "{chosen_runner}"
   - Target Boneka/Ragdoll Baru: "{chosen_target}"
   - Gerakan Idle Pasif Target: "{chosen_idle}"
   - Arena Baru: "{st.session_state.map_choice}"
   - Pijakan Target: "{st.session_state.prop_stand_choice}"
   - Climax Action: "{st.session_state.climax_action_choice}"
2. STRUKTUR 3-BABAK (Ekspansi Durasi): Jika scene yang dihitung lebih panjang dari video asli, sisa scene WAJIB diisi dengan aksi transisi/rintangan tambahan secara logis, berujung pada Aksi Klimaks di scene terakhir.

HASILKAN JSON FORMAT BERIKUT:
{{
  "calculated_scene_count": [ANGKA INT],
  "entity_mapping": {{
    "runner_asli": "[Aktor di video]",
    "runner_remix": "{chosen_runner}",
    "target_asli": "[Target/Objek di video]",
    "target_remix": "{chosen_target}",
    "arena_asli": "[Arena di video]",
    "arena_remix": "{st.session_state.map_choice}"
  }},
  "storyboard_plan": [
    {{
      "scene": 1,
      "fokus_aksi_dan_kamera": "Deskripsi aksi fisik disesuaikan dengan proporsi badan runner, beserta sudut kamera anti-plagiat."
    }}
  ]
}}
"""
    with st.spinner("Membongkar Video, Kalkulasi Durasi & Meracik Blueprint Anti-Plagiat..."):
        try:
            raw = ask(client, prompt, parts, json_mode=True)
            data = extract_json(raw)
            
            st.session_state.analysis = data
            calculated_count = int(data.get("calculated_scene_count", 0))
            if calculated_count <= 0:
                calculated_count = len(data.get("storyboard_plan", [1]))

            st.session_state.detected_scenes = calculated_count
            st.session_state.entity_mapping = data.get("entity_mapping", {})
            st.session_state.storyboard = data.get("storyboard_plan", [])
            go("analysis")
        except Exception as exc:
            st.error(f"Gagal membedah video: {exc}")

def generate_scene_prompt(scene_number: int, custom_tweak: str = ""):
    client = get_client()
    if not client:
        return False

    analysis = st.session_state.analysis
    storyboard = st.session_state.storyboard
    total_scenes = scene_count()
    is_final_scene = (scene_number == total_scenes)
    
    if storyboard and len(storyboard) >= scene_number:
        scene_focus = storyboard[scene_number - 1].get("fokus_aksi_dan_kamera", f"Aksi scene {scene_number}")
    else:
        scene_focus = f"Aksi fisik dinamis melompati rintangan menuju target scene {scene_number}"
    
    chosen_target = analysis.get('entity_mapping', {}).get('target_remix', st.session_state.target_doll_choice)
    chosen_idle = st.session_state.idle_motion_choice
    
    custom_obstacle = st.session_state.user_scene_obstacles.get(scene_number, "")
    obstacle_str = f"\n[OBSTACLE INJECTION]: {custom_obstacle}" if custom_obstacle else ""
    climax_str = f"\n[FINAL CLIMAX ACTION]: Execute exact climax ending: {st.session_state.climax_action_choice}" if is_final_scene and st.session_state.climax_action_choice != "Auto (Ikuti Remix UGC)" else ""

    parts_list = []
    frame_context_str = ""
    prev_scene_num = scene_number - 1
    
    if prev_scene_num > 0:
        if prev_scene_num in st.session_state.scene_frames and st.session_state.scene_frames[prev_scene_num]:
            frame_data = st.session_state.scene_frames[prev_scene_num]
            parts_list.append(types.Part.from_bytes(data=frame_data["bytes"], mime_type=frame_data["mime"]))
            frame_context_str = f"\n[VISION CONTINUITY]: You MUST start this scene matching the exact character posture, location, and scattered objects shown in the attached image from the previous scene."
        else:
            return "ERROR_NO_FRAME"

    tweak_instruction = f"\n[USER TWEAK REQUEST]: {custom_tweak}" if custom_tweak else ""
    custom_global = f"\n[GLOBAL INSTRUCTION]: {st.session_state.custom_instruction}" if st.session_state.custom_instruction else ""

    prompt = f"""
Write ONE ultra-detailed AI video generation prompt in ENGLISH for Scene {scene_number} of {total_scenes}.
FORMATTING RULE: Output EXACTLY in this categorized format without any other intro text.

[SUBJECT & MOTION]: (Describe {analysis.get('entity_mapping', {}).get('runner_remix')} executing action: {scene_focus}. Action physics must match body type).
[ENVIRONMENT & MAP]: (Set in {analysis.get('entity_mapping', {}).get('arena_remix')} with {st.session_state.prop_stand_choice}).
[OBJECT IDLE & PHYSICS]: (CRITICAL: Target props/dolls are "{chosen_target}". Before impact, targets exhibit idle state: "{chosen_idle}". Total destruction/ragdoll ONLY occurs upon direct runner physical impact).
[CAMERA MOVEMENT]: (Dynamic anti-plagiarism camera angle, distinct from standard front-view).
[VISUAL STYLE & LIGHTING]: ({st.session_state.visual_style}, {st.session_state.aspect_ratio}, 8k resolution, highly detailed motion blur).
{obstacle_str}{climax_str}{frame_context_str}{tweak_instruction}{custom_global}
"""
    with st.spinner(f"Merakit Prompt Terstruktur Scene {scene_number}..."):
        try:
            res_prompt = ask(client, prompt, parts=parts_list, json_mode=False)
            st.session_state.scene_prompts[scene_number] = res_prompt.strip()
            return "SUCCESS"
        except Exception as exc:
            st.error(f"Gagal membuat prompt: {exc}")
            return "ERROR_API"

def generate_seo():
    client = get_client()
    if not client:
        return False

    analysis = st.session_state.analysis
    mapping = analysis.get("entity_mapping", {})
    runner = mapping.get("runner_remix", "Runner")
    target = mapping.get("target_remix", "Target")
    arena = mapping.get("arena_remix", "Arena")

    prompt = f"""
Buatkan paket metadata SEO viral untuk konten Shorts/TikTok/Reels berdasarkan skenario video berikut:
- Karakter Utama: {runner}
- Target Pukulan/Aksi: {target}
- Lokasi Arena: {arena}
- Gaya Visual: {st.session_state.visual_style}

HASILKAN DALAM FORMAT JSON PERSIS SEPERTI INI:
{{
  "titles": [
    "3 Opsi Judul Clickbait Viral dengan Emoji (Maksimal 60 Karakter)"
  ],
  "description": "Deskripsi singkat yang menarik minat tonton, dilengkapi call to action untuk like dan subscribe.",
  "hashtags": ["#Hashtag1", "#Hashtag2", "#Hashtag3", "#Hashtag4", "#Hashtag5", "#Hashtag6"],
  "tags_csv": "kata kunci 1, kata kunci 2, kata kunci 3, kata kunci 4, kata kunci 5"
}}
"""
    with st.spinner("Meracik Judul Viral, Deskripsi & Hashtag SEO..."):
        try:
            raw = ask(client, prompt, json_mode=True)
            st.session_state.seo = extract_json(raw)
            return True
        except Exception as exc:
            st.error(f"Gagal membuat SEO: {exc}")
            return False


# ==========================================
# 6. RENDER ANTARMUKA HALAMAN (VIEWS)
# ==========================================
def render_home():
    st.title("🎬 UGC Remix Studio v10.3 — Entity, Physics & SEO")
    st.caption("Auto Duration Engine, Anti-Plagiarism Flow Jacking, & Dedicated Idle Physics Control.")

    st.subheader("1. Referensi Video / Skenario Manual")
    st.file_uploader("Upload Video Referensi (Shorts / Video Panjang)", type=["mp4", "mov", "webm"], key="ref_file_input")
    st.text_area("Deskripsi Manual Referensi (Opsional)", key="reference_text", height=70)

    st.subheader("2. Penyamaran Identitas (Remix Entities & Environment)")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Pilih Karakter Runner Baru:", RUNNER_PRESETS, key="runner_choice")
        if st.session_state.runner_choice == "Custom / Ketik Sendiri":
            st.text_input("Tulis Deskripsi Karakter Custom Kamu:", key="custom_runner")
            
        st.selectbox("Pilih Target Boneka / Ragdoll Baru:", TARGET_DOLL_OPTIONS, key="target_doll_choice")
        if st.session_state.target_doll_choice == "Custom / Ketik Sendiri":
            st.text_input("Tulis Deskripsi Target Custom Kamu:", key="custom_target_doll")
            
        st.selectbox("Gaya Visual Render:", STYLE_OPTIONS, key="visual_style")

    with col2:
        st.selectbox("Pilih Gerakan Idle Pasif Target (Physics State):", IDLE_MOTION_OPTIONS, key="idle_motion_choice")
        if st.session_state.idle_motion_choice == "Custom / Ketik Sendiri":
            st.text_input("Tulis Deskripsi Gerakan Idle Custom:", key="custom_idle_motion")
            
        st.selectbox("Pilih Map Arena Baru:", MAP_OPTIONS, key="map_choice")
        st.selectbox("Pilih Pijakan Target (Prop Stand):", PROP_STAND_OPTIONS, key="prop_stand_choice")

    st.subheader("3. Durasi Video & Aksi Klimaks Penutup")
    col3, col4 = st.columns(2)
    with col3:
        st.selectbox("Target Durasi & Jumlah Scene:", list(DURATION_SCENES.keys()), key="duration")
        st.selectbox("Rasio Aspek Video:", ASPECT_OPTIONS, key="aspect_ratio")
    with col4:
        st.selectbox("Gaya Aksi Klimaks Penutup (Scene Terakhir):", CLIMAX_ACTION_OPTIONS, key="climax_action_choice")
        st.text_area("Instruksi Tambahan Global (Opsional)", key="custom_instruction", height=70)

    st.markdown("---")
    
    st.subheader("🧭 Navigasi Rintangan Per-Scene (Opsi Manual)")
    calculated_scenes = DURATION_SCENES.get(st.session_state.duration, 0)
    
    if calculated_scenes == 0:
        st.info("💡 **Mode Auto Durasi Aktif:** Rintangan manual tidak ditampilkan di sini karena jumlah scene belum diketahui. AI akan mengatur variasi rintangan secara dinamis setelah video Anda dianalisis.")
    else:
        st.write(f"**Total Scene Ditampilkan:** {calculated_scenes} Scene ({calculated_scenes * 8} Detik Total Durasi)")
        scenes_per_group = 4
        total_groups = (calculated_scenes + scenes_per_group - 1) // scenes_per_group

        if total_groups == 1:
            cols = st.columns(2)
            for i in range(1, calculated_scenes + 1):
                col_idx = (i - 1) % 2
                with cols[col_idx]:
                    chosen_obs = st.selectbox(
                        f"Rintangan Scene {i}:",
                        options=list(OBSTACLE_OPTIONS.keys()),
                        index=0,
                        key=f"obstacle_select_scene_{i}"
                    )
                    st.session_state.user_scene_obstacles[i] = OBSTACLE_OPTIONS[chosen_obs]
        else:
            tab_labels = [
                f"Scene {g * scenes_per_group + 1} - {min((g + 1) * scenes_per_group, calculated_scenes)}" 
                for g in range(total_groups)
            ]
            tabs = st.tabs(tab_labels)
            for g, tab in enumerate(tabs):
                with tab:
                    cols = st.columns(2)
                    start_s = g * scenes_per_group + 1
                    end_s = min((g + 1) * scenes_per_group, calculated_scenes)
                    for idx, scene_idx in enumerate(range(start_s, end_s + 1)):
                        col_idx = idx % 2
                        with cols[col_idx]:
                            chosen_obs = st.selectbox(
                                f"Rintangan Scene {scene_idx}:",
                                options=list(OBSTACLE_OPTIONS.keys()),
                                index=0,
                                key=f"obstacle_select_scene_{scene_idx}"
                            )
                            st.session_state.user_scene_obstacles[scene_idx] = OBSTACLE_OPTIONS[chosen_obs]

    st.markdown("---")
    st.button("🚀 BONGKAR VIDEO & BUAT BLUEPRINT REMIX", type="primary", use_container_width=True, on_click=run_analysis)

def render_analysis():
    st.title("🛡️ Anti-Plagiarism Verification & Storyboard")
    
    mapping = st.session_state.get("entity_mapping", {})
    storyboard = st.session_state.get("storyboard", [])

    if not storyboard:
        st.info("Silakan proses referensi di Beranda terlebih dahulu.")
        return

    st.success(f"⏱️ Kalkulasi AI Selesai: **Target {scene_count()} Scene** (~{scene_count() * 8} Detik).")

    st.subheader("🔄 Tabel Translasi Flow Jacking (Cek Kebocoran)")
    st.markdown("*Pastikan tabel di bawah ini benar. AI telah menghapus entitas asli dan menggantinya dengan pilihan Anda.*")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Elemen", "Karakter Runner")
    col2.metric("Terdeteksi di Video Asli", mapping.get("runner_asli", "-"))
    col3.metric("Diubah Menjadi (Aman)", mapping.get("runner_remix", "-"))

    col1_t, col2_t, col3_t = st.columns(3)
    col1_t.metric("Elemen", "Target Boneka/Ragdoll")
    col2_t.metric("Terdeteksi di Video Asli", mapping.get("target_asli", "-"))
    col3_t.metric("Diubah Menjadi (Aman)", mapping.get("target_remix", "-"))

    col4, col5, col6 = st.columns(3)
    col4.metric("Elemen", "Latar / Arena")
    col5.metric("Terdeteksi di Video Asli", mapping.get("arena_asli", "-"))
    col6.metric("Diubah Menjadi (Aman)", mapping.get("arena_remix", "-"))

    st.markdown("---")
    st.subheader("📋 3-Act Micro Storyboard & Camera Angles")
    for item in storyboard:
        st.info(f"**Scene {item.get('scene', '-')}**: {item.get('fokus_aksi_dan_kamera', '-')}")

    st.markdown("---")
    if st.button("LANJUT KE GENERATOR PROMPT SCENE 1 🎥", type="primary", use_container_width=True):
        go("scenes")

def render_scenes():
    st.title("🎥 Sequential Scene Prompt Generator")
    n = scene_count()
    current = st.session_state.current_scene

    st.subheader(f"Adegan {current} dari {n} " + ("💥 (Final Extended Climax)" if current == n else "⚡ (Action & Setup)"))

    if current > 1 and current - 1 not in st.session_state.scene_frames:
        st.error(f"🛑 STOP! Anda belum mengunggah Gambar Last Frame dari Scene {current-1}. Alur ditahan untuk mencegah AI berhalusinasi (menjaga continuity posisi karakter).")
        if st.button("← Kembali ke Scene Sebelumnya", type="primary"):
            st.session_state.current_scene -= 1
            st.rerun()
        return

    if current not in st.session_state.scene_prompts:
        with st.spinner("Mempersiapkan Prompt Terstruktur (Physics & Continuity checked)..."):
            status = generate_scene_prompt(current)
            if status == "SUCCESS":
                st.rerun()
            elif status == "ERROR_NO_FRAME":
                st.error("Frame scene sebelumnya tidak ditemukan.")
                return

    if current in st.session_state.scene_prompts:
        st.text_area(f"Salin Prompt Scene {current} (Terformat Standar Industri):", value=st.session_state.scene_prompts[current], height=220)

        with st.expander("🔄 Kurang pas? Re-roll Prompt Scene Ini"):
            tweak_val = st.text_input("Ketik revisi (Misal: 'Buat kameranya muter dari atas', 'Bikin jatuh lebih heboh')", key=f"tweak_{current}")
            if st.button("Apply Tweak & Regenerate", key=f"btn_tweak_{current}"):
                generate_scene_prompt(current, custom_tweak=tweak_val)
                st.rerun()

        st.markdown("---")
        
        if current < n:
            st.subheader(f"🖼️ Gatekeeper: Kunci Kontinuitas (Frame Terakhir Scene {current})")
            st.caption("Agar posisi karakter di Scene berikutnya akurat, UPLOAD screenshot frame paling akhir dari video hasil render Scene ini.")
            
            uploaded_frame = st.file_uploader(f"Upload Last Frame Scene {current}", type=["png", "jpg", "jpeg"], key=f"frame_upload_{current}")
            if uploaded_frame:
                st.session_state.scene_frames[current] = {
                    "bytes": uploaded_frame.getvalue(),
                    "mime": getattr(uploaded_frame, "type", "image/png") or "image/png"
                }
                st.image(uploaded_frame, caption=f"Posisi Terkunci! Siap untuk Scene {current+1}", width=300)
            elif current in st.session_state.scene_frames:
                st.success("Frame Continuity sudah diamankan di memori.")
        
        st.markdown("---")
        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if current > 1 and st.button("← Adegan Sebelumnya"):
                st.session_state.current_scene -= 1
                st.rerun()
        with col_nav2:
            if current < n:
                is_disabled = (current not in st.session_state.scene_frames)
                if st.button("Adegan Berikutnya →", type="primary", disabled=is_disabled):
                    st.session_state.current_scene += 1
                    st.rerun()
            elif current == n:
                st.success("🏁 Seluruh Blueprint Scene Selesai Dieksekusi!")
                if st.button("LANJUT KE GENERATOR SEO & METADATA 🏷️", type="primary", use_container_width=True):
                    go("seo")

def render_seo():
    st.title("🏷️ SEO & Metadata Generator Viral")
    st.caption("Racikan judul clickbait, deskripsi, dan hashtag optimal untuk Shorts, Reels, & TikTok.")

    seo = st.session_state.get("seo", {})

    if not seo:
        st.info("Klik tombol di bawah ini untuk membuat paket SEO otomatis berdasarkan proyek video Anda.")
        if st.button("🚀 GENERATE SEO & METADATA SEKARANG", type="primary", use_container_width=True):
            if generate_seo():
                st.rerun()
        return

    st.subheader("🔥 Rekomendasi Judul Viral")
    for idx, title in enumerate(seo.get("titles", []), 1):
        st.code(title, language=None)

    st.markdown("---")
    st.subheader("📝 Deskripsi Video (Siap Copas)")
    st.text_area("Deskripsi:", value=seo.get("description", ""), height=120)

    st.markdown("---")
    st.subheader("🏷️ Hashtags & Tags CSV")
    col_h, col_t = st.columns(2)
    with col_h:
        st.markdown("**Hashtags (Shorts / TikTok):**")
        st.code(" ".join(seo.get("hashtags", [])), language=None)
    with col_t:
        st.markdown("**Tags CSV (YouTube Studio):**")
        st.code(seo.get("tags_csv", ""), language=None)

    st.markdown("---")
    if st.button("🔄 Generate Ulang SEO", use_container_width=True):
        if generate_seo():
            st.rerun()


# ==========================================
# 7. SIDEBAR CONTROLS & MAIN ROUTER
# ==========================================
with st.sidebar:
    st.title("⚙️ Studio Controls")
    st.text_input("Gemini API Key", key="api_key", type="password")
    st.markdown("---")
    st.markdown("**Navigasi Alur Studio:**")
    if st.button("1. 🏠 Beranda & Upload", use_container_width=True):
        go("home")
    if st.button("2. 📋 Verifikasi Anti-Plagiat", use_container_width=True):
        go("analysis")
    if st.button("3. 🎥 Generator Prompt", use_container_width=True):
        go("scenes")
    if st.button("4. 🏷️ Generator SEO & Metadata", use_container_width=True):
        go("seo")

# Routing Halaman Aktif
page = st.session_state.page
if page == "home":
    render_home()
elif page == "analysis":
    render_analysis()
elif page == "scenes":
    render_scenes()
elif page == "seo":
    render_seo()
