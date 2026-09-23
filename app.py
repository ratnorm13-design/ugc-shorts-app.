# ==========================================
# BAGIAN 1 dari 2: CONFIG, CONSTANTS, & CORE LOGIC
# ==========================================
import json
import math
import os
import re
import time
import streamlit as st
from PIL import Image
import google.generativeai as genai

# ==========================================
# 1. PAGE CONFIG & CONSTANTS
# ==========================================
st.set_page_config(
    page_title="UGC Remix Studio v14.2",
    page_icon="🎬",
    layout="wide"
)

# Daftar model resmi Google Gemini (Urutan dari versi terbaru 3.8, 3.6, lalu 3.5)
PRIMARY_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash"
]
APP_VERSION = "14.2 — Production Stable Engine"
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
    "Auto / Random Mix (Otomatis Campur 10 Karakter Unik)": "a lineup of unique non-humanoid comedic ragdoll entities including yellow capsule beans, porcelain toilet heads, fuzzy blue monsters, and armless space beans",
    "1. Kapsul Kuning Mata Goggle (Parodi Minion)": "a row of funny yellow capsule-shaped bean creatures wearing round metallic goggles and blue dungarees",
    "2. Astronaut Kapsul Tanpa Tangan (Parodi Among Us)": "a row of vibrant armless astronaut space bean dolls wearing glassy visor helmets",
    "3. Jelly Bean Kapsul Imut (Parodi Fall Guys)": "a row of cute chubby jelly bean character dolls in bright neon pastel colors",
    "4. Alien Berantena Warna-Warni (Parodi Teletubbies)": "a row of colorful plush alien bean dolls with uniquely shaped head antennas in red, yellow, green, and purple",
    "5. Kepala Konyol Toilet Putih (Parodi Skibidi)": "a row of funny cartoon head entities sticking out from shiny white porcelain toilet bowls",
    "6. Monster Bulu Biru Senyum Lebar (Parodi Huggy Wuggy)": "a row of tall fuzzy blue monster plush dolls with long lanky arms and wide toothy grins",
    "7. Mini-Figure Balok Plastik (Parodi Lego)": "a row of yellow plastic block mini-figures with rigid snap-on limbs and square torsos",
    "8. Ogre Hijau Gemuk Baju Cokelat (Parodi Shrek)": "a row of chubby green ogre-like creature dolls wearing rustic brown burlap vests",
    "9. Bebek Karet Kuning Raksasa (Rubber Duck)": "a row of oversized squeaky yellow rubber duckies with round glossy eyes",
    "10. Tengkorak Kerangka Gila (Ragdoll Skeleton)": "a row of funny goofy 3D skeleton bone ragdolls with loose floppy physics",
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
# 2. STATE INITIALIZATION
# ==========================================
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
    "detected_scenes": 3,
    "seo": {},
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

def go(page_name: str):
    st.session_state.page = page_name
    st.rerun()

# ==========================================
# 3. HELPER FUNCTIONS & CORE LOGIC
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
        raise ValueError("Respons AI tidak berisi format JSON yang valid.")
    start = min(starts)
    for end in range(len(text), start, -1):
        try:
            return json.loads(text[start:end].strip())
        except Exception:
            continue
    raise ValueError("Gagal memproses struktur JSON dari AI.")

def configure_api():
    # Mengutamakan Input Manual dari UI jika ada, baru fallback ke Environment Variable
    key = st.session_state.get("api_key", "").strip() or os.getenv("GEMINI_API_KEY", "").strip()
    key = key.strip("`\"' ")
    if not key:
        st.error("Masukkan Gemini API Key terlebih dahulu pada Control Panel di Sidebar.")
        return False
    
    genai.configure(api_key=key)
    return True

def ask(prompt: str, parts=None, json_mode: bool = False) -> str:
    if not configure_api():
        raise RuntimeError("API Key belum terkonfigurasi.")

    media_parts = list(parts or [])
    contents = media_parts + [prompt]

    gen_config = {"temperature": 0.3}
    if json_mode:
        gen_config["response_mime_type"] = "application/json"

    error_logs = []

    # Coba satu per satu model sampai berhasil
    for model_candidate in PRIMARY_MODELS:
        try:
            model = genai.GenerativeModel(
                model_name=model_candidate,
                generation_config=gen_config
            )
            response = model.generate_content(contents)
            text = getattr(response, "text", None)
            if text and text.strip():
                return text
        except Exception as exc:
            error_logs.append(f"[{model_candidate}]: {exc}")
            time.sleep(0.3)

    # Tampilkan diagnosa detail jika semua model gagal
    joined_errors = " | ".join(error_logs)
    raise RuntimeError(f"Gagal terhubung ke Gemini API. Detail error per model: {joined_errors}")

def scene_count() -> int:
    val = DURATION_SCENES.get(st.session_state.duration, 0)
    if val == 0:
        return st.session_state.detected_scenes
    return val

def get_active_config():
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

def reference_parts(file_uploader_obj):
    if file_uploader_obj is not None:
        try:
            data = file_uploader_obj.getvalue()
            size_mb = len(data) / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                st.warning(f"⚠️ Ukuran file ({size_mb:.1f} MB) melebihi batas {MAX_FILE_SIZE_MB} MB. Beralih ke skenario teks.")
                if st.session_state.reference_text.strip():
                    return [st.session_state.reference_text]
                return []
            mime = getattr(file_uploader_obj, "type", None) or "video/mp4"
            return [{"mime_type": mime, "data": data}]
        except Exception as exc:
            st.warning(f"Gagal membaca file referensi: {exc}")
            return []
    if st.session_state.reference_text.strip():
        return [st.session_state.reference_text]
    return []

def run_analysis():
    ref_file = st.session_state.get("ref_file_input")
    parts = reference_parts(ref_file)
    if not parts and not st.session_state.reference_text.strip():
        st.warning("Masukkan atau upload video/skenario referensi terlebih dahulu.")
        return

    cfg = get_active_config()
    target_scenes = scene_count()
    if target_scenes == 0:
        target_scenes = 3

    prompt = f"""
Anda adalah AI Master Creative Director khusus konten viral 3D Game / Parkour / Obstacle Challenge.

HIRARKI ATURAN UTAMA:
1. UTAMA: Gunakan Pilihan Manual UI User ({cfg['runner']}, {cfg['target_doll']}, {cfg['map_env']}, {cfg['prop_stand']}, {cfg['climax_act']}) sebagai fondasi utama adegan.
2. SEKUNDER: Gunakan Referensi Teks/Video HANYA untuk mengambil inspirasi tempo gerakan.
3. STORYBOARD LENGTH LOCK: Hasilkan skenario runtut tepat sebanyak {target_scenes} adegan/scene.

HASILKAN JSON LENGKAP:
{{
  "video_duration_seconds": {target_scenes * 8},
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
    {", ".join([f'{{"scene": {i}, "fokus_aksi": "Aksi spesifik adegan {i}"}}' for i in range(1, target_scenes + 1)])}
  ],
  "climax_action": "{cfg['climax_act']}",
  "spatial_layout": "Third-person tracking shot"
}}
"""
    with st.spinner("Membedah roadmap & meracik Flow AI Prompt..."):
        try:
            raw = ask(prompt, parts=parts, json_mode=True)
            data = extract_json(raw)
            st.session_state.analysis = data
            st.session_state.storyboard = data.get("storyboard_plan", [])
            
            raw_seconds = data.get("video_duration_seconds", target_scenes * 8)
            if DURATION_SCENES.get(st.session_state.duration, 0) == 0:
                calculated_scenes = math.ceil(raw_seconds / 8)
                st.session_state.detected_scenes = max(1, min(calculated_scenes, 50))
            else:
                st.session_state.detected_scenes = target_scenes
            
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}
            st.session_state.current_scene = 1
            st.session_state.page = "analysis"
            st.rerun()
        except Exception as exc:
            st.error(f"Analisis gagal: {exc}")

def generate_scene_prompt(scene_number: int) -> bool:
    cfg = get_active_config()
    storyboard = st.session_state.analysis.get("storyboard_plan", [])
    total_scenes = scene_count()
    is_final_scene = (scene_number == total_scenes)

    prompt_parts = []
    prev_scene = scene_number - 1
    
    # Penanganan gambar frame continuity yang aman
    if prev_scene in st.session_state.scene_frames and st.session_state.scene_frames[prev_scene]:
        try:
            frame_data = st.session_state.scene_frames[prev_scene]
            if isinstance(frame_data, Image.Image):
                img = frame_data
            else:
                frame_data.seek(0)
                img = Image.open(frame_data).convert("RGB")
                
            prompt_parts.append(img)
            frame_context = f"REAL-TIME VISUAL CONTINUITY: Maintain identical aesthetic, color palette, and character design as shown in Scene {prev_scene}'s frame."
        except Exception as e:
            frame_context = f"No previous image loaded ({e})."
    else:
        frame_context = "No previous frame image attached."

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
            scene_focus = f"Runner berlari kencang melewati {obs_desc}, menendang target ragdoll."

    obstacle_str = f"OBSTACLE MECHANIC: {custom_obstacle}" if custom_obstacle else ""
    maneuver_str = MANEUVER_PROMPT_MAP.get(custom_maneuver, "")

    if scene_number == 1 and not is_final_scene:
        action_instructions = f"""
- PHASE 1 HOOK: High-contrast comedic opening. Target entities ({cfg['target_desc']}) perform idle taunt antics on {cfg['prop_stand']}. Runner ({cfg['runner']}) executes fast acceleration run on {cfg['map_env']}.
- PHASE 2 IMPACT: Runner delivers a heavy kick into Target Entity.
- PHASE 3 AFTERMATH: Target catapulted off into void with loose ragdoll physics.
"""
    elif is_final_scene:
        action_instructions = f"""
- CLIMAX ACTION: {cfg['climax_act']}.
- ACTION: Runner ({cfg['runner']}) strikes remaining target entities on {cfg['prop_stand']}.
- SACRIFICE FALL: Runner loses balance and tumbles off edge together into {cfg['map_env']}.
"""
    else:
        action_instructions = f"""
- SCENE {scene_number} ACTION: {scene_focus}.
{f"- {maneuver_str}" if maneuver_str else ""}
- ACTION: Runner ({cfg['runner']}) strikes target entity ({cfg['target_desc']}) off {cfg['prop_stand']}.
- FOOTING LOCK: Runner lands safely on track and continues forward.
"""

    prompt = f"""
System Directive: Convert sequence into ONE compact English prompt (<100 words) for Flow AI / UGC video generator.

{frame_context}

SCENE PARAMETERS:
- Style: {cfg['style']}, 9:16 aspect ratio.
- Environment: {cfg['map_env']}.
- Character: {cfg['visual_token']}
- Target Entities: {cfg['target_desc']} on {cfg['prop_stand']}
- Camera: {cfg['camera']}
{obstacle_str}

ACTION SEQUENCE:
{action_instructions}

OUTPUT FORMAT: Provide ONLY the final prompt text in English.
"""
    try:
        res_prompt = ask(prompt, parts=prompt_parts, json_mode=False)
        st.session_state.scene_prompts[scene_number] = res_prompt.strip()
        return True
    except Exception as exc:
        st.error(f"⚠️ Gagal menyusun Prompt Scene {scene_number}: {exc}")
        return False
# ==========================================
# BAGIAN 2 dari 2: SEO GENERATOR, UI RENDERING, & MAIN ROUTING
# ==========================================

# ==========================================
# 4. SEO GENERATOR LOGIC
# ==========================================
def generate_seo_metadata():
    cfg = get_active_config()
    prompt = f"""
Anda adalah pakar SEO & Content Strategist Media Sosial (TikTok, YouTube Shorts, Instagram Reels) khusus ceruk konten viral "GTA V Style Ragdoll & Obstacle Challenge".

Buatkan paket metadata SEO lengkap berbasis konfigurasi berikut:
- Character / Runner: {cfg['runner']}
- Target Entity: {cfg['target_doll']}
- Map / Environment: {cfg['map_env']}
- Style Visual: {cfg['style']}

HASILKAN JSON LENGKAP:
{{
  "judul_viral": [
    "5 Pilihan Judul Clickbait & High-CTR dalam Bahasa Indonesia (pake emoji)"
  ],
  "deskripsi_video": "Deskripsi lengkap 2-3 paragraf optimasi kata kunci untuk deskripsi Shorts/Reels/TikTok.",
  "hashtags": [
    "#Hashtag1", "#Hashtag2", "#Hashtag3", "#Hashtag4", "#Hashtag5",
    "#Hashtag6", "#Hashtag7", "#Hashtag8", "#Hashtag9", "#Hashtag10"
  ],
  "tags_keywords": "gta 5 ragdoll, obstacle challenge, parkour game, ugc remix, tiktok game viral"
}}
"""
    with st.spinner("Membuat metadata SEO viral..."):
        try:
            raw = ask(prompt, json_mode=True)
            st.session_state.seo = extract_json(raw)
            return True
        except Exception as exc:
            st.error(f"Gagal generate SEO: {exc}")
            return False


# ==========================================
# 5. UI RENDERING FUNCTIONS
# ==========================================
def render_sidebar():
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.caption(f"App Version: {APP_VERSION}")
        st.markdown("---")

        # API Key Input
        api_key_input = st.text_input(
            "Gemini API Key",
            value=st.session_state.api_key,
            type="password",
            help="Masukkan API Key Google Gemini Anda di sini."
        )
        st.session_state.api_key = api_key_input

        if not st.session_state.api_key and os.getenv("GEMINI_API_KEY"):
            st.info("💡 Menggunakan API Key dari System Env.")

        st.markdown("---")

        # Navigation
        st.subheader("🧭 Navigasi Modul")
        if st.button("🏠 1. Setup Konfigurasi & Analisis", use_container_width=True):
            go("home")
        
        btn_disabled_analysis = not bool(st.session_state.analysis)
        if st.button("📊 2. Blueprint & Spatial Layout", use_container_width=True, disabled=btn_disabled_analysis):
            go("analysis")

        if st.button("🎬 3. Scene Prompt Studio", use_container_width=True, disabled=btn_disabled_analysis):
            go("scenes")

        if st.button("🚀 4. Viral SEO Generator", use_container_width=True, disabled=btn_disabled_analysis):
            go("seo")

        st.markdown("---")
        if st.button("🔄 Reset Semua State", type="secondary", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


def render_home():
    st.title("🎬 UGC Remix Studio v14.2")
    st.subheader("Generator Prompt AI Video Viral untuk Flow AI & UGC Engine")
    st.markdown("---")

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("### 📥 1. Referensi Skenario & Video")
        
        uploaded_file = st.file_uploader(
            "Upload Video Referensi (MP4/MOV, Max 15MB)",
            type=["mp4", "mov", "avi", "webm"],
            key="ref_file_input"
        )
        
        ref_text = st.text_area(
            "Atau Tuliskan Deskripsi Skenario Referensi Teks",
            value=st.session_state.reference_text,
            placeholder="Contoh: Pocong melompat cepat di atas lintasan peti kemas rooftop...",
            height=120
        )
        st.session_state.reference_text = ref_text

        st.markdown("---")
        st.markdown("### ⚙️ 2. Format & Durasi Video")
        
        dur_choice = st.selectbox(
            "Target Durasi & Jumlah Scene",
            options=list(DURATION_SCENES.keys()),
            index=list(DURATION_SCENES.keys()).index(st.session_state.duration) if st.session_state.duration in DURATION_SCENES else 0
        )
        st.session_state.duration = dur_choice

        asp_choice = st.selectbox(
            "Aspect Ratio Video",
            options=ASPECT_OPTIONS,
            index=ASPECT_OPTIONS.index(st.session_state.aspect_ratio)
        )
        st.session_state.aspect_ratio = asp_choice

        style_choice = st.selectbox(
            "Gaya Visual / Graphic Engine",
            options=STYLE_OPTIONS,
            index=STYLE_OPTIONS.index(st.session_state.visual_style)
        )
        st.session_state.visual_style = style_choice

        cam_choice = st.selectbox(
            "Kamera / Pergerakan View",
            options=CAMERA_OPTIONS,
            index=CAMERA_OPTIONS.index(st.session_state.selected_camera)
        )
        st.session_state.selected_camera = cam_choice

    with col_right:
        st.markdown("### 🎭 3. Preset Karakter & Arena (Override UI)")

        runner_c = st.selectbox(
            "🏃 Karakter Utama (Runner)",
            options=RUNNER_PRESETS,
            index=RUNNER_PRESETS.index(st.session_state.runner_choice) if st.session_state.runner_choice in RUNNER_PRESETS else 0
        )
        st.session_state.runner_choice = runner_c

        if runner_c == "Custom / Ketik Sendiri":
            c_runner = st.text_input(
                "Ketik Deskripsi Karakter Custom",
                value=st.session_state.custom_runner,
                placeholder="Contoh: Robot Transformers merah bertopeng topeng monyet..."
            )
            st.session_state.custom_runner = c_runner

        doll_c = st.selectbox(
            "🎯 Karakter Target / Ragdoll Doll",
            options=TARGET_DOLL_PRESETS,
            index=TARGET_DOLL_PRESETS.index(st.session_state.target_doll_choice) if st.session_state.target_doll_choice in TARGET_DOLL_PRESETS else 0
        )
        st.session_state.target_doll_choice = doll_c

        idle_c = st.selectbox(
            "💃 Gaya Idle / Pose Target",
            options=TARGET_IDLE_PRESETS,
            index=TARGET_IDLE_PRESETS.index(st.session_state.target_idle_choice) if st.session_state.target_idle_choice in TARGET_IDLE_PRESETS else 0
        )
        st.session_state.target_idle_choice = idle_c

        map_c = st.selectbox(
            "🗺️ Arena / Map Environment",
            options=MAP_OPTIONS,
            index=MAP_OPTIONS.index(st.session_state.selected_map) if st.session_state.selected_map in MAP_OPTIONS else 0
        )
        st.session_state.selected_map = map_c

        prop_c = st.selectbox(
            "📦 Dudukan / Prop Stand Target",
            options=PROP_STAND_OPTIONS,
            index=PROP_STAND_OPTIONS.index(st.session_state.selected_prop_stand) if st.session_state.selected_prop_stand in PROP_STAND_OPTIONS else 0
        )
        st.session_state.selected_prop_stand = prop_c

        climax_c = st.selectbox(
            "💥 Action Klimaks Scene Akhir",
            options=CLIMAX_ACTION_OPTIONS,
            index=CLIMAX_ACTION_OPTIONS.index(st.session_state.selected_climax_action) if st.session_state.selected_climax_action in CLIMAX_ACTION_OPTIONS else 0
        )
        st.session_state.selected_climax_action = climax_c

    st.markdown("---")
    if st.button("🚀 MULAI ANALISIS & RACIK ROADMAP PROMPT", type="primary", use_container_width=True):
        run_analysis()


def render_analysis():
    st.title("📊 Blueprint & Spatial Layout")
    st.caption("Hasil analisis skenario referensi & konfigurasi remix AI.")
    st.markdown("---")

    analysis = st.session_state.analysis
    if not analysis:
        st.warning("Belum ada data analisis. Silakan kembali ke Home.")
        if st.button("⬅️ Kembali ke Home"):
            go("home")
        return

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🔄 Remixed Mutation Plan")
        mutation = analysis.get("remixed_mutation", {})
        st.json(mutation)

        st.markdown("### 📽️ Track & Spatial Layout")
        st.info(analysis.get("spatial_layout", "Third-person dynamic tracking shot."))

    with col2:
        st.markdown("### 📋 Storyboard Flow Plan")
        storyboard = analysis.get("storyboard_plan", [])
        for idx, item in enumerate(storyboard, start=1):
            with st.expander(f"Scene {idx}: {item.get('fokus_aksi', 'Aksi Scene')}", expanded=True):
                st.write(f"**Focus**: {item.get('fokus_aksi', '-')}")

    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("⬅️ Edit Setup Konfigurasi", use_container_width=True):
            go("home")
    with col_btn2:
        if st.button("🎬 Lanjut ke Scene Prompt Studio ➡️", type="primary", use_container_width=True):
            go("scenes")


def render_scenes():
    st.title("🎬 Scene Prompt Studio")
    st.caption("Generate prompt presisi untuk setiap scene video Flow AI Anda.")
    st.markdown("---")

    total_scenes = scene_count()
    if total_scenes == 0:
        st.warning("Data scene belum terkonfigurasi.")
        return

    # Navigation tabs for scenes
    scene_tabs = [f"Scene {i}" for i in range(1, total_scenes + 1)]
    active_tab_idx = min(st.session_state.current_scene - 1, total_scenes - 1)
    
    selected_tab = st.radio("Pilih Scene:", scene_tabs, index=active_tab_idx, horizontal=True)
    current_sc = int(selected_tab.replace("Scene ", ""))
    st.session_state.current_scene = current_sc

    st.markdown(f"### 📍 Mengedit & Generate Prompt: Scene {current_sc} dari {total_scenes}")

    col_ctrl, col_res = st.columns([1, 1], gap="large")

    with col_ctrl:
        st.markdown("#### 🛠️ Modifier Kustom Adegan")
        
        # Obstacle Selection
        current_obs = st.session_state.user_scene_obstacles.get(current_sc, "")
        obs_keys = list(OBSTACLE_OPTIONS.keys())
        default_obs_idx = 0
        for i, k in enumerate(obs_keys):
            if OBSTACLE_OPTIONS[k] == current_obs:
                default_obs_idx = i
                break

        sel_obs_key = st.selectbox(
            f"⚡ Rintangan Khusus (Scene {current_sc})",
            options=obs_keys,
            index=default_obs_idx
        )
        st.session_state.user_scene_obstacles[current_sc] = OBSTACLE_OPTIONS[sel_obs_key]

        # Maneuver Selection
        current_man = st.session_state.user_scene_maneuvers.get(current_sc, "")
        man_keys = MANEUVER_OPTIONS
        default_man_idx = 0
        if current_man in man_keys:
            default_man_idx = man_keys.index(current_man)

        sel_man_key = st.selectbox(
            f"🏃 Gerakan/Aksi Khusus (Scene {current_sc})",
            options=man_keys,
            index=default_man_idx
        )
        st.session_state.user_scene_maneuvers[current_sc] = sel_man_key

        # Image frame continuity uploader dengan conversion aman
        if current_sc > 1:
            st.markdown(f"#### 🖼️ Frame Continuity (Reference Scene {current_sc - 1})")
            uploaded_frame = st.file_uploader(
                f"Upload Frame Gambar Hasil Render Scene {current_sc - 1}",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"frame_uploader_{current_sc - 1}"
            )
            if uploaded_frame:
                try:
                    uploaded_frame.seek(0)
                    img = Image.open(uploaded_frame)
                    # Deep copy agar image pointer tetap tersimpan aman di session state
                    img_copy = img.copy().convert("RGB")
                    st.session_state.scene_frames[current_sc - 1] = img_copy
                    st.image(img_copy, caption=f"Frame Acuan Continuity Scene {current_sc - 1}", use_container_width=True)
                except Exception as e:
                    st.error(f"Gagal memuat gambar: {e}")

        st.markdown("---")
        if st.button(f"✨ Generate Prompt Scene {current_sc}", type="primary", use_container_width=True):
            if generate_scene_prompt(current_sc):
                st.success(f"Prompt Scene {current_sc} berhasil dibuat!")

        if st.button(f"⚡ Generate SEMUA Prompt ({total_scenes} Scene)", use_container_width=True):
            progress_bar = st.progress(0)
            for sc in range(1, total_scenes + 1):
                generate_scene_prompt(sc)
                progress_bar.progress(sc / total_scenes)
            st.success("Semua prompt scene berhasil dibuat!")
            st.rerun()

    with col_res:
        st.markdown("#### 📝 Hasil Prompt Flow AI")
        prompt_text = st.session_state.scene_prompts.get(current_sc, "")

        if prompt_text:
            st.text_area(
                f"Prompt Ready-to-Copy (Scene {current_sc})",
                value=prompt_text,
                height=220
            )
            st.code(prompt_text, language="text")
        else:
            st.info("Klik tombol 'Generate Prompt' di samping untuk meracik prompt AI Flow.")

    st.markdown("---")
    st.markdown("### 📜 Ringkasan Semua Prompt Scene")
    for sc in range(1, total_scenes + 1):
        p_txt = st.session_state.scene_prompts.get(sc, "*Belum digenerate*")
        with st.expander(f"🎬 Scene {sc} Prompt", expanded=False):
            st.code(p_txt, language="text")

    st.markdown("---")
    if st.button("🚀 Lanjut ke Viral SEO Generator ➡️", type="primary", use_container_width=True):
        go("seo")


def render_seo():
    st.title("🚀 Viral SEO Metadata Generator")
    st.caption("Optimasi Judul, Deskripsi, dan Hashtag untuk TikTok, Shorts, & Reels.")
    st.markdown("---")

    if not st.session_state.seo:
        if st.button("✨ Generate Metadata SEO Sekarang", type="primary", use_container_width=True):
            generate_seo_metadata()

    seo_data = st.session_state.seo
    if seo_data:
        col1, col2 = st.columns([1, 1], gap="large")

        with col1:
            st.markdown("### 📌 Pilihan Judul High-CTR (Clickbait)")
            titles = seo_data.get("judul_viral", [])
            for i, t in enumerate(titles, start=1):
                st.markdown(f"**{i}.** {t}")

            st.markdown("### 🏷️ Hashtag Optimal")
            hashtags = seo_data.get("hashtags", [])
            st.code(" ".join(hashtags), language="text")

            st.markdown("### 🔑 Tags / Keywords")
            st.code(seo_data.get("tags_keywords", ""), language="text")

        with col2:
            st.markdown("### 📝 Deskripsi Video Optimized")
            st.text_area(
                "Copy Deskripsi",
                value=seo_data.get("deskripsi_video", ""),
                height=300
            )

        st.markdown("---")
        if st.button("🔄 Regenerate SEO Metadata", use_container_width=True):
            generate_seo_metadata()
            st.rerun()


# ==========================================
# 6. MAIN ENTRYPOINT & ROUTING
# ==========================================
def main():
    render_sidebar()

    current_page = st.session_state.get("page", "home")

    if current_page == "home":
        render_home()
    elif current_page == "analysis":
        render_analysis()
    elif current_page == "scenes":
        render_scenes()
    elif current_page == "seo":
        render_seo()
    else:
        render_home()


if __name__ == "__main__":
    main()
