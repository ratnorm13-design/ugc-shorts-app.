"""Deterministic validation core for UGC Remix Studio V5.15.
No Gemini/network calls. Safe to unit-test independently.
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


def subject_signature(item: dict) -> tuple[str, str, str]:
    return (
        _id(item.get("id")),
        _id(item.get("jenis")),
        _id(item.get("peran")),
    )


def reconcile_subject_rosters(probe: list, analysis: list) -> dict:
    p = { _id(x.get("id")): x for x in probe if isinstance(x, dict) and x.get("id") }
    a = { _id(x.get("id")): x for x in analysis if isinstance(x, dict) and x.get("id") }
    missing = sorted(set(p) - set(a))
    extra = sorted(set(a) - set(p))
    conflicts = []
    for sid in sorted(set(p) & set(a)):
        ps, ass = subject_signature(p[sid]), subject_signature(a[sid])
        if ps[1:] != ass[1:]:
            conflicts.append({"id": sid, "probe": ps, "analysis": ass})
    ok = not missing and not extra and not conflicts
    return {"ok": ok, "missing": missing, "extra": extra, "conflicts": conflicts}


def _parse_seconds(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    s = _txt(value).lower().replace(",", ".")
    nums = re.findall(r"\d+(?:\.\d+)?", s)
    if not nums:
        return None
    if ":" in s:
        parts = re.findall(r"\d+(?:\.\d+)?", s)
        if len(parts) >= 2:
            return float(parts[-2]) * 60 + float(parts[-1])
    return float(nums[0])


def validate_temporal_crosscheck(temporal: list, duration: float | None) -> dict:
    issues = []
    beats = [b for b in temporal if isinstance(b, dict)]
    if not beats:
        return {"ok": False, "issues": ["temporal_breakdown kosong"]}
    last_end = 0.0
    seen = set()
    for i, beat in enumerate(beats, 1):
        name = _txt(beat.get("beat") or beat.get("id") or f"beat-{i}").strip()
        if name in seen:
            issues.append(f"duplicate beat: {name}")
        seen.add(name)
        start = _parse_seconds(beat.get("start_time", beat.get("time", beat.get("waktu"))))
        end = _parse_seconds(beat.get("end_time"))
        if start is None:
            issues.append(f"beat {name}: timestamp tidak terbaca")
            continue
        if end is None:
            end = start
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


def validate_scene_coverage(scene: dict, temporal_beats: list) -> dict:
    expected = {
        _txt(b.get("beat") or b.get("id")).strip().lower()
        for b in temporal_beats if isinstance(b, dict) and (b.get("beat") or b.get("id"))
    }
    actual = {_txt(x).strip().lower() for x in (scene.get("source_beats") or []) if _txt(x).strip()}
    if expected and not actual:
        return {"ok": False, "issues": ["scene source_beats kosong"]}
    unknown = sorted(actual - expected)
    if unknown:
        return {"ok": False, "issues": [f"scene memakai beat yang tidak ada: {unknown}"]}
    return {"ok": True, "issues": []}


def _subject_states(scene: dict, key: str) -> dict:
    state = scene.get(key) or {}
    items = (state.get("subjects") or []) if isinstance(state, dict) else []
    return {_id(x.get("id")): x for x in items if isinstance(x, dict) and x.get("id")}


def _object_states(scene: dict, key: str) -> dict:
    state = scene.get(key) or {}
    items = (state.get("objects") or []) if isinstance(state, dict) else []
    return {_id(x.get("id")): x for x in items if isinstance(x, dict) and x.get("id")}


def _contradicts(prev_text: str, cur_text: str, pairs: list[tuple[str, str]]) -> bool:
    p, c = prev_text.lower(), cur_text.lower()
    return any(a in p and b in c for a, b in pairs)


def validate_scene_transition(previous: dict, current: dict) -> dict:
    issues = []
    prev_s = _subject_states(previous, "end_state")
    cur_s = _subject_states(current, "start_state")
    for sid in sorted(set(prev_s) & set(cur_s)):
        p = _txt(prev_s[sid])
        c = _txt(cur_s[sid])
        if _contradicts(p, c, [("front passenger", "rear"), ("rear passenger", "front"), ("kursi depan", "kursi belakang"), ("front seat", "back seat"), ("driver", "rear seat")]):
            issues.append(f"subject {sid}: posisi kursi berubah tanpa transition")
        if _contradicts(p, c, [("left", "right"), ("kanan", "kiri")]):
            issues.append(f"subject {sid}: sisi kiri/kanan berubah tanpa transition")
    prev_o = _object_states(previous, "end_state")
    cur_o = _object_states(current, "start_state")
    for oid in sorted(set(prev_o) & set(cur_o)):
        p, c = _txt(prev_o[oid]), _txt(cur_o[oid])
        if _contradicts(p, c, [("held", "ground"), ("dipegang", "di tanah"), ("intact", "broken"), ("utuh", "rusak")]):
            issues.append(f"object {oid}: state berubah tanpa action bridge")
    pb = _txt(previous.get("end_state"))
    cb = _txt(current.get("start_state"))
    if _contradicts(pb, cb, [("inside car", "outside car"), ("dalam mobil", "di luar mobil"), ("daylight", "night"), ("siang", "malam")]):
        issues.append("environment/location berubah secara diskontinu")
    return {"ok": not issues, "issues": issues}


def validate_causal_integrity(scene: dict) -> dict:
    issues = []
    cause = _txt(scene.get("cause"))
    action = _txt(scene.get("aksi"))
    if not cause.strip():
        issues.append("cause kosong")
    if not action.strip():
        issues.append("action kosong")
    fidelity = scene.get("fidelity_audit") or {}
    for k in ("motion_physics", "action_critical_props_preserved"):
        if not _txt(fidelity.get(k)).strip():
            issues.append(f"fidelity_audit.{k} kosong")
    return {"ok": not issues, "issues": issues}


def validate_prompt_against_contract(prompt: str, scene: dict) -> dict:
    p = (prompt or "").lower()
    issues = []
    start = _txt(scene.get("start_state"))
    end = _txt(scene.get("end_state"))
    combined = start + " " + end
    if "front passenger" in combined and "rear seat" in p:
        issues.append("prompt memindahkan front passenger ke rear seat")
    if "rear passenger" in combined and "front passenger" in p:
        issues.append("prompt memindahkan rear passenger ke front passenger")
    if "kursi depan" in combined and "back seat" in p:
        issues.append("prompt memindahkan kursi depan ke back seat")
    if "kursi belakang" in combined and "front seat" in p:
        issues.append("prompt memindahkan kursi belakang ke front seat")
    # Critical props explicitly named in the contract must survive into the prompt.
    props = scene.get("fidelity_audit", {}).get("action_critical_props_preserved", "")
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", _txt(props)):
        if token.lower() not in p and token.lower() not in {"preserved", "preserve", "reference", "action", "critical"}:
            # Only flag strongly named quoted/ID-like props, not generic English words.
            if token[:1].isupper() or token.lower() in {"lollipop", "steering", "dashboard"}:
                issues.append(f"critical prop '{token}' tidak ditemukan di prompt")
    return {"ok": not issues, "issues": issues}
