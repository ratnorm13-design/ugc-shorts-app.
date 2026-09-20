import json
import re
import time
from google import genai
from google.genai import types

# Menggunakan versi model Gemini 3.6 Flash
MODEL_NAME = "gemini-3.6-flash"
APP_VERSION = "10.0 — Full Map/Prop Overrides, Multi-Action Climax & Zero Pop-In Engine"

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
    "🪜 Sky-High Spiral Metal Ladder": "MANDATORY NAVIGATIONAL ACTION: Runner rapidly climbs a steep spiral metal ladder hovering high over open air."
}

ASPECT_OPTIONS = ["9:16 — Shorts / Reels / TikTok", "16:9 — YouTube Long", "1:1 — Kotak"]

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
                raise RuntimeError(f"Gagal terhubung ke Gemini ({MODEL_NAME}): {exc}")
            time.sleep(1.5)
