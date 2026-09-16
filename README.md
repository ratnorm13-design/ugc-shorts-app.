# 🎬 UGC Remix Studio — GTA Parkour & 3D Challenge Engine

Aplikasi web berbasis Streamlit untuk mengurai video referensi (Shorts/Reels/TikTok) dan meremix-nya secara otomatis menjadi rangkaian prompt AI Video (Veo, Kling, Runway, Luma) yang unik tanpa melanggar hak cipta.

---

## 🚀 Fitur Utama

* **Video Vision Analysis**: Mengintegrasikan SDK `google-genai` untuk membedah karakter, rantai sebab-akibat, dan lintasan dari video referensi.
* **Creative Mutation Engine**: Mengubah otomatis kombinasi karakter (Runner vs Boss) dan tipe rintangan agar hasil generasi AI berbeda dari referensi asal (de-duplication).
* **Sequential Prompt Generator**: Memecah video menjadi alur adegan 8 detik (Hook ➔ Process ➔ Climax/Payoff) lengkap dengan format prompt bahasa Inggris berspesifikasi `9:16`.
* **Last Frame Continuity Bridge**: Menyimpan frame terakhir dari adegan sebelumnya untuk menjaga konsistensi visual antar adegan.
* **SEO & Metadata Generator**: Menghasilkan judul, deskripsi, dan hashtag viral otomatis untuk YouTube Shorts & TikTok.

---

## 🛠️ Cara Instalasi & Jalankan Lokal

1. **Clone repository ini / unduh project:**
   ```bash
   git clone [https://github.com/ratnorm13-design/ugc-shorts-app.git](https://github.com/ratnorm13-design/ugc-shorts-app.git)
   cd ugc-shorts-app
