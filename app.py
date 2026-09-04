import streamlit as st
import json
import re
from google import genai
from google.genai import types

st.set_page_config(
    page_title="UGC Remix Studio",
    page_icon="🎬",
    layout="wide"
)

MODEL_NAME = "gemini-3.6-flash"

DURATIONS = {
    "8 seconds": 1,
    "16 seconds": 2,
    "24 seconds": 3,
    "32 seconds": 4,
    "40 seconds": 5,
    "48 seconds": 6,
    "56 seconds": 7,
    "1 minute": 8,
    "1.5 minutes": 12,
    "2 minutes": 15,
    "2.5 minutes": 19,
    "3 minutes": 23,
}

if "page" not in st.session_state:
    st.session_state.page = "home"

if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "remixes" not in st.session_state:
    st.session_state.remixes = []

if "selected_remix" not in st.session_state:
    st.session_state.selected_remix = None

if "master_storyboard" not in st.session_state:
    st.session_state.master_storyboard = []

if "character_anchor" not in st.session_state:
    st.session_state.character_anchor = ""

if "scene_index" not in st.session_state:
    st.session_state.scene_index = 0

if "last_video_prompt" not in st.session_state:
    st.session_state.last_video_prompt = ""

if "last_audio_prompt" not in st.session_state:
    st.session_state.last_audio_prompt = ""

if "seo_package" not in st.session_state:
    st.session_state.seo_package = None


st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(circle at 10% 10%, rgba(124,58,237,.18), transparent 30%),
        radial-gradient(circle at 90% 10%, rgba(14,165,233,.12), transparent 30%),
        #08090d;
    color: #f5f7fb;
}

.block-container {
    max-width: 1400px;
    padding-top: 2rem;
}

.hero {
    padding: 38px;
    border-radius: 26px;
    background: linear-gradient(
        135deg,
        rgba(124,58,237,.25),
        rgba(15,23,42,.9)
    );
    border: 1px solid rgba(139,92,246,.25);
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 42px;
    margin-bottom: 8px;
}

.hero p {
    color: #aeb7c8;
    line-height: 1.7;
}

.card {
    background: rgba(17,20,29,.85);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 16px;
}

.card h3 {
    margin-top: 0;
}

.muted {
    color: #929cad;
    font-size: 13px;
    line-height: 1.6;
}

.badge {
    display: inline-block;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(124,58,237,.18);
    color: #c4b5fd;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 12px;
}

.workflow {
    min-height: 135px;
    background: rgba(17,20,29,.8);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 18px;
    padding: 20px;
}

.workflow-number {
    color: #a78bfa;
    font-weight: 800;
    font-size: 12px;
}

.workflow-title {
    font-weight: 700;
    margin-top: 10px;
}

.workflow-text {
    color: #8e98aa;
    font-size: 12px;
    margin-top: 6px;
    line-height: 1.5;
}

</style>
""", unsafe_allow_html=True)


def get_client(api_key):
    if not api_key:
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def clean_json(text):
    if not text:
        return None

    text = text.strip()

    text = re.sub(
        r"^```json\s*",
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

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return None


def generate_ai(client, prompt, json_mode=False):

    if client is None:
        raise ValueError("Gemini API key belum dimasukkan.")

    config = None

    if json_mode:
        config = types.GenerateContentConfig(
            response_mime_type="application/json"
        )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=config
    )

    if not response or not response.text:
        raise ValueError("Gemini tidak memberikan response.")

    if json_mode:
        result = clean_json(response.text)

        if result is None:
            raise ValueError(
                "Gemini mengembalikan JSON yang tidak valid."
            )

        return result

    return response.text


def reset_project():

    keys = [
        "analysis",
        "remixes",
        "selected_remix",
        "master_storyboard",
        "character_anchor",
        "scene_index",
        "last_video_prompt",
        "last_audio_prompt",
        "seo_package"
    ]

    for key in keys:
        if key in st.session_state:
            st.session_state[key] = (
                [] if key in ["remixes", "master_storyboard"]
                else None if key in ["analysis", "selected_remix", "seo_package"]
                else "" if key in ["character_anchor", "last_video_prompt", "last_audio_prompt"]
                else 0
            )

    st.session_state.page = "home"


with st.sidebar:

    st.markdown(
        """
        <div style="font-size:24px;font-weight:800;">
        🎬 UGC Remix Studio
        </div>
        <div style="color:#7f8a9d;font-size:12px;">
        Universal AI Content Engine
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIza..."
    )

    st.divider()

    st.markdown("### 🧭 Navigation")

    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()

    if st.button("🧠 AI Remix", use_container_width=True):
        st.session_state.page = "remix"
        st.rerun()

    if st.button("🎞️ Storyboard", use_container_width=True):
        st.session_state.page = "storyboard"
        st.rerun()

    if st.button("🎬 Scene Generator", use_container_width=True):
        st.session_state.page = "scene"
        st.rerun()

    if st.button("🚀 Finish & SEO", use_container_width=True):
        st.session_state.page = "finish"
        st.rerun()

    st.divider()

    if st.button("🗑️ Reset Project", use_container_width=True):
        reset_project()
        st.rerun()


def render_home():

    st.markdown(
        """
        <div class="hero">

            <div class="badge">
            V2 • UNIVERSAL CONTENT ENGINE
            </div>

            <h1>
            Turn Any Reference Into An Original Video
            </h1>

            <p>
            Upload a reference video, screenshots, or describe an idea.
            AI analyzes the entertainment structure, creates original
            remix concepts, builds the storyboard, and prepares
            scene-by-scene prompts for Google Flow / Veo.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### ⚡ Workflow")

    cols = st.columns(5)

    workflow = [
        ("01", "Reference", "Video, screenshot, or text."),
        ("02", "Analyze", "Understand hook and story."),
        ("03", "Auto Remix", "Create 3 original concepts."),
        ("04", "Storyboard", "Build all scenes."),
        ("05", "Flow Prompt", "Generate prompts for Flow/Veo.")
    ]

    for col, item in zip(cols, workflow):

        number, title, description = item

        with col:

            st.markdown(
                f"""
                <div class="workflow">

                    <div class="workflow-number">
                    {number}
                    </div>

                    <div class="workflow-title">
                    {title}
                    </div>

                    <div class="workflow-text">
                    {description}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    st.write("")

    st.markdown("### 🎥 Reference")

    reference_type = st.radio(
        "Pilih sumber reference",
        [
            "Video",
            "Screenshots",
            "Text / Idea"
        ],
        horizontal=True
    )

    video_file = None
    image_files = []
    reference_text = ""

    if reference_type == "Video":

        video_file = st.file_uploader(
            "Upload reference video",
            type=[
                "mp4",
                "mov",
                "webm",
                "avi",
                "mkv"
            ]
        )

    elif reference_type == "Screenshots":

        image_files = st.file_uploader(
            "Upload screenshots",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp"
            ],
            accept_multiple_files=True
        )

    else:

        reference_text = st.text_area(
            "Jelaskan reference / ide kamu",
            height=180,
            placeholder=(
                "Contoh: Seorang karakter mencoba membuka "
                "kotak misterius. Setiap kali hampir berhasil, "
                "muncul kejutan lucu. Di akhir ada twist."
            )
        )

    st.markdown("### 🎨 Creative Settings")

    col1, col2 = st.columns(2)

    with col1:

        style = st.selectbox(
            "Visual Style",
            [
                "Realistic cinematic",
                "Stylized 3D animation",
                "Cute cartoon",
                "Photorealistic comedy",
                "Cinematic live action",
                "Anime-inspired original",
                "Dark cinematic",
                "Fast viral social video"
            ]
        )

    with col2:

        aspect_ratio = st.selectbox(
            "Aspect Ratio",
            [
                "9:16 — Shorts / Reels / TikTok",
                "16:9 — YouTube Long Form",
                "1:1 — Square"
            ]
        )

    duration = st.selectbox(
        "Video Duration",
        list(DURATIONS.keys())
    )

    scene_count = DURATIONS[duration]

    st.info(
        f"⏱️ {duration} = {scene_count} scene "
        f"(sekitar 8 detik per scene)"
    )

    custom_instruction = st.text_area(
        "User Creative Instruction",
        height=110,
        placeholder=(
            "Contoh: Buat lebih lucu, pacing cepat, "
            "ending punya twist, cocok untuk penonton global."
        )
    )

    st.markdown(
        """
        <div class="card">

        <h3>🛡️ Originality Guard</h3>

        <div class="muted">
        Sistem mempertahankan entertainment logic seperti hook,
        konflik, sebab-akibat, escalation, emosi dan payoff.
        Namun execution dibuat baru melalui perubahan karakter,
        setting, properti, aksi, kamera, lighting, dialogue,
        sound design dan detail visual.

        Jangan menyalin karakter terkenal, logo, brand,
        dialogue persis, shot persis, atau identitas creator.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    if st.button(
        "🚀 ANALYZE + AUTO REMIX",
        type="primary",
        use_container_width=True
    ):

        if not api_key:
            st.error("Masukkan Gemini API Key terlebih dahulu.")
            return

        if reference_type == "Video" and not video_file:
            st.error("Upload video reference terlebih dahulu.")
            return

        if reference_type == "Screenshots" and not image_files:
            st.error("Upload screenshot terlebih dahulu.")
            return

        if reference_type == "Text / Idea" and not reference_text.strip():
            st.error("Masukkan ide/reference terlebih dahulu.")
            return

        client = get_client(api_key)

        if client is None:
            st.error("Gemini API key tidak valid.")
            return

        if reference_type == "Video":

            reference_description = (
                "A reference video was uploaded. "
                f"Filename: {video_file.name}. "
                "Analyze the provided reference when possible."
            )

        elif reference_type == "Screenshots":

            names = ", ".join(
                image.name for image in image_files
            )

            reference_description = (
                "Reference screenshots were uploaded. "
                f"Files: {names}. "
                "Analyze the visual information provided."
            )

        else:

            reference_description = reference_text

        prompt = f"""
You are a universal AI video creative director.

Analyze the reference and create three ORIGINAL remix concepts.

The system must work for ANY niche:
comedy, prank, cooking, animals, sports, gaming,
horror, cinematic, kids animation, experiments,
challenges, storytelling, satisfying videos, etc.

Do NOT assume the niche.

First identify:

- niche
- format
- hook
- core entertainment idea
- emotional goal
- cause and effect
- pacing
- escalation
- payoff
- important visual elements

Then create exactly THREE original remix concepts.

Preserve the underlying entertainment logic,
but substantially change the execution.

Change:
characters or subjects,
appearance,
clothes,
colors,
props,
setting,
actions,
camera,
lighting,
visual design,
dialogue wording,
sound design,
comedy/drama details,
and ending details.

Do NOT copy recognizable copyrighted characters,
brands, logos, exact dialogue, exact shots,
watermarks, or distinctive creator identity.

Visual style:
{style}

Aspect ratio:
{aspect_ratio}

Duration:
{duration}

Scene count:
{scene_count}

User instruction:
{custom_instruction}

Reference:
{reference_description}

Return ONLY valid JSON:

{{
  "analysis": {{
    "niche": "",
    "format": "",
    "hook": "",
    "core_concept": "",
    "emotional_goal": "",
    "cause_effect": "",
    "pacing": "",
    "escalation": "",
    "payoff": "",
    "visual_elements": []
  }},
  "remixes": [
    {{
      "title": "",
      "concept": "",
      "hook": "",
      "character_anchor": "",
      "setting": "",
      "changed_elements": [],
      "story_arc": "",
      "originality_note": ""
    }},
    {{
      "title": "",
      "concept": "",
      "hook": "",
      "character_anchor": "",
      "setting": "",
      "changed_elements": [],
      "story_arc": "",
      "originality_note": ""
    }},
    {{
      "title": "",
      "concept": "",
      "hook": "",
      "character_anchor": "",
      "setting": "",
      "changed_elements": [],
      "story_arc": "",
      "originality_note": ""
    }}
  ]
}}
"""

        try:

            with st.spinner(
                "🧠 AI sedang menganalisis dan membuat 3 remix..."
            ):

                result = generate_ai(
                    client,
                    prompt,
                    json_mode=True
                )

            st.session_state.analysis = result.get(
                "analysis",
                {}
            )

            st.session_state.remixes = result.get(
                "remixes",
                []
            )

            st.session_state.page = "remix"

            st.success(
                "✅ Analysis + Auto Remix selesai!"
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Terjadi error: {e}"
            )


if st.session_state.page == "home":
    render_home()
    # ============================================================
# PART 2/3 — AUTO REMIX + CONCEPT SELECTOR + STORYBOARD
# ============================================================

def render_remix():
    st.markdown("""
    <div class="hero">
        <div class="eyebrow">STEP 02 • AI REMIX ENGINE</div>
        <h1>Choose Your Remix</h1>
        <p>AI mempertahankan ide hiburan utama, tetapi mengubah eksekusi agar menjadi konsep baru dan original.</p>
    </div>
    """, unsafe_allow_html=True)

    analysis = st.session_state.get("analysis", {})
    concepts = st.session_state.get("concepts", [])

    if not analysis:
        st.warning("Belum ada hasil analisis.")
        if st.button("← BACK TO HOME"):
            st.session_state.page = "home"
            st.rerun()
        return

    # --------------------------------------------------------
    # SOURCE ANALYSIS
    # --------------------------------------------------------

    st.markdown("### 🧠 AI ANALYSIS")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">CONTENT TYPE</div>
                <div class="metric-value">
                    {analysis.get("content_type", "Unknown")}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">CORE IDEA</div>
                <div class="metric-value">
                    {analysis.get("core_idea", "Unknown")}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">SCENES</div>
                <div class="metric-value">
                    {st.session_state.get("scene_count", 1)}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("")

    with st.expander("🔎 View AI Analysis", expanded=False):
        st.write(
            analysis.get(
                "summary",
                analysis.get("description", "No detailed analysis available.")
            )
        )

        if analysis.get("hook"):
            st.markdown("**Hook**")
            st.write(analysis["hook"])

        if analysis.get("emotional_goal"):
            st.markdown("**Emotional Goal**")
            st.write(analysis["emotional_goal"])

        if analysis.get("payoff"):
            st.markdown("**Payoff**")
            st.write(analysis["payoff"])

        if analysis.get("pacing"):
            st.markdown("**Pacing**")
            st.write(analysis["pacing"])

    st.markdown("---")

    # --------------------------------------------------------
    # REMIX CONCEPTS
    # --------------------------------------------------------

    st.markdown("### 🎬 3 ORIGINAL CONCEPTS")

    if not concepts:
        st.error("AI belum menghasilkan konsep remix.")
        if st.button("← BACK"):
            st.session_state.page = "home"
            st.rerun()
        return

    # Normalize to exactly three display slots
    normalized_concepts = concepts[:3]

    while len(normalized_concepts) < 3:
        normalized_concepts.append({
            "title": f"Alternative Concept {len(normalized_concepts) + 1}",
            "concept": "Create an original variation based on the analyzed entertainment structure.",
            "hook": "A stronger opening hook.",
            "setting": "Original setting",
            "subjects": ["Original subject"],
            "visual_direction": "Distinct visual execution",
            "why_it_works": "Preserves the entertainment mechanism while changing the execution."
        })

    cols = st.columns(3)

    for idx, concept in enumerate(normalized_concepts):

        title = concept.get(
            "title",
            f"Concept {idx + 1}"
        )

        concept_text = concept.get(
            "concept",
            concept.get(
                "description",
                "Original remix concept."
            )
        )

        hook = concept.get(
            "hook",
            "Strong opening hook."
        )

        setting = concept.get(
            "setting",
            "Original environment."
        )

        subjects = concept.get(
            "subjects",
            []
        )

        visual_direction = concept.get(
            "visual_direction",
            "Original visual direction."
        )

        why_it_works = concept.get(
            "why_it_works",
            "Keeps the core entertainment mechanism while creating a new execution."
        )

        with cols[idx]:

            st.markdown(
                f"""
                <div class="concept-card">
                    <div class="concept-number">CONCEPT {idx + 1}</div>
                    <h2>{title}</h2>
                    <p>{concept_text}</p>

                    <div class="concept-section">
                        <strong>HOOK</strong>
                        <span>{hook}</span>
                    </div>

                    <div class="concept-section">
                        <strong>SETTING</strong>
                        <span>{setting}</span>
                    </div>

                    <div class="concept-section">
                        <strong>VISUAL</strong>
                        <span>{visual_direction}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if subjects:
                st.caption(
                    "Subjects: " +
                    ", ".join(str(x) for x in subjects)
                )

            st.caption(why_it_works)

            if st.button(
                f"USE CONCEPT {idx + 1}",
                key=f"use_concept_{idx}",
                use_container_width=True
            ):
                st.session_state.selected_concept = concept
                st.session_state.selected_concept_index = idx
                st.session_state.page = "storyboard"
                st.rerun()

    st.markdown("---")

    if st.button("← BACK TO HOME", use_container_width=False):
        st.session_state.page = "home"
        st.rerun()


# ============================================================
# STORYBOARD GENERATOR
# ============================================================

def render_storyboard():
    st.markdown("""
    <div class="hero">
        <div class="eyebrow">STEP 03 • STORYBOARD</div>
        <h1>Build The Story</h1>
        <p>
            AI akan memecah konsep menjadi scene sesuai durasi project,
            lengkap dengan continuity untuk workflow Google Flow / Veo.
        </p>
    </div>
    """, unsafe_allow_html=True)

    selected = st.session_state.get("selected_concept")

    if not selected:
        st.warning("Belum ada konsep yang dipilih.")
        if st.button("← BACK TO REMIX"):
            st.session_state.page = "remix"
            st.rerun()
        return

    scene_count = int(
        st.session_state.get(
            "scene_count",
            1
        )
    )

    duration_label = st.session_state.get(
        "duration",
        "8 seconds"
    )

    # --------------------------------------------------------
    # SELECTED CONCEPT
    # --------------------------------------------------------

    st.markdown("### 🎯 SELECTED CONCEPT")

    st.markdown(
        f"""
        <div class="selected-card">
            <div class="eyebrow">
                CONCEPT {st.session_state.get("selected_concept_index", 0) + 1}
            </div>
            <h2>{selected.get("title", "Untitled Concept")}</h2>
            <p>{selected.get("concept", "")}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("")

    info1, info2, info3 = st.columns(3)

    with info1:
        st.metric("DURATION", duration_label)

    with info2:
        st.metric("TOTAL SCENES", scene_count)

    with info3:
        st.metric(
            "SCENE LENGTH",
            "8 seconds"
        )

    st.markdown("---")

    # --------------------------------------------------------
    # GENERATE STORYBOARD
    # --------------------------------------------------------

    if not st.session_state.get("storyboard"):

        st.markdown("### 🧩 GENERATE STORYBOARD")

        st.info(
            f"""
            AI akan membuat **{scene_count} scene**.

            Setiap scene dirancang sekitar 8 detik dan akan memiliki:
            - visual action
            - camera
            - subject movement
            - environment
            - continuity
            - audio/dialogue guidance
            - transition ke scene berikutnya
            """
        )

        if st.button(
            "⚡ GENERATE STORYBOARD",
            type="primary",
            use_container_width=True
        ):

            if not st.session_state.get("gemini_api_key"):
                st.error("Masukkan Gemini API Key terlebih dahulu.")
                return

            storyboard_prompt = f"""
You are an expert short-form and long-form video storyboard director.

Create an ORIGINAL storyboard based on the selected concept below.

IMPORTANT:
- Do NOT copy the reference video shot-for-shot.
- Do NOT reproduce recognizable copyrighted characters.
- Do NOT use brand names unless they are generic background context.
- Do NOT copy exact dialogue.
- Do NOT copy distinctive creator/studio style.
- Preserve only the underlying entertainment mechanism.
- Make the execution substantially different and original.
- Maintain strong visual continuity between scenes.

PROJECT:
Duration: {duration_label}
Total scenes: {scene_count}
Each scene: approximately 8 seconds

SELECTED CONCEPT:
{json.dumps(selected, ensure_ascii=False, indent=2)}

ORIGINALITY REQUIREMENTS:
{st.session_state.get("originality_guard", "")}

USER CREATIVE INSTRUCTION:
{st.session_state.get("custom_instruction", "")}

Create EXACTLY {scene_count} scenes.

Each scene must contain:

{{
  "scene_number": 1,
  "timecode": "00:00-00:08",
  "purpose": "What this scene accomplishes",
  "visual": "Detailed visual description",
  "action": "What happens during the scene",
  "camera": "Camera framing and movement",
  "subject_continuity": "Important subject details that must remain consistent",
  "environment_continuity": "Important environment details that must remain consistent",
  "audio": "Sound effects, ambience, dialogue or music guidance",
  "transition": "How this scene connects to the next scene"
}}

Return ONLY valid JSON:

{{
  "storyboard": [
    ...
  ]
}}
"""

            with st.spinner(
                f"Building {scene_count}-scene storyboard..."
            ):
                result = generate_ai(
                    storyboard_prompt,
                    temperature=0.7,
                    max_output_tokens=12000
                )

            if result:

                data = clean_json(result)

                if data and isinstance(
                    data.get("storyboard"),
                    list
                ):

                    storyboard = data["storyboard"]

                    # ----------------------------------------
                    # Validate and normalize scene count
                    # ----------------------------------------

                    if len(storyboard) < scene_count:

                        st.warning(
                            f"AI hanya menghasilkan {len(storyboard)} "
                            f"dari {scene_count} scene. "
                            f"Coba generate ulang."
                        )

                        st.session_state.storyboard = None
                        return

                    if len(storyboard) > scene_count:
                        storyboard = storyboard[:scene_count]

                    # Normalize scene numbers and timecodes
                    for i, scene in enumerate(storyboard):

                        scene["scene_number"] = i + 1

                        start_seconds = i * 8
                        end_seconds = (i + 1) * 8

                        def format_time(seconds):
                            minutes = seconds // 60
                            secs = seconds % 60
                            return f"{minutes:02d}:{secs:02d}"

                        scene["timecode"] = (
                            f"{format_time(start_seconds)}-"
                            f"{format_time(end_seconds)}"
                        )

                    st.session_state.storyboard = storyboard
                    st.session_state.current_scene = 1
                    st.session_state.scene_prompts = {}
                    st.session_state.scene_screenshots = {}

                    st.success(
                        f"Storyboard {scene_count} scene berhasil dibuat!"
                    )

                    st.rerun()

                else:
                    st.error(
                        "Format storyboard dari AI tidak valid."
                    )

    # --------------------------------------------------------
    # STORYBOARD DISPLAY
    # --------------------------------------------------------

    storyboard = st.session_state.get(
        "storyboard"
    )

    if storyboard:

        st.markdown("### 🎞️ STORYBOARD")

        progress = (
            len(storyboard) /
            max(scene_count, 1)
        )

        st.progress(
            min(progress, 1.0),
            text=f"{len(storyboard)} / {scene_count} scenes"
        )

        for scene in storyboard:

            scene_number = scene.get(
                "scene_number",
                "?"
            )

            timecode = scene.get(
                "timecode",
                ""
            )

            purpose = scene.get(
                "purpose",
                ""
            )

            visual = scene.get(
                "visual",
                ""
            )

            action = scene.get(
                "action",
                ""
            )

            camera = scene.get(
                "camera",
                ""
            )

            subject_continuity = scene.get(
                "subject_continuity",
                ""
            )

            environment_continuity = scene.get(
                "environment_continuity",
                ""
            )

            audio = scene.get(
                "audio",
                ""
            )

            transition = scene.get(
                "transition",
                ""
            )

            with st.expander(
                f"SCENE {scene_number}  •  {timecode}",
                expanded=(
                    scene_number == 1
                )
            ):

                st.markdown(
                    f"**Purpose**  \n{purpose}"
                )

                st.markdown(
                    f"**Visual**  \n{visual}"
                )

                st.markdown(
                    f"**Action**  \n{action}"
                )

                st.markdown(
                    f"**Camera**  \n{camera}"
                )

                st.markdown(
                    f"**Subject Continuity**  \n{subject_continuity}"
                )

                st.markdown(
                    f"**Environment Continuity**  \n{environment_continuity}"
                )

                st.markdown(
                    f"**Audio**  \n{audio}"
                )

                st.markdown(
                    f"**Transition**  \n{transition}"
                )

        st.markdown("---")

        # ----------------------------------------------------
        # STORYBOARD ACTIONS
        # ----------------------------------------------------

        col_a, col_b = st.columns(2)

        with col_a:

            if st.button(
                "← CHANGE CONCEPT",
                use_container_width=True
            ):
                st.session_state.storyboard = None
                st.session_state.scene_prompts = {}
                st.session_state.page = "remix"
                st.rerun()

        with col_b:

            if st.button(
                "CONTINUE TO SCENE GENERATOR →",
                type="primary",
                use_container_width=True
            ):
                st.session_state.current_scene = 1
                st.session_state.page = "scenes"
                st.rerun()


# ============================================================
# ROUTER UPDATE
# ============================================================

if st.session_state.page == "remix":
    render_remix()

elif st.session_state.page == "storyboard":
    render_storyboard()
    # ============================================================
# PART 3/3 — SCENE GENERATOR + FLOW/VEO PROMPT + SEO + FINISH
# ============================================================

def render_scenes():
    st.markdown("""
    <div class="hero">
        <div class="eyebrow">STEP 04 • FLOW / VEO PROMPT ENGINE</div>
        <h1>Generate Your Scenes</h1>
        <p>
            Generate one production-ready prompt at a time.
            Create the video in Google Flow, upload the final frame,
            then continue to the next scene.
        </p>
    </div>
    """, unsafe_allow_html=True)

    storyboard = st.session_state.get("storyboard", [])

    if not storyboard:
        st.warning("Storyboard belum tersedia.")

        if st.button("← BACK TO STORYBOARD"):
            st.session_state.page = "storyboard"
            st.rerun()

        return

    total_scenes = len(storyboard)

    if total_scenes > 23:
        total_scenes = 23

    current_scene = int(
        st.session_state.get(
            "current_scene",
            1
        )
    )

    current_scene = max(
        1,
        min(current_scene, total_scenes)
    )

    st.session_state.current_scene = current_scene

    # --------------------------------------------------------
    # PROJECT HEADER
    # --------------------------------------------------------

    selected = st.session_state.get(
        "selected_concept",
        {}
    )

    st.markdown(
        f"""
        <div class="selected-card">
            <div class="eyebrow">ACTIVE PROJECT</div>
            <h2>{selected.get("title", "Untitled Project")}</h2>
            <p>
                Scene {current_scene} of {total_scenes}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("")

    # --------------------------------------------------------
    # PROGRESS
    # --------------------------------------------------------

    progress = (
        (current_scene - 1) /
        max(total_scenes, 1)
    )

    st.progress(
        progress,
        text=f"Scene {current_scene} / {total_scenes}"
    )

    # --------------------------------------------------------
    # SCENE NAVIGATION
    # --------------------------------------------------------

    nav_cols = st.columns(5)

    for i in range(total_scenes):

        scene_number = i + 1

        with nav_cols[i % 5]:

            prompt_exists = (
                scene_number in
                st.session_state.get(
                    "scene_prompts",
                    {}
                )
            )

            label = (
                f"✓ {scene_number}"
                if prompt_exists
                else str(scene_number)
            )

            if st.button(
                label,
                key=f"scene_nav_{scene_number}",
                use_container_width=True
            ):
                st.session_state.current_scene = scene_number
                st.rerun()

    st.markdown("---")

    scene = storyboard[current_scene - 1]

    # --------------------------------------------------------
    # SCENE INFORMATION
    # --------------------------------------------------------

    st.markdown(
        f"### 🎬 SCENE {current_scene}"
    )

    st.caption(
        scene.get(
            "timecode",
            f"Scene {current_scene}"
        )
    )

    info_col1, info_col2 = st.columns(2)

    with info_col1:

        st.markdown("#### 🎯 Scene Purpose")

        st.write(
            scene.get(
                "purpose",
                ""
            )
        )

        st.markdown("#### 👀 Visual")

        st.write(
            scene.get(
                "visual",
                ""
            )
        )

        st.markdown("#### 🎭 Action")

        st.write(
            scene.get(
                "action",
                ""
            )
        )

    with info_col2:

        st.markdown("#### 📷 Camera")

        st.write(
            scene.get(
                "camera",
                ""
            )
        )

        st.markdown("#### 🔗 Subject Continuity")

        st.write(
            scene.get(
                "subject_continuity",
                ""
            )
        )

        st.markdown("#### 🌎 Environment Continuity")

        st.write(
            scene.get(
                "environment_continuity",
                ""
            )
        )

    st.markdown("#### 🔊 Audio")

    st.write(
        scene.get(
            "audio",
            ""
        )
    )

    st.markdown("---")

    # --------------------------------------------------------
    # PREVIOUS FRAME
    # --------------------------------------------------------

    previous_frame = None

    if current_scene > 1:

        st.markdown(
            "### 🖼️ LAST FRAME FROM PREVIOUS SCENE"
        )

        previous_frames = st.session_state.get(
            "scene_screenshots",
            {}
        )

        previous_frame = previous_frames.get(
            current_scene - 1
        )

        if previous_frame:

            st.image(
                previous_frame,
                caption=(
                    f"Continuity reference — "
                    f"Scene {current_scene - 1}"
                ),
                use_container_width=True
            )

        else:

            st.info(
                f"""
                Scene {current_scene - 1} belum memiliki
                screenshot frame terakhir.

                Untuk continuity terbaik:
                1. Generate Scene {current_scene - 1}
                2. Buat videonya di Google Flow
                3. Screenshot frame terakhir
                4. Upload screenshot tersebut di sini
                """
            )

    # --------------------------------------------------------
    # UPLOAD CURRENT PREVIOUS FRAME
    # --------------------------------------------------------

    if current_scene > 1:

        uploaded_frame = st.file_uploader(
            f"Upload last frame Scene {current_scene - 1}",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp"
            ],
            key=f"frame_upload_{current_scene}"
        )

        if uploaded_frame:

            st.session_state.scene_screenshots[
                current_scene - 1
            ] = uploaded_frame

            st.image(
                uploaded_frame,
                caption="Continuity frame uploaded",
                use_container_width=True
            )

    # --------------------------------------------------------
    # GENERATE PROMPT
    # --------------------------------------------------------

    existing_prompt = st.session_state.get(
        "scene_prompts",
        {}
    ).get(current_scene)

    if existing_prompt:

        st.markdown("### ⚡ FLOW / VEO PROMPT")

        st.success(
            "Prompt scene ini sudah dibuat."
        )

        st.text_area(
            "Copy this prompt into Google Flow",
            value=existing_prompt,
            height=520,
            key=f"existing_prompt_area_{current_scene}"
        )

        st.markdown("")

        regenerate_col, next_col = st.columns(2)

        with regenerate_col:

            if st.button(
                "🔄 REGENERATE PROMPT",
                use_container_width=True
            ):
                del st.session_state.scene_prompts[
                    current_scene
                ]

                st.rerun()

        with next_col:

            if current_scene < total_scenes:

                if st.button(
                    "NEXT SCENE →",
                    type="primary",
                    use_container_width=True
                ):

                    st.session_state.current_scene = (
                        current_scene + 1
                    )

                    st.rerun()

            else:

                if st.button(
                    "FINISH PROJECT →",
                    type="primary",
                    use_container_width=True
                ):

                    st.session_state.page = "seo"
                    st.rerun()

    else:

        st.markdown("### ⚡ GENERATE FLOW / VEO PROMPT")

        st.info(
            """
            Prompt ini dibuat untuk workflow manual:

            **Generate Prompt → Copy → Google Flow → Generate Video
            → Screenshot Last Frame → Upload → Next Scene**
            """
        )

        if st.button(
            f"⚡ GENERATE SCENE {current_scene} PROMPT",
            type="primary",
            use_container_width=True
        ):

            if not st.session_state.get(
                "gemini_api_key"
            ):
                st.error(
                    "Masukkan Gemini API Key terlebih dahulu."
                )
                return

            # ------------------------------------------------
            # PREVIOUS SCENE CONTEXT
            # ------------------------------------------------

            previous_scene_data = {}

            if current_scene > 1:

                previous_scene_data = storyboard[
                    current_scene - 2
                ]

            # ------------------------------------------------
            # CONTINUITY RULE
            # ------------------------------------------------

            continuity_instruction = ""

            if current_scene == 1:

                continuity_instruction = """
This is Scene 1.

Establish the main subject clearly.
Create a strong visual hook immediately.
Use a clean, readable composition.
The ending frame must provide a useful visual state
for continuation into Scene 2.
"""

            else:

                continuity_instruction = f"""
This is Scene {current_scene}.

A screenshot from the final frame of Scene
{current_scene - 1} may be supplied to the workflow.

Preserve visual continuity with that frame.

Maintain:
- subject identity
- subject appearance
- clothing
- body proportions
- colors
- important props
- environment
- time of day
- lighting direction
- spatial orientation

Do NOT randomly redesign the subject.

Continue naturally from the previous frame.

The first moments of this scene should feel like
the direct continuation of the previous scene.
"""

            # ------------------------------------------------
            # FLOW / VEO PROMPT
            # ------------------------------------------------

            flow_prompt = f"""
You are an expert cinematic AI video prompt engineer.

Create ONE production-ready prompt for Google Flow / Veo.

The prompt will be copied directly into a video generation tool.

PROJECT:
Title: {selected.get("title", "Untitled")}
Content Type: {st.session_state.get("content_type", "")}
Visual Style: {st.session_state.get("visual_style", "")}
Aspect Ratio: {st.session_state.get("aspect_ratio", "")}
Total Duration: {st.session_state.get("duration", "")}
Total Scenes: {total_scenes}

CURRENT SCENE:
Scene Number: {current_scene}
Timecode: {scene.get("timecode", "")}

SCENE PURPOSE:
{scene.get("purpose", "")}

VISUAL:
{scene.get("visual", "")}

ACTION:
{scene.get("action", "")}

CAMERA:
{scene.get("camera", "")}

SUBJECT CONTINUITY:
{scene.get("subject_continuity", "")}

ENVIRONMENT CONTINUITY:
{scene.get("environment_continuity", "")}

AUDIO:
{scene.get("audio", "")}

TRANSITION:
{scene.get("transition", "")}

PREVIOUS SCENE:
{json.dumps(previous_scene_data, ensure_ascii=False, indent=2)}

USER CREATIVE INSTRUCTION:
{st.session_state.get("custom_instruction", "")}

ORIGINALITY GUARD:
{st.session_state.get("originality_guard", "")}

CONTINUITY INSTRUCTION:
{continuity_instruction}

VIDEO REQUIREMENTS:

1. Duration approximately 8 seconds.
2. Clearly describe the main subject.
3. Clearly describe subject appearance.
4. Clearly describe clothing or physical design when relevant.
5. Clearly describe environment.
6. Clearly describe lighting.
7. Clearly describe camera framing.
8. Clearly describe camera movement.
9. Clearly describe physical action.
10. Describe realistic motion and believable physics.
11. Avoid unwanted text, subtitles, logos, watermarks,
    UI elements and random objects.
12. Do not introduce new characters unless the storyboard
    specifically requires them.
13. Do not change the identity or appearance of the
    established subject without a story reason.
14. Keep the scene visually readable.
15. Use cinematic composition appropriate for the selected style.
16. Preserve continuity from the previous scene.
17. Make the ending frame useful for the next scene.
18. Do not mention these instructions in the final prompt.

IMPORTANT:
The final answer must be ONLY the actual video prompt.
Do not add:
- explanation
- title
- JSON
- bullet points
- notes
- quotation marks around the prompt

Write one detailed paragraph suitable for direct
copy/paste into Google Flow / Veo.
"""

            with st.spinner(
                f"Generating Scene {current_scene} prompt..."
            ):

                result = generate_ai(
                    flow_prompt,
                    temperature=0.65,
                    max_output_tokens=5000
                )

            if result:

                final_prompt = result.strip()

                # Remove accidental markdown wrappers
                final_prompt = re.sub(
                    r"^```(?:text|markdown)?\s*",
                    "",
                    final_prompt,
                    flags=re.IGNORECASE
                )

                final_prompt = re.sub(
                    r"\s*```$",
                    "",
                    final_prompt
                )

                st.session_state.scene_prompts[
                    current_scene
                ] = final_prompt

                st.rerun()


# ============================================================
# SEO GENERATOR
# ============================================================

def render_seo():
    st.markdown("""
    <div class="hero">
        <div class="eyebrow">STEP 05 • PUBLISHING</div>
        <h1>SEO & Publishing Pack</h1>
        <p>
            Your video is ready. Generate the title,
            description, hashtags and publishing metadata.
        </p>
    </div>
    """, unsafe_allow_html=True)

    storyboard = st.session_state.get(
        "storyboard",
        []
    )

    selected = st.session_state.get(
        "selected_concept",
        {}
    )

    total_scenes = len(storyboard)

    prompts = st.session_state.get(
        "scene_prompts",
        {}
    )

    completed_scenes = len(prompts)

    st.progress(
        completed_scenes / max(total_scenes, 1),
        text=f"{completed_scenes} / {total_scenes} scene prompts completed"
    )

    # --------------------------------------------------------
    # COMPLETION CHECK
    # --------------------------------------------------------

    if completed_scenes < total_scenes:

        st.warning(
            f"""
            Belum semua scene selesai.

            Progress:
            {completed_scenes}/{total_scenes} prompts.

            Kamu tetap bisa melihat SEO, tetapi sebaiknya
            selesaikan semua scene terlebih dahulu.
            """
        )

    else:

        st.success(
            "🔥 Semua scene prompts sudah selesai!"
        )

    # --------------------------------------------------------
    # PROJECT SUMMARY
    # --------------------------------------------------------

    st.markdown("### 📊 PROJECT SUMMARY")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "SCENES",
            total_scenes
        )

    with col2:
        st.metric(
            "PROMPTS",
            completed_scenes
        )

    with col3:
        st.metric(
            "DURATION",
            st.session_state.get(
                "duration",
                "-"
            )
        )

    with col4:
        st.metric(
            "FORMAT",
            st.session_state.get(
                "aspect_ratio",
                "-"
            )
        )

    st.markdown("---")

    # --------------------------------------------------------
    # GENERATE SEO
    # --------------------------------------------------------

    if not st.session_state.get(
        "seo_package"
    ):

        if st.button(
            "🚀 GENERATE SEO PACKAGE",
            type="primary",
            use_container_width=True
        ):

            if not st.session_state.get(
                "gemini_api_key"
            ):
                st.error(
                    "Masukkan Gemini API Key terlebih dahulu."
                )
                return

            seo_prompt = f"""
You are an expert YouTube SEO strategist.

Create a complete publishing package for an original
YouTube video.

PROJECT TITLE:
{selected.get("title", "")}

CONCEPT:
{selected.get("concept", "")}

CONTENT TYPE:
{st.session_state.get("content_type", "")}

DURATION:
{st.session_state.get("duration", "")}

USER CREATIVE INSTRUCTION:
{st.session_state.get("custom_instruction", "")}

Create:

1. Three highly clickable YouTube titles.
2. One optimized description.
3. Ten relevant search keywords.
4. Fifteen hashtags.
5. One short thumbnail text.
6. One thumbnail concept.
7. One pinned comment.
8. One short CTA.

Avoid:
- misleading claims
- excessive clickbait
- copyrighted character names
- fake celebrity references
- trademark stuffing

Make the metadata suitable for YouTube Shorts
and long-form YouTube.

Return ONLY valid JSON:

{{
  "titles": [
    "...",
    "...",
    "..."
  ],
  "description": "...",
  "keywords": [
    "...",
    "..."
  ],
  "hashtags": [
    "...",
    "..."
  ],
  "thumbnail_text": "...",
  "thumbnail_concept": "...",
  "pinned_comment": "...",
  "cta": "..."
}}
"""

            with st.spinner(
                "Generating YouTube SEO package..."
            ):

                result = generate_ai(
                    seo_prompt,
                    temperature=0.65,
                    max_output_tokens=5000
                )

            if result:

                data = clean_json(result)

                if data:

                    st.session_state.seo_package = data

                    st.rerun()

                else:

                    st.error(
                        "SEO response tidak valid."
                    )

    # --------------------------------------------------------
    # DISPLAY SEO
    # --------------------------------------------------------

    seo = st.session_state.get(
        "seo_package"
    )

    if seo:

        st.markdown("### 🏆 YOUTUBE TITLES")

        titles = seo.get(
            "titles",
            []
        )

        for idx, title in enumerate(
            titles,
            start=1
        ):

            st.text_area(
                f"Title {idx}",
                value=str(title),
                height=70,
                key=f"seo_title_{idx}"
            )

        st.markdown("### 📝 DESCRIPTION")

        st.text_area(
            "YouTube Description",
            value=seo.get(
                "description",
                ""
            ),
            height=220,
            key="seo_description"
        )

        st.markdown("### 🔍 KEYWORDS")

        keywords = seo.get(
            "keywords",
            []
        )

        st.text_area(
            "Keywords",
            value=", ".join(
                str(x)
                for x in keywords
            ),
            height=100,
            key="seo_keywords"
        )

        st.markdown("### #️⃣ HASHTAGS")

        hashtags = seo.get(
            "hashtags",
            []
        )

        st.text_area(
            "Hashtags",
            value=" ".join(
                str(x)
                for x in hashtags
            ),
            height=100,
            key="seo_hashtags"
        )

                st.markdown("### 🖼️ THUMBNAIL")

        thumb_col1, thumb_col2 = st.columns(2)

        with thumb_col1:
            st.text_area(
                "Thumbnail Text",
                value=seo.get(
                    "thumbnail_text",
                    ""
                ),
                height=90,
                key="thumbnail_text"
            )

        with thumb_col2:
            st.text_area(
                "Thumbnail Concept",
                value=seo.get(
                    "thumbnail_concept",
                    ""
                ),
                height=120,
                key="thumbnail_concept"
            )

        st.markdown("### 💬 PINNED COMMENT")

        st.text_area(
            "Pinned Comment",
            value=seo.get(
                "pinned_comment",
                ""
            ),
            height=100,
            key="pinned_comment"
        )

        st.markdown("### 📣 CTA")

        st.text_area(
            "Call To Action",
            value=seo.get(
                "cta",
                ""
            ),
            height=80,
            key="seo_cta"
        )

        st.markdown("---")

        st.markdown("### 🎉 PROJECT COMPLETE")

        st.success(
            """
            Workflow selesai.

            Sekarang kamu memiliki:
            ✓ Original concept
            ✓ Storyboard
            ✓ Scene prompts
            ✓ Continuity workflow
            ✓ YouTube SEO package
            """
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "🎬 BACK TO SCENES",
                use_container_width=True
            ):
                st.session_state.current_scene = 1
                st.session_state.page = "scenes"
                st.rerun()

        with col2:
            if st.button(
                "🆕 NEW PROJECT",
                type="primary",
                use_container_width=True
            ):
                reset_project()
                st.session_state.page = "home"
                st.rerun()


# ============================================================
# FINAL ROUTER
# ============================================================

if st.session_state.page == "scenes":
    render_scenes()

elif st.session_state.page == "seo":
    render_seo()
