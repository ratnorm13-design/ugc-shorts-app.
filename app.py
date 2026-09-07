import json
import re
import time
from typing import Any

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="UGC Remix Studio", page_icon="🎬", layout="wide")

MODEL_NAME = "gemini-3.6-flash"

DURATION_SCENES = {
    "8 detik": 1, "16 detik": 2, "24 detik": 3, "32 detik": 4,
    "40 detik": 5, "48 detik": 6, "56 detik": 7, "1 menit": 8,
    "1,5 menit": 12, "2 menit": 15, "2,5 menit": 19, "3 menit": 23,
}

STYLE_OPTIONS = [
    "Sinematik realistis", "Animasi 3D", "Animasi 2D", "Komedi bergaya",
    "Lucu dan ramah keluarga", "Dokumenter realistis", "Aksi sinematik", "Kustom",
]
ASPECT_OPTIONS = ["9:16 — Shorts", "16:9 — YouTube", "1:1 — Kotak"]
REFERENCE_OPTIONS = ["Video", "Screenshot", "Teks / ide"]

# ============================================================
# TALE OF PAW — FIXED CHARACTER LOCK
# Karakter ini adalah identitas permanen channel. AI tidak boleh
# mengganti, mendesain ulang, atau memilih karakter baru.
# ============================================================
CHARACTER_LOCK = {
    "nama": "Milo",
    "spesies": "anak kucing / kitten domestik kecil",
    "identitas_visual": (
        "kitten kecil dengan bulu putih krem, sedikit abu-abu muda pada telinga "
        "dan punggung, mata besar bulat dan ekspresif, wajah innocent dan penasaran, "
        "proporsi tubuh kitten realistis, ukuran tubuh kecil dan konsisten"
    ),
    "ciri_khas": (
        "pola bulu, struktur wajah, warna mata, bentuk telinga, ukuran tubuh, "
        "dan proporsi tetap sama di setiap adegan dan setiap episode"
    ),
    "aturan_konsistensi": (
        "Milo selalu merupakan kitten yang sama. Jangan mengganti spesies, ras, "
        "warna/pola bulu utama, struktur wajah, warna mata, ukuran relatif, usia visual, "
        "atau proporsi tubuh. Jangan membuat karakter baru sebagai pengganti Milo. "
        "Hanya pakaian/aksesori yang memang dibutuhkan cerita, properti aman, setting, "
        "kamera, lighting, dan detail produksi yang boleh berubah."
    ),
}

CHARACTER_LOCK_EN = """Milo is the permanent main character of Tale Of Paw. He is always the exact same young domestic kitten: small realistic kitten proportions, creamy white fur with subtle light-gray fur on the ears and back, large round expressive eyes, innocent curious face, and consistent facial structure, fur pattern, eye color, ear shape, body size, age appearance, and proportions. Never redesign, replace, age up, morph, or change Milo's identity. Only scene-specific safe clothing/accessories, props, environment, camera, lighting, and production details may change."""

DEFAULTS = {
    "page": "home", "api_key": "", "reference_type": "Video",
    "reference_file": None, "reference_files": [], "reference_text": "",
    "visual_style": STYLE_OPTIONS[0], "aspect_ratio": ASPECT_OPTIONS[0],
    "duration": "8 detik", "custom_instruction": "",
    "analysis": {}, "character": CHARACTER_LOCK.copy(), "storyboard": [], "scene_prompts": {},
    "scene_frames": {}, "current_scene": 1, "storyboard_duration": None, "seo": {},
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def reset_project():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


def go(page):
    st.session_state.page = page
    st.rerun()


def scene_count():
    return DURATION_SCENES[st.session_state.duration]


def safe_text(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def get_client():
    key = st.session_state.api_key.strip()
    if not key:
        st.error("Masukkan Gemini API Key terlebih dahulu.")
        return None
    try:
        return genai.Client(api_key=key)
    except Exception as e:
        st.error(f"Gagal membuat koneksi Gemini: {e}")
        return None


def extract_json(text: str) -> Any:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass
    starts = [x for x in (text.find("{"), text.find("[")) if x >= 0]
    if not starts:
        raise ValueError("Respons AI tidak berisi JSON yang valid.")
    start = min(starts)
    for end in range(len(text), start, -1):
        try:
            return json.loads(text[start:end].strip())
        except Exception:
            continue
    raise ValueError("Respons AI tidak bisa dibaca sebagai JSON.")


def ask(client, prompt, parts=None):
    contents = [prompt] + (parts or [])
    last_error = None
    for attempt in range(3):
        try:
            r = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(temperature=0.7),
            )
            return r.text or ""
        except Exception as e:
            last_error = e
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                time.sleep(3 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"Gemini sedang sibuk setelah 3 percobaan. Coba lagi sebentar. Error: {last_error}")


def upload_to_gemini(client, uploaded_file):
    if uploaded_file is None:
        return None
    try:
        config = {"display_name": uploaded_file.name}
        if getattr(uploaded_file, "type", None):
            config["mime_type"] = uploaded_file.type
        return client.files.upload(file=uploaded_file, config=config)
    except Exception as e:
        st.warning(f"File gagal dikirim ke Gemini: {e}")
        return None


def file_parts(client, uploaded_file):
    remote = upload_to_gemini(client, uploaded_file)
    return [remote] if remote else []


def reference_parts(client):
    rt = st.session_state.reference_type
    if rt == "Video" and st.session_state.reference_file:
        return file_parts(client, st.session_state.reference_file)
    if rt == "Screenshot":
        out = []
        for f in st.session_state.reference_files:
            out.extend(file_parts(client, f))
        return out
    if rt == "Teks / ide" and st.session_state.reference_text.strip():
        return [f"REFERENSI TEKS PENGGUNA:\n{st.session_state.reference_text}"]
    return []


# Sidebar
with st.sidebar:
    st.title("UGC Remix Studio")
    st.caption("Referensi → Analisis → Storyboard → Flow/Veo")
    st.text_input("Gemini API Key", type="password", key="api_key", placeholder="AIza...")
    st.divider()
    if st.button("Beranda", use_container_width=True): go("home")
    if st.button("Analisis Referensi", use_container_width=True): go("analysis")
    if st.button("Storyboard", use_container_width=True): go("storyboard")
    if st.button("Prompt Adegan", use_container_width=True): go("scenes")
    if st.button("SEO YouTube", use_container_width=True): go("seo")
    st.divider()
    if st.button("Proyek Baru", use_container_width=True):
        reset_project(); st.rerun()


def render_home():
    st.title("UGC Remix Studio")
    st.write("Mesin referensi untuk mengubah video acuan menjadi storyboard dan prompt Flow/Veo dengan alur kejadian yang tetap konsisten.")

    st.subheader("1. Referensi")
    st.radio("Jenis referensi", REFERENCE_OPTIONS, horizontal=True, key="reference_type")
    rt = st.session_state.reference_type
    if rt == "Video":
        st.session_state.reference_file = st.file_uploader("Upload video referensi", type=["mp4", "mov", "webm", "avi", "mkv"])
        st.session_state.reference_files = []
    elif rt == "Screenshot":
        st.session_state.reference_files = st.file_uploader("Upload screenshot referensi", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
        st.session_state.reference_file = None
    else:
        st.session_state.reference_text = st.text_area("Tulis referensi atau ide", value=st.session_state.reference_text, height=160)
        st.session_state.reference_file = None
        st.session_state.reference_files = []

    st.subheader("2. Pengaturan Video")
    c1, c2 = st.columns(2)
    with c1:
        st.selectbox("Gaya visual", STYLE_OPTIONS, key="visual_style")
        st.selectbox("Rasio video", ASPECT_OPTIONS, key="aspect_ratio")
    with c2:
        st.selectbox("Durasi video", list(DURATION_SCENES.keys()), key="duration")
        st.text_area("Instruksi tambahan", key="custom_instruction", height=100, placeholder="Contoh: ending lebih lucu, tetap family-friendly.")

    n = scene_count()
    st.info(f"Durasi {st.session_state.duration} = tepat {n} adegan. Setiap adegan sekitar 8 detik.")

    st.subheader("3. Aturan Produksi")
    st.write("Tidak ada remix dan tidak ada 3 konsep. Sistem langsung menganalisis referensi dan mempertahankan urutan kejadian, hook, sebab-akibat, tujuan emosi, payoff, dan logika tempo.")
    st.info("Referensi boleh berasal dari video viral yang kamu temukan di platform sosial mana pun. Aplikasi ini hanya menganalisis file yang kamu upload; sumber referensi tidak mengubah Character Lock Tale Of Paw.")
    st.write("Karakter utama dikunci agar identitasnya konsisten di semua adegan. Untuk konten ini, subjek utama diprioritaskan sebagai anak kucing/kitten dan tidak diganti menjadi karakter lain.")
    st.write("Perbedaan hanya boleh berada pada detail produksi yang dipilih pengguna: penampilan, properti, setting, detail aksi yang tidak mengubah inti kejadian, kamera, pencahayaan, desain visual, dialog, dan suara.")

    if st.button("ANALISIS REFERENSI", type="primary", use_container_width=True):
        run_analysis()


def run_analysis():
    client = get_client()
    if not client: return
    parts = reference_parts(client)
    if not parts:
        st.warning("Masukkan atau upload referensi terlebih dahulu.")
        return
    prompt = f"""
Anda adalah pengarah kreatif untuk sistem produksi video anak yang aman.
Analisis referensi yang diberikan. JANGAN membuat remix dan JANGAN membuat beberapa konsep.
Hasil harus langsung menjadi dasar storyboard video.

ATURAN UTAMA:
1. Pertahankan urutan kejadian dan inti execution referensi sedekat mungkin: hook, sebab-akibat, tujuan emosi, payoff, dan pacing logic harus tetap.
2. Jangan mengubah karakter utama menjadi manusia, robot, atau hewan lain. Untuk proyek ini karakter utama WAJIB anak kucing/kitten.
3. GUNAKAN IDENTITAS KARAKTER TERKUNCI TALE OF PAW di bawah. Jangan memilih atau mendesain karakter baru. Identitas ini wajib dipakai persis di semua adegan.
4. Detail produksi boleh disesuaikan tanpa mengubah inti kejadian: penampilan, properti, setting, detail aksi kecil, kamera, lighting, visual design, dialog, dan sound design.
5. Jangan menambahkan karakter utama baru secara acak.
6. Properti biasa yang tidak berbahaya boleh dipertahankan secara visual. Jika referensi memuat senjata atau mekanisme berbahaya, pertahankan hanya beat aksi sinematik yang tidak operasional dan jangan memberi detail penggunaan; elemen berbahaya harus ditampilkan secara aman/tidak berfungsi.
7. Semua nilai teks WAJIB Bahasa Indonesia.

IDENTITAS KARAKTER TERKUNCI TALE OF PAW:
{json.dumps(CHARACTER_LOCK, ensure_ascii=False, indent=2)}

PENGATURAN:
Gaya visual: {st.session_state.visual_style}
Rasio: {st.session_state.aspect_ratio}
Durasi: {st.session_state.duration}
Jumlah adegan: {scene_count()}
Instruksi pengguna: {st.session_state.custom_instruction}

Kembalikan HANYA JSON valid dengan struktur:
{{
  "ringkasan": "...",
  "niche": "...",
  "hook": "...",
  "sebab_akibat": "...",
  "tujuan_emosi": "...",
  "pacing_logic": "...",
  "payoff": "...",
  "urutan_kejadian": ["kejadian 1", "kejadian 2"],
  "karakter_utama": {{
    "nama": "...",
    "spesies": "anak kucing/kitten",
    "identitas_visual": "...",
    "ciri_khas": "...",
    "aturan_konsistensi": "..."
  }},
  "detail_produksi": {{
    "penampilan": "...",
    "properti": "...",
    "setting": "...",
    "kamera": "...",
    "lighting": "...",
    "visual_design": "...",
    "dialog": "...",
    "sound_design": "..."
  }}
}}
"""
    with st.spinner("Menganalisis referensi..."):
        try:
            data = extract_json(ask(client, prompt, parts))
            char = CHARACTER_LOCK.copy()
            data["karakter_utama"] = char
            st.session_state.analysis = data
            st.session_state.character = char
            st.session_state.storyboard = []
            st.session_state.scene_prompts = {}
            st.session_state.storyboard_duration = None
            st.session_state.scene_frames = {}
            st.session_state.current_scene = 1
            go("analysis")
        except Exception as e:
            st.error(f"Analisis gagal: {e}")


def render_analysis():
    st.title("Analisis Referensi")
    a = st.session_state.analysis
    if not a:
        st.info("Belum ada analisis. Kembali ke Beranda dan analisis referensi.")
        return
    st.subheader("Alur yang Dikunci")
    for label, key in [("Niche", "niche"), ("Hook", "hook"), ("Sebab-akibat", "sebab_akibat"), ("Tujuan emosi", "tujuan_emosi"), ("Pacing logic", "pacing_logic"), ("Payoff", "payoff")]:
        st.write(f"**{label}:** {safe_text(a.get(key))}")
    st.write("**Urutan kejadian:**")
    for i, item in enumerate(a.get("urutan_kejadian", []), 1): st.write(f"{i}. {item}")

    st.subheader("Identitas Karakter Utama — Dikunci")
    c = st.session_state.character
    st.write(f"**Nama:** {safe_text(c.get('nama'))}")
    st.write(f"**Spesies:** {safe_text(c.get('spesies'))}")
    st.write(f"**Identitas visual:** {safe_text(c.get('identitas_visual'))}")
    st.write(f"**Ciri khas:** {safe_text(c.get('ciri_khas'))}")
    st.warning("Identitas ini akan dimasukkan ke setiap prompt agar kitten tetap terlihat sebagai karakter yang sama.")

    st.subheader("Detail Produksi")
    dp = a.get("detail_produksi", {})
    for label, key in [("Penampilan", "penampilan"), ("Properti", "properti"), ("Setting", "setting"), ("Kamera", "kamera"), ("Lighting", "lighting"), ("Desain visual", "visual_design"), ("Dialog", "dialog"), ("Sound design", "sound_design")]:
        st.write(f"**{label}:** {safe_text(dp.get(key))}")
    if st.button("BUAT STORYBOARD", type="primary", use_container_width=True): run_storyboard()


def run_storyboard():
    client = get_client()
    if not client: return
    n = scene_count(); a = st.session_state.analysis; c = st.session_state.character
    prompt = f"""
Buat storyboard berdasarkan analisis referensi berikut. JANGAN membuat remix.

WAJIB tepat {n} adegan, nomor 1 sampai {n}, sekitar 8 detik per adegan.
Semua nilai teks Bahasa Indonesia.

Pertahankan urutan kejadian inti dari referensi: hook, sebab-akibat, tujuan emosi, payoff, dan pacing logic.
Karakter utama HARUS identik secara deskripsi di semua adegan dan selalu berupa kitten yang sama.
Jangan mengganti spesies atau identitas karakter.
Jangan menambahkan kejadian baru yang mengubah alur.
Akhir setiap adegan harus menjelaskan posisi/keadaan kitten dan properti untuk kesinambungan adegan berikutnya.

IDENTITAS KARAKTER TERKUNCI TALE OF PAW:
{json.dumps(c, ensure_ascii=False, indent=2)}

CHARACTER LOCK IN ENGLISH:
{CHARACTER_LOCK_EN}

ANALISIS:
{json.dumps(a, ensure_ascii=False, indent=2)}

Pengaturan: {st.session_state.duration}, {st.session_state.aspect_ratio}, {st.session_state.visual_style}

Kembalikan HANYA JSON:
{{"adegan": [{{"nomor": 1, "waktu": "00:00-00:08", "tujuan": "...", "visual": "...", "aksi": "...", "kamera": "...", "kontinuitas": "...", "audio": "...", "transisi": "..."}}]}}
"""
    with st.spinner(f"Membuat {n} adegan..."):
        try:
            data = extract_json(ask(client, prompt))
            scenes = data.get("adegan", [])
            if len(scenes) != n: raise ValueError(f"Harus tepat {n} adegan, AI menghasilkan {len(scenes)}.")
            for i, s in enumerate(scenes, 1):
                s["nomor"] = i
                s.setdefault("waktu", f"{(i-1)*8:02d}-{i*8:02d}")
            st.session_state.storyboard = scenes
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}
            st.session_state.current_scene = 1
            st.session_state.storyboard_duration = st.session_state.duration
            go("storyboard")
        except Exception as e: st.error(f"Storyboard gagal dibuat: {e}")


def render_storyboard():
    st.title("Storyboard")
    scenes = st.session_state.storyboard
    if not scenes:
        st.info("Storyboard belum dibuat.")
        return
    st.info(f"Durasi {st.session_state.duration} = {len(scenes)} adegan")
    for s in scenes:
        with st.expander(f"Adegan {s['nomor']} — {s.get('waktu','')}"):
            for label, key in [("Tujuan", "tujuan"), ("Visual", "visual"), ("Aksi", "aksi"), ("Kamera", "kamera"), ("Kontinuitas", "kontinuitas"), ("Audio", "audio"), ("Transisi", "transisi")]:
                st.write(f"**{label}:**", s.get(key, ""))
    if st.button("LANJUT KE PROMPT ADEGAN", type="primary", use_container_width=True): go("scenes")


def previous_scene(scene_number):
    if scene_number <= 1: return "Tidak ada adegan sebelumnya."
    return json.dumps(st.session_state.storyboard[scene_number-2], ensure_ascii=False, indent=2)


def generate_scene_prompt(scene_number):
    client = get_client()
    if not client: return False
    scene = st.session_state.storyboard[scene_number-1]
    char = st.session_state.character
    prev_frame = st.session_state.scene_frames.get(scene_number-1)
    prompt = f"""
Write ONE production-ready Google Flow / Veo prompt in ENGLISH for Scene {scene_number}.
This English prompt is the ONLY English output allowed in this workflow.

CRITICAL STORY RULES:
- Follow the reference-derived storyboard exactly for the core event sequence and comedic/emotional timing.
- Do NOT remix, invent a different concept, or change the main character.
- The main character is the SAME kitten in every scene. Repeat the full character identity below whenever relevant.
- Preserve hook, cause/effect, emotional goal, payoff, pacing, and the core action beat.
- Only vary permitted production details without changing the core event: appearance details, props, setting details, camera, lighting, visual design, dialogue wording, and sound design.
- Ordinary non-hazardous props from the reference may remain visually faithful. If a dangerous weapon or hazardous mechanism appears, preserve only the non-actionable cinematic story beat and avoid operational, realistic use details; depict the hazardous element in a clearly non-functional or otherwise safe way.

LOCKED CHARACTER IDENTITY — TALE OF PAW:
{CHARACTER_LOCK_EN}

LOCKED CHARACTER DATA:
{json.dumps(char, ensure_ascii=False, indent=2)}

CURRENT SCENE:
{json.dumps(scene, ensure_ascii=False, indent=2)}

PREVIOUS SCENE:
{previous_scene(scene_number)}

Project style: {st.session_state.visual_style}
Aspect ratio: {st.session_state.aspect_ratio}
Total duration: {st.session_state.duration}

If a previous last-frame image is supplied, use it only for continuity of the same kitten, pose/state, props, environment, lighting direction, and camera geography.

Write one detailed paragraph only. Include the kitten's exact appearance, environment, core action, performance, camera, lens/depth of field, lighting, motion, sound, optional dialogue, and a clean ending that matches the next scene.
"""
    parts = file_parts(client, prev_frame) if prev_frame else []
    with st.spinner(f"Membuat prompt Adegan {scene_number}..."):
        try:
            result = ask(client, prompt, parts).strip()
            if not result: raise ValueError("Prompt kosong.")
            st.session_state.scene_prompts[scene_number] = result
            return True
        except Exception as e:
            st.error(f"Prompt adegan gagal: {e}")
            return False


def render_scenes():
    st.title("Prompt Adegan untuk Flow/Veo")
    scenes = st.session_state.storyboard
    if not scenes:
        st.info("Storyboard belum dibuat."); return
    n = len(scenes)
    expected_n = scene_count()
    if st.session_state.storyboard_duration and st.session_state.storyboard_duration != st.session_state.duration:
        st.warning(
            f"Durasi sekarang {st.session_state.duration} = {expected_n} adegan, "
            f"tetapi storyboard ini dibuat saat durasi {st.session_state.storyboard_duration} = {n} adegan. "
            "Buat ulang storyboard agar jumlah adegan sesuai."
        )
        if st.button("BUAT ULANG STORYBOARD SESUAI DURASI", type="primary", use_container_width=True):
            run_storyboard()
            st.rerun()
        return
    current = max(1, min(st.session_state.current_scene, n))
    st.session_state.current_scene = current
    st.progress(current / n)
    st.write(f"Adegan {current} dari {n}")
    scene = scenes[current-1]
    st.subheader(f"Adegan {current} — {scene.get('waktu','')}")
    st.write("**Aksi:**", scene.get("aksi", ""))
    st.write("**Kontinuitas:**", scene.get("kontinuitas", ""))

    if current > 1:
        frame = st.file_uploader(f"Upload screenshot frame terakhir Adegan {current-1}", type=["png","jpg","jpeg","webp"], key=f"frame_{current}")
        if frame:
            st.session_state.scene_frames[current-1] = frame
            st.success(f"Frame terakhir Adegan {current-1} tersimpan.")

    if current not in st.session_state.scene_prompts:
        if st.button(f"BUAT PROMPT ADEGAN {current}", type="primary", use_container_width=True):
            if generate_scene_prompt(current):
                st.rerun()
    else:
        st.text_area("Prompt Flow/Veo — Bahasa Inggris", value=st.session_state.scene_prompts[current], height=380, key=f"view_{current}")
        c1, c2 = st.columns(2)
        with c1:
            if current > 1 and st.button("ADEGAN SEBELUMNYA", use_container_width=True):
                st.session_state.current_scene = current-1; st.rerun()
        with c2:
            if current < n:
                if st.button("ADEGAN BERIKUTNYA", type="primary", use_container_width=True):
                    st.session_state.current_scene = current+1; st.rerun()
            elif st.button("LANJUT KE SEO", type="primary", use_container_width=True): go("seo")

    st.divider()
    jump = st.selectbox("Pilih adegan", list(range(1,n+1)), index=current-1, key="jump_scene")
    if jump != current:
        st.session_state.current_scene = jump; st.rerun()


def run_seo():
    client = get_client()
    if not client: return
    prompt = f"""
Buat paket SEO YouTube dalam Bahasa Indonesia untuk video berikut.
Analisis: {json.dumps(st.session_state.analysis, ensure_ascii=False)}
Jumlah adegan: {len(st.session_state.storyboard)}
Kembalikan HANYA JSON valid:
{{"judul":["...","...","..."],"deskripsi":"...","kata_kunci":["..."],"hashtag":["..."],"teks_thumbnail":"...","konsep_thumbnail":"...","komentar_tersemat":"...","ajakan":"..."}}
"""
    with st.spinner("Membuat SEO..."):
        try: st.session_state.seo = extract_json(ask(client, prompt))
        except Exception as e: st.error(f"SEO gagal dibuat: {e}")


def render_seo():
    st.title("SEO YouTube")
    if not st.session_state.analysis:
        st.info("Analisis referensi belum tersedia."); return
    if not st.session_state.seo:
        if st.button("BUAT SEO", type="primary", use_container_width=True): run_seo(); st.rerun()
        return
    s=st.session_state.seo
    for i,t in enumerate(s.get("judul",[]),1): st.text_input(f"Judul {i}", str(t), key=f"title_{i}")
    st.text_area("Deskripsi", safe_text(s.get("deskripsi")), height=220)
    st.text_area("Kata kunci", ", ".join(map(str,s.get("kata_kunci",[]))), height=100)
    st.text_area("Hashtag", " ".join(map(str,s.get("hashtag",[]))), height=100)
    st.text_input("Teks thumbnail", safe_text(s.get("teks_thumbnail")))
    st.text_area("Konsep thumbnail", safe_text(s.get("konsep_thumbnail")), height=100)
    st.text_area("Komentar tersemat", safe_text(s.get("komentar_tersemat")), height=100)
    st.text_area("Ajakan", safe_text(s.get("ajakan")), height=100)
    st.success("Alur proyek selesai.")


if st.session_state.page == "home": render_home()
elif st.session_state.page == "analysis": render_analysis()
elif st.session_state.page == "storyboard": render_storyboard()
elif st.session_state.page == "scenes": render_scenes()
elif st.session_state.page == "seo": render_seo()
