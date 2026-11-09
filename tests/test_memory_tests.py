import unittest
import wave
from io import BytesIO

from modules.memory_tests import (
    AYAH_ORDER_CHOICES,
    score_arabic_word_meanings,
    create_sound_sequence_audio,
    score_ayah_order,
    score_sequence,
)


class AdditionalMemoryTests(unittest.TestCase):
    def test_arabic_vocabulary_answers_meanings_in_question_order(self):
        answer = "buku\npena\ncahaya\npintu\nair\nrumah\nmasjid\nalquran"
        self.assertEqual(score_arabic_word_meanings(answer), 8)
        self.assertEqual(score_arabic_word_meanings("buku\ncahaya\nmasjid"), 1)
        self.assertEqual(score_arabic_word_meanings(""), 0)

    def test_ayah_order_accepts_only_correct_choice_at_the_end(self):
        self.assertEqual(score_ayah_order(AYAH_ORDER_CHOICES[-1]), 1)
        self.assertTrue(all(score_ayah_order(choice) == 0 for choice in AYAH_ORDER_CHOICES[:-1]))

    def test_color_and_sound_sequences_score_matching_positions(self):
        self.assertEqual(
            score_sequence("Merah, Hijau, Hijau, Kuning, Ungu", ["Merah", "Biru", "Hijau", "Kuning", "Ungu"]),
            4
        )
        self.assertEqual(
            score_sequence(["Pendek", "Panjang", "Sedang", "Panjang"], ["Sedang", "Panjang", "Sedang", "Panjang"]),
            3
        )

    def test_sound_sequence_is_a_valid_wav_audio_clip(self):
        content = create_sound_sequence_audio(["Pendek", "Sedang", "Panjang"])
        with wave.open(BytesIO(content), "rb") as audio:
            self.assertEqual(audio.getnchannels(), 1)
            self.assertEqual(audio.getframerate(), 16000)
            self.assertGreater(audio.getnframes(), 0)


if __name__ == "__main__":
    unittest.main()
