import json
import re
import time
import cv2
from copy import deepcopy
from typing import Any

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="UGC Reference Studio", page_icon="🎬", layout="wide")

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
    "3,5 menit": 27,
    "4 menit": 30,
    "4,5 menit": 34,
    "5 menit": 38,
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
ASPECT_OPTIONS = ["9:16 — Shorts", "16:9 — YouTube", "1:1 — Kotak"]
REFERENCE_OPTIONS = ["Video", "Screenshot", "Teks / ide"]

# ============================================================
# TALE OF PAW — CHARACTER LOCK
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
    "duration_selector": "8 detik",
    "reference_signature": None,
    "_reset_requested": False,
    "project_nonce": 0,
    "detected_reference_duration": None,
    "duration_extension": None,
    "target_scene_count": None,
    "target_duration_label": None,
    "custom_instruction": "",
    "analysis": {},
    "character": deepcopy(CHARACTER_LOCK),
    "storyboard": [],
    "scene_prompts": {},
    "scene_prompt_notes": {},
    "scene_frames": {},
    "current_scene": 1,
    "storyboard_duration": None,
    "seo": {},
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = deepcopy(value)

def reset_project_callback():
    """Start a fresh project without mutating active widget keys.

    Streamlit widgets are stateful and some widget values cannot safely be
    assigned through Session State. The reset therefore changes a project
    nonce, clears only application data, and lets the new widget keys create
    a clean UI on the next rerun.
    """
    preserved_api_key = st.session_state.get("api_key", "")
    old_nonce = int(st.session_state.get("project_nonce", 0) or 0)

    # Clear application-owned state only. Do not delete/set file_uploader or
    # button keys; changing project_nonce gives those widgets fresh identities.
    widget_keys = {"api_key", "duration_selector", "reference_type", "visual_style", "aspect_ratio", "custom_instruction"}
    for key in list(DEFAULTS):
        if key not in widget_keys:
            st.session_state.pop(key, None)

    for key in list(st.session_state.keys()):
        if key.startswith((
            "title_", "gate_frame_", "advance_frame_", "ref_upload_",
            "frame_saved_", "validate_frame_", "open_next_", "screenshot_ref_"
        )):
            # These are old project-specific widget identities. Removing them
            # in the callback is safe because the new widgets use a new nonce.
            st.session_state.pop(key, None)

    st.session_state["api_key"] = preserved_api_key
    st.session_state["reference_type"] = "Video"
    st.session_state["visual_style"] = STYLE_OPTIONS[0]
    st.session_state["aspect_ratio"] = ASPECT_OPTIONS[0]
    st.session_state["duration_selector"] = "8 detik"
    st.session_state["custom_instruction"] = ""
    st.session_state["project_nonce"] = old_nonce + 1
    st.session_state["page"] = "home"


def go(page):
    st.session_state.page = page
    st.rerun()


def scene_count():
    """Return the locked scene count for the analyzed project.

    Once analysis starts, the scene count must NOT change just because the
    Home duration widget reruns or the user navigates between pages.
    """
    locked = st.session_state.get("target_scene_count")
    if locked:
        return int(locked)
    return DURATION_SCENES[st.session_state.duration]


def detect_video_duration(uploaded_file):
    """Return reference video duration in seconds, or None if it cannot be read."""
    if uploaded_file is None:
        return None
    temp_path = None
    try:
        suffix = ".mp4"
        name = getattr(uploaded_file, "name", "")
        if "." in name:
            suffix = "." + name.rsplit(".", 1)[1].lower()
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            temp_path = tmp.name
        cap = cv2.VideoCapture(temp_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        if fps and fps > 0 and frames and frames > 0:
            return float(frames / fps)
    except Exception:
        return None
    finally:
        if temp_path:
            try:
                import os
                os.remove(temp_path)
            except Exception:
                pass
    return None


def choose_target_duration(seconds):
    """Choose the smallest supported duration that is not shorter than the reference."""
    if seconds is None:
        return None, None
    supported = []
    for label, scenes in DURATION_SCENES.items():
        if label.endswith("detik"):
            total = scenes * 8
        else:
            total = scenes * 8
        supported.append((total, label))
    supported.sort()
    for total, label in supported:
        if seconds <= total + 0.25:
            return label, total
    return "5 menit", DURATION_SCENES["5 menit"] * 8


def apply_reference_duration(uploaded_file):
    """Detect video duration and automatically move the target up when needed."""
    seconds = detect_video_duration(uploaded_file)
    if seconds is None:
        return
    target_label, target_seconds = choose_target_duration(seconds)
    st.session_state.detected_reference_duration = seconds
    if target_label and target_label != st.session_state.duration:
        current_seconds = DURATION_SCENES[st.session_state.duration] * 8
        if target_seconds > current_seconds:
            st.session_state.duration = target_label
            st.session_state.duration_extension = {
                "reference_seconds": round(seconds, 2),
                "target_seconds": target_seconds,
                "target_duration": target_label,
                "added_seconds": round(target_seconds - seconds, 2),
            }
    elif target_label:
        st.session_state.duration_extension = None


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
    """Single Gemini request with bounded retry for transient service errors."""
    content_parts = [types.Part.from_text(text=prompt)]
    content_parts.extend(parts or [])
    contents = [types.Content(role="user", parts=content_parts)]
    last_error = None
    transient_tokens = ("429", "500", "502", "503", "504", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "INTERNAL")
    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(temperature=0.35),
            )
            text = getattr(response, "text", None)
            if not text:
                raise RuntimeError("Gemini mengembalikan respons kosong.")
            return text
        except Exception as exc:
            last_error = exc
            message = str(exc)
            if any(token in message for token in transient_tokens) and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"Gemini gagal setelah retry: {last_error}")


def upload_to_gemini(client, uploaded_file):
    """Upload large reference media through the Gemini Files API.

    Kept for video/reference uploads where inline bytes may be too large.
    """
    if uploaded_file is None:
        return None
    try:
        config = {"display_name": getattr(uploaded_file, "name", "reference") }
        mime = getattr(uploaded_file, "type", None)
        if mime:
            config["mime_type"] = mime
        return client.files.upload(file=uploaded_file, config=config)
    except Exception as exc:
        st.warning(f"File gagal dikirim ke Gemini: {exc}")
        return None


def normalize_frame(uploaded_file):
    """Copy a screenshot into plain bytes so Streamlit reruns cannot invalidate it."""
    if uploaded_file is None:
        return None
    if isinstance(uploaded_file, dict) and uploaded_file.get("data"):
        return uploaded_file
    try:
        data = uploaded_file.getvalue()
        if not data:
            return None
        return {
            "data": data,
            "mime_type": getattr(uploaded_file, "type", None) or "image/jpeg",
            "name": getattr(uploaded_file, "name", "frame.jpg"),
        }
    except Exception:
        return None


def frame_parts(frame):
    frame = normalize_frame(frame)
    if not frame:
        return []
    mime = frame.get("mime_type") or "image/jpeg"
    if not mime.startswith("image/"):
        mime = "image/jpeg"
    return [types.Part.from_bytes(data=frame["data"], mime_type=mime)]


def file_parts(client, uploaded_file):
    """Images always use inline bytes; larger reference media may use Files API."""
    if uploaded_file is None:
        return []
    if isinstance(uploaded_file, dict):
        return frame_parts(uploaded_file)
    mime = getattr(uploaded_file, "type", None) or "application/octet-stream"
    name = getattr(uploaded_file, "name", "").lower()
    if mime.startswith("image/") or name.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return frame_parts(uploaded_file)
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
    st.session_state.scene_prompt_notes = {}
    st.session_state.scene_frames = {}
    st.session_state.current_scene = 1
    st.session_state.storyboard_duration = None
    st.session_state.target_scene_count = None
    st.session_state.target_duration_label = None
    st.session_state.seo = {}


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("UGC Reference Studio")
    st.caption("Referensi → Continuity Analysis → Storyboard → Flow/Veo")
    st.text_input("Gemini API Key", type="password", key="api_key", placeholder="AIza...")
    st.divider()
    if st.button("Beranda", use_container_width=True):
        go("home")
    if st.button("Analisis Referensi", use_container_width=True):
        go("analysis")
    if st.button("Storyboard", use_container_width=True):
        # Storyboard is only a compatibility view; it never reveals future scene prompts.
        go("storyboard")
    if st.button("Prompt Adegan", use_container_width=True):
        go("scenes")
    seo_unlocked = bool(
        st.session_state.analysis
        and scene_count() > 0
        and len(st.session_state.storyboard) >= scene_count()
    )
    if st.button("SEO YouTube", use_container_width=True, disabled=not seo_unlocked):
        go("seo")
    if not seo_unlocked:
        st.caption("🔒 SEO terbuka setelah semua scene selesai.")
    st.divider()
    st.button(
        "Proyek Baru",
        use_container_width=True,
        on_click=reset_project_callback,
    )


# ============================================================
# HOME
# ============================================================
def render_home():
    st.title("UGC Reference Studio")
    st.write(
        "Mesin referensi yang membedah video acuan secara berurutan, memetakan lokasi, "
        "kamera, karakter, properti, aksi, dan keadaan akhir setiap adegan sebelum membuat prompt Flow/Veo."
    )

    st.subheader("1. Referensi")
    st.radio("Jenis referensi", REFERENCE_OPTIONS, horizontal=True, key="reference_type")
    ref_type = st.session_state.reference_type
    if ref_type == "Video":
        uploaded_reference = st.file_uploader(
            "Upload video referensi",
            type=["mp4", "mov", "webm", "avi", "mkv"],
            key=f"ref_upload_{st.session_state.project_nonce}",
        )
        st.session_state.reference_file = uploaded_reference
        st.session_state.reference_files = []

        if uploaded_reference is not None:
            detected = detect_video_duration(uploaded_reference)
            signature = (
                getattr(uploaded_reference, "name", ""),
                getattr(uploaded_reference, "size", None),
            )
            is_new_reference = signature != st.session_state.reference_signature

            if detected is not None:
                st.session_state.detected_reference_duration = detected
                target_label, target_seconds = choose_target_duration(detected)

                # AUTO duration is applied only once when a new reference is uploaded.
                # After that, the user can change the selector without it snapping back
                # on every Streamlit rerun.
                if is_new_reference:
                    st.session_state.reference_signature = signature
                    if target_label:
                        st.session_state.duration_selector = target_label
                        st.session_state.duration = target_label
                        if target_seconds > detected + 0.25:
                            st.session_state.duration_extension = {
                                "reference_seconds": round(detected, 2),
                                "target_seconds": target_seconds,
                                "target_duration": target_label,
                                "added_seconds": round(target_seconds - detected, 2),
                            }
                        else:
                            st.session_state.duration_extension = None

                    # A new reference always starts a fresh analysis/scene sequence.
                    st.session_state.analysis = {}
                    st.session_state.storyboard = []
                    st.session_state.scene_prompts = {}
                    st.session_state.scene_frames = {}
                    st.session_state.current_scene = 1
                    st.session_state.target_scene_count = None
                    st.session_state.target_duration_label = None
                    st.session_state.seo = {}

                if st.session_state.duration_extension:
                    ext = st.session_state.duration_extension
                    st.info(
                        f"Referensi terdeteksi {ext['reference_seconds']:.1f} detik. "
                        f"Target minimum otomatis: {ext['target_duration']} ({ext['target_seconds']} detik / "
                        f"{DURATION_SCENES[ext['target_duration']]} scene). "
                        f"AI akan menambahkan sekitar {ext['added_seconds']:.1f} detik aksi kecil yang natural dan nyambung dengan alur."
                    )

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

    st.subheader("2. Pengaturan Video")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Gaya visual", STYLE_OPTIONS, key="visual_style")
        st.selectbox("Rasio video", ASPECT_OPTIONS, key="aspect_ratio")
    with col2:
        duration_options = list(DURATION_SCENES.keys())
        detected = st.session_state.detected_reference_duration
        minimum_duration = None
        if detected is not None:
            minimum_duration, _ = choose_target_duration(detected)
            minimum_index = duration_options.index(minimum_duration)
            # A reference cannot be analyzed into a shorter target. The selector
            # therefore starts at the automatic minimum and only offers equal or
            # longer durations. This is evaluated BEFORE the widget is created.
            duration_options = duration_options[minimum_index:]
            if st.session_state.duration_selector not in duration_options:
                st.session_state.duration_selector = minimum_duration

        selected_duration = st.selectbox(
            "Durasi video",
            duration_options,
            key="duration_selector",
        )
        st.session_state.duration = selected_duration
        st.text_area(
            "Instruksi tambahan",
            key="custom_instruction",
            height=100,
            placeholder="Contoh: ending lebih lucu, tempo tetap cepat, ekspresi lebih jelas.",
        )

    n = scene_count()
    detected = st.session_state.detected_reference_duration
    if detected is not None:
        chosen_seconds = DURATION_SCENES[st.session_state.duration] * 8
        if chosen_seconds + 0.25 < detected:
            st.warning(
                f"Durasi {st.session_state.duration} lebih pendek dari referensi ({detected:.1f} detik). "
                "Untuk menjaga alur referensi, target tidak boleh lebih pendek dari durasi sumber. "
                "Pilih durasi yang sama atau lebih panjang dari target minimum otomatis."
            )
        else:
            st.info(
                f"{st.session_state.duration} = {n} adegan. Setiap adegan sekitar 8 detik. "
                "Jumlah adegan hanya membagi waktu; alur tidak boleh melompat."
            )
    else:
        st.info(
            f"{st.session_state.duration} = {n} adegan. Setiap adegan sekitar 8 detik. "
            "Jumlah adegan hanya membagi waktu; alur tidak boleh melompat."
        )

    st.subheader("3. Prinsip Continuity")
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

    if st.button("ANALISIS REFERENSI", type="primary", use_container_width=True):
        run_analysis()


# ============================================================
# REFERENCE ANALYSIS — TEMPORAL + SPATIAL + STATE
# ============================================================
def run_analysis():
    client = get_client()
    if not client:
        return
    parts = reference_parts(client)
    if not parts:
        st.warning("Masukkan atau upload referensi terlebih dahulu.")
        return

    # The Home selector already prevents a target shorter than the reference.
    # Re-check here defensively, but never write to a widget key during the same run.
    detected = st.session_state.detected_reference_duration
    if detected is not None:
        min_label, min_seconds = choose_target_duration(detected)
        chosen_seconds = DURATION_SCENES[st.session_state.duration] * 8
        if min_label and chosen_seconds + 0.25 < detected:
            st.session_state.duration = min_label
            st.session_state.duration_extension = {
                "reference_seconds": round(detected, 2),
                "target_seconds": min_seconds,
                "target_duration": min_label,
                "added_seconds": round(min_seconds - detected, 2),
            }
            st.warning(
                f"Referensi {detected:.1f} detik membutuhkan minimal {min_label}. "
                f"Target proyek dikunci ke {min_label} saat analisis."
            )

    target_scenes = DURATION_SCENES[st.session_state.duration]
    extension = st.session_state.duration_extension or {}
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

DURATION EXTENSION:
{json.dumps(extension, ensure_ascii=False)}
Jika reference lebih pendek dari target, tentukan satu titik paling natural untuk menyisipkan micro-action tambahan.
Micro-action harus aman, singkat, menarik/lucu/menumbuhkan rasa penasaran, punya sebab-akibat, dan berakhir dalam state yang langsung menyatu dengan kejadian berikutnya. Jangan menambah lokasi atau karakter acak.
Jika tidak ada extension, jangan menambah kejadian.

Kembalikan HANYA JSON dengan struktur persis:
{{
  "ringkasan": "...",
  "niche": "...",
  "hook": "...",
  "sebab_akibat": "...",
  "tujuan_emosi": "...",
  "pacing_logic": "...",
  "payoff": "...",
  "duration_extension_plan": "...",
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
            data.setdefault("duration_extension_plan", "")
            data["karakter_utama"] = deepcopy(CHARACTER_LOCK)
            st.session_state.analysis = data
            st.session_state.character = deepcopy(CHARACTER_LOCK)
            invalidate_from_analysis()
            # Freeze the project duration/scene count at analysis time.
            st.session_state.target_scene_count = target_scenes
            st.session_state.target_duration_label = st.session_state.duration
            go("analysis")
        except Exception as exc:
            st.error(f"Analisis gagal: {exc}")


# ============================================================
# ANALYSIS PAGE
# ============================================================
def render_analysis():
    st.title("Analisis Referensi + Continuity Map")
    analysis = st.session_state.analysis
    if not analysis:
        st.info("Belum ada analisis. Kembali ke Beranda dan analisis referensi.")
        return

    if st.session_state.duration_extension:
        ext = st.session_state.duration_extension
        st.info(
            f"Duration extension aktif: {ext['reference_seconds']:.1f}s → {ext['target_duration']} "
            f"({ext['target_seconds']}s). AI mengisi sekitar {ext['added_seconds']:.1f}s dengan micro-action yang menyatu dengan alur."
        )

    st.info(
        f"Target proyek terkunci: {st.session_state.target_duration_label or st.session_state.duration} "
        f"→ {scene_count()} scene. Jumlah scene tidak akan berubah selama proses sequential."
    )

    st.subheader("Alur yang Dikunci")
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

    st.subheader("World / Geography Lock")
    st.write(f"**Lokasi utama:** {safe_text(world.get('lokasi_utama'))}")
    st.write(f"**Geografi:** {safe_text(world.get('geografi'))}")
    st.write(f"**Elemen tetap:** {safe_text(world.get('elemen_tetap'))}")
    st.write(f"**Titik masuk/keluar:** {safe_text(world.get('titik_masuk_keluar'))}")
    st.write(f"**Aturan lokasi:** {safe_text(world.get('aturan_lokasi'))}")

    st.subheader("Camera Lock")
    for label, key in [
        ("Posisi", "posisi"),
        ("Tinggi", "tinggi"),
        ("Arah pandang", "arah_pandang"),
        ("Framing", "framing"),
        ("Perspektif/lensa", "perspektif_lensa"),
        ("Gerakan", "gerakan"),
    ]:
        st.write(f"**{label}:** {safe_text(camera.get(key))}")

    st.subheader("Character Lock")
    st.write(f"**Nama:** {CHARACTER_LOCK['nama']}")
    st.write(f"**Visual:** {CHARACTER_LOCK['identitas_visual']}")
    st.warning("Milo tidak boleh berubah identitas. Posisi dan keadaan Milo boleh berubah hanya karena aksi cerita.")

    beats = analysis.get("temporal_breakdown", [])
    st.subheader("Temporal Blueprint")
    st.success(
        f"Blueprint {len(beats)} beat sudah dianalisis dan disimpan sebagai referensi internal. "
        "Beat tidak ditampilkan sebagai daftar scene agar workflow tetap satu-per-satu."
    )
    st.info(
        "Alur sekarang: Scene 1 → generate → upload screenshot frame terakhir → Scene 2 → generate → "
        "upload screenshot → Scene 3, dan seterusnya. Tidak ada prompt semua scene sekaligus."
    )
    if st.button("MULAI SCENE 1", type="primary", use_container_width=True):
        st.session_state.current_scene = 1
        go("scenes")


# ============================================================
# SEQUENTIAL SCENE ENGINE
# ============================================================
def scene_contract_prompt(scene_number, previous_frame_exists=False):
    analysis = st.session_state.analysis
    n = scene_count()
    beats = analysis.get("temporal_breakdown", [])
    previous_contract = st.session_state.storyboard[-1] if st.session_state.storyboard else {}
    frame_note = (
        "A last-frame screenshot from the previous generated scene will be supplied. "
        "Treat that image as the strongest visual starting-state reference."
        if previous_frame_exists else
        "There is no previous generated scene. Start from the reference's initial state."
    )
    return f"""
Anda adalah continuity supervisor untuk Tale Of Paw.
Buat HANYA contract untuk SCENE {scene_number} dari total {n} scene.
JANGAN membuat contract scene lain. JANGAN membuat prompt video di tahap ini.

{frame_note}

TUJUAN UTAMA:
Scene {scene_number} harus merupakan potongan sekitar 8 detik yang benar-benar terjadi setelah
scene sebelumnya. Tidak boleh terasa seperti adegan baru yang berdiri sendiri.

ATURAN KERAS:
1. Gunakan temporal_breakdown sebagai blueprint internal, tetapi hanya keluarkan Scene {scene_number}.
2. Scene 1 dimulai dari initial state referensi.
3. Scene 2+ WAJIB dimulai dari END STATE scene sebelumnya.
4. Untuk Scene 2+, screenshot frame terakhir scene sebelumnya adalah bukti visual utama.
5. Jangan teleport Milo, properti, kamera, pintu, furnitur, atau lokasi.
6. Setiap perubahan wajib mempunyai CAUSE dan ACTION yang jelas.
7. Jangan menambahkan karakter/properti/lokasi baru kecuali memang sudah ada di referensi atau
   diperlukan oleh duration_extension_plan dan masuk secara natural.
8. END STATE scene ini harus jelas dan stabil karena akan menjadi START STATE scene berikutnya.
9. Pertahankan identitas Milo secara persis.
10. Jika duration extension aktif, hanya gunakan micro-action yang sudah direncanakan dalam
    duration_extension_plan; micro-action harus menjadi jembatan natural, bukan filler.
11. Jangan membuat ending yang memotong kontinuitas atau memindahkan kamera secara tiba-tiba.
12. Semua nilai JSON Bahasa Indonesia.

CHARACTER LOCK:
{json.dumps(CHARACTER_LOCK, ensure_ascii=False, indent=2)}

WORLD LOCK:
{json.dumps(analysis.get('world_lock', {}), ensure_ascii=False, indent=2)}

CAMERA LOCK:
{json.dumps(analysis.get('camera_lock', {}), ensure_ascii=False, indent=2)}

TEMPORAL BLUEPRINT INTERNAL:
{json.dumps(beats, ensure_ascii=False, indent=2)}

DURATION EXTENSION:
{json.dumps(st.session_state.duration_extension or {}, ensure_ascii=False, indent=2)}

PREVIOUS SCENE END STATE:
{json.dumps(previous_contract.get('end_state', {}), ensure_ascii=False, indent=2)}

Kembalikan HANYA JSON dengan struktur:
{{
  "nomor": {scene_number},
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
  "kontinuitas": "...",
  "kamera": "...",
  "audio": "...",
  "transisi": "..."
}}
"""


def ask_with_image_fallback(client, prompt, frame, purpose):
    """Try the screenshot as inline bytes, then fall back to its already-grounded contract.

    A 404/NOT_FOUND from the image request is treated as a request-level failure, not
    as evidence that the screenshot itself is invalid. This prevents Scene 2 from
    crashing the whole workflow.
    """
    parts = frame_parts(frame) if frame else []
    try:
        return ask(client, prompt, parts), False
    except Exception as exc:
        message = str(exc)
        if frame and ("404" in message or "NOT_FOUND" in message):
            fallback = (
                prompt
                + "\n\nThe previous scene screenshot is already stored and was used to establish the "
                  "current continuity contract. Do not request or invent another image. "
                  "Generate only from the contract and locked state already supplied above."
            )
            return ask(client, fallback, []), True
        raise RuntimeError(f"{purpose} gagal: {message}") from exc


def generate_scene_contract(scene_number):
    client = get_client()
    if not client:
        return False
    n = scene_count()
    if scene_number < 1 or scene_number > n:
        st.error(f"Nomor scene tidak valid: {scene_number}.")
        return False
    if scene_number > 1 and not st.session_state.scene_frames.get(scene_number - 1):
        st.warning(f"Scene {scene_number} terkunci. Upload screenshot akhir Scene {scene_number - 1} dulu.")
        return False

    previous_frame = st.session_state.scene_frames.get(scene_number - 1)
    prompt = scene_contract_prompt(scene_number, previous_frame is not None)
    with st.spinner(f"Menyusun contract Scene {scene_number}..."):
        try:
            raw, used_fallback = ask_with_image_fallback(
                client, prompt, previous_frame, f"Contract Scene {scene_number}"
            )
            scene = extract_json(raw)
            if not isinstance(scene, dict):
                raise ValueError("AI tidak mengembalikan object scene yang valid.")
            scene["nomor"] = scene_number
            scene.setdefault("waktu", f"{(scene_number - 1) * 8:02d}-{scene_number * 8:02d}")
            scene.setdefault("start_state", {})
            scene.setdefault("end_state", {})
            scene.setdefault("cause", "")
            scene.setdefault("aksi", "")
            scene.setdefault("kontinuitas", "")
            scene["_image_fallback_used"] = bool(used_fallback)
            if not scene["start_state"] or not scene["end_state"]:
                raise ValueError(f"Scene {scene_number} tidak memiliki START STATE/END STATE lengkap.")

            # Never let AI rewrite already completed scenes.
            if len(st.session_state.storyboard) >= scene_number:
                st.session_state.storyboard[scene_number - 1] = scene
            else:
                st.session_state.storyboard.append(scene)
            return True
        except Exception as exc:
            st.error(f"Contract Scene {scene_number} gagal dibuat: {exc}")
            return False


def ask_scene_prompt(client, prompt, previous_frame):
    return ask_with_image_fallback(client, prompt, previous_frame, "Prompt adegan")


def generate_scene_prompt(scene_number):
    client = get_client()
    if not client:
        return False
    scenes = st.session_state.storyboard
    ready, reason = scene_ready_for_prompt(scene_number)
    if not ready:
        st.warning(reason)
        return False

    if scene_number > 1 and not st.session_state.scene_frames.get(scene_number - 1):
        st.warning(f"Prompt Scene {scene_number} terkunci. Upload screenshot akhir Scene {scene_number - 1} terlebih dahulu.")
        return False

    scene = scenes[scene_number - 1]
    previous_frame = st.session_state.scene_frames.get(scene_number - 1)
    analysis = st.session_state.analysis
    previous = scenes[scene_number - 2] if scene_number > 1 else {}

    prompt = f"""
Write ONE production-ready Google Flow / Veo prompt in ENGLISH for Scene {scene_number} only.
This is a CONTINUATION TASK, not a new concept.

ABSOLUTE CONTINUITY RULES:
- The opening image must match the previous scene's final visual state exactly when a previous scene exists.
- Use the uploaded last-frame screenshot as the strongest visual reference for Scene {scene_number} when supplied.
- Never teleport or relocate Milo, props, furniture, doors, windows, vehicles, or camera.
- Never introduce a new location or unexplained object/person.
- Any movement must be caused by the visible action.
- Preserve left/right/front/back geography.
- Preserve camera position and perspective unless a continuous camera move is explicitly required.
- Milo must remain exactly the same kitten.
- The final image must clearly establish the END STATE below for the next scene.
- Do not create an abrupt cut that destroys spatial continuity.

MILO LOCK:
{CHARACTER_LOCK_EN}

WORLD LOCK:
{json.dumps(analysis.get('world_lock', {}), ensure_ascii=False, indent=2)}

CAMERA LOCK:
{json.dumps(analysis.get('camera_lock', {}), ensure_ascii=False, indent=2)}

CURRENT SCENE CONTRACT:
{json.dumps(scene, ensure_ascii=False, indent=2)}

PREVIOUS SCENE CONTRACT:
{json.dumps(previous, ensure_ascii=False, indent=2)}

STYLE: {st.session_state.visual_style}
ASPECT: {st.session_state.aspect_ratio}

Write one detailed English paragraph. Include opening composition, fixed geography, Milo's exact appearance,
continuous cause-and-effect action, camera movement, lighting continuity, sound when useful, and the exact final state.
Do not add anything outside the contracts.
"""
    with st.spinner(f"Membuat prompt Scene {scene_number}..."):
        try:
            result, used_text_fallback = ask_scene_prompt(client, prompt, previous_frame)
            result = result.strip()
            if not result:
                raise ValueError("Prompt kosong.")
            st.session_state.scene_prompts[scene_number] = result
            if used_text_fallback:
                st.session_state.setdefault("scene_prompt_notes", {})
                st.session_state.scene_prompt_notes[scene_number] = (
                    "Screenshot sudah dipakai saat membuat contract scene ini. "
                    "Gemini menolak pengiriman gambar ulang pada request prompt, jadi prompt dibuat dari contract yang sudah screenshot-grounded."
                )
            return True
        except Exception as exc:
            st.error(f"Prompt Scene {scene_number} gagal: {exc}")
            return False


def render_storyboard():
    """Storyboard is now a single active scene contract, not a dump of all scenes."""
    st.title("Storyboard — Sequential Continuity")
    if not st.session_state.analysis:
        st.info("Analisis referensi belum tersedia.")
        return

    n = scene_count()
    current = st.session_state.current_scene
    st.progress(current / n)
    st.markdown(f"### SCENE {current} / {n}")

    if current == 1 and not st.session_state.storyboard:
        st.info("Scene 1 belum dibuat. AI sudah menyimpan blueprint referensi secara internal.")
        if st.button("BUAT SCENE 1", type="primary", use_container_width=True):
            if generate_scene_contract(1):
                st.rerun()
        return

    if len(st.session_state.storyboard) < current:
        st.warning(f"Scene {current} belum dibuka. Selesaikan Scene {current - 1} terlebih dahulu.")
        return

    scene = st.session_state.storyboard[current - 1]
    st.subheader(f"Scene {current} — {scene.get('waktu', '')}")
    st.write(f"**Tujuan:** {safe_text(scene.get('tujuan'))}")
    st.write(f"**START STATE:** {safe_text(scene.get('start_state'))}")
    st.write(f"**CAUSE:** {safe_text(scene.get('cause'))}")
    st.write(f"**ACTION:** {safe_text(scene.get('aksi'))}")
    st.write(f"**END STATE:** {safe_text(scene.get('end_state'))}")
    st.write(f"**Continuity:** {safe_text(scene.get('kontinuitas'))}")

    if current not in st.session_state.scene_prompts:
        if st.button(f"BUAT PROMPT SCENE {current}", type="primary", use_container_width=True):
            if generate_scene_prompt(current):
                st.rerun()
    else:
        st.success(f"Prompt Scene {current} siap.")
        st.text_area("Prompt Flow/Veo", st.session_state.scene_prompts[current], height=380)
        st.info("Generate video ini di Flow/Veo. Setelah selesai, upload screenshot frame TERAKHIR di halaman Prompt Adegan.")


def scene_ready_for_prompt(scene_number):
    """Validate the sequential state before any prompt request is allowed."""
    n = scene_count()
    if scene_number < 1 or scene_number > n:
        return False, "Nomor scene di luar target proyek."
    if len(st.session_state.storyboard) < scene_number:
        return False, f"Contract Scene {scene_number} belum tersedia."
    if scene_number > 1 and not st.session_state.scene_frames.get(scene_number - 1):
        return False, f"Screenshot akhir Scene {scene_number - 1} belum tersedia."
    return True, ""


def frame_fingerprint(frame):
    """Small deterministic identity for a screenshot bridge."""
    if not frame or not frame.get("data"):
        return None
    import hashlib
    return hashlib.sha256(frame["data"]).hexdigest()


def store_scene_frame(scene_number, uploaded_file):
    """Store exactly one bridge and invalidate only work after that bridge."""
    frame = normalize_frame(uploaded_file)
    if not frame:
        return False

    fp = frame_fingerprint(frame)
    existing = st.session_state.scene_frames.get(scene_number)
    if existing and existing.get("fingerprint") == fp:
        return False

    frame["fingerprint"] = fp
    st.session_state.scene_frames[scene_number] = frame

    # Anything after this bridge depends on its visual state. Remove it so a
    # replaced screenshot can never leave stale contracts/prompts behind.
    for key in list(st.session_state.scene_prompts):
        if key > scene_number:
            st.session_state.scene_prompts.pop(key, None)
    for key in list(st.session_state.scene_prompt_notes):
        if key > scene_number:
            st.session_state.scene_prompt_notes.pop(key, None)
    while len(st.session_state.storyboard) > scene_number:
        st.session_state.storyboard.pop()
    for key in list(st.session_state.scene_frames):
        if key > scene_number:
            st.session_state.scene_frames.pop(key, None)
    st.session_state.seo = {}
    return True




def validate_bridge(scene_number):
    """Validate that the exact previous scene frame exists and is a real image."""
    frame = st.session_state.scene_frames.get(scene_number)
    if not frame or not frame.get("data"):
        return False, f"Screenshot akhir Scene {scene_number} belum tersedia."
    mime = frame.get("mime_type", "")
    if not mime.startswith("image/"):
        return False, "File bridge bukan gambar yang didukung."
    if len(frame.get("data", b"")) < 128:
        return False, "Screenshot bridge terlalu kecil atau kosong."
    return True, ""
def render_scenes():
    st.title("Prompt Adegan — Sequential Visual Bridge")
    if not st.session_state.analysis:
        st.info("Analisis referensi belum tersedia.")
        return

    n = scene_count()
    current = max(1, min(int(st.session_state.current_scene), n))
    st.session_state.current_scene = current
    st.progress(current / n)
    st.markdown(f"### SCENE {current} / {n}")

    # ------------------------------------------------------------
    # GATE: every scene after Scene 1 requires the previous scene's
    # final screenshot BEFORE its contract/prompt can be created.
    # ------------------------------------------------------------
    if current > 1:
        previous_frame = st.session_state.scene_frames.get(current - 1)
        if not previous_frame:
            st.subheader(f"🔒 Scene {current} terkunci")
            st.info(
                f"Generate Scene {current - 1} di Flow/Veo, lalu upload SCREENSHOT FRAME TERAKHIR. "
                f"Screenshot tersebut menjadi visual bridge wajib untuk membuka Scene {current}."
            )

            uploaded = st.file_uploader(
                f"Upload screenshot FRAME TERAKHIR Scene {current - 1}",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"gate_frame_{st.session_state.project_nonce}_{current}",
            )

            if uploaded is not None:
                frame = normalize_frame(uploaded)
                if frame:
                    fp = frame_fingerprint(frame)
                    existing = st.session_state.scene_frames.get(current - 1)
                    if not existing or existing.get("fingerprint") != fp:
                        frame["fingerprint"] = fp
                        st.session_state.scene_frames[current - 1] = frame
                        # Do not call Gemini merely because the uploader changed.
                        # The explicit validation button below is the transaction
                        # boundary. This prevents upload -> API call -> rerun races.
                        st.session_state.pop(
                            f"frame_validated_{st.session_state.project_nonce}_{current}",
                            None,
                        )
                        st.success("Screenshot tersimpan sebagai visual bridge. Klik VALIDASI untuk membuka scene.")
                    else:
                        st.success("Screenshot bridge sudah tersimpan.")

            if st.session_state.scene_frames.get(current - 1):
                if st.button(
                    f"VALIDASI SCREENSHOT → BUKA SCENE {current}",
                    type="primary",
                    use_container_width=True,
                    key=f"validate_frame_{st.session_state.project_nonce}_{current}",
                ):
                    ok, reason = validate_bridge(current - 1)
                    if not ok:
                        st.error(reason)
                    elif generate_scene_contract(current):
                        st.session_state[f"frame_validated_{st.session_state.project_nonce}_{current}"] = True
                        st.session_state.current_scene = current
                        st.rerun()
            return

    # Scene 1 (or a newly unlocked scene) gets exactly one contract.
    if len(st.session_state.storyboard) < current:
        if generate_scene_contract(current):
            st.rerun()
        return

    scene = st.session_state.storyboard[current - 1]
    st.subheader(f"Scene {current} — {scene.get('waktu', '')}")
    st.write(f"**START STATE:** {safe_text(scene.get('start_state'))}")
    st.write(f"**CAUSE:** {safe_text(scene.get('cause'))}")
    st.write(f"**ACTION:** {safe_text(scene.get('aksi'))}")
    st.write(f"**END STATE:** {safe_text(scene.get('end_state'))}")

    # ------------------------------------------------------------
    # Prompt generation is a separate explicit action.
    # ------------------------------------------------------------
    if current not in st.session_state.scene_prompts:
        if st.button(
            f"BUAT PROMPT SCENE {current}",
            type="primary",
            use_container_width=True,
            key=f"make_prompt_{st.session_state.project_nonce}_{current}",
        ):
            if generate_scene_prompt(current):
                st.rerun()
        return

    st.success(f"Prompt Scene {current} siap.")
    note = st.session_state.scene_prompt_notes.get(current)
    if note:
        st.caption(note)
    st.text_area(
        "Prompt Flow/Veo — Bahasa Inggris",
        st.session_state.scene_prompts[current],
        height=430,
        key=f"prompt_display_{st.session_state.project_nonce}_{current}",
    )

    # ------------------------------------------------------------
    # Bridge upload for the next scene. Uploading alone NEVER opens the
    # next scene; the user explicitly confirms the bridge.
    # ------------------------------------------------------------
    if current < n:
        st.divider()
        st.subheader(f"Lanjut ke Scene {current + 1}")
        st.info(
            f"Generate Scene {current} di Flow/Veo. Ambil SCREENSHOT FRAME TERAKHIR, "
            f"upload di bawah, lalu konfirmasi. Baru Scene {current + 1} terbuka."
        )

        next_uploaded = st.file_uploader(
            f"Upload screenshot FRAME TERAKHIR Scene {current}",
            type=["png", "jpg", "jpeg", "webp"],
            key=f"advance_frame_{st.session_state.project_nonce}_{current}",
        )

        if next_uploaded is not None:
            frame = normalize_frame(next_uploaded)
            if frame:
                fp = frame_fingerprint(frame)
                existing = st.session_state.scene_frames.get(current)
                if not existing or existing.get("fingerprint") != fp:
                    frame["fingerprint"] = fp
                    st.session_state.scene_frames[current] = frame
                    # The next scene contract/prompt does not exist yet, so no
                    # downstream data should survive a replacement bridge.
                    for key in list(st.session_state.scene_prompts):
                        if key > current:
                            st.session_state.scene_prompts.pop(key, None)
                    while len(st.session_state.storyboard) > current:
                        st.session_state.storyboard.pop()
                    st.session_state.seo = {}
                st.success("Screenshot Scene terakhir tersimpan sebagai visual bridge.")

            if st.button(
                f"KONFIRMASI FRAME → BUKA SCENE {current + 1}",
                type="primary",
                use_container_width=True,
                key=f"open_next_{st.session_state.project_nonce}_{current}",
            ):
                if validate_bridge(current):
                    st.session_state.current_scene = current + 1
                    st.rerun()
        else:
            st.caption(f"🔒 Scene {current + 1} tetap terkunci sampai screenshot akhir Scene {current} tersedia.")
    else:
        st.success("🎬 Semua scene selesai. Sekarang bisa lanjut ke SEO.")
        if st.button(
            "LANJUT KE SEO",
            type="primary",
            use_container_width=True,
            key=f"finish_seo_{st.session_state.project_nonce}",
        ):
            go("seo")

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
    st.title("SEO YouTube")
    if not st.session_state.analysis:
        st.info("Analisis referensi belum tersedia.")
        return
    if not st.session_state.seo:
        if st.button("BUAT SEO", type="primary", use_container_width=True):
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
