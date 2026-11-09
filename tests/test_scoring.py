import unittest
import math

from modules.scoring import score_all


class ScoringTests(unittest.TestCase):
    def base_answers(self):
        answers = {
            "memori_jawaban": "Alquran, Masjid, Hafalan, Pahala, Surga, Doa, Ustadz, Sabar, Ikhlas, Amal",
            "Keputusan": "LOLOS",
            "Confidence": 99
        }
        for index in range(1, 8):
            answers[f"dass_d{index}"] = 0
            answers[f"dass_a{index}"] = 0
            answers[f"dass_s{index}"] = 0
        for index in range(1, 9):
            answers[f"gs{index}"] = 5 if index in {2, 4, 6, 8} else 1
        for index in range(1, 26):
            answers[f"cdrisc{index}"] = 4
        for index in range(1, 6):
            answers[f"rb{index}"] = 0
        return answers

    def test_scoring_returns_readiness_without_admission_decision(self):
        result = score_all(self.base_answers())

        self.assertEqual(result["Skor_Kesiapan_30Juz"], 100.0)
        self.assertEqual(result["Jenis_Santri"], "santri_baru")
        self.assertNotIn("Keputusan", result)
        self.assertNotIn("Confidence", result)

    def test_behavior_responses_do_not_reduce_readiness_index(self):
        answers = self.base_answers()
        baseline = score_all(answers)["Skor_Kesiapan_30Juz"]
        for index in range(1, 6):
            answers[f"rb{index}"] = 1

        self.assertEqual(score_all(answers)["Skor_Kesiapan_30Juz"], baseline)

    def test_memory_score_counts_exact_words_only(self):
        answers = self.base_answers()
        answers["memori_jawaban"] = "Alquran masjidan hafalanku"

        self.assertEqual(score_all(answers)["Memori_Score"], 1)

    def test_additional_memory_tests_are_scored_separately(self):
        answers = self.base_answers()
        answers.update({
            "memory_arabic_answer": "buku\npena\ncahaya\npintu\nair\nrumah\nmasjid\nalquran",
            "memory_ayah_answer": "إِنَّ اللَّهَ مَعَ الصَّابِرِينَ",
            "memory_color_target": ["Merah", "Biru", "Hijau", "Kuning", "Ungu"],
            "memory_color_answer": "Merah, Hijau, Hijau, Kuning, Ungu",
            "memory_sound_target": ["Pendek", "Sedang", "Panjang", "Pendek"],
            "memory_sound_answer": ["Pendek", "Panjang", "Panjang", "Pendek"]
        })

        result = score_all(answers)
        self.assertEqual(result["Memori_Arab_Score"], 8)
        self.assertEqual(result["Memori_Ayat_Score"], 1)
        self.assertEqual(result["Memori_Warna_Score"], 4)
        self.assertEqual(result["Memori_Suara_Score"], 3)

    def test_survey_type_is_preserved(self):
        answers = self.base_answers()
        answers["jenis_santri"] = "santri_aktif"

        result = score_all(answers)
        self.assertEqual(result["Jenis_Santri"], "santri_aktif")
        self.assertTrue(math.isnan(result["Skor_Kesiapan_30Juz"]))


if __name__ == "__main__":
    unittest.main()
