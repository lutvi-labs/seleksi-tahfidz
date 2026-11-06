# Changelog

Semua perubahan penting pada proyek ini akan didokumentasikan dalam file ini.

## [1.0.0] - 2024-11-06 (Rilis Perdana)
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