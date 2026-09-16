from validation_core import validate_reference_fidelity, validate_performance_profiles, validate_scene_coverage_complete, validate_temporal_keyframe_alignment

def must_fail(result, label):
    assert not result["ok"], f"BUG NOT CAUGHT: {label}: {result}"

must_fail(validate_reference_fidelity({}), "empty reference_fidelity")
must_fail(validate_reference_fidelity({
    "camera_geometry":"kamera konsisten","subject_geography":"subjek konsisten",
    "motion_physics_map":"gerakan konsisten","action_critical_props":"prop konsisten",
    "hook_mechanics":"hook konsisten","payoff_fidelity":"payoff konsisten",
    "must_preserve":["something"],"forbidden_drift":["something"]}), "generic fidelity")

roster=[{"id":"S1","jenis":"cat","peran":"protagonist"},{"id":"S2","jenis":"dog","peran":"reaction"}]
complete={"subject_id":"S1","baseline_emotion":"calm","emotional_role":"leader",
"trigger_map":["trigger"],"arc":["start","end"],"facial_performance":["visible"],
"head_and_gaze":["gaze"],"body_performance":["posture"],"hands_or_paws":["paw tension"],
"movement_quality":["movement"],"micro_reactions":["reaction"],"attention_targets":["target"],"timing_logic":"after trigger"}
missing_hands=dict(complete); missing_hands.pop("hands_or_paws")
must_fail(validate_performance_profiles(roster,[missing_hands]), "missing hands_or_paws")
must_fail(validate_performance_profiles(roster,[complete]), "missing S2 profile")

must_fail(validate_scene_coverage_complete([{"scene":1,"source_time_window":"0-8s","source_beats":[],"must_preserve":["hook"],"forbidden_drift":["position"]}], [{"beat":1,"waktu":"0-3s"}]), "coverage missing beat")
must_fail(validate_temporal_keyframe_alignment([{"beat":1,"waktu":"0-3s"}], []), "missing keyframe evidence")
print("V5.17 preflight tests: expected failures were caught")
