import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime
from fpdf import FPDF
from modules.ai_engine import analyze_individual

# =========================
# HELPER KONVERSI SKALAR
# =========================
def _to_float(val, default=0.0):
    try:
        if isinstance(val, (pd.Series, pd.DataFrame)):
            val = val.iloc[0] if len(val) > 0 else default
        if hasattr(val, 'item'):
            val = val.item()
        return float(val)
    except Exception:
        return float(default)

def _to_str(val, default=""):
    try:
        if isinstance(val, (pd.Series, pd.DataFrame)):
            val = val.iloc[0] if len(val) > 0 else default
        return str(val) if val is not None else str(default)
    except Exception:
        return str(default)


# =========================
# INTERPRETASI & REKOMENDASI
# =========================
def get_interpretasi_dass(dep, anx, str_s):
    dep, anx, str_s = _to_float(dep), _to_float(anx), _to_float(str_s)
    notes = []
    if dep >= 21:
        notes.append("Depresi Sangat Berat/Berat: Membutuhkan konseling klinis sebelum program hafalan padat.")
    elif dep >= 14:
        notes.append("Depresi Sedang: Perlu pemantauan suasana hati dan motivasi belajar.")
    else:
        notes.append("Depresi Normal/Ringan: Suasana hati stabil, siap mengikuti kegiatan harian.")

    if anx >= 15:
        notes.append("Kecemasan Sangat Berat/Berat: Rentan panik saat ujian/sima'an. Butuh teknik relaksasi.")
    elif anx >= 10:
        notes.append("Kecemasan Sedang: Perlu pembiasaan panggung dan sima'an bertahap.")
    else:
        notes.append("Kecemasan Normal/Ringan: Mampu mengelola rasa gugup dengan baik.")

    if str_s >= 26:
        notes.append("Stres Sangat Berat/Berat: Kapasitas mental terbebani. Risiko burnout tinggi.")
    elif str_s >= 19:
        notes.append("Stres Sedang: Perlu manajemen waktu dan istirahat seimbang.")
    else:
        notes.append("Stres Normal/Ringan: Ketahanan terhadap tekanan harian sangat baik.")
    return notes


def generate_rekomendasi(row):
    decision = _to_str(row.get('Keputusan', ''))
    grit = _to_float(row.get('Grit_Score', 0))
    cdrisc = _to_float(row.get('CDRISC_Score', 0))
    mem = _to_float(row.get('Memori_Score', 0))
    rb = _to_float(row.get('RB_Score', 0))

    reks = []
    if decision == 'LOLOS':
        reks.append("Direkomendasikan masuk kelas target percepatan (30 juz < 3 tahun).")
        reks.append("Saran: target harian 1-2 halaman + muroja'ah terstruktur.")
    elif decision == 'LOLOS BERSYARAT':
        reks.append("Diterima dengan masa percobaan 3 bulan / kelas reguler.")
        if grit < 3.5:
            reks.append("Fokus: pembentukan kebiasaan (habit) dan kedisiplinan.")
        if cdrisc < 65:
            reks.append("Fokus: konseling sebaya dan motivasi berkala.")
        if mem < 7:
            reks.append("Fokus: latih metode menghafal visual/auditori.")
    else:
        reks.append("Belum direkomendasikan masuk program percepatan tahfidz saat ini.")
        if rb >= 2:
            reks.append("Catatan: indikasi masalah perilaku, perlu pembinaan karakter.")
        else:
            reks.append("Catatan: kuatkan kesehatan mental sebelum mendaftar kembali.")
    return reks


# =========================
# CHART
# =========================
def plot_radar_profile(row):
    dep = _to_float(row.get('DASS_Depresi', 0))
    anx = _to_float(row.get('DASS_Anxiety', 0))
    str_s = _to_float(row.get('DASS_Stress', 0))
    grit = _to_float(row.get('Grit_Score', 0))
    cdrisc = _to_float(row.get('CDRISC_Score', 0))
    mem = _to_float(row.get('Memori_Score', 0))
    rb = _to_float(row.get('RB_Score', 0))

    dass_health = max(0.0, 100.0 - ((dep + anx + str_s) / 126.0 * 100.0))
    grit_pct = (grit / 5.0) * 100.0
    cdrisc_pct = (cdrisc / 100.0) * 100.0
    mem_pct = (mem / 10.0) * 100.0
    rb_safety = max(0.0, 100.0 - (rb * 20.0))

    categories = ['Kesehatan Mental', 'Semangat (Grit)', 'Resiliensi', 'Daya Ingat', 'Integritas']
    santri_values = [dass_health, grit_pct, cdrisc_pct, mem_pct, rb_safety]
    cutoff_values = [75, 70, 65, 70, 80]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=santri_values + [santri_values[0]],
        theta=categories + [categories[0]],
        fill='toself', fillcolor='rgba(13, 110, 253, 0.25)',
        name='Capaian Santri', line=dict(color='#0d6efd', width=2)
    ))
    fig.add_trace(go.Scatterpolar(
        r=cutoff_values + [cutoff_values[0]],
        theta=categories + [categories[0]],
        fill='none', name='Batas Minimum Lolos Target',
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


def plot_dass_bar(row):
    dep = _to_float(row.get('DASS_Depresi', 0))
    anx = _to_float(row.get('DASS_Anxiety', 0))
    str_s = _to_float(row.get('DASS_Stress', 0))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Skor DASS-21 Santri',
        x=['Depresi', 'Kecemasan', 'Stres'],
        y=[dep, anx, str_s],
        marker_color=[
            '#dc3545' if dep >= 14 else '#28a745',
            '#dc3545' if anx >= 10 else '#28a745',
            '#dc3545' if str_s >= 19 else '#28a745'
        ]
    ))
    fig.add_hline(y=13, line_dash="dash", line_color="#dc3545",
                  annotation_text="Batas Maks Depresi (13)", annotation_position="top left")
    fig.add_hline(y=9, line_dash="dot", line_color="#ffc107",
                  annotation_text="Batas Maks Kecemasan (9)", annotation_position="top right")
    fig.update_layout(
        title="Profil Gangguan Mental (Makin Rendah Makin Baik)",
        yaxis_title="Skor (0 - 42)", yaxis_range=[0, 42], showlegend=False
    )
    return fig


# =========================
# PDF GENERATOR
# =========================
class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 8, 'LAPORAN HASIL SELEKSI SANTRI TAHFIDZ', ln=True, align='C')
        self.set_font('Helvetica', '', 10)
        self.cell(0, 6, 'Sistem Seleksi Terpadu - Target 30 Juz < 3 Tahun', ln=True, align='C')
        self.ln(2)
        self.set_draw_color(13, 110, 253)
        self.set_line_width(0.6)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f'Halaman {self.page_no()} | Dicetak: {datetime.now().strftime("%d/%m/%Y %H:%M")}', align='C')


def _pdf_safe(text):
    """Buang karakter non-latin1 agar FPDF tidak error."""
    if text is None:
        return "-"
    text = str(text)
    # Ganti beberapa karakter umum
    replacements = {
        '—': '-', '–': '-', '“': '"', '”': '"', '‘': "'", '’': "'",
        '•': '-', '✅': '[OK]', '❌': '[X]', '⚠️': '[!]', '💡': '*',
        '🔴': '[!]', '🟡': '[~]', '🟢': '[OK]', '📊': '', '🤖': '',
        '💪': '', '👤': '', '📖': '', '🌟': '', '✨': '', '📌': '',
        '🧠': '', '📥': '', '🚀': '', '🕌': '', '←': '<-', '→': '->',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Encode aman
    return text.encode('latin-1', 'replace').decode('latin-1')


def build_individual_pdf(row, ai_text=None):
    nama = _to_str(row.get('nama', 'Santri'))
    username = _to_str(row.get('username', '-'))
    usia = _to_str(row.get('usia', '-'))
    jk = _to_str(row.get('jenis_kelamin', '-'))
    asal = _to_str(row.get('asal_sekolah', '-'))
    motivasi = _to_str(row.get('motivasi', '-'))
    keputusan = _to_str(row.get('Keputusan', '-'))
    confidence = _to_float(row.get('Confidence', 0))
    waktu = _to_str(row.get('waktu_submit', '-'))

    dep = _to_float(row.get('DASS_Depresi', 0))
    anx = _to_float(row.get('DASS_Anxiety', 0))
    str_s = _to_float(row.get('DASS_Stress', 0))
    grit = _to_float(row.get('Grit_Score', 0))
    cdrisc = _to_float(row.get('CDRISC_Score', 0))
    mem = _to_float(row.get('Memori_Score', 0))
    rb = _to_float(row.get('RB_Score', 0))
    grit_kat = _to_str(row.get('Grit_Kategori', '-'))
    cdrisc_kat = _to_str(row.get('CDRISC_Kategori', '-'))

    dass_notes = get_interpretasi_dass(dep, anx, str_s)
    reks = generate_rekomendasi(row)

    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font('Helvetica', '', 11)

    # --- Identitas ---
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, _pdf_safe('1. IDENTITAS PESERTA'), ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, _pdf_safe(f'Nama Lengkap    : {nama}'), ln=True)
    pdf.cell(0, 7, _pdf_safe(f'Username        : {username}'), ln=True)
    pdf.cell(0, 7, _pdf_safe(f'Usia / JK       : {usia} tahun / {jk}'), ln=True)
    pdf.cell(0, 7, _pdf_safe(f'Asal Sekolah    : {asal}'), ln=True)
    pdf.cell(0, 7, _pdf_safe(f'Waktu Submit    : {waktu}'), ln=True)
    pdf.ln(3)

    # --- Keputusan ---
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, _pdf_safe('2. HASIL KEPUTUSAN'), ln=True)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 9, _pdf_safe(f'KEPUTUSAN: {keputusan}'), ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, _pdf_safe(f'Confidence Score: {confidence:.1f} / 100'), ln=True)
    pdf.ln(3)

    # --- Skor ---
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, _pdf_safe('3. SKOR VARIABEL UTAMA'), ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, _pdf_safe(f'DASS-21  : Depresi={dep:.0f} | Kecemasan={anx:.0f} | Stres={str_s:.0f}  (skala 0-42)'), ln=True)
    pdf.cell(0, 7, _pdf_safe(f'Grit-8   : {grit:.2f} / 5.0  ({grit_kat})'), ln=True)
    pdf.cell(0, 7, _pdf_safe(f'CD-RISC  : {cdrisc:.0f} / 100  ({cdrisc_kat})'), ln=True)
    pdf.cell(0, 7, _pdf_safe(f'Memori   : {mem:.0f} / 10 kata'), ln=True)
    pdf.cell(0, 7, _pdf_safe(f'RB-5     : {rb:.0f}  (risiko perilaku)'), ln=True)
    pdf.ln(3)

    # --- Interpretasi DASS ---
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, _pdf_safe('4. INTERPRETASI KESEHATAN MENTAL (DASS-21)'), ln=True)
    pdf.set_font('Helvetica', '', 11)
    for n in dass_notes:
        pdf.multi_cell(0, 6, _pdf_safe(f'- {n}'))
    pdf.ln(2)

    # --- Rekomendasi ---
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, _pdf_safe('5. REKOMENDASI PANITIA'), ln=True)
    pdf.set_font('Helvetica', '', 11)
    for r in reks:
        pdf.multi_cell(0, 6, _pdf_safe(f'- {r}'))
    pdf.ln(2)

    # --- Motivasi ---
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, _pdf_safe('6. MOTIVASI & NIAT SANTRI'), ln=True)
    pdf.set_font('Helvetica', 'I', 11)
    pdf.multi_cell(0, 6, _pdf_safe(f'"{motivasi}"'))
    pdf.ln(3)

    # --- AI Report ---
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, _pdf_safe('7. ANALISIS AI (GOOGLE GEMINI)'), ln=True)
    pdf.set_font('Helvetica', '', 11)
    if ai_text and str(ai_text).strip():
        # Bersihkan markdown kasar
        clean_ai = str(ai_text)
        for md in ['### ', '## ', '# ', '**', '__', '* ', '- [ ]', '```']:
            clean_ai = clean_ai.replace(md, '')
        pdf.multi_cell(0, 6, _pdf_safe(clean_ai))
    else:
        pdf.multi_cell(0, 6, _pdf_safe(
            'Analisis AI belum digenerate. Silakan klik tombol '
            '"Generate Laporan AI" di dashboard sebelum mengunduh PDF lengkap.'
        ))

    pdf.ln(6)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, _pdf_safe(
        'Catatan: Laporan ini bersifat skrining awal untuk keperluan seleksi internal. '
        'Keputusan akhir tetap menjadi kewenangan panitia dan/atau psikolog berizin.'
    ))

    # Output bytes
    out = pdf.output()
    if isinstance(out, str):
        return out.encode('latin-1')
    return bytes(out)


# =========================
# TAMPILAN LAPORAN INDIVIDUAL
# =========================
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

    if not sel_nama:
        return

    p_df = df[df['nama'] == sel_nama]
    if p_df.empty:
        return
    row = p_df.iloc[0]

    confidence = _to_float(row.get('Confidence', 0.0))
    keputusan = _to_str(row.get('Keputusan', '-'))
    nama_santri = _to_str(row.get('nama', ''))
    username_santri = _to_str(row.get('username', ''))
    usia = _to_str(row.get('usia', '-'))
    jk = _to_str(row.get('jenis_kelamin', '-'))
    asal = _to_str(row.get('asal_sekolah', '-'))
    motivasi = _to_str(row.get('motivasi', '-'))
    memori_sc = _to_float(row.get('Memori_Score', 0))
    waktu_sub = _to_str(row.get('waktu_submit', '-'))

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
    with col_left:
        st.plotly_chart(plot_radar_profile(row), use_container_width=True)
    with col_right:
        st.plotly_chart(plot_dass_bar(row), use_container_width=True)

    st.markdown("### 🔍 Analisis Psikologis Bawaan")
    c_an1, c_an2 = st.columns(2)
    with c_an1:
        st.markdown("#### 1. Diagnostik Kesehatan Mental (DASS-21)")
        for n in get_interpretasi_dass(row.get('DASS_Depresi', 0), row.get('DASS_Anxiety', 0), row.get('DASS_Stress', 0)):
            st.write(f"• {n}")
    with c_an2:
        st.markdown("#### 2. Rekomendasi & Tindak Lanjut")
        for r in generate_rekomendasi(row):
            st.write(f"• {r}")

    st.markdown("#### 3. Motivasi & Niat Santri")
    st.info(f'"{motivasi}"')

    # --- AI Individual ---
    st.markdown("---")
    st.markdown("### 🤖 Laporan Analisis AI Khusus Santri (Google Gemini)")
    st.write("Klik tombol di bawah untuk membuat narasi analisis psikologis personal, lalu unduh PDF lengkap.")

    # Key session unik per santri
    ai_key = f"ai_report_{nama_santri}"
    if ai_key not in st.session_state:
        st.session_state[ai_key] = ""

    col_ai1, col_ai2 = st.columns([1, 1])
    with col_ai1:
        if st.button(f"✨ Generate Laporan AI untuk {nama_santri}", type="primary", use_container_width=True):
            with st.spinner(f"AI Gemini sedang membuat laporan khusus untuk {nama_santri}..."):
                ai_ind_report = analyze_individual(row)
                st.session_state[ai_key] = ai_ind_report

    if st.session_state.get(ai_key):
        st.markdown(
            f"<div style='background-color: white; padding: 25px; border-radius: 12px; "
            f"border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>"
            f"{st.session_state[ai_key]}</div>",
            unsafe_allow_html=True
        )

    # --- DOWNLOAD SECTION ---
    st.markdown("---")
    st.markdown("### 📥 Unduh Laporan")

    # TXT
    dep_val = _to_float(row.get('DASS_Depresi', 0))
    anx_val = _to_float(row.get('DASS_Anxiety', 0))
    str_val = _to_float(row.get('DASS_Stress', 0))
    grit_val = _to_float(row.get('Grit_Score', 0))
    cdrisc_val = _to_float(row.get('CDRISC_Score', 0))
    rb_val = _to_float(row.get('RB_Score', 0))
    grit_kat = _to_str(row.get('Grit_Kategori', ''))
    cdrisc_kat = _to_str(row.get('CDRISC_Kategori', ''))

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
- DASS-21 : Depresi={dep_val:.0f}, Anxiety={anx_val:.0f}, Stress={str_val:.0f}
- Grit-8  : {grit_val:.2f} / 5.0 ({grit_kat})
- CD-RISC : {cdrisc_val:.0f} / 100 ({cdrisc_kat})
- Memori  : {memori_sc:.0f} / 10 Kata
- RB-5    : {rb_val:.0f}

INTERPRETASI:
{chr(10).join(['- ' + n for n in get_interpretasi_dass(dep_val, anx_val, str_val)])}

REKOMENDASI:
{chr(10).join(['- ' + r for r in generate_rekomendasi(row)])}

MOTIVASI:
"{motivasi}"

ANALISIS AI:
{st.session_state.get(ai_key) or '(Belum digenerate)'}
==================================================
"""

    c_dl1, c_dl2 = st.columns(2)
    with c_dl1:
        st.download_button(
            label="📄 Download Laporan Teks (.txt)",
            data=report_text,
            file_name=f"Laporan_Seleksi_{nama_santri}.txt",
            mime="text/plain",
            use_container_width=True
        )

    with c_dl2:
        try:
            pdf_bytes = build_individual_pdf(row, ai_text=st.session_state.get(ai_key, ""))
            st.download_button(
                label="📕 Download Laporan PDF (.pdf)",
                data=pdf_bytes,
                file_name=f"Laporan_Seleksi_{nama_santri}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        except Exception as e:
            st.error(f"Gagal membuat PDF: {e}")
            st.caption("Pastikan library fpdf2 sudah terpasang di requirements.txt")