import streamlit as st
import pandas as pd
import google.generativeai as genai

def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if api_key and api_key != "AIzaSy_masukkan_api_key_anda" and len(api_key) > 10:
        try:
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-3.5-flash-lite')
        except Exception as e:
            return None
    return None

def analyze_cohort(df):
    if df is None or df.empty:
        return "⚠️ Data peserta masih kosong."
    
    total = len(df)
    lolos = len(df[df['Keputusan'] == 'LOLOS'])
    bersyarat = len(df[df['Keputusan'] == 'LOLOS BERSYARAT'])
    tidak_lolos = len(df[df['Keputusan'] == 'TIDAK LOLOS'])

    # Menggunakan Memori_Score (Sesuai scoring.py)
    avg_dep = df['DASS_Depresi'].mean() if 'DASS_Depresi' in df.columns else 0
    avg_anx = df['DASS_Anxiety'].mean() if 'DASS_Anxiety' in df.columns else 0
    avg_str = df['DASS_Stress'].mean() if 'DASS_Stress' in df.columns else 0
    avg_grit = df['Grit_Score'].mean() if 'Grit_Score' in df.columns else 0
    avg_cdrisc = df['CDRISC_Score'].mean() if 'CDRISC_Score' in df.columns else 0
    avg_mem = df['Memori_Score'].mean() if 'Memori_Score' in df.columns else 0
    avg_conf = df['Confidence'].mean() if 'Confidence' in df.columns else 0

    prompt = f"""
    Anda adalah seorang Psikolog Klinis dan Konsultan Pendidikan Tahfidz Al-Qur'an Senior.
    Berikut adalah data statistik hasil seleksi psikotes angkatan calon santri tahfidz (target 30 juz < 3 tahun):

    - Total Peserta: {total} orang
    - Lolos Murni: {lolos} ({lolos/total*100:.1f}%)
    - Lolos Bersyarat: {bersyarat} ({bersyarat/total*100:.1f}%)
    - Tidak Lolos: {tidak_lolos} ({tidak_lolos/total*100:.1f}%)
    - Rata-rata Confidence Score: {avg_conf:.1f}/100
    - Rata-rata Skor Depresi (0-42): {avg_dep:.1f}
    - Rata-rata Skor Kecemasan (0-42): {avg_anx:.1f}
    - Rata-rata Skor Stres (0-42): {avg_str:.1f}
    - Rata-rata Ketekunan/Grit (1-5): {avg_grit:.2f}
    - Rata-rata Resiliensi/CD-RISC (0-100): {avg_cdrisc:.1f}
    - Rata-rata Memori Daya Ingat (0-10): {avg_mem:.1f} kata

    Berikan analisis komprehensif dalam format Markdown yang rapi meliputi:
    1. **Ringkasan Eksekutif Kesiapan Angkatan**
    2. **Analisis Risiko Kesehatan Mental & Ketahanan Psikologis**
    3. **Rekomendasi Kurikulum & Program Pendampingan Pengasuhan**
    4. **Strategi Mitigasi Santri Lolos Bersyarat & Tidak Lolos**
    """

    model = init_gemini()
    if model:
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ **API AI mengalami kendala ({e}). Menampilkan laporan otomatis bawaan:**\n\n" + _fallback_cohort_report(total, lolos, bersyarat, tidak_lolos, avg_conf, avg_grit, avg_cdrisc, avg_mem)
    else:
        return _fallback_cohort_report(total, lolos, bersyarat, tidak_lolos, avg_conf, avg_grit, avg_cdrisc, avg_mem)

# --- FUNGSI BARU: ANALISIS INDIVIDUAL DENGAN AI ---
def analyze_individual(row):
    def _get_val(k, def_val=0):
        val = row.get(k, def_val)
        if hasattr(val, 'item'): val = val.item()
        return val

    nama = str(_get_val('nama', 'Santri'))
    usia = str(_get_val('usia', '-'))
    jk = str(_get_val('jenis_kelamin', '-'))
    asal = str(_get_val('asal_sekolah', '-'))
    keputusan = str(_get_val('Keputusan', '-'))
    confidence = float(_get_val('Confidence', 0.0))

    dep = float(_get_val('DASS_Depresi', 0))
    anx = float(_get_val('DASS_Anxiety', 0))
    str_s = float(_get_val('DASS_Stress', 0))
    grit = float(_get_val('Grit_Score', 0))
    cdrisc = float(_get_val('CDRISC_Score', 0))
    mem = float(_get_val('Memori_Score', 0))
    rb = float(_get_val('RB_Score', 0))
    motivasi = str(_get_val('motivasi', '-'))

    prompt = f"""
    Anda adalah Psikolog Anak & Konsultan Pengasuhan Tahfidz Qur'an Senior.
    Buatkan laporan diagnostik psikologis individual yang hangat, mendalam, dan solutif untuk calon santri berikut:

    - Nama Santri: {nama}
    - Usia / Jenis Kelamin: {usia} Tahun / {jk}
    - Asal Sekolah: {asal}
    - Hasil Keputusan Seleksi: {keputusan} (Confidence Score: {confidence:.1f}/100)
    - Motivasi Santri: "{motivasi}"

    Hasil Tes Psikotes:
    1. Kesehatan Mental (DASS-21 Sub-skala): Depresi={dep:.0f}, Kecemasan={anx:.0f}, Stres={str_s:.0f} (Skor 0-42)
    2. Ketekunan & Semangat Belajar (Grit-8): {grit:.2f} / 5.0
    3. Resiliensi / Ketahanan Mental (CD-RISC-25): {cdrisc:.0f} / 100
    4. Daya Ingat Memori Kata (MV-10): {mem:.0f} / 10 Kata
    5. Indikator Risiko Perilaku (RB-5): {rb:.0f}

    Formatlah balasan Anda menggunakan Markdown yang indah dengan struktur berikut:
    ### 👤 Ringkasan Profil Psikologis {nama}
    ### 💪 Potensi & Kekuatan Utama
    ### ⚠️ Area Perhatian & Potensi Hambatan Mental
    ### 📖 Rekomendasi Metode Menghafal & Pendampingan Ustaz
    ### 🌟 Pesan Motivasi Islami Khusus untuk Santri
    """

    model = init_gemini()
    if model:
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ **API AI tidak merespon ({e}). Menampilkan analisis bawaan sistem:**\n\n" + _fallback_individual_report(nama, keputusan, confidence, grit, cdrisc, mem, dep, anx, str_s)
    else:
        return _fallback_individual_report(nama, keputusan, confidence, grit, cdrisc, mem, dep, anx, str_s)

def _fallback_cohort_report(total, lolos, bersyarat, tidak_lolos, avg_conf, avg_grit, avg_cdrisc, avg_mem):
    return f"""
    ### 📊 Ringkasan Laporan Angkatan (Format Standar)
    * **Rata-rata Kesiapan:** Confidence Score angkatan berada pada tingkat **{avg_conf:.1f}/100**.
    * **Sebaran Kelolosan:** Dari **{total}** santri, **{lolos}** ({lolos/total*100:.1f}%) Lolos Murni, **{bersyarat}** ({bersyarat/total*100:.1f}%) Lolos Bersyarat, dan **{tidak_lolos}** ({tidak_lolos/total*100:.1f}%) Tidak Lolos.
    * **Rata-rata Parameter:** Ketekunan (Grit) **{avg_grit:.2f}/5.0**, Resiliensi **{avg_cdrisc:.1f}/100**, Memori **{avg_mem:.1f}/10 kata**.

    *(Catatan: Untuk analisis narrative AI lengkap, pastikan `GEMINI_API_KEY` terisi di `.streamlit/secrets.toml`)*
    """

def _fallback_individual_report(nama, keputusan, confidence, grit, cdrisc, mem, dep, anx, str_s):
    return f"""
    ### 👤 Ringkasan Profil Psikologis {nama}
    Santri ini memperoleh hasil **{keputusan}** dengan Confidence Score sebesar **{confidence:.1f}/100**.

    ### 💪 Potensi & Kekuatan Utama
    * Daya ingat memori jangka pendek mampu merekam **{mem:.0f} dari 10 kata**.
    * Tingkat ketekunan (Grit) bernilai **{grit:.2f}/5.0** dan resiliensi **{cdrisc:.0f}/100**.

    ### ⚠️ Area Perhatian & Tantangan Mental
    * Skor sub-skala DASS-21: Depresi **{dep:.0f}**, Kecemasan **{anx:.0f}**, Stres **{str_s:.0f}**.
    * Santri memerlukan suasana belajar yang sejuk, nyaman, dan terhindar dari tekanan tinggi.

    ### 📖 Rekomendasi Pendampingan Ustaz
    * Diberikan kurikulum hafalan bertahap serta pendampingan motivasi berkala.

    *(Catatan: Masukkan `GEMINI_API_KEY` di secrets.toml untuk narasi AI interaktif)*
    """