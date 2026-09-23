import ast
from pathlib import Path

APP = Path(__file__).with_name('app.py')
source = APP.read_text(encoding='utf-8')
tree = ast.parse(source)

# Syntax / duplicate-function gate.
funcs = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
assert len(funcs) == len(set(funcs)), 'Duplicate top-level functions found.'

# Architecture gates.
assert 'from google import genai' in source
assert 'from google.genai import types' in source
assert 'client.files.upload' in source
assert 'types.Part.from_uri' in source
assert 'media_processing="AGENTIC"' in source
assert 'ffprobe' in source
assert 'gemini-3.8-flash' in source
assert 'gemini-3.7-flash' in source
assert 'gemini-3.6-flash' in source
assert 'gemini-3.5-flash-lite' in source

# Removed legacy/dead paths.
for forbidden in (
    'google.generativeai',
    'gemini-2.5-flash',
    'temperature=',
    'top_p=',
    'top_k=',
    'Generate ALL Scenes',
    'custom_instruction',
):
    assert forbidden not in source, f'Forbidden legacy/dead path remains: {forbidden}'

# Sequential bridge gate.
assert '_has_valid_previous_frame' in source
assert 'Scene berikutnya →' in source
assert 'Upload Last Frame Scene' in source

print('V15.1 static release gate: PASS')
