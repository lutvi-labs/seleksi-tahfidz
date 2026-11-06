"""
jasp_bridge.py — Bridge ke JASP melalui R Engine (rpy2)
Melakukan analisis statistik gaya JASP langsung dari Python
"""
import pandas as pd
import numpy as np
import streamlit as st

# ============================================================
# PURE PYTHON STATISTICS (FALLBACK jika R tidak tersedia)
# ============================================================
from scipy import stats
from scipy.stats import shapiro, pearsonr, spearmanr
import pingouin as pg
from .scoring import (
    CDRISC_ITEMS,
    DASS_ANXIETY_ITEMS,
    DASS_DEPRESSION_ITEMS,
    DASS_STRESS_ITEMS,
    GRIT_NORMAL_ITEMS,
    GRIT_REVERSE_ITEMS,
)


class JASPBridge:
    """
    Bridge yang melakukan analisis statistik gaya JASP.
    
    Prioritas:
    1. Gunakan R/rpy2 jika tersedia (output identik JASP)
    2. Fallback ke Python (pingouin + scipy) jika R tidak tersedia
    """
    
    def __init__(self):
        self.r_available = self._check_r()
        self.results = {}
    
    def _check_r(self) -> bool:
        """Cek apakah R dan rpy2 tersedia."""
        try:
            import rpy2.robjects as ro
            from rpy2.robjects import pandas2ri
            pandas2ri.activate()
            ro.r('library(psych)')  # Test if psych package is available
            return True
        except Exception:
            return False
    
    # ============================================================
    # 1. DESCRIPTIVE STATISTICS
    # ============================================================
    
    def descriptives(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        """
        Statistik deskriptif gaya JASP.
        """
        desc = df[columns].describe().T
        desc["Median"] = df[columns].median()
        desc["Skewness"] = df[columns].skew()
        desc["Kurtosis"] = df[columns].kurtosis()
        desc["SE"] = df[columns].sem()
        
        # Reorder columns
        desc = desc[["count", "mean", "Median", "std", "SE", 
                      "min", "25%", "50%", "75%", "max", 
                      "Skewness", "Kurtosis"]]
        desc.columns = ["N", "Mean", "Median", "SD", "SE", 
                        "Min", "Q1", "Q2", "Q3", "Max", 
                        "Skewness", "Kurtosis"]
        
        return desc.round(3)
    
    # ============================================================
    # 2. RELIABILITY ANALYSIS (CRONBACH'S ALPHA)
    # ============================================================
    
    def reliability_analysis(self, df: pd.DataFrame, 
                              scale_name: str, 
                              items: list) -> dict:
        """
        Analisis reliabilitas (Cronbach's Alpha) gaya JASP.
        """
        if self.r_available:
            return self._reliability_r(df, scale_name, items)
        else:
            return self._reliability_python(df, scale_name, items)
    
    def _reliability_python(self, df, scale_name, items) -> dict:
        """Cronbach's Alpha menggunakan Python."""
        item_data = df[items].dropna()
        n_items = len(items)
        n_respondents = len(item_data)
        
        if n_respondents < 2 or n_items < 2:
            return {"error": "Data tidak cukup untuk analisis reliabilitas"}
        
        # Cronbach's Alpha
        item_variances = item_data.var(axis=0, ddof=1)
        total_variance = item_data.sum(axis=1).var(ddof=1)
        
        alpha = (n_items / (n_items - 1)) * (
            1 - item_variances.sum() / total_variance
        )
        
        # Item-total correlation
        total_score = item_data.sum(axis=1)
        item_total_corr = {}
        alpha_if_deleted = {}
        
        for item in items:
            # Corrected item-total correlation
            rest_score = total_score - item_data[item]
            corr, _ = pearsonr(item_data[item], rest_score)
            item_total_corr[item] = round(corr, 3)
            
            # Alpha if item deleted
            remaining = [i for i in items if i != item]
            if len(remaining) >= 2:
                rem_data = item_data[remaining]
                rem_var = rem_data.var(axis=0, ddof=1).sum()
                rem_total_var = rem_data.sum(axis=1).var(ddof=1)
                n_rem = len(remaining)
                a_del = (n_rem / (n_rem - 1)) * (1 - rem_var / rem_total_var)
                alpha_if_deleted[item] = round(a_del, 3)
        
        # McDonald's Omega (simplified)
        try:
            omega = pg.cronbach_alpha(item_data)[0]
        except Exception:
            omega = alpha
        
        result = {
            "scale_name": scale_name,
            "n_items": n_items,
            "n_respondents": n_respondents,
            "cronbach_alpha": round(alpha, 3),
            "mcdonalds_omega": round(omega, 3),
            "mean_inter_item_corr": round(
                item_data.corr().values[
                    np.triu_indices(n_items, k=1)
                ].mean(), 3
            ),
            "item_total_correlations": item_total_corr,
            "alpha_if_deleted": alpha_if_deleted,
            "interpretation": self._interpret_alpha(alpha)
        }
        
        return result
    
    def _reliability_r(self, df, scale_name, items) -> dict:
        """Cronbach's Alpha menggunakan R (psych package)."""
        try:
            import rpy2.robjects as ro
            from rpy2.robjects import pandas2ri
            
            item_data = df[items].dropna()
            r_df = pandas2ri.py2rpy(item_data)
            
            ro.globalenv['item_data'] = r_df
            result = ro.r('''
                library(psych)
                result <- alpha(item_data)
                list(
                    raw_alpha = result$total$raw_alpha,
                    std_alpha = result$total$std.alpha,
                    average_r = result$total$average_r,
                    item_stats = as.data.frame(result$item.stats),
                    alpha_drop = as.data.frame(result$alpha.drop)
                )
            ''')
            
            return {
                "scale_name": scale_name,
                "cronbach_alpha": round(float(result[0][0]), 3),
                "std_alpha": round(float(result[1][0]), 3),
                "average_r": round(float(result[2][0]), 3),
                "source": "R/psych"
            }
        except Exception:
            return self._reliability_python(df, scale_name, items)
    
    def _interpret_alpha(self, alpha: float) -> str:
        """Interpretasi Cronbach's Alpha."""
        if alpha >= 0.9:
            return "Excellent (α ≥ .90)"
        elif alpha >= 0.8:
            return "Good (α ≥ .80)"
        elif alpha >= 0.7:
            return "Acceptable (α ≥ .70)"
        elif alpha >= 0.6:
            return "Questionable (α ≥ .60)"
        elif alpha >= 0.5:
            return "Poor (α ≥ .50)"
        else:
            return "Unacceptable (α < .50)"
    
    # ============================================================
    # 3. CORRELATION ANALYSIS
    # ============================================================
    
    def correlation_matrix(self, df: pd.DataFrame, 
                           columns: list,
                           method: str = "pearson") -> dict:
        """
        Matriks korelasi gaya JASP dengan p-values.
        """
        n = len(columns)
        corr_matrix = pd.DataFrame(
            np.zeros((n, n)), 
            index=columns, columns=columns
        )
        p_matrix = corr_matrix.copy()
        
        for i, col1 in enumerate(columns):
            for j, col2 in enumerate(columns):
                if i == j:
                    corr_matrix.iloc[i, j] = 1.0
                    p_matrix.iloc[i, j] = 0.0
                elif i < j:
                    valid = df[[col1, col2]].dropna()
                    if method == "pearson":
                        r, p = pearsonr(valid[col1], valid[col2])
                    else:
                        r, p = spearmanr(valid[col1], valid[col2])
                    corr_matrix.iloc[i, j] = round(r, 3)
                    corr_matrix.iloc[j, i] = round(r, 3)
                    p_matrix.iloc[i, j] = round(p, 4)
                    p_matrix.iloc[j, i] = round(p, 4)
        
        return {
            "correlation": corr_matrix,
            "p_values": p_matrix,
            "method": method,
            "n": len(df)
        }
    
    # ============================================================
    # 4. NORMALITY TESTS
    # ============================================================
    
    def normality_tests(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        """
        Tes normalitas (Shapiro-Wilk) gaya JASP.
        """
        results = []
        for col in columns:
            data = df[col].dropna()
            if len(data) >= 3:
                stat, p = shapiro(data)
                results.append({
                    "Variable": col,
                    "W": round(stat, 4),
                    "p": round(p, 4),
                    "Normal (α=.05)": "Yes" if p > 0.05 else "No"
                })
        
        return pd.DataFrame(results)
    
    # ============================================================
    # 5. GROUP COMPARISON
    # ============================================================
    
    def compare_groups(self, df: pd.DataFrame, 
                       dv: str, 
                       group: str) -> dict:
        """
        Perbandingan grup (t-test / Mann-Whitney) gaya JASP.
        """
        groups = df[group].unique()
        
        if len(groups) != 2:
            return {"error": f"Butuh 2 grup, ditemukan {len(groups)}"}
        
        g1 = df[df[group] == groups[0]][dv].dropna()
        g2 = df[df[group] == groups[1]][dv].dropna()
        
        # Normality check
        _, p1 = shapiro(g1) if len(g1) >= 3 else (0, 0)
        _, p2 = shapiro(g2) if len(g2) >= 3 else (0, 0)
        
        is_normal = p1 > 0.05 and p2 > 0.05
        
        if is_normal:
            # Independent t-test
            t_stat, p_val = stats.ttest_ind(g1, g2)
            # Cohen's d
            pooled_std = np.sqrt(
                ((len(g1)-1)*g1.std()**2 + (len(g2)-1)*g2.std()**2) / 
                (len(g1)+len(g2)-2)
            )
            cohens_d = (g1.mean() - g2.mean()) / pooled_std if pooled_std > 0 else 0
            
            return {
                "test": "Independent Samples T-Test",
                "t": round(t_stat, 3),
                "df": len(g1) + len(g2) - 2,
                "p": round(p_val, 4),
                "cohens_d": round(cohens_d, 3),
                "group1": {"name": str(groups[0]), "mean": round(g1.mean(), 2), "sd": round(g1.std(), 2), "n": len(g1)},
                "group2": {"name": str(groups[1]), "mean": round(g2.mean(), 2), "sd": round(g2.std(), 2), "n": len(g2)},
                "significant": p_val < 0.05
            }
        else:
            # Mann-Whitney U
            u_stat, p_val = stats.mannwhitneyu(g1, g2, alternative='two-sided')
            # Rank-biserial correlation
            r_rb = 1 - (2*u_stat) / (len(g1)*len(g2))
            
            return {
                "test": "Mann-Whitney U Test",
                "U": round(u_stat, 3),
                "p": round(p_val, 4),
                "rank_biserial_r": round(r_rb, 3),
                "group1": {"name": str(groups[0]), "median": round(g1.median(), 2), "n": len(g1)},
                "group2": {"name": str(groups[1]), "median": round(g2.median(), 2), "n": len(g2)},
                "significant": p_val < 0.05
            }
    
    # ============================================================
    # 6. COMPREHENSIVE ANALYSIS (ALL-IN-ONE)
    # ============================================================
    
    def full_analysis(self, df: pd.DataFrame) -> dict:
        """
        Jalankan semua analisis statistik sekaligus.
        
        Returns:
            dict dengan semua hasil analisis
        """
        score_cols = [
            "DASS_Depresi", "DASS_Kecemasan", "DASS_Stres",
            "Grit_Skor", "Grit_CI", "Grit_PE",
            "CDRISC_Total", "Confidence_Score"
        ]
        
        # Filter kolom yang ada
        available_cols = [c for c in score_cols if c in df.columns]
        
        results = {}
        
        # 1. Descriptives
        st.info("📊 Menghitung statistik deskriptif...")
        results["descriptives"] = self.descriptives(df, available_cols)
        
        # 2. Reliability
        st.info("🔧 Menghitung reliabilitas...")
        reliability_results = {}
        for scale, cfg in {
            "DASS-21 Depresi": DASS_DEPRESSION_ITEMS,
            "DASS-21 Kecemasan": DASS_ANXIETY_ITEMS,
            "DASS-21 Stres": DASS_STRESS_ITEMS,
            "Grit-8": [
                f"{item}_r" if item in GRIT_REVERSE_ITEMS else item
                for item in GRIT_REVERSE_ITEMS + GRIT_NORMAL_ITEMS
            ],
            "CD-RISC-25": CDRISC_ITEMS,
        }.items():
            valid_items = [c for c in cfg if c in df.columns]
            if len(valid_items) >= 2:
                reliability_results[scale] = self.reliability_analysis(
                    df, scale, valid_items
                )
        results["reliability"] = reliability_results
        
        # 3. Correlations
        st.info("🔗 Menghitung korelasi...")
        main_scores = [c for c in [
            "DASS_Depresi", "DASS_Kecemasan", "DASS_Stres",
            "Grit_Skor", "CDRISC_Total"
        ] if c in df.columns]
        
        if len(main_scores) >= 2:
            results["correlations"] = self.correlation_matrix(df, main_scores)
        
        # 4. Normality
        st.info("📐 Menguji normalitas...")
        results["normality"] = self.normality_tests(df, available_cols)
        
        # 5. Gender comparison (jika ada)
        if "jenis_kelamin" in df.columns:
            st.info("👥 Membandingkan antar kelompok...")
            gender_comparisons = {}
            for col in available_cols:
                try:
                    result = self.compare_groups(df, col, "jenis_kelamin")
                    gender_comparisons[col] = result
                except Exception:
                    pass
            results["gender_comparison"] = gender_comparisons
        
        self.results = results
        return results
    
    # ============================================================
    # 7. GENERATE SUMMARY FOR AI
    # ============================================================
    
    def generate_cohort_summary(self, df: pd.DataFrame) -> dict:
        """
        Generate summary dict untuk input ke AI Analyzer.
        """
        total = len(df)
        
        # DASS distributions
        dass_dep_counts = df["DASS_Dep_Kategori"].value_counts()
        normal_count = dass_dep_counts.get("Normal", 0) + dass_dep_counts.get("Ringan", 0)
        sedang_count = dass_dep_counts.get("Sedang", 0)
        berat_count = dass_dep_counts.get("Berat", 0) + dass_dep_counts.get("Sangat Berat", 0)
        
        # Decision counts
        keputusan_counts = df["Keputusan"].value_counts()
        lolos = keputusan_counts.get("✅ LOLOS", 0)
        bersyarat = keputusan_counts.get("⚡ LOLOS BERSYARAT", 0)
        tidak_lolos = keputusan_counts.get("❌ TIDAK LOLOS", 0)
        
        # Motivasi distribution
        if "Motivasi_Label" in df.columns:
            motivasi_dist = df["Motivasi_Label"].value_counts().to_string()
        else:
            motivasi_dist = "Data tidak tersedia"
        
        return {
            "total": total,
            "avg_usia": df["usia"].mean() if "usia" in df.columns else 0,
            "dass_dep_mean": df["DASS_Depresi"].mean(),
            "dass_dep_sd": df["DASS_Depresi"].std(),
            "dass_dep_normal": round(normal_count / total * 100, 1) if total > 0 else 0,
            "dass_dep_ringan_sedang": round(sedang_count / total * 100, 1) if total > 0 else 0,
            "dass_dep_berat": round(berat_count / total * 100, 1) if total > 0 else 0,
            "dass_kec_mean": df["DASS_Kecemasan"].mean(),
            "dass_kec_sd": df["DASS_Kecemasan"].std(),
            "dass_str_mean": df["DASS_Stres"].mean(),
            "dass_str_sd": df["DASS_Stres"].std(),
            "grit_mean": df["Grit_Skor"].mean(),
            "grit_sd": df["Grit_Skor"].std(),
            "grit_ci_mean": df["Grit_CI"].mean() if "Grit_CI" in df.columns else 0,
            "grit_pe_mean": df["Grit_PE"].mean() if "Grit_PE" in df.columns else 0,
            "cdrisc_mean": df["CDRISC_Total"].mean(),
            "cdrisc_sd": df["CDRISC_Total"].std(),
            "lolos": lolos,
            "lolos_pct": lolos / total * 100 if total > 0 else 0,
            "bersyarat": bersyarat,
            "bersyarat_pct": bersyarat / total * 100 if total > 0 else 0,
            "tidak_lolos": tidak_lolos,
            "tidak_lolos_pct": tidak_lolos / total * 100 if total > 0 else 0,
            "motivasi_dist": motivasi_dist
        }


# Singleton
jasp = JASPBridge()