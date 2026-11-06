# 🕌 Sistem Seleksi Terpadu Calon Santri Tahfidz 30 Juz

Sistem informasi berbasis web untuk menyeleksi calon santri tahfidz Al-Qur'an (target 30 juz dalam waktu < 3 tahun). Aplikasi ini menggabungkan tes psikometri terstandarisasi, tes daya ingat, dan analisis Artificial Intelligence (AI) untuk menghasilkan rekomendasi penerimaan santri yang akurat dan komprehensif.

## ✨ Fitur Utama

### 👦 Portal Peserta (Ramah Anak)
* **Sistem Akun:** Registrasi dan Login peserta mandiri terintegrasi database cloud (Supabase).
* **Multi-step Survey:** UI yang dibagi menjadi 7 langkah agar anak (usia 10-12 tahun) tidak merasa terbebani.
* **Instrumen Psikologi Tersamar:**
  * **DS-21 (DASS-21):** Mengukur tingkat Depresi, Kecemasan, dan Stres.
  * **GS-8 (Grit Scale):** Mengukur ketekunan dan semangat juang.
  * **CR-25 (CD-RISC):** Mengukur resiliensi dan ketahanan mental.
  * **RB-5 (Risk Behavior):** Skrining jujur pelanggaran dan risiko perilaku.
* **Tes Memori MV-10:** Tes daya ingat visual jangka pendek (10 kata) dengan *countdown timer* 15 detik.

### 👨‍💻 Dashboard Admin
* **Real-time Analytics:** Ringkasan kelolosan, visualisasi *Pie Chart* dan *Scatter Plot* ketangguhan (Plotly).
* **Laporan Individual Komprehensif:** 
  * Radar chart perbandingan skor santri vs garis batas minimum (Threshold).
  * Bar chart DASS-21 dengan batas toleransi maksimal.
  * Fitur Export Laporan ke format `.txt`.
* **Analisis AI (Google Gemini):** Generate narasi psikologis dan rekomendasi pendampingan personal secara otomatis.
* **JASP-Style Statistics:** Matriks korelasi Pearson dan statistik deskriptif menggunakan `pingouin`.
* **Fitur Simulasi & Upload:** Generate data fiktif untuk uji coba atau upload data via CSV.

## 🛠️ Tech Stack
* **Frontend/Backend:** Python, Streamlit
* **Database & Auth:** Supabase (PostgreSQL)
* **Data Science:** Pandas, NumPy, Pingouin, SciPy
* **Visualization:** Plotly Express & Graph Objects
* **Artificial Intelligence:** Google Generative AI (Gemini 3.5 Flash Lite)

## 🚀 Cara Menjalankan Secara Lokal
1. Clone repository ini.
2. Buat virtual environment: `python -m venv venv`
3. Aktivasi venv: `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Buat folder `.streamlit` dan file `secrets.toml` berisi kredensial Supabase & Gemini.
6. Jalankan aplikasi: `streamlit run app.py`

## 🔒 Lisensi & Hak Cipta

Project ini dilindungi di bawah lisensi **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**.

- ❌ **No Commercial:** Tidak boleh digunakan untuk tujuan komersial/dijual.
- ❌ **No Derivatives:** Tidak boleh diubah, dimodifikasi, atau di-remix.
- ℹ️ **Attribution:** Wajib mencantumkan nama pembuat asli Lutvi-labs.