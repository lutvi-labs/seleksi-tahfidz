"""
dashboard.py â€” Visualisasi dashboard menggunakan Plotly + Streamlit
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import streamlit as st


class Dashboard:
    """Dashboard visualisasi hasil seleksi santri tahfidz."""
    
    def __init__(self):
        self.colors = {
            "lolos": "#2ecc71",
            "bersyarat": "#f39c12",
            "tidak_lolos": "#e74c3c",
            "primary": "#3498db",
            "secondary": "#9b59b6",
            "dark": "#2c3e50",
            "light": "#ecf0f1"
        }
    
    # ============================================================
    # OVERVIEW METRICS
    # ============================================================
    
    def render_overview_metrics(self, df: pd.DataFrame):
        """Render kartu metrik overview di bagian atas dashboard."""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        total = len(df)
        lolos = len(df[df["Keputusan"] == "âœ… LOLOS"])
        bersyarat = len(df[df["Keputusan"] == "âš¡ LOLOS BERSYARAT"])
        tidak_lolos = len(df[df["Keputusan"] == "âŒ TIDAK LOLOS"])
        avg_confidence = df["Confidence_Score"].mean()
        
        col1.metric("ðŸ“‹ Total Pendaftar", total)
        col2.metric("âœ… Lolos", lolos, f"{lolos/total*100:.1f}%")
        col3.metric("âš¡ Bersyarat", bersyarat, f"{bersyarat/total*100:.1f}%")
        col4.metric("âŒ Tidak Lolos", tidak_lolos, f"{tidak_lolos/total*100:.1f}%")
        col5.metric("ðŸ“Š Avg Confidence", f"{avg_confidence:.1f}")
    
    # ============================================================
    # DECISION PIE CHART
    # ============================================================
    
    def plot_decision_pie(self, df: pd.DataFrame) -> go.Figure:
        """Pie chart distribusi keputusan."""
        counts = df["Keputusan"].value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.4,
            marker_colors=[
                self.colors["lolos"], 
                self.colors["bersyarat"], 
                self.colors["tidak_lolos"]
            ],
            textinfo='label+value+percent',
            textfont_size=14
        )])
        
        fig.update_layout(
            title="ðŸ“Š Distribusi Keputusan Seleksi",
            font=dict(size=14),
            height=400
        )
        
        return fig
    
    # ============================================================
    # DASS DISTRIBUTION
    # ============================================================
    
    def plot_dass_distribution(self, df: pd.DataFrame) -> go.Figure:
        """Histogram distribusi skor DASS-21."""
        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=("Depresi", "Kecemasan", "Stres")
        )
        
        for i, (col, color) in enumerate([
            ("DASS_Depresi", "#e74c3c"),
            ("DASS_Kecemasan", "#f39c12"),
            ("DASS_Stres", "#3498db")
        ]):
            fig.add_trace(
                go.Histogram(
                    x=df[col], 
                    name=col.split("_")[1],
                    marker_color=color,
                    opacity=0.7,
                    nbinsx=15
                ),
                row=1, col=i+1
            )
        
        fig.update_layout(
            title="ðŸ“ˆ Distribusi Skor DASS-21",
            showlegend=True,
            height=400
        )
        
        return fig
    
    # ============================================================
    # GRIT & CD-RISC SCATTER
    # ============================================================
    
    def plot_grit_cdrisc_scatter(self, df: pd.DataFrame) -> go.Figure:
        """Scatter plot Grit vs CD-RISC dengan warna keputusan."""
        color_map = {
            "âœ… LOLOS": self.colors["lolos"],
            "âš¡ LOLOS BERSYARAT": self.colors["bersyarat"],
            "âŒ TIDAK LOLOS": self.colors["tidak_lolos"]
        }
        
        fig = go.Figure()
        
        for keputusan, color in color_map.items():
            mask = df["Keputusan"] == keputusan
            fig.add_trace(go.Scatter(
                x=df[mask]["Grit_Skor"],
                y=df[mask]["CDRISC_Total"],
                mode="markers",
                name=keputusan,
                marker=dict(size=10, color=color, opacity=0.7),
                text=df[mask]["nama_lengkap"],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Grit: %{x:.2f}<br>"
                    "CD-RISC: %{y}<br>"
                    "<extra></extra>"
                )
            ))
        
        # Threshold lines
        fig.add_hline(y=65, line_dash="dash", line_color="gray", 
                      annotation_text="CD-RISC Cutoff (65)")
        fig.add_vline(x=3.5, line_dash="dash", line_color="gray",
                      annotation_text="Grit Cutoff (3.5)")
        
        fig.update_layout(
            title="ðŸŽ¯ Grit vs Resiliensi (CD-RISC)",
            xaxis_title="Grit Score (1-5)",
            yaxis_title="CD-RISC Total (0-100)",
            height=500
        )
        
        return fig
    
    # ============================================================
    # RADAR CHART (INDIVIDUAL PROFILE)
    # ============================================================
    
    def plot_individual_radar(self, row: pd.Series) -> go.Figure:
        """Radar chart profil individual santri."""
        categories = [
            "Kesehatan Mental\n(DASS-inv)",
            "Ketekunan\n(Grit)",
            "Resiliensi\n(CD-RISC)",
            "Motivasi",
            "Konsistensi\n(Grit CI)",
            "Kegigihan\n(Grit PE)"
        ]
        
        # Normalisasi semua ke 0-100
        values = [
            max(0, 100 - (row.get("DASS_Depresi", 0) + 
                          row.get("DASS_Kecemasan", 0) + 
                          row.get("DASS_Stres", 0)) / 63 * 100),
            row.get("Grit_Skor", 0) / 5 * 100,
            row.get("CDRISC_Total", 0),
            row.get("Motivasi_Skor", 3) / 5 * 100,
            row.get("Grit_CI", 0) / 5 * 100,
            row.get("Grit_PE", 0) / 5 * 100
        ]
        
        fig = go.Figure(data=go.Scatterpolar(
            r=values + [values[0]],  # Close the polygon
            theta=categories + [categories[0]],
            fill='toself',
            marker_color=self.colors["primary"],
            opacity=0.6
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title=f"ðŸŽ¯ Profil: {row.get('nama_lengkap', 'N/A')}",
            height=450
        )
        
        return fig
    
    # ============================================================
    # RANKING TABLE
    # ============================================================
    
    def render_ranking_table(self, df: pd.DataFrame):
        """Render tabel ranking interaktif."""
        display_cols = [
            "Ranking", "nama_lengkap", "usia",
            "DASS_Depresi", "DASS_Kecemasan", "DASS_Stres",
            "Grit_Skor", "CDRISC_Total",
            "Confidence_Score", "Keputusan"
        ]
        
        available_cols = [c for c in display_cols if c in df.columns]
        display_df = df[available_cols].sort_values("Ranking")
        
        # Color-code the dataframe
        def highlight_decision(val):
            if "LOLOS" in str(val) and "TIDAK" not in str(val) and "BERSYARAT" not in str(val):
                return "background-color: #d4edda"
            elif "BERSYARAT" in str(val):
                return "background-color: #fff3cd"
            elif "TIDAK" in str(val):
                return "background-color: #f8d7da"
            return ""
        
        styled = display_df.style.applymap(
            highlight_decision, subset=["Keputusan"]
        )
        
        st.dataframe(styled, use_container_width=True, height=500)
    
    # ============================================================
    # CORRELATION HEATMAP
    # ============================================================
    
    def plot_correlation_heatmap(self, corr_result: dict) -> go.Figure:
        """Heatmap korelasi gaya JASP."""
        corr_matrix = corr_result["correlation"]
        p_matrix = corr_result["p_values"]
        
        # Buat annotation text
        annotations = []
        for i in range(len(corr_matrix)):
            for j in range(len(corr_matrix)):
                r = corr_matrix.iloc[i, j]
                p = p_matrix.iloc[i, j]
                sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
                annotations.append(f"{r:.2f}{sig}")
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale="RdBu_r",
            zmid=0,
            text=np.array(annotations).reshape(corr_matrix.shape),
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverinfo="z"
        ))
        
        fig.update_layout(
            title="ðŸ”— Matriks Korelasi (***p<.001, **p<.01, *p<.05)",
            height=500
        )
        
        return fig
    
    # ============================================================
    # RELIABILITY SUMMARY
    # ============================================================
    
    def render_reliability_table(self, reliability_results: dict):
        """Render tabel reliabilitas."""
        rows = []
        for scale, result in reliability_results.items():
            if "error" not in result:
                rows.append({
                    "Skala": scale,
                    "N Items": result.get("n_items", "N/A"),
                    "Cronbach's Î±": result.get("cronbach_alpha", "N/A"),
                    "Interpretasi": result.get("interpretation", "N/A")
                })
        
        if rows:
            st.table(pd.DataFrame(rows))
        else:
            st.warning("Tidak ada data reliabilitas yang tersedia.")
    
    # ============================================================
    # CONFIDENCE SCORE DISTRIBUTION
    # ============================================================
    
    def plot_confidence_distribution(self, df: pd.DataFrame) -> go.Figure:
        """Histogram confidence score dengan cutoff markers."""
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=df["Confidence_Score"],
            nbinsx=20,
            marker_color=self.colors["primary"],
            opacity=0.7,
            name="Confidence Score"
        ))
        
        # Add mean line
        mean_val = df["Confidence_Score"].mean()
        fig.add_vline(
            x=mean_val, line_dash="dash", line_color="red",
            annotation_text=f"Mean: {mean_val:.1f}"
        )
        
        fig.update_layout(
            title="ðŸ“Š Distribusi Confidence Score",
            xaxis_title="Confidence Score (0-100)",
            yaxis_title="Frekuensi",
            height=400
        )
        
        return fig


# Singleton
dashboard = Dashboard()
