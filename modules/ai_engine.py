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
    type_col = df.get('Jenis_Santri', pd.Series('santri_baru', index=df.index))
    new_students = df[type_col == 'santri_baru']
    current_students = df[type_col == 'santri_aktif']

    # Menggunakan Memori_Score (Sesuai scoring.py)
    avg_dep = df['DASS_Depresi'].mean() if 'DASS_Depresi' in df.columns else 0
    avg_anx = df['DASS_Anxiety'].mean() if 'DASS_Anxiety' in df.columns else 0
    avg_str = df['DASS_Stress'].mean() if 'DASS_Stress' in df.columns else 0
    avg_grit = df['Grit_Score'].mean() if 'Grit_Score' in df.columns else 0
    avg_cdrisc = df['CDRISC_Score'].mean() if 'CDRISC_Score' in df.columns else 0
    avg_mem = df['Memori_Score'].mean() if 'Memori_Score' in df.columns else 0
    avg_readiness = new_students['Skor_Kesiapan_30Juz'].mean() if 'Skor_Kesiapan_30Juz' in new_students.columns and not new_students.empty else 0
    avg_juz = current_students['juz_dikuasai'].mean() if 'juz_dikuasai' in current_students.columns and not current_students.empty else 0

    prompt = f"""
    Anda adalah konsultan pendidikan Tahfidz Al-Qur'an.
    Berikut data ringkas asesmen dan perkembangan santri (target hafalan 30 juz):

    - Total Peserta: {total} orang
    - Santri Baru: {len(new_students)} orang
    - Santri Aktif: {len(current_students)} orang
    - Rata-rata Skor Kesiapan Santri Baru: {avg_readiness:.1f}/100
    - Rata-rata Hafalan Santri Aktif: {avg_juz:.1f} juz
    - Rata-rata Skor Depresi (0-42): {avg_dep:.1f}
    - Rata-rata Skor Kecemasan (0-42): {avg_anx:.1f}
    - Rata-rata Skor Stres (0-42): {avg_str:.1f}
    - Rata-rata Ketekunan/Grit (1-5): {avg_grit:.2f}
    - Rata-rata Resiliensi/CD-RISC (0-100): {avg_cdrisc:.1f}
    - Rata-rata Memori Daya Ingat (0-10): {avg_mem:.1f} kata

    Skor kesiapan adalah indeks ringkasan yang belum divalidasi sebagai probabilitas keberhasilan.
    Jangan memberikan keputusan penerimaan, diagnosis klinis, atau menyimpulkan peluang keberhasilan.
    Berikan analisis Markdown yang memisahkan santri baru dan aktif, membahas:
    1. Ringkasan deskriptif dan keterbatasan data.
    2. Kekuatan dan area yang sebaiknya mendapat dukungan (tanpa diagnosis).
    3. Rekomendasi pendampingan yang praktis dan tidak menghukum.
    """

    model = init_gemini()
    if model:
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ **API AI mengalami kendala ({e}). Menampilkan ringkasan otomatis:**\n\n" + _fallback_cohort_report(total, len(new_students), len(current_students), avg_readiness, avg_grit, avg_cdrisc, avg_mem)
    else:
        return _fallback_cohort_report(total, len(new_students), len(current_students), avg_readiness, avg_grit, avg_cdrisc, avg_mem)

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
    jenis_santri = str(_get_val('Jenis_Santri', _get_val('jenis_santri', 'santri_baru')))
    readiness_value = _get_val('Skor_Kesiapan_30Juz', 0.0)
    readiness = float(readiness_value) if jenis_santri == 'santri_baru' and pd.notna(readiness_value) else None
    readiness_text = (
        f"{readiness:.1f}/100 (indeks, bukan probabilitas)"
        if readiness is not None
        else "Tidak dihitung untuk santri aktif"
    )

    dep = float(_get_val('DASS_Depresi', 0))
    anx = float(_get_val('DASS_Anxiety', 0))
    str_s = float(_get_val('DASS_Stress', 0))
    grit = float(_get_val('Grit_Score', 0))
    cdrisc = float(_get_val('CDRISC_Score', 0))
    mem = float(_get_val('Memori_Score', 0))
    mem_arab = int(_get_val('Memori_Arab_Score', 0))
    mem_ayah = int(_get_val('Memori_Ayat_Score', 0))
    mem_color = int(_get_val('Memori_Warna_Score', 0))
    mem_sound = int(_get_val('Memori_Suara_Score', 0))
    rb = float(_get_val('RB_Score', 0))
    motivasi = str(_get_val('motivasi', '-'))
    kelas = str(_get_val('kelas_saat_ini', '-'))
    lama_mondok = str(_get_val('lama_mondok_bulan', '-'))
    juz_dikuasai = str(_get_val('juz_dikuasai', '-'))
    juz_terjaga = str(_get_val('juz_terjaga', '-'))
    juz_baru_3_bulan = str(_get_val('juz_baru_3_bulan', '-'))
    perasaan = str(_get_val('perasaan_belajar', '-'))
    kendala = str(_get_val('kendala_belajar', '-'))
    harapan = str(_get_val('harapan_belajar', '-'))

    prompt = f"""
    Anda adalah konsultan pendidikan Tahfidz Al-Qur'an yang suportif.
    Buatkan ringkasan asesmen dan rekomendasi pendampingan individual. Hindari diagnosis klinis,
    keputusan diterima/ditolak, dan klaim bahwa skor adalah probabilitas keberhasilan.

    - Nama Santri: {nama}
    - Usia / Jenis Kelamin: {usia} Tahun / {jk}
    - Asal Sekolah: {asal}
    - Jenis Santri: {jenis_santri}
    - Skor Kesiapan 30 Juz: {readiness_text}
    - Motivasi Santri: "{motivasi}"
    - Harapan Belajar: "{harapan}"
    - Kelas / Lama di Pondok (bulan): {kelas} / {lama_mondok}
    - Hafalan dikuasai / terjaga / tambahan 3 bulan terakhir: {juz_dikuasai} / {juz_terjaga} / {juz_baru_3_bulan} juz
    - Perasaan belajar: {perasaan}
    - Kendala yang dilaporkan: "{kendala}"

    Hasil Tes Psikotes:
    1. Kesehatan Mental (DASS-21 Sub-skala): Depresi={dep:.0f}, Kecemasan={anx:.0f}, Stres={str_s:.0f} (Skor 0-42)
    2. Ketekunan & Semangat Belajar (Grit-8): {grit:.2f} / 5.0
    3. Resiliensi / Ketahanan Mental (CD-RISC-25): {cdrisc:.0f} / 100
    4. Daya Ingat Memori Kata (MV-10): {mem:.0f} / 10 Kata
    5. Variasi memori eksploratif — arti kosakata Arab {mem_arab}/8,
       urutan nukilan Al-Baqarah 2:153 {mem_ayah}/1, urutan warna lima benda berbeda bentuk
       {mem_color}/5, dan urutan bunyi {mem_sound}/4. Variasi ini belum tervalidasi dan
       tidak termasuk skor kesiapan.
    6. Indikator Risiko Perilaku (RB-5): {rb:.0f}

    Formatlah balasan Anda menggunakan Markdown yang indah dengan struktur berikut:
    ### Ringkasan asesmen {nama}
    ### Kekuatan dan faktor pendukung
    ### Hal yang perlu didukung (bukan diagnosis)
    ### Rekomendasi pendampingan dan metode belajar
    ### Pesan penyemangat
    """

    model = init_gemini()
    if model:
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ **API AI tidak merespon ({e}). Menampilkan analisis bawaan sistem:**\n\n" + _fallback_individual_report(nama, jenis_santri, readiness, grit, cdrisc, mem, dep, anx, str_s)
    else:
        return _fallback_individual_report(nama, jenis_santri, readiness, grit, cdrisc, mem, dep, anx, str_s)

def _fallback_cohort_report(total, new_students, current_students, avg_readiness, avg_grit, avg_cdrisc, avg_mem):
    return f"""
    ### 📊 Ringkasan Laporan Angkatan (Format Standar)
    * **Jumlah Peserta:** {total} (santri baru: {new_students}, santri aktif: {current_students}).
    * **Rata-rata Skor Kesiapan Santri Baru:** **{avg_readiness:.1f}/100** (indeks asesmen, bukan probabilitas).
    * **Rata-rata Parameter:** Ketekunan (Grit) **{avg_grit:.2f}/5.0**, Resiliensi **{avg_cdrisc:.1f}/100**, Memori **{avg_mem:.1f}/10 kata**.

    *(Catatan: Untuk analisis narrative AI lengkap, pastikan `GEMINI_API_KEY` terisi di `.streamlit/secrets.toml`)*
    """

def _fallback_individual_report(nama, jenis_santri, readiness, grit, cdrisc, mem, dep, anx, str_s):
    readiness_text = (
        f"Skor Kesiapan Target 30 Juz adalah **{readiness:.1f}/100**. Ini indeks asesmen, bukan probabilitas keberhasilan atau keputusan penerimaan."
        if jenis_santri == "santri_baru" and readiness is not None
        else "Skor kesiapan penerimaan tidak digunakan untuk santri aktif."
    )
    return f"""
    ### 👤 Ringkasan Asesmen {nama}
    {readiness_text}

    ### 💪 Potensi & Kekuatan Utama
    * Daya ingat memori jangka pendek mampu merekam **{mem:.0f} dari 10 kata**.
    * Tingkat ketekunan (Grit) bernilai **{grit:.2f}/5.0** dan resiliensi **{cdrisc:.0f}/100**.

    ### ⚠️ Area yang dapat didukung
    * Skor sub-skala DASS-21: Depresi **{dep:.0f}**, Kecemasan **{anx:.0f}**, Stres **{str_s:.0f}**.
    * Santri memerlukan suasana belajar yang sejuk, nyaman, dan terhindar dari tekanan tinggi.

    ### 📖 Rekomendasi Pendampingan Ustadz/ Ustadzah
    * Diberikan kurikulum hafalan bertahap serta pendampingan motivasi berkala.

    *(Catatan: Masukkan `GEMINI_API_KEY` di secrets.toml untuk narasi AI interaktif)*
    """