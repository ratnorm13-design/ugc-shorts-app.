import json
import re
import time
import cv2
import hashlib
import os
import tempfile
from copy import deepcopy
from typing import Any

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="UGC Reference Studio", page_icon="🐾", layout="wide")

MODEL_NAME = "gemini-3.6-flash"
APP_VERSION = "5.12.5 — State-Safe Analyze + Auto Remix → Storyboard → Prompt Scene"

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
MAX_SUPPORTED_SECONDS = DURATION_SCENES["5 menit"] * 8

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
    "reference_content_signature": None,
    "reference_type_last": "Video",
    "_reset_requested": False,
    "project_nonce": 0,
    "detected_reference_duration": None,
    "duration_extension": None,
    "target_scene_count": None,
    "target_duration_label": None,
    "custom_instruction": "",
    "scene_custom_instructions": {},
    "scene_prompt_input_signatures": {},
    "analysis": {},
    "emotion_performance": {},
    "reference_fidelity": {},
    "remix_strategy": {},
    "reference_ground_truth": {},
    "character": deepcopy(CHARACTER_LOCK),
    "storyboard": [],
    "scene_prompts": {},
    "scene_prompt_notes": {},
    "scene_frames": {},
    "continuity_bridges": {},
    "current_scene": 1,
    "storyboard_duration": None,
    "seo": {},
    "analysis_project_signature": None,
    "analysis_valid": False,
    "analysis_stale_reason": "",
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
    st.session_state["reference_type_last"] = "Video"
    st.session_state["visual_style"] = STYLE_OPTIONS[0]
    st.session_state["aspect_ratio"] = ASPECT_OPTIONS[0]
    st.session_state["duration_selector"] = "8 detik"
    st.session_state["custom_instruction"] = ""
    st.session_state["analysis_project_signature"] = None
    st.session_state["analysis_valid"] = False
    st.session_state["analysis_stale_reason"] = ""
    st.session_state["scene_custom_instructions"] = {}
    st.session_state["scene_prompt_input_signatures"] = {}
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
    if seconds > MAX_SUPPORTED_SECONDS + 0.25:
        return None, None
    supported = [(scenes * 8, label) for label, scenes in DURATION_SCENES.items()]
    supported.sort()
    for total, label in supported:
        if seconds <= total + 0.25:
            return label, total
    return None, None


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
    # Prefer a server-side secret when deployed; fall back to the sidebar key.
    key = (os.getenv("GEMINI_API_KEY") or st.session_state.api_key or "").strip()
    key = key.strip("`\"' ")
    if not key:
        st.error("Masukkan Gemini API Key terlebih dahulu.")
        return None
    try:
        return genai.Client(api_key=key)
    except Exception as exc:
        message = str(exc)
        if "API_KEY_INVALID" in message or "invalid api key" in message.lower():
            st.error("Gemini API Key tidak valid. Buat/gunakan Auth key yang aktif di Google AI Studio.")
        else:
            st.error(f"Gagal membuat koneksi Gemini: {message}")
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


def ask(client, prompt, parts=None, json_mode=False, google_search=False):
    """Single Gemini request with safe retry behavior.

    Daily free-tier quota errors are never retried because waiting a few seconds
    cannot restore a per-day quota. JSON-producing stages use structured JSON mode;
    prose prompt stages keep normal text output.
    """
    content_parts = [types.Part.from_text(text=prompt)]
    content_parts.extend(parts or [])
    contents = [types.Content(role="user", parts=content_parts)]

    config_kwargs = {}
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"
    if google_search:
        config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]
    last_error = None
    transient_tokens = ("500", "502", "503", "504", "UNAVAILABLE", "INTERNAL")

    for attempt in range(4):
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
            last_error = exc
            message = str(exc)
            upper = message.upper()

            # Authentication/quota/request errors should fail immediately.
            if "API_KEY_INVALID" in upper or "INVALID_API_KEY" in upper:
                raise RuntimeError("API key Gemini tidak valid. Gunakan Auth key yang aktif.") from exc
            if "GENERATE_CONTENT_FREE_TIER_REQUESTS" in upper or "GENERATEREQUESTSPERDAYPERPROJECTPERMODEL-FREETIER" in upper:
                raise RuntimeError("Kuota harian Gemini Free Tier untuk project/model ini sudah habis. Jangan retry otomatis; tunggu reset kuota atau gunakan billing/paid tier.") from exc
            if "429" in upper and ("QUOTA" in upper or "RESOURCE_EXHAUSTED" in upper):
                # A generic 429 may be per-minute or per-day. Do one short retry only
                # when the response does not explicitly identify a daily quota.
                if "PERDAY" not in upper and "PER_DAY" not in upper:
                    if attempt < 3:
                        time.sleep(2 ** attempt)
                        continue
                raise RuntimeError(f"Gemini rate/quota limit: {message}") from exc

            if any(token in upper for token in transient_tokens) and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise

    raise RuntimeError(f"Gemini gagal setelah retry: {last_error}")


def upload_to_gemini(client, uploaded_file):
    """Upload reference media and wait until Gemini marks it ACTIVE.

    Streamlit UploadedFile is first copied to a temporary real file because the
    documented Files API examples upload from a filesystem path. Video files also
    require polling while their media is processed before inference.
    """
    if uploaded_file is None:
        return None

    temp_path = None
    try:
        name = getattr(uploaded_file, "name", "reference.bin")
        suffix = os.path.splitext(name)[1].lower() or ".bin"
        data = uploaded_file.getvalue()
        if not data:
            raise ValueError("File referensi kosong.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(data)
            temp_path = tmp.name

        mime = getattr(uploaded_file, "type", None)
        config_kwargs = {"display_name": name}
        if mime:
            config_kwargs["mime_type"] = mime
        config = types.UploadFileConfig(**config_kwargs)
        remote = client.files.upload(file=temp_path, config=config)

        # Video files can remain PROCESSING after upload. Never send a video URI
        # to generate_content until it is ACTIVE.
        state = getattr(remote, "state", None)
        state_name = getattr(state, "name", str(state or ""))
        deadline = time.time() + 180
        while state_name != "ACTIVE":
            if state_name == "FAILED":
                raise RuntimeError("Gemini gagal memproses file referensi.")
            if time.time() >= deadline:
                raise TimeoutError("Gemini terlalu lama memproses video referensi (lebih dari 180 detik).")
            time.sleep(3)
            remote = client.files.get(name=remote.name)
            state = getattr(remote, "state", None)
            state_name = getattr(state, "name", str(state or ""))

        return remote
    except Exception as exc:
        st.error(f"File referensi gagal diproses Gemini: {exc}")
        return None
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass


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
    """Convert an uploaded media item into canonical Gemini Parts."""
    if uploaded_file is None:
        return []
    if isinstance(uploaded_file, dict):
        return frame_parts(uploaded_file)

    mime = getattr(uploaded_file, "type", None) or "application/octet-stream"
    name = getattr(uploaded_file, "name", "").lower()
    if mime.startswith("image/") or name.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return frame_parts(uploaded_file)

    remote = upload_to_gemini(client, uploaded_file)
    if not remote:
        return []
    file_uri = getattr(remote, "uri", None)
    file_mime = getattr(remote, "mime_type", None) or mime
    if not file_uri:
        return []

    # For short video references, sample above the default 1 FPS so fast reactions
    # are less likely to disappear. The API documents video_metadata on file_data.
    fps = 2.0
    duration = st.session_state.get("detected_reference_duration")
    if duration and duration <= 30:
        fps = 3.0
    elif duration and duration > 120:
        fps = 1.0

    if file_mime.startswith("video/"):
        return [
            types.Part(
                file_data=types.FileData(file_uri=file_uri, mime_type=file_mime),
                video_metadata=types.VideoMetadata(fps=fps),
            )
        ]
    return [types.Part.from_uri(file_uri=file_uri, mime_type=file_mime)]



def reference_keyframe_budget(duration_seconds):
    """Choose an adaptive analysis-frame budget from the actual source duration.

    The original video is always the primary evidence. Keyframes are an audit
    layer, so the budget scales with source duration rather than assuming a
    fixed 16-second clip. The practical ceiling keeps a 5-minute reference
    from exploding the multimodal request while still giving roughly scene-level
    temporal coverage.
    """
    try:
        duration = max(0.0, float(duration_seconds))
    except (TypeError, ValueError):
        duration = 0.0
    if duration <= 0:
        return 8

    # Roughly one baseline evidence frame per ~8 seconds, with extra coverage
    # for transitions/reactions. Keep enough frames for very short clips too.
    estimated_scenes = max(1, int((duration + 7.999) // 8))
    budget = int(round(estimated_scenes * 1.5)) + 2
    return max(6, min(48, budget))


def _select_adaptive_timestamps(cap, duration, budget):
    """Select timeline + motion-peak timestamps, deterministically.

    This is intentionally lightweight OpenCV analysis: it does not try to
    understand the scene semantically. It only helps ensure that fast motion,
    abrupt reactions, impacts, prop changes, and transitions are represented
    alongside the original video.
    """
    if duration <= 0 or budget <= 0:
        return []

    # Baseline timeline: approximately one evidence point per source scene,
    # plus endpoints. This scales from seconds to the full 5-minute limit.
    baseline_count = max(3, min(budget, int(round(duration / 8.0)) + 1))
    baseline = [0.0] if baseline_count == 1 else [
        duration * i / (baseline_count - 1) for i in range(baseline_count)
    ]

    # Low-cost motion scan. Sample about every 0.5s, but never more than 180
    # probes. Motion score is frame-to-frame grayscale difference at low res.
    probe_count = max(12, min(180, int(round(duration * 2.0)) + 1))
    probe_times = [0.0] if probe_count == 1 else [
        duration * i / (probe_count - 1) for i in range(probe_count)
    ]
    scored = []
    previous = None
    for ts in probe_times:
        safe_ts = max(0.0, min(float(ts), max(0.0, duration - 0.02)))
        cap.set(cv2.CAP_PROP_POS_MSEC, safe_ts * 1000.0)
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        small = cv2.resize(frame, (96, 54), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        if previous is None:
            score = 0.0
        else:
            score = float(cv2.absdiff(gray, previous).mean())
        previous = gray
        scored.append((score, safe_ts))

    # Prefer local motion peaks over arbitrary global maxima. A peak must be
    # separated from an already selected timestamp so one chaotic moment does
    # not consume the whole budget.
    peak_candidates = []
    for i, (score, ts) in enumerate(scored):
        left = scored[i - 1][0] if i > 0 else score
        right = scored[i + 1][0] if i + 1 < len(scored) else score
        if score >= left and score >= right:
            peak_candidates.append((score, ts))
    peak_candidates.sort(key=lambda x: x[0], reverse=True)

    selected = list(baseline)
    min_gap = max(0.75, min(4.0, duration / max(4.0, budget / 2.0)))
    for _, ts in peak_candidates:
        if len(selected) >= budget:
            break
        if all(abs(ts - existing) >= min_gap for existing in selected):
            selected.append(ts)

    # If motion peaks were insufficient, fill remaining slots uniformly so the
    # entire source duration remains covered.
    if len(selected) < budget:
        fill_count = budget * 2
        fillers = [duration * i / max(1, fill_count - 1) for i in range(fill_count)]
        for ts in fillers:
            if len(selected) >= budget:
                break
            if all(abs(ts - existing) >= min_gap for existing in selected):
                selected.append(ts)

    selected = sorted({round(max(0.0, min(ts, max(0.0, duration - 0.02))), 3) for ts in selected})
    return selected[:budget]


def extract_reference_keyframes(uploaded_file, max_frames=None):
    """Extract adaptive timestamped keyframes from the original video.

    The source video remains the primary multimodal evidence. The number of
    stills scales with the actual reference duration and is supplemented by
    lightweight motion-peak sampling. This works for short clips and long
    references up to the project's 5-minute ceiling without hardcoding a
    16-second assumption.
    """
    if uploaded_file is None:
        return []
    name = getattr(uploaded_file, "name", "reference.mp4")
    data = uploaded_file.getvalue()
    if not data:
        return []
    suffix = os.path.splitext(name)[1].lower() or ".mp4"
    temp_path = None
    cap = None
    frames = []
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(data)
            temp_path = tmp.name
        cap = cv2.VideoCapture(temp_path)
        if not cap.isOpened():
            return []
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = float(frame_count / fps) if fps > 0 and frame_count > 0 else None
        if not duration or duration <= 0:
            duration = st.session_state.get("detected_reference_duration")
        if not duration or duration <= 0:
            return []

        budget = int(max_frames) if max_frames else reference_keyframe_budget(duration)
        budget = max(6, min(48, budget))
        timestamps = _select_adaptive_timestamps(cap, duration, budget)
        for ts in timestamps:
            cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000.0)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
            if not ok:
                continue
            frames.append({
                "timestamp": round(ts, 3),
                "data": encoded.tobytes(),
                "mime_type": "image/jpeg",
            })
        return frames
    except Exception:
        return []
    finally:
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass


def reference_analysis_parts(client):
    """Build the reference analysis evidence bundle.

    For video references: Gemini receives the original video PLUS adaptive, timestamped
    keyframes scaled to the actual source duration. This is intentionally analysis-only;
    sequential scene generation still uses the last-frame bridge workflow.
    """
    if st.session_state.reference_type != "Video" or not st.session_state.reference_file:
        return reference_parts(client)
    video_parts = file_parts(client, st.session_state.reference_file)
    if not video_parts:
        return []
    keyframes = extract_reference_keyframes(st.session_state.reference_file)
    parts = list(video_parts)
    for item in keyframes:
        ts = item["timestamp"]
        parts.append(types.Part.from_text(text=(
            f"REFERENCE KEYFRAME — timestamp {ts:.2f}s. "
            "This frame is audit evidence from the original video at this exact point. "
            "Do not treat it as a new reference or separate scene."
        )))
        parts.append(types.Part.from_bytes(data=item["data"], mime_type=item["mime_type"]))
    return parts


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
        text = f"REFERENSI TEKS PENGGUNA:\n{st.session_state.reference_text}"
        return [types.Part.from_text(text=text)]
    return []


def current_project_signature():
    """Return a deterministic fingerprint for every setting that affects analysis/storyboard/prompt output."""
    payload = {
        "reference_type": st.session_state.get("reference_type"),
        "reference_content_signature": st.session_state.get("reference_content_signature"),
        "visual_style": st.session_state.get("visual_style"),
        "aspect_ratio": st.session_state.get("aspect_ratio"),
        "duration": st.session_state.get("duration"),
        "custom_instruction": st.session_state.get("custom_instruction", ""),
        "character_lock": CHARACTER_LOCK,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def mark_analysis_stale_if_needed():
    """Invalidate downstream artifacts when an analyzed project configuration changes."""
    saved = st.session_state.get("analysis_project_signature")
    if not saved or not st.session_state.get("analysis_valid"):
        return False
    current = current_project_signature()
    if current == saved:
        return False

    st.session_state.analysis_valid = False
    st.session_state.analysis_stale_reason = (
        "Konfigurasi project berubah setelah analisis. "
        "Jalankan ANALYZE + AUTO REMIX lagi sebelum membuat storyboard atau prompt scene."
    )
    invalidate_from_analysis()
    return True


def require_current_analysis():
    """Hard gate: no storyboard/scene generation may use stale analysis."""
    if not st.session_state.get("analysis"):
        return False, "Analisis belum tersedia. Jalankan ANALYZE + AUTO REMIX terlebih dahulu."
    mark_analysis_stale_if_needed()
    if not st.session_state.get("analysis_valid"):
        return False, st.session_state.get("analysis_stale_reason") or (
            "Analisis tidak lagi sinkron dengan konfigurasi project. "
            "Jalankan ANALYZE + AUTO REMIX lagi."
        )
    return True, ""


def invalidate_from_analysis():
    """Clear every artifact derived from the current reference analysis."""
    st.session_state.storyboard = []
    st.session_state.scene_prompts = {}
    st.session_state.scene_prompt_notes = {}
    st.session_state.scene_prompt_input_signatures = {}
    st.session_state.scene_frames = {}
    st.session_state.continuity_bridges = {}
    st.session_state.current_scene = 1
    st.session_state.storyboard_duration = None
    st.session_state.target_scene_count = None
    st.session_state.target_duration_label = None
    st.session_state.seo = {}


def invalidate_from_reference_change(clear_duration=True):
    """Invalidate all reference-derived state after a reference/type change."""
    st.session_state.analysis = {}
    st.session_state.emotion_performance = {}
    st.session_state.reference_fidelity = {}
    st.session_state.remix_strategy = {}
    st.session_state.reference_ground_truth = {}
    st.session_state.character = deepcopy(CHARACTER_LOCK)
    invalidate_from_analysis()
    st.session_state.detected_reference_duration = None
    st.session_state.duration_extension = None
    st.session_state.reference_signature = None
    st.session_state.analysis_project_signature = None
    st.session_state.analysis_valid = False
    st.session_state.analysis_stale_reason = ""
    if clear_duration:
        st.session_state.duration = "8 detik"
        st.session_state.duration_selector = "8 detik"


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("UGC Reference Studio")
    st.caption(f"Referensi → Continuity Analysis → Storyboard → Flow/Veo · v{APP_VERSION.split(" — ")[0]}")
    st.text_input("Gemini API Key", type="password", key="api_key", placeholder="AIza...")
    st.divider()
    if st.button("Beranda", use_container_width=True):
        go("home")
    if st.button("Analyze + Auto Remix", use_container_width=True):
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
    previous_type = st.session_state.get("reference_type_last", st.session_state.reference_type)
    st.radio("Jenis referensi", REFERENCE_OPTIONS, horizontal=True, key="reference_type")
    ref_type = st.session_state.reference_type

    # Changing the input mode is a new reference even if the same widget values
    # happen to remain. Clear old analysis before accepting the new source.
    if ref_type != previous_type:
        invalidate_from_reference_change(clear_duration=True)
        st.session_state.reference_text = ""
        st.session_state.reference_type_last = ref_type
    else:
        st.session_state.reference_type_last = ref_type

    if ref_type == "Video":
        uploaded_reference = st.file_uploader(
            "Upload video referensi",
            type=["mp4", "mov", "webm", "avi", "mkv"],
            key=f"ref_upload_{st.session_state.project_nonce}",
        )
        st.session_state.reference_file = uploaded_reference
        st.session_state.reference_files = []

        if uploaded_reference is None:
            if st.session_state.reference_content_signature is not None:
                invalidate_from_reference_change(clear_duration=True)
                st.session_state.reference_content_signature = None
        else:
            raw_reference = uploaded_reference.getvalue()
            signature = (
                "Video",
                getattr(uploaded_reference, "name", ""),
                len(raw_reference),
                hashlib.sha256(raw_reference).hexdigest(),
            )
            is_new_reference = signature != st.session_state.reference_content_signature
            detected = detect_video_duration(uploaded_reference)

            if detected is not None and detected > MAX_SUPPORTED_SECONDS + 0.25:
                if is_new_reference:
                    invalidate_from_reference_change(clear_duration=False)
                    st.session_state.reference_content_signature = signature
                    st.session_state.reference_signature = signature
                st.error(
                    f"Referensi {detected:.1f} detik melebihi batas maksimum proyek "
                    f"({MAX_SUPPORTED_SECONDS} detik / 5 menit). Potong referensi menjadi 5 menit atau kurang."
                )
            elif is_new_reference:
                invalidate_from_reference_change(clear_duration=False)
                st.session_state.reference_content_signature = signature
                st.session_state.reference_signature = signature

            if detected is not None:
                st.session_state.detected_reference_duration = detected
                target_label, target_seconds = choose_target_duration(detected)
                if is_new_reference and target_label:
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

            if st.session_state.duration_extension:
                ext = st.session_state.duration_extension
                st.info(
                    f"Referensi terdeteksi {ext['reference_seconds']:.1f} detik. "
                    f"Target minimum otomatis: {ext['target_duration']} ({ext['target_seconds']} detik / "
                    f"{DURATION_SCENES[ext['target_duration']]} scene). "
                    f"AI akan menambahkan sekitar {ext['added_seconds']:.1f} detik aksi kecil yang natural dan nyambung dengan alur."
                )

    elif ref_type == "Screenshot":
        uploaded_references = st.file_uploader(
            "Upload screenshot referensi secara berurutan",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key=f"ref_screens_{st.session_state.project_nonce}",
        )
        st.session_state.reference_files = uploaded_references or []
        st.session_state.reference_file = None

        if not uploaded_references:
            if st.session_state.reference_content_signature is not None:
                invalidate_from_reference_change(clear_duration=True)
                st.session_state.reference_content_signature = None
        else:
            signatures = []
            for item in uploaded_references:
                data = item.getvalue()
                signatures.append((
                    getattr(item, "name", ""),
                    len(data),
                    hashlib.sha256(data).hexdigest(),
                ))
            signature = ("Screenshot", tuple(signatures))
            if signature != st.session_state.reference_content_signature:
                invalidate_from_reference_change(clear_duration=False)
                st.session_state.reference_content_signature = signature

    else:
        reference_text = st.text_area(
            "Tulis referensi atau ide",
            value=st.session_state.reference_text,
            height=160,
        )
        st.session_state.reference_text = reference_text
        st.session_state.reference_file = None
        st.session_state.reference_files = []

        if not reference_text.strip():
            if st.session_state.reference_content_signature is not None:
                invalidate_from_reference_change(clear_duration=True)
                st.session_state.reference_content_signature = None
        else:
            signature = ("Teks / ide", hashlib.sha256(reference_text.encode("utf-8")).hexdigest())
            if signature != st.session_state.reference_content_signature:
                invalidate_from_reference_change(clear_duration=False)
                st.session_state.reference_content_signature = signature

    st.subheader("2. Pengaturan Video")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Gaya visual", STYLE_OPTIONS, key="visual_style")
        st.selectbox("Rasio video", ASPECT_OPTIONS, key="aspect_ratio")
    with col2:
        duration_options = list(DURATION_SCENES.keys())
        detected = st.session_state.detected_reference_duration
        minimum_duration = None
        if detected is not None and detected <= MAX_SUPPORTED_SECONDS + 0.25:
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

        # Keep duration-extension metadata synchronized when the user chooses a
        # longer target after the automatic minimum was calculated.
        detected = st.session_state.detected_reference_duration
        if detected is not None:
            chosen_seconds = DURATION_SCENES[selected_duration] * 8
            if chosen_seconds > detected + 0.25:
                st.session_state.duration_extension = {
                    "reference_seconds": round(detected, 2),
                    "target_seconds": chosen_seconds,
                    "target_duration": selected_duration,
                    "added_seconds": round(chosen_seconds - detected, 2),
                }
            else:
                st.session_state.duration_extension = None

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
        if detected > MAX_SUPPORTED_SECONDS + 0.25:
            st.error(
                f"Referensi {detected:.1f} detik melebihi batas maksimum 5 menit. "
                "Potong referensi terlebih dahulu sebelum analisis."
            )
        elif chosen_seconds + 0.25 < detected:
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

    if mark_analysis_stale_if_needed():
        st.warning(st.session_state.analysis_stale_reason)

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

    if st.button("ANALYZE + AUTO REMIX", type="primary", use_container_width=True):
        run_analysis()


# ============================================================
# EMOTION PERFORMANCE NORMALIZATION / REPAIR
# ============================================================
def build_fallback_emotion_profile(subject: dict) -> dict:
    """Build a continuity-safe local performance profile without another Gemini call."""
    sid = str(subject.get("id", "")).strip()
    role = str(subject.get("peran") or "supporting")
    baseline = str(subject.get("ekspresi_emosi") or "netral / observatif")
    action = str(subject.get("aksi_perilaku") or "mempertahankan aksi saat ini")
    orientation = str(subject.get("orientasi") or "")
    interactions = subject.get("interaksi_dengan") or []
    if not isinstance(interactions, list):
        interactions = [str(interactions)]
    function = str(subject.get("fungsi_dalam_humor_atau_emosi") or "")

    allowed_roles = {"leader", "contrast", "late_reactor", "support", "reaction"}
    emotional_role = role if role in allowed_roles else "support"
    attention_targets = [str(x) for x in interactions if str(x).strip()] or ["aksi utama / pemicu kejadian"]

    return {
        "subject_id": sid,
        "baseline_emotion": baseline,
        "emotional_role": emotional_role,
        "trigger_map": [
            "Bereaksi terhadap perubahan visual yang benar-benar terjadi pada scene.",
            f"Pemicu utama mengikuti aksi/peran subjek: {action}."
        ],
        "arc": [baseline, "pergeseran perhatian", "reaksi terbaca", "kembali stabil sesuai end state"],
        "facial_performance": [
            f"Pertahankan ekspresi dasar: {baseline}.",
            "Gunakan perubahan mata, alis, mulut/paruh, atau wajah yang terlihat saat pemicu terjadi."
        ],
        "head_and_gaze": [
            f"Pertahankan orientasi awal: {orientation}." if orientation else "Arahkan kepala/pandangan mengikuti pemicu yang benar-benar terlihat.",
            "Perubahan gaze harus mengikuti perhatian subjek, bukan berubah secara acak."
        ],
        "body_performance": [
            f"Lanjutkan perilaku utama: {action}.",
            "Perlihatkan perubahan postur atau ketegangan secara proporsional ketika pemicu terjadi."
        ],
        "hands_or_paws": [
            "Pertahankan posisi tangan/kaki/paw yang sudah ada.",
            "Tambahkan micro-reaction kecil hanya jika secara fisik masuk akal dan tidak merusak continuity."
        ],
        "movement_quality": [
            "Gerakan natural, berkesinambungan, dan cause-driven.",
            "Hindari perpindahan posisi mendadak tanpa sebab visual."
        ],
        "micro_reactions": [
            "glance singkat ke pemicu",
            "perubahan postur kecil",
            "jeda reaksi singkat sebelum kembali ke aksi utama"
        ],
        "attention_targets": attention_targets,
        "timing_logic": (
            "Subjek mempertahankan baseline sampai ada pemicu visual; setelah pemicu, "
            "reaksi meningkat secara bertahap lalu berakhir pada state yang konsisten dengan bridge."
        ),
        "reference_function": function,
        "profile_repaired": True
    }


def normalize_emotion_profiles(data: dict) -> tuple[dict, list[dict]]:
    """Ensure every detected subject has exactly one usable performance profile.

    Missing profiles are repaired locally so a model omission does not waste another
    Gemini request or block the whole analysis. Existing model-generated cues are kept.
    """
    emotion_data = data.get("emotion_performance_analysis")
    if not isinstance(emotion_data, dict):
        raise ValueError("emotion_performance_analysis harus berupa object performance yang lengkap.")

    roster = data.get("subject_roster")
    if not isinstance(roster, list) or not roster:
        raise ValueError("subject_roster harus berupa list hasil deteksi seluruh subjek reference.")

    raw_profiles = emotion_data.get("subject_emotion_profiles", [])
    if not isinstance(raw_profiles, list):
        raise ValueError("subject_emotion_profiles harus berupa list.")

    roster_by_id = {}
    for subject in roster:
        if not isinstance(subject, dict) or not subject.get("id"):
            continue
        roster_by_id[str(subject["id"])] = subject

    profiles_by_id = {}
    repair_log = []
    duplicate_ids = []
    for profile in raw_profiles:
        if not isinstance(profile, dict) or not profile.get("subject_id"):
            continue
        sid = str(profile["subject_id"])
        if sid not in roster_by_id:
            # Unknown profile IDs are rejected later; do not silently attach them.
            profiles_by_id[sid] = profile
            continue
        if sid in profiles_by_id:
            duplicate_ids.append(sid)
            continue
        profiles_by_id[sid] = profile

    for sid, subject in roster_by_id.items():
        if sid not in profiles_by_id:
            profiles_by_id[sid] = build_fallback_emotion_profile(subject)
            repair_log.append({
                "subject_id": sid,
                "reason": "missing_profile",
                "action": "local_fallback",
            })
            continue

        # Fill only genuinely missing fields; never overwrite model-generated cues.
        fallback = build_fallback_emotion_profile(subject)
        profile = profiles_by_id[sid]
        filled = []
        for key, fallback_value in fallback.items():
            if key == "subject_id":
                continue
            value = profile.get(key)
            missing = value is None or value == "" or (isinstance(value, list) and not value)
            if missing:
                profile[key] = deepcopy(fallback_value)
                filled.append(key)
        if filled:
            repair_log.append({
                "subject_id": sid,
                "reason": "incomplete_profile",
                "action": "local_fill_missing_fields",
                "fields": filled,
            })

    if duplicate_ids:
        repair_log.append({
            "subject_id": ",".join(sorted(set(duplicate_ids))),
            "reason": "duplicate_profile",
            "action": "kept_first_profile",
        })

    normalized_profiles = [profiles_by_id[sid] for sid in roster_by_id]
    emotion_data["subject_emotion_profiles"] = normalized_profiles
    if repair_log:
        emotion_data["performance_profile_repaired"] = True
        emotion_data["performance_profile_repair_log"] = repair_log
    else:
        emotion_data["performance_profile_repaired"] = False
        emotion_data["performance_profile_repair_log"] = []

    # Final structural checks after repair.
    roster_ids = set(roster_by_id)
    profile_ids = {str(p.get("subject_id")) for p in normalized_profiles if p.get("subject_id")}
    important_ids = {
        str(x.get("id")) for x in roster
        if isinstance(x, dict) and x.get("wajib_terlihat") is True and x.get("id")
    }
    if important_ids - profile_ids:
        raise ValueError(f"Performance profile tetap hilang setelah repair: {sorted(important_ids - profile_ids)}")
    if profile_ids - roster_ids:
        raise ValueError(f"subject_emotion_profiles mengandung subject_id yang tidak ada di subject_roster: {sorted(profile_ids - roster_ids)}")

    data["emotion_performance_analysis"] = emotion_data
    return data, repair_log


# ============================================================
# REFERENCE ANALYSIS — TEMPORAL + SPATIAL + STATE
# ============================================================
def _parse_time_seconds(value):
    """Parse common mm:ss / ss formats used by the model's temporal blueprint."""
    if value is None:
        return None
    text = str(value).strip()
    match = re.search(r'(\d+):(\d+(?:\.\d+)?)\s*[-–]\s*(\d+):(\d+(?:\.\d+)?)', text)
    if match:
        start = int(match.group(1)) * 60 + float(match.group(2))
        end = int(match.group(3)) * 60 + float(match.group(4))
        return start, end
    match = re.search(r'(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*s?', text, re.I)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None


def temporal_beats_for_scene(scene_number):
    """Return only reference beats overlapping the source-time window for this scene.

    The full temporal blueprint remains in analysis, but scene-level generation receives
    only the relevant beats. This reduces accidental import of later payoff events.
    """
    analysis = st.session_state.get("analysis", {})
    beats = analysis.get("temporal_breakdown", []) or []
    target_start = (scene_number - 1) * 8.0
    target_end = scene_number * 8.0
    selected = []
    for beat in beats:
        if not isinstance(beat, dict):
            continue
        parsed = _parse_time_seconds(beat.get("waktu") or beat.get("source_time") or beat.get("time"))
        if parsed is None:
            continue
        start, end = parsed
        if end > target_start and start < target_end:
            selected.append(beat)
    if selected:
        return selected
    # For extension scenes beyond the source duration, use the extension plan rather
    # than borrowing an arbitrary later beat.
    duration = st.session_state.get("detected_reference_duration")
    if duration is not None and target_start >= float(duration):
        return [{
            "beat": f"extension_scene_{scene_number}",
            "waktu": f"{target_start:.1f}-{target_end:.1f}s",
            "start_state": "lanjutkan END STATE sumber terakhir",
            "action": "micro-action extension yang sudah direncanakan",
            "cause": "mengikuti duration_extension_plan",
            "end_state": "state yang menyatu dengan alur",
            "extension_only": True,
        }]
    return []


def _source_time_window(scene_number):
    return {
        "start_seconds": float((scene_number - 1) * 8),
        "end_seconds": float(scene_number * 8),
        "label": f"{(scene_number - 1) * 8:02d}-{scene_number * 8:02d}s",
    }


def run_analysis():
    client = get_client()
    if not client:
        return

    # Reject an over-limit video before uploading it to Gemini.
    detected = st.session_state.detected_reference_duration
    if detected is not None and detected > MAX_SUPPORTED_SECONDS + 0.25:
        st.error(
            f"Referensi {detected:.1f} detik melebihi batas maksimum proyek "
            f"({MAX_SUPPORTED_SECONDS} detik / 5 menit). Potong referensi terlebih dahulu."
        )
        return

    parts = reference_analysis_parts(client)
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
            # Defensive fallback only; the Home selector normally prevents this.
            st.session_state.duration = min_label
            st.session_state.duration_extension = {
                "reference_seconds": round(detected, 2),
                "target_seconds": min_seconds,
                "target_duration": min_label,
                "added_seconds": round(min_seconds - detected, 2),
            }

    target_scenes = DURATION_SCENES[st.session_state.duration]
    extension = st.session_state.duration_extension or {}
    prompt = f"""
Anda adalah showrunner dan continuity supervisor untuk video pendek komedi sinematik.
Analisis referensi yang diberikan SECARA TEMPORAL dan SPATIAL sebelum membuat storyboard.
Jangan langsung menulis prompt video.

EVIDENCE PRIORITY: video asli adalah sumber utama. Timestamped keyframes yang menyertai video adalah bukti audit tambahan. Bandingkan keyframe awal, tengah, transisi, dan akhir untuk mendeteksi perubahan posisi, ekspresi, prop, motion, debu/efek lingkungan, dan payoff. Jangan menyimpulkan seluruh video dari satu frame.

TUJUAN:
Membangun satu sumber kebenaran (single source of truth) tentang apa yang terjadi,
di mana karakter berada, dari mana objek datang, bagaimana kamera melihat kejadian,
dan bagaimana satu kejadian menyebabkan kejadian berikutnya.

ATURAN KERAS — REFERENCE GROUND TRUTH:
1. VIDEO ASLI adalah sumber kebenaran utama. Timestamped keyframes adalah bukti audit tambahan. Jangan merangkum video hanya dari frame pembuka.
2. Lakukan SELF-AUDIT sebelum output: cek ulang setiap beat terhadap timeline, posisi subjek, kamera, objek, motion, prop, emosi, dan payoff. Jika ada konflik antar-frame, pilih keadaan yang benar-benar terlihat pada timestamp yang relevan dan tandai transisinya.
3. Pisahkan tiga hal: (A) FAKTA YANG TERLIHAT DI REFERENCE, (B) INFERENSI YANG MASIH WAJAR, (C) PENINGKATAN REMIX. Jangan mencampur B/C ke dalam fakta reference.
4. Urutan kejadian harus mengikuti reference. Jangan memindahkan payoff akhir ke scene awal. Jangan membuat kejadian baru untuk "membuat lebih menarik" di dalam reference timeline.
5. Setiap beat WAJIB memiliki START STATE → CAUSE → ACTION → END STATE. END STATE harus konsisten dengan beat berikutnya.
6. Jika suatu objek/subjek baru muncul, catat kapan pertama terlihat dan dari mana ia masuk. Jika hilang, catat kapan dan bagaimana ia keluar/hilang. Jangan menganggap teleport.
7. Deteksi SEMUA subjek penting sepanjang video, bukan hanya subjek yang paling besar pada frame awal.
8. Untuk setiap subjek, bedakan SCREEN POSITION dengan PHYSICAL POSITION. Jangan memakai "kiri/kanan" saja. Gunakan koordinat relatif terhadap kendaraan/ruangan dan terhadap kamera.
9. Jika kendaraan/kabin memiliki kursi, WAJIB buat SEAT MAP: row (front/rear), physical side (driver/passenger/center), screen position, occupant, dan adjacency. Jangan pernah menyebut subject sebagai rear passenger jika sebenarnya berada di front passenger seat.
10. Untuk beberapa subjek yang duduk berdampingan, catat hubungan: SAME ROW, ADJACENT SEAT, DEPTH, dan OCCUPANT. Posisi ini adalah LOCK, bukan sekadar deskripsi.
11. Kamera WAJIB dipetakan sebagai physical camera placement: mounting/handheld position, row, side, height, distance, orientation, framing, perspective/lens feel, dan camera movement. Hubungkan kamera dengan anchor objects seperti steering wheel, dashboard, seats, doors, windows.
12. Jangan mengubah perspektif kamera hanya agar prompt terdengar lebih sinematik. Kamera adalah bagian dari hook bila reference mengandalkannya.
13. MOTION MAP WAJIB memisahkan: vehicle motion, camera motion, background motion, subject inertia, wheel/ground contact, environmental effects, dan direction.
14. Setiap efek seperti debu, asap, air, serpihan, atau gerakan lingkungan WAJIB memiliki EFFECT SOURCE + SOURCE ZONE + DIRECTION + TIMING. Jangan menaruh efek di lokasi lain hanya karena secara visual "bagus".
15. Untuk payoff fisik, catat keadaan tepat SEBELUM, SAAT, dan SESUDAH kejadian. Contoh: vehicle nose/front contact → vehicle stops/halts → dust erupts from the front ground contact zone. Jangan ubah menjadi dust behind the vehicle bila reference menunjukkan sumber di depan.
16. Tandai ACTION-CRITICAL PROP: benda yang digigit, dipegang, ditarik, diinjak, dipakai, atau menjadi pemicu aksi. Catat owner, body contact, posisi, status, first_seen, last_seen, allowed transitions, forbidden changes.
17. Performance harus dianalisis sebagai perilaku yang terlihat: face, eyes, brows, mouth, head, gaze, torso, limbs/paws, grip, posture, movement quality, reaction delay, dan perubahan intensitas. Jangan cukup menulis "confident" atau "panicked".
18. EMOTION TIMELINE harus terikat pada trigger nyata. Gunakan CAUSE → EMOTION → PERFORMANCE → CONSEQUENCE.
19. REACTION HIERARCHY: tentukan siapa yang bereaksi dulu, siapa terlambat, siapa menjadi contrast/comedic foil. Jangan membuat semua subjek bereaksi bersamaan tanpa bukti.
20. HOOK ANALYSIS: jelaskan apa yang terlihat pada 1–3 detik pertama, anomaly, attention anchor, curiosity gap, escalation signal, dan payoff promise. Hook mechanism harus dipertahankan dalam remix.
21. PAYOFF FIDELITY: payoff reference harus tetap terjadi pada bagian waktu yang benar. Remix boleh memperjelas ekspresi/reaction/absurdity, tetapi tidak boleh mengganti causal core atau memajukan payoff.
22. REMIX ENHANCEMENT harus dibatasi. Default: boleh meningkatkan ekspresi, timing reaction, micro-gesture, curiosity, visual comedy, dan readability. JANGAN menambah aksi kausal besar, kendaraan baru, prop baru, perpindahan lokasi, atau event baru kecuali memang diperlukan oleh duration extension dan disebut eksplisit dalam plan.
23. Untuk video yang lebih pendek dari target, extension hanya boleh terjadi SETELAH END STATE reference terakhir. Extension tidak boleh menyisipkan event baru di tengah reference timeline.
24. Untuk setiap target scene, buat SCENE COVERAGE MAP: source_time_window, source_beats, must_preserve, allowed_remix_enhancement, forbidden_drift. Scene berikutnya tidak boleh mengambil beat dari scene lain.
25. Semua nilai JSON Bahasa Indonesia.

REFERENCE FIDELITY SELF-CHECK:
- Apakah posisi fisik setiap subjek benar?
- Apakah seat row dan adjacency benar?
- Apakah kamera benar-benar berada di posisi reference?
- Apakah arah gerak kendaraan dan background konsisten?
- Apakah efek lingkungan berasal dari sumber spatial yang benar?
- Apakah action-critical prop tetap ada?
- Apakah ekspresi/performance mengikuti trigger?
- Apakah payoff berada di waktu yang benar?
- Apakah remix enhancement tidak mengganti causal core?

CHARACTER LOCK:
{json.dumps(CHARACTER_LOCK, ensure_ascii=False, indent=2)}

PENGATURAN:
Gaya visual: {st.session_state.visual_style}
Rasio: {st.session_state.aspect_ratio}
Durasi target: {st.session_state.duration}
Jumlah scene target: {target_scenes}
Durasi reference terdeteksi: {st.session_state.detected_reference_duration}
Instruksi pengguna: {st.session_state.custom_instruction}

DURATION EXTENSION:
{json.dumps(extension, ensure_ascii=False)}
Jika reference lebih pendek dari target, extension hanya ditempatkan SETELAH END STATE reference terakhir.
Micro-action extension harus continuity-safe, tidak boleh mengganti payoff reference atau menyisipkan event baru di tengah timeline.

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
    "baris_ruang_atau_kursi": "...",
    "sisi_fisik": "...",
    "tinggi": "...",
    "jarak": "...",
    "arah_pandang": "...",
    "framing": "...",
    "perspektif_lensa": "...",
    "gerakan": "...",
    "anchor_objects": ["..."],
    "aturan_kamera": ["..."]
  }},
  "subject_roster": [
    {{
      "id": "S1",
      "jenis": "...",
      "peran": "protagonist/co-protagonist/supporting/reaction/background",
      "deskripsi_visual": "...",
      "physical_position": "...",
      "screen_position": "...",
      "depth_layer": "foreground/midground/background",
      "seat_row": "front/rear/not_applicable",
      "seat_side": "driver/passenger/center/not_applicable",
      "adjacent_to": ["S2"],
      "orientasi": "...",
      "ekspresi_emosi": "...",
      "aksi_perilaku": "...",
      "interaksi_dengan": ["..."],
      "fungsi_dalam_humor_atau_emosi": "...",
      "first_seen": "...",
      "last_seen": "...",
      "wajib_terlihat": true
    }}
  ],
  "seat_map": [
    {{
      "seat_id": "seat_front_driver",
      "row": "front",
      "physical_side": "driver",
      "screen_position": "...",
      "occupied_by": "S1",
      "adjacent_seat": "seat_front_passenger"
    }}
  ],
  "object_inventory": [
    {{
      "id": "O1",
      "nama": "...",
      "kategori": "prop/vehicle/furniture/environment/background",
      "physical_position": "...",
      "screen_position": "...",
      "status_awal": "...",
      "fungsi_dalam_aksi": "...",
      "perubahan": "...",
      "first_seen": "...",
      "last_seen": "...",
      "wajib_konsisten": true
    }}
  ],
  "spatial_layout": {{
    "coordinate_system": "screen + physical/world relative",
    "deskripsi_frame": "...",
    "zona": ["..."],
    "seat_relationships": ["..."],
    "relasi_subjek": ["..."],
    "relasi_subjek_objek": ["..."],
    "elemen_yang_harus_bersamaan_dalam_frame": ["..."],
    "forbidden_relocations": ["..."]
  }},
  "character_lock": {{
    "nama": "Milo",
    "peran_dalam_referensi": "...",
    "posisi_awal": "...",
    "gerakan_khas": "..."
  }},
  "prop_locks": [
    {{"nama":"...", "status_awal":"...", "lokasi":"...", "owner_subject":"...", "body_contact":"...", "perubahan":"...", "forbidden_changes":["..."]}}
  ],
  "temporal_breakdown": [
    {{
      "beat": 1,
      "waktu": "00:00-00:08",
      "source_evidence": ["timestamp ..."],
      "start_state": "...",
      "action": "...",
      "cause": "...",
      "end_state": "...",
      "camera_state": "...",
      "character_state": "...",
      "prop_state": "...",
      "motion_state": "...",
      "emotion_state": "...",
      "payoff_relation": "setup/escalation/payoff/extension",
      "continuity_to_next": "..."
    }}
  ],
  "urutan_kejadian": ["..."],
  "reference_ground_truth": {{
    "facts_vs_inference_notes": ["..."],
    "seat_map": ["..."],
    "camera_anchor_relationships": ["..."],
    "effect_event_map": [
      {{
        "effect": "...",
        "source_object": "...",
        "source_zone": "...",
        "timing": "...",
        "direction": "...",
        "forbidden_placement": ["..."]
      }}
    ],
    "prop_state_timeline": ["..."],
    "payoff_state": {{
      "pre": "...",
      "event": "...",
      "post": "...",
      "protagonist_reaction": "...",
      "environment_state": "..."
    }}
  }},
  "emotion_performance_analysis": {{
    "emotional_arc_global": ["..."],
    "performance_principles": ["..."],
    "reaction_hierarchy": [
      {{"subject_id":"S1", "hierarchy":"primary/secondary/tertiary/background", "emotional_function":"..."}}
    ],
    "subject_emotion_profiles": [
      {{
        "subject_id":"S1",
        "baseline_emotion":"...",
        "emotional_role":"leader/contrast/late_reactor/support/reaction",
        "trigger_map":["..."],
        "arc":["..."],
        "facial_performance":["..."],
        "head_and_gaze":["..."],
        "body_performance":["..."],
        "hands_or_paws":["..."],
        "movement_quality":["..."],
        "micro_reactions":["..."],
        "attention_targets":["..."],
        "timing_logic":"..."
      }}
    ],
    "emotion_timeline": [
      {{"beat":1, "trigger":"...", "emotional_shift":"...", "intensity_start":1, "intensity_end":3, "performance_cues":["..."], "consequence":"..."}}
    ],
    "curiosity_beats": [
      {{"beat":1, "what_viewer_knows":"...", "unknown_or_question":"...", "signal":"...", "delay":"...", "escalation":"...", "payoff":"..."}}
    ],
    "remix_emotional_enhancement": ["..."],
    "anti_flat_performance_rules": ["..."],
    "scene_performance_targets": [
      {{"scene":1, "emotion_start":"...", "trigger":"...", "emotion_shift":"...", "emotion_end":"...", "required_visible_cues":["..."], "reaction_priority":["S1","S2"]}}
    ]
  }},
  "reference_fidelity": {{
    "camera_geometry": "...",
    "subject_geography": ["..."],
    "motion_physics_map": [
      {{"beat":1,"vehicle_motion":"...","background_motion":"...","camera_motion":"...","subject_motion":"...","contact_source":"...","effect_source":"...","effect_zone":"...","effect_direction":"...","forbidden_effect_placement":["..."]}}
    ],
    "action_critical_props": [
      {{"id":"O1","owner_subject":"S1","state":"...","contact":"...","continuity_rule":"...","forbidden_changes":["..."]}}
    ],
    "hook_mechanics": {{
      "opening_anomaly":"...",
      "attention_anchor":"...",
      "curiosity_gap":"...",
      "escalation_signal":"...",
      "payoff_setup":"..."
    }},
    "payoff_fidelity": {{
      "pre_payoff_state":"...",
      "payoff_event":"...",
      "post_payoff_state":"...",
      "protagonist_reaction":"...",
      "environment_state":"..."
    }},
    "scene_coverage_map": [
      {{"scene":1,"source_time_window":"...","source_beats":["..."],"must_preserve":["..."],"allowed_remix_enhancement":["..."],"forbidden_drift":["..."]}}
    ]
  }},
  "remix_strategy": {{
    "causal_core_to_preserve":["..."],
    "hook_to_preserve":["..."],
    "emotion_to_preserve":["..."],
    "allowed_enhancement_scope":["expression","reaction_timing","micro_gesture","curiosity","visual_comedy"],
    "safe_enhancements":["..."],
    "forbidden_new_causal_actions":["..."],
    "forbidden_drift":["..."],
    "absurdity_strategy":"..."
  }},
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

    with st.spinner("Membedah referensi penuh: timeline, seat map, kamera, geography, motion physics, prop state, performance, hook, dan payoff..."):
        try:
            data = extract_json(ask(client, prompt, parts, json_mode=True))
            data.setdefault("duration_extension_plan", "")
            required_analysis = (
                "ringkasan", "niche", "hook", "sebab_akibat", "tujuan_emosi",
                "pacing_logic", "payoff", "world_lock", "camera_lock",
                "subject_roster", "object_inventory", "spatial_layout", "temporal_breakdown",
                "emotion_performance_analysis", "reference_fidelity", "remix_strategy", "reference_ground_truth",
            )
            missing_analysis = [key for key in required_analysis if key not in data]
            if missing_analysis:
                raise ValueError(f"Analisis reference tidak lengkap; field hilang: {missing_analysis}")
            if not isinstance(data.get("subject_roster"), list):
                raise ValueError("subject_roster harus berupa list hasil deteksi seluruh subjek reference.")
            emotion_data = data.get("emotion_performance_analysis")
            if not isinstance(emotion_data, dict):
                raise ValueError("emotion_performance_analysis harus berupa object performance yang lengkap.")
            data, repair_log = normalize_emotion_profiles(data)
            if repair_log:
                st.warning(
                    "⚠️ Performance profile tidak lengkap dari model untuk sebagian subject. "
                    "Sistem mengisi continuity-safe fallback secara lokal tanpa menambah request Gemini. "
                    f"Repair: {len(repair_log)} item."
                )
            if not isinstance(data.get("object_inventory"), list):
                raise ValueError("object_inventory harus berupa list hasil inventaris objek reference.")
            if not isinstance(data.get("spatial_layout"), dict):
                raise ValueError("spatial_layout harus berupa object layout reference.")
            if not isinstance(data.get("world_lock"), dict) or not isinstance(data.get("camera_lock"), dict):
                raise ValueError("world_lock dan camera_lock harus berupa object continuity reference.")
            if not isinstance(data.get("temporal_breakdown"), list) or not data.get("temporal_breakdown"):
                raise ValueError("temporal_breakdown harus berupa list beat yang tidak kosong.")
            if not isinstance(data.get("emotion_performance_analysis"), dict):
                raise ValueError("emotion_performance_analysis harus berupa object performance yang lengkap.")
            if not isinstance(data.get("reference_fidelity"), dict) or not data.get("reference_fidelity"):
                raise ValueError("reference_fidelity kosong; analisis video harus menghasilkan fidelity map.")
            if not isinstance(data.get("reference_ground_truth"), dict) or not data.get("reference_ground_truth"):
                raise ValueError("reference_ground_truth kosong; analisis harus menghasilkan spatial/motion ground truth.")
            if not isinstance(data.get("remix_strategy"), dict) or not data.get("remix_strategy"):
                raise ValueError("remix_strategy kosong; analisis harus menentukan peningkatan hook tanpa merusak causal core.")
            data["karakter_utama"] = deepcopy(CHARACTER_LOCK)
            st.session_state.analysis = data
            st.session_state.character = deepcopy(CHARACTER_LOCK)
            invalidate_from_analysis()
            # Keep the performance analysis after clearing downstream artifacts.
            st.session_state.emotion_performance = deepcopy(data.get("emotion_performance_analysis", {}))
            st.session_state.reference_fidelity = deepcopy(data.get("reference_fidelity", {}))
            st.session_state.remix_strategy = deepcopy(data.get("remix_strategy", {}))
            st.session_state.reference_ground_truth = deepcopy(data.get("reference_ground_truth", {}))
            # Freeze the project duration/scene count at analysis time.
            st.session_state.target_scene_count = target_scenes
            st.session_state.target_duration_label = st.session_state.duration
            st.session_state.analysis_project_signature = current_project_signature()
            st.session_state.analysis_valid = True
            st.session_state.analysis_stale_reason = ""
            go("analysis")
        except Exception as exc:
            st.error(f"Analisis gagal: {exc}")


# ============================================================
# ANALYSIS PAGE
# ============================================================
def render_analysis():
    st.title("Analisis Referensi + Continuity Map")
    analysis = st.session_state.analysis
    current_ok, current_reason = require_current_analysis()
    if not current_ok:
        if analysis:
            st.warning(current_reason)
        else:
            st.info(current_reason)
        return
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

    st.subheader("👥 Subject Roster — Semua Subjek Reference")
    roster = analysis.get("subject_roster", [])
    if roster:
        for i, subject in enumerate(roster, 1):
            st.markdown(
                f"**{i}. {safe_text(subject.get('jenis'))}** — {safe_text(subject.get('peran'))} | "
                f"Posisi: {safe_text(subject.get('posisi_awal'))} | "
                f"Emosi: {safe_text(subject.get('ekspresi_emosi'))}"
            )
    else:
        st.warning("Subject roster kosong — hasil analisis reference tidak lengkap.")

    st.subheader("🧰 Object Inventory")
    objects = analysis.get("object_inventory", [])
    if objects:
        for i, obj in enumerate(objects, 1):
            st.markdown(
                f"**{i}. {safe_text(obj.get('nama'))}** — {safe_text(obj.get('kategori'))} | "
                f"Posisi: {safe_text(obj.get('posisi'))} | "
                f"Fungsi: {safe_text(obj.get('fungsi_dalam_aksi'))}"
            )
    else:
        st.info("Tidak ada objek penting yang terdeteksi.")

    st.subheader("📐 Spatial Layout")
    st.write(safe_text(analysis.get("spatial_layout", {})))

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

    ground_truth = analysis.get("reference_ground_truth", {})
    fidelity = analysis.get("reference_fidelity", {})
    remix = analysis.get("remix_strategy", {})
    st.subheader("🧭 Reference Ground Truth")
    st.write(f"**Seat map:** {safe_text(ground_truth.get('seat_map'))}")
    st.write(f"**Camera anchors:** {safe_text(ground_truth.get('camera_anchor_relationships'))}")
    st.write(f"**Effect event map:** {safe_text(ground_truth.get('effect_event_map'))}")
    st.write(f"**Payoff state:** {safe_text(ground_truth.get('payoff_state'))}")

    st.subheader("🎯 Reference Fidelity + Motion Map")
    st.write(f"**Camera geometry:** {safe_text(fidelity.get('camera_geometry'))}")
    st.write(f"**Subject geography:** {safe_text(fidelity.get('subject_geography'))}")
    st.write(f"**Motion / physics:** {safe_text(fidelity.get('motion_physics_map'))}")
    st.write(f"**Action-critical props:** {safe_text(fidelity.get('action_critical_props'))}")
    st.write(f"**Hook mechanics:** {safe_text(fidelity.get('hook_mechanics'))}")
    st.write(f"**Payoff fidelity:** {safe_text(fidelity.get('payoff_fidelity'))}")
    st.subheader("🧨 Remix Enhancement Strategy")
    st.write(f"**Causal core:** {safe_text(remix.get('causal_core_to_preserve'))}")
    st.write(f"**Hook:** {safe_text(remix.get('hook_to_preserve'))}")
    st.write(f"**Emotion:** {safe_text(remix.get('emotion_to_preserve'))}")
    st.write(f"**Enhancements:** {safe_text(remix.get('safe_enhancements'))}")
    st.write(f"**Forbidden drift:** {safe_text(remix.get('forbidden_drift'))}")
    st.write(f"**Absurdity strategy:** {safe_text(remix.get('absurdity_strategy'))}")

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

    ep = analysis.get("emotion_performance_analysis", {})
    st.subheader("🎭 Emotion & Performance Engine")
    st.write(f"**Emotional arc:** {safe_text(ep.get('emotional_arc_global'))}")
    st.write(f"**Performance principles:** {safe_text(ep.get('performance_principles'))}")
    profiles = ep.get("subject_emotion_profiles", [])
    if profiles:
        for profile in profiles:
            with st.expander(f"Subject {safe_text(profile.get('subject_id'))} — {safe_text(profile.get('emotional_role'))}"):
                st.write(f"**Baseline:** {safe_text(profile.get('baseline_emotion'))}")
                st.write(f"**Arc:** {safe_text(profile.get('arc'))}")
                st.write(f"**Trigger:** {safe_text(profile.get('trigger_map'))}")
                st.write(f"**Face:** {safe_text(profile.get('facial_performance'))}")
                st.write(f"**Head/Gaze:** {safe_text(profile.get('head_and_gaze'))}")
                st.write(f"**Body:** {safe_text(profile.get('body_performance'))}")
                st.write(f"**Micro-reactions:** {safe_text(profile.get('micro_reactions'))}")
    curiosity = ep.get("curiosity_beats", [])
    if curiosity:
        st.write(f"**Curiosity beats:** {safe_text(curiosity)}")
    if st.button("LANJUT KE STORYBOARD", type="primary", use_container_width=True):
        st.session_state.current_scene = 1
        go("storyboard")


# ============================================================
# SEQUENTIAL SCENE ENGINE
# ============================================================
def scene_contract_prompt(scene_number, previous_frame_exists=False):
    analysis = st.session_state.analysis
    n = scene_count()
    beats = analysis.get("temporal_breakdown", [])
    scene_beats = temporal_beats_for_scene(scene_number)
    source_window = _source_time_window(scene_number)["label"]
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
1. Buat HANYA contract Scene {scene_number}. Jangan mengambil kejadian dari scene lain.
2. SOURCE TIME WINDOW LOCK: Scene {scene_number} hanya boleh memakai beat reference yang overlap dengan {source_window}. Untuk extension, hanya gunakan extension plan setelah reference selesai.
3. Gunakan SCENE-SPECIFIC REFERENCE BEATS di bawah sebagai sumber temporal utama. Jangan membaca payoff scene lain lalu memajukannya ke scene ini.
4. Scene 1 harus dimulai dari initial state reference. Scene 2+ harus dimulai dari screenshot last-frame scene sebelumnya dan END STATE sebelumnya.
5. Untuk Scene 2+, continuity_bridge harus dideskripsikan dari screenshot yang benar-benar terlihat. Jangan mengarang posisi baru.
6. PHYSICAL GEOGRAPHY LOCK: jika S1 dan S2 berada di kursi depan, tulis eksplisit bahwa keduanya berada pada FRONT ROW dan ADJACENT SEATS. Bedakan physical seat side dari screen-left/screen-right.
7. CAMERA LOCK: pertahankan physical camera placement, height, distance, orientation, framing, perspective, dan anchor objects. Jangan mengubah ke kamera generik.
8. MOTION LOCK: setiap gerakan kendaraan, background, tubuh, kamera, dan efek lingkungan harus memiliki arah dan sumber yang jelas.
9. EFFECT SOURCE LOCK: debu/kotoran/asap/efek lain harus berasal dari SOURCE ZONE yang sama dengan reference. Jika payoff terjadi di bagian depan kendaraan, efek tidak boleh dipindah ke belakang.
10. ACTION-CRITICAL PROP LOCK: prop yang digigit/dipegang/dipakai tetap pada owner dan body contact sampai ada aksi eksplisit yang mengubah statusnya. Tidak boleh disappear.
11. CAUSE/EFFECT LOCK: setiap action memiliki cause dan menghasilkan consequence yang terlihat. Jangan menambahkan gear shift, laugh, object movement, crash, atau event baru hanya karena terdengar lucu jika reference/scene coverage tidak mendukungnya.
12. REMIX ENHANCEMENT default hanya performance, reaction timing, micro-gesture, curiosity, readable escalation, dan safe visual comedy. Jangan mengganti causal core.
13. HOOK LOCK: pertahankan attention anchor dan anomaly dari reference pada bagian waktu yang tepat. Curiosity boleh ditingkatkan dengan delay/readability, bukan dengan event palsu.
14. EMOTION LOCK: protagonis dan subject lain harus mempertahankan emotional contrast reference. Jika S1 tetap percaya diri/cuek saat chaos, jangan membuatnya panik tanpa trigger.
15. PAYOFF LOCK: payoff harus berada pada source beat yang benar. Contract wajib menyebut pre-payoff, payoff event, post-payoff state, dan protagonist reaction.
16. START STATE → ACTION → END STATE harus konsisten. END STATE scene ini menjadi sumber scene berikutnya.
17. Jangan membuat loncatan frame/time. Tidak boleh ada perubahan lokasi, seat row, camera position, prop state, vehicle state, atau subject pose yang tidak dijelaskan sebagai continuous transition.
18. Semua nilai JSON Bahasa Indonesia.

SCENE-SPECIFIC REFERENCE BEATS:
{json.dumps(scene_beats, ensure_ascii=False, indent=2)}

DETERMINISTIC SOURCE WINDOW:
{source_window}

REFERENCE GROUND TRUTH:
{json.dumps(analysis.get('reference_ground_truth', {}), ensure_ascii=False, indent=2)}

REFERENCE FIDELITY:
{json.dumps(analysis.get('reference_fidelity', {}), ensure_ascii=False, indent=2)}

REMIX STRATEGY:
{json.dumps(analysis.get('remix_strategy', {}), ensure_ascii=False, indent=2)}

EMOTION PERFORMANCE:
{json.dumps(analysis.get('emotion_performance_analysis', {}), ensure_ascii=False, indent=2)}

DURATION EXTENSION:
{json.dumps(st.session_state.duration_extension or {}, ensure_ascii=False, indent=2)}

CHARACTER LOCK:
{json.dumps(CHARACTER_LOCK, ensure_ascii=False, indent=2)}

WORLD LOCK:
{json.dumps(analysis.get('world_lock', {}), ensure_ascii=False, indent=2)}

CAMERA LOCK:
{json.dumps(analysis.get('camera_lock', {}), ensure_ascii=False, indent=2)}

SUBJECT ROSTER:
{json.dumps(analysis.get('subject_roster', []), ensure_ascii=False, indent=2)}

OBJECT INVENTORY:
{json.dumps(analysis.get('object_inventory', []), ensure_ascii=False, indent=2)}

SPATIAL LAYOUT:
{json.dumps(analysis.get('spatial_layout', {}), ensure_ascii=False, indent=2)}

SCENE-SPECIFIC TEMPORAL EVIDENCE:
{json.dumps(scene_beats, ensure_ascii=False, indent=2)}

DURATION EXTENSION:
{json.dumps(st.session_state.duration_extension or {}, ensure_ascii=False, indent=2)}

REFERENCE FIDELITY MAP:
{json.dumps(analysis.get('reference_fidelity', {}), ensure_ascii=False, indent=2)}

REMIX ENHANCEMENT STRATEGY:
{json.dumps(analysis.get('remix_strategy', {}), ensure_ascii=False, indent=2)}

EMOTION & PERFORMANCE ANALYSIS:
{json.dumps(analysis.get('emotion_performance_analysis', {}), ensure_ascii=False, indent=2)}

PREVIOUS SCENE END STATE:
{json.dumps(previous_contract.get('end_state', {}), ensure_ascii=False, indent=2)}

Kembalikan HANYA JSON dengan struktur:
{{
  "nomor": {scene_number},
  "waktu": "{source_window}",
  "tujuan": "...",
  "source_time_window": "{source_window}",
  "source_beats": ["..."],
  "continuity_bridge": {{
    "source_scene": {scene_number - 1},
    "visual_truth": "...",
    "camera": "...",
    "framing": "...",
    "subjects": [
      {{"id":"S1", "visible":true, "position":"...", "scale":"...", "pose":"...", "expression":"..."}}
    ],
    "objects": [
      {{"id":"O1", "visible":true, "position":"...", "state":"..."}}
    ],
    "environment": "...",
    "lighting": "...",
    "locked_at_opening": ["..."],
    "allowed_transition": ["..."]
  }},
  "start_state": {{
    "lokasi": "...",
    "kamera": "...",
    "subjects": [
      {{"id":"S1", "state":"...", "position":"...", "expression":"...", "action":"..."}}
    ],
    "objects": [
      {{"id":"O1", "state":"...", "position":"..."}}
    ],
    "properti": "...",
    "elemen_lingkungan": "..."
  }},
  "cause": "...",
  "aksi": "...",
  "fidelity_audit": {{
    "source_time_window": "{source_window}",
    "reference_beat_source": "...",
    "hook_element_preserved": "...",
    "camera_geometry_preserved": "...",
    "motion_physics": "...",
    "action_critical_props_preserved": ["..."],
    "emotion_contrast_preserved": "...",
    "remix_enhancement": "...",
    "payoff_or_curiosity_progress": "..."
  }},
  "emotion_performance": {{
    "emotional_arc": ["..."],
    "primary_subject": "S1",
    "reaction_hierarchy": ["S1", "S2"],
    "trigger": "...",
    "cause_to_emotion": "...",
    "performance_timeline": [
      {{"phase":"opening_hold", "emotion":"...", "intensity":1, "facial_cues":["..."], "head_gaze":["..."], "body_cues":["..."], "hand_paw_cues":["..."], "movement_quality":"...", "attention_target":"..."}},
      {{"phase":"escalation", "emotion":"...", "intensity":3, "facial_cues":["..."], "head_gaze":["..."], "body_cues":["..."], "hand_paw_cues":["..."], "movement_quality":"...", "attention_target":"..."}},
      {{"phase":"end_state", "emotion":"...", "intensity":2, "facial_cues":["..."], "head_gaze":["..."], "body_cues":["..."], "hand_paw_cues":["..."], "movement_quality":"...", "attention_target":"..."}}
    ],
    "secondary_subject_performance": [
      {{"subject_id":"S2", "emotion":"...", "reaction_delay":"...", "visible_cues":["..."], "contrast_function":"..."}}
    ],
    "curiosity_beat": "...",
    "payoff_reaction": "..."
  }},
  "end_state": {{
    "lokasi": "...",
    "kamera": "...",
    "subjects": [
      {{"id":"S1", "state":"...", "position":"...", "expression":"...", "action":"..."}}
    ],
    "objects": [
      {{"id":"O1", "state":"...", "position":"..."}}
    ],
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
        return ask(client, prompt, parts, json_mode=purpose.startswith("Contract")), False
    except Exception as exc:
        message = str(exc)
        if frame and ("404" in message or "NOT_FOUND" in message):
            fallback = (
                prompt
                + "\n\nThe previous scene screenshot is already stored and was used to establish the "
                  "current continuity contract. Do not request or invent another image. "
                  "Generate only from the contract and locked state already supplied above."
            )
            return ask(client, fallback, [], json_mode=purpose.startswith("Contract")), True
        raise RuntimeError(f"{purpose} gagal: {message}") from exc


def validate_scene_spatial_fidelity(scene: dict, scene_number: int):
    """Reject obvious spatial contradictions against the reference ground truth.

    This is deliberately conservative: it catches high-impact contradictions such as
    moving a front-row passenger to the rear, while leaving ordinary narrative wording
    to the model. Scene 2+ uses the actual screenshot bridge as the stronger source.
    """
    if scene_number != 1:
        return
    analysis = st.session_state.get("analysis", {})
    ground = analysis.get("reference_ground_truth", {}) or {}
    seat_map = ground.get("seat_map") or analysis.get("seat_map") or []
    if not isinstance(seat_map, list):
        return
    state = scene.get("start_state") or {}
    subjects = state.get("subjects") or []
    subject_text = {str(x.get("id")): json.dumps(x, ensure_ascii=False).lower() for x in subjects if isinstance(x, dict) and x.get("id")}
    for seat in seat_map:
        if not isinstance(seat, dict):
            continue
        sid = str(seat.get("occupied_by") or "")
        row = str(seat.get("row") or "").lower()
        if not sid or sid not in subject_text:
            continue
        text = subject_text[sid]
        if row == "front" and any(token in text for token in ("rear", "belakang", "kursi belakang", "baris belakang")):
            raise ValueError(
                f"Scene {scene_number} spatial contradiction: {sid} terdeteksi sebagai kursi FRONT di reference "
                "tetapi start_state menyebut REAR/BELAKANG."
            )
        if row == "rear" and any(token in text for token in ("front", "depan", "kursi depan", "baris depan")):
            raise ValueError(
                f"Scene {scene_number} spatial contradiction: {sid} terdeteksi sebagai kursi REAR di reference "
                "tetapi start_state menyebut FRONT/DEPAN."
            )


def generate_scene_contract(scene_number):
    current_ok, current_reason = require_current_analysis()
    if not current_ok:
        st.warning(current_reason)
        return False
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
            scene["source_time_window"] = scene.get("source_time_window") or _source_time_window(scene_number)["label"]
            if scene["source_time_window"] != _source_time_window(scene_number)["label"]:
                # Keep the deterministic project window authoritative.
                scene["source_time_window"] = _source_time_window(scene_number)["label"]
            deterministic_source_beats = [
                str(item.get("beat")) for item in temporal_beats_for_scene(scene_number)
                if isinstance(item, dict) and item.get("beat") is not None
            ]
            scene["source_beats"] = deterministic_source_beats
            scene.setdefault("waktu", f"{(scene_number - 1) * 8:02d}-{scene_number * 8:02d}")
            scene.setdefault("start_state", {})
            scene.setdefault("end_state", {})
            scene.setdefault("cause", "")
            scene.setdefault("aksi", "")
            scene.setdefault("kontinuitas", "")
            scene.setdefault("continuity_bridge", {})
            scene.setdefault("emotion_performance", {})
            if not isinstance(scene.get("emotion_performance"), dict) or not scene.get("emotion_performance"):
                raise ValueError(f"Scene {scene_number} emotion_performance kosong; contract ditolak agar performance tidak datar.")
            if scene_number > 1:
                bridge = scene.get("continuity_bridge") or {}
                required_bridge_fields = ("visual_truth", "camera", "framing", "subjects", "objects", "environment", "lighting", "locked_at_opening", "allowed_transition")
                missing_bridge = [k for k in required_bridge_fields if k not in bridge]
                if missing_bridge:
                    raise ValueError(
                        f"Scene {scene_number} continuity bridge tidak lengkap: {missing_bridge}. "
                        "Contract ditolak agar sambungan visual tidak longgar."
                    )
            scene["_image_fallback_used"] = bool(used_fallback)
            if not scene["start_state"] or not scene["end_state"]:
                raise ValueError(f"Scene {scene_number} tidak memiliki START STATE/END STATE lengkap.")

            required_ids = {
                str(item.get("id"))
                for item in st.session_state.analysis.get("subject_roster", [])
                if item.get("wajib_terlihat") is True and item.get("id")
            }
            for state_name in ("start_state", "end_state"):
                state = scene.get(state_name) or {}
                seen_ids = {str(item.get("id")) for item in (state.get("subjects") or []) if item.get("id")}
                missing = sorted(required_ids - seen_ids)
                if missing:
                    raise ValueError(
                        f"Scene {scene_number} menghilangkan subject wajib {missing} pada {state_name}. "
                        "Contract ditolak agar supporting subject tidak hilang."
                    )

            expected_window = _source_time_window(scene_number)["label"]
            if scene.get("source_time_window") != expected_window:
                raise ValueError(f"Scene {scene_number} source_time_window tidak sesuai window proyek: expected {expected_window}.")

            validate_scene_spatial_fidelity(scene, scene_number)

            fidelity_audit = scene.get("fidelity_audit") or {}
            if not isinstance(fidelity_audit, dict) or not fidelity_audit:
                raise ValueError(f"Scene {scene_number} fidelity_audit kosong; contract harus membuktikan hook/motion/geography tetap terjaga.")
            fidelity_required = ("reference_beat_source", "hook_element_preserved", "camera_geometry_preserved", "motion_physics", "action_critical_props_preserved", "emotion_contrast_preserved", "remix_enhancement", "payoff_or_curiosity_progress")
            missing_fidelity = [k for k in fidelity_required if k not in fidelity_audit]
            if missing_fidelity:
                raise ValueError(f"Scene {scene_number} fidelity_audit tidak lengkap: {missing_fidelity}")

            emotion_contract = scene.get("emotion_performance") or {}
            hierarchy = emotion_contract.get("reaction_hierarchy") or []
            allowed_subject_ids = {str(x.get("id")) for x in st.session_state.analysis.get("subject_roster", []) if isinstance(x, dict) and x.get("id")}
            if isinstance(hierarchy, list):
                bad_hierarchy = [str(x) for x in hierarchy if str(x) not in allowed_subject_ids]
                if bad_hierarchy:
                    raise ValueError(f"Scene {scene_number} emotion reaction hierarchy memakai subject ID tidak dikenal: {bad_hierarchy}")
            timeline = emotion_contract.get("performance_timeline") or []
            if not isinstance(timeline, list) or len(timeline) < 2:
                raise ValueError(f"Scene {scene_number} performance_timeline harus memiliki minimal opening dan perubahan/end state.")
            for phase in timeline:
                if not isinstance(phase, dict):
                    raise ValueError(f"Scene {scene_number} performance_timeline memiliki item tidak valid.")
                intensity = phase.get("intensity")
                if intensity is not None:
                    try:
                        if not 1 <= int(intensity) <= 5:
                            raise ValueError(f"Scene {scene_number} emotion intensity harus 1-5.")
                    except (TypeError, ValueError):
                        raise ValueError(f"Scene {scene_number} emotion intensity harus integer 1-5.")

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
    current_ok, current_reason = require_current_analysis()
    if not current_ok:
        st.warning(current_reason)
        return False
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

    current_signature = scene_prompt_input_signature(scene_number)
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
- The first visual beat is a HARD CONTINUITY HOLD: do not immediately zoom out, cut, reframe, relocate, add characters, or alter the environment.
- Treat CONTINUITY BRIDGE below as a locked visual contract extracted from the previous scene's actual last frame.
- Any change listed under allowed_transition must happen progressively after the opening hold, never as a jump at frame 0.
- Never teleport or relocate Milo, props, furniture, doors, windows, vehicles, or camera.
- Never introduce a new location or unexplained object/person.
- ANY important subject detected in SUBJECT ROSTER must remain represented unless the reference explicitly has that subject leave the frame.
- Do not collapse a multi-subject composition into a single-subject close-up.
- Preserve each subject's role, relative position, interaction, expression/emotional function, and visibility requirements.
- Preserve left/right/front/back geography and subject-to-object relationships.
- Any movement must be caused by the visible action.
- Preserve camera position and perspective unless a continuous camera move is explicitly required.
- If multiple important subjects are marked wajib_terlihat, use framing/coverage that keeps them simultaneously readable whenever the reference does so.
- PERFORMANCE IS MANDATORY: show emotion through visible facial expression, head movement, gaze/attention, body language, hand/paw behavior, and movement quality. Do not rely on emotion labels alone.
- Every emotional change must have a visible trigger and causal transition. Use CAUSE → EMOTION → PERFORMANCE → CONSEQUENCE.
- Preserve emotional contrast and reaction hierarchy; primary, secondary, and background subjects must not all react identically.
- Use the emotion_performance contract as a timed visual-performance plan, while keeping the opening hold locked to the bridge.
- Use fidelity_audit + REFERENCE FIDELITY MAP as non-negotiable evidence that this scene still follows the reference mechanism.
- Preserve the actual camera geography exactly. If the reference camera is inside the front cabin at seat/dashboard level, keep that same physical placement and relationship to the front seats, steering wheel, dashboard, doors, and windows.
- Preserve motion causality: vehicle movement, subject inertia, background motion, and dust/debris must visibly originate from the correct spatial source.
- Preserve action-critical props exactly where they are attached/held/bitten until an explicit action changes them. Never make them disappear between beats.
- Remix only by enhancing performance, reaction timing, micro-gestures, readable curiosity, or safe visual comedy after the locked opening. Do NOT invent a new causal action unless CURRENT SCENE CONTRACT explicitly lists it under allowed_remix_enhancement.
- Never invent a gear shift, steering action, laugh, crash, object release, dust burst, camera relocation, seat relocation, or new prop merely to make the prompt more entertaining.
- Every physical event must be traceable to CURRENT SCENE CONTRACT -> source beat -> cause -> action -> consequence.
- If a detail is not in the current scene contract and is not a continuity-safe micro-enhancement, omit it rather than guessing.
- For vehicle scenes, explicitly preserve FRONT-ROW SEATING and ADJACENCY when the contract says subjects occupy adjacent front seats. Never reinterpret an adjacent front passenger as a rear passenger.
- For environmental effects, state the effect source zone and direction exactly as specified by the contract; do not relocate dust/debris behind the vehicle when the source is at the front ground-contact zone.
- The first seconds must contain the hook's attention anchor and a clear unanswered question or escalating signal.
- Build curiosity through information gaps, delayed reveal, escalation, and readable reaction when the contract specifies them.
- The final frame must visibly establish each required subject's emotional state, gaze/attention, pose, and action state for the next bridge.
- Milo must remain exactly the same kitten.
- The final image must clearly establish the END STATE below for the next scene.
- Do not create an abrupt cut that destroys spatial continuity.

MILO LOCK:
{CHARACTER_LOCK_EN}

WORLD LOCK:
{json.dumps(analysis.get('world_lock', {}), ensure_ascii=False, indent=2)}

CAMERA LOCK:
{json.dumps(analysis.get('camera_lock', {}), ensure_ascii=False, indent=2)}

SUBJECT ROSTER:
{json.dumps(analysis.get('subject_roster', []), ensure_ascii=False, indent=2)}

OBJECT INVENTORY:
{json.dumps(analysis.get('object_inventory', []), ensure_ascii=False, indent=2)}

SPATIAL LAYOUT:
{json.dumps(analysis.get('spatial_layout', {}), ensure_ascii=False, indent=2)}

CURRENT SCENE CONTRACT:
{json.dumps(scene, ensure_ascii=False, indent=2)}

SCENE SOURCE WINDOW:
{json.dumps(_source_time_window(scene_number), ensure_ascii=False, indent=2)}

SCENE SOURCE BEATS:
{json.dumps(temporal_beats_for_scene(scene_number), ensure_ascii=False, indent=2)}

PREVIOUS SCENE CONTRACT:
{json.dumps(previous, ensure_ascii=False, indent=2)}

CONTINUITY BRIDGE:
{json.dumps(scene.get("continuity_bridge", {}), ensure_ascii=False, indent=2)}

EMOTION & PERFORMANCE CONTRACT:
{json.dumps(scene.get("emotion_performance", {}), ensure_ascii=False, indent=2)}

FIDELITY AUDIT:
{json.dumps(scene.get("fidelity_audit", {}), ensure_ascii=False, indent=2)}

REFERENCE GROUND TRUTH:
{json.dumps(analysis.get("reference_ground_truth", {}), ensure_ascii=False, indent=2)}

REFERENCE FIDELITY MAP:
{json.dumps(analysis.get("reference_fidelity", {}), ensure_ascii=False, indent=2)}

REMIX ENHANCEMENT STRATEGY:
{json.dumps(analysis.get("remix_strategy", {}), ensure_ascii=False, indent=2)}

STYLE: {st.session_state.visual_style}
ASPECT: {st.session_state.aspect_ratio}

SCENE-SPECIFIC USER INSTRUCTION:
{st.session_state.get("scene_custom_instructions", {}).get(scene_number, "") or "(none)"}

INSTRUCTION PRIORITY:
- Apply the scene-specific user instruction only where it is compatible with the locked continuity bridge.
- Never let the instruction override the exact opening visual state, geography, subject identity, or required continuity.
- If the instruction requests a new expression, gesture, reaction, camera move, prop action, or micro-beat, introduce it AFTER the hard opening hold unless it is already visible in the bridge.
- Never add a new subject, location, or major prop unless the existing scene contract explicitly allows it.

Write one detailed English paragraph. Begin by describing a very short opening hold that matches the CONTINUITY BRIDGE exactly, then describe only the allowed transition and subsequent action. Include opening composition with ALL required subjects, fixed geography, subject-to-subject and subject-to-object relationships, Milo's exact appearance, continuous cause-and-effect action, camera movement, lighting continuity, sound when useful, and the exact final state. Explicitly stage the emotional performance as visible action: facial change, eyes/gaze, head direction, body posture, hand/paw tension, movement quality, reaction delay, and escalation/relief where specified. The viewer must be able to read the emotional shift without narration. Do not omit or silently remove any important supporting subject from the roster.
Do not add anything outside the contracts.
"""
    with st.spinner(f"Membuat prompt Scene {scene_number}..."):
        try:
            result, used_text_fallback = ask_scene_prompt(client, prompt, previous_frame)
            result = result.strip()
            if not result:
                raise ValueError("Prompt kosong.")
            st.session_state.scene_prompts[scene_number] = result
            st.session_state.setdefault("scene_prompt_input_signatures", {})[scene_number] = current_signature
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
    current_ok, current_reason = require_current_analysis()
    if not current_ok:
        st.warning(current_reason)
        st.button("ANALYZE + AUTO REMIX DULU", type="primary", use_container_width=True, on_click=lambda: go("home"))
        return
    if not st.session_state.analysis:
        st.info("Analisis referensi belum tersedia.")
        return

    n = scene_count()
    current = st.session_state.current_scene
    st.progress(current / n)
    st.markdown(f"### SCENE {current} / {n}")

    if current == 1 and not st.session_state.storyboard:
        st.info("Scene 1 belum dibuat. AI sudah menyimpan blueprint referensi secara internal.")
        if st.button("BUAT STORYBOARD SCENE 1", type="primary", use_container_width=True):
            if generate_scene_contract(1):
                st.rerun()
        return

    if len(st.session_state.storyboard) < current:
        st.warning(f"Scene {current} belum dibuka. Selesaikan Scene {current - 1} terlebih dahulu.")
        return

    scene = st.session_state.storyboard[current - 1]
    st.subheader(f"Scene {current} — {scene.get('waktu', '')}")
    st.write(f"**Tujuan:** {safe_text(scene.get('tujuan'))}")
    if current > 1 and scene.get("continuity_bridge"):
        with st.expander("🔒 Continuity Bridge — START STATE LOCK", expanded=True):
            st.write(f"**Visual truth:** {safe_text(scene['continuity_bridge'].get('visual_truth'))}")
            st.write(f"**Camera:** {safe_text(scene['continuity_bridge'].get('camera'))}")
            st.write(f"**Framing:** {safe_text(scene['continuity_bridge'].get('framing'))}")
            st.write(f"**Locked opening:** {safe_text(scene['continuity_bridge'].get('locked_at_opening'))}")
            st.write(f"**Allowed transition:** {safe_text(scene['continuity_bridge'].get('allowed_transition'))}")
    st.write(f"**START STATE:** {safe_text(scene.get('start_state'))}")
    st.write(f"**CAUSE:** {safe_text(scene.get('cause'))}")
    st.write(f"**ACTION:** {safe_text(scene.get('aksi'))}")
    st.write(f"**END STATE:** {safe_text(scene.get('end_state'))}")
    st.write(f"**Continuity:** {safe_text(scene.get('kontinuitas'))}")
    if scene.get("emotion_performance"):
        with st.expander("🎭 Emotion & Performance Contract", expanded=True):
            ep_scene = scene.get("emotion_performance", {})
            st.write(f"**Arc:** {safe_text(ep_scene.get('emotional_arc'))}")
            st.write(f"**Trigger:** {safe_text(ep_scene.get('trigger'))}")
            st.write(f"**Cause → Emotion:** {safe_text(ep_scene.get('cause_to_emotion'))}")
            st.write(f"**Reaction hierarchy:** {safe_text(ep_scene.get('reaction_hierarchy'))}")
            st.write(f"**Performance timeline:** {safe_text(ep_scene.get('performance_timeline'))}")

    st.divider()
    if current not in st.session_state.scene_prompts:
        st.success("Storyboard scene ini sudah siap. Sekarang lanjut ke generator Prompt Scene.")
        if st.button(f"🚀 BUAT PROMPT SCENE {current}", type="primary", use_container_width=True):
            st.session_state.current_scene = current
            go("scenes")
    else:
        st.success(f"Prompt Scene {current} siap.")
        if st.button(f"BUKA PROMPT SCENE {current}", type="primary", use_container_width=True):
            st.session_state.current_scene = current
            go("scenes")


def scene_prompt_input_signature(scene_number):
    """Fingerprint every input that can change a scene prompt.

    This prevents a stale prompt from surviving after the user edits the
    per-scene instruction, replaces the previous-frame bridge, or changes
    prompt-relevant project settings.
    """
    scenes = st.session_state.get("storyboard", [])
    if scene_number < 1 or scene_number > len(scenes):
        return None
    scene = scenes[scene_number - 1]
    previous = scenes[scene_number - 2] if scene_number > 1 and len(scenes) >= scene_number else {}
    bridge_frame = st.session_state.get("scene_frames", {}).get(scene_number - 1) if scene_number > 1 else None
    bridge_fp = (bridge_frame or {}).get("fingerprint") if isinstance(bridge_frame, dict) else None
    payload = {
        "scene_number": scene_number,
        "scene": scene,
        "previous_scene": previous,
        "bridge_fingerprint": bridge_fp,
        "scene_instruction": st.session_state.get("scene_custom_instructions", {}).get(scene_number, ""),
        "visual_style": st.session_state.get("visual_style"),
        "aspect_ratio": st.session_state.get("aspect_ratio"),
        "analysis_signature": st.session_state.get("reference_content_signature") or st.session_state.get("reference_signature"),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def invalidate_scene_prompt(scene_number):
    """Remove only the prompt artifacts for one scene."""
    st.session_state.setdefault("scene_prompts", {}).pop(scene_number, None)
    st.session_state.setdefault("scene_prompt_notes", {}).pop(scene_number, None)
    st.session_state.setdefault("scene_prompt_input_signatures", {}).pop(scene_number, None)


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
    # Keep the user's future scene instructions. They are independent intent,
    # while contracts/prompts are the artifacts that depend on the replaced bridge.
    for key in list(st.session_state.get("scene_prompt_input_signatures", {})):
        if key > scene_number:
            st.session_state.scene_prompt_input_signatures.pop(key, None)
    while len(st.session_state.storyboard) > scene_number:
        st.session_state.storyboard.pop()
    for key in list(st.session_state.scene_frames):
        if key > scene_number:
            st.session_state.scene_frames.pop(key, None)
    for key in list(st.session_state.continuity_bridges):
        if key > scene_number:
            st.session_state.continuity_bridges.pop(key, None)
    st.session_state.seo = {}
    return True




def validate_bridge(scene_number):
    """Validate that the bridge exists, is an image, and can actually be decoded."""
    frame = st.session_state.scene_frames.get(scene_number)
    if not frame or not frame.get("data"):
        return False, f"Screenshot akhir Scene {scene_number} belum tersedia."
    mime = frame.get("mime_type", "")
    if not mime.startswith("image/"):
        return False, "File bridge bukan gambar yang didukung."
    data = frame.get("data", b"")
    if len(data) < 128:
        return False, "Screenshot bridge terlalu kecil atau kosong."
    try:
        import numpy as np
        image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            return False, "Screenshot bridge tidak bisa dibaca sebagai gambar yang valid."
    except Exception:
        # If OpenCV decoding is unavailable for a rare image format, the MIME/byte
        # checks still provide a safe minimum rather than blocking the workflow.
        pass
    return True, ""
def render_scenes():
    st.title("Prompt Adegan — Sequential Visual Bridge")
    current_ok, current_reason = require_current_analysis()
    if not current_ok:
        st.warning(current_reason)
        st.button("ANALYZE + AUTO REMIX DULU", type="primary", use_container_width=True, on_click=lambda: go("home"))
        return
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
    if current > 1 and scene.get("continuity_bridge"):
        with st.expander("🔒 Continuity Bridge — START STATE LOCK", expanded=True):
            st.write(f"**Visual truth:** {safe_text(scene['continuity_bridge'].get('visual_truth'))}")
            st.write(f"**Camera:** {safe_text(scene['continuity_bridge'].get('camera'))}")
            st.write(f"**Framing:** {safe_text(scene['continuity_bridge'].get('framing'))}")
            st.write(f"**Locked opening:** {safe_text(scene['continuity_bridge'].get('locked_at_opening'))}")
            st.write(f"**Allowed transition:** {safe_text(scene['continuity_bridge'].get('allowed_transition'))}")
    st.write(f"**START STATE:** {safe_text(scene.get('start_state'))}")
    st.write(f"**CAUSE:** {safe_text(scene.get('cause'))}")
    st.write(f"**ACTION:** {safe_text(scene.get('aksi'))}")
    st.write(f"**END STATE:** {safe_text(scene.get('end_state'))}")

    # ------------------------------------------------------------
    # Scene-specific instruction: this affects only the current scene prompt.
    # It cannot override the locked visual bridge.
    # ------------------------------------------------------------
    scene_instruction_key = f"scene_instruction_{st.session_state.project_nonce}_{current}"
    existing_scene_instruction = st.session_state.get("scene_custom_instructions", {}).get(current, "")
    scene_instruction = st.text_area(
        f"Instruksi tambahan untuk hasil Prompt Scene {current}",
        value=existing_scene_instruction,
        height=100,
        placeholder=(
            "Contoh: setelah opening hold, buat Milo terlihat lebih kaget, "
            "lalu menoleh ke kiri sebelum melanjutkan aksi utama."
        ),
        key=scene_instruction_key,
        help=(
            "Instruksi ini hanya berlaku untuk scene ini. Continuity bridge tetap menjadi "
            "aturan tertinggi untuk frame pembuka."
        ),
    )
    st.session_state.setdefault("scene_custom_instructions", {})[current] = scene_instruction

    # If the user edits the instruction after a prompt was generated, the old
    # prompt is no longer authoritative. Remove it immediately so the next
    # explicit generation uses the new instruction.
    stored_signature = st.session_state.get("scene_prompt_input_signatures", {}).get(current)
    current_signature = scene_prompt_input_signature(current)
    if current in st.session_state.scene_prompts and stored_signature != current_signature:
        invalidate_scene_prompt(current)
        st.info("Instruksi Scene berubah — prompt lama dibatalkan. Klik BUAT PROMPT untuk menghasilkan versi terbaru.")

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
                    for key in list(st.session_state.scene_prompt_notes):
                        if key > current:
                            st.session_state.scene_prompt_notes.pop(key, None)
                    for key in list(st.session_state.get("scene_prompt_input_signatures", {})):
                        if key > current:
                            st.session_state.scene_prompt_input_signatures.pop(key, None)
                    while len(st.session_state.storyboard) > current:
                        st.session_state.storyboard.pop()
                    for key in list(st.session_state.continuity_bridges):
                        if key > current:
                            st.session_state.continuity_bridges.pop(key, None)
                    st.session_state.seo = {}
                st.success("Screenshot Scene terakhir tersimpan sebagai visual bridge.")

            if st.button(
                f"KONFIRMASI FRAME → BUKA SCENE {current + 1}",
                type="primary",
                use_container_width=True,
                key=f"open_next_{st.session_state.project_nonce}_{current}",
            ):
                ok, reason = validate_bridge(current)
                if not ok:
                    st.error(reason)
                else:
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
    current_ok, current_reason = require_current_analysis()
    if not current_ok:
        st.warning(current_reason)
        return
    client = get_client()
    if not client:
        return

    analysis = st.session_state.analysis
    storyboard = st.session_state.storyboard

    # Google Search is an optional enrichment pass. SEO generation must remain
    # fully usable when grounding is unavailable, quota-limited, or unsupported.
    research_prompt = f"""
Anda adalah YouTube SEO researcher untuk channel Tale Of Paw dengan target GLOBAL.
Jika Google Search tersedia, gunakan untuk memeriksa phrasing pencarian yang relevan.
Jika Search tidak tersedia, tetap lakukan riset semantik dari isi video dan jangan berhenti.

VIDEO ANALYSIS:
{json.dumps(analysis, ensure_ascii=False)}

SCENE CONTRACTS:
{json.dumps(storyboard, ensure_ascii=False)}

Tugas:
1. Identifikasi search intent utama video.
2. Buat konsep broad, mid-tail, dan long-tail yang benar-benar sesuai isi.
3. Prioritaskan istilah yang kemungkinan dipakai penonton global untuk mencari video sejenis.
4. Buat padanan Indonesia yang natural.
5. Hindari keyword yang tidak ada hubungannya, nama brand/karakter yang tidak muncul, tren palsu,
   keyword stuffing, dan clickbait.
6. Jangan mengklaim search volume, ranking, atau trend score tanpa data nyata.
7. Jika Search aktif, rangkum maksimal 5 query/sumber yang paling membantu. Jika tidak aktif,
   nyatakan bahwa hasil berasal dari semantic SEO analysis.

Berikan ringkasan riset yang ringkas dan dapat dipakai oleh generator metadata.
"""

    with st.spinner("🔎 Riset SEO global + semantic relevance..."):
        try:
            research = ask(client, research_prompt, google_search=True)
        except Exception as exc:
            research = (
                "OPTIONAL GOOGLE SEARCH UNAVAILABLE. "
                "Continue with semantic SEO from the actual video analysis and scene contracts. "
                f"Reason: {exc}"
            )
            st.info("ℹ️ Riset Google Search opsional tidak tersedia. SEO tetap dibuat penuh dari isi video + semantic search intent.")

    prompt = f"""
Buat paket metadata YouTube untuk Tale Of Paw berdasarkan ISI VIDEO AKTUAL dan hasil riset di bawah.
Target audiens GLOBAL, tetapi output wajib memiliki versi ENGLISH dan INDONESIAN.

PRINSIP UTAMA:
- Relevansi terhadap isi video lebih penting daripada keyword populer.
- Jangan keyword stuffing.
- Jangan memasukkan topik, karakter, objek, atau tren yang tidak benar-benar relevan.
- Jangan menjanjikan viral, ranking, atau feed tertentu.
- Judul harus menarik tetapi tetap jujur terhadap isi.
- English adalah versi utama untuk target global; Indonesian adalah versi lokal yang natural.
- Deskripsi harus jelas, natural, dan memasukkan istilah relevan secara wajar.
- Hashtag harus terbatas dan sangat relevan.
- Tags adalah variasi istilah relevan EN + ID, bukan daftar kata acak.
- Wajib menghasilkan TEPAT 15 global tags total, gabungan EN + ID.
- Distribusi default 8 English + 7 Indonesian, kecuali isi video jelas lebih cocok dengan distribusi berbeda.
- Jaga setiap tag singkat (umumnya 1-4 kata) agar 15 tag tetap praktis untuk ditempel ke YouTube Studio.
- Setiap tag harus merupakan frasa pencarian yang natural dan benar-benar relevan.
- Jangan menambahkan # pada tags.
- Hindari duplikat, sinonim yang hampir sama, nama yang tidak ada di video, dan keyword populer yang tidak relevan.
- Gunakan detail dari scene contracts untuk menangkap hook, aksi, karakter, emosi, dan payoff aktual.
- Judul: 3 opsi yang searchable + curiosity, tetapi tetap akurat.
- Description: 2-3 baris pertama harus langsung menjelaskan video dan memuat 1-2 istilah utama secara natural.
- Hashtags: 3-5 hashtag yang sangat relevan, bukan tumpukan keyword.
- Sertakan alasan singkat mengapa primary keywords dipilih.

VIDEO ANALYSIS:
{json.dumps(analysis, ensure_ascii=False)}

SCENE CONTRACTS:
{json.dumps(storyboard, ensure_ascii=False)}

HASIL RISET GOOGLE SEARCH:
{research}

Kembalikan HANYA JSON valid dengan struktur:
{{
  "english": {{
    "titles": ["...", "...", "..."],
    "description": "...",
    "hashtags": ["..."],
    "tags": ["..."]
  }},
  "indonesian": {{
    "titles": ["...", "...", "..."],
    "description": "...",
    "hashtags": ["..."],
    "tags": ["..."]
  }},
  "global_tags_15": ["exactly 15 tags total, mixed EN + ID"],
  "seo_strategy": {{
    "primary_topic": "...",
    "primary_search_intent": "...",
    "core_keywords": ["..."],
    "relevance_notes": ["..."]
  }},
  "teks_thumbnail": "...",
  "konsep_thumbnail": "...",
  "komentar_tersemat": "...",
  "ajakan": "..."
}}
"""
    with st.spinner("🧠 Menyusun metadata EN + ID..."):
        try:
            seo_data = extract_json(ask(client, prompt, json_mode=True))
            if not isinstance(seo_data, dict):
                raise ValueError("SEO response bukan object JSON.")

            # Deterministically enforce the user's requested 15 bilingual global tags.
            def _clean_tags(values):
                out = []
                seen = set()
                for value in values if isinstance(values, list) else []:
                    tag = re.sub(r"^#+", "", str(value).strip())
                    if not tag:
                        continue
                    key = tag.casefold()
                    if key not in seen:
                        seen.add(key)
                        out.append(tag)
                return out

            global_tags = _clean_tags(seo_data.get("global_tags_15"))
            en_tags = _clean_tags((seo_data.get("english") or {}).get("tags"))
            id_tags = _clean_tags((seo_data.get("indonesian") or {}).get("tags"))

            # Prefer an explicit global list, then fill from EN/ID without duplicates.
            for tag in en_tags + id_tags:
                if len(global_tags) >= 15:
                    break
                if tag.casefold() not in {x.casefold() for x in global_tags}:
                    global_tags.append(tag)

            if len(global_tags) < 15:
                raise ValueError(
                    f"AI hanya menghasilkan {len(global_tags)} global tags unik; minimal/tepat 15 diperlukan."
                )
            global_tags = global_tags[:15]
            seo_data["global_tags_15"] = global_tags

            # Keep language-specific lists usable too, while the global list is the
            # canonical upload-ready set requested by the user.
            seo_data.setdefault("seo_strategy", {})
            seo_data["seo_strategy"]["global_tag_count"] = len(global_tags)
            seo_data["seo_strategy"]["global_tag_language_mix"] = {
                "english_candidates": len(en_tags),
                "indonesian_candidates": len(id_tags),
            }
            seo_data["research"] = research
            st.session_state.seo = seo_data
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
    en = seo.get("english", {}) if isinstance(seo.get("english", {}), dict) else {}
    idn = seo.get("indonesian", {}) if isinstance(seo.get("indonesian", {}), dict) else {}

    global_tags = seo.get("global_tags_15", [])
    st.subheader("🌍 15 Global Tags — EN + ID")
    st.caption("15 tag final untuk dipakai sebagai satu set. Tags membantu relevansi, tetapi YouTube menyebut judul, thumbnail, dan deskripsi lebih penting.")
    st.text_area("Global Tags (15)", ", ".join(map(str, global_tags)), height=90)

    st.subheader("🌍 English — Global")
    for index, title in enumerate(en.get("titles", []), 1):
        st.text_input(f"English Title {index}", str(title), key=f"title_en_{index}")
    st.text_area("English Description", safe_text(en.get("description")), height=220)
    st.text_area("English Hashtags", " ".join(map(str, en.get("hashtags", []))), height=100)
    st.text_area("English Tags", ", ".join(map(str, en.get("tags", []))), height=100)

    st.subheader("🇮🇩 Indonesian")
    for index, title in enumerate(idn.get("titles", []), 1):
        st.text_input(f"Indonesian Title {index}", str(title), key=f"title_id_{index}")
    st.text_area("Indonesian Description", safe_text(idn.get("description")), height=220)
    st.text_area("Indonesian Hashtags", " ".join(map(str, idn.get("hashtags", []))), height=100)
    st.text_area("Indonesian Tags", ", ".join(map(str, idn.get("tags", []))), height=100)

    strategy = seo.get("seo_strategy", {}) if isinstance(seo.get("seo_strategy", {}), dict) else {}
    st.subheader("SEO Strategy")
    st.write(f"**Primary topic:** {safe_text(strategy.get('primary_topic'))}")
    st.write(f"**Search intent:** {safe_text(strategy.get('primary_search_intent'))}")
    st.text_area("Core Keywords", ", ".join(map(str, strategy.get("core_keywords", []))), height=90)
    st.text_area("Relevance Notes", "\n".join(map(str, strategy.get("relevance_notes", []))), height=120)

    st.subheader("Creative Support")
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
