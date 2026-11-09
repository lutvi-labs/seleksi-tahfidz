import unittest
from io import BytesIO

from docx import Document

from modules.report_individual import (
    RADAR_MINIMUM_THRESHOLD,
    build_individual_docx,
    plot_radar_profile,
)
from modules.scoring import score_all


class IndividualReportTests(unittest.TestCase):
    def scored_answers(self, kind):
        answers = {
            "nama": "Contoh Santri",
            "usia": 12,
            "jenis_kelamin": "Perempuan",
            "jenis_santri": kind,
            "memori_jawaban": "Alquran masjid hafalan",
            "motivasi": "Ingin terus belajar",
            "harapan_belajar": "Menambah hafalan"
        }
        for index in range(1, 8):
            answers[f"dass_d{index}"] = 1
            answers[f"dass_a{index}"] = 1
            answers[f"dass_s{index}"] = 1
        for index in range(1, 9):
            answers[f"gs{index}"] = 4
        for index in range(1, 26):
            answers[f"cdrisc{index}"] = 3
        for index in range(1, 6):
            answers[f"rb{index}"] = 0
        if kind == "santri_aktif":
            answers.update({
                "kelas_saat_ini": "2 SMP",
                "lama_mondok_bulan": 18,
                "juz_dikuasai": 5,
                "juz_terjaga": 4,
                "juz_baru_3_bulan": 1,
                "murajaah_menit_per_hari": 45,
                "perasaan_belajar": "Cukup bersemangat",
                "kendala_belajar": "Mengatur waktu"
            })
        return score_all(answers)

    def test_new_student_report_has_readiness_note_and_assessment_charts(self):
        row = self.scored_answers("santri_baru")
        radar = plot_radar_profile(row)
        content = build_individual_docx(row)
        document = Document(BytesIO(content))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]

        self.assertIn("Skor Kesiapan Target 30 Juz", paragraphs)
        self.assertEqual(len(document.inline_shapes), 3)
        self.assertTrue(any("bukan probabilitas" in paragraph for paragraph in paragraphs))
        self.assertEqual(len(radar.data), 2)
        self.assertEqual(radar.data[1].line.dash, "dash")
        self.assertEqual(set(radar.data[1].r), {RADAR_MINIMUM_THRESHOLD})
        self.assertTrue(any("batas minimal referensi" in paragraph for paragraph in paragraphs))

    def test_current_student_report_includes_progress_and_extra_chart(self):
        content = build_individual_docx(self.scored_answers("santri_aktif"))
        document = Document(BytesIO(content))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]

        self.assertIn("Perkembangan Belajar di Pondok", paragraphs)
        self.assertEqual(len(document.inline_shapes), 4)
        self.assertFalse(any("Skor Kesiapan Target 30 Juz" in paragraph for paragraph in paragraphs))


if __name__ == "__main__":
    unittest.main()
