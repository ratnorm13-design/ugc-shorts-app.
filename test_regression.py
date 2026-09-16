"""Golden/adversarial regression tests for the known continuity failure mode."""
from validation_core import *


def must_fail(r, name):
    assert not r["ok"], f"REGRESSION LEAK: {name}: {r}"


def must_pass(r, name):
    assert r["ok"], f"FALSE BLOCK: {name}: {r}"

# Golden reference: S1 driver, S2 front passenger, fast vehicle, dust from wheels,
# S2 reacts late, S1 remains stoic, lollipop stays action-critical.
roster = [
    {"id":"S1","jenis":"kitten","peran":"protagonist"},
    {"id":"S2","jenis":"dog","peran":"reaction"},
]
profiles = []
for sid, emotion in (("S1","confident"),("S2","surprised")):
    profiles.append({
        "subject_id": sid, "baseline_emotion": emotion, "emotional_role": "leader" if sid=="S1" else "late_reactor",
        "trigger_map":["vehicle acceleration triggers visible reaction"], "arc":[emotion,"attention shift","reaction","end state"],
        "facial_performance":["eyes and mouth visibly change"], "head_and_gaze":["gaze follows trigger"],
        "body_performance":["posture changes with cause"], "hands_or_paws":["paw tension changes"], "movement_quality":["continuous motion"],
        "micro_reactions":["brief glance"], "attention_targets":["vehicle motion"], "timing_logic":"react after trigger"
    })
must_pass(validate_performance_profiles(roster, profiles), "complete performance profiles")
must_fail(validate_performance_profiles(roster, profiles[:1]), "missing S2 profile")

fidelity = {
    "camera_geometry":"low front-side camera tracks the moving vehicle and keeps both front seats visible",
    "subject_geography":"S1 stays in driver seat; S2 stays adjacent in the front passenger seat",
    "motion_physics_map":"vehicle accelerates forward; dust originates at tire-ground contact, not from an unrelated object",
    "action_critical_props":"lollipop remains with S1 through the setup and is visible before the reaction",
    "hook_mechanics":"first seconds show fast motion plus S1's calm confidence while S2 is exposed to the movement",
    "payoff_fidelity":"vehicle halts in dirt and the reaction resolves after the stop",
    "must_preserve":["front-seat adjacency","dust source at wheels","S1 stoic performance"],
    "forbidden_drift":["move S2 to rear seat","invent a crash or new prop"]
}
must_pass(validate_reference_fidelity(fidelity), "golden fidelity")
must_fail(validate_reference_fidelity({}), "empty fidelity")

scene1 = {
    "end_state":{"subjects":[{"id":"S1","position":"driver seat, stoic"},{"id":"S2","position":"front passenger seat, reacting"}],
                 "objects":[{"id":"O1","status":"held by S1, intact"}]},
}
scene2_bad = {
    "start_state":{"subjects":[{"id":"S1","position":"driver seat, laughing"},{"id":"S2","position":"rear seat"}],
                   "objects":[{"id":"O1","status":"on ground, broken"}]},
}
must_fail(validate_scene_transition(scene1, scene2_bad), "cross-scene geography/prop drift")

contract = {
    "start_state": {"subjects":[{"id":"S2","position":"front passenger seat"}]},
    "end_state": {"subjects":[{"id":"S2","position":"front passenger seat"}]},
}
must_fail(validate_prompt_against_contract("The dog moves to the rear seat and stays there.", contract), "prompt contract contradiction")

print("V5.17 golden regression tests: PASS")
