import json
import re
import time
from typing import Any

import streamlit as st
from google import genai
from google.genai import types


# ============================================================
# CONFIG
# ============================================================

MODEL = "gemini-3.6-flash"

DURATION_MAP = {
    "8 detik": 1,
    "16 detik": 2,
    "24 detik": 3,
    "32 detik": 4,
    "40 detik": 5,
    "48 detik": 6,
    "56 detik": 7,
    "1 menit": 8,
    "1.5 menit": 12,
    "2 menit": 15,
    "2.5 menit": 19,
    "3 menit": 23,
}

STYLE_OPTIONS = [
    "Realistic",
    "3D Animation",
    "Cartoon",
    "Pixar-like 3D animation",
    "Cinematic",
    "Cute Kids Animation",
]

ASPECT_OPTIONS = [
    "9:16 Vertical",
    "16:9 Horizontal",
    "1:1 Square",
]

REFERENCE_OPTIONS = [
    "Video",
    "Screenshots",
    "Text / Idea",
]


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "page": "home",
    "analysis": None,
    "concepts": [],
    "selected_concept": None,
    "storyboard": [],
    "scene_prompts": {},
    "scene_frames": {},
    "seo": None,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# ORIGINALITY ENGINE
# ============================================================

ORIGINALITY_RULES = """
ORIGINALITY RULES:

- Keep the same main subject/type as the reference.
- If the reference's main subject is a cat, keep the main subject a cat.
- Do not randomly replace the main subject with a robot, human, different animal,
  or unrelated creature.
- Preserve the same core comedic scene sequence.
- Preserve the important actions, cause-and-effect, timing, setup, and main joke.
- Do not change the main comedic event merely to make the result different.
- Make the result original mainly through execution details:
  environment details, colors, wardrobe, props, composition, camera movement,
  lens feel, lighting, textures, facial expressions, animation design,
  sound design, and secondary visual details.
- Do not copy recognizable characters, logos, brands, exact dialogue,
  exact shots, or distinctive creator/studio style.
- The final result should feel like an original production while preserving
  the entertainment logic of the reference.
- The ending/payoff may be made funnier with an additional harmless reaction,
  funny expression, exaggerated movement, or small comedic twist.
- Keep the main subject visually consistent across all scenes.
"""


# ============================================================
# ACTION CONTINUITY ENGINE
# ============================================================

ACTION_CONTINUITY_RULES = """
ACTION CONTINUITY RULES:

Every important action must happen visibly and sequentially.

Never skip, magically complete, or instantly transform an important action.

Break important actions into natural physical stages such as:

1. Preparation
2. Approach / movement toward the object
3. Physical contact
4. Grip / interaction
5. Manipulation or visible action
6. Main action
7. Visible result
8. Reaction / comedic payoff

The exact stages depend on the reference.

Objects must not suddenly become:
- opened
- peeled
- broken
- moved
- transformed
- consumed
- completed
- activated
- changed in appearance

unless a visible action causes that change.

Do NOT allow:
- magical state changes
- instant transformations
- unexplained object movement
- unexplained object disappearance
- unexplained object appearance
- sudden completed tasks
- teleporting props
- sudden changes of pose
- sudden changes of environment

If an action starts in one state, continue logically from that state.

Example:

If a character interacts with an unpeeled food item,
the result must not suddenly show the food already peeled.

The visible sequence should communicate:
approach → touch → hold → perform the action → visible change → result.

For physical comedy, preserve the original comedic timing while making
every important cause-and-effect relationship visually understandable.

If a complex action cannot naturally fit inside one scene,
distribute the action across consecutive scenes while preserving continuity.

Every scene must have a clear beginning state and ending state.

The ending state of Scene N becomes the starting state of Scene N+1.
"""


# ============================================================
# SAFETY
# ============================================================

SAFETY_RULES = """
SAFETY RULES:

If the reference contains a dangerous real-world action, do not reproduce
instructions that teach or facilitate the dangerous action.

Preserve the harmless narrative/comedic structure where possible, but replace
only the dangerous element with a clearly fictional, toy-like, unplugged,
non-functional, or otherwise harmless equivalent.

Do not provide operational instructions for real weapons, explosives,
live electricity, dangerous chemicals, or other hazardous activities.

The scene should remain visually clear, comedic, and safe.
"""


# ============================================================
# BASIC HELPERS
# ============================================================

def reset_project():
    for key, value in DEFAULT_STATE.items():
        st.session_state[key] = value


def go(page: str):
    st.session_state.page = page
    st.rerun()


def scene_count(duration: str) -> int:
    return DURATION_MAP.get(duration, 1)


def selected_concept() -> dict:
    idx = st.session_state.selected_concept

    if idx is None:
        return {}

    concepts = st.session_state.concepts

    if not concepts:
        return {}

    if idx < 0 or idx >= len(concepts):
        return {}

    return concepts[idx]


def safe_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


# ============================================================
# GEMINI
# ============================================================

def get_client():
    api_key = st.session_state.get("api_key", "")

    if not api_key:
        return None

    return genai.Client(api_key=api_key)


def ask(client, prompt, parts=None):
    content = [prompt] + (parts or [])

    last_error = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=content,
                config=types.GenerateContentConfig(
                    temperature=0.8
                )
            )

            return response.text or ""

        except Exception as e:
            last_error = e

            if "503" in str(e) or "UNAVAILABLE" in str(e):
                time.sleep(3 * (attempt + 1))
                continue

            raise e

    raise RuntimeError(
        "Gemini sedang sibuk setelah 3 percobaan.\n\n"
        "Coba tekan tombol lagi beberapa saat kemudian.\n\n"
        f"Error: {last_error}"
    )


# ============================================================
# JSON EXTRACTION
# ============================================================

def extract_json(text: str):
    text = text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL
    )

    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    match = re.search(
        r"\[.*\]",
        text,
        flags=re.DOTALL
    )

    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    raise ValueError("Output AI bukan JSON yang valid.")


# ============================================================
# FILE UPLOAD
# ============================================================

def upload_file(client, uploaded_file):
    if not uploaded_file:
        return None

    try:
        mime = getattr(
            uploaded_file,
            "type",
            None
        )

        return client.files.upload(
            file=uploaded_file,
            config={
                "display_name": uploaded_file.name,
                "mime_type": mime,
            }
        )

    except Exception as e:
        st.warning(
            f"Upload file gagal: {e}"
        )

        return None


def file_part(client, uploaded_file):
    uploaded = upload_file(
        client,
        uploaded_file
    )

    if not uploaded:
        return []

    return [
        uploaded
    ]


# ============================================================
# PREVIOUS SCENE INFO
# ============================================================

def previous_scene_info(scene_number: int) -> str:
    scenes = st.session_state.storyboard

    if scene_number <= 1:
        return "No previous scene. This is Scene 1."

    previous_index = scene_number - 2

    if previous_index < 0:
        return "No previous scene."

    if previous_index >= len(scenes):
        return "Previous scene information unavailable."

    previous = scenes[previous_index]

    return f"""
Previous Scene #{scene_number - 1}

Purpose:
{safe_text(previous.get("purpose"))}

Visual:
{safe_text(previous.get("visual"))}

Action:
{safe_text(previous.get("action"))}

Micro Actions:
{safe_text(previous.get("micro_actions"))}

Ending State:
{safe_text(previous.get("ending_state"))}

Continuity:
{safe_text(previous.get("continuity"))}

Camera:
{safe_text(previous.get("camera"))}

Audio:
{safe_text(previous.get("audio"))}
"""


# ============================================================
# ANALYZER
# ============================================================

def run_analysis():
    client = get_client()

    if client is None:
        st.error(
            "Masukkan Gemini API Key terlebih dahulu."
        )
        return

    reference_type = st.session_state.reference_type
    duration = st.session_state.duration
    style = st.session_state.style
    aspect = st.session_state.aspect
    instruction = st.session_state.creative_instruction

    parts = []

    reference_text = ""

    if reference_type == "Video":
        video = st.session_state.reference_video

        if video:
            parts.extend(
                file_part(
                    client,
                    video
                )
            )

        reference_text = """
The uploaded reference is a video.
Analyze its visual sequence, subjects, actions, timing,
cause-and-effect, comedic beats, and important physical interactions.
"""

    elif reference_type == "Screenshots":
        screenshots = st.session_state.reference_screenshots or []

        for image in screenshots:
            parts.extend(
                file_part(
                    client,
                    image
                )
            )

        reference_text = """
The uploaded references are screenshots.
Infer the scene order, visual continuity, important actions,
subject identity, object states, and comedic progression.
"""

    else:
        reference_text = f"""
The user provided this text/idea:

{st.session_state.reference_text}

Treat it as the creative reference.
"""

    prompt = f"""
You are an AI video concept analyzer.

Analyze the user's reference and create exactly 3 original remix concepts.

IMPORTANT:

The reference determines the niche and the type of content.

Do not randomly change the main subject.

If the reference is about a cat, the concepts should remain about the cat.
If the reference is about a specific type of object or character,
preserve that main subject/type.

Preserve the important comedic scene logic, core actions,
cause-and-effect, and timing.

Make the result original through visual execution and secondary details.

{ORIGINALITY_RULES}

{ACTION_CONTINUITY_RULES}

{SAFETY_RULES}

{reference_text}

Target duration:
{duration}

Target scene count:
{scene_count(duration)}

Visual style:
{style}

Aspect ratio:
{aspect}

Additional creative instruction:
{instruction}

Return ONLY valid JSON.

The JSON must have this structure:

{{
  "analysis": {{
    "summary": "...",
    "main_subject": "...",
    "content_type": "...",
    "core_story": "...",
    "core_actions": [],
    "action_sequence": [],
    "micro_actions": [],
    "comedic_beats": [],
    "visual_identity": "...",
    "continuity_requirements": []
  }},
  "concepts": [
    {{
      "title": "...",
      "hook": "...",
      "description": "...",
      "main_subject": "...",
      "core_scene_sequence": [],
      "action_sequence": [],
      "micro_actions": [],
      "visual_execution": "...",
      "ending_payoff": "...",
      "originality_notes": "..."
    }},
    {{
      "title": "...",
      "hook": "...",
      "description": "...",
      "main_subject": "...",
      "core_scene_sequence": [],
      "action_sequence": [],
      "micro_actions": [],
      "visual_execution": "...",
      "ending_payoff": "...",
      "originality_notes": "..."
    }},
    {{
      "title": "...",
      "hook": "...",
      "description": "...",
      "main_subject": "...",
      "core_scene_sequence": [],
      "action_sequence": [],
      "micro_actions": [],
      "visual_execution": "...",
      "ending_payoff": "...",
      "originality_notes": "..."
    }}
  ]
}}

Analysis, concepts, and all JSON content must be written in Indonesian.
"""

    try:
        raw = ask(
            client,
            prompt,
            parts
        )

        data = extract_json(raw)

        concepts = data.get(
            "concepts",
            []
        )

        if len(concepts) < 3:
            raise ValueError(
                "AI tidak menghasilkan 3 konsep."
            )

        st.session_state.analysis = data.get(
            "analysis",
            {}
        )

        st.session_state.concepts = concepts[:3]
        st.session_state.selected_concept = None
        st.session_state.storyboard = []
        st.session_state.scene_prompts = {}
        st.session_state.scene_frames = {}
        st.session_state.seo = None

        go("concepts")

    except Exception as e:
        st.error(
            f"Analisis gagal: {e}"
        )


# ============================================================
# HOME PAGE
# ============================================================

def render_home():

    st.title(
        "🎬 UGC Shorts AI Remix Engine"
    )

    st.caption(
        "Reference → AI Analyzer → 3 Concepts → Storyboard → "
        "Flow/Veo Prompts → SEO"
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "1. Reference"
        )

        reference_type = st.selectbox(
            "Reference type",
            REFERENCE_OPTIONS,
            key="reference_type"
        )

        if reference_type == "Video":

            st.session_state.reference_video = st.file_uploader(
                "Upload reference video",
                type=[
                    "mp4",
                    "mov",
                    "webm",
                    "mkv"
                ],
                key="reference_video"
            )

        elif reference_type == "Screenshots":

            st.session_state.reference_screenshots = st.file_uploader(
                "Upload screenshots",
                type=[
                    "png",
                    "jpg",
                    "jpeg",
                    "webp"
                ],
                accept_multiple_files=True,
                key="reference_screenshots"
            )

        else:

            st.session_state.reference_text = st.text_area(
                "Describe your reference / idea",
                height=180,
                placeholder=(
                    "Contoh: seekor kucing melakukan aksi lucu "
                    "dengan sebuah telur..."
                ),
                key="reference_text"
            )

    with col2:

        st.subheader(
            "2. Video Settings"
        )

        st.selectbox(
            "Duration",
            list(DURATION_MAP.keys()),
            key="duration"
        )

        st.selectbox(
            "Visual Style",
            STYLE_OPTIONS,
            key="style"
        )

        st.selectbox(
            "Aspect Ratio",
            ASPECT_OPTIONS,
            key="aspect"
        )

        st.text_area(
            "Creative Instruction",
            height=120,
            placeholder=(
                "Contoh: buat ending lebih lucu, "
                "ekspresi karakter lebih kocak..."
            ),
            key="creative_instruction"
        )

    st.divider()

    st.subheader(
        "3. AI Analyzer"
    )

    st.info(
        f"Durasi {st.session_state.duration} = "
        f"{scene_count(st.session_state.duration)} scene "
        f"(±8 detik per scene)."
    )

    if st.button(
        "🚀 ANALYZE & CREATE 3 CONCEPTS",
        type="primary",
        use_container_width=True
    ):
        run_analysis()
    # ============================================================
# PART 2/3
# CONCEPTS + STORYBOARD
# ============================================================


# ============================================================
# CONCEPTS PAGE
# ============================================================

def render_concepts():

    st.title("💡 3 Original Concepts")

    if not st.session_state.concepts:
        st.info("Belum ada konsep. Kembali ke Home.")
        if st.button("🏠 Kembali ke Home"):
            go("home")
        return

    analysis = st.session_state.analysis or {}

    with st.expander("🔎 Hasil Analisis Reference", expanded=False):

        st.write(
            "**Main Subject:**",
            safe_text(analysis.get("main_subject"))
        )

        st.write(
            "**Content Type:**",
            safe_text(analysis.get("content_type"))
        )

        st.write(
            "**Core Story:**",
            safe_text(analysis.get("core_story"))
        )

        st.write(
            "**Core Actions:**"
        )

        for item in analysis.get("core_actions", []):
            st.write(f"• {safe_text(item)}")

        st.write(
            "**Action Sequence:**"
        )

        for item in analysis.get("action_sequence", []):
            st.write(f"• {safe_text(item)}")

    st.divider()

    st.subheader("Pilih 1 konsep untuk dibuat menjadi storyboard")

    concepts = st.session_state.concepts

    for i, concept in enumerate(concepts[:3]):

        st.markdown(
            f"### Concept {i + 1}: "
            f"{safe_text(concept.get('title'))}"
        )

        st.write(
            f"**Hook:** "
            f"{safe_text(concept.get('hook'))}"
        )

        st.write(
            f"**Description:** "
            f"{safe_text(concept.get('description'))}"
        )

        st.write(
            f"**Main Subject:** "
            f"{safe_text(concept.get('main_subject'))}"
        )

        with st.expander("🎬 Core Scene Sequence"):

            sequence = concept.get(
                "core_scene_sequence",
                []
            )

            for n, item in enumerate(sequence, 1):
                st.write(
                    f"{n}. {safe_text(item)}"
                )

        with st.expander("🎭 Action Sequence"):

            actions = concept.get(
                "action_sequence",
                []
            )

            for n, item in enumerate(actions, 1):
                st.write(
                    f"{n}. {safe_text(item)}"
                )

        with st.expander("🔬 Micro Actions"):

            micro = concept.get(
                "micro_actions",
                []
            )

            for n, item in enumerate(micro, 1):
                st.write(
                    f"{n}. {safe_text(item)}"
                )

        st.write(
            f"**Visual Execution:** "
            f"{safe_text(concept.get('visual_execution'))}"
        )

        st.write(
            f"**Ending Payoff:** "
            f"{safe_text(concept.get('ending_payoff'))}"
        )

        if st.button(
            f"✅ Pilih Concept {i + 1}",
            key=f"select_concept_{i}",
            use_container_width=True
        ):

            st.session_state.selected_concept = i
            st.session_state.storyboard = []
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}

            go("storyboard")

        st.divider()

    if st.button(
        "🏠 Kembali ke Home",
        use_container_width=True
    ):
        go("home")


# ============================================================
# STORYBOARD GENERATOR
# ============================================================

def generate_storyboard():

    client = get_client()

    if client is None:
        st.error(
            "Masukkan Gemini API Key terlebih dahulu."
        )
        return

    concept = selected_concept()

    if not concept:
        st.error(
            "Belum ada konsep yang dipilih."
        )
        return

    duration = st.session_state.duration
    total_scenes = scene_count(duration)

    prompt = f"""
You are a professional storyboard director for AI video generation.

Create a complete storyboard for the selected concept.

IMPORTANT:

Target duration:
{duration}

EXACT number of scenes:
{total_scenes}

Each scene is approximately 8 seconds.

You MUST return exactly {total_scenes} scenes.

Do not return fewer scenes.
Do not return more scenes.

LANGUAGE:

All storyboard content must be written in Indonesian.

The final video will later be generated using Google Flow/Veo.

REFERENCE / CONCEPT:

Title:
{safe_text(concept.get("title"))}

Hook:
{safe_text(concept.get("hook"))}

Description:
{safe_text(concept.get("description"))}

Main Subject:
{safe_text(concept.get("main_subject"))}

Core Scene Sequence:
{safe_text(concept.get("core_scene_sequence"))}

Action Sequence:
{safe_text(concept.get("action_sequence"))}

Micro Actions:
{safe_text(concept.get("micro_actions"))}

Visual Execution:
{safe_text(concept.get("visual_execution"))}

Ending Payoff:
{safe_text(concept.get("ending_payoff"))}

USER SETTINGS:

Style:
{st.session_state.style}

Aspect Ratio:
{st.session_state.aspect}

Additional Creative Instruction:
{st.session_state.creative_instruction}

{ORIGINALITY_RULES}

{ACTION_CONTINUITY_RULES}

{SAFETY_RULES}


CRITICAL STORYBOARD LOGIC:

The storyboard must preserve the core comedic sequence.

Do not randomly replace the main subject.

Do not change the important action merely to make it original.

Originality should come mainly from visual execution.

Every important physical action must be represented as a sequence.

For example:

approach
→ contact
→ grip
→ manipulation
→ visible change
→ result
→ reaction

Do not allow an object to suddenly appear already completed.

Do not allow an object to magically change state.

Do not skip an important cause-and-effect action.

If an action is too long for one 8-second scene,
continue it into the next scene.

The next scene MUST begin from the ending state of the previous scene.

IMPORTANT CONTINUITY:

Scene 1 establishes the initial visual state.

Scene 2 must continue from Scene 1's ending state.

Scene 3 must continue from Scene 2's ending state.

And so on.

Each scene must explicitly describe:

- starting state
- action progression
- ending state

The ending state must be specific enough that a screenshot of the final frame
could be used as the exact visual starting point for the next scene.

Do not reset the character.

Do not reset object positions.

Do not randomly change wardrobe.

Do not randomly change environment.

Do not randomly change lighting direction.

Do not randomly change camera geography.

Do not randomly change the state of props.

Only change established states when the current action visibly causes the change.


RETURN ONLY VALID JSON.

Use this exact structure:

{{
  "scenes": [
    {{
      "scene_number": 1,
      "duration_sec": 8,
      "purpose": "...",
      "starting_state": "...",
      "visual": "...",
      "action": "...",
      "micro_actions": [],
      "camera": "...",
      "continuity": "...",
      "ending_state": "...",
      "audio": "...",
      "transition": "..."
    }}
  ]
}}

The "scenes" array MUST contain exactly {total_scenes} objects.

Remember:

Scene N ending_state
must logically become
Scene N+1 starting_state.
"""

    try:

        raw = ask(
            client,
            prompt
        )

        data = extract_json(raw)

        scenes = data.get(
            "scenes",
            []
        )

        if len(scenes) != total_scenes:

            raise ValueError(
                f"Storyboard menghasilkan "
                f"{len(scenes)} scene, "
                f"seharusnya {total_scenes}."
            )

        normalized = []

        for i, scene in enumerate(scenes, 1):

            scene["scene_number"] = i
            scene["duration_sec"] = 8

            if not isinstance(
                scene.get("micro_actions"),
                list
            ):
                scene["micro_actions"] = []

            normalized.append(scene)

        st.session_state.storyboard = normalized

        st.session_state.scene_prompts = {}
        st.session_state.scene_frames = {}

        st.success(
            f"Storyboard berhasil dibuat: "
            f"{total_scenes} scene."
        )

    except Exception as e:

        st.error(
            f"Storyboard gagal dibuat: {e}"
        )


# ============================================================
# STORYBOARD PAGE
# ============================================================

def render_storyboard():

    st.title("🎞️ Storyboard")

    concept = selected_concept()

    if not concept:
        st.warning(
            "Belum ada konsep yang dipilih."
        )

        if st.button("💡 Kembali ke Concepts"):
            go("concepts")

        return

    total_scenes = scene_count(
        st.session_state.duration
    )

    st.info(
        f"Durasi: {st.session_state.duration}  |  "
        f"Total: {total_scenes} scene  |  "
        f"±8 detik / scene"
    )

    st.subheader(
        safe_text(concept.get("title"))
    )

    st.write(
        safe_text(concept.get("description"))
    )

    st.divider()

    if not st.session_state.storyboard:

        st.warning(
            "Storyboard belum dibuat."
        )

        if st.button(
            "🎬 GENERATE STORYBOARD",
            type="primary",
            use_container_width=True
        ):

            with st.spinner(
                "AI sedang menyusun storyboard..."
            ):
                generate_storyboard()

        if st.button(
            "⬅️ Kembali ke Concepts",
            use_container_width=True
        ):
            go("concepts")

        return

    st.success(
        f"Storyboard siap — "
        f"{len(st.session_state.storyboard)} scene"
    )

    st.divider()

    for scene in st.session_state.storyboard:

        number = scene.get(
            "scene_number",
            0
        )

        with st.expander(
            f"🎬 Scene {number} — 8 detik",
            expanded=False
        ):

            st.write(
                "**Purpose:**"
            )

            st.write(
                safe_text(
                    scene.get("purpose")
                )
            )

            st.write(
                "**Starting State:**"
            )

            st.write(
                safe_text(
                    scene.get("starting_state")
                )
            )

            st.write(
                "**Visual:**"
            )

            st.write(
                safe_text(
                    scene.get("visual")
                )
            )

            st.write(
                "**Action:**"
            )

            st.write(
                safe_text(
                    scene.get("action")
                )
            )

            st.write(
                "**Micro Actions:**"
            )

            micro = scene.get(
                "micro_actions",
                []
            )

            for i, item in enumerate(
                micro,
                1
            ):

                st.write(
                    f"{i}. {safe_text(item)}"
                )

            st.write(
                "**Camera:**"
            )

            st.write(
                safe_text(
                    scene.get("camera")
                )
            )

            st.write(
                "**Continuity:**"
            )

            st.write(
                safe_text(
                    scene.get("continuity")
                )
            )

            st.write(
                "**Ending State:**"
            )

            st.write(
                safe_text(
                    scene.get("ending_state")
                )
            )

            st.write(
                "**Audio:**"
            )

            st.write(
                safe_text(
                    scene.get("audio")
                )
            )

            st.write(
                "**Transition:**"
            )

            st.write(
                safe_text(
                    scene.get("transition")
                )
            )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🔄 Regenerate Storyboard",
            use_container_width=True
        ):

            st.session_state.storyboard = []
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}

            st.rerun()

    with col2:

        if st.button(
            "🎥 Lanjut ke Scene Generator",
            type="primary",
            use_container_width=True
        ):

            st.session_state.current_scene = 1

            go("scenes")

    if st.button(
        "💡 Kembali ke Concepts",
        use_container_width=True
    ):

        go("concepts")
    # ============================================================
# PART 3/3
# SCENE GENERATOR + SCREENSHOT CONTINUITY + SEO + NAVIGATION
# ============================================================


# ============================================================
# SCENE PROMPT GENERATOR
# ============================================================

def generate_scene_prompt(scene_number: int):

    client = get_client()

    if client is None:
        st.error(
            "Masukkan Gemini API Key terlebih dahulu."
        )
        return

    scenes = st.session_state.storyboard

    if not scenes:
        st.error(
            "Storyboard belum tersedia."
        )
        return

    if scene_number < 1 or scene_number > len(scenes):
        st.error(
            "Nomor scene tidak valid."
        )
        return

    # IMPORTANT:
    # Scene 1 = index 0
    # Scene 2 = index 1
    # Scene 3 = index 2
    scene = scenes[scene_number - 1]

    concept = selected_concept()

    parts = []

    # ========================================================
    # PREVIOUS FRAME
    # ========================================================

    previous_frame = None

    if scene_number > 1:

        previous_frame = st.session_state.scene_frames.get(
            scene_number - 1
        )

        if not previous_frame:
            st.warning(
                f"Upload screenshot final Scene "
                f"{scene_number - 1} terlebih dahulu."
            )
            return

        parts.extend(
            file_part(
                client,
                previous_frame
            )
        )

    # ========================================================
    # PREVIOUS SCENE DATA
    # ========================================================

    previous_info = previous_scene_info(
        scene_number
    )

    # ========================================================
    # PROMPT
    # ========================================================

    if scene_number == 1:

        continuity_instruction = """
This is Scene 1.

Establish the initial visual state clearly.

The character, environment, props, wardrobe,
lighting and camera geography must be stable.

Do not skip important physical actions.
"""

    else:

        continuity_instruction = f"""
THIS IS SCENE {scene_number}.

The uploaded image is the FINAL FRAME of Scene {scene_number - 1}.

IMPORTANT:

The uploaded previous-scene image is NOT merely a visual reference.

It is the EXACT STARTING VISUAL STATE for this scene.

Start the new scene from the exact state shown in that image.

Preserve:

- character identity
- character appearance
- character pose
- body position
- facial expression
- wardrobe
- prop identity
- prop position
- object state
- environment
- background
- lighting direction
- shadows
- camera geography
- spatial relationships
- motion state

DO NOT:

- reset the character
- recreate the scene from scratch
- change the character
- change the environment
- randomly move props
- randomly change object states
- randomly change wardrobe
- randomly change lighting
- teleport objects
- jump to a later action
- make an object already completed
- restart an action that was already completed

The current scene must continue naturally from the exact final state
shown in the uploaded image.

Only change the established visual state when the CURRENT ACTION
visibly causes that change.

The first moment of this scene should visually connect directly
to the uploaded previous final frame.
"""

    prompt = f"""
You are creating ONE production-ready prompt for Google Flow / Veo.

The final prompt MUST be written entirely in ENGLISH.

Do not include Indonesian explanations inside the final prompt.

============================================================
PROJECT
============================================================

Concept:
{safe_text(concept.get("title"))}

Concept Description:
{safe_text(concept.get("description"))}

Main Subject:
{safe_text(concept.get("main_subject"))}

Visual Style:
{st.session_state.style}

Aspect Ratio:
{st.session_state.aspect}

Duration:
8 seconds

============================================================
CURRENT SCENE
============================================================

Scene Number:
{scene_number}

Purpose:
{safe_text(scene.get("purpose"))}

Starting State:
{safe_text(scene.get("starting_state"))}

Visual:
{safe_text(scene.get("visual"))}

Action:
{safe_text(scene.get("action"))}

Micro Actions:
{safe_text(scene.get("micro_actions"))}

Camera:
{safe_text(scene.get("camera"))}

Continuity:
{safe_text(scene.get("continuity"))}

Ending State:
{safe_text(scene.get("ending_state"))}

Audio:
{safe_text(scene.get("audio"))}

Transition:
{safe_text(scene.get("transition"))}

============================================================
PREVIOUS SCENE
============================================================

{previous_info}

============================================================
CONTINUITY INSTRUCTION
============================================================

{continuity_instruction}

============================================================
ACTION CONTINUITY
============================================================

{ACTION_CONTINUITY_RULES}

Every important physical action must be visible.

Do not compress multiple important actions into one unexplained
state change.

If a character needs to interact with an object:

show the approach,
then physical contact,
then the interaction,
then the visible change,
then the result,
then the reaction.

Do not make the result appear before the action that causes it.

Objects must maintain logical physical states.

============================================================
ORIGINALITY
============================================================

{ORIGINALITY_RULES}

============================================================
SAFETY
============================================================

{SAFETY_RULES}

============================================================
VIDEO GENERATION REQUIREMENTS
============================================================

Create a natural 8-second continuous video shot.

The animation must have clear cause-and-effect.

Preserve the main subject.

Preserve the core comedic action.

Preserve the important story beat.

Make the visual execution original through secondary details,
cinematography, environment, lighting, textures, expressions,
and visual design.

Do not copy recognizable characters, brands, logos,
exact dialogue, exact shots, or distinctive creator/studio style.

Avoid unexplained cuts.

Avoid teleportation.

Avoid sudden object state changes.

Avoid sudden character state changes.

Avoid impossible continuity.

The ending frame must clearly establish the ending state described
in the storyboard so it can be used as the starting point for the
next scene.

============================================================
FINAL OUTPUT
============================================================

Return ONLY the final production prompt.

No explanation.
No JSON.
No headings outside the prompt.
No Indonesian text.

Write a detailed but efficient prompt suitable for Google Flow / Veo.
"""

    try:

        raw = ask(
            client,
            prompt,
            parts
        )

        final_prompt = raw.strip()

        st.session_state.scene_prompts[
            scene_number
        ] = final_prompt

        st.success(
            f"Prompt Scene {scene_number} berhasil dibuat."
        )

    except Exception as e:

        st.error(
            f"Generate prompt gagal: {e}"
        )


# ============================================================
# SCENE GENERATOR PAGE
# ============================================================

def render_scenes():

    st.title(
        "🎥 Scene Generator"
    )

    scenes = st.session_state.storyboard

    if not scenes:

        st.warning(
            "Storyboard belum tersedia."
        )

        if st.button(
            "🎞️ Kembali ke Storyboard"
        ):
            go("storyboard")

        return

    total = len(scenes)

    if "current_scene" not in st.session_state:
        st.session_state.current_scene = 1

    current = st.session_state.current_scene

    if current < 1:
        current = 1

    if current > total:
        current = total

    st.session_state.current_scene = current

    st.info(
        f"Scene {current} / {total}  |  "
        f"Durasi scene: 8 detik"
    )

    st.progress(
        current / total
    )

    scene = scenes[current - 1]

    st.subheader(
        f"🎬 Scene {current}"
    )

    st.write(
        f"**Purpose:** "
        f"{safe_text(scene.get('purpose'))}"
    )

    st.write(
        f"**Starting State:** "
        f"{safe_text(scene.get('starting_state'))}"
    )

    st.write(
        f"**Visual:** "
        f"{safe_text(scene.get('visual'))}"
    )

    st.write(
        f"**Action:** "
        f"{safe_text(scene.get('action'))}"
    )

    micro = scene.get(
        "micro_actions",
        []
    )

    if micro:

        st.write(
            "**Micro Actions:**"
        )

        for i, item in enumerate(
            micro,
            1
        ):

            st.write(
                f"{i}. {safe_text(item)}"
            )

    st.write(
        f"**Ending State:** "
        f"{safe_text(scene.get('ending_state'))}"
    )

    st.divider()

    # ========================================================
    # SCREENSHOT CONTINUITY
    # ========================================================

    if current > 1:

        st.subheader(
            f"📸 Screenshot Final Scene {current - 1}"
        )

        st.info(
            "Screenshot ini menjadi EXACT STARTING STATE "
            "untuk Scene berikutnya."
        )

        frame_key = (
            f"scene_frame_{current - 1}"
        )

        uploaded_frame = st.file_uploader(
            f"Upload screenshot final Scene {current - 1}",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp"
            ],
            key=frame_key
        )

        if uploaded_frame:

            st.session_state.scene_frames[
                current - 1
            ] = uploaded_frame

            st.success(
                f"Screenshot Scene {current - 1} tersimpan."
            )

        elif not st.session_state.scene_frames.get(
            current - 1
        ):

            st.warning(
                f"Scene {current} membutuhkan screenshot "
                f"final Scene {current - 1}."
            )

    else:

        st.success(
            "Scene 1 dimulai dari reference + storyboard."
        )

    st.divider()

    # ========================================================
    # GENERATE
    # ========================================================

    existing_prompt = st.session_state.scene_prompts.get(
        current
    )

    if current > 1 and not st.session_state.scene_frames.get(
        current - 1
    ):

        st.warning(
            "Upload screenshot scene sebelumnya "
            "sebelum membuat prompt."
        )

    else:

        if st.button(
            f"✨ Generate Prompt Scene {current}",
            type="primary",
            use_container_width=True
        ):

            with st.spinner(
                f"AI sedang membuat prompt Scene {current}..."
            ):

                generate_scene_prompt(
                    current
                )

    existing_prompt = st.session_state.scene_prompts.get(
        current
    )

    if existing_prompt:

        st.divider()

        st.subheader(
            "📋 Flow / Veo Prompt"
        )

        st.caption(
            "Prompt final selalu dalam English."
        )

        st.text_area(
            "Copy prompt ini ke Google Flow / Veo",
            value=existing_prompt,
            height=400,
            key=f"prompt_display_{current}"
        )

        st.success(
            "Setelah video scene ini selesai dibuat, "
            "ambil screenshot frame terakhirnya."
        )

    # ========================================================
    # NAVIGATION
    # ========================================================

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        if current > 1:

            if st.button(
                "⬅️ Previous",
                use_container_width=True
            ):

                st.session_state.current_scene -= 1
                st.rerun()

    with col2:

        if st.button(
            "🎞️ Storyboard",
            use_container_width=True
        ):

            go("storyboard")

    with col3:

        if current < total:

            if st.button(
                "Next ➡️",
                use_container_width=True
            ):

                st.session_state.current_scene += 1
                st.rerun()

        else:

            if st.button(
                "🔍 Generate SEO",
                type="primary",
                use_container_width=True
            ):

                go("seo")


# ============================================================
# SEO GENERATOR
# ============================================================

def generate_seo():

    client = get_client()

    if client is None:
        st.error(
            "Masukkan Gemini API Key terlebih dahulu."
        )
        return

    concept = selected_concept()

    prompt = f"""
You are a YouTube Shorts and video SEO specialist.

Create SEO metadata for this original AI-generated video.

Concept:
{safe_text(concept.get("title"))}

Description:
{safe_text(concept.get("description"))}

Main Subject:
{safe_text(concept.get("main_subject"))}

Duration:
{st.session_state.duration}

Visual Style:
{st.session_state.style}

Create:

- 5 clickable Indonesian titles
- 1 recommended title
- 1 Indonesian description
- 15 relevant hashtags
- 15 search keywords
- 3 thumbnail text ideas

Do not use misleading claims.

Do not mention copyrighted characters or brands unless they are
actually part of the user's own original content.

Return ONLY valid JSON:

{{
  "titles": [],
  "recommended_title": "",
  "description": "",
  "hashtags": [],
  "keywords": [],
  "thumbnail_text": []
}}
"""

    try:

        raw = ask(
            client,
            prompt
        )

        data = extract_json(raw)

        st.session_state.seo = data

    except Exception as e:

        st.error(
            f"SEO gagal dibuat: {e}"
        )


# ============================================================
# SEO PAGE
# ============================================================

def render_seo():

    st.title(
        "🚀 YouTube SEO"
    )

    if not st.session_state.seo:

        st.info(
            "SEO metadata belum dibuat."
        )

        if st.button(
            "✨ Generate SEO",
            type="primary",
            use_container_width=True
        ):

            with st.spinner(
                "AI sedang membuat SEO..."
            ):

                generate_seo()

    seo = st.session_state.seo

    if not seo:
        return

    st.subheader(
        "🔥 Recommended Title"
    )

    st.code(
        safe_text(
            seo.get("recommended_title")
        )
    )

    st.subheader(
        "🎯 Other Title Ideas"
    )

    for i, title in enumerate(
        seo.get("titles", []),
        1
    ):

        st.write(
            f"{i}. {safe_text(title)}"
        )

    st.subheader(
        "📝 Description"
    )

    st.text_area(
        "Description",
        value=safe_text(
            seo.get("description")
        ),
        height=180
    )

    st.subheader(
        "#️⃣ Hashtags"
    )

    hashtags = seo.get(
        "hashtags",
        []
    )

    st.code(
        " ".join(
            safe_text(x)
            for x in hashtags
        )
    )

    st.subheader(
        "🔎 Keywords"
    )

    keywords = seo.get(
        "keywords",
        []
    )

    st.code(
        ", ".join(
            safe_text(x)
            for x in keywords
        )
    )

    st.subheader(
        "🖼️ Thumbnail Text"
    )

    for item in seo.get(
        "thumbnail_text",
        []
    ):

        st.write(
            f"• {safe_text(item)}"
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🎥 Kembali ke Scene",
            use_container_width=True
        ):

            go("scenes")

    with col2:

        if st.button(
            "🆕 New Project",
            type="primary",
            use_container_width=True
        ):

            reset_project()
            st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar():

    st.sidebar.title(
        "⚙️ Settings"
    )

    st.sidebar.text_input(
        "Gemini API Key",
        type="password",
        key="api_key",
        placeholder="AIza..."
    )

    st.sidebar.divider()

    st.sidebar.caption(
        "Workflow"
    )

    pages = [
        ("🏠 Home", "home"),
        ("💡 Concepts", "concepts"),
        ("🎞️ Storyboard", "storyboard"),
        ("🎥 Scene Generator", "scenes"),
        ("🚀 SEO", "seo"),
    ]

    for label, page in pages:

        if st.sidebar.button(
            label,
            use_container_width=True
        ):

            st.session_state.page = page
            st.rerun()

    st.sidebar.divider()

    if st.sidebar.button(
        "🆕 New Project",
        use_container_width=True
    ):

        reset_project()
        st.rerun()


# ============================================================
# APP ROUTER
# ============================================================

st.set_page_config(
    page_title="UGC Shorts AI Remix Engine",
    page_icon="🎬",
    layout="wide"
)

render_sidebar()


if st.session_state.page == "home":

    render_home()

elif st.session_state.page == "concepts":

    render_concepts()

elif st.session_state.page == "storyboard":

    render_storyboard()

elif st.session_state.page == "scenes":

    render_scenes()

elif st.session_state.page == "seo":

    render_seo()

else:

    st.session_state.page = "home"
    st.rerun()
