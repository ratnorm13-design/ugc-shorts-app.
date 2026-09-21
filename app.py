import json
import os
import re
import time
import streamlit as st
from google import genai
from google.genai import types

# ==========================================
# CONSTANTS & CONFIGURATION (Single File)
# ==========================================
MODEL_NAME = "gemini-2.5-flash"
APP_VERSION = "11.0 — Flow AI No-Edit UI Engine (Camera Choice & Object Stability Lock)"

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

CAMERA_OPTIONS = [
    "Auto / Dynamic Tracking (Ikuti Runner dari Belakang)",
    "Slow Cinematic Zoom-In (Zoom Perlahan Fokus ke Target)",
    "Smooth Side Panning Shot (Kamera Bergerak dari Samping)",
    "Low-Angle Action Chase (Sudut Rendah Dramatis / Dari Bawah)"
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

TARGET_IDLE_PRESETS = [
    "Auto / Random Mix (Otomatis Bervariasi per Target)",
    "🕺 Joget & Konyol (TikTok Idle Dance, Goyang Pinggul, Body Sway)",
    "😱 Panik & Ketakutan (Trembling In-Place, Frantic Hand Waving)",
    "😎 Sombong & Ngeledek (Chest Slap, Taunting Gesture, Pointing)",
    "🗿 Mode Diam / Patung (Classic Static Stance)"
]

MAP_OPTIONS = [
    "Auto (Ikuti Remix UGC)",
    "1. Maze Bank Tower Rooftop (Downtown Los Santos Skyscraper)",
    "2. Mount Chiliad Mega Ramp & Ridge (High Mountain Canyon)",
    "3. Pacific Ocean Docks & Shipping Containers (Sea Port)",
    "4. Sky-High Cloud Ramp (Floating Infinite Cloud Void)",
    "5. Alamo Sea Desert Airfield Ramp (Sandy Shores Valley)",
    "6. Del Perro Pier Coastal Boardwalk (Beach Ferris Wheel View)",
    "7. Fort Zancudo Military Airbase Overhead (Jet Base View)",
    "8. Zancudo River Canyon Bridge (Red Rock River)",
    "9. Neon City Cyberpunk Night (Glow Los Santos Nightlife)",
    "10. Lava Volcano Caldera Arena (Active Volcano Lava Pit)"
]

PROP_STAND_OPTIONS = [
    "Auto (Ikuti Remix UGC)",
    "1. Direct Concrete Rooftop / Flat Container Surface",
    "2. Giant Yoga / Exercise Fitness Balls (Colored Balls)",
    "3. Wooden Cargo Barrels & Metal Oil Drums",
    "4. Stacked Rubber Tires & Wheels",
    "5. Vertical Trampoline Impulse Pads",
    "6. Glass Ice Cubes & Translucent Pillars",
    "7. Rotating Wooden Cylinder Log Rollers",
    "8. High Concrete Construction Blocks",
    "9. Floating Pool Inflatable Donuts",
    "10. Steel Spring Coil Platforms"
]

CLIMAX_ACTION_OPTIONS = [
    "Auto (Ikuti Remix UGC)",
    "1. Double Hit Combo + Sacrifice Fall (Runner hits 2 targets & falls off edge together)",
    "2. Flying Knee Jump Kick + Domino Ragdoll Collapse",
    "3. 360 Spinning Backfist + Abyss Drag Drop",
    "4. Double Dropkick + Explosion Bounce Sacrifice Fall",
    "5. Superman Punch & Barrel Destruction + Full Ragdoll Fall",
    "6. Tackle & Hug Fall (Kamikaze Drag off the cliff)",
    "7. High-Velocity Running Sweep Kick + Terpelanting Off-Limit",
    "8. Consecutive Punch-Kick Combo (3 Hits) + Edge Slurry Fall",
    "9. Trampoline Launch Overhead Smash + Surface Collapse Fall",
    "10. Sliding Tackle Multi-Target Clear + Edge Overshoot Fall"
]

OBSTACLE_OPTIONS = {
    "None / Lari Datar": "",
    "1. ⛓️ Swinging Giant Pendulums & Hammers": "ENVIRONMENT MECHANIC: Giant swinging pendulums and massive hammers obstruct the path; runner must weave and dodge around them skillfully.",
    "2. 🔥 Flamethrower & Fire Jet Gates": "ENVIRONMENT MECHANIC: Periodic intense fire jets shoot up from the platform surface; runner timing must be precise.",
    "3. 🌀 Rotating Spike Rollers": "ENVIRONMENT MECHANIC: Fast-spinning spiked cylinders block the middle path; runner must leap over them cleanly.",
    "4. 💣 Explosive Red Barrels": "ENVIRONMENT MECHANIC: Highly unstable red explosive barrels line the edges; accidental contact triggers physics blast.",
    "5. 🪓 Oscillating Guillotine Blades": "ENVIRONMENT MECHANIC: Massive razor-sharp guillotine blades drop up and down rapidly across the lane.",
    "6. 🧱 Crushing Hydraulic Pistons": "ENVIRONMENT MECHANIC: Heavy concrete hydraulic blocks punch horizontally across the runner's path.",
    "7. 🌉 Narrow Crumbling Bridge / Glass Tiles": "ENVIRONMENT MECHANIC: Fragile glass tiles and crumbling concrete blocks shatter 1 second after being stepped on.",
    "8. ⚡ Electrified Fence & Laser Barriers": "ENVIRONMENT MECHANIC: High-voltage flickering electric laser barriers force the runner to slide or jump high.",
    "9. 🌀 High-Speed Wind Turbine Fans": "ENVIRONMENT MECHANIC: Industrial wind turbine fans blow strong lateral gusts threatening to push runner off the edge.",
    "10. 🪜 Sky-High Spiral Metal Ladder": "MANDATORY NAVIGATIONAL ACTION: Runner rapidly climbs a steep spiral metal ladder hovering high over open air."
}

ASPECT_OPTIONS = ["9:16 — Shorts / Reels / TikTok", "16:9 — YouTube Long", "1:1 — Kotak"]

# ==========================================
# HELPER FUNCTIONS & STATE INIT
# ==========================================
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

st.set_page_config(page_title="UGC Remix Studio v11.0", page_icon="🎬", layout="wide")

DEFAULTS = {
    "page": "home",
    "api_key": "",
    "reference_file": None,
    "reference_text": "",
    "visual_style": STYLE_OPTIONS[0],
    "selected_camera": CAMERA_OPTIONS[0],
    "runner_choice": RUNNER_PRESETS[1],
    "target_idle_choice": TARGET_IDLE_PRESETS[0],
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

# ==========================================
# ENGINE LOGIC
# ==========================================
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
2. PERMANENT OBJECT INITIAL PLACEMENT & IN-PLACE IDLE MOTION: Setiap pilar/dudukan ({st.session_state.selected_prop_stand}) terisi boneka target sejak Frame 1. Setiap boneka target memiliki gaya gerakan idle diam di tempat.
3. Rancang mutasi karakter runner utama menjadi: "{chosen_runner}", serta sesuaikan target boss/ragdoll dengan opsi copyright-safe.
4. Sediakan skenario klimaks dramatis di mana runner dan target mengalami ragdoll chaos.

PENGATURAN MANUAL OVERRIDE (JIKA DISUAP):
- Camera Movement Style: {st.session_state.selected_camera}
- Target Idle Motion Override: {st.session_state.target_idle_choice}
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
    "boss_baru": "Deretan boneka target ragdoll unik yang berdiri & beratraksi idle di atas pijakan sejak awal",
    "target_idle_behavior": "{st.session_state.target_idle_choice}",
    "camera_movement": "{st.session_state.selected_camera}",
    "track_baru": "Lintasan kontainer/pijakan 1:1 dengan boneka ganda",
    "map_environment": "{st.session_state.selected_map if st.session_state.selected_map != 'Auto (Ikuti Remix UGC)' else 'Dynamic 3D Game Map'}",
    "prop_stand": "{st.session_state.selected_prop_stand if st.session_state.selected_prop_stand != 'Auto (Ikuti Remix UGC)' else 'Standard Flat Surface'}",
    "visual_anchor_token": "Deskripsi ketat kosmetik karakter pilihan user agar konsisten",
    "alasan_remix": "Alasan modifikasi"
  }},
  "storyboard_plan": [
    {{"scene": 1, "fokus_aksi": "Runner berlari cepat di atas lintasan. Boneka target melakukan gerakan idle konyol di atas drum sebelum ditendang jatuh."}},
    {{"scene": 2, "fokus_aksi": "Melanjutkan navigasi rintangan berikutnya dengan target aktif selanjutnya."}},
    {{"scene": 3, "fokus_aksi": "Klimaks aksi ganda penutupan, hantaman beruntun, dan runner ikut terjun jatuh bebas (ragdoll sacrifice fall)."}}
  ],
  "climax_action": "{st.session_state.selected_climax_action if st.session_state.selected_climax_action != 'Auto (Ikuti Remix UGC)' else 'Multi-hit combo with sacrifice fall'}",
  "spatial_layout": "Third-person tracking shot with initial object coordinates and anchored idle target animations"
}}
"""
    with st.spinner("Membedah roadmap 1:1 & meracik variasi idle target & Flow AI anti-looping..."):
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

    cam_choice = st.session_state.selected_camera
    if "Zoom-In" in cam_choice:
        camera_desc = "Slow, continuous linear zoom-in centered smoothly on the action and target entities."
    elif "Panning" in cam_choice:
        camera_desc = "Smooth lateral side-panning tracking shot maintaining steady spatial alignment."
    elif "Low-Angle" in cam_choice:
        camera_desc = "Low-angle dramatic trailing camera locked close to the floor, tracking upward momentum."
    else:
        camera_desc = "Dynamic third-person forward tracking camera locked steadily behind the runner."

    idle_style = st.session_state.target_idle_choice
    if idle_style == "Auto / Random Mix (Otomatis Bervariasi per Target)":
        idle_desc = "Target doll A performs an absurd in-place TikTok dance; Target doll B on the next stand is frantically trembling in panic."
    elif "Joget" in idle_style:
        idle_desc = "Target dolls perform absurd in-place idle dances (swaying hips, funny body movements) while strictly anchored on top of their platforms."
    elif "Panik" in idle_style:
        idle_desc = "Target dolls display funny shivering and frantic hand-waving panic animations while anchored on top of their platforms."
    elif "Sombong" in idle_style:
        idle_desc = "Target dolls perform hilarious taunting gestures (slapping chest, pointing fingers) anchored on top of their platforms."
    else:
        idle_desc = "Target dolls stand still in a classic idle pose anchored on top of their platforms."

    scene_focus = "Melanjutkan aksi lari dan rintangan di atas jalur."
    if storyboard and len(storyboard) >= scene_number:
        scene_focus = storyboard[scene_number - 1].get("fokus_aksi", scene_focus)

    custom_obstacle_instruction = st.session_state.user_scene_obstacles.get(scene_number, "")
    obstacle_inject_str = ""
    if custom_obstacle_instruction:
        obstacle_inject_str = f"SPECIAL SCENE OBSTACLE MECHANIC: {custom_obstacle_instruction}"

    prev_frame_context = ""
    if scene_number > 1 and (scene_number - 1) in st.session_state.scene_frames:
        prev_frame_context = f"STRICT CONTINUITY: Scene {scene_number} starts at the exact position where Scene {scene_number-1} ended."

    if scene_number == 1:
        action_desc = f"""
TIME PHASING & FLOW AI STRICT PHYSICS (ONE-WAY MOMENTUM):
- SETUP PHASE (0s - 2s): Target dolls ({mutation.get('boss_baru')}) are initially visible from Frame 1 on top of {prop_stand}. {idle_desc}
- IMPACT PHASE (2s - 4s): Runner ({mutation.get('runner_baru')}) sprints forward and delivers a heavy kick into the first target doll.
- AFTERMATH & UNCONSTRAINED FALL (4s - 8s): Upon impact, target doll INSTANTLY CANCELS its idle animation, transitioning into a loose ragdoll physics object. It flies off {prop_stand} and tumbles down into the void. The camera actively tracks past the platform as objects fall.
- STRICT FLOW AI ANTI-LOOPING RULE: Motion is strictly PERMANENT and ONE-WAY forward. Target doll and platform MUST remain fallen / knocked down. DO NOT reset position, bounce back, or return to initial standing pose.
"""
    elif is_final_scene:
        action_desc = f"""
ULTIMATE MULTI-ACTION CLIMAX & SACRIFICE FALL:
- Final Combo Executed: {climax_act}.
- Action Sequence: Runner ({mutation.get('runner_baru')}) strikes remaining target dolls ({mutation.get('boss_baru')}) standing on {prop_stand}.
- Sacrifice Fall (MUST HAPPEN): Runner loses balance and FALLS OFF THE EDGE TOGETHER WITH TARGET DOLLS, tumbling continuously downward into {map_env}.
- STRICT FLOW AI ANTI-LOOPING RULE: Continuous downward tumbling motion. Never loop or reset position back to the top platform.
"""
    else:
        action_desc = f"""
ROADMAP CONTINUATION: {scene_focus}. 
Target entities are initially placed on {prop_stand} performing in-place micro-animations ({idle_desc}) before being struck down permanently with irreversible physics.
"""

    audio_cues = "Immersive game audio: heavy footfalls, impact thuds, roaring wind, comedic screams, and dynamic ragdoll sound cues."

    prompt = f"""
Write ONE ultra-detailed AI video generation prompt in ENGLISH for Scene {scene_number} of {total_scenes} (approx. 8 seconds segment), optimized specifically for Flow AI video generation.

ENVIRONMENT & INITIAL SETUP (FLOW AI OBJECT PERSISTENCE):
- MAP BACKGROUND: {map_env} (Bright daytime lighting, vivid sunny sky, high-contrast colorful 3D game aesthetics).
- STATIC ENVIRONMENT LOCK: Bridges, containers, platforms ({prop_stand}), and background scenery maintain exact shapes, colors, and rigid structure with ZERO morphing, popping, flickering, or background deformation.
- INITIAL OBJECT PLACEMENT: Target dolls are fully visible in Frame 1.

ASSETS & ENTITIES:
- Style: {st.session_state.visual_style}
- Aspect Ratio: {st.session_state.aspect_ratio}
- Runner Character: {mutation.get('visual_anchor_token')} (Consistent visual identity, locked outfit and colors).
- Target Entities (Initially placed on {prop_stand}): {mutation.get('boss_baru')}
- Environment Path: {mutation.get('track_baru')}

NAVIGATIONAL ACTION OVERRIDE:
{obstacle_inject_str}

ACTION PHASING & STRICT FLOW AI PHYSICS:
{action_desc}
- Camera Movement: {camera_desc}
- Audio Cues: {audio_cues}
{prev_frame_context}

RULES:
Output ONLY the final raw English prompt without markdown formatting or extra text. Ready to copy-paste directly into Flow AI.
"""
    with st.spinner(f"Menyusun Prompt Scene {scene_number} (Flow AI No-Edit Engine)..."):
        try:
            res_prompt = ask(client, prompt, json_mode=False)
            st.session_state.scene_prompts[scene_number] = res_prompt.strip()
            return True
        except Exception as exc:
            st.error(f"Gagal menyusun prompt: {exc}")
            return False
# ==========================================
# RENDER VIEWS
# ==========================================
def render_home():
    st.title("🎬 UGC Remix Studio v11.0")
    st.caption("Engine Otomasi Konten 3D Game Challenge dengan Target Idle Motion, Opsi Kamera UI, & Flow AI No-Edit Engine.")

    st.subheader("1. Referensi Video / Skenario")
    st.file_uploader("Upload Video Referensi (Shorts atau Long Video)", type=["mp4", "mov", "webm"], key="ref_file_input")
    st.text_area("Deskripsi Referensi Manual", key="reference_text", height=80, placeholder="Contoh: Video lari menendang dua boneka berurutan...")

    st.subheader("2. Pilihan Karakter Runner & Animasi Target Idle")
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        st.selectbox("Pilih Preset Karakter Runner:", RUNNER_PRESETS, key="runner_choice")
        if st.session_state.runner_choice == "Custom / Ketik Sendiri":
            st.text_input("Tulis Deskripsi Karakter Bebas Kamu:", key="custom_runner", placeholder="Misal: Karakter anomali unik...")
    with col_k2:
        st.selectbox("🎭 Gaya Gerakan Idle Target (Sebelum Ditendang):", TARGET_IDLE_PRESETS, key="target_idle_choice")

    st.subheader("3. Modifikasi Manual Map, Dudukan & Aksi Klimaks (10 Options)")
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
    st.subheader("🧭 Navigasi & Rintangan Jalur Per-Scene (10 Options)")
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
        st.markdown("### 🚀 Hasil Remix AI (Flow AI No-Edit Optimized)")
        st.write(f"**Runner Baru:** `{remix.get('runner_baru', '-')}`")
        st.write(f"**Target Baru:** `{remix.get('boss_baru', '-')}`")
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

    st.write(f"### Adegan {current} dari {n}" + (" 💥 (SCENE KLIMAKS COMBO & SACRIFICE FALL)" if current == n else " ⚡ (FAST-PACED DUAL ACTION & IDLE TARGET)"))

    if current not in st.session_state.scene_prompts:
        if st.button(f"Generate Prompt Scene {current}", type="primary"):
            generate_scene_prompt(current)
            st.rerun()

    if current in st.session_state.scene_prompts:
        st.text_area("Prompt AI Video (Langsung Copy-Paste ke Flow AI tanpa perlu diedit):", value=st.session_state.scene_prompts[current], height=240)

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
3. "hashtags": [8 Hashtag viral & relevan dipisah spasi, gabungan Broad, Niche, dan Contextual, contoh: #UGC #3DParkour #FYP],
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

                st.markdown("#### 0️⃣ Hashtag Relevan (Copy-Paste langsung):")
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
# SIDEBAR & ROUTER EXECUTION
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
