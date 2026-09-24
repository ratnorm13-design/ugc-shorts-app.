import json
import re
import time
import os

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="UGC Remix Studio v9.7 — Compact Scene Controls & Physical Engine",
    page_icon="🎬",
    layout="wide"
)

MODEL_NAME = "gemini-3.6-flash"

# TARGET DURATION SCENE OPTIONS
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

# FULL RESTORED RUNNER PRESETS
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

# FULL RESTORED MAP OPTIONS
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

# FULL RESTORED PROP STAND OPTIONS
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

# FULL RESTORED CLIMAX ACTION OPTIONS
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

# FULL RESTORED OBSTACLE OPTIONS
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

# INITIAL STATE DEFAULTS
DEFAULTS = {
    "page": "home",
    "api_key": "",
    "reference_file": None,
    "reference_text": "",
    "visual_style": STYLE_OPTIONS[0],
    "runner_choice": RUNNER_PRESETS[6],
    "custom_runner": "",
    "map_choice": MAP_OPTIONS[0],
    "prop_stand_choice": PROP_STAND_OPTIONS[0],
    "climax_action_choice": CLIMAX_ACTION_OPTIONS[0],
    "aspect_ratio": ASPECT_OPTIONS[0],
    "duration": "180 detik (22 Scene - 3 Menit Full Challenge)",
    "custom_instruction": "",
    "user_scene_obstacles": {},
    "analysis": {},
    "storyboard": [],
    "scene_prompts": {},
    "scene_frames": {},
    "current_scene": 1,
    "detected_scenes": 22,
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


def run_analysis():
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

    chosen_map = st.session_state.map_choice
    chosen_stand = st.session_state.prop_stand_choice
    chosen_climax = st.session_state.climax_action_choice
    total_target_scenes = scene_count()

    prompt = f"""
Anda adalah AI Master Creative Director khusus konten 3D Parkour / Ragdoll Challenge.

TUGAS UTAMA:
Buatkan STORYBOARD LENGKAP untuk EXACT {total_target_scenes} SCENE (Per scene durasi ~8 detik, total {total_target_scenes * 8} detik).

ATURAN HUKUM FISIKA KAUSALITAS & CONTINUITY LINIER (SANGAT KETAT):
1. RUNNER ({chosen_runner}) ADALAH SATU-SATUNYA PEMINCI AKSI DAN KEHANCURAN FISIK.
2. DILARANG KERAS membuat ban, platform, atau boneka hancur/berhamburan secara gaib tanpa disentuh/ditendang Runner!
3. Jika Runner diam, lingkungan HARUS diam. Setiap kehancuran HARUS akibat benturan langsung dari aksi Runner.
4. Setiap item pada array 'storyboard_plan' (harus berisi TEPAT {total_target_scenes} item) WAJIB mendeskripsikan:
   - Posisi awal Runner
   - Aksi fisik aktif Runner (misal: lari, melompat keras, menendang target ke-N)
   - Efek fisik berurutan (misal: target terpelanting karena terkena impak tendangan)
   - Posisi pendaratan Runner di akhir detik ke-8 untuk disambung oleh scene berikutnya.

DATA PARAMETER USER:
- Runner Utama: "{chosen_runner}"
- Map Arena/Place: "{chosen_map}"
- Target Stand: "{chosen_stand}"
- Aksi Klimaks Penutup (Scene Terakhir): "{chosen_climax}"

HASILKAN JSON PRESISI DENGAN ARRAY 'storyboard_plan' SEBANYAK TEPAT {total_target_scenes} ITEM:
{{
  "video_duration_seconds": {total_target_scenes * 8},
  "calculated_scene_count": {total_target_scenes},
  "original_reference": {{
    "runner_asli": "Karakter utama di referensi",
    "boss_asli": "Target di ujung",
    "track_asli": "Jalur rintangan"
  }},
  "remixed_mutation": {{
    "runner_baru": "{chosen_runner}",
    "boss_baru": "Deretan boneka target berurutan di atas {chosen_stand}",
    "track_baru": "Arena {chosen_map} dengan rantai {chosen_stand}",
    "visual_anchor_token": "Deskripsi visual spesifik {chosen_runner}",
    "alasan_remix": "Modifikasi alur fisik kausalitas"
  }},
  "storyboard_plan": [
    {{
      "scene": 1,
      "fokus_aksi": "Runner mulai berlari cepat di jalur awal, melompat presisi dan menendang boneka target pertama hingga terpelanting jatuh."
    }}
  ],
  "climax_action": "{chosen_climax}"
}}
"""
    with st.spinner(f"Menyusun Roadmap Storyboard {total_target_scenes} Scene Tanpa Cacat Kausalitas..."):
        try:
            raw = ask(client, prompt, parts, json_mode=True)
            data = extract_json(raw)
            st.session_state.analysis = data
            st.session_state.storyboard = data.get("storyboard_plan", [])
            st.session_state.detected_scenes = total_target_scenes
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}
            st.session_state.current_scene = 1
            go("analysis")
        except Exception as exc:
            st.error(f"Gagal membuat analisis roadmap: {exc}")


def generate_scene_prompt(scene_number: int) -> bool:
    client = get_client()
    if not client:
        return False

    analysis = st.session_state.analysis
    mutation = analysis.get("remixed_mutation", {})
    storyboard = analysis.get("storyboard_plan", [])
    total_scenes = scene_count()
    is_final_scene = (scene_number == total_scenes)

    scene_focus = f"Runner secara aktif melompat ke pijakan berikutnya dan menendang target fisik ke-{scene_number}."
    if storyboard and len(storyboard) >= scene_number:
        scene_focus = storyboard[scene_number - 1].get("fokus_aksi", scene_focus)

    custom_obstacle_instruction = st.session_state.user_scene_obstacles.get(scene_number, "")
    obstacle_str = f"ENVIRONMENT OBSTACLE INJECTED: {custom_obstacle_instruction}" if custom_obstacle_instruction else ""

    map_context = f"MAP ARENA: {st.session_state.map_choice}" if st.session_state.map_choice != "Auto (Ikuti Remix UGC)" else ""
    stand_context = f"TARGET STAND: Targets sit directly on {st.session_state.prop_stand_choice}" if st.session_state.prop_stand_choice != "Auto (Ikuti Remix UGC)" else ""

    parts_list = []
    prev_scene_num = scene_number - 1
    prev_prompt_text = st.session_state.scene_prompts.get(prev_scene_num, "")

    frame_context_str = ""
    if prev_scene_num in st.session_state.scene_frames and st.session_state.scene_frames[prev_scene_num]:
        try:
            frame_file = st.session_state.scene_frames[prev_scene_num]
            img_bytes = frame_file.getvalue()
            img_mime = getattr(frame_file, "type", "image/png") or "image/png"
            parts_list.append(types.Part.from_bytes(data=img_bytes, mime_type=img_mime))
            frame_context_str = f"VISION CONTINUITY REQUIREMENT: Read the attached screenshot showing Scene {prev_scene_num}'s FINAL FRAME. Scene {scene_number} MUST START EXACTLY at the runner's landing coordinates, body posture, and tire/doll positions shown in this image. No positional jumps."
        except Exception as exc:
            frame_context_str = f"CONTINUITY REQUIREMENT: Continue directly from Scene {prev_scene_num} ending state: '{prev_prompt_text}'."
    elif prev_prompt_text:
        frame_context_str = f"TEXT CONTINUITY REQUIREMENT: Continue directly from Scene {prev_scene_num} ending state: '{prev_prompt_text}'."

    prompt = f"""
Write ONE ultra-detailed AI video generation prompt in ENGLISH for Scene {scene_number} of {total_scenes} (~8 seconds segment).

VISUAL STYLE & ENVIRONMENT:
- Visual Style: {st.session_state.visual_style}
- Aspect Ratio: {st.session_state.aspect_ratio}
- Main Character (Runner): {mutation.get('visual_anchor_token')}
- Target Entities: {mutation.get('boss_baru')}
- Environment Track: {mutation.get('track_baru')}
- {map_context}
- {stand_context}
- {obstacle_str}

STRICT PHYSICAL CAUSALITY & CONTINUITY LAWS (CRITICAL):
1. RUNNER-DRIVEN ACTION ONLY: The Runner ({mutation.get('runner_baru')}) is the SOLE physical trigger in this scene. Props, tires, or dolls MUST NOT move, fly, or explode on their own.
2. NO IDLE RUNNER: The runner DOES NOT stand still. The runner is dynamically sprinting, leaping, or stomping forward.
3. CAUSE AND EFFECT: Every destruction or ragdoll fall occurs ONLY AFTER direct impact from the runner's feet/body.
4. SCENE ACTION FOCUS: {scene_focus}
5. FRAME CONTINUITY BRIDGE: {frame_context_str}

{"6. CLIMAX PAYOFF: Execute high-impact climax physical collapse as the runner tackles the final target combo!" if is_final_scene else ""}

FORMATTING RULE:
Output ONLY the raw English generation prompt string without any markdown formatting, bullet points, or commentary.
"""
    with st.spinner(f"Merancang Prompt Scene {scene_number} (Vision & Physical Causality Checked)..."):
        try:
            res_prompt = ask(client, prompt, parts=parts_list, json_mode=False)
            st.session_state.scene_prompts[scene_number] = res_prompt.strip()
            return True
        except Exception as exc:
            st.error(f"Gagal merancang prompt Scene {scene_number}: {exc}")
            return False


# UI COMPONENT RENDERING
def render_home():
    st.title("🎬 UGC Remix Studio v9.7 — Dynamic Compact Controls")
    st.caption("Engine Otomasi Video Prompt 3D Parkour dengan Pemetaan Kausalitas Fisik & Ringkas Per-Scene Control.")

    st.subheader("1. Referensi Video / Skenario Manual")
    st.file_uploader("Upload Video Referensi (Shorts / Video Panjang)", type=["mp4", "mov", "webm"], key="ref_file_input")
    st.text_area("Deskripsi Manual Referensi (Jika tidak upload video)", key="reference_text", height=70, placeholder="Contoh: Katak melompat satu per satu di atas ban bekas dan menendang boneka berurutan...")

    st.subheader("2. Pilihan Karakter & Arena (Lengkap)")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Pilih Preset Karakter Runner Utama:", RUNNER_PRESETS, key="runner_choice")
        if st.session_state.runner_choice == "Custom / Ketik Sendiri":
            st.text_input("Tulis Deskripsi Karakter Custom Kamu:", key="custom_runner")
        st.selectbox("Gaya Visual Render", STYLE_OPTIONS, key="visual_style")
    with col2:
        st.selectbox("Pilih Map Arena / Latar Place:", MAP_OPTIONS, key="map_choice")
        st.selectbox("Pilih Pijakan Target (Prop Stand):", PROP_STAND_OPTIONS, key="prop_stand_choice")

    st.subheader("3. Durasi Video & Aksi Klimaks Penutup")
    col3, col4 = st.columns(2)
    with col3:
        st.selectbox("Target Durasi & Jumlah Scene (Hingga 3 Menit):", list(DURATION_SCENES.keys()), key="duration")
        st.selectbox("Rasio Aspek Video", ASPECT_OPTIONS, key="aspect_ratio")
    with col4:
        st.selectbox("Gaya Aksi Klimaks Penutup (Scene Terakhir):", CLIMAX_ACTION_OPTIONS, key="climax_action_choice")
        st.text_area("Instruksi Tambahan (Opsional)", key="custom_instruction", height=70, placeholder="Misal: Buat efek lontaran ban lebih tinggi...")

    st.markdown("---")
    
    # REVISED: Dynamic Compact Obstacle Selector per 4 Scenes (Batch/Tab View)
    calculated_scenes = DURATION_SCENES.get(st.session_state.duration, 0)
    if calculated_scenes == 0:
        calculated_scenes = st.session_state.get("detected_scenes", 22)

    st.subheader("🧭 Navigasi Rintangan Per-Scene (Disesuaikan Durasi)")
    st.write(f"**Total Scene Ditampilkan:** {calculated_scenes} Scene ({calculated_scenes * 8} Detik Total Durasi)")

    scenes_per_group = 4
    total_groups = (calculated_scenes + scenes_per_group - 1) // scenes_per_group

    if total_groups == 1:
        # Menampilkan langsung 1-4 scene jika durasi singkat (16 - 32 detik)
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
        # Pengelompokan Tab Per-4 Scene agar tampilan ringkas jika durasi panjang (1-3 menit)
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
    st.button("🚀 PROSES & BUAT ROADMAP SCENE LINIER", type="primary", use_container_width=True, on_click=run_analysis)


def render_analysis():
    st.title("🔍 Roadmap Analysis & Storyboard Flow")
    analysis = st.session_state.get("analysis", {})
    storyboard = st.session_state.get("storyboard", [])

    if not analysis:
        st.info("Belum ada data roadmap. Kembali ke Beranda untuk memproses.")
        return

    st.success(f"⏱️ Total Target: **{scene_count()} Scene** (~{scene_count() * 8} Detik Video Full Continuity)")

    st.subheader("📋 Storyboard Terstruktur (Kausalitas Fisik Dijamin)")
    for item in storyboard:
        st.write(f"• **Scene {item.get('scene', '-')}:** {item.get('fokus_aksi', '-')}")

    st.markdown("---")
    if st.button("LANJUT KE GENERATOR PROMPT ADEGAN 🎥", type="primary", use_container_width=True):
        go("scenes")


def render_scenes():
    st.title("🎥 AI Video Prompt Generator (Vision Continuity Enabled)")
    n = scene_count()
    current = st.session_state.current_scene

    st.subheader(f"Adegan {current} dari {n} " + ("💥 (SCENE KLIMAKS)" if current == n else "⚡ (PHYSICAL ACTION)"))

    if current not in st.session_state.scene_prompts:
        if st.button(f"✨ Generate Prompt Scene {current}", type="primary"):
            generate_scene_prompt(current)
            st.rerun()

    if current in st.session_state.scene_prompts:
        st.text_area(f"Prompt AI Video Scene {current} (Copy ke Veo / Kling / Luma):", value=st.session_state.scene_prompts[current], height=180)

        st.markdown("---")
        st.subheader("🖼️ Multimodal Last Frame Bridge (Upload Frame Terakhir)")
        st.caption("Upload screenshot frame paling akhir dari video hasil Scene ini. AI akan **MEMBACA GAMBAR TERSEBUT** untuk mengunci posisi Runner di Scene berikutnya!")

        uploaded_frame = st.file_uploader(f"Upload Last Frame Scene {current}", type=["png", "jpg", "jpeg"], key=f"frame_file_{current}")
        if uploaded_frame:
            st.session_state.scene_frames[current] = uploaded_frame
            st.image(uploaded_frame, caption=f"Frame Akhir Scene {current} Terkunci untuk Scene {current+1}", width=320)

        st.markdown("---")
        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if current > 1 and st.button("← Adegan Sebelumnya"):
                st.session_state.current_scene -= 1
                st.rerun()
        with col_nav2:
            if current < n and st.button("Adegan Berikutnya →", type="primary"):
                st.session_state.current_scene += 1
                st.rerun()

        if current == n:
            st.markdown("---")
            st.subheader("🎯 Finalisasi Metadata & SEO Generator")
            if st.button("🚀 Generate Judul CTR Tinggi, Deskripsi CTA & 18 Tags SEO", type="primary", use_container_width=True):
                client = get_client()
                if client:
                    prompt = f"""
Bertindaklah sebagai Pakar Algoritma YouTube & TikTok.
Berdasarkan data remix UGC berikut: {json.dumps(st.session_state.analysis, ensure_ascii=False)}

Buatkan format SEO lengkap dalam bentuk JSON terstruktur dengan ketentuan:
1. "judul": [3 Pilihan Judul singkat, memancing curiosity gap, & CTR tinggi],
2. "deskripsi": "Deskripsi cerita singkat mengandung kata kunci natural + WAJIB ADA CALL TO ACTION (CTA) ajakan Komen seberapa seru videonya, Like, Subscribe, dan Lonceng Notifikasi",
3. "tags": [Tepat 18 Tags SEO unik berbahasa Inggris tanpa duplikat]
"""
                    with st.spinner("Meracik Judul, CTA, dan 18 Tags SEO Unik..."):
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
    st.title("🚀 Metadata & SEO Center")
    seo_data = st.session_state.get("seo", {})
    if seo_data:
        st.json(seo_data)
    else:
        st.info("Metadata SEO akan otomatis diracik saat Anda menyelesaikan prompt scene terakhir di menu Scene Prompts.")


# SIDEBAR ROUTING CONTROLS
with st.sidebar:
    st.title("⚙️ Studio Controls")
    st.text_input("Gemini API Key", key="api_key", type="password")
    st.markdown("---")
    if st.button("🏠 Beranda / Main Setup", use_container_width=True):
        go("home")
    if st.button("📋 Storyboard Roadmap", use_container_width=True):
        go("analysis")
    if st.button("🎥 Prompt Generator per Scene", use_container_width=True):
        go("scenes")
    if st.button("🚀 Metadata & SEO Center", use_container_width=True):
        go("seo")


# PAGE ROUTER
page = st.session_state.page
if page == "home":
    render_home()
elif page == "analysis":
    render_analysis()
elif page == "scenes":
    render_scenes()
elif page == "seo":
    render_seo()
