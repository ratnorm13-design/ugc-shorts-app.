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

# DNA Si Kumis dikunci mati
SI_KUMIS_DNA = (
    "CHARACTER IP LOCK: 'Si Kumis'. "
    "A photorealistic white cat wearing stylish black sunglasses over its eyes, "
    "featuring a distinct black mustache-like fur mark directly under its pink nose. "
    "Has a small black fur patch on the top of its head between ears, pure white coat body, "
    "and maintains a cool, calm, deadpan poker-face expression. "
    "CRITICAL CONSTRAINTS: Identical white fur, black mustache mark, head patch, and sunglasses across every frame."
)

ASPECT_RATIOS = ["9:16 — TikTok / Reels / Shorts", "16:9 — YouTube Long", "1:1 — Square"]

# ==========================================
# 2. STATE MANAGEMENT (ANTI KEY-ERROR)
# ==========================================
# Mendaftarkan semua variabel agar tidak pernah KeyError saat pindah halaman
def init_state():
    defaults = {
        "page": "home", "api_key": "", "aspect_ratio": ASPECT_RATIOS[0],
        "analysis_data": {}, "scene_frames": {}, "scene_prompts": {}, 
        "current_scene": 1, "total_scenes": 0, "seo_package": {},
        "is_completed": False
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()

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
    
    config = {"temperature": 0.3} # Sedikit lebih tinggi untuk komedi absurd
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
# 3. CORE LOGIC (AI Analisis 8 Detik & Audio)
# ==========================================
def run_viral_adaptation():
    client = get_gemini_client()
    if not client: return

    file_upload = st.session_state.get("viral_video_file")
    media_payload = []
    
    if not file_upload:
        st.error("Silakan upload video referensi."); return

    try:
        file_bytes = file_upload.getvalue()
        mime_type = getattr(file_upload, "type", "video/mp4") or "video/mp4"
        media_payload.append(types.Part.from_bytes(data=file_bytes, mime_type=mime_type))
    except Exception as err:
        st.error(f"Gagal memuat video: {err}"); return
            
    sys_instruction = f"""
TUGAS: Analisis video viral ini dan buat adaptasi komedi absurd untuk AI Video Generator (seperti Flow AI).

ATURAN WAJIB (Rule of Adaptation):
1. DURASI & SCENE (8 Detik/Scene): Estimasi durasi video asli. Tambahkan ekstensi aksi komedi di akhir agar total durasi menjadi KELIPATAN 8 DETIK (misal 16s = 2 Scene, 24s = 3 Scene, dst).
2. KOMEDI ABSURD: Ekstensi/tambahan cerita tidak boleh datar. Harus melebih-lebihkan kelucuan/keanehan aksi aslinya.
3. SUBJEK UTAMA: GANTI TOTAL subjek asli menjadi "Si Kumis".
4. ANTI-COPYRIGHT: Ubah tekstur latar dan warna secara natural agar beda dari video asli.
5. AUDIO CUES: Pastikan deskripsi memuat pemicu suara (misal: benda jatuh, teriak, mesin, tabrakan) agar AI pembuat video bisa menghasilkan Native Audio.

OUTPUT WAJIB JSON dengan struktur berikut:
{{
  "original_duration_est": 10,
  "extended_total_duration": 16,
  "total_scenes": 2,
  "adaptation_strategy": "Penjelasan singkat (Bahasa Indonesia) modifikasi latar & komedi.",
  "scenes": [
    {{
      "scene_num": 1,
      "original_breakdown": "Deskripsi (Bahasa Indonesia) apa yang terjadi di video asli pada bagian ini.",
      "modified_action_en": "English description of the modified absurd action for Si Kumis, including sound triggers (e.g., *loud thud sound*, *engine revving*).",
      "environment_en": "English description of the modified anti-copyright environment."
    }}
  ]
}}
"""
    with st.spinner("AI sedang membedah video, menghitung durasi 8-detik, & meracik komedi absurd..."):
        try:
            res = call_ai(client, sys_instruction, media_payload, is_json=True)
            data = parse_ai_json(res)
            
            # Reset state untuk produksi baru
            st.session_state.update({
                "analysis_data": data,
                "total_scenes": int(data.get("total_scenes", 1)),
                "current_scene": 1,
                "scene_prompts": {}, "scene_frames": {}, "seo_package": {},
                "is_completed": False
            })
            navigate_to("analysis")
        except Exception as err:
            st.error(f"Gagal memproses video: {err}")

def generate_scene_prompt(scene_num: int):
    data = st.session_state.analysis_data
    scenes = data.get("scenes", [])
    
    # Cari data scene yang sesuai
    scene_data = next((s for s in scenes if s["scene_num"] == scene_num), None)
    if not scene_data: return False

    action_en = scene_data.get("modified_action_en", "")
    env_en = scene_data.get("environment_en", "")

    if scene_num == 1:
        mode = "MODE: Text-to-Video (T2V). Establish the environment clearly."
        continuity = f"[P3 - ENVIRONMENT]: {env_en}. Highly detailed ambient lighting."
    else:
        # Pengecekan gembok I2V
        prev = scene_num - 1
        if prev not in st.session_state.scene_frames: return "LOCKED"
        
        mode = "MODE: Image-to-Video (I2V). Use provided image as starting frame."
        continuity = f"[P1 - CONTINUITY STRICT]: Match the provided image EXACTLY. Do not teleport. [P3 - ENVIRONMENT]: {env_en}."

    prompt = f"""
{mode}
[P0 - CHARACTER DNA LOCK]: {SI_KUMIS_DNA}.
[P1 - ACTION & AUDIO]: {action_en}. Ensure action causes natural sound effects.
[P2 - MICRO BEHAVIOR]: Subtle breathing, realistic fur movement, deadpan poker-face amidst the absurdity.
{continuity}
[P4 - CAMERA & STYLE]: Dynamic natural physics, UGC style, {st.session_state.aspect_ratio}.
"""
    # Langsung simpan hasil rakitan, tidak perlu call AI lagi karena teks sudah Inggris dari fase 1
    st.session_state.scene_prompts[scene_num] = prompt.strip()
    return True

def build_viral_seo():
    client = get_gemini_client()
    data = st.session_state.analysis_data
    
    prompt = f"""
Buatkan Paket SEO Video Pendek komedi viral berdasarkan cerita "Si Kumis" berikut:
{json.dumps(data.get('scenes', []))}

OUTPUT JSON:
{{
  "title": "Judul clickbait absurd (YouTube Shorts)",
  "caption": "Caption interaktif TikTok + Hashtags (#SiKumis #KucingAbsurd dll)",
  "description": "Deskripsi singkat 1-2 kalimat ramah SEO",
  "tags": "tag1, tag2, tag3, tag4, tag5..."
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
    st.caption("Ubah Video Viral jadi Konten 'Si Kumis' — Auto 8s/Scene & Audio Cues")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Video Referensi")
        st.file_uploader("Upload Video (mp4/mov)", type=["mp4","mov","webm"], key="viral_video_file")
    with col2:
        st.subheader("2. Setting Output")
        st.selectbox("Rasio Video", ASPECT_RATIOS, key="aspect_ratio")
        st.info("💡 **AI Flow:** Video akan dihitung durasinya, digenapkan ke kelipatan 8 detik, lalu dipecah menjadi beberapa Scene dengan tambahan aksi komedi absurd di akhir.")

    st.button("🚀 EKSTRAK & BEDAH VIDEO", type="primary", use_container_width=True, on_click=run_viral_adaptation)

def view_analysis():
    data = st.session_state.analysis_data
    st.title("📋 Peta Storyboard & Adaptasi")
    
    col_info1, col_info2 = st.columns(2)
    col_info1.metric("Estimasi Durasi Asli", f"{data.get('original_duration_est', 0)} Detik")
    col_info2.metric("Durasi Modifikasi (Kelipatan 8)", f"{data.get('extended_total_duration', 0)} Detik ({st.session_state.total_scenes} Scene)")
    
    st.success(f"🛡️ **Strategi Adaptasi:** {data.get('adaptation_strategy', '')}")
    st.markdown("---")
    
    # Layout Komparasi Atas vs Bawah per Scene
    for scene in data.get("scenes", []):
        s_num = scene['scene_num']
        st.markdown(f"### 🎬 Scene {s_num}")
        
        # ATAS: Bedah Asli
        st.info(f"**🔍 Video Asli (Referensi):**\n{scene.get('original_breakdown', '')}")
        # BAWAH: Modifikasi AI
        st.warning(f"**🕶️ Modifikasi Si Kumis (Absurd & Audio Cues):**\n{scene.get('modified_action_en', '')}")
        st.markdown("---")
    
    col1, col2 = st.columns([1,3])
    with col1:
        if st.button("← Batal"): navigate_to("home")
    with col2:
        if st.button("✅ KUNCI SCENE & MASUK STUDIO", type="primary", use_container_width=True):
            navigate_to("scenes")

def view_scenes():
    curr = st.session_state.current_scene
    total = st.session_state.total_scenes
    if total == 0: return navigate_to("home")

    st.title(f"🎥 Meja Produksi — Scene {curr} / {total}")
    
    # Validasi Gembok Kontinuitas (Scene 2+)
    if curr > 1 and (curr - 1) not in st.session_state.scene_frames:
        st.error(f"🛑 **CONTINUITY LOCKED:** Wajib upload Last Frame dari Scene {curr-1} agar AI Video (Flow AI) tidak loncat/patah.")
        if st.button("← Kembali ke Scene Sebelumnya"):
            st.session_state.current_scene -= 1; st.rerun()
        return

    # Generate Prompt Otomatis di Backend
    if curr not in st.session_state.scene_prompts:
        generate_scene_prompt(curr)

    if curr in st.session_state.scene_prompts:
        st.info("🔥 Text-to-Video. Copy ke AI tanpa gambar." if curr == 1 else "🖼️ Image-to-Video. Wajib pakai frame terakhir scene sebelumnya.")
        st.code(st.session_state.scene_prompts[curr], language="markdown")
        
        st.markdown("---")
        # Wajib Upload Bukti Frame (Agar Continuity Terjaga)
        if curr < total:
            st.subheader(f"🖼️ Upload Last Frame Scene {curr}")
            st.caption("Setelah render selesai di Flow AI, screenshot frame paling akhir dan upload ke sini untuk membuka kunci Scene berikutnya.")
            
            f_up = st.file_uploader("Upload Gambar", type=["png","jpg"], key=f"fup_{curr}")
            if f_up:
                st.session_state.scene_frames[curr] = {"bytes": f_up.getvalue(), "mime": getattr(f_up, "type", "image/jpeg") or "image/jpeg"}
                st.image(f_up, width=200, caption="✔️ Kunci Terbuka!")
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
                    
        # Logika Khusus Scene Terakhir & SEO Trigger
        if curr == total:
            st.markdown("---")
            if not st.session_state.get("is_completed", False):
                st.info("💡 Render Scene terakhir ini. Jika video full sudah selesai, konfirmasi untuk memunculkan Paket SEO.")
                if st.button("✅ Ya, Video Selesai Dibuat", type="primary", use_container_width=True):
                    st.session_state.is_completed = True
                    st.rerun()
            else:
                st.success("🎉 Produksi Selesai! Buka Paket SEO di bawah.")
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
    if st.button("🏠 Mulai Baru", use_container_width=True):
        st.session_state.clear()
        init_state()
        st.rerun()
    if st.session_state.total_scenes > 0:
        if st.button("📋 Peta Storyboard", use_container_width=True): navigate_to("analysis")
        if st.button("🎬 Lanjut Produksi", use_container_width=True): navigate_to("scenes")

if st.session_state.page == "home": view_home()
elif st.session_state.page == "analysis": view_analysis()
elif st.session_state.page == "scenes": view_scenes()
