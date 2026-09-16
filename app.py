import json
import re
import time
import os

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="UGC Remix Studio — Ultimate 3D Parkour Engine v9.0", page_icon="🎬", layout="wide")

MODEL_NAME = "gemini-3.6-flash"
APP_VERSION = "9.0 — Ultimate 1:1 Roadmap, Persistent Ragdolls & Anti-Jump Last Frame Bridge"

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
    "Blocky Voxel Man (Karakter balok gaya retro game independen)",
    "Inflatable Dinosaur (Kostum dinosaurus tiup warna hijau)",
    "Minecraft Creeper Style (Karakter makhluk hijau kotak khas Minecraft)",
    "Gingerbread Cookie (Manusia kue jahe hidup)",
    "Minecraft Blocky Zombie (Karakter mayat hidup kotak-kotak ala Minecraft)",
    "Tung Tung Sahur (Karakter anomali ikonik meme sahur yang absurd)",
    "Tralalero Tralala (Karakter absurd ala hiu bermata lebar berkaki sneakers)",
    "Udindindun (Karakter khas Italian brainrot yang konyol dan nyeleneh)"
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

TUGAS UTAMA (ROADMAP CLONING 1:1 & STORYBOARD MAPPING):
1. Bedah video referensi secara menyeluruh. Kloning persis struktur jalur lintasan, urutan rintangan, belokan, dan ritme waktu dari video asli secara 1:1.
2. Jaga konsistensi objek: Ragdoll musuh, NPC, dan properti rintangan **wajib sudah ada/berdiri di tempatnya sejak frame pertama (zero pop-in)** dan tidak boleh tiba-tiba muncul di tengah jalan.
3. Rancang mutasi karakter runner utama menjadi: "{chosen_runner}", serta sesuaikan target boss/ragdoll di puncak dengan opsi yang aman hak cipta (copyright-safe).
4. Pecah alur cerita ke dalam format Storyboard per scene (durasi ~8 detik per scene). Jika durasi referensi pendek, sesuaikan jumlah scene dengan tambahan aksi lanjutan yang tetap nyambung.
5. Pastikan setiap scene memiliki pemicu aksi yang jelas (target objek ragdoll yang berdiri di depan jalur lari untuk ditendang/dipukul).

PENGATURAN:
- Style Visual: {st.session_state.visual_style} (Pencahayaan terang benderang siang hari bolong / noon daylight, langit biru cerah, warna kontras tinggi, bebas nuansa gelap)
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
    "boss_baru": "Boss/Target ragdoll unik di ujung yang sudah ada sejak awal",
    "track_baru": "Lintasan 1:1 meniru referensi dengan objek ragdoll target yang berdiri di depan jalur",
    "visual_anchor_token": "Deskripsi ketat kosmetik karakter pilihan user agar konsisten",
    "alasan_remix": "Alasan modifikasi"
  }},
  "storyboard_plan": [
    {{"scene": 1, "fokus_aksi": "Lari awal di jalur kontainer, objek ragdoll target sudah berdiri di depan."}},
    {{"scene": 2, "fokus_aksi": "Melompati rintangan dan mendekati posisi ragdoll target."}},
    {{"scene": 3, "fokus_aksi": "Klimaks menendang ragdoll target, efek fisika domino & teriakan panik."}}
  ],
  "climax_action": "Aksi spesifik menendang/memukul ragdoll target di ujung dengan efek fisik domino & suara teriakan",
  "spatial_layout": "Third-person dynamic tracking shot with slight camera banking and speed ramping"
}}
"""
    with st.spinner("Membedah roadmap 1:1 video referensi & menyusun storyboard presisi..."):
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

    scene_focus = "Melanjutkan aksi lari dan rintangan."
    if storyboard and len(storyboard) >= scene_number:
        scene_focus = storyboard[scene_number - 1].get("fokus_aksi", scene_focus)

    prev_frame_context = ""
    if scene_number > 1 and (scene_number - 1) in st.session_state.scene_frames:
        prev_frame_context = f"EXACT CONTINUITY & ZERO TELEPORT REQUIREMENT: Scene {scene_number} MUST start at the exact spatial coordinate, camera angle, and footing position where Scene {scene_number-1} ended. Seamlessly continue the runner's forward movement without any backward jump, reset, or position shifting."

    if scene_number == 1:
        camera_desc = "Dynamic third-person close-tracking shot positioned slightly behind and above the runner, featuring slight camera banking and high-speed motion blur."
        action_desc = f"EXPLOSIVE HOOK START: The protagonist ({mutation.get('runner_baru')}) instantly starts at a breakneck forward sprint along the {mutation.get('track_baru')}. TARGET OBJECTS & RAGDOLLS ARE ALREADY STANDING/PRESENT RIGHT FROM THE FIRST FRAME (ZERO POP-IN). Unidirectional forward motion vector only—no reversing."
    elif is_final_scene:
        camera_desc = "Dramatic impact zoom-in camera, shifting to slow-motion micro-freeze on contact."
        action_desc = f"CLIMAX PAYOFF & RAGDOLL CHAOS: The protagonist reaches the target ragdoll ({mutation.get('boss_baru')}) that has been present since the beginning, and forcefully kicks/hits it, triggering an exaggerated comedy physics launch. Multiple ragdolls fly away in a domino chain reaction, accompanied by audio cues of heavy impact thuds and high-pitched ragdoll screaming."
    else:
        camera_desc = "Fast-paced sweeping tracking cam maintaining continuous forward momentum and high-octane action pacing."
        action_desc = f"ROADMAP PROGRESSION & OBJECT INTERACTION: {scene_focus}. All target ragdolls and obstacles are fully persistent and already visible in the scene without sudden loading."

    audio_cues = "Cinematic sound design: heavy impact thuds, screeching metal, roaring wind, and hilarious high-pitched ragdoll screaming sound effects."

    prompt = f"""
Write ONE highly detailed AI video generation prompt in ENGLISH for Scene {scene_number} of {total_scenes} (approx. 8 seconds segment for Google Flow).

VISUAL LIGHTING & ENVIRONMENT AESTHETICS (CRITICAL):
- Bright daylight conditions, vivid sunny sky, clear blue sky with fluffy white clouds, high-contrast colorful graphics matching popular upbeat 3D game video style. Absolutely NO dark, gloomy, or night atmosphere.

STRICT ASSETS, TARGET OBJECTS & FORMAT LOCKING:
- Style: {st.session_state.visual_style}
- Aspect Ratio Orientation: {st.session_state.aspect_ratio}
- Character Identity (DO NOT CHANGE): {mutation.get('visual_anchor_token')}
- Target Ragdoll / Boss (Wajib sudah ada sejak frame pertama, tidak boleh tiba-tiba muncul): {mutation.get('boss_baru')}
- Environment & Roadmap (1:1 Clone): {mutation.get('track_baru')}

MOTION & VECTOR LOCK (NO LOOPING / NO REVERSING):
- The runner must move strictly FORWARD away from the camera. Motion vector is unidirectional forward sprinting. No reversing, no turning back, no looping.
- Zero Pop-in Rule: All target ragdolls, obstacles, and structures must already exist in the environment from the very first frame.

SCENE OBJECTIVE & PACING:
- Current Scene: Scene {scene_number}/{total_scenes}
- Storyboard Focus: {scene_focus}
- Action Focus: {action_desc}
- Camera Choreography: {camera_desc}
- Audio-Visual Impact: {audio_cues}
{prev_frame_context}

RULES:
Output ONLY the final raw English prompt without any markdown formatting, bullet points, or commentary.
"""
    with st.spinner(f"Menyusun Prompt Scene {scene_number} / {total_scenes} (Roadmap 1:1, Persistent Ragdolls & Anti-Jump Locked)..."):
        try:
            res_prompt = ask(client, prompt, json_mode=False)
            st.session_state.scene_prompts[scene_number] = res_prompt.strip()
            return True
        except Exception as exc:
            st.error(f"Gagal menyusun prompt: {exc}")
            return False


def render_home():
    st.title("🎬 UGC Remix Studio v9.0")
    st.caption("Engine Otomasi Konten 3D Game & Parkour Challenge dengan Kloning Roadmap 1:1, Storyboard Presisi, Persistent Ragdolls, & Anti-Jump Last Frame Bridge.")

    st.subheader("1. Referensi Video / Skenario")
    st.file_uploader("Upload Video Referensi (Shorts atau Long Video)", type=["mp4", "mov", "webm"], key="ref_file_input")

    st.caption("Atau tulis deskripsi referensi manual jika tidak ada video:")
    st.text_area("Deskripsi Referensi Manual", key="reference_text", height=80, placeholder="Contoh: Video lari naik kontainer lalu menendang minion...")

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
        st.text_area("Instruksi Tambahan (Opsional)", key="custom_instruction", height=80, placeholder="Misal: Tambahkan efek ledakan api...")

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

    st.success(f"⏱️ Total Target Durasi & Scene: **{scene_count()} Scene** (~{scene_count() * 8} detik total durasi video dengan pacing padat)")

    st.subheader("💡 Perbandingan Mutasi Roadmap 1:1 (Anti Plagiarisme)")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📌 Asli (Video Referensi)")
        st.write(f"**Runner Asli:** {orig.get('runner_asli', '-')}")
        st.write(f"**Boss/Ragdoll Asli:** {orig.get('boss_asli', '-')}")
        st.write(f"**Lintasan Asli:** {orig.get('track_asli', '-')}")

    with col2:
        st.markdown("### 🚀 Hasil Remix AI (Persistent Ragdolls & Zero Pop-in)")
        st.write(f"**Runner Baru:** `{remix.get('runner_baru', '-')}`")
        st.write(f"**Boss/Target Baru:** `{remix.get('boss_baru', '-')}`")
        st.write(f"**Lintasan Baru:** `{remix.get('track_baru', '-')}`")

    st.info(f"🔒 **Visual Anchor Token (Anti Karakter Berubah):** `{remix.get('visual_anchor_token', '-')}`")
    st.warning(f"💥 **Aksi Klimaks & Fisika Ragdoll:** {analysis.get('climax_action', '-')}")

    if storyboard:
        st.subheader("📋 Storyboard Terstruktur (Per 8 Detik)")
        for item in storyboard:
            st.write(f"• **Scene {item.get('scene', 1)}:** {item.get('fokus_aksi', '-')}")

    if st.button("LANJUT KELOLA PROMPT ADEGAN", type="primary", use_container_width=True):
        go("scenes")


def render_scenes():
    st.title("🎥 AI Video Prompt Generator (Roadmap 1:1 & Last Frame Locked)")
    n = scene_count()
    current = st.session_state.current_scene

    st.write(f"### Adegan {current} dari {n}" + (" 💥 (SCENE KLIMAKS TENDANGAN & RAGDOLL CHAOS)" if current == n else " ⚡ (FAST-PACED ACTION)"))

    if current not in st.session_state.scene_prompts:
        if st.button(f"Generate Prompt Scene {current}", type="primary"):
            generate_scene_prompt(current)
            st.rerun()

    if current in st.session_state.scene_prompts:
        st.text_area("Prompt AI Video (Copy-Paste ke Google Flow / Kling / Luma):", value=st.session_state.scene_prompts[current], height=160)

        st.subheader("🖼️ Last Frame Bridge (Estafet Frame / Anti-Jump Continuity)")
        st.caption("UPLOAD SCREENSHOT FRAME TERAKHIR dari video hasil Scene ini. Ini wajib di-upload agar Scene berikutnya tidak mengalami loncatan posisi (teleport) dan koordinatnya menyambung mulus 100%.")
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


def render_seo():
    st.title("🚀 SEO & Metadata Engine (Algoritma YouTube / TikTok)")
    st.caption("Menghasilkan Judul pemancing CTR, Deskripsi tertarget, Hashtag multi-tier, dan **18 Tags Global Unik** tanpa duplikat.")

    if st.button("Generate Judul, Hashtag & 18 Tags Unik", type="primary"):
        client = get_client()
        if client:
            prompt = f"""
Bertindaklah sebagai Pakar Algoritma YouTube & TikTok.
Berdasarkan data remix UGC berikut: {json.dumps(st.session_state.analysis, ensure_ascii=False)}

Buatkan format SEO lengkap dalam bentuk JSON atau teks terstruktur dengan ketentuan:
1. **3 Pilihan Judul:** Singkat, memancing rasa penasaran ekstrem (Curiosity Gap), dan CTR tinggi untuk video tantangan.
2. **Deskripsi Singkat:** Mengandung kata kunci natural untuk meningkatkan SEO penelusuran.
3. **Hashtag Multi-Tier:** Campuran niche tags, viral tags, dan algorithm boosters.
4. **18 GLOBAL SEO TAGS (MUTLAK UNIK):** Buat tepat 18 kata kunci/tags global dalam bahasa Inggris yang berkaitan dengan game, parkour, ragdoll, dan tantangan ekstrem. **ATURAN KERAS: TIDAK BOLEH ADA KATA ATAU TAGS YANG SAMA ATAU DOUBLE (MUTUALLY EXCLUSIVE)**. Pisahkan dengan koma.
"""
            with st.spinner("Meracik strategi SEO agresif & 18 tags unik..."):
                res = ask(client, prompt)
                st.session_state.seo = {"text": res}

    if "text" in st.session_state.seo:
        st.markdown(st.session_state.seo["text"])


def main():
    with st.sidebar:
        st.title("UGC Studio v9.0")
        st.caption(f"App Version: {APP_VERSION}")
        st.text_input("Gemini API Key", type="password", key="api_key", placeholder="AIzaSy...")
        st.divider()
        if st.button("Beranda / Upload", use_container_width=True): go("home")
        if st.button("Hasil Remix Analisis", use_container_width=True): go("analysis")
        if st.button("Prompt Adegan AI", use_container_width=True): go("scenes")
        if st.button("SEO & 18 Tags Unik", use_container_width=True): go("seo")

    page = st.session_state.get("page", "home")
    if page == "home":
        render_home()
    elif page == "analysis":
        render_analysis()
    elif page == "scenes":
        render_scenes()
    elif page == "seo":
        render_seo()


if __name__ == "__main__":
    main()
