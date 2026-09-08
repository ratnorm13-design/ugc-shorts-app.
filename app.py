import json
import re
import time
from copy import deepcopy
from typing import Any

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="UGC Reference Studio", page_icon=":material/movie:", layout="wide")

MODEL_NAME = "gemini-3.6-flash"

DURATION_SCENES = {
    "8 detik": 1,
    "16 detik": 2,
    "24 detik": 3,
    "32 detik": 4,
    "40 detik": 5,
    "48 detik": 6,
    "56 detik": 7,
    "1 menit": 8,
    "1,5 menit": 12,
    "2 menit": 15,
    "2,5 menit": 19,
    "3 menit": 23,
}

STYLE_OPTIONS = [
    "Sinematik realistis",
    "Animasi 3D",
    "Animasi 2D",
    "Komedi bergaya",
    "Lucu dan ramah keluarga",
    "Dokumenter realistis",
    "Aksi sinematik",
    "Kustom",
]
ASPECT_OPTIONS = ["9:16 - Shorts", "16:9 - YouTube", "1:1 - Kotak"]
REFERENCE_OPTIONS = ["Video", "Screenshot", "Teks / ide"]

# ============================================================
# TALE OF PAW - CHARACTER LOCK
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
        "struktur wajah, pola bulu, warna mata, bentuk telinga, ukuran tubuh, "
        "usia visual, dan proporsi harus tetap sama di setiap adegan"
    ),
    "aturan_konsistensi": (
        "Milo selalu kitten yang sama. Jangan mengganti spesies, identitas wajah, "
        "warna/pola bulu utama, warna mata, ukuran, usia visual, atau proporsi. "
        "Detail kostum/aksesori, properti, lingkungan, kamera, lighting, dan aksi "
        "boleh berubah hanya jika memang dibutuhkan oleh alur referensi."
    ),
}

CHARACTER_LOCK_EN = (
    "Milo is the permanent main character of Tale Of Paw. He is always the exact same "
    "young domestic kitten: small realistic kitten proportions, creamy white fur with "
    "subtle light-gray fur on the ears and back, large round expressive eyes, innocent "
    "curious face, and consistent facial structure, fur pattern, eye color, ear shape, "
    "body size, age appearance, and proportions. Never redesign, replace, age up, morph, "
    "or change Milo's identity. Scene-specific clothing or accessories, safe props, "
    "environment, camera, lighting, and production details may change only when required "
    "by the established story continuity."
)

DEFAULTS = {
    "page": "home",
    "api_key": "",
    "reference_type": "Video",
    "reference_file": None,
    "reference_files": [],
    "reference_text": "",
    "visual_style": STYLE_OPTIONS[0],
    "aspect_ratio": ASPECT_OPTIONS[0],
    "duration": "8 detik",
    "custom_instruction": "",
    "analysis": {},
    "character": deepcopy(CHARACTER_LOCK),
    "storyboard": [],
    "scene_prompts": {},
    "scene_frames": {},
    "current_scene": 1,
    "storyboard_duration": None,
    "seo": {},
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = deepcopy(value)


def reset_project():
    for key, value in DEFAULTS.items():
        st.session_state[key] = deepcopy(value)


def go(page):
    st.session_state.page = page
    st.rerun()


def scene_count():
    return DURATION_SCENES[st.session_state.duration]


def safe_text(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(x) for x in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def get_client():
    key = st.session_state.api_key.strip()
    if not key:
        st.error("Masukkan Gemini API Key terlebih dahulu.")
        return None
    try:
        return genai.Client(api_key=key)
    except Exception as exc:
        st.error(f"Gagal membuat koneksi Gemini: {exc}")
        return None


def extract_json(text: str) -> Any:
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
    raise ValueError("Respons AI tidak bisa dibaca sebagai JSON.")


def ask(client, prompt, parts=None):
    contents = [prompt] + (parts or [])
    last_error = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(temperature=0.35),
            )
            return response.text or ""
        except Exception as exc:
            last_error = exc
            if "503" in str(exc) or "UNAVAILABLE" in str(exc):
                time.sleep(3 * (attempt + 1))
                continue
            raise
    raise RuntimeError(
        "Gemini sedang sibuk setelah 3 percobaan. Coba lagi sebentar. "
        f"Error: {last_error}"
    )


def upload_to_gemini(client, uploaded_file):
    if uploaded_file is None:
        return None
    try:
        config = {"display_name": uploaded_file.name}
        mime = getattr(uploaded_file, "type", None)
        if mime:
            config["mime_type"] = mime
        return client.files.upload(file=uploaded_file, config=config)
    except Exception as exc:
        st.warning(f"File gagal dikirim ke Gemini: {exc}")
        return None


def file_parts(client, uploaded_file):
    remote = upload_to_gemini(client, uploaded_file)
    return [remote] if remote else []


def reference_parts(client):
    ref_type = st.session_state.reference_type
    if ref_type == "Video" and st.session_state.reference_file:
        return file_parts(client, st.session_state.reference_file)
    if ref_type == "Screenshot":
        result = []
        for uploaded_file in st.session_state.reference_files:
            result.extend(file_parts(client, uploaded_file))
        return result
    if ref_type == "Teks / ide" and st.session_state.reference_text.strip():
        return [f"REFERENSI TEKS PENGGUNA:\n{st.session_state.reference_text}"]
    return []


def invalidate_from_analysis():
    st.session_state.storyboard = []
    st.session_state.scene_prompts = {}
    st.session_state.scene_frames = {}
    st.session_state.current_scene = 1
    st.session_state.storyboard_duration = None
    st.session_state.seo = {}


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title(":material/movie: UGC Reference Studio")
    st.caption("Referensi -> Continuity Analysis -> Storyboard -> Flow/Veo")
    st.text_input("Gemini API Key", type="password", key="api_key", placeholder="AIza...")
    st.divider()
    if st.button(":material/home: Beranda", use_container_width=True):
        go("home")
    if st.button(":material/analytics: Analisis Referensi", use_container_width=True):
        go("analysis")
    if st.button(":material/account_tree: Storyboard", use_container_width=True):
        go("storyboard")
    if st.button(":material/auto_awesome: Prompt Adegan", use_container_width=True):
        go("scenes")
    if st.button(":material/search: SEO YouTube", use_container_width=True):
        go("seo")
    st.divider()
    if st.button(":material/add: Proyek Baru", use_container_width=True):
        reset_project()
        st.rerun()


# ============================================================
# HOME
# ============================================================
def render_home():
    st.title(":material/movie: UGC Reference Studio")
    st.write(
        "Mesin referensi yang membedah video acuan secara berurutan, memetakan lokasi, "
        "kamera, karakter, properti, aksi, dan keadaan akhir setiap adegan sebelum membuat prompt Flow/Veo."
    )

    st.subheader(":material/video_library: 1. Referensi")
    st.radio("Jenis referensi", REFERENCE_OPTIONS, horizontal=True, key="reference_type")
    ref_type = st.session_state.reference_type
    if ref_type == "Video":
        st.session_state.reference_file = st.file_uploader(
            "Upload video referensi",
            type=["mp4", "mov", "webm", "avi", "mkv"],
        )
        st.session_state.reference_files = []
    elif ref_type == "Screenshot":
        st.session_state.reference_files = st.file_uploader(
            "Upload screenshot referensi secara berurutan",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
        )
        st.session_state.reference_file = None
    else:
        st.session_state.reference_text = st.text_area(
            "Tulis referensi atau ide",
            value=st.session_state.reference_text,
            height=160,
        )
        st.session_state.reference_file = None
        st.session_state.reference_files = []

    st.subheader(":material/tune: 2. Pengaturan Video")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Gaya visual", STYLE_OPTIONS, key="visual_style")
        st.selectbox("Rasio video", ASPECT_OPTIONS, key="aspect_ratio")
    with col2:
        st.selectbox("Durasi video", list(DURATION_SCENES.keys()), key="duration")
        st.text_area(
            "Instruksi tambahan",
            key="custom_instruction",
            height=100,
            placeholder="Contoh: ending lebih lucu, tempo tetap cepat, ekspresi lebih jelas.",
        )

    n = scene_count()
    st.info(
        f"{st.session_state.duration} = {n} adegan. Setiap adegan sekitar 8 detik. "
        "Jumlah adegan hanya membagi waktu; alur tidak boleh melompat."
    )

    st.subheader(":material/link: 3. Prinsip Continuity")
    st.write(
        "Sistem tidak langsung membuat prompt. Referensi dibedah dulu menjadi urutan kejadian, "
        "peta lokasi, posisi kamera, posisi karakter, status properti, start state, action, dan end state."
    )
    st.write(
        "Adegan berikutnya wajib dimulai dari end state adegan sebelumnya. Tidak boleh tiba-tiba "
        "muncul pintu, orang, lokasi, properti, atau kamera baru tanpa sebab yang sudah dibangun."
    )
    st.write(
        "Video viral dari platform sosial mana pun boleh digunakan sebagai referensi yang kamu upload. "
        "Identitas karakter utama Tale Of Paw tetap Milo."
    )

    if st.button(":material/analytics: ANALISIS REFERENSI", type="primary", use_container_width=True):
        run_analysis()


# ============================================================
# REFERENCE ANALYSIS - TEMPORAL + SPATIAL + STATE
# ============================================================
def run_analysis():
    client = get_client()
    if not client:
        return
    parts = reference_parts(client)
    if not parts:
        st.warning("Masukkan atau upload referensi terlebih dahulu.")
        return

    target_scenes = scene_count()
    prompt = f"""
Anda adalah showrunner dan continuity supervisor untuk video pendek komedi sinematik.
Analisis referensi yang diberikan SECARA TEMPORAL dan SPATIAL sebelum membuat storyboard.
Jangan langsung menulis prompt video.

TUJUAN:
Membangun satu sumber kebenaran (single source of truth) tentang apa yang terjadi,
di mana karakter berada, dari mana objek datang, bagaimana kamera melihat kejadian,
dan bagaimana satu kejadian menyebabkan kejadian berikutnya.

ATURAN KERAS:
1. Urutan kejadian harus mengikuti referensi. Jangan mengarang plot baru.
2. Setiap perubahan harus mempunyai sebab yang terlihat atau sudah disiapkan sebelumnya.
3. Jangan membuat objek, pintu, orang, kendaraan, ruangan, atau kamera tiba-tiba muncul.
4. Jika sesuatu baru muncul pada referensi, jelaskan bagaimana dan dari mana ia masuk.
5. Bedakan elemen yang SUDAH ADA sejak awal dengan elemen yang BARU MASUK.
6. Catat posisi relatif: kiri/kanan/tengah/depan/belakang, dekat/jauh, di atas/bawah.
7. Catat kamera: posisi, tinggi, arah pandang, framing, lensa/perspektif, dan gerak kamera.
8. Catat status properti: dipegang, di lantai, di meja, di dalam kendaraan, terbuka/tertutup, dll.
9. Setiap beat harus memiliki START STATE, ACTION, dan END STATE.
10. END STATE beat sebelumnya menjadi START STATE beat berikutnya kecuali referensi sendiri menunjukkan perubahan.
11. Jika target video {st.session_state.duration} membutuhkan {target_scenes} scene, pecah kejadian referensi secara temporal.
    Jangan menambah kejadian baru hanya untuk memenuhi jumlah scene.
12. Untuk karakter utama, gunakan Milo sebagai karakter Tale Of Paw. Karakter pendukung hanya boleh ada jika memang diperlukan oleh referensi/alur.
13. Properti biasa dan lingkungan yang tidak berbahaya harus dipertahankan secara visual. Untuk elemen berbahaya, pertahankan fungsi dramatis/komedinya tanpa detail operasional dan buat representasinya aman.
14. Jangan mengubah lokasi atau geografi hanya agar prompt terlihat lebih sinematik.
15. Semua nilai JSON berbahasa Indonesia.

CHARACTER LOCK:
{json.dumps(CHARACTER_LOCK, ensure_ascii=False, indent=2)}

PENGATURAN:
Gaya visual: {st.session_state.visual_style}
Rasio: {st.session_state.aspect_ratio}
Durasi target: {st.session_state.duration}
Jumlah scene target: {target_scenes}
Instruksi pengguna: {st.session_state.custom_instruction}

Kembalikan HANYA JSON dengan struktur persis:
{{
  "ringkasan": "...",
  "niche": "...",
  "hook": "...",
  "sebab_akibat": "...",
  "tujuan_emosi": "...",
  "pacing_logic": "...",
  "payoff": "...",
  "world_lock": {{
    "lokasi_utama": "...",
    "geografi": "...",
    "elemen_tetap": ["..."],
    "titik_masuk_keluar": ["..."],
    "aturan_lokasi": ["..."]
  }},
  "camera_lock": {{
    "posisi": "...",
    "tinggi": "...",
    "arah_pandang": "...",
    "framing": "...",
    "perspektif_lensa": "...",
    "gerakan": "...",
    "aturan_kamera": ["..."]
  }},
  "character_lock": {{
    "nama": "Milo",
    "peran_dalam_referensi": "...",
    "posisi_awal": "...",
    "gerakan_khas": "..."
  }},
  "prop_locks": [
    {{"nama":"...", "status_awal":"...", "lokasi":"...", "perubahan":"..."}}
  ],
  "temporal_breakdown": [
    {{
      "beat": 1,
      "waktu": "00:00-00:08",
      "start_state": "...",
      "action": "...",
      "cause": "...",
      "end_state": "...",
      "camera_state": "...",
      "character_state": "...",
      "prop_state": "...",
      "continuity_to_next": "..."
    }}
  ],
  "urutan_kejadian": ["..."],
  "detail_produksi": {{
    "penampilan": "...",
    "setting": "...",
    "lighting": "...",
    "visual_design": "...",
    "dialog": "...",
    "sound_design": "..."
  }}
}}
"""

    with st.spinner("Membedah referensi: urutan, lokasi, kamera, karakter, properti, dan continuity..."):
        try:
            data = extract_json(ask(client, prompt, parts))
            data["karakter_utama"] = deepcopy(CHARACTER_LOCK)
            st.session_state.analysis = data
            st.session_state.character = deepcopy(CHARACTER_LOCK)
            invalidate_from_analysis()
            go("analysis")
        except Exception as exc:
            st.error(f"Analisis gagal: {exc}")

# ============================================================
# ANALYSIS PAGE
# ============================================================
def render_analysis():
    st.title(":material/analytics: Analisis Referensi + Continuity Map")
    analysis = st.session_state.analysis
    if not analysis:
        st.info("Belum ada analisis. Kembali ke Beranda dan analisis referensi.")
        return

    st.subheader(":material/account_tree: Alur yang Dikunci")
    for label, key in [
        ("Niche", "niche"),
        ("Hook", "hook"),
        ("Sebab-akibat", "sebab_akibat"),
        ("Tujuan emosi", "tujuan_emosi"),
        ("Pacing", "pacing_logic"),
        ("Payoff", "payoff"),
    ]:
        st.write(f"**{label}:** {safe_text(analysis.get(key))}")

    world = analysis.get("world_lock", {})
    camera = analysis.get("camera_lock", {})

    st.subheader(":material/map: World / Geography Lock")
    st.write(f"**Lokasi utama:** {safe_text(world.get('lokasi_utama'))}")
    st.write(f"**Geografi:** {safe_text(world.get('geografi'))}")
    st.write(f"**Elemen tetap:** {safe_text(world.get('elemen_tetap'))}")
    st.write(f"**Titik masuk/keluar:** {safe_text(world.get('titik_masuk_keluar'))}")
    st.write(f"**Aturan lokasi:** {safe_text(world.get('aturan_lokasi'))}")

    st.subheader(":material/photo_camera: Camera Lock")
    for label, key in [
        ("Posisi", "posisi"),
        ("Tinggi", "tinggi"),
        ("Arah pandang", "arah_pandang"),
        ("Framing", "framing"),
        ("Perspektif/lensa", "perspektif_lensa"),
        ("Gerakan", "gerakan"),
    ]:
        st.write(f"**{label}:** {safe_text(camera.get(key))}")

    st.subheader(":material/pets: Character Lock")
    st.write(f"**Nama:** {CHARACTER_LOCK['nama']}")
    st.write(f"**Visual:** {CHARACTER_LOCK['identitas_visual']}")
    st.warning("Milo tidak boleh berubah identitas. Posisi dan keadaan Milo boleh berubah hanya karena aksi cerita.")

    st.subheader(":material/timeline: Temporal Breakdown")
    beats = analysis.get("temporal_breakdown", [])
    for beat in beats:
        with st.expander(f"Beat {beat.get('beat')} - {beat.get('waktu', '')}"):
            for label, key in [
                ("Start state", "start_state"),
                ("Cause", "cause"),
                ("Action", "action"),
                ("End state", "end_state"),
                ("Camera state", "camera_state"),
                ("Character state", "character_state"),
                ("Prop state", "prop_state"),
                ("Continuity ke berikutnya", "continuity_to_next"),
            ]:
                st.write(f"**{label}:** {safe_text(beat.get(key))}")

    if st.button(":material/account_tree: BUAT STORYBOARD DARI CONTINUITY MAP", type="primary", use_container_width=True):
        run_storyboard()


# ============================================================
# STORYBOARD GENERATOR - START/ACTION/END CONTRACT
# ============================================================
def run_storyboard():
    client = get_client()
    if not client:
        return
    n = scene_count()
    analysis = st.session_state.analysis

    prompt = f"""
Anda adalah continuity supervisor. Buat storyboard final dari continuity map yang sudah dianalisis.
Jangan membuat konsep baru dan jangan mengarang kejadian baru.

TARGET:
- Tepat {n} scene.
- Masing-masing sekitar 8 detik.
- Scene 1 dimulai dari keadaan awal referensi.
- Scene N berakhir pada payoff/keadaan akhir referensi.
- Setiap scene harus menjadi kelanjutan langsung scene sebelumnya.

ATURAN WAJIB:
1. START STATE Scene 1 harus konsisten dengan referensi.
2. START STATE Scene 2+ harus sama dengan END STATE scene sebelumnya, kecuali perubahan terjadi secara eksplisit dalam transisi.
3. Setiap scene wajib memiliki satu rantai: START STATE -> CAUSE -> ACTION -> END STATE.
4. Jangan memperkenalkan objek/karakter/lokasi baru tanpa menjelaskan asal dan momen masuknya.
5. Jangan mengubah posisi pintu, jendela, tangga, kendaraan, meja, kamera, atau elemen lingkungan tetap.
6. Jangan memindahkan kamera ke tempat lain kecuali camera lock/reference memang menunjukkan perpindahan.
7. Jangan memindahkan properti secara teleport. Jika properti berpindah, tulis aksi yang memindahkannya.
8. Milo harus karakter yang sama secara fisik di semua scene.
9. Jangan menambahkan scene filler yang tidak ada hubungan sebab-akibat.
10. Jika jumlah target scene lebih besar daripada jumlah beat referensi, pecah satu beat menjadi beberapa langkah mikro yang memang terjadi secara natural; jangan membuat plot baru.
11. Jika jumlah target scene lebih kecil, gabungkan beat yang berdekatan tanpa menghilangkan sebab-akibat.
12. Buat ending setiap scene mudah dilanjutkan oleh generator video berikutnya.
13. Semua teks JSON Bahasa Indonesia.

CHARACTER LOCK:
{json.dumps(CHARACTER_LOCK, ensure_ascii=False, indent=2)}

CONTINUITY MAP:
{json.dumps(analysis, ensure_ascii=False, indent=2)}

Kembalikan HANYA JSON:
{{
  "adegan": [
    {{
      "nomor": 1,
      "waktu": "00:00-00:08",
      "tujuan": "...",
      "start_state": {{
        "lokasi": "...",
        "kamera": "...",
        "milo": "...",
        "properti": "...",
        "elemen_lingkungan": "..."
      }},
      "cause": "...",
      "aksi": "...",
      "end_state": {{
        "lokasi": "...",
        "kamera": "...",
        "milo": "...",
        "properti": "...",
        "elemen_lingkungan": "..."
      }},
      "kontinuitas": "Jelaskan tepat bagaimana end state ini menjadi start state scene berikutnya.",
      "kamera": "...",
      "audio": "...",
      "transisi": "..."
    }}
  ]
}}
"""

    with st.spinner(f"Menyusun {n} scene dengan continuity contract..."):
        try:
            data = extract_json(ask(client, prompt))
            scenes = data.get("adegan", [])
            if len(scenes) != n:
                raise ValueError(f"Harus tepat {n} scene, tetapi AI menghasilkan {len(scenes)}.")

            for index, scene in enumerate(scenes, 1):
                scene["nomor"] = index
                scene.setdefault("waktu", f"{(index - 1) * 8:02d}-{index * 8:02d}")
                scene.setdefault("start_state", {})
                scene.setdefault("end_state", {})
                scene.setdefault("cause", "")
                scene.setdefault("aksi", "")
                scene.setdefault("kontinuitas", "")

            # Local structural validation before allowing prompts.
            if not scenes[0].get("start_state"):
                raise ValueError("Scene 1 tidak memiliki START STATE.")
            for index in range(1, len(scenes)):
                if not scenes[index].get("start_state") or not scenes[index].get("end_state"):
                    raise ValueError(f"Scene {index + 1} tidak memiliki state lengkap.")

            st.session_state.storyboard = scenes
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}
            st.session_state.current_scene = 1
            st.session_state.storyboard_duration = st.session_state.duration
            st.session_state.seo = {}
            go("storyboard")
        except Exception as exc:
            st.error(f"Storyboard gagal dibuat: {exc}")


# ============================================================
# STORYBOARD PAGE
# ============================================================
def render_storyboard():
    st.title(":material/account_tree: Storyboard - Continuity Terkunci")
    scenes = st.session_state.storyboard
    if not scenes:
        st.info("Storyboard belum dibuat.")
        return

    st.info(
        f"{st.session_state.duration} = {len(scenes)} scene. "
        "Setiap scene memiliki START STATE, CAUSE, ACTION, dan END STATE."
    )

    for scene in scenes:
        with st.expander(f"Scene {scene['nomor']} - {scene.get('waktu', '')}", expanded=scene['nomor'] == 1):
            st.write(f"**Tujuan:** {safe_text(scene.get('tujuan'))}")
            st.write("**START STATE:**")
            st.json(scene.get("start_state", {}))
            st.write(f"**CAUSE:** {safe_text(scene.get('cause'))}")
            st.write(f"**ACTION:** {safe_text(scene.get('aksi'))}")
            st.write("**END STATE:**")
            st.json(scene.get("end_state", {}))
            st.write(f"**Continuity:** {safe_text(scene.get('kontinuitas'))}")
            st.write(f"**Camera:** {safe_text(scene.get('kamera'))}")
            st.write(f"**Audio:** {safe_text(scene.get('audio'))}")
            st.write(f"**Transition:** {safe_text(scene.get('transisi'))}")

    if st.button(":material/arrow_forward: LANJUT KE PROMPT ADEGAN", type="primary", use_container_width=True):
        go("scenes")


# ============================================================
# SCENE PROMPT GENERATOR
# ============================================================
def previous_scene_text(scene_number):
    if scene_number <= 1:
        return "Tidak ada scene sebelumnya; gunakan initial state dari continuity map/reference."
    previous = st.session_state.storyboard[scene_number - 2]
    return json.dumps(previous, ensure_ascii=False, indent=2)


def next_scene_text(scene_number):
    scenes = st.session_state.storyboard
    if scene_number >= len(scenes):
        return "Ini scene terakhir; ending harus menyelesaikan payoff tanpa membuat lokasi baru."
    return json.dumps(scenes[scene_number], ensure_ascii=False, indent=2)


def generate_scene_prompt(scene_number):
    client = get_client()
    if not client:
        return False

    scenes = st.session_state.storyboard
    scene = scenes[scene_number - 1]
    previous_frame = st.session_state.scene_frames.get(scene_number - 1)
    analysis = st.session_state.analysis

    prompt = f"""
Write ONE production-ready Google Flow / Veo prompt in ENGLISH for Scene {scene_number}.
Do not write commentary before or after the prompt.

THIS IS A CONTINUATION TASK, NOT A NEW IMAGE CONCEPT.
The generated scene must look like the immediate continuation of the previous scene.

CONTINUITY HIERARCHY - highest priority first:
1. Previous scene END STATE and uploaded last-frame image, if supplied.
2. Current scene START STATE.
3. Locked location/geography and camera.
4. Locked character identity.
5. Current scene ACTION and CAUSE.
6. Current scene END STATE.
7. Style/lighting polish.

ABSOLUTE RULES:
- Never teleport or relocate a character, prop, doorway, vehicle, furniture, or camera.
- Never introduce a new environment that was not established.
- Never make a person/object suddenly appear without a visible entrance or cause defined by the storyboard.
- Keep the same physical geography: left/right/center, foreground/background, entrances and exits.
- Keep the same camera position and perspective unless the storyboard explicitly requires a camera move.
- If the camera moves, describe the movement continuously from its previous position rather than cutting to an unrelated angle.
- The first moment of this scene must visually match the previous END STATE.
- The final moment must visually match this scene's END STATE so the next scene can continue from it.
- Milo must remain exactly the same kitten.
- Do not redesign Milo between scenes.
- Ordinary non-hazardous props and environmental details should remain visually faithful to the established reference.
- For hazardous elements, keep only the non-operational cinematic/comedic beat and do not provide realistic operational details.

MILO LOCK:
{CHARACTER_LOCK_EN}

WORLD LOCK:
{json.dumps(analysis.get('world_lock', {}), ensure_ascii=False, indent=2)}

CAMERA LOCK:
{json.dumps(analysis.get('camera_lock', {}), ensure_ascii=False, indent=2)}

CURRENT SCENE CONTRACT:
{json.dumps(scene, ensure_ascii=False, indent=2)}

PREVIOUS SCENE CONTRACT:
{previous_scene_text(scene_number)}

NEXT SCENE CONTRACT:
{next_scene_text(scene_number)}

PROJECT STYLE: {st.session_state.visual_style}
ASPECT RATIO: {st.session_state.aspect_ratio}
TOTAL DURATION: {st.session_state.duration}

OUTPUT REQUIREMENT:
Write one detailed paragraph in English. Explicitly describe:
- exact opening state and composition;
- fixed geography and object positions;
- Milo's exact appearance and current pose;
- cause and continuous action;
- camera position and movement;
- lighting continuity;
- sound/dialogue only when appropriate;
- exact final state and where every important character/prop is located.
Do not invent anything that conflicts with the contracts.
"""

    parts = file_parts(client, previous_frame) if previous_frame else []

    with st.spinner(f"Membuat prompt Scene {scene_number} dengan continuity lock..."):
        try:
            result = ask(client, prompt, parts).strip()
            if not result:
                raise ValueError("Prompt kosong.")
            st.session_state.scene_prompts[scene_number] = result
            return True
        except Exception as exc:
            st.error(f"Prompt Scene {scene_number} gagal: {exc}")
            return False


# ============================================================
# SCENE PAGE
# ============================================================
def render_scenes():
    st.title(":material/auto_awesome: Prompt Adegan untuk Flow/Veo")
    scenes = st.session_state.storyboard
    if not scenes:
        st.info("Storyboard belum dibuat.")
        return

    n = len(scenes)
    expected = scene_count()
    if st.session_state.storyboard_duration != st.session_state.duration:
        st.warning(
            f"Storyboard ini dibuat untuk {st.session_state.storyboard_duration} ({n} scene), "
            f"sedangkan durasi sekarang {st.session_state.duration} ({expected} scene). "
            "Buat ulang storyboard agar jumlah scene sesuai."
        )
        if st.button(":material/refresh: BUAT ULANG STORYBOARD SESUAI DURASI", type="primary", use_container_width=True):
            run_storyboard()
        return

    current = max(1, min(st.session_state.current_scene, n))
    st.session_state.current_scene = current
    st.progress(current / n)
    st.write(f"**Scene {current} / {n}**")

    scene = scenes[current - 1]
    st.subheader(f"Scene {current} - {scene.get('waktu', '')}")
    st.write(f"**Start state:** {safe_text(scene.get('start_state'))}")
    st.write(f"**Cause:** {safe_text(scene.get('cause'))}")
    st.write(f"**Action:** {safe_text(scene.get('aksi'))}")
    st.write(f"**End state:** {safe_text(scene.get('end_state'))}")

    if current > 1:
        st.info(
            f"Scene {current} harus dimulai dari END STATE Scene {current - 1}. "
            "Upload frame terakhir hasil Flow/Veo untuk continuity visual yang lebih kuat."
        )
        frame = st.file_uploader(
            f"Upload screenshot frame terakhir Scene {current - 1}",
            type=["png", "jpg", "jpeg", "webp"],
            key=f"frame_{current}",
        )
        if frame is not None:
            st.session_state.scene_frames[current - 1] = frame
            st.success(f"Frame terakhir Scene {current - 1} tersimpan.")

    if current not in st.session_state.scene_prompts:
        if st.button(f":material/auto_awesome: BUAT PROMPT SCENE {current}", type="primary", use_container_width=True):
            if generate_scene_prompt(current):
                st.rerun()
    else:
        st.success(f"Prompt Scene {current} sudah dibuat.")
        st.text_area(
            "Prompt Flow/Veo - Bahasa Inggris",
            value=st.session_state.scene_prompts[current],
            height=430,
            key=f"view_prompt_{current}",
        )

        left, right = st.columns(2)
        with left:
            if current > 1 and st.button(":material/arrow_back: SCENE SEBELUMNYA", use_container_width=True):
                st.session_state.current_scene = current - 1
                st.rerun()
        with right:
            if current < n:
                if st.button(":material/arrow_forward: SCENE BERIKUTNYA", type="primary", use_container_width=True):
                    st.session_state.current_scene = current + 1
                    st.rerun()
            else:
                if st.button(":material/search: LANJUT KE SEO", type="primary", use_container_width=True):
                    go("seo")

    st.divider()
    jump = st.selectbox(
        "Pilih scene",
        list(range(1, n + 1)),
        index=current - 1,
        key="jump_scene",
    )
    if jump != current:
        st.session_state.current_scene = jump
        st.rerun()


# ============================================================
# SEO
# ============================================================
def run_seo():
    client = get_client()
    if not client:
        return
    prompt = f"""
Buat paket SEO YouTube dalam Bahasa Indonesia untuk video Tale Of Paw berikut.
Jangan mengubah inti cerita.

Analisis:
{json.dumps(st.session_state.analysis, ensure_ascii=False)}
Jumlah scene: {len(st.session_state.storyboard)}

Kembalikan HANYA JSON valid:
{{
  "judul":["...","...","..."],
  "deskripsi":"...",
  "kata_kunci":["..."],
  "hashtag":["..."],
  "teks_thumbnail":"...",
  "konsep_thumbnail":"...",
  "komentar_tersemat":"...",
  "ajakan":"..."
}}
"""
    with st.spinner("Membuat SEO..."):
        try:
            st.session_state.seo = extract_json(ask(client, prompt))
        except Exception as exc:
            st.error(f"SEO gagal dibuat: {exc}")


def render_seo():
    st.title(":material/search: SEO YouTube")
    if not st.session_state.analysis:
        st.info("Analisis referensi belum tersedia.")
        return
    if not st.session_state.seo:
        if st.button(":material/auto_awesome: BUAT SEO", type="primary", use_container_width=True):
            run_seo()
            st.rerun()
        return

    seo = st.session_state.seo
    for index, title in enumerate(seo.get("judul", []), 1):
        st.text_input(f"Judul {index}", str(title), key=f"title_{index}")
    st.text_area("Deskripsi", safe_text(seo.get("deskripsi")), height=220)
    st.text_area("Kata kunci", ", ".join(map(str, seo.get("kata_kunci", []))), height=100)
    st.text_area("Hashtag", " ".join(map(str, seo.get("hashtag", []))), height=100)
    st.text_input("Teks thumbnail", safe_text(seo.get("teks_thumbnail")))
    st.text_area("Konsep thumbnail", safe_text(seo.get("konsep_thumbnail")), height=100)
    st.text_area("Komentar tersemat", safe_text(seo.get("komentar_tersemat")), height=100)
    st.text_area("Ajakan", safe_text(seo.get("ajakan")), height=100)
    st.success("Alur proyek selesai.")


# ============================================================
# ROUTER
# ============================================================
if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "analysis":
    render_analysis()
elif st.session_state.page == "storyboard":
    render_storyboard()
elif st.session_state.page == "scenes":
    render_scenes()
elif st.session_state.page == "seo":
    render_seo()
