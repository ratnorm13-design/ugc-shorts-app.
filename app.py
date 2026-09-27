import json
import re
import time
import os
import streamlit as st
from google import genai
from google.genai import types

# ==========================================
# 1. KONFIGURASI HALAMAN & GLOBAL VARIABEL
# ==========================================
st.set_page_config(
    page_title="Si Kumis IP Studio",
    page_icon="🕶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

MODEL_NAME = "gemini-3.6-flash"

# DNA Si Kumis dikunci mati untuk disisipkan ke semua prompt (Anti-Shapeshifting)
SI_KUMIS_DNA = (
    "CHARACTER IP LOCK: 'Si Kumis'. "
    "A photorealistic white cat wearing stylish black sunglasses over its eyes, "
    "featuring a distinct black mustache-like fur mark directly under its pink nose. "
    "Has a small black fur patch on the top of its head between ears, pure white coat body, "
    "and maintains a cool, calm, deadpan poker-face expression. "
    "CRITICAL CONSTRAINTS: Must maintain identical white fur, black mustache mark, head patch, "
    "and black sunglasses across every single video frame without altering facial structure."
)

ASPECT_RATIOS = ["9:16 — TikTok / Reels / Shorts", "16:9 — YouTube Long", "1:1 — Square"]

# ==========================================
# 2. STATE MANAGEMENT & UTILITIES
# ==========================================
if "page" not in st.session_state:
    st.session_state.update({
        "page": "home", "api_key": "", "analysis_data": {}, 
        "storyboard_text": "", "scene_prompts": {}, "scene_frames": {}, 
        "current_scene": 1, "total_scenes": 0, "seo_package": {},
        "aspect_ratio": ASPECT_RATIOS[0], "is_completed": False
    })

def navigate_to(page_name: str):
    st.session_state.page = page_name
    st.rerun()

def get_gemini_client():
    raw_key = (os.getenv("GEMINI_API_KEY") or st.session_state.get("api_key", "")).strip("`\"' \n\r\t")
    if not raw_key:
        st.error("Masukkan Gemini API Key di Sidebar terlebih dahulu.")
        return None
    try:
        return genai.Client(api_key=raw_key)
    except Exception as err:
        st.error(f"Koneksi Gemini gagal: {err}")
        return None

def parse_ai_json(text_response: str):
    clean_text = re.sub(r"^```(?:json)?\s*", "", text_response.strip(), flags=re.I)
    clean_text = re.sub(r"\s*```$", "", clean_text)
    try:
        return json.loads(clean_text)
    except Exception:
        starts = [p for p in (clean_text.find("{"), clean_text.find("[")) if p >= 0]
        if starts:
            start_pos = min(starts)
            for end_pos in range(len(clean_text), start_pos, -1):
                try:
                    return json.loads(clean_text[start_pos:end_pos].strip())
                except:
                    continue
        raise ValueError("Gagal membaca struktur JSON dari AI.")

def call_ai(client, prompt: str, media_parts=None, is_json=False):
    contents = media_parts if media_parts else []
    contents.append(types.Part.from_text(text=prompt))
    
    config = {"temperature": 0.25} 
    if is_json: config["response_mime_type"] = "application/json"

    for _ in range(3):
        try:
            res = client.models.generate_content(
                model=MODEL_NAME,
                contents=[types.Content(role="user", parts=contents)],
                config=types.GenerateContentConfig(**config)
            )
            return res.text
        except Exception:
            time.sleep(2)
    raise RuntimeError("AI Gagal merespons setelah 3 kali percobaan.")

# ==========================================
# 3. CORE LOGIC (Analisis & Ekstraksi AI)
# ==========================================
def run_viral_adaptation():
    client = get_gemini_client()
    if not client: return

    file_upload = st.session_state.get("viral_video_file")
    text_scenario = st.session_state.get("manual_scenario", "")
    
    media_payload = []
    
    if file_upload:
        try:
            file_bytes = file_upload.getvalue()
            mime_type = getattr(file_upload, "type", "video/mp4") or "video/mp4"
            media_payload.append(types.Part.from_bytes(data=file_bytes, mime_type=mime_type))
        except Exception as err:
            st.error(f"Gagal memuat video: {err}"); return
            
        sys_instruction = f"""
TUGAS: Ekstrak aksi video viral ini & Adaptasi untuk menghindari Plagiasi/Copyright.
ATURAN WAJIB (Rule of Adaptation):
1. AKSI INTI: Pertahankan aksi fisik utama, tempo, dan angle kamera (misal kaget, jatuh, berlari).
2. SUBJEK UTAMA: GANTI TOTAL subjek asli menjadi "Si Kumis" ({SI_KUMIS_DNA}).
3. POLESAN VISUAL (Anti-Copyright): 
   - Ubah tipis tekstur latar (misal: dinding bata kusam jadi dinding bata estetik).
   - Geser tone warna/lighting (misal: siang biasa jadi golden hour/cinematic).
   - Modifikasi desain objek pendukung (misal: kaleng minuman diubah merek dan warnanya).
"""
    elif text_scenario.strip():
        sys_instruction = f"""
TUGAS: Buat storyboard komedi UGC berdasarkan skenario ini: "{text_scenario}".
Karakter Utama WAJIB "Si Kumis" ({SI_KUMIS_DNA}). Buat detail latar dan lighting yang sinematik/menarik.
"""
    else:
        st.error("Masukkan Video atau Teks Skenario."); return

    prompt = f"""
{sys_instruction}

Bagi menjadi beberapa scene (1 scene = ~5 detik) secara berurutan dan natural.
OUTPUT WAJIB JSON:
{{
  "adaptation_strategy": "Penjelasan singkat bagaimana visual/objek dipoles agar berbeda dari aslinya tanpa hilang vibe viralnya",
  "total_scenes": [JUMLAH_SCENE_INTEGER],
  "storyboard": "Scene 1: [Deskripsi mendetail aksi & latar hasil modifikasi]\\nScene 2: [Deskripsi kelanjutan aksi yang mulus]..."
}}
"""
    with st.spinner("AI sedang membedah video & memodifikasi elemen visual (Anti-Plagiasi)..."):
        try:
            res = call_ai(client, prompt, media_payload, is_json=True)
            data = parse_ai_json(res)
            
            st.session_state.update({
                "analysis_data": data,
                "total_scenes": int(data.get("total_scenes", 4)),
                "storyboard_text": data.get("storyboard", ""),
                "current_scene": 1,
                "scene_prompts": {}, "scene_frames": {}, "seo_package": {},
                "is_completed": False
            })
            navigate_to("analysis")
        except Exception as err:
            st.error(f"Gagal proses adaptasi: {err}")

def generate_scene_prompt(scene_num: int):
    client = get_gemini_client()
    if not client: return False

    lines = st.session_state.storyboard_text.split("\n")
    action_desc = next((L for L in lines if f"scene {scene_num}" in L.lower()), f"Action scene {scene_num}")

    media_parts = []
    if scene_num == 1:
        mode_instruction = "MODE: Text-to-Video (T2V). Establish the modified environment and character clearly."
        continuity = "[P3 - ENVIRONMENT]: Highly detailed, natural ambient lighting."
    else:
        prev = scene_num - 1
        if prev not in st.session_state.scene_frames: return "LOCKED"
        
        f_data = st.session_state.scene_frames[prev]
        media_parts.append(types.Part.from_bytes(data=f_data["bytes"], mime_type=f_data["mime"]))
        
        mode_instruction = "MODE: Image-to-Video (I2V). Use provided image as starting frame."
        continuity = "[P1 - CONTINUITY STRICT]: Match the provided image EXACTLY. Continue the movement naturally without sudden teleportation, jumping cuts, or background shifting. Maintain physical proportions."

    prompt = f"""
Write ONE single-paragraph AI Video Prompt in ENGLISH for video generators.
{mode_instruction}

STRUCTURE (Combine into ONE smooth paragraph):
[P0 - CHARACTER DNA LOCK]: {SI_KUMIS_DNA}.
[P1 - ACTION]: {action_desc}. {continuity}
[P2 - MICRO BEHAVIOR]: Subtle breathing, realistic fur movement, deadpan poker-face.
[P4 - CAMERA & STYLE]: Natural physics, UGC TikTok style, {st.session_state.aspect_ratio}.

OUTPUT ONLY THE FINAL PROMPT TEXT. NO PREAMBLE.
"""
    with st.spinner(f"Merakit Kode Prompt Scene {scene_num}..."):
        try:
            res = call_ai(client, prompt, media_parts)
            st.session_state.scene_prompts[scene_num] = res.strip()
            return True
        except Exception:
            return False

def build_viral_seo():
    client = get_gemini_client()
    prompt = f"""
Buatkan Paket SEO Video Pendek viral berdasarkan aksi "Si Kumis" berikut:
{st.session_state.storyboard_text}

OUTPUT JSON:
{{
  "title": "Judul clickbait (YouTube Shorts)",
  "caption": "Caption interaktif TikTok + Hashtags (#SiKumis #CatPOV dll)",
  "description": "Deskripsi singkat 1-2 kalimat ramah SEO",
  "tags": "tag1, tag2, tag3..."
}}
"""
    with st.spinner("Meracik Algoritma SEO..."):
        try:
            res = call_ai(client, prompt, is_json=True)
            st.session_state.seo_package = parse_ai_json(res)
            return True
        except:
            st.error("Gagal buat SEO")
            return False

# ==========================================
# 4. VIEWS (UI Render)
# ==========================================
def view_home():
    st.title("🕶️ Si Kumis IP Studio")
    st.caption("Ubah Video Viral jadi Konten 'Si Kumis' Tervalidasi Anti-Plagiasi & Konsisten")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Sumber Ide (Pilih Salah Satu)")
        st.file_uploader("Upload Video Referensi (mp4/mov)", type=["mp4","mov","webm"], key="viral_video_file")
        st.markdown("**ATAU**")
        st.text_area("Ketik Skenario Manual", key="manual_scenario", placeholder="Contoh: Kucing lari kaget lihat timun...")
    with col2:
        st.subheader("2. Setting Output")
        st.selectbox("Rasio Video", ASPECT_RATIOS, key="aspect_ratio")
        st.info("💡 **Catatan Sistem:** Latar & gaya kamera akan dideteksi dari video asli, lalu **dipoles otomatis oleh AI** agar warna, tekstur, dan properti berbeda dari aslinya guna menghindari isu hak cipta.")

    st.button("🚀 EKSTRAK & ADAPTASI", type="primary", use_container_width=True, on_click=run_viral_adaptation)

def view_analysis():
    st.title("📋 Peta Skenario (Adaptasi)")
    if "adaptation_strategy" in st.session_state.analysis_data:
        st.success(f"🛡️ **Strategi Modifikasi Visual:** {st.session_state.analysis_data['adaptation_strategy']}")
    
    st.caption(f"Total: {st.session_state.total_scenes} Scene. Edit teks di bawah jika ingin mengubah adegan.")
    edited = st.text_area("Skenario Final:", value=st.session_state.storyboard_text, height=250)
    
    col1, col2 = st.columns([1,3])
    with col1:
        if st.button("← Batal"): navigate_to("home")
    with col2:
        if st.button("✅ KUNCI SKENARIO & MASUK STUDIO", type="primary", use_container_width=True):
            st.session_state.storyboard_text = edited
            navigate_to("scenes")

def view_scenes():
    curr = st.session_state.current_scene
    total = st.session_state.total_scenes
    if total == 0: return navigate_to("home")

    st.title(f"🎬 Meja Produksi — Scene {curr} / {total}")
    
    # Validasi Gembok Kontinuitas (Scene 2+)
    if curr > 1 and (curr - 1) not in st.session_state.scene_frames:
        st.error(f"🛑 **CONTINUITY LOCKED:** Anda belum mengunggah Last Frame dari Scene {curr-1}. Sistem tidak mengizinkan loncatan scene agar video tidak patah.")
        if st.button("← Kembali ke Scene Sebelumnya"):
            st.session_state.current_scene -= 1; st.rerun()
        return

    # Generate Prompt Otomatis
    if curr not in st.session_state.scene_prompts:
        status = generate_scene_prompt(curr)
        if status == True: st.rerun()
        else: st.error("Gagal menyusun prompt. Coba muat ulang.")

    if curr in st.session_state.scene_prompts:
        st.info("🔥 Murni Text-to-Video. Copy ke AI Generator tanpa gambar." if curr == 1 else "🖼️ Image-to-Video. Pakai frame dari scene sebelumnya.")
        st.code(st.session_state.scene_prompts[curr], language="markdown")
        
        st.markdown("---")
        # Wajib Upload Bukti Frame (Agar Continuity Terjaga)
        if curr < total:
            st.subheader(f"🖼️ Wajib Upload Last Frame (Akhir Scene {curr})")
            st.caption("Screenshot detik terakhir dari hasil render Anda. Ini wajib diupload untuk referensi Scene berikutnya agar gerakan Si Kumis tidak loncat.")
            
            f_up = st.file_uploader(f"Upload Gambar Last Frame", type=["png","jpg"], key=f"fup_{curr}")
            if f_up:
                st.session_state.scene_frames[curr] = {"bytes": f_up.getvalue(), "mime": getattr(f_up, "type", "image/jpeg") or "image/jpeg"}
                st.image(f_up, width=200, caption="✔️ Terkunci!")
            elif curr in st.session_state.scene_frames:
                st.success("✔️ Frame tersimpan.")

        # Navigasi Antar Scene
        col1, col2 = st.columns(2)
        with col1:
            if curr > 1 and st.button("← Scene Sebelumnya"):
                st.session_state.current_scene -= 1; st.rerun()
        with col2:
            if curr < total:
                # Kunci tombol next jika belum upload
                if st.button("Scene Berikutnya →", type="primary", disabled=(curr not in st.session_state.scene_frames)):
                    st.session_state.current_scene += 1; st.rerun()
                    
        # Logika Khusus Scene Terakhir & SEO
        if curr == total:
            st.markdown("---")
            if not st.session_state.get("is_completed", False):
                st.info("💡 Render Scene terakhir ini di AI Generator. Jika sudah selesai dan merakitnya jadi 1 video utuh, konfirmasi di bawah ini.")
                if st.button("✅ Ya, Video Selesai Dibuat", type="primary", use_container_width=True):
                    st.session_state.is_completed = True
                    st.rerun()
            else:
                st.success("🎉 Luar biasa! Produksi seluruh Scene selesai.")
                if st.button("🚀 GENERATE PAKET SEO VIRAL", type="primary", use_container_width=True):
                    if build_viral_seo(): st.rerun()

                if st.session_state.seo_package:
                    s = st.session_state.seo_package
                    st.text_input("📌 Judul Shorts:", value=s.get("title",""))
                    st.text_area("📱 Caption TikTok:", value=s.get("caption",""), height=80)
                    st.text_area("📝 Deskripsi Video:", value=s.get("description",""), height=80)
                    st.text_area("🏷️ Tags:", value=s.get("tags",""))

# ==========================================
# 5. SIDEBAR & ROUTING
# ==========================================
with st.sidebar:
    st.title("🕶️ Si Kumis Studio")
    st.text_input("Gemini API Key", key="api_key", type="password")
    st.divider()
    if st.button("🏠 Mulai Baru", use_container_width=True): navigate_to("home")
    if st.session_state.total_scenes > 0:
        if st.button("🎬 Lanjut Produksi", use_container_width=True): navigate_to("scenes")

if st.session_state.page == "home": view_home()
elif st.session_state.page == "analysis": view_analysis()
elif st.session_state.page == "scenes": view_scenes()
