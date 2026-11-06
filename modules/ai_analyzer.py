"""
ai_analyzer.py — AI-powered analysis & interpretation
Menggunakan OpenAI GPT-4o-mini atau Google Gemini
"""
# ============================================================
# AI PROVIDER ABSTRACTION
# ============================================================

class AIAnalyzer:
    """
    AI-powered analyzer untuk interpretasi hasil tes psikologi.
    Mendukung OpenAI GPT dan Google Gemini.
    """
    
    def __init__(self):
        self.provider = "disabled"
        self.model = "gpt-4o-mini"
        self.temperature = 0.3
        self.max_tokens = 1200
        self.client = None
    
    def configure(self, provider: str, api_key: str = ""):
        """Configure the selected AI provider using the key entered in the UI."""
        self.provider = provider
        self.client = None

        if provider == "openai" and api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        elif provider == "gemini" and api_key:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel("gemini-3.5-flash-lite")
    
    def _call_ai(self, prompt: str) -> str:
        """Panggil AI model dengan prompt."""
        if not self.client:
            return "⚠️ AI tidak tersedia. Silakan konfigurasi API Key."
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content or ""
            
            elif self.provider == "gemini":
                response = self.client.generate_content(
                    f"{SYSTEM_PROMPT}\n\n{prompt}"
                )
                return response.text
        
        except Exception as e:
            return f"❌ Error AI: {str(e)}"
    
    # ============================================================
    # INDIVIDUAL ANALYSIS
    # ============================================================
    
    def analyze_individual(self, row: dict) -> str:
        """
        Analisis mendalam untuk satu calon santri.
        
        Args:
            row: dict berisi semua skor santri
        
        Returns:
            str: Interpretasi naratif dari AI
        """
        prompt = f"""
Analisis profil psikologis calon santri tahfidz berikut untuk program 
menghafal 30 juz Al-Qur'an dalam waktu kurang dari 3 tahun:

## DATA SANTRI
- Nama: {row.get('nama_lengkap', 'N/A')}
- Usia: {row.get('usia', 'N/A')} tahun
- Jenis Kelamin: {row.get('jenis_kelamin', 'N/A')}

## SKOR DASS-21
- Depresi: {row.get('DASS_Depresi', 'N/A')} ({row.get('DASS_Dep_Kategori', 'N/A')})
- Kecemasan: {row.get('DASS_Kecemasan', 'N/A')} ({row.get('DASS_Kec_Kategori', 'N/A')})
- Stres: {row.get('DASS_Stres', 'N/A')} ({row.get('DASS_Str_Kategori', 'N/A')})

## SKOR GRIT-8
- Skor Total: {row.get('Grit_Skor', 'N/A')}/5.0 ({row.get('Grit_Kategori', 'N/A')})
- Consistency of Interest: {row.get('Grit_CI', 'N/A')}
- Perseverance of Effort: {row.get('Grit_PE', 'N/A')}

## SKOR CD-RISC-25
- Skor Total: {row.get('CDRISC_Total', 'N/A')}/100 ({row.get('CDRISC_Kategori', 'N/A')})

## MOTIVASI
- Tipe: {row.get('Motivasi_Tipe', 'N/A')}
- Label: {row.get('Motivasi_Label', 'N/A')}

## CONFIDENCE SCORE
- {row.get('Confidence_Score', 'N/A')}/100

## KEPUTUSAN SISTEM
- {row.get('Keputusan', 'N/A')}

---

Berikan analisis dalam format berikut:

### 1. RINGKASAN PROFIL
(2-3 kalimat ringkasan profil psikologis)

### 2. KEKUATAN
(Bullet points kekuatan yang mendukung keberhasilan tahfidz)

### 3. AREA PERHATIAN
(Bullet points area yang perlu diperhatikan/diwaspadai)

### 4. REKOMENDASI
(Rekomendasi spesifik: diterima/ditolak/bersyarat, dan langkah selanjutnya)

### 5. CATATAN UNTUK MUSYRIF/PEMBIMBING
(Tips spesifik jika santri ini diterima)
"""
        return self._call_ai(prompt)
    
    # ============================================================
    # BATCH ANALYSIS (COHORT-LEVEL)
    # ============================================================
    
    def analyze_cohort(self, df_summary: dict) -> str:
        """
        Analisis level kohort: tren, distribusi, dan rekomendasi umum.
        
        Args:
            df_summary: dict berisi statistik deskriptif seluruh kohort
        
        Returns:
            str: Analisis kohort
        """
        prompt = f"""
Analisis kohort calon santri tahfidz (program 30 juz < 3 tahun):

## STATISTIK KOHORT
- Total Pendaftar: {df_summary['total']}
- Rata-rata Usia: {df_summary['avg_usia']:.1f} tahun

## DISTRIBUSI DASS-21
- Depresi: Mean={df_summary['dass_dep_mean']:.1f}, SD={df_summary['dass_dep_sd']:.1f}
  - Normal: {df_summary['dass_dep_normal']}%
  - Ringan-Sedang: {df_summary['dass_dep_ringan_sedang']}%
  - Berat-Sangat Berat: {df_summary['dass_dep_berat']}%
- Kecemasan: Mean={df_summary['dass_kec_mean']:.1f}, SD={df_summary['dass_kec_sd']:.1f}
- Stres: Mean={df_summary['dass_str_mean']:.1f}, SD={df_summary['dass_str_sd']:.1f}

## DISTRIBUSI GRIT
- Mean: {df_summary['grit_mean']:.2f}, SD: {df_summary['grit_sd']:.2f}
- CI (Consistency): {df_summary['grit_ci_mean']:.2f}
- PE (Perseverance): {df_summary['grit_pe_mean']:.2f}

## DISTRIBUSI CD-RISC
- Mean: {df_summary['cdrisc_mean']:.1f}, SD: {df_summary['cdrisc_sd']:.1f}

## HASIL SELEKSI
- Lolos: {df_summary['lolos']} ({df_summary['lolos_pct']:.1f}%)
- Lolos Bersyarat: {df_summary['bersyarat']} ({df_summary['bersyarat_pct']:.1f}%)
- Tidak Lolos: {df_summary['tidak_lolos']} ({df_summary['tidak_lolos_pct']:.1f}%)

## DISTRIBUSI MOTIVASI
{df_summary['motivasi_dist']}

---

Berikan analisis kohort meliputi:
1. **Profil Umum Kohort**: Bagaimana kualitas kohort ini secara keseluruhan?
2. **Temuan Menarik**: Pola-pola yang perlu diperhatikan
3. **Perbandingan Subskala**: Apakah ada ketimpangan antara Grit CI vs PE?
4. **Red Flags Kohort**: Apakah ada tren yang mengkhawatirkan?
5. **Rekomendasi untuk Pesantren**: Saran persiapan berdasarkan profil kohort
6. **Estimasi Keberhasilan**: Berdasarkan data ini, berapa persen yang 
   diperkirakan bisa menyelesaikan 30 juz dalam < 3 tahun?
"""
        return self._call_ai(prompt)
    
    # ============================================================
    # RISK ASSESSMENT
    # ============================================================
    
    def assess_risk(self, row: dict) -> dict:
        """
        Asesmen risiko otomatis tanpa AI (rule-based).
        Lebih cepat dan tidak butuh API.
        
        Returns:
            dict: {level, flags, recommendations}
        """
        risk_level = "LOW"
        flags = []
        recommendations = []
        
        # DASS checks
        if row.get("DASS_Depresi", 0) >= 11:
            risk_level = "HIGH"
            flags.append("Depresi berat")
            recommendations.append("Wajib wawancara klinis dengan psikolog")
        elif row.get("DASS_Depresi", 0) >= 7:
            if risk_level == "LOW":
                risk_level = "MEDIUM"
            flags.append("Depresi sedang")
            recommendations.append("Perlu eksplorasi lebih lanjut di wawancara")
        
        if row.get("DASS_Kecemasan", 0) >= 8:
            risk_level = "HIGH"
            flags.append("Kecemasan berat")
            recommendations.append("Evaluasi kemampuan mengatasi tekanan")
        
        if row.get("DASS_Stres", 0) >= 13:
            risk_level = "HIGH"
            flags.append("Stres berat")
            recommendations.append("Identifikasi sumber stres sebelum masuk pesantren")
        
        # Grit checks
        if row.get("Grit_Skor", 0) < 2.5:
            if risk_level == "LOW":
                risk_level = "MEDIUM"
            flags.append("Grit sangat rendah")
            recommendations.append("Risiko dropout tinggi — perlu pendampingan intensif")
        
        if row.get("Grit_CI", 0) < 2.0:
            flags.append("Konsistensi minat sangat rendah")
            recommendations.append("Cenderung berpindah-pindah minat")
        
        # CD-RISC checks
        if row.get("CDRISC_Total", 0) < 35:
            if risk_level == "LOW":
                risk_level = "MEDIUM"
            flags.append("Resiliensi sangat rendah")
            recommendations.append("Rentan breakdown saat menghadapi kesulitan hafalan")
        
        # Motivasi checks
        if row.get("Motivasi_Skor", 3) <= 2:
            flags.append("Motivasi ekstrinsik dominan")
            recommendations.append("Pastikan keputusan menghafal bukan paksaan orang tua")
        
        # Riwayat konseling
        if row.get("riwayat_konseling", 0) == 1:  # "Ya, sedang aktif"
            flags.append("Sedang menjalani konseling/terapi")
            recommendations.append("Koordinasi dengan terapis sebelum penerimaan")
        
        return {
            "level": risk_level,
            "flags": flags,
            "recommendations": recommendations,
            "flag_count": len(flags)
        }


# ============================================================
# SYSTEM PROMPT (untuk AI)
# ============================================================
SYSTEM_PROMPT = """
Anda adalah seorang psikolog klinis senior yang berpengalaman dalam 
asesmen psikologi pendidikan, khususnya untuk program tahfidz Al-Qur'an intensif.

Tugas Anda:
1. Menginterpretasikan hasil tes psikologi (DASS-21, Grit Scale, CD-RISC-25)
2. Memberikan analisis yang AKURAT, BERIMBANG, dan ACTIONABLE
3. Menggunakan bahasa Indonesia yang profesional namun mudah dipahami
4. Mempertimbangkan konteks pesantren dan program hafalan intensif

Prinsip Anda:
- TIDAK membuat diagnosis klinis (hanya skrining)
- Selalu merekomendasikan tindak lanjut profesional untuk kasus berisiko tinggi
- Mempertimbangkan faktor budaya dan religius
- Skor rendah bukan vonis — selalu berikan rekomendasi konstruktif
- Prioritaskan keselamatan dan kesejahteraan calon santri

Format output: Gunakan Markdown dengan heading yang jelas.
"""

# Singleton
ai_analyzer = AIAnalyzer()