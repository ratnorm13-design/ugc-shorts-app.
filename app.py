import json
import math
import os
import re
import time
import streamlit as st
from google import genai
from google.genai import types

# ==========================================
# CONSTANTS & CONFIGURATION (MODEL FIX)
# ==========================================
MODEL_NAME = "gemini-2.5-flash"
FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b"
]
APP_VERSION = "14.2 — Comedic Parkour & Maximum Viral Hook Engine"

MAX_FILE_SIZE_MB = 15

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

TARGET_DOLL_PRESETS = [
    "Auto / Random Mix (Otomatis Campur 10 Karakter Unik)",
    "1. Kapsul Kuning Mata Goggle (Parodi Minion)",
    "2. Astronaut Kapsul Tanpa Tangan (Parodi Among Us)",
    "3. Jelly Bean Kapsul Imut (Parodi Fall Guys)",
    "4. Alien Berantena Warna-Warni (Parodi Teletubbies)",
    "5. Kepala Konyol Toilet Putih (Parodi Skibidi)",
    "6. Monster Bulu Biru Senyum Lebar (Parodi Huggy Wuggy)",
    "7. Mini-Figure Balok Plastik (Parodi Lego)",
    "8. Ogre Hijau Gemuk Baju Cokelat (Parodi Shrek)",
    "9. Bebek Karet Kuning Raksasa (Rubber Duck)",
    "10. Tengkorak Kerangka Gila (Ragdoll Skeleton)",
]

TARGET_DOLL_PROMPT_MAP = {
    "Auto / Random Mix (Otomatis Campur 10 Karakter Unik)": 
        "a lineup of unique non-humanoid comedic ragdoll entities including yellow capsule beans, porcelain toilet heads, fuzzy blue monsters, and armless space beans",
    "1. Kapsul Kuning Mata Goggle (Parodi Minion)": 
        "a row of funny yellow capsule-shaped bean creatures wearing round metallic goggles and blue dungarees",
    "2. Astronaut Kapsul Tanpa Tangan (Parodi Among Us)": 
        "a row of vibrant armless astronaut space bean dolls wearing glassy visor helmets",
    "3. Jelly Bean Kapsul Imut (Parodi Fall Guys)": 
        "a row of cute chubby jelly bean character dolls in bright neon pastel colors",
    "4. Alien Berantena Warna-Warni (Parodi Teletubbies)": 
        "a row of colorful plush alien bean dolls with uniquely shaped head antennas in red, yellow, green, and purple",
    "5. Kepala Konyol Toilet Putih (Parodi Skibidi)": 
        "a row of funny cartoon head entities sticking out from shiny white porcelain toilet bowls",
    "6. Monster Bulu Biru Senyum Lebar (Parodi Huggy Wuggy)": 
        "a row of tall fuzzy blue monster plush dolls with long lanky arms and wide toothy grins",
    "7. Mini-Figure Balok Plastik (Parodi Lego)": 
        "a row of yellow plastic block mini-figures with rigid snap-on limbs and square torsos",
    "8. Ogre Hijau Gemuk Baju Cokelat (Parodi Shrek)": 
        "a row of chubby green ogre-like creature dolls wearing rustic brown burlap vests",
    "9. Bebek Karet Kuning Raksasa (Rubber Duck)": 
        "a row of oversized squeaky yellow rubber duckies with round glossy eyes",
    "10. Tengkorak Kerangka Gila (Ragdoll Skeleton)": 
        "a row of funny goofy 3D skeleton bone ragdolls with loose floppy physics",
}

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

MANEUVER_OPTIONS = [
    "Auto / Lari Standar (Otomatis Penyesuaian AI)",
    "1. ⚠️ Terpeleset Hampir Jatuh (Near-Miss Clutch & Recovery)",
    "2. 🧗 Lari Miring di Dinding (Wall Run & Bounce)",
    "3. 🛹 Meluncur Rendah di Floor (Sliding Tackle & Slide)",
    "4. 🚀 Melambung Trampolin & Injak dari Udara (Trampoline Vault & Smash)",
    "5. 🛹 Grind di Pipa / Pagar (Rail Balance Grinding)",
    "6. 🕺 Joget & Ejekan Sambil Lari (Mid-Run Emote & Taunt)",
    "7. 🪂 Meluncur Tali Zipline (Zipline Speed Drop)",
    "8. 🥊 Menunduk & Dodge Serangan Target (Target Counter & Dodge)",
    "9. ⚡ Injak Karpet Speed Boost (Nitro Dash Acceleration)",
    "10. 🧱 Melompat Presisi Antar Pilar (Precision Pillar Vaulting)"
]

MANEUVER_PROMPT_MAP = {
    "Auto / Lari Standar (Otomatis Penyesuaian AI)": "",
    "1. ⚠️ Terpeleset Hampir Jatuh (Near-Miss Clutch & Recovery)": "MANEUVER ACTION: Runner stumbles clumsily near the edge, almost falling into the void in panic, but dramatically catches the ledge with one hand and pulls up back onto the track.",
    "2. 🧗 Lari Miring di Dinding (Wall Run & Bounce)": "MANEUVER ACTION: Runner wall-runs vertically along the adjacent container side wall before leaping diagonally back onto the platform.",
    "3. 🛹 Meluncur Rendah di Floor (Sliding Tackle & Slide)": "MANEUVER ACTION: Runner performs a fast low-angle baseball slide underneath high obstacles while sweeping forward.",
    "4. 🚀 Melambung Trampolin & Injak dari Udara (Trampoline Vault & Smash)": "MANEUVER ACTION: Runner hits a glowing launch pad, soaring high into the air with a comedic acrobatic flip before landing on the path.",
    "5. 🛹 Grind di Pipa / Pagar (Rail Balance Grinding)": "MANEUVER ACTION: Runner leaps onto a narrow side railing, balancing on one foot while grinding forward at high speed.",
    "6. 🕺 Joget & Ejekan Sambil Lari (Mid-Run Emote & Taunt)": "MANEUVER ACTION: Runner executes a hilarious 1-second taunt emote (pointing, hip sway, finger snap) mid-sprint without slowing down.",
    "7. 🪂 Meluncur Tali Zipline (Zipline Speed Drop)": "MANEUVER ACTION: Runner grabs an overhead zipline handle, zipping rapidly over a gap before dropping precisely onto the track.",
    "8. 🥊 Menunduk & Dodge Serangan Target (Target Counter & Dodge)": "MANEUVER ACTION: Target entity tosses a comedic object; runner duck-slides under it and instantly counters with a heavy kick.",
    "9. ⚡ Injak Karpet Speed Boost (Nitro Dash Acceleration)": "MANEUVER ACTION: Runner steps on a glowing neon speed pad, gaining instant nitro boost speed with motion blur effect.",
    "10. 🧱 Melompat Presisi Antar Pilar (Precision Pillar Vaulting)": "MANEUVER ACTION: Runner rapidly vaults across a series of narrow, disconnected concrete pillars over open air."
}

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

    safety_settings = [
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    ]

    config_kwargs = {
        "temperature": 0.3,
        "safety_settings": safety_settings
    }
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"

    models_to_try = [MODEL_NAME] + FALLBACK_MODELS
    last_exception = None

    for model_candidate in models_to_try:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_candidate,
                    contents=contents,
                    config=types.GenerateContentConfig(**config_kwargs),
                )
                text = getattr(response, "text", None)
                if text and text.strip():
                    return text
            except Exception as exc:
                last_exception = exc
                time.sleep(1.0)

    raise RuntimeError(f"Gagal terhubung ke Gemini API ({models_to_try}): {last_exception}")

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

def get_active_config():
    """Fungsi Penyelaras State (Mencegah Inkonsistensi UI vs Memory Analysis)"""
    analysis = st.session_state.get("analysis", {})
    mutation = analysis.get("remixed_mutation", {})

    runner = st.session_state.get("runner_choice", RUNNER_PRESETS[1])
    if runner == "Custom / Ketik Sendiri":
        runner = st.session_state.get("custom_runner") or "Unique funny character"

    target_doll = st.session_state.get("target_doll_choice", TARGET_DOLL_PRESETS[0])
    target_desc = TARGET_DOLL_PROMPT_MAP.get(target_doll, "a row of unique comedic non-humanoid ragdoll entities")

    map_env = st.session_state.get("selected_map")
    if not map_env or map_env == "Auto (Ikuti Remix UGC)":
        map_env = mutation.get("map_environment", "Vivid 3D Game Environment")

    prop_stand = st.session_state.get("selected_prop_stand")
    if not prop_stand or prop_stand == "Auto (Ikuti Remix UGC)":
        prop_stand = mutation.get("prop_stand", "Container Roof Platforms")

    climax_act = st.session_state.get("selected_climax_action")
    if not climax_act or climax_act == "Auto (Ikuti Remix UGC)":
        climax_act = analysis.get("climax_action", "Multi-hit combo with sacrifice fall")

    return {
        "runner": runner,
        "target_doll": target_doll,
        "target_desc": target_desc,
        "map_env": map_env,
        "prop_stand": prop_stand,
        "climax_act": climax_act,
        "idle_style": st.session_state.get("target_idle_choice", TARGET_IDLE_PRESETS[0]),
        "camera": st.session_state.get("selected_camera", CAMERA_OPTIONS[0]),
        "style": st.session_state.get("visual_style", STYLE_OPTIONS[0]),
        "aspect": st.session_state.get("aspect_ratio", ASPECT_OPTIONS[0]),
        "visual_token": mutation.get("visual_anchor_token", runner)
    }

def reference_parts(client, file_uploader_obj):
    if file_uploader_obj is not None:
        try:
            data = file_uploader_obj.getvalue()
            size_mb = len(data) / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                st.warning(f"⚠️ Ukuran file video ({size_mb:.1f} MB) melebihi batas {MAX_FILE_SIZE_MB} MB. Sistem otomatis mengalihkan ke mode analisis teks jika ada.")
                if st.session_state.reference_text.strip():
                    return [types.Part.from_text(text=st.session_state.reference_text)]
                return []
            mime = getattr(file_uploader_obj, "type", None) or "video/mp4"
            return [types.Part.from_bytes(data=data, mime_type=mime)]
        except Exception as exc:
            st.warning(f"Gagal membaca file video: {exc}")
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

    cfg = get_active_config()

    prompt = f"""
Anda adalah AI Master Creative Director khusus konten viral 3D Game / Parkour / Obstacle Challenge.

HIRARKI ATURAN UTAMA (STRICT OVERRIDE):
1. UTAMA (KASTA TERTINGGI): Gunakan Pilihan Manual UI User ({cfg['runner']}, {cfg['target_doll']}, {cfg['map_env']}, {cfg['prop_stand']}, {cfg['climax_act']}) sebagai fondasi utama adegan.
2. SEKUNDER: Gunakan Video Referensi HANYA untuk mengambil inspirasi gaya kamera, pencahayaan, dan tempo gerakan. JIKA video referensi tidak memiliki rintangan/aksi yang sesuai dengan UI, ABAIKAN isi video tersebut dan SEPENUHNYA ikuti rintangan dari pilihan UI.
3. DURATION DETECTION: Tentukan durasi asli video referensi dalam detik (misal: 14 detik, 20 detik, 30 detik).

PENGATURAN SCENE DARI USER:
- Style Visual: {cfg['style']}
- Map Background: {cfg['map_env']}
- Target Stand: {cfg['prop_stand']}
- Action Climax Scene Akhir: {cfg['climax_act']}

HASILKAN JSON SANGAT RINGKAS:
{{
  "video_duration_seconds": 16,
  "original_reference": {{
    "runner_asli": "Karakter di referensi",
    "boss_asli": "Target di referensi",
    "track_asli": "Jalur di referensi"
  }},
  "remixed_mutation": {{
    "runner_baru": "{cfg['runner']}",
    "boss_baru": "{cfg['target_doll']}",
    "target_idle_behavior": "{cfg['idle_style']}",
    "camera_movement": "{cfg['camera']}",
    "track_baru": "Lintasan 3D game dengan dudukan {cfg['prop_stand']}",
    "map_environment": "{cfg['map_env']}",
    "prop_stand": "{cfg['prop_stand']}",
    "visual_anchor_token": "3D stylized game character {cfg['runner']}",
    "alasan_remix": "Penggabungan otomatis berbasis hirarki UI"
  }},
  "storyboard_plan": [
    {{"scene": 1, "fokus_aksi": "Runner meluncur dengan akselerasi kaget, menendang Target A jatuh dari dudukan, lalu lanjut lari stabil di lintasan."}},
    {{"scene": 2, "fokus_aksi": "Runner melakukan manuver parkour konyol melewati rintangan, menendang Target B jatuh, dan bersiap untuk aksi klimaks."}}
  ],
  "climax_action": "{cfg['climax_act']}",
  "spatial_layout": "Third-person tracking shot"
}}
"""
    with st.spinner("Membedah roadmap 1:1 & meracik Flow AI No-Edit Prompt..."):
        try:
            raw = ask(client, prompt, parts, json_mode=True)
            data = extract_json(raw)
            st.session_state.analysis = data
            st.session_state.storyboard = data.get("storyboard_plan", [])
            
            # --- PEMBULATAN MATEMATIKA PASTI 8 DETIK (CEILING FUNCTION) ---
            raw_seconds = data.get("video_duration_seconds", 16)
            if DURATION_SCENES.get(st.session_state.duration, 0) == 0:
                calculated_scenes = math.ceil(raw_seconds / 8)
                st.session_state.detected_scenes = max(1, min(calculated_scenes, 50))
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

    cfg = get_active_config()
    storyboard = st.session_state.analysis.get("storyboard_plan", [])
    total_scenes = scene_count()
    is_final_scene = (scene_number == total_scenes)

    # --- SINKRONISASI MULTIMODAL LAST FRAME BRIDGE ---
    prompt_parts = []
    prev_scene = scene_number - 1
    if prev_scene in st.session_state.scene_frames and st.session_state.scene_frames[prev_scene]:
        try:
            frame_file = st.session_state.scene_frames[prev_scene]
            frame_bytes = frame_file.getvalue()
            mime = getattr(frame_file, "type", "image/png")
            prompt_parts.append(types.Part.from_bytes(data=frame_bytes, mime_type=mime))
            frame_context = f"REAL-TIME VISUAL CONTINUITY: Analyze the attached image from Scene {prev_scene}'s last frame. Scene {scene_number} MUST start precisely from this exact character positioning, camera perspective, and platform alignment."
        except Exception:
            frame_context = "No image attachment parsed."
    else:
        frame_context = "No previous frame image attached."

    # Fallback Penentuan Fokus Aksi
    custom_obstacle = st.session_state.user_scene_obstacles.get(scene_number, "")
    custom_maneuver = st.session_state.user_scene_maneuvers.get(scene_number, "")
    
    scene_focus = ""
    if storyboard and len(storyboard) >= scene_number:
        scene_focus = storyboard[scene_number - 1].get("fokus_aksi", "")
    
    if not scene_focus:
        if is_final_scene:
            scene_focus = f"Klimaks aksi: {cfg['climax_act']}."
        else:
            obs_name = [k for k, v in OBSTACLE_OPTIONS.items() if v == custom_obstacle]
            obs_desc = obs_name[0] if obs_name else "rintangan jalur"
            scene_focus = f"Runner berlari kencang melewati {obs_desc}, menendang target ragdoll hingga terpelanting, lalu melanjutkan lari di atas track."

    obstacle_str = f"OBSTACLE MECHANIC: {custom_obstacle}" if custom_obstacle else ""
    maneuver_str = MANEUVER_PROMPT_MAP.get(custom_maneuver, "")

    if scene_number == 1 and not is_final_scene:
        action_instructions = f"""
- PHASE 1 (0-2s) MAXIMUM VIRAL VISUAL HOOK: High-contrast comedic opening. In Frame 1, target entities ({cfg['target_desc']}) perform absurd high-energy idle antics on {cfg['prop_stand']}. The runner ({cfg['runner']}) executes a dramatic, funny acceleration start with dynamic camera punch-in, creating instant visual suspense.
- PHASE 2 (2-4s) HIGH-IMPACT COLLISION: Runner sprints at full momentum and delivers a heavy, comedic impact kick directly into Target Entity A.
- PHASE 3 (4-8s) AFTERMATH & CONTINUITY: Target A is catapulted off the platform into the void with loose ragdoll physics.
- CRITICAL FOOTING LOCK: Runner MUST land safely and firmly on the track surface, maintain perfect upright balance, and sprint continuously forward toward the next section. DO NOT let the runner fall in Scene 1.
"""
    elif is_final_scene:
        action_instructions = f"""
- CLIMAX ACTION: {cfg['climax_act']}.
- ACTION: Runner ({cfg['runner']}) strikes remaining target entities on {cfg['prop_stand']}.
- SACRIFICE FALL (MANDATORY IN FINAL SCENE): Runner loses balance and tumbles off the edge together with the target into {cfg['map_env']}.
"""
    else:
        action_instructions = f"""
- SCENE {scene_number} ACTION: {scene_focus}.
{f"- {maneuver_str}" if maneuver_str else ""}
- ACTION: Runner ({cfg['runner']}) strikes target entity ({cfg['target_desc']}) off {cfg['prop_stand']}.
- CRITICAL FOOTING LOCK: Runner MUST land safely on the track surface, maintain balance, and continue sprinting forward along the path. DO NOT fall in this middle scene.
"""

    prompt = f"""
System Directive: You are a Flow AI Prompt Compiler. Convert the following sequence into ONE ultra-compact, high-density English prompt (<110 words) optimized for Flow AI video generator without glitching or morphing.

{frame_context}

SCENE PARAMETERS:
- Style: {cfg['style']}, 9:16 aspect ratio.
- Environment: {cfg['map_env']}, bright daytime sky. Rigid environment persistence, zero background flickering.
- Character: {cfg['visual_token']}
- Target Entities: {cfg['target_desc']} on {cfg['prop_stand']}
- Camera: {cfg['camera']}
{obstacle_str}

ACTION SEQUENCE:
{action_instructions}

NATURAL TIME EXTENSION & PACING RULES:
If the action finishes early in this 8-second segment, fill remaining seconds naturally with extended ragdoll tumbling physics, smooth landing foot adjustments, and continuous forward dash momentum. NEVER freeze or apply fake slow motion.

OUTPUT FORMAT:
Provide ONLY the final direct prompt text in clear English. Do not write markdown tags, extra commentary, or section labels.
"""
    try:
        res_prompt = ask(client, prompt, parts=prompt_parts, json_mode=False)
        st.session_state.scene_prompts[scene_number] = res_prompt.strip()
        return True
    except Exception as exc:
        st.error(f"⚠️ Gagal menyusun Prompt Scene {scene_number}: {exc}")
        return False
# ==========================================
# RENDER VIEWS
# ==========================================
def render_home():
    st.title("🎬 UGC Remix Studio v14.2")
    st.caption("Engine Otomasi Konten 3D Game Challenge dengan Comedic Parkour Maneuvers, Multimodal Continuity Bridge, & Flow AI No-Edit Engine.")

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
