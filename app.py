import json, re
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title='UGC Remix Studio', page_icon='🎬', layout='wide')

MODEL = 'gemini-3.6-flash'

DURATIONS = {
    '8 seconds': 1,
    '16 seconds': 2,
    '24 seconds': 3,
    '32 seconds': 4,
    '40 seconds': 5,
    '48 seconds': 6,
    '56 seconds': 7,
    '1 minute': 8,
    '1.5 minutes': 12,
    '2 minutes': 15,
    '2.5 minutes': 19,
    '3 minutes': 23
}

STYLES = [
    'Realistic cinematic',
    '3D animation',
    '2D animation',
    'Stylized comedy',
    'Cute family-friendly',
    'Documentary / realistic',
    'Action cinematic',
    'Custom'
]

RATIOS = [
    '9:16 — Shorts / Reels / TikTok',
    '16:9 — YouTube',
    '1:1 — Square'
]

DEFAULTS = dict(
    page='home',
    api_key='',
    reference_type='Video',
    reference_file=None,
    reference_files=[],
    reference_text='',
    visual_style='Realistic cinematic',
    aspect_ratio=RATIOS[0],
    duration='8 seconds',
    custom_instruction='',
    analysis={},
    concepts=[],
    selected_concept=None,
    selected_concept_index=None,
    storyboard=[],
    scene_prompts={},
    scene_frames={},
    current_scene=1,
    seo={}
)

for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


def reset():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


def client():
    key = st.session_state.api_key.strip()

    if not key:
        st.error('Masukkan Gemini API Key di sidebar.')
        return None

    try:
        return genai.Client(api_key=key)
    except Exception as e:
        st.error(f'Gemini client error: {e}')
        return None


def ask(c, prompt, parts=None):
    content = [prompt] + (parts or [])

    last_error = None

    for attempt in range(3):
        try:
            r = c.models.generate_content(
                model=MODEL,
                contents=content,
                config=types.GenerateContentConfig(
                    temperature=0.8
                )
            )

            return r.text or ''

        except Exception as e:
            last_error = e

            if '503' in str(e) or 'UNAVAILABLE' in str(e):
                import time
                time.sleep(3 * (attempt + 1))
                continue

            raise e

    raise RuntimeError(
        f'Gemini sedang sibuk setelah 3 percobaan. '
        f'Coba tekan tombol lagi beberapa saat kemudian.\n\n'
        f'Error: {last_error}'
    )
    content = [prompt] + (parts or [])

    r = c.models.generate_content(
        model=MODEL,
        contents=content,
        config=types.GenerateContentConfig(
            temperature=0.8
        )
    )

    return r.text or ''


def to_json(text):
    text = text.strip()

    text = re.sub(
        r'^```(?:json)?\s*',
        '',
        text,
        flags=re.I
    )

    text = re.sub(
        r'\s*```$',
        '',
        text
    )

    try:
        return json.loads(text)
    except:
        pass

    for start in [
        text.find('{'),
        text.find('[')
    ]:
        if start >= 0:
            for end in range(
                len(text),
                start,
                -1
            ):
                try:
                    return json.loads(
                        text[start:end]
                    )
                except:
                    pass

    raise ValueError(
        'Respons AI bukan JSON valid.'
    )


def upload(c, f):
    if not f:
        return None

    try:
        mime = getattr(
            f,
            'type',
            None
        )

        return c.files.upload(
            file=f,
            config={
                'display_name': f.name,
                'mime_type': mime
            }
        )

    except Exception as e:
        st.warning(
            f'Upload gagal: {e}'
        )
        return None


def nav(page):
    st.session_state.page = page
    st.rerun()


def nscene():
    return DURATIONS[
        st.session_state.duration
    ]


def concept():
    return (
        st.session_state.selected_concept
        or {}
    )


def safe(v):
    if isinstance(v, list):
        return ', '.join(
            map(str, v)
        )

    return str(v or '')


with st.sidebar:

    st.title('🎬 UGC Remix Studio')

    st.caption(
        'Reference → Remix → Storyboard → Flow/Veo'
    )

    st.text_input(
        'Gemini API Key',
        type='password',
        key='api_key',
        placeholder='AIza...'
    )

    st.divider()

    for label, page in [
        ('🏠 Home', 'home'),
        ('💡 Concepts', 'concepts'),
        ('🧩 Storyboard', 'storyboard'),
        ('🎥 Scene Prompts', 'scenes'),
        ('🔎 YouTube SEO', 'seo')
    ]:

        if st.button(
            label,
            use_container_width=True
        ):
            nav(page)

    st.divider()

    if st.button(
        '🆕 New Project',
        use_container_width=True
    ):
        reset()
        st.rerun()


# ============================================================
# AI ANALYZER
# ============================================================

def analyze():

    c = client()

    if not c:
        return

    ref = st.session_state.reference_type

    parts = []

    if (
        ref == 'Video'
        and st.session_state.reference_file
    ):
        x = upload(
            c,
            st.session_state.reference_file
        )

        if x:
            parts = [x]

    elif ref == 'Screenshots':

        for f in st.session_state.reference_files:

            x = upload(c, f)

            if x:
                parts.append(x)

    source = (
        st.session_state.reference_text
        if ref == 'Text / idea'
        else '(reference file supplied)'
    )

    p = f'''
Analyze this reference and create
3 ORIGINAL remix concepts.

ALL analysis and concepts MUST be
in BAHASA INDONESIA.

Only the later Flow/Veo production
prompt uses English.

REFERENCE TYPE:
{ref}

TEXT:
{source}

STYLE:
{st.session_state.visual_style}

RATIO:
{st.session_state.aspect_ratio}

DURATION:
{st.session_state.duration}

CREATIVE INSTRUCTION:
{st.session_state.custom_instruction}


IMPORTANT MAIN SUBJECT RULE:

Identify the main subject.

Keep the same main subject/type
when it is clearly identifiable.

If the reference has a cat,
keep a cat.

Do NOT randomly replace the main
subject with a robot, human, alien,
or unrelated animal.

Remix the story execution instead.


ORIGINALITY:

Preserve the high-level hook,
cause/effect, emotional goal,
escalation, payoff and pacing.

But substantially change the execution.

Change setting, secondary details,
props, action details, camera,
lighting, dialogue wording and
sound design.

Do not copy brands, logos,
watermarks, exact dialogue,
exact shots, distinctive costumes,
or recognizable creator/studio identity.


SAFETY:

Never create real dangerous
electrical interaction.

If electricity, plugs, sockets,
wires, fire or similar hazards
appear, convert them into clearly
fake, unplugged, toy-like,
harmless or fictional props.

Keep the entertainment logic.


RETURN ONLY JSON.

The JSON must contain:

{{
  "analysis": {{
    "main_subject": "...",
    "source_summary": "...",
    "niche": "...",
    "hook": "...",
    "cause_effect": "...",
    "emotional_goal": "...",
    "pacing_logic": "...",
    "payoff": "...",
    "key_visual_mechanics": "...",
    "transformation_notes": "..."
  }},

  "concepts": [
    {{
      "title": "...",
      "one_line_pitch": "...",
      "niche": "...",
      "main_subjects": "...",
      "hook": "...",
      "story_arc": "...",
      "setting": "...",
      "visual_direction": "...",
      "comedy_or_drama_engine": "...",
      "ending_payoff": "...",
      "why_it_is_original": "..."
    }}
  ]
}}

The concepts array MUST contain
EXACTLY 3 concepts.
'''

    with st.spinner(
        'AI Analyzer + Auto Remix berjalan...'
    ):

        try:

            data = to_json(
                ask(
                    c,
                    p,
                    parts
                )
            )

            cs = data.get(
                'concepts',
                []
            )

            if len(cs) != 3:
                raise ValueError(
                    f'AI menghasilkan '
                    f'{len(cs)} konsep, '
                    f'harus 3.'
                )

            st.session_state.analysis = \
                data.get(
                    'analysis',
                    {}
                )

            st.session_state.concepts = cs

            st.session_state.selected_concept = None
            st.session_state.storyboard = []
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}

            nav('concepts')

        except Exception as e:

            st.error(
                f'Analisis gagal: {e}'
            )


# ============================================================
# HOME
# ============================================================

def home():

    st.title(
        '🎬 UGC Remix Studio'
    )

    st.write(
        'Masukkan referensi → '
        'AI analisis → 3 konsep → '
        'storyboard → prompt Flow/Veo → SEO.'
    )

    st.subheader(
        '1. Reference'
    )

    st.session_state.reference_type = st.radio(
        'Jenis referensi',
        [
            'Video',
            'Screenshots',
            'Text / idea'
        ],
        horizontal=True,
        index=[
            'Video',
            'Screenshots',
            'Text / idea'
        ].index(
            st.session_state.reference_type
        )
    )

    if (
        st.session_state.reference_type
        == 'Video'
    ):

        st.session_state.reference_file = \
            st.file_uploader(
                'Upload video',
                type=[
                    'mp4',
                    'mov',
                    'webm',
                    'avi',
                    'mkv'
                ],
                key='ref_video'
            )

    elif (
        st.session_state.reference_type
        == 'Screenshots'
    ):

        st.session_state.reference_files = \
            st.file_uploader(
                'Upload screenshot',
                type=[
                    'png',
                    'jpg',
                    'jpeg',
                    'webp'
                ],
                accept_multiple_files=True,
                key='ref_images'
            )

    else:

        st.session_state.reference_text = \
            st.text_area(
                'Tulis ide / deskripsi referensi',
                height=140,
                value=st.session_state.reference_text
            )

    st.subheader(
        '2. Output'
    )

    st.session_state.visual_style = \
        st.selectbox(
            'Visual style',
            STYLES,
            index=STYLES.index(
                st.session_state.visual_style
            )
        )

    st.session_state.aspect_ratio = \
        st.selectbox(
            'Aspect ratio',
            RATIOS,
            index=RATIOS.index(
                st.session_state.aspect_ratio
            )
        )

    st.session_state.duration = \
        st.selectbox(
            'Duration',
            list(DURATIONS),
            index=list(DURATIONS).index(
                st.session_state.duration
            )
        )

    st.caption(
        f'≈ 8 detik per scene • '
        f'total {nscene()} scene'
    )

    st.session_state.custom_instruction = \
        st.text_area(
            'Creative instruction (opsional)',
            value=st.session_state.custom_instruction,
            height=100
        )

    st.subheader(
        '3. Originality & Safety'
    )

    st.info(
        'Subjek utama tetap konsisten. '
        'Detail eksekusi dibuat baru. '
        'Adegan berbahaya diubah menjadi '
        'properti aman/fiktif.'
    )

    if st.button(
        '🚀 ANALYZE + CREATE 3 CONCEPTS',
        type='primary',
        use_container_width=True
    ):
        analyze()


# ============================================================
# CONCEPTS
# ============================================================

def concepts():

    st.title(
        '💡 3 Original Concepts'
    )

    if not st.session_state.concepts:

        st.info(
            'Belum ada konsep. '
            'Kembali ke Home.'
        )

        return
    st.write(
        'Pilih salah satu konsep untuk dibuatkan storyboard.'
    )

    for i, cpt in enumerate(
        st.session_state.concepts
    ):

        with st.container(border=True):

            st.subheader(
                f'Concept {i + 1}: {cpt.get("title", "")}'
            )

            st.write(
                cpt.get(
                    'one_line_pitch',
                    ''
                )
            )

            col1, col2 = st.columns(2)

            with col1:
                st.write(
                    '**Niche:**',
                    cpt.get('niche', '')
                )

                st.write(
                    '**Main Subject:**',
                    cpt.get('main_subjects', '')
                )

                st.write(
                    '**Hook:**',
                    cpt.get('hook', '')
                )

                st.write(
                    '**Setting:**',
                    cpt.get('setting', '')
                )

            with col2:

                st.write(
                    '**Story Arc:**',
                    cpt.get('story_arc', '')
                )

                st.write(
                    '**Visual Direction:**',
                    cpt.get('visual_direction', '')
                )

                st.write(
                    '**Payoff:**',
                    cpt.get('ending_payoff', '')
                )

            if st.button(
                f'✅ USE CONCEPT {i + 1}',
                key=f'use_concept_{i}',
                type='primary',
                use_container_width=True
            ):

                st.session_state.selected_concept = cpt
                st.session_state.selected_concept_index = i
                st.session_state.storyboard = []
                st.session_state.scene_prompts = {}
                st.session_state.scene_frames = {}
                st.session_state.current_scene = 1

                nav('storyboard')


# ============================================================
# STORYBOARD
# ============================================================

def make_storyboard():

    c = client()

    if not c:
        return

    cpt = concept()
    n = nscene()

    p = f'''
Create a production storyboard for this ORIGINAL video concept.

IMPORTANT LANGUAGE RULE:

Write the ENTIRE storyboard in
BAHASA INDONESIA.

Do NOT write the storyboard in English.

English is reserved ONLY for the
final Google Flow / Veo generation prompt.

CONCEPT:
{json.dumps(cpt, ensure_ascii=False, indent=2)}

TOTAL DURATION:
{st.session_state.duration}

TOTAL SCENES:
{n}

VISUAL STYLE:
{st.session_state.visual_style}

ASPECT RATIO:
{st.session_state.aspect_ratio}

CREATIVE INSTRUCTION:
{st.session_state.custom_instruction}


MAIN SUBJECT RULE:

Keep the main subject from the
selected concept consistent.

If the main subject is a cat,
keep it a cat in every scene.

Do NOT randomly transform the
main subject into a robot, human,
alien, or unrelated creature.

Maintain consistent appearance,
identity, behavior and important
props.


STORY STRUCTURE:

Each scene is approximately
8 seconds.

Create exactly {n} scenes.

The story must have a clear:

HOOK
→ DEVELOPMENT
→ ESCALATION
→ PAYOFF

Every scene must logically connect
to the next scene.


CONTINUITY:

Maintain consistent:

- main subject
- appearance
- environment
- important props
- lighting
- time of day
- spatial geography
- action progression


SAFETY:

Never instruct a person or animal
to interact with live electricity
or dangerous equipment.

If the story contains electricity,
plugs, sockets, wires, fire or
similar hazards, convert them into
clearly fake, unplugged, toy-like,
harmless or fictional props.

Keep the story entertaining.


RETURN ONLY VALID JSON:

{{
  "scenes": [
    {{
      "scene": 1,
      "time": "00:00-00:08",
      "purpose": "...",
      "visual": "...",
      "action": "...",
      "camera": "...",
      "continuity": "...",
      "audio": "...",
      "transition": "..."
    }}
  ]
}}

The scenes array MUST contain
exactly {n} scenes.
'''

    with st.spinner(
        f'Membuat storyboard {n} scene...'
    ):

        try:

            data = to_json(
                ask(c, p)
            )

            scenes = data.get(
                'scenes',
                []
            )

            if len(scenes) != n:

                raise ValueError(
                    f'Storyboard harus {n} scene, '
                    f'tetapi AI menghasilkan '
                    f'{len(scenes)} scene.'
                )

            for i, scene in enumerate(
                scenes,
                start=1
            ):

                scene['scene'] = i

                if not scene.get('time'):
                    scene['time'] = (
                        f'{(i - 1) * 8:02d}-'
                        f'{i * 8:02d}'
                    )

            st.session_state.storyboard = scenes
            st.session_state.scene_prompts = {}
            st.session_state.scene_frames = {}
            st.session_state.current_scene = 1

            st.rerun()

        except Exception as e:

            st.error(
                f'Gagal membuat storyboard: {e}'
            )


def storyboard():

    st.title(
        '🧩 Storyboard'
    )

    cpt = concept()

    if not cpt:

        st.info(
            'Pilih konsep terlebih dahulu.'
        )

        if st.button(
            '← Kembali ke Concepts'
        ):
            nav('concepts')

        return

    st.success(
        f'Concept {st.session_state.selected_concept_index + 1}: '
        f'{cpt.get("title", "")}'
    )

    st.write(
        f'**Duration:** {st.session_state.duration} '
        f'• **Scenes:** {nscene()}'
    )

    if not st.session_state.storyboard:

        if st.button(
            '🧩 GENERATE STORYBOARD',
            type='primary',
            use_container_width=True
        ):

            make_storyboard()

        return

    for scene in st.session_state.storyboard:

        with st.expander(
            f'Scene {scene["scene"]} • '
            f'{scene.get("time", "")} • '
            f'{scene.get("purpose", "")}'
        ):

            st.write(
                '**Visual:**',
                scene.get('visual', '')
            )

            st.write(
                '**Action:**',
                scene.get('action', '')
            )

            st.write(
                '**Camera:**',
                scene.get('camera', '')
            )

            st.write(
                '**Continuity:**',
                scene.get('continuity', '')
            )

            st.write(
                '**Audio:**',
                scene.get('audio', '')
            )

            st.write(
                '**Transition:**',
                scene.get('transition', '')
            )

    st.divider()

    if st.button(
        '🎥 CONTINUE TO SCENE PROMPTS',
        type='primary',
        use_container_width=True
    ):

        nav('scenes')


# ============================================================
# SCENE PROMPT
# ============================================================

def previous_scene_info(scene_number):

    if scene_number <= 1:

        return (
            'Scene 1. There is no previous scene.'
        )

    previous = (
        st.session_state.storyboard[
            scene_number - 2
        ]
    )

    return json.dumps(
        previous,
        ensure_ascii=False,
        indent=2
    )


def make_scene_prompt(scene_number):

    c = client()

    if not c:
        return

    scenes = st.session_state.storyboard

    scene = scenes[
        scene_number - 1
    ]

    cpt = concept()

    previous_frame = (
        st.session_state.scene_frames.get(
            scene_number - 1
        )
    )

    p = f'''
You are writing ONE production-ready
Google Flow / Veo video generation prompt.

Create the prompt for:

SCENE {scene_number} OF {len(scenes)}

PROJECT CONCEPT:
{cpt.get("title", "")}

MAIN SUBJECT:
{cpt.get("main_subjects", "")}

VISUAL STYLE:
{st.session_state.visual_style}

ASPECT RATIO:
{st.session_state.aspect_ratio}

TOTAL DURATION:
{st.session_state.duration}


CURRENT STORYBOARD SCENE:

{json.dumps(
    scene,
    ensure_ascii=False,
    indent=2
)}


PREVIOUS SCENE:

{previous_scene_info(scene_number)}


LANGUAGE RULE:

The FINAL prompt MUST be written
ONLY in ENGLISH.

Do NOT output Indonesian.

Do NOT output JSON.

Do NOT output headings.

Do NOT output bullet points.

Write exactly ONE detailed paragraph.


MAIN SUBJECT CONSISTENCY:

The main subject must remain
consistent with the selected concept.

If the main subject is a cat,
it MUST remain a cat.

Never randomly transform the main
subject into a robot, human, alien,
or another unrelated creature.

Keep appearance, identity and
important props consistent.


CONTINUITY:

If a previous scene last-frame
image is supplied, use it to
maintain visual continuity.

Preserve:

subject identity,
appearance,
wardrobe if applicable,
prop placement,
environment,
lighting direction,
camera geography,
and motion state.

Do not copy unrelated details.


ORIGINALITY:

Do not reproduce copyrighted
characters, brands, logos,
watermarks, exact dialogue,
exact shots, distinctive costumes,
or recognizable creator/studio style.

Preserve the story logic but use
original execution.


SAFETY:

Do not show or instruct real
dangerous electrical interaction.

If the scene contains plugs,
sockets, wires, electricity,
fire or similar hazards, make
them clearly fake, unplugged,
toy-like, harmless or fictional.

Never show an animal or person
performing a dangerous electrical
action.


THE PROMPT MUST INCLUDE:

Detailed subject appearance,
environment, exact action,
facial/body performance,
camera framing,
camera movement,
lens,
depth of field,
lighting,
color mood,
realistic physics and motion,
sound effects,
ambient sound,
dialogue only when necessary,
and a clean transition-ready ending.

Make the scene directly usable
inside Google Flow / Veo.
'''

    parts = []

    if previous_frame:

        try:

            uploaded = upload(
                c,
                previous_frame
            )

            if uploaded:
                parts.append(uploaded)

        except Exception as e:

            st.warning(
                f'Frame continuity gagal '
                f'dikirim: {e}'
            )

    with st.spinner(
        f'Generating Flow/Veo prompt Scene {scene_number}...'
    ):

        try:

            result = ask(
                c,
                p,
                parts
            ).strip()

            if not result:

                raise ValueError(
                    'AI mengembalikan prompt kosong.'
                )

            st.session_state.scene_prompts[
                scene_number
            ] = result

        except Exception as e:

            st.error(
                f'Gagal membuat prompt scene: {e}'
            )


def scenes_page():

    st.title(
        '🎥 Scene-by-Scene Flow/Veo Prompts'
    )

    scenes = (
        st.session_state.storyboard
    )

    if not scenes:

        st.info(
            'Storyboard belum dibuat.'
        )

        if st.button(
            '← Kembali ke Storyboard'
        ):
            nav('storyboard')

        return

    total = len(scenes)

    current = max(
        1,
        min(
            st.session_state.current_scene,
            total
        )
    )

    st.session_state.current_scene = current

    scene = scenes[
        current - 1
    ]

    st.subheader(
        f'Scene {current} / {total}'
    )

    st.caption(
        f'{scene.get("time", "")} • '
        f'{scene.get("purpose", "")}'
    )

    with st.expander(
        '📋 Lihat storyboard scene'
    ):

        st.write(
            '**Visual:**',
            scene.get('visual', '')
        )

        st.write(
            '**Action:**',
            scene.get('action', '')
        )

        st.write(
            '**Camera:**',
            scene.get('camera', '')
        )

        st.write(
            '**Continuity:**',
            scene.get('continuity', '')
        )

        st.write(
            '**Audio:**',
            scene.get('audio', '')
        )

        st.write(
            '**Transition:**',
            scene.get('transition', '')
        )

    st.divider()

    if current > 1:

        st.write(
            '📸 Upload last-frame dari '
            f'Scene {current - 1} untuk continuity.'
        )

        frame = st.file_uploader(
            f'Last-frame Scene {current - 1}',
            type=[
                'png',
                'jpg',
                'jpeg',
                'webp'
            ],
            key=f'frame_{current - 1}'
        )

        if frame:

            st.session_state.scene_frames[
                current - 1
            ] = frame

            st.image(
                frame,
                caption=(
                    f'Last-frame Scene '
                    f'{current - 1}'
                ),
                use_container_width=True
            )

    prompt = (
        st.session_state.scene_prompts.get(
            current,
            ''
        )
    )

    if not prompt:

        if st.button(
            f'✨ GENERATE PROMPT SCENE {current}',
            type='primary',
            use_container_width=True
        ):

            make_scene_prompt(current)

            st.rerun()

    else:

        st.success(
            'Prompt siap dipakai di Google Flow / Veo.'
        )

        st.text_area(
            'Flow / Veo Prompt',
            value=prompt,
            height=330,
            key=f'prompt_display_{current}'
        )

        st.download_button(
            '📄 Download Prompt',
            data=prompt,
            file_name=(
                f'scene_{current}_prompt.txt'
            ),
            mime='text/plain',
            use_container_width=True
        )

        if st.button(
            f'🔄 REGENERATE SCENE {current}',
            use_container_width=True
        ):

            del st.session_state.scene_prompts[
                current
            ]

            make_scene_prompt(current)

            st.rerun()

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        if current > 1:

            if st.button(
                '⬅️ PREVIOUS',
                use_container_width=True
            ):

                st.session_state.current_scene -= 1
                st.rerun()

    with col2:

        st.write(
            f'**{current} / {total}**'
        )

    with col3:

        if current < total:

            if st.button(
                'NEXT ➡️',
                use_container_width=True
            ):

                st.session_state.current_scene += 1
                st.rerun()

    st.divider()

    jump = st.selectbox(
        'Jump ke scene',
        list(range(1, total + 1)),
        index=current - 1
    )

    if jump != current:

        st.session_state.current_scene = jump
        st.rerun()

    if current == total:

        st.success(
            '🎉 Semua scene selesai. '
            'Lanjut ke SEO.'
        )

        if st.button(
            '🔎 CONTINUE TO YOUTUBE SEO',
            type='primary',
            use_container_width=True
        ):

            nav('seo')


# ============================================================
# YOUTUBE SEO
# ============================================================

def make_seo():

    c = client()

    if not c:
        return

    cpt = concept()

    p = f'''
Create a YouTube SEO package for
this original video.

WRITE EVERYTHING IN BAHASA INDONESIA.

Concept:
{json.dumps(
    cpt,
    ensure_ascii=False,
    indent=2
)}

Duration:
{st.session_state.duration}

Main subject:
{cpt.get("main_subjects", "")}

Return ONLY valid JSON:

{{
  "title": "...",
  "alternative_titles": [
    "...",
    "...",
    "..."
  ],
  "description": "...",
  "hashtags": [
    "#...",
    "#...",
    "#..."
  ],
  "keywords": [
    "...",
    "...",
    "..."
  ],
  "thumbnail_text": "..."
}}
'''

    with st.spinner(
        'Membuat YouTube SEO...'
    ):

        try:

            data = to_json(
                ask(c, p)
            )

            st.session_state.seo = data

        except Exception as e:

            st.error(
                f'Gagal membuat SEO: {e}'
            )


def seo_page():

    st.title(
        '🔎 YouTube SEO'
    )

    if not st.session_state.storyboard:

        st.info(
            'Buat storyboard terlebih dahulu.'
        )

        return

    seo = st.session_state.seo

    if not seo:

        if st.button(
            '🚀 GENERATE YOUTUBE SEO',
            type='primary',
            use_container_width=True
        ):

            make_seo()

            st.rerun()

        return

    st.subheader(
        '🎯 Judul Utama'
    )

    st.text_input(
        'Title',
        value=seo.get(
            'title',
            ''
        )
    )

    st.subheader(
        '💡 Alternative Titles'
    )

    for title in seo.get(
        'alternative_titles',
        []
    ):

        st.write(
            f'• {title}'
        )

    st.subheader(
        '📝 Description'
    )

    st.text_area(
        'Description',
        value=seo.get(
            'description',
            ''
        ),
        height=220
    )

    st.subheader(
        '#️⃣ Hashtags'
    )

    st.write(
        ' '.join(
            seo.get(
                'hashtags',
                []
            )
        )
    )

    st.subheader(
        '🔑 Keywords'
    )

    st.write(
        ', '.join(
            seo.get(
                'keywords',
                []
            )
        )
    )

    st.subheader(
        '🖼️ Thumbnail Text'
    )

    st.write(
        seo.get(
            'thumbnail_text',
            ''
        )
    )

    if st.button(
        '🔄 REGENERATE SEO',
        use_container_width=True
    ):

        st.session_state.seo = {}

        make_seo()

        st.rerun()


# ============================================================
# ROUTER
# ============================================================

if st.session_state.page == 'home':

    home()

elif st.session_state.page == 'concepts':

    concepts()

elif st.session_state.page == 'storyboard':

    storyboard()

elif st.session_state.page == 'scenes':

    scenes_page()

elif st.session_state.page == 'seo':

    seo_page()

else:

    home()
