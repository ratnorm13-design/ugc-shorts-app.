from validation_core import *

def ok(x): assert x["ok"], x

def fail(x): assert not x["ok"], x

probe=[{"id":"S1","jenis":"cat","peran":"protagonist"},{"id":"S2","jenis":"dog","peran":"reaction"}]
analysis=[{"id":"S1","jenis":"cat","peran":"protagonist"},{"id":"S2","jenis":"dog","peran":"reaction"}]
ok(reconcile_subject_rosters(probe,analysis))
fail(reconcile_subject_rosters(probe,[{"id":"S1","jenis":"cat","peran":"protagonist"}]))

fidelity={
 "camera_geometry":"kamera berada rendah di sisi depan kendaraan dengan arah pandang mengikuti gerak maju",
 "subject_geography":"S1 di kursi pengemudi dan S2 di kursi penumpang depan di sisi kanan frame",
 "motion_physics_map":"kendaraan bergerak maju cepat; debu berasal dari kontak roda dengan permukaan tanah",
 "action_critical_props":"O1 berupa lollipop berada di tangan S1 dan tetap terlihat sebelum reaksi utama",
 "hook_mechanics":"0-3s menampilkan kendaraan bergerak cepat dan ekspresi percaya diri sebagai anomaly hook",
 "payoff_fidelity":"payoff terjadi setelah kendaraan berhenti dan debu mengendap pada akhir reference",
 "must_preserve":["posisi S1/S2","sumber debu","urutan cause-effect"],
 "forbidden_drift":["memindahkan S2 ke belakang","mengubah sumber debu"]
}
ok(validate_reference_fidelity(fidelity))
fail(validate_reference_fidelity({}))
fail(validate_reference_fidelity({k:v for k,v in fidelity.items() if k!='hook_mechanics'}))

roster=[{"id":"S1","jenis":"cat","peran":"protagonist"},{"id":"S2","jenis":"dog","peran":"reaction"}]
profile={"subject_id":"S1","baseline_emotion":"tenang","emotional_role":"leader","trigger_map":["x"],"arc":["a"],"facial_performance":["a"],"head_and_gaze":["a"],"body_performance":["a"],"hands_or_paws":["a"],"movement_quality":["a"],"micro_reactions":["a"],"attention_targets":["a"],"timing_logic":"a"}
ok(validate_performance_profiles(roster,[profile | {}])) if False else None
fail(validate_performance_profiles(roster,[profile]))
ok(validate_performance_profiles(roster,[profile, dict(profile, subject_id="S2")]))

beats=[
 {"beat":"hook","waktu":"0-3s","start_state":"A","cause":"B","action":"C","end_state":"D"},
 {"beat":"payoff","waktu":"3-8s","start_state":"D","cause":"E","action":"F","end_state":"G"}
]
ok(validate_temporal_crosscheck(beats,8))
fail(validate_temporal_crosscheck([{"beat":"bad","waktu":"7-3s","start_state":"A","cause":"B","action":"C","end_state":"D"}],8))
ok(validate_temporal_keyframe_alignment(beats,[0.0,2.5,4.0,7.5]))
fail(validate_temporal_keyframe_alignment(beats,[20.0]))

coverage=[
 {"scene":1,"source_time_window":"0-8s","source_beats":["hook","payoff"],"must_preserve":["cause"],"forbidden_drift":["position"]}
]
ok(validate_scene_coverage_complete(coverage,beats))
fail(validate_scene_coverage_complete([{**coverage[0],"source_beats":[]}],beats))

prev={"end_state":{"subjects":[{"id":"S2","position":"front passenger seat"}]}}
cur={"start_state":{"subjects":[{"id":"S2","position":"rear seat"}]}}
fail(validate_scene_transition(prev,cur))
ok(validate_causal_integrity({"cause":"car accelerates","aksi":"dog reacts","fidelity_audit":{"motion_physics":"tire motion","action_critical_props_preserved":"lollipop"}}))
fail(validate_causal_integrity({"cause":"","aksi":"","fidelity_audit":{}}))
print('V5.17 validation_core tests: PASS')
