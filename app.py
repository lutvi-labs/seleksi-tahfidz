# ==============================================================================
# COPYRIGHT (C) 2026 [LUTVI-LABS]. ALL RIGHTS RESERVED.
# Dilarang menyalin, mengubah, atau mendistribusikan kode ini tanpa izin tertulis.
# ==============================================================================

import streamlit as st
import pandas as pd
import random
import string
import time

# --- IMPORTS DARI MODULES ---
from modules.scoring import score_all
from modules.jasp_engine import get_descriptives, get_correlations
from modules.ai_engine import analyze_cohort
from modules.report_individual import show_individual_report
from modules.db_supabase import (
    login_user, 
    register_user, 
    get_all_responses, 
    get_all_users, 
    check_user_already_submitted, 
    save_survey_response
)

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Seleksi Santri Tahfidz",
    page_icon="🕌",
    layout="wide"
)

# --- CSS CUSTOM ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .stProgress .st-bo { background-color: #28a745; }
    .card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'user_logged_in' not in st.session_state:
    st.session_state.user_logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'survey_step' not in st.session_state:
    st.session_state.survey_step = 1
if 'survey_data' not in st.session_state:
    st.session_state.survey_data = {}

# --- HELPER USER SANITIZER ---
def sanitize_user(user):
    if isinstance(user, tuple) and len(user) > 0: user = user[0]
    if isinstance(user, list) and len(user) > 0: user = user[0]
    return user if isinstance(user, dict) else None

# --- FUNGSI HALAMAN PESERTA (LOGIN/REGISTER) ---
def show_login_peserta():
    st.markdown("<div style='text-align: center; margin-bottom: 30px;'>", unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/3588/3588102.png", width=100)
    st.title("Ahlan wa Sahlan! 🕌")
    st.subheader("Portal Seleksi Calon Santri Tahfidz")
    st.write("**Assalamu'alaikum adik-adik yang shalih dan shalihah!** 👋")
    st.write("Yuk, silakan **Login** atau **Buat Akun Baru** dulu ya sebelum mulai.")
    st.markdown("</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔑 Login (Sudah Punya Akun)", "📝 Buat Akun Baru (Peserta Baru)"])

    with tab1:
        with st.form("form_login_peserta"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Masuk ke Halaman Tes", type="primary")

            if submit:
                user = login_user(username, password)
                user = sanitize_user(user)

                if user:
                    if user.get('role') == 'admin':
                        st.error("Akun Admin silakan login di halaman khusus admin!")
                    else:
                        st.session_state.user_logged_in = True
                        st.session_state.current_user = user
                        st.success(f"Alhamdulillah, selamat datang {user.get('nama_lengkap', '')}!")
                        st.rerun()
                else:
                    st.error("Username atau password salah! Silakan periksa kembali ya.")

    with tab2:
        with st.form("form_register_peserta"):
            new_nama = st.text_input("Nama Lengkap Adik*")
            new_username = st.text_input("Username (Buat nama unik tanpa spasi, contoh: ahmad123)*")
            new_password = st.text_input("Password (Buat password yang mudah diingat)*", type="password")
            new_email = st.text_input("Email Orang Tua / Pembimbing (Boleh dikosongkan)")
            submit_reg = st.form_submit_button("Daftar Akun Baru", type="primary")

            if submit_reg:
                if not new_nama or not new_username or not new_password:
                    st.error("Nama Lengkap, Username, dan Password harus diisi ya!")
                else:
                    reg_result = register_user(new_username, new_password, new_nama, new_email)
                    if reg_result:
                        st.success("Hore! Akun berhasil dibuat. Silakan klik Tab 'Login' di sebelah kiri untuk masuk.")
                    else:
                        st.error("Waduh, username ini sudah dipakai teman yang lain. Coba ganti yang lain ya.")

# --- FUNGSI HALAMAN SURVEI (RAMAH ANAK & ISLAMI) ---
def show_survey():
    if not st.session_state.user_logged_in:
        show_login_peserta()
        return

    user = sanitize_user(st.session_state.current_user)
    if not user:
        st.error("Sesi telah berakhir. Silakan login kembali.")
        st.session_state.clear()
        st.rerun()
        return

    if check_user_already_submitted(user['id']):
        st.success(f"Alhamdulillah, {user.get('nama_lengkap', '')}! Kamu sudah selesai mengerjakan semua tugas.")
        st.info("Jawabanmu sudah tersimpan dengan aman. Semoga hasilnya yang terbaik. Baarakallahu fiik!")
        if st.button("Logout / Keluar"):
            st.session_state.clear()
            st.rerun()
        return

    col1, col2 = st.columns([4, 1])
    with col1:
        st.header(f"Bismillah, Semangat {user.get('nama_lengkap', '')}! ✨")
        st.caption("Jawablah semua pertanyaan di bawah ini dengan jujur sesuai isi hatimu. Tidak ada jawaban yang salah kok!")
    with col2:
        if st.button("Keluar (Logout)", key="btn_logout_peserta"):
            st.session_state.clear()
            st.rerun()

    step = st.session_state.survey_step
    total_steps = 7

    if step <= total_steps:
        st.progress(step / total_steps)

    # ------------------ STEP 1: DATA DIRI ------------------
    if step == 1:
        st.subheader("Langkah 1 dari 7: Data Diri")
        with st.form("step1"):
            jk = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            usia = st.number_input("Umur Berapa Tahun Sekarang?", min_value=8, max_value=25, value=11)
            hp = st.text_input("Nomor WA (Milik Kamu / Orang Tua)")
            asal = st.text_input("Asal Sekolah / SD / MI / SMP")
            
            if st.form_submit_button("Lanjut ke Pertanyaan Berikutnya ➡️"):
                st.session_state.survey_data.update({
                    "nama": user.get('nama_lengkap', ''), "jenis_kelamin": jk, "usia": usia, "no_hp": hp, "asal_sekolah": asal
                })
                st.session_state.survey_step = 2
                st.rerun()

    # ------------------ STEP 2: DS-21 ------------------
    elif step == 2:
        st.subheader("Langkah 2 dari 7: Perasaan Sehari-hari (DS-21)")
        st.info("Pilihlah seberapa SERING kamu merasakan hal-hal berikut dalam 1 minggu terakhir:")
        
        options_dass = {"Tidak Pernah": 0, "Kadang-kadang": 1, "Sering": 2, "Hampir Setiap Hari": 3}
        questions_dass = {
            "dass_d1": "Saya merasa masa depan saya kurang menyenangkan atau menyedihkan.",
            "dass_d2": "Saya sering merasa sedih dan murung tanpa alasan yang jelas.",
            "dass_d3": "Saya merasa sulit untuk gembira atau menikmati permainan/kegiatan.",
            "dass_d4": "Saya merasa tidak bertenaga dan cepat sekali lelah.",
            "dass_d5": "Saya merasa tidak bersemangat melakukan hal yang biasanya saya sukai.",
            "dass_d6": "Saya merasa diri saya tidak sepintar atau seberharga teman-teman lain.",
            "dass_d7": "Saya merasa hidup saya membosankan dan tidak ada gunanya.",
            "dass_a1": "Mulut saya sering terasa sangat kering saat merasa takut atau deg-degan.",
            "dass_a2": "Saya sering merasa sulit bernapas atau ngos-ngosan padahal tidak sedang berolahraga.",
            "dass_a3": "Tangan atau tubuh saya sering gemetar (misalnya saat ditunjuk guru/ustaz).",
            "dass_a4": "Saya takut tiba-tiba merasa panik dan bingung di depan orang banyak.",
            "dass_a5": "Saya pernah merasa ingin pingsan atau sangat lemas saat ketakutan.",
            "dass_a6": "Jantung saya sering berdebar-debar kencang padahal sedang duduk biasa.",
            "dass_a7": "Saya sering merasa takut tiba-tiba tanpa ada alasan yang jelas.",
            "dass_s1": "Saya merasa sulit untuk santai atau beristirahat dengan tenang.",
            "dass_s2": "Saya gampang kaget atau terlalu cepat marah untuk hal-hal kecil.",
            "dass_s3": "Saya gampang merasa lelah karena terlalu banyak khawatir atau deg-degan.",
            "dass_s4": "Saya gampang merasa gelisah dan tidak bisa duduk tenang.",
            "dass_s5": "Saya merasa susah sekali untuk tenang jika sedang ada masalah.",
            "dass_s6": "Saya gampang kesal kalau harus menunggu atau ada hal yang mengganggu.",
            "dass_s7": "Saya gampang tersinggung atau marah jika disentil teman/orang lain."
        }

        with st.form("step2"):
            ans = {}
            for key, q_text in questions_dass.items():
                ans[key] = st.radio(q_text, list(options_dass.keys()), horizontal=True, key=f"radio_{key}")
                st.markdown("---")
            if st.form_submit_button("Lanjut ke Bagian Berikutnya ➡️"):
                for k, v in ans.items(): st.session_state.survey_data[k] = options_dass[v]
                st.session_state.survey_step = 3
                st.rerun()

    # ------------------ STEP 3: GS-8 ------------------
    elif step == 3:
        st.subheader("Langkah 3 dari 7: Semangat & Ketekunan (GS-8)")
        st.info("Pilihlah seberapa SETUJU kamu dengan kalimat-kalimat di bawah ini:")
        
        options_gs = {"Sangat Tidak Setuju": 1, "Kurang Setuju": 2, "Netral / Kadang-kadang": 3, "Setuju": 4, "Sangat Setuju": 5}
        questions_gs = {
            "gs1": "Saya sering ganti-ganti hobi atau cita-cita baru, lalu cepat bosan dengan yang lama.",
            "gs2": "Kalau saya gagal atau mendapat nilai jelek, saya tidak menyerah dan mau mencoba lagi.",
            "gs3": "Perhatian saya gampang terganggu oleh mainan, HP, atau hal lain saat sedang belajar/mengaji.",
            "gs4": "Saya anak yang rajin dan selalu berusaha menyelesaikan tugas sampai tuntas.",
            "gs5": "Saya gampang bosan kalau harus melakukan hal yang sama dalam waktu yang lama.",
            "gs6": "Saya selalu fokus dan bersungguh-sungguh pada hal yang sedang saya kerjakan.",
            "gs7": "Hal-hal yang saya sukai sering berubah-ubah dengan sangat cepat.",
            "gs8": "Saya tetap rajin belajar/menghafal meskipun pelajarannya terasa sulit atau capek."
        }

        with st.form("step3"):
            ans = {}
            for key, q_text in questions_gs.items():
                ans[key] = st.radio(q_text, list(options_gs.keys()), horizontal=True, key=f"radio_{key}")
                st.markdown("---")
            if st.form_submit_button("Lanjut ke Bagian Berikutnya ➡️"):
                for k, v in ans.items(): st.session_state.survey_data[k] = options_gs[v]
                st.session_state.survey_step = 4
                st.rerun()

    # ------------------ STEP 4: CR-25 ------------------
    elif step == 4:
        st.subheader("Langkah 4 dari 7: Ketahanan Mental (CR-25)")
        st.info("Pilihlah seberapa SETUJU kamu dengan kalimat-kalimat ini berdasarkan sifat aslimu:")
        
        options_cr = {
            "Sangat Tidak Setuju": 0, "Kurang Setuju": 1, "Netral / Kadang-kadang": 2, "Setuju": 3, "Sangat Setuju": 4
        }
        questions_cr = {
            "cdrisc1": "Saya bisa dengan mudah menyesuaikan diri jika harus pindah kelas, pindah sekolah, atau bertemu teman baru.",
            "cdrisc2": "Saya punya teman dekat atau keluarga yang selalu siap mendengarkan saat saya ada masalah.",
            "cdrisc3": "Saya percaya Allah akan selalu membantu dan melindungi saya saat saya dalam kesulitan.",
            "cdrisc4": "Saya bisa menenangkan diri saya sendiri saat merasa sedih, takut, atau marah.",
            "cdrisc5": "Setelah mengalami masa sulit, gagal, atau sakit, saya bisa cepat bangkit dan ceria lagi.",
            "cdrisc6": "Saya tetap bisa tersenyum atau melihat sisi lucunya meskipun sedang menghadapi masalah.",
            "cdrisc7": "Menghadapi kesulitan atau hukuman justru membuat saya belajar menjadi anak yang lebih kuat.",
            "cdrisc8": "Saya tidak gampang terpuruk; saya cepat bersemangat lagi setelah kecewa.",
            "cdrisc9": "Saya yakin setiap kejadian tidak enak yang saya alami pasti ada hikmah atau kebaikan dari Allah.",
            "cdrisc10": "Saya selalu berusaha sekuat tenaga dan memberikan yang terbaik dalam setiap hal yang saya kerjakan.",
            "cdrisc11": "Saya sangat yakin bisa mencapai target hafalan Al-Qur'an jika saya terus berusaha keras.",
            "cdrisc12": "Meskipun hafalan atau tugas yang saya kerjakan rasanya sangat berat, saya tidak mau menyerah.",
            "cdrisc13": "Saya selalu tahu harus minta tolong ke siapa (orang tua/ustaz) jika sedang bingung atau ada masalah.",
            "cdrisc14": "Saya tetap bisa berpikir tenang meskipun sedang diuji atau dinilai oleh ustaz/guru.",
            "cdrisc15": "Saya berani mengambil keputusan sendiri dalam hal-hal kecil sehari-hari tanpa harus selalu disuruh.",
            "cdrisc16": "Saya tidak gampang putus asa atau merasa diri saya bodoh hanya karena gagal satu kali.",
            "cdrisc17": "Saya menganggap diri saya sebagai anak yang tangguh, kuat, dan pantang menyerah.",
            "cdrisc18": "Saya berani melakukan hal yang benar (jujur) meskipun rasanya takut atau sulit.",
            "cdrisc19": "Saya yakin pada kemampuan saya untuk menyelesaikan tugas-tugas hafalan yang diberikan oleh ustaz.",
            "cdrisc20": "Saya punya cita-cita dan impian yang sangat jelas (misalnya menjadi hafidz 30 juz).",
            "cdrisc21": "Saya merasa bisa membagi dan mengatur waktu belajar, mengaji, dan bermain saya sendiri.",
            "cdrisc22": "Saya justru merasa semangat kalau diberi tantangan atau hafalan ayat baru yang lebih panjang.",
            "cdrisc23": "Saya ikhlas dan mau mengorbankan waktu bermain saya demi meraih cita-cita menghafal Al-Qur'an.",
            "cdrisc24": "Saya merasa sangat bangga pada diri sendiri saat berhasil menyelesaikan tugas dengan baik.",
            "cdrisc25": "Saya yakin dengan banyak berdoa dan berusaha, Allah pasti memberikan jalan keluar terbaik."
        }

        with st.form("step4"):
            ans = {}
            for key, q_text in questions_cr.items():
                ans[key] = st.radio(q_text, list(options_cr.keys()), horizontal=True, key=f"radio_{key}")
                st.markdown("---")
            if st.form_submit_button("Lanjut ke Bagian Berikutnya ➡️"):
                for k, v in ans.items(): st.session_state.survey_data[k] = options_cr[v]
                st.session_state.survey_step = 5
                st.rerun()

    # ------------------ STEP 5: TES MEMORI MV-10 (COUNTDOWN TIMER 15 DETIK) ------------------
    elif step == 5:
        st.subheader("Langkah 5 dari 7: Tes Daya Ingat (MV-10)")

        if 'memori_started' not in st.session_state:
            st.session_state.memori_started = False
        if 'memori_finished' not in st.session_state:
            st.session_state.memori_finished = False

        if not st.session_state.memori_finished:
            st.warning("⚠️ **Petunjuk:** Klik tombol di bawah untuk melihat 10 kata. Kamu hanya punya waktu **15 detik** untuk menghafalnya sebelum kata-katanya hilang!")
            
            if not st.session_state.memori_started:
                if st.button("⏱️ Mulai Hafalkan 10 Kata (15 Detik)", type="primary"):
                    st.session_state.memori_started = True
                    st.rerun()
            else:
                placeholder = st.empty()
                progress_bar = st.progress(1.0)
                words_text = "Alquran — Masjid — Hafalan — Pahala — Surga — Doa — Ustadz — Sabar — Ikhlas — Amal"
                
                # Loop Countdown 15 detik
                for i in range(15, -1, -1):
                    placeholder.markdown(f"""
                    <div style='text-align: center; background-color: #e9ecef; padding: 25px; border-radius: 12px; font-size: 24px; font-weight: bold; letter-spacing: 1px; color: #0f5132;'>
                    {words_text}
                    <br><br>
                    <span style='color: #dc3545; font-size: 18px;'>⏱️ Sisa waktu menghafal: {i} detik!</span>
                    </div>
                    """, unsafe_allow_html=True)
                    progress_bar.progress(i / 15.0)
                    time.sleep(1)
                
                placeholder.empty()
                progress_bar.empty()
                st.session_state.memori_finished = True
                st.rerun()
        else:
            st.success("🔒 Waktu 15 detik telah habis! 10 Kata telah disembunyikan. Tuliskan kata yang kamu ingat di bawah ini:")
            with st.form("step5"):
                jawaban = st.text_area("Tuliskan kata-kata yang berhasil kamu ingat (pisahkan dengan spasi atau koma):", height=120)
                if st.form_submit_button("Lanjut ke Bagian Berikutnya ➡️"):
                    st.session_state.survey_data['memori_jawaban'] = jawaban
                    # Reset state untuk penggunaan berikutnya
                    st.session_state.memori_started = False
                    st.session_state.memori_finished = False
                    st.session_state.survey_step = 6
                    st.rerun()

    # ------------------ STEP 6: RB-5 ------------------
    elif step == 6:
        st.subheader("Langkah 6 dari 7: Kuesioner Kejujuran (RB-5)")
        st.info("Jawablah dengan jujur ya, Allah Maha Mengetahui dan Melihat segala yang kita lakukan:")
        
        options_rb = {"Tidak Pernah": 0, "Pernah": 1}
        questions_rb = {
            "rb1": "Pernahkah kamu mengambil barang atau uang milik orang lain tanpa izin?",
            "rb2": "Pernahkah kamu dengan sengaja merusak barang sekolah, fasilitas umum, atau milik teman?",
            "rb3": "Pernahkah kamu menyakiti diri sendiri (seperti menggores kulit/memukul tembok) saat sangat marah atau sedih?",
            "rb4": "Pernahkah kamu membolos sekolah atau tidak masuk mengaji tanpa alasan yang jelas?",
            "rb5": "Pernahkah kamu berkelahi secara fisik dengan sengaja untuk menyakiti teman?"
        }

        with st.form("step6"):
            ans = {}
            for key, q_text in questions_rb.items():
                ans[key] = st.radio(q_text, list(options_rb.keys()), horizontal=True, key=f"radio_{key}")
                st.markdown("---")
            if st.form_submit_button("Lanjut ke Bagian Terakhir ➡️"):
                for k, v in ans.items(): st.session_state.survey_data[k] = options_rb[v]
                st.session_state.survey_step = 7
                st.rerun()

    # ------------------ STEP 7: MOTIVASI & SUBMIT ------------------
    elif step == 7:
        st.subheader("Langkah 7 dari 7: Cita-cita & Motivasi")
        with st.form("step7"):
            motivasi = st.text_area("Terakhir, ceritakan secara singkat ya, kenapa sih kamu ingin banget menjadi seorang Hafidz/Hafidzah 30 Juz Al-Qur'an?", height=150)
            
            st.info("Bismillah, periksa lagi hatimu dan niatkan karena Allah Ta'ala sebelum klik tombol di bawah ini ya.")
            if st.form_submit_button("Selesai & Kirim Semua Jawaban 🚀", type="primary"):
                st.session_state.survey_data['motivasi'] = motivasi
                sukses = save_survey_response(user['id'], user['username'], st.session_state.survey_data)
                
                if sukses:
                    st.session_state.survey_step = 8
                    st.rerun()
                else:
                    st.error("Waduh, koneksi terputus saat menyimpan data. Silakan klik tombol kirim sekali lagi.")

    # ------------------ STEP 8: SELESAI (ISLAMI) ------------------
    elif step == 8:
        st.balloons()
        st.markdown("<h2 style='text-align: center; color: #28a745;'>Alhamdulillah! Masya Allah! 🌟</h2>", unsafe_allow_html=True)
        st.success(f"Hebat sekali, {user.get('nama_lengkap', '')}! Kamu sudah menyelesaikan semua tugas dan pertanyaan dengan sangat baik.")
        
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #dee2e6;'>
            <p style='font-size: 18px;'>Semoga Allah SWT senantiasa memberikan kemudahan kepadamu, menjaga keikhlasan niatmu, dan mengabulkan cita-citamu untuk memberikan mahkota kemuliaan bagi kedua orang tuamu kelak di surga.</p>
            <h4 style='color: #0d6efd;'>Baarakallahu fiik! (Semoga Allah memberkahimu)</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.info("Sekarang kamu boleh klik tombol di bawah ini untuk keluar. Jangan lupa doakan kedua orang tuamu hari ini ya!")
        if st.button("🚪 Keluar dan Selesai (Logout)", type="primary"):
            st.session_state.clear()
            st.rerun()

# --- FUNGSI HALAMAN ADMIN DASHBOARD (SIDEBAR NAVIGATION) ---
def show_dashboard():
    # ============ SIDEBAR KIRI ============
    with st.sidebar:
        st.markdown("## 🕌 Panel Admin")
        st.caption("Sistem Seleksi Tahfidz 30 Juz")
        st.markdown("---")

        menu = st.radio(
            "Navigasi Menu",
            options=[
                "🎛️ Dashboard",
                "📋 Laporan Individual",
                "📈 Analisis JASP",
                "🤖 AI Report Angkatan",
                "👥 Data User",
                "📂 Database",
                "⚙️ Simulasi & Upload"
            ],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### 🔗 Link Cepat")
        st.markdown("**Portal Peserta:**")
        # Link relatif agar otomatis cocok di localhost maupun Streamlit Cloud
        st.code("?page=survey", language=None)
        st.caption("Tambahkan `?page=survey` di akhir URL aplikasi Anda.")

        st.markdown("---")
        if st.button("🚪 Logout Admin", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

    # ============ KONTEN UTAMA ============
    st.markdown(
        "<h1 style='margin-bottom:0;'>📊 Sistem Seleksi Santri Tahfidz</h1>"
        "<p style='color:#64748b; margin-top:4px;'>Dashboard Admin • Target 30 Juz &lt; 3 Tahun</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    responses = get_all_responses()
    users = get_all_users()

    # Jika belum ada data survei
    if not responses:
        st.warning("⚠️ Belum ada peserta yang mengisi survei.")
        if users:
            st.info(f"Total user terdaftar di sistem: **{len(users)}**")
            df_users = pd.DataFrame(users)
            st.dataframe(
                df_users[['id', 'username', 'nama_lengkap', 'email', 'role', 'sudah_mengerjakan', 'created_at']],
                use_container_width=True
            )

        st.markdown("---")
        st.subheader("⚙️ Simulasi Data Cepat")
        st.write("Gunakan tombol ini untuk mengisi dashboard dengan data uji coba.")
        if st.button("🚀 Generate 5 Data Simulasi", type="primary"):
            generate_dummy_data()
        return

    # Proses scoring
    processed_data = []
    for r in responses:
        raw_dict = r['data']
        scored = score_all(raw_dict)
        scored['id_response'] = r['id']
        scored['username'] = r['username']
        scored['waktu_submit'] = r['submitted_at']
        processed_data.append(scored)

    df = pd.DataFrame(processed_data)
    df = df.loc[:, ~df.columns.duplicated()]

    # ============ ROUTING MENU ============
    if menu == "🎛️ Dashboard":
        st.subheader("Ringkasan Hasil Seleksi")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Peserta Tes", len(df))
        col2.metric("Lolos Murni", len(df[df['Keputusan'] == 'LOLOS']))
        col3.metric("Lolos Bersyarat", len(df[df['Keputusan'] == 'LOLOS BERSYARAT']))
        col4.metric("Tidak Lolos", len(df[df['Keputusan'] == 'TIDAK LOLOS']))

        c1, c2 = st.columns(2)
        with c1:
            import plotly.express as px
            fig_pie = px.pie(
                df, names='Keputusan', title='Proporsi Hasil Seleksi Santri', color='Keputusan',
                color_discrete_map={
                    'LOLOS': '#28a745',
                    'LOLOS BERSYARAT': '#ffc107',
                    'TIDAK LOLOS': '#dc3545'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            fig_scatter = px.scatter(
                df, x='Grit_Score', y='CDRISC_Score', color='Keputusan',
                hover_data=['nama'], title='Peta Ketangguhan Santri (Semangat vs Resiliensi)'
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.subheader("Ranking Peserta (Confidence Score)")
        top_df = df.sort_values(by='Confidence', ascending=False)
        st.dataframe(
            top_df[['nama', 'Confidence', 'Keputusan', 'DASS_Kategori_Depresi', 'Grit_Kategori', 'CDRISC_Kategori']],
            use_container_width=True
        )

    elif menu == "📋 Laporan Individual":
        show_individual_report(df)

    elif menu == "📈 Analisis JASP":
        st.subheader("Analisis Statistik Standar JASP")
        desc_df = get_descriptives(df)
        st.dataframe(desc_df, use_container_width=True)
        st.markdown("#### Matriks Korelasi Pearson (Pingouin)")
        corr_df = get_correlations(df)
        if corr_df is not None:
            st.dataframe(corr_df, use_container_width=True)
        else:
            st.info("Data belum cukup untuk menghitung korelasi.")

    elif menu == "🤖 AI Report Angkatan":
        st.subheader("Laporan Psikologis AI (Google Gemini)")
        st.write("AI akan menganalisis tren kesehatan mental dan ketahanan santri secara keseluruhan.")
        if st.button("Mulai Analisis AI Angkatan", type="primary"):
            with st.spinner("AI sedang membaca dan menganalisis data santri..."):
                report = analyze_cohort(df)
                st.markdown(
                    f"<div class='card' style='background:white;padding:24px;border-radius:12px;"
                    f"border:1px solid #e2e8f0;'>{report}</div>",
                    unsafe_allow_html=True
                )

    elif menu == "👥 Data User":
        st.subheader("Daftar Akun Terdaftar")
        if users:
            df_users = pd.DataFrame(users)
            st.dataframe(
                df_users[['id', 'username', 'nama_lengkap', 'email', 'role', 'sudah_mengerjakan', 'created_at']],
                use_container_width=True
            )
        else:
            st.info("Belum ada user terdaftar.")

    elif menu == "📂 Database":
        st.subheader("Unduh Raw Data Database")
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Database CSV",
            data=csv,
            file_name="database_seleksi_tahfidz.csv",
            mime="text/csv"
        )

    elif menu == "⚙️ Simulasi & Upload":
        st.header("⚙️ Simulasi & Upload Data Offline")
        colA, colB = st.columns(2)

        with colA:
            st.subheader("1. Generate Data Uji Coba")
            st.write("Klik tombol ini untuk membuat 5 peserta simulasi secara instan.")
            if st.button("🚀 Generate 5 Data Simulasi", type="primary"):
                generate_dummy_data()

        with colB:
            st.subheader("2. Upload Data CSV Manual")
            template_cols = ['nama', 'jenis_kelamin', 'usia', 'asal_sekolah']
            for i in range(1, 8):
                template_cols.extend([f'dass_d{i}', f'dass_a{i}', f'dass_s{i}'])
            for i in range(1, 9):
                template_cols.append(f'gs{i}')
            for i in range(1, 26):
                template_cols.append(f'cdrisc{i}')
            template_cols.append('memori_jawaban')
            for i in range(1, 6):
                template_cols.append(f'rb{i}')

            df_template = pd.DataFrame(columns=template_cols)
            csv_template = df_template.to_csv(index=False).encode('utf-8')

            st.download_button(
                "📥 Download Format Template CSV",
                data=csv_template,
                file_name="template_upload.csv",
                mime="text/csv"
            )

            uploaded_file = st.file_uploader("Upload CSV Hasil Tes Offline", type=['csv'])
            if uploaded_file is not None:
                if st.button("Proses Upload File CSV"):
                    with st.spinner("Mengunggah data..."):
                        try:
                            df_upload = pd.read_csv(uploaded_file)
                            sukses_count = 0
                            for index, row in df_upload.iterrows():
                                rand_suffix = ''.join(random.choices(string.digits, k=4))
                                uname = f"csv_{rand_suffix}"
                                user_data = register_user(
                                    uname, "123456", row.get('nama', f'User CSV {rand_suffix}')
                                )
                                user_data = sanitize_user(user_data)
                                if user_data:
                                    uid = user_data['id']
                                    payload = row.to_dict()
                                    payload = {
                                        k: (0 if pd.isna(v) and isinstance(v, (int, float))
                                            else ("" if pd.isna(v) else v))
                                        for k, v in payload.items()
                                    }
                                    save_survey_response(uid, uname, payload)
                                    sukses_count += 1
                            st.success(f"Berhasil mengunggah {sukses_count} data!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal memproses file CSV: {e}")
def generate_dummy_data():
    with st.spinner("Sedang membuat 5 sampel peserta simulasi..."):
        for i in range(5):
            rand_suffix = ''.join(random.choices(string.digits, k=4))
            uname = f"sim_{rand_suffix}"
            nama = f"Santri Simulasi {rand_suffix}"
            user_data = register_user(uname, "123456", nama)
            user_data = sanitize_user(user_data)
            if user_data:
                uid = user_data['id']
                payload = {
                    "nama": nama, "usia": random.randint(10, 13), "jenis_kelamin": random.choice(["Laki-laki", "Perempuan"]),
                    "asal_sekolah": f"SDIT / SMPIT {random.randint(1,5)}",
                    "memori_jawaban": random.choice(["alquran masjid hafalan pahala surga", "alquran doa ustadz sabar ikhlas", "masjid pahala surga amal"]),
                    "motivasi": "Ingin memberikan mahkota cahaya untuk kedua orang tua di surga."
                }
                for j in range(1, 8):
                    payload[f'dass_d{j}'] = random.choices([0, 1, 2, 3], weights=[65, 20, 10, 5])[0]
                    payload[f'dass_a{j}'] = random.choices([0, 1, 2, 3], weights=[65, 20, 10, 5])[0]
                    payload[f'dass_s{j}'] = random.choices([0, 1, 2, 3], weights=[65, 20, 10, 5])[0]
                for j in range(1, 9): payload[f'gs{j}'] = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 40, 25])[0]
                for j in range(1, 26): payload[f'cdrisc{j}'] = random.choices([0, 1, 2, 3, 4], weights=[5, 10, 20, 40, 25])[0]
                for j in range(1, 6): payload[f'rb{j}'] = random.choices([0, 1], weights=[95, 5])[0]
                save_survey_response(uid, uname, payload)
        st.success("Berhasil! 5 Data peserta simulasi telah dibuat.")
        st.rerun()

def main():
    query_params = st.query_params
    page = query_params.get("page", [""])[0] if isinstance(query_params.get("page", ""), list) else query_params.get("page", "")

    if page == "survey":
        show_survey()
    else:
        if st.session_state.admin_logged_in:
            show_dashboard()
        else:
            st.markdown("<div style='text-align: center; margin-bottom: 20px;'>", unsafe_allow_html=True)
            st.image("https://cdn-icons-png.flaticon.com/512/9069/9069153.png", width=90)
            st.title("Login Admin Seleksi Tahfidz")
            st.markdown("</div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                with st.form("admin_login"):
                    username = st.text_input("Username Admin")
                    password = st.text_input("Password Admin", type="password")
                    submit = st.form_submit_button("Masuk Dashboard Admin", type="primary")

                    if submit:
                        if username == "admin":
                            user = login_user(username, password)
                            user = sanitize_user(user)
                            if user and user.get('role') == 'admin':
                                st.session_state.admin_logged_in = True
                                st.rerun()
                            else: st.error("Password Admin salah!")
                        else: st.error("Username ini bukan akun Admin!")

if __name__ == "__main__":
    main()