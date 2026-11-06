# Product Requirements Document (PRD)
**Project Name:** Sistem Seleksi Santri Tahfidz 30 Juz
**Target Audience:** Calon Santri (Usia 10-12 Tahun) & Panitia/Ustaz Penguji

## 1. Latar Belakang & Tujuan
Pesantren tahfidz dengan target akselerasi (30 juz dalam < 3 tahun) membutuhkan santri dengan ketahanan mental (resiliensi), ketekunan (grit), dan kesehatan mental yang stabil. Mengandalkan tes hafalan saja tidak cukup, seringkali santri *burnout* atau stres di tengah jalan. Aplikasi ini bertujuan mendigitalkan proses skrining psikologis awal secara otomatis, menyenangkan bagi anak, dan memberikan laporan analitik mendalam bagi panitia.

## 2. Kebutuhan Pengguna (User Needs)
* **Calon Santri:** Membutuhkan platform tes yang mudah diakses, tidak menakutkan, bahasanya mudah dipahami anak SD/SMP, dan memberikan nuansa Islami yang ramah.
* **Panitia (Admin):** Membutuhkan dashboard yang merangkum siapa yang layak masuk program, apa kelemahan mental masing-masing santri, serta rekomendasi penanganan (pendampingan) dari AI dan aturan baku.

## 3. Scope Fitur (Functional Requirements)
1. **Autentikasi:** Peserta dapat mendaftar dan login (Hash SHA256). Admin memiliki kredensial khusus. Anti-double submit.
2. **Kuesioner Dinamis (Multistep):**
   * Tahap 1: Data Diri
   * Tahap 2: DS-21 (Kesehatan Mental)
   * Tahap 3: GS-8 (Ketekunan)
   * Tahap 4: CR-25 (Resiliensi)
   * Tahap 5: MV-10 (Tes Memori 15 detik)
   * Tahap 6: RB-5 (Risiko Perilaku)
   * Tahap 7: Motivasi & Submit
3. **Scoring Engine:** Mengubah jawaban mentah menjadi metrik baku (0-100) dan mengkategorikan hasil (Normal, Ringan, Sedang, Berat).
4. **Admin Dashboard:** Menampilkan statistik deskriptif, korelasi Pearson, dan profil individual interaktif (Radar Chart).
5. **AI Reporter:** Mengubah angka statistik menjadi narasi psikologis menggunakan LLM (Google Gemini).

## 4. Keamanan & Privasi
* Data disimpan di region Asia Tenggara (Supabase Singapore).
* Judul tes disamarkan dengan kode (DS-21, GS-8, dll) agar peserta tidak memanipulasi jawaban berdasarkan nama tes.
* Kredensial database dan API AI disembunyikan menggunakan Streamlit Secrets Management.