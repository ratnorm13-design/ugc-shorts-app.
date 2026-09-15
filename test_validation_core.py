from validation_core import *

def ok(x): assert x["ok"], x

def fail(x): assert not x["ok"], x

probe=[{"id":"S1","jenis":"cat","peran":"protagonist"},{"id":"S2","jenis":"dog","peran":"reaction"}]
analysis=[{"id":"S1","jenis":"cat","peran":"protagonist"},{"id":"S2","jenis":"dog","peran":"reaction"}]
ok(reconcile_subject_rosters(probe,analysis))
fail(reconcile_subject_rosters(probe,[{"id":"S1","jenis":"cat","peran":"protagonist"}]))
ok(validate_temporal_crosscheck([
 {"beat":"hook","start_time":"0s","end_time":"3s","start_state":"A","cause":"B","action":"C","end_state":"D"},
 {"beat":"payoff","start_time":"3s","end_time":"8s","start_state":"D","cause":"E","action":"F","end_state":"G"}],8))
fail(validate_temporal_crosscheck([{"beat":"bad","start_time":"7s","end_time":"3s","start_state":"A","cause":"B","action":"C","end_state":"D"}],8))
prev={"end_state":{"subjects":[{"id":"S2","position":"front passenger seat"}]}}
cur={"start_state":{"subjects":[{"id":"S2","position":"rear seat"}]}}
fail(validate_scene_transition(prev,cur))
ok(validate_causal_integrity({"cause":"car accelerates","aksi":"dog reacts","fidelity_audit":{"motion_physics":"tire motion","action_critical_props_preserved":"lollipop"}}))
fail(validate_causal_integrity({"cause":"","aksi":"","fidelity_audit":{}}))
print('V5.15 validation_core tests: PASS')
