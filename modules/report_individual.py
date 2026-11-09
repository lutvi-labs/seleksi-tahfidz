import io
import re
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

RADAR_MINIMUM_THRESHOLD = 70


def get_col(row, keys, default=0.0):
    if isinstance(row, pd.Series):
        row = row.to_dict()
    if not isinstance(row, dict):
        return default

    clean_row = {str(key).strip().lower(): value for key, value in row.items()}
    for key in keys:
        value = clean_row.get(str(key).strip().lower())
        if value is None or pd.isna(value):
            continue
        if isinstance(default, float):
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        if isinstance(default, int):
            try:
                return int(float(value))
            except (TypeError, ValueError):
                continue
        return str(value)
    return default


def _readiness_dimensions(row):
    dep = get_col(row, ["DASS_Depresi"], 0.0)
    anxiety = get_col(row, ["DASS_Anxiety"], 0.0)
    stress = get_col(row, ["DASS_Stress"], 0.0)
    grit = get_col(row, ["Grit_Score"], 0.0)
    resilience = get_col(row, ["CDRISC_Score"], 0.0)
    memory = get_col(row, ["Memori_Score"], 0.0)
    behavior = get_col(row, ["RB_Score"], 0.0)
    return {
        "Kesejahteraan\n(berdasarkan DASS)": max(0, 100 - ((dep + anxiety + stress) / 126 * 100)),
        "Ketekunan\n(Grit)": max(0, min(100, grit / 5 * 100)),
        "Resiliensi": max(0, min(100, resilience)),
        "Memori": max(0, min(100, memory / 10 * 100)),
        "Perilaku\n(non-RB)": max(0, min(100, 100 - behavior * 20)),
    }


def plot_radar_profile(row):
    dimensions = _readiness_dimensions(row)
    categories = list(dimensions)
    values = list(dimensions.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        name="Profil asesmen",
        fill="toself",
        line=dict(color="#1b5e20", width=3),
        fillcolor="rgba(27, 94, 32, 0.25)"
    ))
    fig.add_trace(go.Scatterpolar(
        r=[RADAR_MINIMUM_THRESHOLD] * (len(categories) + 1),
        theta=categories + [categories[0]],
        name=f"Batas minimal referensi ({RADAR_MINIMUM_THRESHOLD})",
        mode="lines",
        line=dict(color="#c62828", width=2, dash="dash")
    ))
    fig.update_layout(
        title="Profil Dimensi Asesmen (Skala 0-100)",
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=55, b=35),
        height=380
    )
    return fig


def plot_dass_bar(row):
    categories = ["Depresi", "Kecemasan", "Stres"]
    scores = [
        get_col(row, ["DASS_Depresi"], 0.0),
        get_col(row, ["DASS_Anxiety"], 0.0),
        get_col(row, ["DASS_Stress"], 0.0)
    ]
    fig = go.Figure(go.Bar(
        x=categories,
        y=scores,
        marker_color=["#4c956c", "#e9c46a", "#e76f51"],
        text=[f"{score:.0f}" for score in scores],
        textposition="auto"
    ))
    fig.update_layout(
        title="Skor DASS-21 per Dimensi (0-42)",
        yaxis=dict(title="Skor", range=[0, 42]),
        height=320,
        margin=dict(l=30, r=30, t=55, b=35),
        showlegend=False
    )
    return fig


def _chart_image(row, chart_type):
    import matplotlib.pyplot as plt

    image = io.BytesIO()
    if chart_type == "radar":
        labels = list(_readiness_dimensions(row))
        values = list(_readiness_dimensions(row).values())
        angles = [index / float(len(labels)) * 2 * 3.14159 for index in range(len(labels))]
        values += values[:1]
        angles += angles[:1]

        figure, axis = plt.subplots(figsize=(7, 5), subplot_kw={"polar": True})
        axis.plot(angles, values, color="#1b5e20", linewidth=2)
        axis.fill(angles, values, color="#2e7d32", alpha=0.2)
        axis.set_xticks(angles[:-1])
        axis.set_xticklabels(labels, fontsize=8)
        axis.set_ylim(0, 100)
        axis.plot(
            angles,
            [RADAR_MINIMUM_THRESHOLD] * len(angles),
            color="#c62828",
            linewidth=1.5,
            linestyle="--",
            label=f"Batas minimal referensi ({RADAR_MINIMUM_THRESHOLD})"
        )
        axis.legend(loc="lower center", bbox_to_anchor=(0.5, -0.2), fontsize=8)
        axis.set_title("Profil Dimensi Asesmen (Skala 0-100)", pad=20)
    elif chart_type == "progress":
        labels = ["Hafalan\ndikuasai", "Hafalan\nterjaga", "Hafalan baru\n(3 bulan)"]
        values = [
            get_col(row, ["juz_dikuasai"], 0.0),
            get_col(row, ["juz_terjaga"], 0.0),
            get_col(row, ["juz_baru_3_bulan"], 0.0)
        ]
        figure, axis = plt.subplots(figsize=(7, 3.5))
        axis.bar(labels, values, color=["#2e7d32", "#52b788", "#95d5b2"])
        axis.set_ylabel("Perkiraan jumlah juz")
        axis.set_ylim(0, 30)
        axis.set_title("Ringkasan Progres Hafalan (data yang dilaporkan)")
        axis.grid(axis="y", alpha=0.2)
    elif chart_type == "dass":
        labels = ["Depresi", "Kecemasan", "Stres"]
        values = [
            get_col(row, ["DASS_Depresi"], 0.0),
            get_col(row, ["DASS_Anxiety"], 0.0),
            get_col(row, ["DASS_Stress"], 0.0)
        ]
        figure, axis = plt.subplots(figsize=(7, 3.5))
        axis.bar(labels, values, color=["#4c956c", "#e9c46a", "#e76f51"])
        axis.set_ylabel("Skor (0-42)")
        axis.set_ylim(0, 42)
        axis.set_title("Skor DASS-21 per Dimensi")
        axis.grid(axis="y", alpha=0.2)
    else:
        labels = ["Grit", "Resiliensi", "Memori", "Kesejahteraan"]
        dimensions = _readiness_dimensions(row)
        values = [
            dimensions["Ketekunan\n(Grit)"],
            dimensions["Resiliensi"],
            dimensions["Memori"],
            dimensions["Kesejahteraan\n(berdasarkan DASS)"]
        ]
        figure, axis = plt.subplots(figsize=(7, 3.5))
        axis.bar(labels, values, color=["#2e7d32", "#40916c", "#74c69d", "#95d5b2"])
        axis.set_ylabel("Skala 0-100")
        axis.set_ylim(0, 100)
        axis.set_title("Ringkasan Skor Tes (skala dinormalisasi)")
        axis.grid(axis="y", alpha=0.2)

    figure.tight_layout()
    figure.savefig(image, format="png", dpi=160, bbox_inches="tight")
    plt.close(figure)
    image.seek(0)
    return image


def _add_ai_text(document, text):
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        heading = re.match(r"^#{1,3}\s+(.+)$", line)
        if heading:
            document.add_heading(heading.group(1).replace("**", ""), level=min(line.count("#"), 3))
        elif line.startswith(("- ", "* ")):
            document.add_paragraph(line[2:].replace("**", ""), style="List Bullet")
        else:
            document.add_paragraph(line.replace("**", "").replace("__", ""))


def build_individual_docx(row, ai_text=""):
    document = Document()
    styles = document.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10)

    kind = get_col(row, ["Jenis_Santri", "jenis_santri"], "santri_baru")
    is_current = kind == "santri_aktif"
    title = "LAPORAN ASESMEN SANTRI AKTIF" if is_current else "LAPORAN ASESMEN SANTRI BARU"
    heading = document.add_heading(title, level=0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_paragraph("Target program tahfidz: 30 juz dalam waktu kurang dari 3 tahun")

    name = get_col(row, ["nama", "nama_lengkap", "username"], "-")
    identity = document.add_table(rows=0, cols=2)
    identity.style = "Light Shading Accent 1"
    identity_rows = [
        ("Nama", name),
        ("Usia", f"{get_col(row, ['usia'], '-') } tahun"),
        ("Jenis kelamin", get_col(row, ["jenis_kelamin"], "-")),
        ("Asal sekolah", get_col(row, ["asal_sekolah"], "-")),
        ("Tanggal laporan", datetime.now().strftime("%d-%m-%Y")),
    ]
    if is_current:
        identity_rows.extend([
            ("Kelas saat ini", get_col(row, ["kelas_saat_ini"], "-")),
            ("Lama belajar di pondok", f"{get_col(row, ['lama_mondok_bulan'], 0)} bulan")
        ])
    for label, value in identity_rows:
        cells = identity.add_row().cells
        cells[0].text = label
        cells[1].text = str(value)

    if not is_current:
        readiness = get_col(row, ["Skor_Kesiapan_30Juz"], 0.0)
        document.add_heading("Skor Kesiapan Target 30 Juz", level=1)
        paragraph = document.add_paragraph()
        run = paragraph.add_run(f"{readiness:.1f}%")
        run.bold = True
        run.font.size = Pt(18)
        run.font.color.rgb = RGBColor(27, 94, 32)
        document.add_paragraph(
            "Skor ini adalah indeks ringkasan berbobot: indikator kondisi psikologis berbasis DASS (25%), "
            "ketekunan (25%), resiliensi (30%), dan memori (20%). Indeks bukan probabilitas "
            "keberhasilan dan bukan keputusan penerimaan, serta belum divalidasi terhadap data "
            "capaian hafalan dari waktu ke waktu. Respons perilaku ditampilkan terpisah sebagai "
            "bahan pendampingan dan tidak mengurangi skor. Keputusan PSB tetap menjadi pertimbangan panitia."
        )

    document.add_heading("Ringkasan Hasil Tes", level=1)
    score_rows = [
        ("DASS-21 Depresi", get_col(row, ["DASS_Depresi"], 0.0), "0-42"),
        ("DASS-21 Kecemasan", get_col(row, ["DASS_Anxiety"], 0.0), "0-42"),
        ("DASS-21 Stres", get_col(row, ["DASS_Stress"], 0.0), "0-42"),
        ("Grit-8", get_col(row, ["Grit_Score"], 0.0), "1-5"),
        ("Resiliensi (CR-25)", get_col(row, ["CDRISC_Score"], 0.0), "0-100"),
        ("Tes memori kata", get_col(row, ["Memori_Score"], 0.0), "0-10 kata"),
        ("Arti kosakata Arab (eksploratif)", get_col(row, ["Memori_Arab_Score"], 0), "0-8 arti"),
        ("Urutan potongan Al-Baqarah (eksploratif)", get_col(row, ["Memori_Ayat_Score"], 0), "0-1 benar"),
        ("Urutan warna benda (eksploratif)", get_col(row, ["Memori_Warna_Score"], 0), "0-5 posisi"),
        ("Urutan bunyi (eksploratif)", get_col(row, ["Memori_Suara_Score"], 0), "0-4 posisi"),
        ("Indikator respons perilaku (RB-5)", get_col(row, ["RB_Score"], 0.0), "0-5 respons")
    ]
    scores = document.add_table(rows=1, cols=3)
    scores.style = "Light Shading Accent 1"
    for cell, label in zip(scores.rows[0].cells, ["Dimensi", "Skor", "Rentang"]):
        cell.text = label
    for label, value, scale in score_rows:
        cells = scores.add_row().cells
        cells[0].text = label
        cells[1].text = f"{value:.2f}" if isinstance(value, float) else str(value)
        cells[2].text = scale

    document.add_heading("Visualisasi Hasil Asesmen", level=1)
    document.add_paragraph(
        "Grafik menggambarkan skor asesmen dan bukan ambang kelulusan. Variasi tes memori "
        "bersifat eksploratif dan belum menjadi bagian dari skor kesiapan. Garis putus-putus "
        f"pada radar adalah batas minimal referensi {RADAR_MINIMUM_THRESHOLD}/100, bukan ambang kelulusan."
    )
    document.add_picture(_chart_image(row, "radar"), width=Inches(6.1))
    document.add_picture(_chart_image(row, "scores"), width=Inches(6.1))
    document.add_picture(_chart_image(row, "dass"), width=Inches(6.1))

    if is_current:
        document.add_heading("Perkembangan Belajar di Pondok", level=1)
        for label, keys in [
            ("Perkiraan hafalan dikuasai", ["juz_dikuasai"]),
            ("Perkiraan hafalan yang terjaga", ["juz_terjaga"]),
            ("Tambahan hafalan 3 bulan terakhir", ["juz_baru_3_bulan"])
        ]:
            document.add_paragraph(f"{label}: {get_col(row, keys, '-') } juz")
        document.add_paragraph(
            f"Rata-rata murajaah harian: {get_col(row, ['murajaah_menit_per_hari'], '-')} menit"
        )
        document.add_picture(_chart_image(row, "progress"), width=Inches(6.1))

        document.add_heading("Kondisi dan Kebutuhan Dukungan", level=1)
        for label, keys in [
            ("Perasaan saat belajar", ["perasaan_belajar"]),
            ("Kendala yang dirasakan", ["kendala_belajar"]),
            ("Hal yang membuat tetap bersemangat", ["motivasi"]),
            ("Harapan belajar", ["harapan_belajar"])
        ]:
            document.add_paragraph(f"{label}: {get_col(row, keys, '-')}")
    else:
        document.add_heading("Motivasi dan Harapan", level=1)
        document.add_paragraph(f"Motivasi: {get_col(row, ['motivasi'], '-')}")
        document.add_paragraph(f"Harapan belajar: {get_col(row, ['harapan_belajar'], '-')}")

    document.add_heading("Catatan Interpretasi", level=1)
    document.add_paragraph(
        "Instrumen dan indeks dalam laporan ini merupakan bahan pertimbangan pendampingan. "
        "Hasil bukan diagnosis psikologis. Skor perlu ditafsirkan bersama asesmen langsung, "
        "observasi pembimbing, serta data capaian hafalan yang terukur."
    )
    if ai_text.strip():
        document.add_heading("Analisis AI dan Rekomendasi Pendampingan", level=1)
        _add_ai_text(document, ai_text)
        document.add_paragraph(
            "Catatan: keluaran AI merupakan dukungan penyusunan rekomendasi dan perlu ditinjau "
            "oleh panitia atau pembimbing."
        )

    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def show_individual_report(df_responses):
    st.title("📋 Laporan Individual Santri")
    st.markdown("Laporan hasil asesmen, visualisasi, dan rekomendasi pendampingan. Unduhan tersedia dalam format DOCX yang dapat diedit.")

    if df_responses is None or (isinstance(df_responses, pd.DataFrame) and df_responses.empty):
        st.warning("⚠️ Belum ada data respons peserta yang tersimpan di database Supabase.")
        return

    df = df_responses.copy()
    if "Jenis_Santri" not in df.columns:
        df["Jenis_Santri"] = df.get("jenis_santri", "santri_baru")
    df["Jenis_Santri"] = df["Jenis_Santri"].fillna("santri_baru")
    type_labels = {"santri_baru": "Santri baru", "santri_aktif": "Santri aktif"}
    selected_type = st.selectbox("Jenis laporan", list(type_labels), format_func=type_labels.get)
    df = df[df["Jenis_Santri"] == selected_type]
    if df.empty:
        st.info("Belum ada hasil asesmen untuk jenis santri ini.")
        return

    name_col = next((column for column in ["nama", "nama_lengkap", "username", "Nama_Lengkap"] if column in df.columns), None)
    if not name_col:
        st.error("⚠️ Kolom identifier peserta tidak ditemukan.")
        return

    participants = df[name_col].dropna().astype(str).unique().tolist()
    if not participants:
        st.warning("⚠️ Belum ada santri yang menyelesaikan survei.")
        return
    selected_name = st.selectbox("Pilih nama santri", participants)
    row_data = df[df[name_col].astype(str) == selected_name].iloc[0].to_dict()

    st.markdown("---")
    col_identity, col_score = st.columns(2)
    with col_identity:
        st.subheader("Identitas Santri")
        st.write(f"**Nama:** {get_col(row_data, ['nama', 'nama_lengkap', 'username'], '-')}")
        st.write(f"**Usia:** {get_col(row_data, ['usia'], '-')}")
        if selected_type == "santri_aktif":
            st.write(f"**Kelas:** {get_col(row_data, ['kelas_saat_ini'], '-')}")
            st.write(f"**Lama di pondok:** {get_col(row_data, ['lama_mondok_bulan'], '-') } bulan")
    with col_score:
        if selected_type == "santri_baru":
            readiness = get_col(row_data, ["Skor_Kesiapan_30Juz"], 0.0)
            st.metric("Skor Kesiapan Target 30 Juz", f"{readiness:.1f}%")
            st.caption("Indeks asesmen, bukan probabilitas keberhasilan atau keputusan PSB.")
        else:
            st.metric("Hafalan dikuasai", f"{get_col(row_data, ['juz_dikuasai'], 0.0):g} juz")
            st.metric("Hafalan terjaga", f"{get_col(row_data, ['juz_terjaga'], 0.0):g} juz")

    chart1, chart2 = st.columns(2)
    with chart1:
        st.plotly_chart(plot_radar_profile(row_data), use_container_width=True)
        st.caption(
            f"Garis putus-putus menunjukkan batas minimal referensi {RADAR_MINIMUM_THRESHOLD}/100, "
            "bukan ambang kelulusan."
        )
    with chart2:
        st.plotly_chart(plot_dass_bar(row_data), use_container_width=True)
    st.markdown("#### Rincian Hasil Tes")
    st.dataframe(pd.DataFrame([
        {"Tes": label, "Skor": value, "Rentang": scale}
        for label, value, scale in [
            ("DASS-21 Depresi", get_col(row_data, ["DASS_Depresi"], 0.0), "0-42"),
            ("DASS-21 Kecemasan", get_col(row_data, ["DASS_Anxiety"], 0.0), "0-42"),
            ("DASS-21 Stres", get_col(row_data, ["DASS_Stress"], 0.0), "0-42"),
            ("Grit-8", get_col(row_data, ["Grit_Score"], 0.0), "1-5"),
            ("Resiliensi (CR-25)", get_col(row_data, ["CDRISC_Score"], 0.0), "0-100"),
            ("Tes memori kata", get_col(row_data, ["Memori_Score"], 0.0), "0-10 kata"),
            ("Arti kosakata Arab (eksploratif)", get_col(row_data, ["Memori_Arab_Score"], 0), "0-8 arti"),
            ("Urutan potongan Al-Baqarah (eksploratif)", get_col(row_data, ["Memori_Ayat_Score"], 0), "0-1 benar"),
            ("Urutan warna benda (eksploratif)", get_col(row_data, ["Memori_Warna_Score"], 0), "0-5 posisi"),
            ("Urutan bunyi (eksploratif)", get_col(row_data, ["Memori_Suara_Score"], 0), "0-4 posisi"),
            ("RB-5", get_col(row_data, ["RB_Score"], 0.0), "0-5 respons")
        ]
    ]), hide_index=True, use_container_width=True)

    if selected_type == "santri_aktif":
        st.markdown("#### Progres dan Refleksi Santri")
        progress_cols = [
            column for column in [
                "juz_dikuasai", "juz_terjaga", "juz_baru_3_bulan",
                "murajaah_menit_per_hari", "perasaan_belajar", "kendala_belajar", "motivasi"
            ] if column in row_data
        ]
        st.dataframe(pd.DataFrame([row_data])[progress_cols], hide_index=True, use_container_width=True)

    st.markdown("---")
    st.subheader("Analisis AI Individual")
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", selected_name).strip("_") or "santri"
    ai_session_key = f"ai_report_{selected_type}_{safe_name}"
    if ai_session_key not in st.session_state:
        st.session_state[ai_session_key] = ""
    if st.button("✨ Buat Analisis dan Rekomendasi AI", type="primary"):
        with st.spinner("AI sedang menyusun rekomendasi pendampingan..."):
            from modules.ai_engine import analyze_individual
            st.session_state[ai_session_key] = analyze_individual(row_data)
    if st.session_state[ai_session_key]:
        st.markdown(st.session_state[ai_session_key])
    else:
        st.caption("Buat analisis AI untuk menambahkan rekomendasi ke laporan.")

    st.markdown("---")
    st.subheader("Unduh Laporan")
    try:
        report_bytes = build_individual_docx(row_data, st.session_state[ai_session_key])
    except Exception as error:
        st.error(f"Gagal membuat dokumen DOCX: {error}")
        return
    st.download_button(
        label="📝 Unduh Laporan Editable (DOCX)",
        data=report_bytes,
        file_name=f"Laporan_Asesmen_{selected_type}_{safe_name}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
