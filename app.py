import streamlit as st
import yt_dlp
import os
from google import genai

# --- PAGE CONFIG ---
st.set_page_config(page_title="Studio AI - Pro Continuity UGC Engine", page_icon="⚡", layout="centered")
st.title("⚡ UGC Vtoyz Studio AI")
st.caption("AI Video Continuity: Step-by-Step Chain + Sizing Pas 8s per Scene (No Cut CapCut!)")

# --- API KEYS SETUP ---
gemini_key = st.sidebar.text_input("Gemini API Key (Wajib - Format AQ...)", type="password")

client = None
if gemini_key:
    clean_key = gemini_key.strip().replace(" ", "_").replace("\n", "").replace("\r", "")
    try:
        client = genai.Client(api_key=clean_key)
    except Exception as e:
        st.sidebar.error(f"Format Key Error: {e}")

# --- PILIH STYLE VISUAL & TARGET DURASI DI SIDEBAR ---
style_pilihan = st.sidebar.selectbox(
    "🎨 Pilih Gaya Visual Video:",
    options=[
        "2D Anime (Studio Ghibli 100% Traditional Hand-Drawn Cel-Shaded Style)",
        "Realistis / Photorealistic (8K Cinematic)",
        "3D Animation (Pixar / Dreamworks Style)",
        "Comic Book / Pop Art (Bold Lines & Halftone)",
        "Claymation (Stop Motion Style)"
    ]
)

target_durasi_label = st.sidebar.selectbox(
    "⏱️ Target Total Durasi Video (Kelipatan 8s):",
    options=[
        "16 Detik (2 Scene)",
        "24 Detik (3 Scene)",
        "32 Detik (4 Scene)",
        "40 Detik (5 Scene)",
        "48 Detik (6 Scene)",
        "56 Detik (7 Scene)"
    ]
)

# Konversi pilihan durasi jadi angka maksimal scene
max_scenes = int(target_durasi_label.split("(")[1].split(" ")[0])

# --- WORKFLOW SESSION STATE ---
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.scene_history = []
    st.session_state.current_story_context = ""

# --- TAHAP 1: MEMBUAT SCENE 1 ---
if st.session_state.step == 1:
    st.subheader(f"🎬 Tahap 1 dari {max_scenes}: Buat Adegan Pertama (Scene 1)")
    st.info(f"💡 Target total video lu: **{target_durasi_label}** (Setiap scene berdurasi tepat 8 detik).")
    
    input_mode = st.radio(
        "Metode Input Awal:",
        ("📁 Upload File Video Referensi", "✍️ Input Topik / Ide Cerita Baru")
    )

    video_path = "temp_video.mp4"
    video_ready = False
    user_topic = ""

    if input_mode == "📁 Upload File Video Referensi":
        uploaded_video = st.file_uploader("Upload Video Referensi:", type=["mp4", "mov", "avi"])
        if uploaded_video is not None:
            with open(video_path, "wb") as f:
                f.write(uploaded_video.read())
            video_ready = True
            st.success("Video referensi siap!")
    else:
        user_topic = st.text_area("Tuliskan Ide / Topik Cerita Keseluruhan:")
        if user_topic:
            video_ready = True

    if st.button("🚀 Racik Prompt Scene 1"):
        if not gemini_key or not client:
            st.error("⚠️ Masukkan Gemini API Key di sidebar!")
        elif not video_ready:
            st.error("⚠️ Masukkan input video atau topik terlebih dahulu!")
        else:
            with st.spinner("AI sedang merancang fondasi karakter dan Scene 1 (8 detik)..."):
                try:
                    system_instruction = f"""
                    Kamu adalah Sutradara & Master Prompt Engineer spesialis AI Video Generation.
                    Tugasmu membuat SCENE 1 (Durasi tepat 8 detik) dari total {max_scenes} scene yang direncanakan.
                    
                    GAYA VISUAL WAJIB: {style_pilihan}.
                    
                    Tugas spesifik:
                    1. Tetapkan 'CHARACTER ANCHOR' yang sangat detail (bentuk fisik, warna, pakaian, ekspresi) di awal prompt agar nanti bisa konsisten dipakai di {max_scenes} scene berikutnya.
                    2. Buat Prompt Scene 1 yang sinematik berdurasi 8 detik.
                    3. Buat Naskah Voiceover (VO) Scene 1 dalam Bahasa Indonesia yang pas untuk durasi 8 detik.

                    FORMAT OUTPUT MESTI TERPISAH:
                    [SCENE_DESC]
                    (Deskripsi detail karakter & prompt scene 1 - 8 detik)
                    [/SCENE_DESC]
                    [VO_SCRIPT]
                    (Naskah VO Scene 1)
                    [/VO_SCRIPT]
                    """

                    if input_mode == "✍️ Input Topik / Ide Cerita Baru":
                        full_prompt = f"{system_instruction}\n\nTopik Cerita:\n{user_topic}"
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=full_prompt
                        )
                    else:
                        video_file = client.files.upload(file=video_path)
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=[video_file, system_instruction]
                        )

                    raw_text = response.text
                    st.session_state.current_story_context = f"=== SCENE 1 (00:00 - 00:08) ===\n" + raw_text
                    st.session_state.step = 2
                    st.rerun()

                except Exception as e:
                    st.error(f"Error: {e}")

# --- TAHAP BERIKUTNYA (SCENE 2 SAMPAI BATAS MAX_SCENES) ---
elif 2 <= st.session_state.step <= max_scenes:
    st.subheader(f"🎬 Tahap {st.session_state.step} dari {max_scenes}: Lanjutkan Scene Berikutnya")
    st.info(f"💡 **Tips Kontinuitas:** Generate video Scene {st.session_state.step - 1} di AI generator-mu, lalu **Screenshot detik terakhirnya** dan upload di bawah agar karakter & posisinya nyambung!")

    with st.expander("📂 Lihat Riwayat Script & Prompt Sebelumnya"):
        st.write(st.session_state.current_story_context)

    last_frame = st.file_uploader(
        f"📸 Upload Screenshot Detik Terakhir dari Scene {st.session_state.step - 1}:", 
        type=["png", "jpg", "jpeg"]
    )
    
    next_action_note = st.text_input("Mau diarahkan ke kejadian apa di scene ini selanjutnya? (Opsional):", placeholder="Contoh: Kucing kaget lalu lari ke arah dapur...")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"🚀 Racik Prompt Scene {st.session_state.step}"):
            if not client:
                st.error("API Key belum diset.")
            else:
                start_time = (st.session_state.step - 1) * 8
                end_time = st.session_state.step * 8
                with st.spinner(f"AI menganalisis gambar akhir & meracik Scene {st.session_state.step} ({start_time}s - {end_time}s)..."):
                    try:
                        continuity_instruction = f"""
                        Kamu adalah Sutradara AI profesional. Ini adalah kelanjutan Scene {st.session_state.step} dari total {max_scenes} scene.
                        GAYA VISUAL WAJIB: {style_pilihan}.
                        
                        ATURAN UTAMA KONTINUITAS:
                        1. Berdasarkan GAMBAR SCREENSHOT TERAKHIR yang di-upload user, pertahankan karakter, baju, gaya visual (Ghibli 2D hand-drawn), dan latar tempat yang sama persis (tidak boleh ada perubahan gaya / style drift!).
                        2. Lanjutkan alur cerita ke scene berdurasi tepat 8 detik berikutnya secara mulus tanpa efek teleportasi.
                        
                        Catatan tambahan dari user untuk scene ini: {next_action_note}

                        FORMAT OUTPUT MESTI TERPISAH:
                        [SCENE_DESC]
                        (Prompt Scene {st.session_state.step} berdurasi 8 detik yang konsisten dengan gambar referensi)
                        [/SCENE_DESC]
                        [VO_SCRIPT]
                        (Naskah VO Scene {st.session_state.step} durasi 8 detik)
                        [/VO_SCRIPT]
                        """

                        if last_frame is not None:
                            frame_path = "temp_frame.jpg"
                            with open(frame_path, "wb") as f:
                                f.write(last_frame.read())
                            uploaded_img = client.files.upload(file=frame_path)
                            response = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=[uploaded_img, continuity_instruction]
                            )
                        else:
                            response = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=continuity_instruction
                            )

                        raw_text = response.text
                        st.session_state.current_story_context += f"\n\n=== SCENE {st.session_state.step} ({start_time:02d}:00 - {end_time:02d}:00) ===\n" + raw_text
                        st.session_state.step += 1
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error: {e}")

    with col2:
        if st.button("🔄 Reset / Mulai dari Awal"):
            st.session_state.step = 1
            st.session_state.scene_history = []
            st.session_state.current_story_context = ""
            st.rerun()

    if st.session_state.current_story_context:
        st.markdown("---")
        st.subheader("📜 Riwayat Script & Prompt Keseluruhan")
        st.text_area("Salin Semua Script & Prompt:", value=st.session_state.current_story_context, height=350)

# --- JIKA SUDAH SELESAI SELURUH SCENE ---
elif st.session_state.step > max_scenes:
    st.success(f"🎉 Selamat! Semua {max_scenes} scene ({max_scenes * 8} Detik) Selesai Dirancang dengan Sempurna!")
    st.info("Semua klip video masing-masing berdurasi pas 8 detik tanpa perlu dipotong-potong lagi saat digabung di CapCut.")
    
    st.subheader("📋 Final Master Script & Prompt Package")
    st.text_area("Salin Paket Final untuk CapCut & Generator AI:", value=st.session_state.current_story_context, height=450)

    if st.button("🔄 Buat Proyek Baru / Reset"):
        st.session_state.step = 1
        st.session_state.scene_history = []
        st.session_state.current_story_context = ""
        st.rerun()
