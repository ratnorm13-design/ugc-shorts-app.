import json
import re
import time
import os

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="UGC Remix Studio — 3D Parkour Engine", page_icon="🎬", layout="wide")

MODEL_NAME = "gemini-2.5-flash"
APP_VERSION = "5.19 — Bugfree Mobile Edition"

DURATION_SCENES = {
    "8 detik (1 Scene)": 1,
    "16 detik (2 Scene)": 2,
    "24 detik (3 Scene)": 3,
    "32 detik (4 Scene)": 4,
    "40 detik (5 Scene)": 5,
}

STYLE_OPTIONS = [
    "GTA V Modded Gameplay Style",
    "3D Animated Game Graphics",
    "Unreal Engine 5 Parkour Render",
    "Sinematik Realistis 3D",
]
ASPECT_OPTIONS = ["9:16 — Shorts / Reels / TikTok", "16:9 — YouTube Long", "1:1 — Kotak"]

DEFAULTS = {
    "page": "home",
    "api_key": "",
    "reference_file": None,
    "reference_text": "",
    "visual_style": STYLE_OPTIONS[0],
    "aspect_ratio": ASPECT_OPTIONS[0],
    "duration": "16 detik (2 Scene)",
    "custom_instruction": "",
    "analysis": {},
    "storyboard": [],
    "scene_prompts": {},
    "scene_frames": {},
    "current_scene": 1,
    "seo": {},
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def go(page: str):
    st.session_state.page = page
    st.rerun()


def scene_count() -> int:
    return DURATION_SCENES.get(st.session_state.duration, 2)


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

    config_kwargs = {"temperature": 0.3}
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

    target_scenes = scene_count()
    prompt = f"""
Anda adalah AI Creative Director khusus konten viral 3D Game / GTA V Parkour / Obstacle Challenge.

TUGAS UTAMA:
1. Analisis video/skenario referensi.
2. LAKUKAN CREATIVE MUTATION (De-duplication): Ubah karakter utama (Runner), karakter musuh/boss di puncak, atau jenis lintasan rintangan agar hasilnya TIDAK SAMA dengan referensi, tapi tetap memiliki daya tarik viral yang setara.

PENGATURAN:
- Style Visual: {st.session_state.visual_style}
- Ratio: {st.session_state.aspect_ratio}
- Target Durasi: {st.session_state.duration} ({target_scenes} adegan)
- Instruksi Tambahan User: {st.session_state.custom_instruction}

HASILKAN JSON SANGAT RINGKAS DAN PRESISI:
{{
  "original_reference": {{
    "runner_asli": "Karakter utama di referensi",
    "boss_asli": "Karakter di puncak",
    "track_asli": "Jenis rintangan"
  }},
  "remixed_mutation": {{
    "runner_baru": "Karakter baru (misal: Spider-Man, SpongeBob)",
    "boss_baru": "Boss baru (misal: Red Hulk, Giant Minion)",
    "track_baru": "Lintasan baru (misal: Balok Es Licin, Container Kayu)",
    "alasan_remix": "Alasan modifikasi ini viral"
  }},
  "hook_3s": "Deskripsi hook pembuka",
  "spatial_layout": "Third-person view dari belakang runner",
  "temporal_breakdown": [
    {{
      "scene_num": 1,
      "waktu": "00:00-00:08",
      "action": "Aksi utama",
      "end_state": "Kondisi akhir"
    }}
  ]
}}
"""
    with st.spinner("Membedah referensi & mengaplikasikan Creative Mutation Engine..."):
        try:
            raw = ask(client, prompt, parts, json_mode=True)
            data = extract_json(raw)
            st.session_state.analysis = data
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

    prompt = f"""
Write ONE highly detailed, production-ready AI video prompt (for Veo / Kling / Runway / Luma) in ENGLISH for Scene {scene_number} of {scene_count()}.

CONTEXT & REMIXED ASSETS:
- Style: {st.session_state.visual_style}
- Aspect Ratio: 9:16 vertical video
- Main Runner (Protagonist): {mutation.get('runner_baru', 'Superhero')}
- Boss/Target at Top: {mutation.get('boss_baru', 'Giant Character')}
- Environment/Track: {mutation.get('track_baru', 'High obstacle ramp in the sky')}
- Scene Number: {scene_number}

RULES:
1. Camera Angle: Third-person perspective behind the runner, video game gameplay footage style.
2. High detail on 3D textures, vibrant lighting, clear blue sky, smooth parkour movement.
3. Explicitly describe the action of climbing/running and the obstacle ahead.
4. Output ONLY the final raw English prompt string without markdown wrapping or comments.
"""
    with st.spinner(f"Menyusun Prompt AI Video Scene {scene_number}..."):
        try:
            res_prompt = ask(client, prompt, json_mode=False)
            st.session_state.scene_prompts[scene_number] = res_prompt.strip()
            return True
        except Exception as exc:
            st.error(f"Gagal menyusun prompt: {exc}")
            return False


def render_home():
    st.title("🎬 UGC Remix Studio")
    st.caption("Automation Engine untuk Konten 3D Game & GTA V Parkour Challenge.")

    st.subheader("1. Referensi Video / Skenario")
    st.file_uploader("Upload Video Referensi (Shorts/Reels/TikTok)", type=["mp4", "mov", "webm"], key="ref_file_input")

    st.caption("Atau tulis deskripsi referensi manual jika tidak ada video:")
    st.text_area("Deskripsi Referensi Manual", key="reference_text", height=80, placeholder="Contoh: Video GTA V Nobita lari di atas kontainer oranye dikejar Hulk...")

    st.subheader("2. Pengaturan Visual & Durasi")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Gaya Visual", STYLE_OPTIONS, key="visual_style")
        st.selectbox("Rasio Video", ASPECT_OPTIONS, key="aspect_ratio")
    with col2:
        st.selectbox("Durasi Target", list(DURATION_SCENES.keys()), key="duration")
        st.text_area("Instruksi Tambahan (Opsional)", key="custom_instruction", height=80, placeholder="Misal: Pakai karakter SpongeBob sebagai runner...")

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

    st.subheader("💡 Perbandingan Mutasi (Bebas Plagiarisme)")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📌 Asli (Video Referensi)")
        st.write(f"**Runner:** {orig.get('runner_asli', '-')}")
        st.write(f"**Boss Puncak:** {orig.get('boss_asli', '-')}")
        st.write(f"**Lintasan:** {orig.get('track_asli', '-')}")

    with col2:
        st.markdown("### 🚀 Hasil Remix AI (Beda Asset)")
        st.write(f"**Runner Baru:** `{remix.get('runner_baru', '-')}`")
        st.write(f"**Boss Baru:** `{remix.get('boss_baru', '-')}`")
        st.write(f"**Lintasan Baru:** `{remix.get('track_baru', '-')}`")

    st.info(f"**Alasan Strategi Remix:** {remix.get('alasan_remix', '-')}")

    st.subheader("🎬 Alur Konten & Hook")
    st.write(f"**Hook 3 Detik Pertama:** {analysis.get('hook_3s', '-')}")
    st.write(f"**Perspektif Kamera:** {analysis.get('spatial_layout', '-')}")

    if st.button("LANJUT KELOLA PROMPT ADEGAN", type="primary", use_container_width=True):
        go("scenes")


def render_scenes():
    st.title("🎥 AI Video Prompt Generator")
    n = scene_count()
    current = st.session_state.current_scene

    st.write(f"### Adegan {current} dari {n}")

    if current not in st.session_state.scene_prompts:
        if st.button(f"Generate Prompt Scene {current}", type="primary"):
            generate_scene_prompt(current)
            st.rerun()

    if current in st.session_state.scene_prompts:
        st.text_area("Prompt AI Video (Copy-Paste ke Kling / Luma / Runway / Veo):", value=st.session_state.scene_prompts[current], height=140)

        st.subheader("🖼️ Last Frame Bridge (Kontinuitas)")
        st.caption("Upload screenshot frame terakhir dari hasil video adegan ini untuk menjaga konsistensi adegan berikutnya.")
        uploaded_frame = st.file_uploader(f"Upload Last Frame Scene {current}", type=["png", "jpg", "jpeg"], key=f"frame_{current}")
        if uploaded_frame:
            st.session_state.scene_frames[current] = uploaded_frame
            st.success(f"Frame Scene {current} berhasil tersimpan!")

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
    st.title("🚀 SEO & Metadata Shorts / TikTok")
    if st.button("Generate Judul & Hashtag Viral", type="primary"):
        client = get_client()
        if client:
            prompt = f"Buat 3 pilihan judul clickable, deskripsi ringkas, dan 10 hashtag viral untuk YouTube Shorts / TikTok dari data remix ini: {json.dumps(st.session_state.analysis, ensure_ascii=False)}"
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
        if st.button("SEO & Metadata", use_container_width=True): go("seo")

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
