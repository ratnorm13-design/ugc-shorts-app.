# -*- coding: utf-8 -*-
import json
import re
import time
import os

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="UGC Remix Studio — Ultimate 3D Parkour Engine v9.3", page_icon="🎬", layout="wide")

MODEL_NAME = "gemini-2.5-flash"
APP_VERSION = "9.3 — Ultimate 1:1 Roadmap, Permanent Multi-Container Entities, Multi-Action & SEO Suite"

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
    
    config_kwargs = {"temperature": 0.4}
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=content_parts,
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
    
    chosen_runner = st.session_state.runner_choice
    if chosen_runner == "Custom / Ketik Sendiri":
        chosen_runner = st.session_state.custom_runner or "Unique funny custom character"

    prompt = f"""
Anda adalah AI Master Creative Director khusus konten viral 3D Game / Parkour / Obstacle Challenge di TikTok & YouTube Shorts.

TUGAS UTAMA:
1. Bedah referensi secara menyeluruh dan buat roadmap kloning 1:1.
2. Rancang mutasi karakter runner utama menjadi: "{chosen_runner}".
3. Buat paket SEO viral (judul, deskripsi menarik, dan hashtag populer).

PENGATURAN:
- Style Visual: {st.session_state.visual_style}
- Rasio Aspek: {st.session_state.aspect_ratio}
- Instruksi User: {st.session_state.custom_instruction}

HASILKAN JSON PRESISI:
{{
  "video_duration_seconds": 24,
  "calculated_scene_count": {scene_count()},
  "original_reference": {{
    "runner_asli": "Karakter utama di referensi",
    "boss_asli": "Target ragdoll di ujung",
    "track_asli": "Jalur di referensi"
  }},
  "remixed_mutation": {{
    "runner_baru": "{chosen_runner}",
    "boss_baru": "Deretan boneka/target ragdoll unik",
    "track_baru": "Lintasan kontainer 1:1",
    "visual_anchor_token": "Deskripsi ketat kosmetik karakter",
    "alasan_remix": "Alasan modifikasi"
  }},
  "storyboard_plan": [
    {{"scene": 1, "fokus_aksi": "Runner berlari dan menendang rintangan pertama."}},
    {{"scene": 2, "fokus_aksi": "Melanjutkan rintangan berikutnya."}},
    {{"scene": 3, "fokus_aksi": "Klimaks aksi penutupan dan ragdoll physics."}}
  ],
  "seo_package": {{
    "judul_viral": "Judul video yang bikin penasaran dan klik tinggi",
    "deskripsi": "Deskripsi singkat penjelas video untuk TikTok/YouTube",
    "hashtag": ["#parkour", "#gaming", "#viral", "#foryou", "#ugc"]
  }}
}}
"""
    with st.spinner("Membedah roadmap & menyusun paket SEO viral..."):
        try:
            raw = ask(client, prompt, parts, json_mode=True)
            data = extract_json(raw)
            st.session_state.analysis = data
            st.session_state.storyboard = data.get("storyboard_plan", [])
            st.session_state.seo = data.get("seo_package", {})
            
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

    analysis = st.session_state.get("analysis", {})
    mutation = analysis.get("remixed_mutation", {})
    storyboard = analysis.get("storyboard_plan", [])
    total_scenes = scene_count()
    is_final_scene = (scene_number == total_scenes)

    scene_focus = "Melanjutkan aksi lari dan rintangan."
    if storyboard and len(storyboard) >= scene_number:
        scene_focus = storyboard[scene_number - 1].get("fokus_aksi", scene_focus)

    if scene_number == 1:
        camera_desc = "Dynamic third-person trailing camera locked tightly behind the runner."
    elif is_final_scene:
        camera_desc = "Dramatic close-up tracking zoom in cinematic slow-motion."
    else:
        camera_desc = "High-octane sweeping third-person tracking shot."

    prompt = f"""
Write ONE ultra-detailed AI video generation prompt in ENGLISH for Scene {scene_number} of {total_scenes} (approx. 8 seconds segment).

ENVIRONMENT & AESTHETICS:
- Bright daytime lighting, vivid sunny sky, clear blue atmosphere, high-contrast colorful 3D game aesthetics.

ASSETS & PERMANENT ENTITIES LOCK:
- Style: {st.session_state.visual_style}
- Aspect Ratio: {st.session_state.aspect_ratio}
- Runner Character: {mutation.get('visual_anchor_token', st.session_state.runner_choice)}
- Target Entities: {mutation.get('boss_baru', 'Active target dolls')}
- Environment Path: {mutation.get('track_baru', 'Container path')}

PHYSICS & MULTI-ACTION LAWS:
- Focus action: {scene_focus}
- Surface confinement: Runner stays strictly on container roofs.
- Camera: {camera_desc}

RULES:
Output ONLY the final raw English prompt without any markdown formatting or extra text.
"""
    with st.spinner(f"Menyusun Prompt Scene {scene_number}..."):
        try:
            res_prompt = ask(client, prompt, json_mode=False)
            st.session_state.scene_prompts[scene_number] = res_prompt.strip()
            return True
        except Exception as exc:
            st.error(f"Gagal menyusun prompt: {exc}")
            return False
with st.sidebar:
    st.title("Konfigurasi Sistem")
    st.session_state.api_key = st.text_input("Gemini API Key", value=st.session_state.api_key, type="password", placeholder="AIzaSy...")
    st.markdown("---")
    st.info("Panduan Cepat:\n1. Masukkan API Key di atas.\n2. Upload video / isi deskripsi.\n3. Pilih karakter runner.\n4. Klik Proses Remix.")
    st.markdown(f"**Versi:** {APP_VERSION}")


def render_home():
    st.title("UGC Remix Studio v9.3")
    st.caption("Engine Otomasi Konten 3D Game & Parkour Challenge dengan Paket SEO Lengkap.")

    st.subheader("1. Referensi Video / Skenario")
    st.file_uploader("Upload Video Referensi", type=["mp4", "mov", "webm"], key="ref_file_input")
    st.text_area("Deskripsi Referensi Manual (Opsional)", key="reference_text", height=80, placeholder="Contoh: Video lari menendang dua boneka...")

    st.subheader("2. Pilihan Karakter Runner Utama")
    st.selectbox("Pilih Preset Karakter Runner:", RUNNER_PRESETS, key="runner_choice")
    if st.session_state.runner_choice == "Custom / Ketik Sendiri":
        st.text_input("Tulis Deskripsi Karakter Bebas Kamu:", key="custom_runner", placeholder="Misal: Karakter anomali unik...")

    st.subheader("3. Pengaturan Visual, Rasio & Durasi")
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
    st.title("Hasil Bedah Roadmap & Paket SEO Viral")
    st.caption("Roadmap struktur jalur, objek permanen, dan paket optimasi media sosial.")

    analysis = st.session_state.get("analysis", {})
    if not analysis:
        st.warning("Belum ada data analisis. Silakan kembali ke Beranda.")
        if st.button("Kembali ke Beranda"):
            go("home")
        return

    mut = analysis.get("remixed_mutation", {})
    ref = analysis.get("original_reference", {})
    seo = analysis.get("seo_package", st.session_state.get("seo", {}))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Referensi Asli")
        st.markdown(f"- **Runner Asli:** {ref.get('runner_asli', '-')}")
        st.markdown(f"- **Boss/Target Asli:** {ref.get('boss_asli', '-')}")
        st.markdown(f"- **Track Asli:** {ref.get('track_asli', '-')}")
    with c2:
        st.markdown("### Hasil Remix & Mutasi 1:1")
        st.markdown(f"- **Runner Baru:** {mut.get('runner_baru', '-')}")
        st.markdown(f"- **Target Boneka Permanen:** {mut.get('boss_baru', '-')}")
        st.markdown(f"- **Track Kontainer:** {mut.get('track_baru', '-')}")

    st.info(f"Alasan Remix: {mut.get('alasan_remix', '-')}")

    st.markdown("---")
    st.subheader("📊 Paket SEO & Judul Viral Otomatis")
    st.text_input("Judul Video Viral:", value=seo.get("judul_viral", ""), key="seo_title_box")
    st.text_area("Deskripsi Video:", value=seo.get("deskripsi", ""), height=80, key="seo_desc_box")
    hashtags = seo.get("hashtag", [])
    st.text_input("Hashtag Populer:", value=" ".join(hashtags) if isinstance(hashtags, list) else str(hashtags), key="seo_tags_box")

    st.markdown("---")
    st.markdown("### Storyboard & Rencana Aksi per Scene")
    storyboard = st.session_state.get("storyboard", [])
    for idx, item in enumerate(storyboard):
        s_num = item.get("scene", idx + 1)
        fokus = item.get("fokus_aksi", "Aksi lari dan rintangan.")
        st.markdown(f"**Scene {s_num}:** {fokus}")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Ulangi Pengaturan (Home)", use_container_width=True):
            go("home")
    with col_btn2:
        if st.button("Lanjut ke Generator Prompt Scene", type="primary", use_container_width=True):
            go("generator")


def render_generator():
    st.title("Multi-Scene & Multi-Action Prompt Generator")
    st.caption("Generate prompt video berkualitas tinggi untuk setiap scene.")

    total_scenes = scene_count()
    current = st.session_state.get("current_scene", 1)

    cols = st.columns(min(total_scenes, 8))
    for i in range(1, total_scenes + 1):
        with cols[(i - 1) % 8]:
            btn_type = "primary" if current == i else "secondary"
            if st.button(f"Scene {i}", key=f"btn_scene_{i}", type=btn_type, use_container_width=True):
                st.session_state.current_scene = i
                st.rerun()

    st.markdown("---")
    st.subheader(f"Pengaturan Scene {current} dari {total_scenes}")

    if st.button(f"Generate Prompt Scene {current}", type="primary", key=f"gen_btn_{current}"):
        success = generate_scene_prompt(current)
        if success:
            st.success(f"Prompt Scene {current} berhasil dibuat!")
            st.rerun()

    prompts_dict = st.session_state.setdefault("scene_prompts", {})
    current_prompt = prompts_dict.get(current, "")

    edited_prompt = st.text_area(
        f"Prompt Video untuk Scene {current} (Bisa diedit manual):",
        value=current_prompt,
        height=150,
        key=f"prompt_box_{current}",
    )
    
    if edited_prompt != current_prompt:
        prompts_dict[current] = edited_prompt

    st.markdown("---")
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if current > 1:
            if st.button("Scene Sebelumnya"):
                st.session_state.current_scene = current - 1
                st.rerun()
    with col_nav2:
        if current < total_scenes:
            if st.button("Scene Berikutnya"):
                st.session_state.current_scene = current + 1
                st.rerun()

    st.markdown("---")
    if st.button("Ekspor Semua Prompt ke Paket Teks", use_container_width=True):
        go("export")


def render_export():
    st.title("Ekspor Hasil UGC Remix Studio")
    st.caption("Salin atau unduh seluruh rangkaian prompt, roadmap, dan paket SEO video Anda.")

    analysis = st.session_state.get("analysis", {})
    prompts = st.session_state.get("scene_prompts", {})
    seo = st.session_state.get("seo", {})
    total_scenes = scene_count()

    full_report = [
        "# UGC REMIX STUDIO v9.3 — ROADMAP, SEO & PROMPT REPORT\n",
        f"## Paket SEO Viral\n- Judul: {seo.get('judul_viral', '-')}\n- Deskripsi: {seo.get('deskripsi', '-')}\n- Hashtag: {' '.join(seo.get('hashtag', []))}\n",
        f"\n## Analisis & Mutasi\n{json.dumps(analysis, indent=2)}\n",
        "\n## Daftar Prompt Scene\n"
    ]

    for i in range(1, total_scenes + 1):
        p = prompts.get(i, "[Belum digenerate]")
        full_report.append(f"### Scene {i}\n{p}\n")

    report_text = "\n".join(full_report)

    st.text_area("Salin Seluruh Laporan & Paket SEO:", value=report_text, height=300)
    
    st.download_button(
        label="Download Paket Prompt & SEO (.txt)",
        data=report_text,
        file_name="ugc_remix_prompts_and_seo.txt",
        mime="text/plain",
        type="primary",
        use_container_width=True,
    )

    if st.button("Kembali ke Halaman Utama"):
        go("home")


page = st.session_state.get("page", "home")
if page == "home":
    render_home()
elif page == "analysis":
    render_analysis()
elif page == "generator":
    render_generator()
elif page == "export":
    render_export()
