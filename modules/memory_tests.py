import math
import re
import struct
import wave
from io import BytesIO


ARABIC_MEMORY_WORDS = [
    "كِتَابٌ", "قَلَمٌ", "نُورٌ", "بَابٌ",
    "مَاءٌ", "بَيْتٌ", "مَسْجِدٌ", "قُرْآنٌ"
]

SURAH_AL_IKHLAS = (
    "قُلْ هُوَ اللَّهُ أَحَدٌ\n"
    "اللَّهُ الصَّمَدُ\n"
    "لَمْ يَلِدْ وَلَمْ يُولَدْ\n"
    "وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ"
)

AYAH_ORDER_CHOICES = [
    "قُلْ هُوَ اللَّهُ أَحَدٌ",
    "هُوَ قُلْ اللَّهُ أَحَدٌ",
    "قُلْ اللَّهُ أَحَدٌ هُوَ",
    "أَحَدٌ هُوَ قُلْ اللَّهُ"
]

COLOR_OPTIONS = ["Merah", "Biru", "Hijau", "Kuning", "Ungu"]
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


def count_arabic_words_recalled(answer):
    aliases = [
        {"كتاب", "kitab", "kitabun"},
        {"قلم", "qalam", "qalamun"},
        {"نور", "nur", "noor"},
        {"باب", "bab", "baab"},
        {"ماء", "ما", "maa", "maaun"},
        {"بيت", "bait", "bayt", "baitun"},
        {"مسجد", "masjid"},
        {"قران", "قرآن", "quran", "qur'an"}
    ]
    arabic_answer = normalize_arabic_words(answer)
    latin_answer = set(re.findall(r"[a-z']+", str(answer or "").casefold()))
    return sum(bool(words.intersection(arabic_answer | latin_answer)) for words in aliases)


def score_ayah_order(answer):
    return int(answer == AYAH_ORDER_CHOICES[0])


def score_sequence(answer, target):
    if not isinstance(answer, (list, tuple)) or not isinstance(target, (list, tuple)):
        return 0
    return sum(actual == expected for actual, expected in zip(answer, target))


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
