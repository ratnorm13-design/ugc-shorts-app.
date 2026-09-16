import ast, pathlib, re, zipfile

root = pathlib.Path(__file__).parent
app = (root / "app.py").read_text()
core = (root / "validation_core.py").read_text()

ast.parse(app); ast.parse(core)
for text, name in ((app, "app.py"), (core, "validation_core.py")):
    tree = ast.parse(text)
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    dup = sorted({x for x in funcs if funcs.count(x) > 1})
    assert not dup, f"duplicate functions in {name}: {dup}"

assert 'APP_VERSION = "5.17 RC' in app
assert 'reference_fidelity' in app and 'validate_reference_fidelity' in app
assert 'validate_performance_profiles' in app
assert 'reference_keyframe_timestamps' in app
assert 'validate_temporal_keyframe_alignment' in app
assert 'validate_scene_coverage_complete' in app
assert 'getattr(response, "parsed", None)' in app

assert 'validate_subject_roster_strict' in app
assert 'PROBE_SUBJECT_ROSTER_SCHEMA' in app
assert 'preserve_validation=True' in app
assert 'client = get_client()\n    client = get_client()' not in app
assert 'reference_gemini_compatible.mp4' in app
print("V5.17 static release tests: PASS")
