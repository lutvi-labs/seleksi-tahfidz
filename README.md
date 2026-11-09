# 🕌 Sistem Seleksi Terpadu Calon Santri Tahfidz 30 Juz

Sistem informasi berbasis web untuk asesmen calon dan santri aktif tahfidz Al-Qur'an (target 30 juz dalam waktu < 3 tahun). Sistem ini menggabungkan tes psikometri, tes daya ingat, informasi perkembangan hafalan, dan analisis Artificial Intelligence (AI) sebagai bahan pertimbangan dan rekomendasi pendampingan.

## ✨ Fitur Utama

### 👦 Portal Peserta (Ramah Anak)
* **Sistem Akun:** Registrasi dan Login peserta mandiri terintegrasi database cloud (Supabase).
* **Multi-step Survey:** Alur peserta menyediakan paket santri baru dan santri aktif.
* **Instrumen Psikologi Tersamar:**
  * **DS-21 (DASS-21):** Mengukur tingkat Depresi, Kecemasan, dan Stres.
  * **GS-8 (Grit Scale):** Mengukur ketekunan dan semangat juang.
  * **CR-25 (CD-RISC):** Mengukur resiliensi dan ketahanan mental.
  * **RB-5 (Risk Behavior):** Skrining jujur pelanggaran dan risiko perilaku.
* **Tes Memori MV-10:** Tes daya ingat visual jangka pendek (10 kata) dengan *countdown timer* 15 detik.
* **Variasi Tes Memori:** Mengingat kosakata Arab dengan menuliskan artinya saja sesuai urutan soal, urutan kata dari nukilan Surah Al-Baqarah ayat 153 (pilihan jawaban diperbesar), urutan warna pada lima benda dengan bentuk berbeda, serta pola bunyi pendek/sedang/panjang. Jawaban warna ditulis sebagai urutan dari kiri ke kanan. Hasil variasi ditampilkan terpisah sebagai data eksploratif dan belum memengaruhi skor kesiapan.
* **Asesmen Santri Aktif:** Mencatat kelas, lama mondok, progres hafalan dan murajaah, perasaan belajar, kendala, serta sumber motivasi.
* **Skor Kesiapan:** Santri baru mendapatkan indeks kesiapan 30 juz dalam skala 0-100 tanpa keputusan lolos/tidak lolos. Radar menampilkan garis putus-putus referensi 70/100, bukan ambang kelulusan. Indeks ini bukan probabilitas keberhasilan dan belum divalidasi terhadap hasil alumni.

### 👨‍💻 Dashboard Admin
* **Real-time Analytics:** Ringkasan peserta, skor kesiapan santri baru, dan progres santri aktif.
* **Laporan Individual Komprehensif:** 
  * Radar chart profil asesmen dan grafik skor tes.
  * Laporan DOCX yang dapat diedit, termasuk visualisasi dan rekomendasi pendampingan.
* **Analisis AI (Google Gemini):** Generate narasi psikologis dan rekomendasi pendampingan personal secara otomatis.
* **JASP-Style Statistics:** Matriks korelasi Pearson dan statistik deskriptif menggunakan `pingouin`.
* **Fitur Simulasi & Upload:** Generate data fiktif untuk uji coba atau upload data via CSV.

### 🧭 Batasan dan Proposal Validasi
* Skor kesiapan saat ini merupakan indeks berbobot dari hasil asesmen, bukan probabilitas terkalibrasi. Indeks tidak menentukan keputusan PSB.
* Untuk mengukur kesiapan hafalan secara lebih langsung, tahap berikutnya yang disarankan adalah tes setoran terpantau dengan waktu persiapan seragam, tes recall tertunda, serta rubrik tajwid, kelancaran, dan kesalahan yang dinilai pembimbing.
* Sebelum menampilkan peluang keberhasilan dalam persen, kumpulkan data progres santri dari waktu ke waktu dan validasi model pada kohort terpisah bersama ahli pendidikan/psikometri.

## 🛠️ Tech Stack
* **Frontend/Backend:** Python, Streamlit
* **Database & Auth:** Supabase (PostgreSQL)
* **Data Science:** Pandas, NumPy, Pingouin, SciPy, Matplotlib
* **Dokumen:** python-docx (DOCX editable)
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