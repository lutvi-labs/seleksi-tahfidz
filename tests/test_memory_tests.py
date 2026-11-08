import unittest
import wave
from io import BytesIO

from modules.memory_tests import (
    AYAH_ORDER_CHOICES,
    count_arabic_words_recalled,
    create_sound_sequence_audio,
    score_ayah_order,
    score_sequence,
)


class AdditionalMemoryTests(unittest.TestCase):
    def test_arabic_words_are_counted_with_or_without_diacritics(self):
        answer = "كتاب نور masjid quran"
        self.assertEqual(count_arabic_words_recalled(answer), 4)

    def test_ayah_order_accepts_only_the_correct_first_verse(self):
        self.assertEqual(score_ayah_order(AYAH_ORDER_CHOICES[0]), 1)
        self.assertEqual(score_ayah_order(AYAH_ORDER_CHOICES[1]), 0)

    def test_color_and_sound_sequences_score_matching_positions(self):
        self.assertEqual(score_sequence(["Merah", "Biru", "Hijau"], ["Merah", "Hijau", "Hijau"]), 2)
        self.assertEqual(score_sequence(["Pendek", "Panjang"], ["Sedang", "Panjang"]), 1)

    def test_sound_sequence_is_a_valid_wav_audio_clip(self):
        content = create_sound_sequence_audio(["Pendek", "Sedang", "Panjang"])
        with wave.open(BytesIO(content), "rb") as audio:
            self.assertEqual(audio.getnchannels(), 1)
            self.assertEqual(audio.getframerate(), 16000)
            self.assertGreater(audio.getnframes(), 0)


if __name__ == "__main__":
    unittest.main()
