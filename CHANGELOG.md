# Changelog

Semua perubahan penting pada proyek ini akan didokumentasikan dalam file ini.

## [Unreleased]
### Diubah
- Menambahkan garis putus-putus batas minimal referensi 70/100 pada radar dashboard dan laporan; garis ini bukan ambang kelulusan.
- Tes kosakata Arab kini meminta arti saja sesuai urutan soal; pilihan jawaban nukilan Al-Baqarah diperbesar untuk keterbacaan.
- Menghapus keputusan otomatis lolos/tidak lolos; skor kesiapan santri baru kini berupa indeks berbobot 0-100 dan bukan probabilitas keberhasilan.
- Respons RB-5 tidak mengurangi skor kesiapan dan tetap ditampilkan terpisah sebagai bahan pendampingan.
- Mengganti ekspor laporan PDF dengan laporan DOCX editable yang memuat rincian hasil tes dan grafik radar/skor.
- Memperbarui analisis AI agar berfokus pada rekomendasi pendampingan, tanpa diagnosis atau keputusan penerimaan.
### Ditambahkan
- Pilihan jenis asesmen santri baru atau santri aktif, dengan ringkasan dashboard dan laporan yang dipisahkan berdasarkan jenis santri.
- Untuk santri aktif, pencatatan kelas, lama mondok, progres hafalan dan murajaah, perasaan belajar, kendala, motivasi, dan harapan; laporan DOCX aktif menyertakan grafik progres.
- Pengujian otomatis untuk perhitungan skor dan pembuatan laporan DOCX kedua jenis santri.
- Dokumentasi batasan indeks kesiapan dan usulan validasi menggunakan data capaian hafalan longitudinal.
- Opsi memulai asesmen baru bagi akun yang sudah pernah mengirim jawaban, termasuk pilihan ulang jenis santri; asesmen sebelumnya tetap tersimpan.
- Perpindahan tahap survei kini mengarahkan tampilan kembali ke bagian paling atas agar pertanyaan di awal tahap tidak terlewat.
- Menambahkan empat variasi tes memori: menuliskan kosakata Arab beserta artinya, mengingat urutan kata dari nukilan Al-Baqarah 2:153 (jawaban benar berada di pilihan terakhir), menuliskan urutan warna lima benda berbeda bentuk dari kiri ke kanan, dan mengingat urutan bunyi; skor ditampilkan terpisah dan tidak memengaruhi indeks kesiapan sebelum divalidasi.

## [1.0.0] - 2026-11-06 (Rilis Perdana)
### Ditambahkan
- **Modul Survei Peserta**: Integrasi form Streamlit native sebagai pengganti PsyToolkit.
- **Scoring Engine Automatis**: Perhitungan skor DASS-21, Grit-8, CD-RISC-25, MV-10, dan RB-5.
- **Sistem Keputusan (Decision Rules)**: Algoritma Lolos, Lolos Bersyarat, dan Tidak Lolos berdasarkan threshold psikologi.
- **Database Cloud (Supabase)**: Registrasi, login, dan penyimpanan data JSON terpusat.
- **Dashboard Admin**: Metrik utama, Chart Plotly, dan Tabel Manajemen User.
- **Laporan Individual**: Radar chart (dengan garis putus-putus threshold target) dan DASS-21 Bar Chart.
- **Integrasi AI**: Penggunaan Google Gemini (Flash Lite series) untuk analisis psikologis angkatan dan individual.
- **UI Ramah Anak**: Penyesuaian bahasa kuesioner agar mudah dipahami anak usia 10-12 tahun dengan sapaan Islami.
- **Fitur Timer MV-10**: Countdown otomatis 15 detik untuk tes daya ingat.
