import json
import re
import time
import os

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="UGC Remix Studio — Ultimate 3D Parkour Engine", page_icon="🎬", layout="wide")

MODEL_NAME = "gemini-3.6-flash"
APP_VERSION = "7.2 — Bright Daylight & Forward-Locked UGC Engine"

DURATION_SCENES = {
    "Auto (Sesuai Video Referensi & Pacing)": 0,
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

# 10 Pilihan Karakter Runner (Aman Copyright + Italian Brainrot + Minecraft)
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
    "duration": "Auto (Sesuai Video Referensi & Pacing)",
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
Anda adalah AI Growth & Creative Director profesional khusus konten viral 3D Game / Parkour / Obstacle Challenge di TikTok, YouTube Shorts, & Long-Form Video.

TUGAS UTAMA:
1. Analisis video/skenario referensi secara menyeluruh (visual, tempo, rintangan, dan aksi). Hitung jumlah scene optimal dengan standar 8 detik per scene di Google Flow.
2. GUNAKAN KARAKTER PILIHAN USER SEBAGAI RUNNER UTAMA: "{chosen_runner}". Rancang boss/target di puncak dan jenis lintasan rintangan yang cocok dan bebas dari pelanggaran hak cipta (copyright-safe).
3. RANCANG PACING PADAT (HIGH RETENTION): Pastikan tidak ada adegan lari lambat/kosong. Setiap adegan harus penuh aksi cepat (*high-speed momentum*, *rapid obstacle dodging*). Scene terakhir **wajib** berupa aksi klimaks instan (menendang ragdoll, memukul boss, atau menghempaskan musuh berjejer dengan efek fisik memuaskan).
4. TETAPKAN VISUAL ANCHOR TOKEN: Buat deskripsi fisik karakter yang sangat spesifik dan konsisten agar tidak terjadi perubahan bentuk/baju di tengah scene (Visual Drift Protection).

PENGATURAN:
- Style Visual: {st.session_state.visual_style} (Pencahayaan terang benderang siang hari bolong ala game aslinya, langit biru cerah, warna kontras tinggi, bebas dari nuansa gelap/suram)
- Rasio Aspek Video: {st.session_state.aspect_ratio}
- Instruksi Tambahan User: {st.session_state.custom_instruction}

HASILKAN JSON SANGAT RINGKAS DAN PRESISI:
{{
  "video_duration_seconds": 180,
  "calculated_scene_count": {scene_count()},
  "original_reference": {{
    "runner_asli": "Karakter utama di referensi",
    "boss_asli": "Karakter di puncak",
    "track_asli": "Jenis rintangan"
  }},
  "remixed_mutation": {{
    "runner_baru": "{chosen_runner}",
    "boss_baru": "Boss/Target unik di puncak yang aman copyright",
    "track_baru": "Lintasan baru yang ekstrem dengan tambahan variasi rintangan seru",
    "visual_anchor_token": "Deskripsi ketat kosmetik karakter pilihan user agar tidak berubah antar scene",
    "alasan_remix": "Alasan modifikasi"
  }},
  "hook_3s": "Deskripsi hook pembuka yang langsung menggebrak di 3 detik pertama",
  "climax_action": "Aksi spesifik menendang/mengalahkan ragdoll di puncak pada scene akhir dengan efek benturan keras",
  "spatial_layout": "Third-person dynamic view / tracking shot"
}}
"""
    with st.spinner("Membedah video, menghitung durasi optimal & merancang alur pacing padat..."):
        try:
            raw = ask(client, prompt, parts, json_mode=True)
            data = extract_json(raw)
            st.session_state.analysis = data
            
            if DURATION_SCENES.get(st.session_state.duration, 0) == 0:
                calc_scenes = data.get("calculated_scene_count", 4)
                st.session_state.detected_scenes = max(1, min(calc_scenes, 24))
            else:
                st.session_state.detected_scenes = scene_count()
            
            st.session_state.storyboard = []
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
    total_scenes = scene_count()
    is_final_scene = (scene_number == total_scenes)

    prev_frame_context = ""
    if scene_number > 1 and (scene_number - 1) in st.session_state.scene_frames:
        prev_frame_context = f"CONTINUITY REQUIREMENT (NO JUMP): Seamless transition continuing directly from the previous scene's end position (Scene {scene_number-1}). Maintain exact character position, lighting, camera angle, and environment state without jumping."

    if scene_number == 1:
        camera_desc = "Dynamic third-person tracking shot, camera positioned closely behind and slightly above the runner, maintaining forward momentum."
        action_desc = f"FORWARD SPRINT START & VARIETY OBSTACLES: The protagonist ({mutation.get('runner_baru')}) starts instantly at a continuous forward sprint along the {mutation.get('track_baru')}. The character moves ONLY forward, avoiding any backward movement or looping. Dodging colorful rotating barriers, swinging hammers, and jumping over gaps with high energy."
    elif is_final_scene:
        camera_desc = "Impact zoom-in camera, dramatic low-angle framing shifting to dynamic slow-motion on impact."
        action_desc = f"CLIMAX PAYOFF: The protagonist reaches the final platform and forcefully delivers an explosive flying kick/hit to {mutation.get('boss_baru')}, sending multiple ragdolls flying off the ledge into physics chaos."
    else:
        camera_desc = "Fast-paced side-scrolling tracking cam or sweeping high-angle view maintaining continuous forward speed."
        action_desc = f"RAPID ESCALATION & EXTRA OBSTACLES: Continuous forward running, leaping over moving platforms, ducking under rotating blades, maintaining maximum forward speed towards the top."

    audio_cues = "Cinematic sound design: heavy impact thuds, roaring wind, screeching metal, satisfying ragdoll crunch sound effects."

    prompt = f"""
Write ONE highly detailed AI video generation prompt in ENGLISH for Scene {scene_number} of {total_scenes} (approx. 8 seconds segment for Google Flow).

VISUAL LIGHTING & ENVIRONMENT AESTHETICS (CRITICAL):
- Bright daylight conditions, vivid sunny sky, clear blue sky with white fluffy clouds, high-contrast colorful graphics matching popular upbeat 3D game video style. Absolutely NO dark, gloomy, or night atmosphere.

STRICT ASSETS & FORMAT LOCKING:
- Style: {st.session_state.visual_style}
- Aspect Ratio Orientation: {st.session_state.aspect_ratio} (Ensure framing matches this layout strictly)
- Character Identity (DO NOT CHANGE): {mutation.get('visual_anchor_token')}
- Target Boss / Obstacle: {mutation.get('boss_baru')}
- Environment: {mutation.get('track_baru')}

MOTION & VECTOR LOCK (NO LOOPING / NO REVERSING):
- The runner must move strictly FORWARD away from the camera. Motion vector is unidirectional forward sprinting. No reversing, no turning back, no looping.

SCENE OBJECTIVE & PACING:
- Current Scene: Scene {scene_number}/{total_scenes}
- Action Focus: {action_desc}
- Camera Choreography: {camera_desc}
- Audio-Visual Impact: {audio_cues}
{prev_frame_context}

RULES:
Output ONLY the final raw English prompt without any markdown formatting, bullet points, or commentary.
"""
    with st.spinner(f"Menyusun Prompt AI Video Scene {scene_number} / {total_scenes} (Bright Daylight & Forward-Locked)..."):
        try:
            res_prompt = ask(client, prompt, json_mode=False)
            st.session_state.scene_prompts[scene_number] = res_prompt.strip()
            return True
        except Exception as exc:
            st.error(f"Gagal menyusun prompt: {exc}")
            return False


def render_home():
    st.title("🎬 UGC Remix Studio")
    st.caption("Engine Otomasi Konten 3D Game & Parkour Challenge dengan Pacing Padat, 10 Karakter Aman Copyright, & Rasio Aspek Kustom.")

    st.subheader("1. Referensi Video / Skenario")
    st.file_uploader("Upload Video Referensi (Shorts atau Long Video)", type=["mp4", "mov", "webm"], key="ref_file_input")

    st.caption("Atau tulis deskripsi referensi manual jika tidak ada video:")
    st.text_area("Deskripsi Referensi Manual", key="reference_text", height=80, placeholder="Contoh: Video lari rintangan ekstrem...")

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
        st.text_area("Instruksi Tambahan (Opsional)", key="custom_instruction", height=80, placeholder="Misal: Tambahkan jebakan api...")

    if st.button("PROSES & REMIX REFERENSI", type="primary", use_container_width=True):
        run_analysis()


def render_analysis():
    st.title("🔍 Hasil De-duplication & Creative Remix")
    analysis = st.session_state.get("analysis", {})
    if not analysis:
        st.info("Belum ada data analisis. Silakan upload referensi di Beranda.")
        return

    orig = analysis.get("original_reference", {})
    remix = analysis.get("remixed_mutation", {})

    st.success(f"⏱️ Total Target Durasi & Scene: **{scene_count()} Scene** (~{scene_count() * 8} detik total durasi video dengan pacing padat)")

    st.subheader("💡 Perbandingan Mutasi (Bebas Plagiarisme & Copyright)")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📌 Asli (Video Referensi)")
        st.write(f"**Runner Asli:** {orig.get('runner_asli', '-')}")
        st.write(f"**Boss Puncak Asli:** {orig.get('boss_asli', '-')}")
        st.write(f"**Lintasan Asli:** {orig.get('track_asli', '-')}")

    with col2:
        st.markdown("### 🚀 Hasil Remix AI (Anti-Drift)")
        st.write(f"**Runner Baru:** `{remix.get('runner_baru', '-')}`")
        st.write(f"**Boss Baru:** `{remix.get('boss_baru', '-')}`")
        st.write(f"**Lintasan Baru:** `{remix.get('track_baru', '-')}`")

    st.info(f"🔒 **Visual Anchor Token (Anti Karakter Berubah):** `{remix.get('visual_anchor_token', '-')}`")
    st.warning(f"💥 **Aksi Klimaks Puncak:** {analysis.get('climax_action', '-')}")

    if st.button("LANJUT KELOLA PROMPT ADEGAN", type="primary", use_container_width=True):
        go("scenes")


def render_scenes():
    st.title("🎥 AI Video Prompt Generator (Dense Pacing & Aspect Locked)")
    n = scene_count()
    current = st.session_state.current_scene

    st.write(f"### Adegan {current} dari {n}" + (" 💥 (SCENE KLIMAKS TENDANGAN/RAGDOLL)" if current == n else " ⚡ (FAST-PACED ACTION)"))

    if current not in st.session_state.scene_prompts:
        if st.button(f"Generate Prompt Scene {current}", type="primary"):
            generate_scene_prompt(current)
            st.rerun()

    if current in st.session_state.scene_prompts:
        st.text_area("Prompt AI Video (Copy-Paste ke Google Flow / Kling / Luma):", value=st.session_state.scene_prompts[current], height=160)

        st.subheader("🖼️ Last Frame Bridge (Estafet Frame / Anti-Jump Continuity)")
        st.caption("Upload frame terakhir dari hasil video Scene ini ke Google Flow untuk mengunci posisi koordinat agar scene berikutnya nyambung mulus tanpa patah.")
        uploaded_frame = st.file_uploader(f"Upload Last Frame Scene {current}", type=["png", "jpg", "jpeg"], key=f"frame_{current}")
        if uploaded_frame:
            st.session_state.scene_frames[current] = uploaded_frame
            st.success(f"Frame Scene {current} tersimpan! Prompt Scene {current+1} akan disesuaikan dengan posisi akhir ini.")

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
        st.title("UGC Studio")
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
