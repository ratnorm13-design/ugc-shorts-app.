# 🕶️ Si Kumis IP Studio — Viral Cat UGC Pipeline

**Si Kumis IP Studio** adalah aplikasi pembuat blueprint video UGC (*User-Generated Content*) berbasis **Streamlit** dan **Vision AI (Google Gemini API)**. Aplikasi ini dirancang khusus untuk menganalisis video viral apa pun dan membedahnya detik demi detik, lalu mentransformasikannya menjadi video komedi berdurasi pendek dengan karakter IP konsisten: **Si Kumis** (kucing putih berkacamata hitam dengan corak kumis khas).

---

## 🌟 Fitur Utama

- 👁️ **Vision AI Video Analysis:** Menganalisis video viral yang diunggah untuk menemukan *Viral Hook* (0-3 detik pertama), tempo, dan struktur komedi secara otomatis.
- 🧬 **Brand Character DNA Locking:** Mengunci ciri fisik **Si Kumis** (kucing putih, kacamata hitam, corak kumis di bawah hidung) di setiap prompt untuk mencegah perubahan bentuk fisik (*anti-shapeshifting*).
- 🎬 **Structured P0-P5 Prompt Engineering:** Menghasilkan prompt bahasa Inggris terstruktur yang dioptimalkan untuk generator AI video terkemuka seperti **Google Veo, Kling AI, Runway, dan Luma Dream Machine**.
- 🔒 **Continuity Gatekeeper System:** Sistem pembatas scene yang mewajibkan unggah gambar *last frame* dari scene sebelumnya untuk menjaga kontinuitas latar dan gerakan dalam mode *Image-to-Video* (I2V).
- 🚀 **Viral SEO Package Generator:** Otomatisasi pembuatan Judul YouTube Shorts clickbait, Caption TikTok/Reels, Deskripsi ramah SEO, dan Tagar/Hashtag viral.

---

## 📋 Persyaratan Sistem (Prerequisites)

- **Python:** Versi `3.10` atau lebih baru.
- **Google Gemini API Key:** Memiliki akses ke model `gemini-3.6-flash`.

---

## 📦 Dependensi (`requirements.txt`)

Isi dari file `requirements.txt`:

```text
streamlit>=1.30.0
google-genai>=0.1.0
