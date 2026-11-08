import pandas as pd
import re

def score_dass21(df):
    d_items = [f'dass_d{i}' for i in range(1, 8)]
    a_items = [f'dass_a{i}' for i in range(1, 8)]
    s_items = [f'dass_s{i}' for i in range(1, 8)]

    df['DASS_Depresi'] = df[[c for c in d_items if c in df.columns]].sum(axis=1) * 2
    df['DASS_Anxiety'] = df[[c for c in a_items if c in df.columns]].sum(axis=1) * 2
    df['DASS_Stress'] = df[[c for c in s_items if c in df.columns]].sum(axis=1) * 2

    def cat_dep(x):
        if x <= 9: return 'Normal'
        elif x <= 13: return 'Ringan'
        elif x <= 20: return 'Sedang'
        elif x <= 27: return 'Berat'
        else: return 'Sangat Berat'

    def cat_anx(x):
        if x <= 7: return 'Normal'
        elif x <= 9: return 'Ringan'
        elif x <= 14: return 'Sedang'
        elif x <= 19: return 'Berat'
        else: return 'Sangat Berat'

    def cat_str(x):
        if x <= 14: return 'Normal'
        elif x <= 18: return 'Ringan'
        elif x <= 25: return 'Sedang'
        elif x <= 33: return 'Berat'
        else: return 'Sangat Berat'

    df['DASS_Kategori_Depresi'] = df['DASS_Depresi'].apply(cat_dep)
    df['DASS_Kategori_Anxiety'] = df['DASS_Anxiety'].apply(cat_anx)
    df['DASS_Kategori_Stress'] = df['DASS_Stress'].apply(cat_str)
    return df

def score_grit8(df):
    gs_cols = [f'gs{i}' for i in range(1, 9)]
    rev_items = ['gs1', 'gs3', 'gs5', 'gs7']
    
    df_grit = df[[c for c in gs_cols if c in df.columns]].copy()
    for col in rev_items:
        if col in df_grit.columns:
            df_grit[col] = 6 - df_grit[col]
    
    df['Grit_Score'] = df_grit.mean(axis=1) if not df_grit.empty else 0.0

    def cat_grit(x):
        if x >= 4.5: return 'Sangat Tinggi'
        elif x >= 3.5: return 'Tinggi'
        elif x >= 2.5: return 'Sedang'
        else: return 'Rendah'

    df['Grit_Kategori'] = df['Grit_Score'].apply(cat_grit)
    return df

def score_cdrisc25(df):
    cr_cols = [f'cdrisc{i}' for i in range(1, 26)]
    df['CDRISC_Score'] = df[[c for c in cr_cols if c in df.columns]].sum(axis=1)

    def cat_cr(x):
        if x >= 80: return 'Sangat Tinggi'
        elif x >= 65: return 'Tinggi'
        elif x >= 50: return 'Sedang'
        else: return 'Rendah'

    df['CDRISC_Kategori'] = df['CDRISC_Score'].apply(cat_cr)
    return df

def score_tahap_lanjut(df):
    memory_words = {
        "alquran", "masjid", "hafalan", "pahala", "surga",
        "doa", "ustadz", "sabar", "ikhlas", "amal"
    }
    
    def count_memori(val):
        if not isinstance(val, str): return 0
        recalled_words = set(re.findall(r"\w+", val.casefold()))
        return len(memory_words.intersection(recalled_words))

    if 'memori_jawaban' in df.columns:
        df['Memori_Score'] = df['memori_jawaban'].apply(count_memori)
    else:
        df['Memori_Score'] = 0

    rb_cols = [f'rb{i}' for i in range(1, 6)]
    df['RB_Score'] = df[[c for c in rb_cols if c in df.columns]].sum(axis=1)
    return df

def calculate_readiness_score(row):
    dep = row.get('DASS_Depresi', 0)
    anx = row.get('DASS_Anxiety', 0)
    str_s = row.get('DASS_Stress', 0)
    grit = row.get('Grit_Score', 0)
    cdrisc = row.get('CDRISC_Score', 0)
    mem = row.get('Memori_Score', 0)
    dass_health = max(0, 100 - ((dep + anx + str_s) / 126.0 * 100))
    grit_pct = (grit / 5.0) * 100
    cdrisc_pct = (cdrisc / 100.0) * 100
    mem_pct = (mem / 10.0) * 100

    readiness = (dass_health * 0.25) + (grit_pct * 0.25) + (cdrisc_pct * 0.3) + (mem_pct * 0.2)
    readiness = max(0.0, min(100.0, readiness))

    return round(readiness, 1)

def score_all(data_input):
    # Aman menangani masukan Dict maupun DataFrame
    if isinstance(data_input, dict):
        df = pd.DataFrame([data_input])
        is_single_dict = True
    else:
        df = data_input.copy()
        is_single_dict = False

    df = score_dass21(df)
    df = score_grit8(df)
    df = score_cdrisc25(df)
    df = score_tahap_lanjut(df)

    df['Jenis_Santri'] = (
        df.get('jenis_santri', pd.Series('santri_baru', index=df.index))
        .fillna('santri_baru')
        .astype(str)
        .str.strip()
        .str.lower()
    )
    df['Skor_Kesiapan_30Juz'] = df.apply(calculate_readiness_score, axis=1)
    df.loc[df['Jenis_Santri'] == 'santri_aktif', 'Skor_Kesiapan_30Juz'] = float('nan')
    df = df.drop(columns=['Keputusan', 'Confidence'], errors='ignore')

    if is_single_dict:
        return df.iloc[0].to_dict()
    return df