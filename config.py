import json
import re
import time
from google.genai import types

APP_VERSION = "v10.0 — Ultimate 3D Parkour & UGC Remix Studio"

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

MAP_OPTIONS = [
    "Auto (Ikuti Remix UGC)",
    "Container Roofs High Above Ocean (Siang Bolong)",
    "Rooftop City Skyscraper Parkour",
    "Neon Cyberpunk Highway Container",
    "Tropical Island Obstacle Track",
    "Industrial Factory Roofs",
    "Desert Canyons Suspension Bridge",
    "Snowy Mountain Cliffside Containers",
    "Futuristic Space Station Walkway",
    "Retro Arcade Neon City Grid"
]

PROP_STAND_OPTIONS = [
    "Auto (Ikuti Remix UGC)",
    "Container Roofs",
    "Steel Beams Platform",
    "Wooden Plank Bridge",
    "Glass Rooftop Walkway",
    "Narrow Scaffold Poles",
    "Bouncy Trampoline Mesh",
    "Industrial Conveyor Belts",
    "Floating Neon Grid Panels",
    "Rusted Pipeline Surfaces"
]

CLIMAX_ACTION_OPTIONS = [
    "Auto (Ikuti Remix UGC)",
    "Double-hit combo and chaotic ragdoll collapse",
    "Spinning hurricane kick knocking all target dolls off the edge",
    "High-speed tackle causing domino effect ragdoll explosion",
    "Sliding tackle launching multiple obstacles into the air",
    "Aerial dive-kick triggering massive chain-reaction collapse",
    "Backflip stomp shattering the final platform structure",
    "Shoulder-charge impact sending targets flying off-screen",
    "Power-slide sweep knocking down all remaining obstacles",
    "Dramatic final leap with slow-motion multi-target impact"
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

OBSTACLE_OPTIONS = {
    "None / Lari Datar": "",
    "🪜 Steep Staircase (Naik Tangga Besi)": "MANDATORY NAVIGATIONAL ACTION: Runner approaches and rapidly climbs up a steep metal staircase/ladder to reach a higher elevated platform.",
    "🛝 Glass Pipe Slide (Meluncur Perosotan)": "MANDATORY NAVIGATIONAL ACTION: Runner slides down a transparent glass pipe/slide at high speed before landing gracefully.",
    "🎯 Bounce Pad / Trampolin (Pelontar Vertikal)": "MANDATORY NAVIGATIONAL ACTION: Runner steps onto a high-impulse launch pad and bounces high up into the air to the next platform.",
    "🌉 Thin Steel Beam (Jembatan Besi Sempit)": "MANDATORY NAVIGATIONAL ACTION: Runner carefully sprints across a narrow steel beam balancing high over open gaps.",
    "🪢 Zipline / Swing Rope (Bergelayut Tali)": "MANDATORY NAVIGATIONAL ACTION: Runner leaps off the edge, grabs an overhead zip-line/rope, and swings across a massive gap.",
    "⛓️ Swinging Pendulum (Menghindari Palu)": "ENVIRONMENT MECHANIC: Giant swinging pendulums obstruct the path; runner must weave and dodge around them skillfully."
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

def ask(client, prompt: str, parts=None, json_mode: bool = False, model_name: str = "gemini-3.6-flash") -> str:
    media_parts = list(parts or [])
    content_parts = media_parts + [types.Part.from_text(text=prompt)]
    contents = [types.Content(role="user", parts=content_parts)]

    config_kwargs = {"temperature": 0.4}
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model_name,
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
