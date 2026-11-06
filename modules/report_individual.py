import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.ai_engine import analyze_individual

# --- HELPER KONVERSI SKALAR MURNI ---
def _to_float(val, default=0.0):
    try:
        if isinstance(val, (pd.Series, pd.DataFrame)):
            val = val.iloc[0] if len(val) > 0 else default
        if hasattr(val, 'item'): val = val.item()
        return float(val)
    except Exception: return float(default)

def _to_str(val, default=""):
    try:
        if isinstance(val, (pd.Series, pd.DataFrame)):
            val = val.iloc[0] if len(val) > 0 else default
        return str(val) if val is not None else str(default)
    except Exception: return str(default)

def get_interpretasi_dass(dep, anx, str_s):
    dep, anx, str_s = _to_float(dep), _to_float(anx), _to_float(str_s)
    notes = []
    if dep >= 21: notes.append("🔴 **Depresi Sangat Berat/Berat**: Membutuhkan konseling klinis sebelum mengikuti program hafalan padat.")
    elif dep >= 14: notes.append("🟡 **Depresi Sedang**: Perlu pemantauan kondisi suasana hati dan motivasi belajar.")
    else: notes.append("🟢 **Depresi Normal/Ringan**: Suasana hati stabil, siap mengikuti kegiatan harian santri.")

    if anx >= 15: notes.append("🔴 **Kecemasan Sangat Berat/Berat**: Rentan mengalami panik saat ujian/sima'an hafalan.")
    elif anx >= 10: notes.append("🟡 **Kecemasan Sedang**: Perlu pembiasaan panggung dan sima'an bertahap.")
    else: notes.append("🟢 **Kecemasan Normal/Ringan**: Mampu mengelola rasa gugup dengan baik.")

    if str_s >= 26: notes.append("🔴 **Stres Sangat Berat/Berat**: Kapasitas mental terbebani. Risiko burnout tinggi.")
    elif str_s >= 19: notes.append("🟡 **Stres Sedang**: Perlu manajemen waktu dan istirahat yang seimbang.")
    else: notes.append("🟢 **Stres Normal/Ringan**: Ketahanan terhadap tekanan harian sangat baik.")

    return "\n\n".join(notes)

# --- RADAR CHART DENGAN GARIS PUTUS-PUTUS BATAS MINIMUM ---
def plot_radar_profile(row):
    dep, anx, str_s = _to_float(row.get('DASS_Depresi', 0)), _to_float(row.get('DASS_Anxiety', 0)), _to_float(row.get('DASS_Stress', 0))
    grit, cdrisc = _to_float(row.get('Grit_Score', 0)), _to_float(row.get('CDRISC_Score', 0))
    mem, rb = _to_float(row.get('Memori_Score', 0)), _to_float(row.get('RB_Score', 0))

    # Skor Santri (0-100)
    dass_health = max(0.0, 100.0 - ((dep + anx + str_s) / 126.0 * 100.0))
    grit_pct = (grit / 5.0) * 100.0
    cdrisc_pct = (cdrisc / 100.0) * 100.0
    mem_pct = (mem / 10.0) * 100.0
    rb_safety = max(0.0, 100.0 - (rb * 20.0))

    categories = ['Kesehatan Mental', 'Semangat (Grit)', 'Resiliensi', 'Daya Ingat', 'Integritas']
    santri_values = [dass_health, grit_pct, cdrisc_pct, mem_pct, rb_safety]

    # Batas Minimum Lolos Target 30 Juz < 3 Thn
    # Kesehatan: 75%, Grit: 70% (3.5/5), Resiliensi: 65%, Daya Ingat: 70% (7/10), Integritas: 80% (RB <= 1)
    cutoff_values = [75, 70, 65, 70, 80]

    fig = go.Figure()

    # 1. Area Skor Santri
    fig.add_trace(go.Scatterpolar(
        r=santri_values + [santri_values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(13, 110, 253, 0.25)',
        name='Capaian Santri',
        line=dict(color='#0d6efd', width=2)
    ))

    # 2. Garis Merah Putus-Putus Batas Minimum Lolos
    fig.add_trace(go.Scatterpolar(
        r=cutoff_values + [cutoff_values[0]],
        theta=categories + [categories[0]],
        fill='none',
        name='Batas Minimum Lolos Target',
        line=dict(color='#dc3545', dash='dash', width=2.5)
    ))

    nama_str = _to_str(row.get('nama', 'Peserta'))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        title=f"Profil Potensi vs Batas Target: {nama_str}",
        margin=dict(t=50, b=80, l=40, r=40)
    )
    return fig

# --- BAR CHART DENGAN GARIS AMBANG BATAS RISIKO ---
def plot_dass_bar(row):
    dep, anx, str_s = _to_float(row.get('DASS_Depresi', 0)), _to_float(row.get('DASS_Anxiety', 0)), _to_float(row.get('DASS_Stress', 0))
    
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Skor DASS-21 Santri',
        x=['Depresi', 'Kecemasan', 'Stres'],
        y=[dep, anx, str_s],
        marker_color=['#dc3545' if dep >= 14 else '#28a745',
                      '#dc3545' if anx >= 10 else '#28a745',
                      '#dc3545' if str_s >= 19 else '#28a745']
    ))

    # Batas Maksimal Toleransi (Batas Ringan -> Sedang)
    fig.add_hline(y=13, line_dash="dash", line_color="#dc3545", annotation_text="Batas Maks Depresi (13)", annotation_position="top left")
    fig.add_hline(y=9, line_dash="dot", line_color="#ffc107", annotation_text="Batas Maks Kecemasan (9)", annotation_position="top right")

    fig.update_layout(
        title="Profil Gangguan Mental (Makin Rendah Makin Baik)",
        yaxis_title="Skor (0 - 42)",
        yaxis_range=[0, 42],
        showlegend=False
    )
    return fig

def generate_rekomendasi(row):
    decision = _to_str(row.get('Keputusan', ''))
    grit, cdrisc = _to_float(row.get('Grit_Score', 0)), _to_float(row.get('CDRISC_Score', 0))
    mem, rb = _to_float(row.get('Memori_Score', 0)), _to_float(row.get('RB_Score', 0))

    reks = []
    if decision == 'LOLOS':
        reks.append("✅ **Rekomendasi Utama**: Direkomendasikan masuk kelas target percepatan (30 juz < 3 tahun).")
        reks.append("💡 **Saran Pendampingan**: Diberikan target harian 1-2 halaman per hari dengan muroja'ah terstruktur.")
    elif decision == 'LOLOS BERSYARAT':
        reks.append("⚠️ **Rekomendasi Utama**: Diterima dengan masa percobaan 3 bulan / kelas reguler.")
        if grit < 3.5: reks.append("💡 **Fokus Pendampingan**: Butuh pembentukan kebiasaan (habit) dan kedisiplinan.")
        if cdrisc < 65: reks.append("💡 **Fokus Pendampingan**: Diberikan dukungan konseling sebaya dan motivasi berkala.")
        if mem < 7: reks.append("💡 **Fokus Pendampingan**: Dilatih metode menghafal visual/auditori yang sesuai.")
    else:
        reks.append("❌ **Rekomendasi Utama**: Belum direkomendasikan masuk program percepatan tahfidz saat ini.")
        if rb >= 2: reks.append("💡 **Catatan Khusus**: Terdapat indikasi masalah perilaku yang perlu pembinaan karakter.")
        else: reks.append("💡 **Catatan Khusus**: Disarankan menguatkan kesehatan mental sebelum mendaftar kembali.")

    return "\n\n".join(reks)

def show_individual_report(df):
    if df is None or df.empty:
        st.warning("Belum ada data peserta.")
        return

    df = df.loc[:, ~df.columns.duplicated()]

    st.subheader("📋 Laporan Individual Peserta")
    peserta_list = df['nama'].dropna().unique().tolist()
    if not peserta_list:
        st.warning("Data nama peserta tidak ditemukan.")
        return

    sel_nama = st.selectbox("Pilih Santri/Peserta:", peserta_list)

    if sel_nama:
        p_df = df[df['nama'] == sel_nama]
        if p_df.empty: return
        row = p_df.iloc[0]

        confidence = _to_float(row.get('Confidence', 0.0))
        keputusan = _to_str(row.get('Keputusan', '-'))
        nama_santri = _to_str(row.get('nama', ''))
        username_santri = _to_str(row.get('username', ''))
        usia, jk, asal = _to_str(row.get('usia', '-')), _to_str(row.get('jenis_kelamin', '-')), _to_str(row.get('asal_sekolah', '-'))
        motivasi = _to_str(row.get('motivasi', '-'))
        memori_sc, waktu_sub = _to_float(row.get('Memori_Score', 0)), _to_str(row.get('waktu_submit', '-'))

        color_map = {'LOLOS': '#28a745', 'LOLOS BERSYARAT': '#ffc107', 'TIDAK LOLOS': '#dc3545'}
        badge_color = color_map.get(keputusan, '#6c757d')

        st.markdown(f"""
        <div style='background-color: white; padding: 20px; border-radius: 10px; border-left: 6px solid {badge_color}; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
            <h2 style='margin:0; color: #1e293b;'>{nama_santri}</h2>
            <p style='margin: 5px 0 0 0; color: #64748b;'><strong>Asal:</strong> {asal} | <strong>Usia:</strong> {usia} Thn | <strong>JK:</strong> {jk}</p>
        </div>
        """, unsafe_allow_html=True)

        col_meta1, col_meta2, col_meta3 = st.columns(3)
        col_meta1.metric("📌 Hasil Keputusan", keputusan)
        col_meta2.metric("📊 Confidence Score", f"{confidence:.1f}/100")
        col_meta3.metric("🧠 Daya Ingat (Memori)", f"{memori_sc:.0f}/10 Kata")

        st.markdown("---")

        col_left, col_right = st.columns(2)
        with col_left: st.plotly_chart(plot_radar_profile(row), use_container_width=True)
        with col_right: st.plotly_chart(plot_dass_bar(row), use_container_width=True)

        st.markdown("### 🔍 Analisis Psikologis Bawaan")
        c_an1, c_an2 = st.columns(2)
        with c_an1:
            st.markdown("#### 1. Diagnostik Kesehatan Mental (DASS-21)")
            st.write(get_interpretasi_dass(row.get('DASS_Depresi', 0), row.get('DASS_Anxiety', 0), row.get('DASS_Stress', 0)))
        with c_an2:
            st.markdown("#### 2. Rekomendasi & Tindak Lanjut")
            st.write(generate_rekomendasi(row))

        st.markdown("#### 3. Motivasi & Niat Santri")
        st.info(f'"{motivasi}"')

        # --- FITUR AI INDIVIDUAL ---
        st.markdown("---")
        st.markdown("### 🤖 Laporan Analisis AI Khusus Santri (Google Gemini)")
        st.write("Klik tombol di bawah ini untuk membuat narasi analisis psikologis dan rencana pendampingan khusus untuk santri ini.")
        
        if st.button(f"✨ Generate Laporan AI untuk {nama_santri}", type="primary"):
            with st.spinner(f"AI Gemini sedang membuat laporan khusus untuk {nama_santri}..."):
                ai_ind_report = analyze_individual(row)
                st.markdown(f"<div style='background-color: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>{ai_ind_report}</div>", unsafe_allow_html=True)

        st.markdown("---")
        # Download Report TXT
        dep_val, anx_val, str_val = _to_float(row.get('DASS_Depresi', 0)), _to_float(row.get('DASS_Anxiety', 0)), _to_float(row.get('DASS_Stress', 0))
        grit_val, cdrisc_val, rb_val = _to_float(row.get('Grit_Score', 0)), _to_float(row.get('CDRISC_Score', 0)), _to_float(row.get('RB_Score', 0))
        grit_kat, cdrisc_kat = _to_str(row.get('Grit_Kategori', '')), _to_str(row.get('CDRISC_Kategori', ''))

        report_text = f"""==================================================
LAPORAN HASIL SELEKSI PSIKOTES TAHFIDZ SANTRI
==================================================
Nama Lengkap    : {nama_santri}
Username        : {username_santri}
Usia / JK       : {usia} Thn / {jk}
Asal Sekolah    : {asal}
Waktu Submit    : {waktu_sub}

--------------------------------------------------
HASIL KEPUTUSAN : {keputusan}
CONFIDENCE SCORE: {confidence:.1f} / 100
--------------------------------------------------

SKOR VARIABEL UTAMA:
- Kesehatan Mental (DASS-21) : Depresi={dep_val:.0f}, Anxiety={anx_val:.0f}, Stress={str_val:.0f}
- Ketekunan (Grit-8)        : {grit_val:.2f} / 5.0 ({grit_kat})
- Resiliensi (CD-RISC-25)    : {cdrisc_val:.0f} / 100 ({cdrisc_kat})
- Daya Ingat Memori (MV-10)  : {memori_sc:.0f} / 10 Kata
- Risiko Perilaku (RB-5)     : {rb_val:.0f} (Pelanggaran/Risiko)

INTERPRETASI KESEHATAN MENTAL:
{get_interpretasi_dass(dep_val, anx_val, str_val)}

REKOMENDASI PANITIA:
{generate_rekomendasi(row)}

MOTIVASI SANTRI:
"{motivasi}"
==================================================
"""
        st.download_button(
            label="📥 Download Laporan Teks (.txt)",
            data=report_text,
            file_name=f"Laporan_Seleksi_{nama_santri}.txt",
            mime="text/plain"
        )