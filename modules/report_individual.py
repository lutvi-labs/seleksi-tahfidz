import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io
import datetime

# Helper Akses Nilai Aman (Case-Insensitive & Multi-Key)
def get_val(row, *keys, default="-"):
    if not isinstance(row, dict):
        try:
            row = row.to_dict()
        except:
            return default
            
    for k in keys:
        if k in row and pd.notna(row[k]) and row[k] is not None:
            return row[k]
        # Cari pencocokan tanpa peduli kapital/kecil
        for r_k in row.keys():
            if str(r_k).lower() == str(k).lower() and pd.notna(row[r_k]) and row[r_k] is not None:
                return row[r_k]
    return default

def _to_float(val, default=0.0):
    try:
        if pd.isna(val) or val is None:
            return default
        return float(val)
    except:
        return default

def _to_str(val, default="-"):
    if pd.isna(val) or val is None:
        return default
    return str(val)

# Helper Pembersih Teks untuk PDF (Menghapus Emoji & Formatting Kasar)
def clean_text_for_pdf(text):
    if not text:
        return ""
    text = str(text)
    replacements = {
        '–': '-', '—': '-', '“': '"', '”': '"', '‘': "'", '’': "'",
        '•': '-', '…': '...', '🤖': '', '📊': '', '✅': '[v]', '❌': '[x]',
        '⚠️': '!', '💡': '*', '📌': '*', '🎯': '*', '⭐': '*', '📈': ''
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = text.replace('**', '').replace('*', '')
    return text.encode('latin-1', 'replace').decode('latin-1')

# Interpretasi DASS
def get_interpretasi_dass(dep, anx, str_val):
    def dep_cat(v):
        if v <= 9: return "Normal"
        if v <= 13: return "Ringan"
        if v <= 20: return "Sedang"
        if v <= 27: return "Berat"
        return "Sangat Berat"
        
    def anx_cat(v):
        if v <= 7: return "Normal"
        if v <= 9: return "Ringan"
        if v <= 14: return "Sedang"
        if v <= 19: return "Berat"
        return "Sangat Berat"

    def str_cat(v):
        if v <= 14: return "Normal"
        if v <= 18: return "Ringan"
        if v <= 25: return "Sedang"
        if v <= 33: return "Berat"
        return "Sangat Berat"

    return {
        'dep_cat': dep_cat(dep),
        'anx_cat': anx_cat(anx),
        'str_cat': str_cat(str_val)
    }

# Rekomendasi Pengasuh
def generate_rekomendasi(row):
    keputusan = _to_str(get_val(row, 'Keputusan_Sistem', 'keputusan_sistem', default='LOLOS BERSYARAT')).upper()
    reks = []
    
    if "TIDAK LOLOS" in keputusan:
        reks.append("• Belum direkomendasikan untuk program akselerasi tahfidz intensif saat ini.")
        reks.append("• Disarankan mengikuti konseling psikologis awal untuk mengelola gejala kecemasan/stres.")
        reks.append("• Perlu pendampingan belajar dengan ritme yang lebih bertahap.")
    elif "BERSYARAT" in keputusan:
        reks.append("• Diterima dengan catatan pemantauan berkala pada 3 bulan pertama.")
        reks.append("• Perlu musyrif/pendamping khusus untuk penguatan ketahanan mental (resiliensi).")
        reks.append("• Evaluasi daya ingat hafalan secara mingguan.")
    else:
        reks.append("• Sangat direkomendasikan untuk program akselerasi tahfidz 30 Juz.")
        reks.append("• Siap mengikuti target hafalan tinggi dengan pengawasan standar.")
        reks.append("• Dapat dijadikan pendorong semangat (peer-leader) bagi rekan seangkatan.")
        
    return "\n".join(reks)

# Plot Radar Profile
def plot_radar_profile(row):
    categories = ['Kesehatan Mental', 'Ketekunan (Grit)', 'Resiliensi', 'Daya Ingat', 'Integritas (Anti-RB)']
    
    dep = _to_float(get_val(row, 'DASS_Depresi', 'dass_depresi', default=0))
    anx = _to_float(get_val(row, 'DASS_Kecemasan', 'dass_kecemasan', default=0))
    stres = _to_float(get_val(row, 'DASS_Stres', 'dass_stres', default=0))
    dass_tot = dep + anx + stres
    health_score = max(0.0, min(100.0, 100.0 - (dass_tot / 126.0 * 100.0)))
    
    grit_score = (_to_float(get_val(row, 'GS8_Score', 'gs8_score', default=0)) / 5.0) * 100.0
    cdrisc_score = _to_float(get_val(row, 'CDRISC_Score', 'cdrisc_score', default=0))
    mem_score = (_to_float(get_val(row, 'Memori_Score', 'memori_score', default=0)) / 10.0) * 100.0
    rb_score = max(0.0, 100.0 - (_to_float(get_val(row, 'RB5_Score', 'rb5_score', default=0)) * 20.0))
    
    values = [health_score, grit_score, cdrisc_score, mem_score, rb_score]
    thresholds = [75, 70, 65, 70, 80]
    
    fig = go.Figure()
    
    # Threshold Min (Garis Putus-Putus Merah)
    fig.add_trace(go.Scatterpolar(
        r=thresholds + [thresholds[0]],
        theta=categories + [categories[0]],
        name='Batas Minimum Standard',
        line=dict(color='red', dash='dash', width=2),
        fill=None
    ))
    
    # Profile Santri
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        name='Skor Ananda',
        fill='toself',
        line=dict(color='#1b5e20', width=3),
        fillcolor='rgba(27, 94, 32, 0.25)'
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        margin=dict(l=40, r=40, t=30, b=30),
        height=380
    )
    return fig

# Plot DASS Bar
def plot_dass_bar(row):
    categories = ['Depresi', 'Kecemasan', 'Stres']
    scores = [
        _to_float(get_val(row, 'DASS_Depresi', 'dass_depresi', default=0)),
        _to_float(get_val(row, 'DASS_Kecemasan', 'dass_kecemasan', default=0)),
        _to_float(get_val(row, 'DASS_Stres', 'dass_stres', default=0))
    ]
    cutoffs = [9, 7, 14]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categories,
        y=scores,
        name='Skor Peserta',
        marker_color=['#2e7d32' if scores[i] <= cutoffs[i] else '#c62828' for i in range(3)],
        text=scores,
        textposition='auto'
    ))
    fig.update_layout(
        title="Distribusi Gejala Psikologis (DS-21)",
        yaxis=dict(title="Skor (0 - 42)", range=[0, 42]),
        height=300,
        margin=dict(l=30, r=30, t=40, b=30),
        showlegend=False
    )
    return fig

# Generasi PDF Report
class IndividualPDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(27, 94, 32)
        self.cell(0, 8, clean_text_for_pdf("SISTEM SELEKSI SANTRI TAHFIDZ AL-QUR'AN"), ln=True, align='C')
        self.set_font('Helvetica', 'I', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, clean_text_for_pdf("Laporan Hasil Asesmen Psikologi & AI Recommendation"), ln=True, align='C')
        self.set_draw_color(200, 200, 200)
        self.line(15, 25, 195, 25)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        page_str = f"Halaman {self.page_no()}/{{nb}} - Rahasia & Terbatas"
        self.cell(0, 10, clean_text_for_pdf(page_str), align='C')

def build_individual_pdf(row, ai_text=""):
    pdf = IndividualPDFReport(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    epw = 180 

    # 1. Identitas
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.set_x(15)
    pdf.cell(epw, 7, clean_text_for_pdf("I. IDENTITAS ANANDA"), ln=True)
    pdf.ln(1)
    
    nama = _to_str(get_val(row, 'Nama_Lengkap', 'nama', 'nama_lengkap'))
    nisn = _to_str(get_val(row, 'NISN', 'nisn'))
    usia = _to_str(get_val(row, 'Usia', 'usia'))
    gender = _to_str(get_val(row, 'Jenis_Kelamin', 'jenis_kelamin'))
    
    data_id = [
        [("Nama Lengkap", nama), ("NISN", nisn)],
        [("Usia / Gender", f"{usia} Tahun / {gender}"), ("Tanggal Tes", datetime.datetime.now().strftime("%d-%m-%Y"))]
    ]
    
    for line in data_id:
        pdf.set_x(15)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(30, 6, clean_text_for_pdf(line[0][0] + " :"), border=0)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(60, 6, clean_text_for_pdf(line[0][1]), border=0)
        
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(30, 6, clean_text_for_pdf(line[1][0] + " :"), border=0)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(60, 6, clean_text_for_pdf(line[1][1]), border=0, ln=True)

    pdf.ln(4)

    # 2. Status Keputusan
    keputusan = _to_str(get_val(row, 'Keputusan_Sistem', 'keputusan_sistem', default='LOLOS BERSYARAT')).upper()
    conf = _to_float(get_val(row, 'Confidence_Score', 'confidence_score', default=0))
    
    pdf.set_x(15)
    if "TIDAK LOLOS" in keputusan:
        pdf.set_fill_color(255, 235, 238)
        pdf.set_text_color(183, 28, 28)
    elif "BERSYARAT" in keputusan:
        pdf.set_fill_color(255, 248, 225)
        pdf.set_text_color(245, 127, 23)
    else:
        pdf.set_fill_color(232, 245, 233)
        pdf.set_text_color(27, 94, 32)
        
    pdf.set_font('Helvetica', 'B', 11)
    status_str = f"STATUS REKOMENDASI: {keputusan} (Indeks Kesesuaian: {conf:.1f}%)"
    pdf.cell(epw, 9, clean_text_for_pdf(status_str), border=1, ln=True, align='C', fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # 3. Hasil Skor Tes
    pdf.set_x(15)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(epw, 7, clean_text_for_pdf("II. RINGKASAN HASIL ASESMEN PSIKOMETRI"), ln=True)
    pdf.ln(1)

    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_x(15)
    pdf.cell(70, 7, clean_text_for_pdf("Dimensi Psikologis"), border=1, fill=True)
    pdf.cell(35, 7, clean_text_for_pdf("Skor Riil"), border=1, align='C', fill=True)
    pdf.cell(75, 7, clean_text_for_pdf("Kategori & Interpretasi"), border=1, align='C', fill=True, ln=True)

    pdf.set_font('Helvetica', '', 9)
    grit = _to_float(get_val(row, 'GS8_Score', 'gs8_score', default=0))
    cdrisc = _to_float(get_val(row, 'CDRISC_Score', 'cdrisc_score', default=0))
    mem = _to_float(get_val(row, 'Memori_Score', 'memori_score', default=0))
    rb = _to_float(get_val(row, 'RB5_Score', 'rb5_score', default=0))
    
    table_data = [
        ("Ketekunan Belajar (GS-8)", f"{grit:.2f} / 5.0", "Tinggi" if grit>=3.5 else ("Sedang" if grit>=2.5 else "Rendah")),
        ("Resiliensi / Ketahanan (CR-25)", f"{cdrisc:.0f} / 100", "Sangat Baik" if cdrisc>=80 else ("Cukup" if cdrisc>=65 else "Perlu Pendampingan")),
        ("Daya Ingat Kata (MV-10)", f"{mem:.0f} / 10 Kata", "Sangat Baik" if mem>=7 else ("Cukup" if mem>=4 else "Kurang")),
        ("Risiko Perilaku (RB-5)", f"{rb:.0f} Indikasi", "Aman (Tidak Ada)" if rb==0 else f"Perlu Perhatian ({int(rb)} Isu)")
    ]

    for item in table_data:
        pdf.set_x(15)
        pdf.cell(70, 6, clean_text_for_pdf(item[0]), border=1)
        pdf.cell(35, 6, clean_text_for_pdf(item[1]), border=1, align='C')
        pdf.cell(75, 6, clean_text_for_pdf(item[2]), border=1, align='C', ln=True)

    pdf.ln(4)

    # 4. Screening DASS-21
    pdf.set_x(15)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(epw, 7, clean_text_for_pdf("III. SKREENING KESEHATAN MENTAL (DS-21)"), ln=True)
    pdf.ln(1)

    dep = _to_float(get_val(row, 'DASS_Depresi', 'dass_depresi', default=0))
    anx = _to_float(get_val(row, 'DASS_Kecemasan', 'dass_kecemasan', default=0))
    stres = _to_float(get_val(row, 'DASS_Stres', 'dass_stres', default=0))
    dass_interp = get_interpretasi_dass(dep, anx, stres)

    pdf.set_font('Helvetica', '', 9)
    pdf.set_x(15)
    dass_txt = f"• Depresi: {dep:.0f} ({dass_interp['dep_cat']})   |   • Kecemasan: {anx:.0f} ({dass_interp['anx_cat']})   |   • Stres: {stres:.0f} ({dass_interp['str_cat']})"
    pdf.multi_cell(epw, 6, clean_text_for_pdf(dass_txt), border=1, align='C')
    pdf.ln(4)

    # 5. Rekomendasi Pengasuh
    pdf.set_x(15)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(epw, 7, clean_text_for_pdf("IV. CATATAN & REKOMENDASI PENGASUH"), ln=True)
    pdf.ln(1)

    pdf.set_font('Helvetica', '', 9)
    reks_text = generate_rekomendasi(row)
    for line in reks_text.split('\n'):
        pdf.set_x(15)
        pdf.multi_cell(epw, 5, clean_text_for_pdf(line))
        pdf.ln(1)

    pdf.ln(3)

    # 6. Motivasi Peserta
    motivasi = _to_str(get_val(row, 'Motivasi_Peserta', 'motivasi_peserta', 'motivasi'))
    if motivasi != '-':
        pdf.set_x(15)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(epw, 6, clean_text_for_pdf("Motivasi Ananda:"), ln=True)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_x(15)
        pdf.multi_cell(epw, 5, clean_text_for_pdf(f'"{motivasi}"'), border=0)
        pdf.ln(4)

    # 7. AI Gemini Output
    if ai_text and len(ai_text.strip()) > 10:
        pdf.set_x(15)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(27, 94, 32)
        pdf.cell(epw, 7, clean_text_for_pdf("V. ANALISIS EKSPERTIS AI (GEMINI ENGINE)"), ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

        pdf.set_font('Helvetica', '', 8.5)
        for l in ai_text.split('\n'):
            l_clean = clean_text_for_pdf(l.strip())
            if l_clean:
                pdf.set_x(15)
                pdf.multi_cell(epw, 4.5, l_clean)
                pdf.ln(0.5)

    return bytes(pdf.output())


# UI Utama Laporan Individual
def show_individual_report(df_responses):
    st.title("📋 Laporan Individual Santri")
    st.markdown("Analisis mendalam profil psikologi, ketahanan mental, serta laporan siap cetak PDF.")

    # Cek Jika DataFrame Kosong
    if df_responses is None or (isinstance(df_responses, pd.DataFrame) and df_responses.empty):
        st.warning("⚠️ Belum ada data respons peserta yang tersimpan di database Supabase.")
        st.info("💡 **Petunjuk Pengujian Cepat:**\nAnda dapat masuk ke menu **⚙️ Simulasi & Upload** di menu sidebar kiri, lalu klik **🎲 Generate 5 Data Dummy Santri** untuk membuat sampel data uji coba.")
        return

    # Cari Kolom Nama
    name_col = None
    possible_cols = ['Nama_Lengkap', 'nama', 'nama_lengkap', 'Nama', 'user_id']
    for c in possible_cols:
        if c in df_responses.columns:
            name_col = c
            break

    if not name_col:
        st.error("⚠️ Kolom nama peserta tidak ditemukan pada tabel respons database.")
        st.info("💡 Silakan isi data sampel melalui menu **⚙️ Simulasi & Upload**.")
        return

    # Ambil Daftar Nama Peserta yang Valid
    peserta_names = df_responses[name_col].dropna().astype(str).unique().tolist()

    if not peserta_names:
        st.warning("⚠️ Belum ada santri yang menyelesaikan survei.")
        st.info("👉 Minta santri mengisi survei melalui link `?page=survey`, atau buat data sampel di menu **⚙️ Simulasi & Upload**.")
        return

    # Dropdown Pilih Santri
    col_sel, _ = st.columns([2, 1])
    with col_sel:
        selected_nama = st.selectbox("🎯 Pilih Nama Ananda Santri:", peserta_names)

    # Filter Data Santri Terpilih
    selected_df = df_responses[df_responses[name_col].astype(str) == str(selected_nama)]
    if selected_df.empty:
        st.warning("Data untuk santri ini tidak ditemukan.")
        return

    row_data = selected_df.iloc[0].to_dict()

    st.markdown("---")

    # Layout Ringkasan Identitas & Hasil
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        st.subheader("👤 Identitas Santri")
        st.write(f"**Nama:** {get_val(row_data, 'Nama_Lengkap', 'nama', 'nama_lengkap')}")
        st.write(f"**NISN:** {get_val(row_data, 'NISN', 'nisn')}")
        st.write(f"**Usia:** {get_val(row_data, 'Usia', 'usia')} Tahun")
        st.write(f"**Gender:** {get_val(row_data, 'Jenis_Kelamin', 'jenis_kelamin')}")

    with c2:
        st.subheader("📊 Hasil Asesmen")
        kep = _to_str(get_val(row_data, 'Keputusan_Sistem', 'keputusan_sistem', default='LOLOS BERSYARAT'))
        if "TIDAK LOLOS" in kep.upper():
            st.error(f"**{kep}**")
        elif "BERSYARAT" in kep.upper():
            st.warning(f"**{kep}**")
        else:
            st.success(f"**{kep}**")
        
        conf = _to_float(get_val(row_data, 'Confidence_Score', 'confidence_score', default=0))
        st.metric("Indeks Kesesuaian Program", f"{conf:.1f}%")

    with c3:
        st.subheader("💬 Motivasi Ananda")
        mot = get_val(row_data, 'Motivasi_Peserta', 'motivasi_peserta', 'motivasi')
        st.info(f'"{mot}"')

    st.markdown("---")

    # Chart Visualisasi
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("##### 🕸️ Radar Profil Psikometri vs Threshold Minimum")
        fig_radar = plot_radar_profile(row_data)
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_chart2:
        st.markdown("##### 🩺 Skreeking Kesehatan Mental (DS-21)")
        fig_dass = plot_dass_bar(row_data)
        st.plotly_chart(fig_dass, use_container_width=True)

    st.markdown("---")

    # Fitur AI Individual
    st.subheader("🤖 Analisis AI Individual (Gemini Engine)")
    
    nama_clean = str(get_val(row_data, 'Nama_Lengkap', 'nama', default='santri')).replace(" ", "_")
    ai_session_key = f"ai_report_{nama_clean}"
    
    if ai_session_key not in st.session_state:
        st.session_state[ai_session_key] = ""

    col_ai_btn, col_ai_status = st.columns([1, 2])
    with col_ai_btn:
        if st.button("✨ Generasi Analisis AI Individual", type="primary"):
            with st.spinner("AI Gemini sedang menganalisis profil psikologis Ananda..."):
                from modules.ai_engine import analyze_individual
                ai_res = analyze_individual(row_data)
                st.session_state[ai_session_key] = ai_res
                st.rerun()

    if st.session_state[ai_session_key]:
        st.markdown(st.session_state[ai_session_key])
    else:
        st.caption("Klik tombol di atas untuk membuat analisis mendalam berbasis AI Gemini.")

    st.markdown("---")

    # Export / Download
    st.subheader("📥 Export Laporan Individual")
    
    c_down1, c_down2 = st.columns(2)
    
    # 1. Download TXT
    with c_down1:
        txt_content = f"LAPORAN HASIL SELEKSI INDIVIDUAL\nNama: {get_val(row_data, 'Nama_Lengkap', 'nama')}\nHasil: {get_val(row_data, 'Keputusan_Sistem', 'keputusan_sistem')}\nConfidence: {get_val(row_data, 'Confidence_Score', 'confidence_score')}%\n\nANALISIS AI:\n{st.session_state[ai_session_key]}"
        st.download_button(
            label="📄 Download Laporan (Teks / TXT)",
            data=txt_content,
            file_name=f"Laporan_{nama_clean}.txt",
            mime="text/plain"
        )

    # 2. Download PDF
    with c_down2:
        try:
            pdf_bytes = build_individual_pdf(row_data, st.session_state[ai_session_key])
            st.download_button(
                label="📕 Download Laporan Lengkap (PDF)",
                data=pdf_bytes,
                file_name=f"Laporan_Seleksi_{nama_clean}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Gagal membuat PDF: {e}")