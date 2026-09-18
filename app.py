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

RUNNER_PRESETS = [
    "Custom / Ketik Sendiri",
    "Fat Orange Cat (Kucing oranye gemuk berjaket hoodie)",
    "Funny Green Frog (Katak hijau nyeleneh berkacamata hitam)",
    "Inflatable Dinosaur (Kostum dinosaurus tiup warna hijau)",
    "Minecraft Creeper Style (Karakter makhluk hijau kotak khas Minecraft)",
    "Minecraft Blocky Zombie (Karakter mayat hidup kotak-kotak ala Minecraft)",
    "Tung Tung Sahur (Karakter anomali ikonik meme sahur yang absurd)",
    "Tralalero Tralala (Karakter absurd ala hiu bermata lebar berkaki sneakers)",
    "Udindi (Karakter khas Italian brainrot, yang konyol dan nyeleneh)",
    "Pocong Gesit (Hantu Lokal Melompat Absurd)",
    "Bebek Karet Raksasa (Licin & Membal)",
    "Karakter Roblox / Blocky Noob (Balok Pecah Maksimal)",
    "Sktetelons / Tengkorak Gila (Tulang Copot & Ragdoll Mantap)"
]

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
                st.session_state.detected_scenes = max(1, min(calc_scenes, 24))
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

PHYSICS & MULTI-ACTION LAWS (MANDATORY):
- Multi-action density: The 8-second video must contain TWO distinct hits/kicks in sequence (e.g., kicking the first doll, then immediately punching/kicking the second doll placed closely ahead).
- Surface confinement: Runner stays strictly on container roofs, executing a sharp right turn transition after the second action. No falling into the water.
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


with st.sidebar:
    st.title("⚙️ Konfigurasi Sistem")
    st.session_state.api_key = st.text_input("Gemini API Key", value=st.session_state.api_key, type="password", placeholder="AIzaSy...")
    st.markdown("---")
    st.info("💡 **Panduan Cepat:**\n1. Masukkan API Key di atas.\n2. Upload referensi video / isi deskripsi.\n3. Pilih karakter runner.\n4. Klik Proses Remix.")
    st.markdown(f"**Versi:** {APP_VERSION}")


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

    if st.button("PROSES & REMIX REFERENSI", type="primary", use_container_width=True):
        run_analysis()
def render_analysis():
    st.title("📊 Hasil Bedah 1:1 Roadmap & Multi-Action Density")
    st.caption("Roadmap pemetaan struktur jalur kontainer, objek permanen, dan ritme aksi ganda.")

    analysis = st.session_state.get("analysis", {})
    if not analysis:
        st.warning("Belum ada data analisis. Silakan kembali ke Beranda.")
        if st.button("⬅️ Kembali ke Beranda"):
            go("home")
        return

    mut = analysis.get("remixed_mutation", {})
    ref = analysis.get("original_reference", {})

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🔍 Referensi Asli")
        st.markdown(f"- **Runner Asli:** {ref.get('runner_asli', '-')}")
        st.markdown(f"- **Boss/Target Asli:** {ref.get('boss_asli', '-')}")
        st.markdown(f"- **Track Asli:** {ref.get('track_asli', '-')}")
    with c2:
        st.markdown("### 🚀 Hasil Remix & Mutasi 1:1")
        st.markdown(f"- **Runner Baru:** {mut.get('runner_baru', '-')}")
        st.markdown(f"- **Target Boneka Permanen:** {mut.get('boss_baru', '-')}")
        st.markdown(f"- **Track Kontainer:** {mut.get('track_baru', '-')}")

    st.info(f"💡 **Alasan Remix:** {mut.get('alasan_remix', '-')}")

    st.markdown("### 📋 Storyboard & Rencana Multi-Action per Scene")
    storyboard = st.session_state.get("storyboard", [])
    for idx, item in enumerate(storyboard):
        s_num = item.get("scene", idx + 1)
        fokus = item.get("fokus_aksi", "Aksi lari dan rintangan.")
        st.markdown(f"**Scene {s_num}:** {fokus}")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("⬅️ Ulangi Pengaturan (Home)", use_container_width=True):
            go("home")
    with col_btn2:
        if st.button("🎬 Lanjut ke Generator Prompt Scene", type="primary", use_container_width=True):
            go("generator")


def render_generator():
    st.title("🎬 Multi-Scene & Multi-Action Prompt Generator")
    st.caption("Generate prompt video berkualitas tinggi untuk setiap scene dengan transisi dan objek permanen yang konsisten.")

    total_scenes = scene_count()
    current = st.session_state.get("current_scene", 1)

    # Navigasi tab mini per scene
    cols = st.columns(min(total_scenes, 8))
    for i in range(1, total_scenes + 1):
        with cols[(i - 1) % 8]:
            btn_type = "primary" if current == i else "secondary"
            if st.button(f"Scene {i}", key=f"btn_scene_{i}", type=btn_type, use_container_width=True):
                st.session_state.current_scene = i
                st.rerun()

    st.markdown(f"---")
    st.subheader(f"⚙️ Pengaturan Scene {current} dari {total_scenes}")

    # Tombol generate otomatis untuk scene aktif
    if st.button(f"✨ Generate Prompt Scene {current}", type="primary"):
        generate_scene_prompt(current)
        st.rerun()

    prompts = st.session_state.get("scene_prompts", {})
    current_prompt = prompts.get(current, "")

    edited_prompt = st.text_area(
        f"Prompt Video untuk Scene {current} (Bisa diedit manual):",
        value=current_prompt,
        height=150,
        key=f"text_prompt_{current}",
    )
    if edited_prompt != current_prompt:
        st.session_state.scene_prompts[current] = edited_prompt

    st.markdown("---")
    st.subheader(f"🖼️ Simulasi / Catatan Visual Frame & Aksi Ganda Scene {current}")
    
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if current > 1:
            if st.button("⬅️ Scene Sebelumnya"):
                st.session_state.current_scene = current - 1
                st.rerun()
    with col_nav2:
        if current < total_scenes:
            if st.button("Scene Berikutnya ➡️"):
                st.session_state.current_scene = current + 1
                st.rerun()

    st.markdown("---")
    if st.button("📦 Ekspor Semua Prompt ke Format Teks / Paket Lengkap", use_container_width=True):
        go("export")


def render_export():
    st.title("📦 Ekspor Hasil UGC Remix Studio")
    st.caption("Salin atau unduh seluruh rangkaian prompt dan roadmap video Anda.")

    analysis = st.session_state.get("analysis", {})
    prompts = st.session_state.get("scene_prompts", {})
    total_scenes = scene_count()

    full_report = []
    full_report.append("# UGC REMIX STUDIO v9.2 — ROADMAP & PROMPT REPORT\n")
    full_report.append(f"## Analisis & Mutasi\n{json.dumps(analysis, indent=2)}\n")
    full_report.append("## Daftar Prompt Scene\n")

    for i in range(1, total_scenes + 1):
        p = prompts.get(i, "[Belum digenerate]")
        full_report.append(f"### Scene {i}\n{p}\n")

    report_text = "\n".join(full_report)

    st.text_area("Salin Seluruh Laporan & Prompt:", value=report_text, height=300)
    
    st.download_button(
        label="📥 Download Paket Prompt (.txt)",
        data=report_text,
        file_name="ugc_remix_prompts.txt",
        mime="text/plain",
        type="primary",
        use_container_width=True,
    )

    if st.button("🔄 Kembali ke Halaman Utama"):
        go("home")


# Routing halaman utama Streamlit
page = st.session_state.get("page", "home")
if page == "home":
    render_home()
elif page == "analysis":
    render_analysis()
elif page == "generator":
    render_generator()
elif page == "export":
    render_export()
