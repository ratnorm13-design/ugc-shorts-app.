"""Deterministic validation core for UGC Remix Studio V5.16.
No Gemini/network calls. The core is intentionally strict: model omissions are
reported as failures instead of being silently repaired into authoritative state.
"""
from __future__ import annotations
import re
from typing import Any


def _txt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, dict):
        return " ".join(f"{k} {v2}" for k, v2 in v.items())
    if isinstance(v, list):
        return " ".join(_txt(x) for x in v)
    return str(v)


def _id(x: Any) -> str:
    return str(x).strip().lower()


def _parse_seconds(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    s = _txt(value).lower().replace(",", ".")
    if ":" in s:
        parts = re.findall(r"\d+(?:\.\d+)?", s)
        if len(parts) >= 2:
            return float(parts[-2]) * 60 + float(parts[-1])
    nums = re.findall(r"\d+(?:\.\d+)?", s)
    return float(nums[0]) if nums else None


def _parse_range(value: Any) -> tuple[float, float] | None:
    s = _txt(value).lower().replace(",", ".")
    nums = re.findall(r"\d+(?:\.\d+)?", s)
    if len(nums) >= 2:
        if ":" in s:
            # mm:ss-mm:ss is handled approximately by splitting the two endpoints.
            parts = re.findall(r"(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)", s)
            if len(parts) >= 2:
                return float(parts[0][0]) * 60 + float(parts[0][1]), float(parts[1][0]) * 60 + float(parts[1][1])
        return float(nums[0]), float(nums[1])
    if len(nums) == 1:
        x = float(nums[0])
        return x, x
    return None


def subject_signature(item: dict) -> tuple[str, str, str]:
    return (_id(item.get("id")), _id(item.get("jenis")), _id(item.get("peran")))


def reconcile_subject_rosters(probe: list, analysis: list) -> dict:
    p = {_id(x.get("id")): x for x in probe if isinstance(x, dict) and x.get("id")}
    a = {_id(x.get("id")): x for x in analysis if isinstance(x, dict) and x.get("id")}
    missing = sorted(set(p) - set(a))
    extra = sorted(set(a) - set(p))
    conflicts = []
    for sid in sorted(set(p) & set(a)):
        ps, ass = subject_signature(p[sid]), subject_signature(a[sid])
        if ps[1:] != ass[1:]:
            conflicts.append({"id": sid, "probe": ps, "analysis": ass})
    return {"ok": not missing and not extra and not conflicts, "missing": missing, "extra": extra, "conflicts": conflicts}


def validate_reference_fidelity(fidelity: Any) -> dict:
    """Require concrete, non-generic fidelity evidence for every critical dimension."""
    if not isinstance(fidelity, dict) or not fidelity:
        return {"ok": False, "issues": ["reference_fidelity kosong"]}
    required = ("camera_geometry", "subject_geography", "motion_physics_map", "action_critical_props", "hook_mechanics", "payoff_fidelity")
    issues = []
    generic = {
        "konsisten", "tetap konsisten", "sesuai reference", "sesuai referensi",
        "camera consistent", "subject consistent", "motion consistent", "prop consistent",
    }
    for key in required:
        value = _txt(fidelity.get(key)).strip()
        if not value:
            issues.append(f"{key} kosong")
            continue
        low = value.lower().strip(" .:-")
        if low in generic or len(value) < 18:
            issues.append(f"{key} tidak cukup substantif")
    must = fidelity.get("must_preserve")
    forbidden = fidelity.get("forbidden_drift")
    if not isinstance(must, list) or len([x for x in must if _txt(x).strip()]) < 3:
        issues.append("must_preserve minimal 3 bukti/aturan konkret")
    if not isinstance(forbidden, list) or len([x for x in forbidden if _txt(x).strip()]) < 2:
        issues.append("forbidden_drift minimal 2 drift konkret")
    return {"ok": not issues, "issues": issues}


def validate_performance_profiles(roster: list, profiles: list) -> dict:
    """Hard gate: exactly one complete model profile per detected subject."""
    issues = []
    subjects = {_id(x.get("id")): x for x in roster if isinstance(x, dict) and x.get("id")}
    if not subjects:
        return {"ok": False, "issues": ["subject_roster kosong"]}
    if not isinstance(profiles, list):
        return {"ok": False, "issues": ["subject_emotion_profiles bukan list"]}
    seen = set()
    required = ("subject_id", "baseline_emotion", "emotional_role", "trigger_map", "arc", "facial_performance", "head_and_gaze", "body_performance", "hands_or_paws", "movement_quality", "micro_reactions", "attention_targets", "timing_logic")
    for profile in profiles:
        if not isinstance(profile, dict) or not profile.get("subject_id"):
            issues.append("profile tanpa subject_id")
            continue
        sid = _id(profile["subject_id"])
        if sid in seen:
            issues.append(f"duplicate performance profile: {sid}")
        seen.add(sid)
        if sid not in subjects:
            issues.append(f"profile untuk subject yang tidak terdeteksi: {sid}")
        for key in required:
            value = profile.get(key)
            if isinstance(value, str) and value.strip().lower() in {"n/a", "na", "none", "same", "consistent", "sesuai", "tidak ada"}:
                issues.append(f"{sid}: {key} terlalu generik/placeholder")
            if isinstance(value, list):
                if not value or not any(_txt(x).strip() for x in value):
                    issues.append(f"{sid}: {key} kosong")
            elif not _txt(value).strip():
                issues.append(f"{sid}: {key} kosong")
    missing = sorted(set(subjects) - seen)
    extra = sorted(seen - set(subjects))
    issues.extend(f"subject tanpa performance profile: {sid}" for sid in missing)
    issues.extend(f"profile subject tidak ada di roster: {sid}" for sid in extra)
    return {"ok": not issues, "issues": issues}


def validate_temporal_crosscheck(temporal: list, duration: float | None) -> dict:
    issues = []
    beats = [b for b in temporal if isinstance(b, dict)]
    if not beats:
        return {"ok": False, "issues": ["temporal_breakdown kosong"]}
    last_end = 0.0
    seen = set()
    for i, beat in enumerate(beats, 1):
        name = _txt(beat.get("beat") or beat.get("id") or f"beat-{i}").strip()
        if not name:
            issues.append(f"beat {i}: id/beat kosong")
            name = f"beat-{i}"
        if name.lower() in seen:
            issues.append(f"duplicate beat: {name}")
        seen.add(name.lower())
        rng = _parse_range(beat.get("waktu") or beat.get("time") or beat.get("start_time"))
        if rng is None:
            issues.append(f"beat {name}: timestamp tidak terbaca")
            continue
        start, end = rng
        if end < start:
            issues.append(f"beat {name}: end < start")
        if start + 0.01 < last_end:
            issues.append(f"beat {name}: timeline mundur/overlap")
        last_end = max(last_end, end)
        for field in ("start_state", "cause", "action", "end_state"):
            if not _txt(beat.get(field)).strip():
                issues.append(f"beat {name}: field {field} kosong")
    if duration and last_end > float(duration) + 1.0:
        issues.append(f"temporal breakdown melewati durasi video ({last_end:.2f}s > {duration:.2f}s)")
    return {"ok": not issues, "issues": issues}


def validate_temporal_keyframe_alignment(temporal: list, keyframes: list[float], tolerance: float = 2.5) -> dict:
    """Every temporal beat must have nearby visual evidence when keyframes are available."""
    if not keyframes:
        return {"ok": False, "issues": ["tidak ada timestamp keyframe evidence"]}
    issues = []
    clean = sorted(float(x) for x in keyframes)
    for beat in temporal or []:
        if not isinstance(beat, dict):
            continue
        name = _txt(beat.get("beat") or beat.get("id") or "beat").strip()
        rng = _parse_range(beat.get("waktu"))
        if rng is None:
            issues.append(f"{name}: waktu tidak terbaca")
            continue
        start, end = rng
        if not any(start - tolerance <= ts <= end + tolerance for ts in clean):
            issues.append(f"{name}: tidak memiliki keyframe evidence di sekitar {start:g}-{end:g}s")
    return {"ok": not issues, "issues": issues}


def validate_scene_coverage_complete(coverage: list, temporal_beats: list) -> dict:
    expected = {_txt(b.get("beat") or b.get("id")).strip().lower() for b in temporal_beats if isinstance(b, dict) and (b.get("beat") or b.get("id"))}
    if not isinstance(coverage, list) or not coverage:
        return {"ok": False, "issues": ["scene_coverage_map kosong"]}
    issues = []
    seen_beats = set()
    scenes = set()
    for item in coverage:
        if not isinstance(item, dict):
            issues.append("coverage item bukan object")
            continue
        scene = item.get("scene") or item.get("scene_num")
        if scene is None:
            issues.append("coverage item tanpa scene")
        else:
            scenes.add(str(scene))
        beats = {_txt(x).strip().lower() for x in (item.get("source_beats") or []) if _txt(x).strip()}
        if not beats:
            issues.append(f"scene {scene}: source_beats kosong")
        unknown = sorted(beats - expected)
        if unknown:
            issues.append(f"scene {scene}: beat tidak dikenal {unknown}")
        seen_beats |= beats
        if not _txt(item.get("source_time_window")).strip():
            issues.append(f"scene {scene}: source_time_window kosong")
        if len([x for x in (item.get("must_preserve") or []) if _txt(x).strip()]) < 1:
            issues.append(f"scene {scene}: must_preserve kosong")
        if len([x for x in (item.get("forbidden_drift") or []) if _txt(x).strip()]) < 1:
            issues.append(f"scene {scene}: forbidden_drift kosong")
    uncovered = sorted(expected - seen_beats)
    if uncovered:
        issues.append(f"temporal beat tidak dipetakan ke scene: {uncovered}")
    return {"ok": not issues, "issues": issues}


def validate_scene_coverage(scene: dict, temporal_beats: list) -> dict:
    expected = {_txt(b.get("beat") or b.get("id")).strip().lower() for b in temporal_beats if isinstance(b, dict) and (b.get("beat") or b.get("id"))}
    actual = {_txt(x).strip().lower() for x in (scene.get("source_beats") or []) if _txt(x).strip()}
    if expected and not actual:
        return {"ok": False, "issues": ["scene source_beats kosong"]}
    unknown = sorted(actual - expected)
    return {"ok": not unknown, "issues": [f"scene memakai beat yang tidak ada: {unknown}"] if unknown else []}


def _state_items(scene: dict, key: str, group: str) -> dict:
    state = scene.get(key) or {}
    items = state.get(group) or [] if isinstance(state, dict) else []
    return {_id(x.get("id")): x for x in items if isinstance(x, dict) and x.get("id")}


def _contradicts(prev_text: str, cur_text: str, pairs: list[tuple[str, str]]) -> bool:
    p, c = prev_text.lower(), cur_text.lower()
    return any(a in p and b in c for a, b in pairs)


def validate_scene_transition(previous: dict, current: dict) -> dict:
    """Hard END→START reconciliation for subject/object/environment/camera state."""
    issues = []
    if not previous or not current:
        return {"ok": False, "issues": ["previous/current scene contract kosong"]}

    prev_s = _state_items(previous, "end_state", "subjects")
    cur_s = _state_items(current, "start_state", "subjects")
    if not prev_s or not cur_s:
        issues.append("subject state END→START tidak dapat direkonsiliasi")
    for sid in sorted(set(prev_s) | set(cur_s)):
        if sid not in prev_s:
            issues.append(f"subject {sid}: muncul di START tanpa END state sebelumnya")
            continue
        if sid not in cur_s:
            issues.append(f"subject {sid}: hilang di START scene berikutnya")
            continue
        p, c = _txt(prev_s[sid]), _txt(cur_s[sid])
        pairs = [
            ("front passenger", "rear seat"), ("rear passenger", "front passenger"),
            ("kursi depan", "kursi belakang"), ("kursi belakang", "kursi depan"),
            ("left", "right"), ("right", "left"), ("kiri", "kanan"), ("kanan", "kiri"),
            ("inside car", "outside car"), ("outside car", "inside car"),
            ("dalam mobil", "di luar mobil"), ("di luar mobil", "dalam mobil"),
        ]
        for a, b in pairs:
            if a in p.lower() and b in c.lower():
                issues.append(f"subject {sid}: state berubah dari '{a}' ke '{b}' tanpa bridge transition")

    prev_o = _state_items(previous, "end_state", "objects")
    cur_o = _state_items(current, "start_state", "objects")
    for oid in sorted(set(prev_o) & set(cur_o)):
        p, c = _txt(prev_o[oid]), _txt(cur_o[oid])
        for a, b in [("held", "ground"), ("dipegang", "di tanah"), ("intact", "broken"), ("utuh", "rusak")]:
            if a in p.lower() and b in c.lower():
                issues.append(f"object {oid}: state berubah dari '{a}' ke '{b}' tanpa action bridge")

    pb, cb = _txt(previous.get("end_state")), _txt(current.get("start_state"))
    env_pairs = [
        ("daylight", "night"), ("night", "daylight"), ("siang", "malam"), ("malam", "siang"),
        ("inside", "outside"), ("inside", "outdoor"), ("dalam", "luar"),
    ]
    for a, b in env_pairs:
        if a in pb.lower() and b in cb.lower():
            issues.append(f"environment berubah dari '{a}' ke '{b}' tanpa transition")
    return {"ok": not issues, "issues": issues}


def validate_causal_integrity(scene: dict) -> dict:
    issues = []
    if not _txt(scene.get("cause")).strip():
        issues.append("cause kosong")
    if not _txt(scene.get("aksi")).strip():
        issues.append("action kosong")
    fidelity = scene.get("fidelity_audit") or {}
    for k in ("motion_physics", "action_critical_props_preserved"):
        if not _txt(fidelity.get(k)).strip():
            issues.append(f"fidelity_audit.{k} kosong")
    return {"ok": not issues, "issues": issues}


def validate_prompt_against_contract(prompt: str, scene: dict) -> dict:
    p = (prompt or "").lower()
    issues = []
    start, end = _txt(scene.get("start_state")), _txt(scene.get("end_state"))
    combined = start + " " + end
    pairs = [
        (("front passenger", "rear seat"), "front passenger → rear seat"),
        (("rear passenger", "front passenger"), "rear passenger → front passenger"),
        (("kursi depan", "back seat"), "kursi depan → back seat"),
        (("kursi belakang", "front seat"), "kursi belakang → front seat"),
    ]
    for (a, b), label in pairs:
        if a in combined.lower() and b in p:
            issues.append(f"prompt memindahkan {label}")
    return {"ok": not issues, "issues": issues}
