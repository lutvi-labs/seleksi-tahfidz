import math
import re
import struct
import wave
from io import BytesIO


ARABIC_MEMORY_WORDS = [
    "كِتَابٌ", "قَلَمٌ", "نُورٌ", "بَابٌ",
    "مَاءٌ", "بَيْتٌ", "مَسْجِدٌ", "قُرْآنٌ"
]

ARABIC_WORD_MEANINGS = {
    "كتاب": {"buku", "kitab"},
    "قلم": {"pena", "pulpen"},
    "نور": {"cahaya", "sinar"},
    "باب": {"pintu"},
    "ماء": {"air"},
    "بيت": {"rumah"},
    "مسجد": {"masjid"},
    "قران": {"alquran", "quran", "al-quran"}
}
ARABIC_WORD_ALIASES = {
    "كتاب": {"kitab", "kitabun"},
    "قلم": {"qalam", "qalamun"},
    "نور": {"nur", "noor"},
    "باب": {"bab", "baab"},
    "ماء": {"maa", "maaun"},
    "بيت": {"bait", "bayt", "baitun"},
    "مسجد": {"masjid"},
    "قران": {"quran", "qur"}
}

AYAH_ORDER_CHOICES = [
    "مَعَ اللَّهِ إِنَّ الصَّابِرِينَ",
    "إِنَّ الصَّابِرِينَ مَعَ اللَّهِ",
    "إِنَّ الصَّابِرِينَ اللَّهَ مَعَ",
    "إِنَّ اللَّهَ مَعَ الصَّابِرِينَ"
]
AYAH_MEMORY_EXCERPT = "وَاسْتَعِينُوا بِالصَّبْرِ وَالصَّلَاةِ ۚ إِنَّ اللَّهَ مَعَ الصَّابِرِينَ"

COLOR_OPTIONS = ["Merah", "Biru", "Hijau", "Kuning", "Ungu"]
COLOR_HEX = {
    "Merah": "#e53935",
    "Biru": "#1e88e5",
    "Hijau": "#43a047",
    "Kuning": "#fdd835",
    "Ungu": "#8e24aa"
}
COLOR_SHAPES = ["●", "■", "▲", "◆", "★"]
SOUND_OPTIONS = ["Pendek", "Sedang", "Panjang"]
SOUND_DURATIONS = {"Pendek": 0.16, "Sedang": 0.34, "Panjang": 0.56}


def normalize_arabic_words(text):
    text = str(text or "").translate(str.maketrans({
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا"
    }))
    text = re.sub(r"[\u064B-\u065F\u0670\u06D6-\u06ED]", "", text)
    return set(re.findall(r"[\u0621-\u064A]+", text))


def score_arabic_word_meanings(answer):
    correct = 0
    recalled_words = set()
    for line in str(answer or "").splitlines():
        parts = re.split(r"\s*(?:=|:|->|—|–)\s*", line, maxsplit=1)
        if len(parts) != 2:
            continue
        left, right = parts
        left_arabic = normalize_arabic_words(left)
        right_arabic = normalize_arabic_words(right)
        left_latin = set(re.findall(r"[a-z]+", left.casefold()))
        right_latin = set(re.findall(r"[a-z]+", right.casefold()))

        for arabic_word, meanings in ARABIC_WORD_MEANINGS.items():
            if arabic_word in recalled_words:
                continue
            aliases = ARABIC_WORD_ALIASES[arabic_word]
            left_is_word = arabic_word in left_arabic or bool(aliases.intersection(left_latin))
            right_is_word = arabic_word in right_arabic or bool(aliases.intersection(right_latin))
            if left_is_word:
                meaning_arabic, meaning_latin = right_arabic, right_latin
            elif right_is_word:
                meaning_arabic, meaning_latin = left_arabic, left_latin
            else:
                continue
            if meanings.intersection(meaning_arabic | meaning_latin):
                correct += 1
                recalled_words.add(arabic_word)
                break
    return correct


def score_ayah_order(answer):
    return int(answer == AYAH_ORDER_CHOICES[-1])


def score_sequence(answer, target):
    if isinstance(answer, str):
        answer = [value.strip().casefold() for value in re.split(r"[,،\s]+", answer) if value.strip()]
    if not isinstance(answer, (list, tuple)) or not isinstance(target, (list, tuple)):
        return 0
    return sum(
        str(actual).strip().casefold() == str(expected).strip().casefold()
        for actual, expected in zip(answer, target)
    )


def create_sound_sequence_audio(sequence, sample_rate=16000):
    audio_frames = []
    for label in sequence:
        duration = SOUND_DURATIONS[label]
        frame_count = int(sample_rate * duration)
        for frame in range(frame_count):
            envelope = min(1.0, frame / 120, (frame_count - frame) / 120)
            sample = int(9000 * envelope * math.sin(2 * math.pi * 740 * frame / sample_rate))
            audio_frames.append(struct.pack("<h", sample))
        audio_frames.extend([b"\x00\x00"] * int(sample_rate * 0.16))

    audio_buffer = BytesIO()
    with wave.open(audio_buffer, "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(sample_rate)
        audio_file.writeframes(b"".join(audio_frames))
    return audio_buffer.getvalue()
