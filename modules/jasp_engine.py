import pandas as pd
import pingouin as pg

def get_descriptives(df):
    score_cols = ["DASS_Depresi", "DASS_Kecemasan", "DASS_Stres", "Grit_Skor", "CDRISC_Total", "Skor_Memori", "Skor_RB", "Confidence"]
    exist = [c for c in score_cols if c in df.columns]
    if not exist: return pd.DataFrame()
    
    desc = df[exist].describe().T
    desc["Median"] = df[exist].median()
    desc["Skewness"] = df[exist].skew()
    desc = desc[["count", "mean", "Median", "std", "min", "max", "Skewness"]]
    desc.columns = ["N", "Mean", "Median", "SD", "Min", "Max", "Skewness"]
    return desc.round(2)

def get_correlations(df):
    score_cols = ["DASS_Depresi", "Grit_Skor", "CDRISC_Total", "Skor_Memori", "Skor_RB", "Confidence"]
    exist = [c for c in score_cols if c in df.columns]
    if len(exist) < 2: return pd.DataFrame()
    
    return df[exist].rcorr(method='pearson', stars=True)