import os
import re
import subprocess
import ffmpeg
import filetype
import sys

from PyQt6.QtWidgets import QApplication, QFileDialog
from pathlib import Path
from faster_whisper import WhisperModel

# Initialize model once so it doesn't reload for every file
#model = WhisperModel("turbo", device="cpu", compute_type="int8")
NUMBER_MAP = {
    "null": "0",
    "eins": "1",
    "ein": "1",
    "eine": "1",
    "one": "1",
    "zwei": "2",
    "zwo": "2",    # Common German audio/film set pronunciation for clarity
    "two": "2",
    "drei": "3",
    "three": "3",
    "vier": "4",
    "four": "4",
    "fünf": "5",
    "five": "5",
    "sechs": "6",
    "six": "6",
    "sieben": "7",
    "seven": "7",
    "acht": "8",
    "eight": "8",
    "neun": "9",
    "nine": "9",
    "zehn": "10",
    "ten": "10",
    "elf": "11",
    "eleven": "11",
    "zwölf": "12",
    "twelve": "12",
    "dreizehn": "13",
    "thirteen": "13",
    "vierzehn": "14",
    "fourteen": "14",
    "fünfzehn": "15",
    "fifteen": "15",
    "sechzehn": "16",
    "sixteen": "16",
    "siebzehn": "17",
    "seventeen": "17",
    "achtzehn": "18",
    "eighteen": "18",
    "neunzehn": "19",
    "nineteen": "19",
    "zwanzig": "20",
    "twenty": "20",
    "einundzwanzig": "21",
    "zweiundzwanzig": "22",
    "dreiundzwanzig": "23",
    "vierundzwanzig": "24",
    "fünfundzwanzig": "25",
    "sechsundzwanzig": "26",
    "siebenundzwanzig": "27",
    "achtundzwanzig": "28",
    "neunundzwanzig": "29",
    "dreißig": "30",
    "thirty": "30",
}


def extract_audio_snippet(video_path, output_audio_path, duration=15):
    """Extracts the first N seconds of audio using FFmpeg to speed up processing."""
    cmd = [
        "ffmpeg", "-y", "-ss", "00:00:00", "-i", str(video_path),
        "-t", str(duration), "-q:a", "0", "-map", "a", str(output_audio_path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0

def transcribe_clip(temp_audio, model):
    try:
        segments, _ = model.transcribe(
            str(temp_audio),
            beam_size=10,
            language="de",
            vad_filter=True,  # Crucial for filtering out set noise, clicks, or the clapperboard clap
            condition_on_previous_text=False,
            initial_prompt=(
            "Filmset Audio-Log. Umgangssprachliche Klappen und Ansagen. "
            "Beispiele: 'Szene vier, Shot drei A, Take eins', 'Take zwei, Szene fünf', "
            "'Moment, noch mal Take drei', 'Äh, Szene zwölf, erster Take'."
            ),
        )
        transcript = " ".join([seg.text for seg in segments])
        transcript = re.sub(r"[^\w\s]", " ", transcript)
        console_log = f'  -> Heard: "{transcript}..." \n'
        print(console_log)
        return transcript, console_log
    except Exception as e:
        print(f"  -> Transcription error: {e}")
        if temp_audio.exists():
            temp_audio.unlink()
        return None, None


def get_regex_pattern(input_pattern=None):
    if not input_pattern:
        input_pattern = "Szene $n, Shot $n, Take $n"

    # Define common Whisper mishearings for film set terminology
    synonyms = {
        r"\bszene\b": r"(?:szene|zene|sene|zähne|szne)",

        # Shot / Take variations
        r"\bshot\b": r"(?:shot|schott|schuss|schot|chod|schod)",
        r"\btake\b": r"(?:take|teik|tek|tack|teck)",
    }

    # Substitute keywords in the template with flexible regex alternation groups
    pattern_to_parse = input_pattern
    for target_word, regex_alt in synonyms.items():
        pattern_to_parse = re.sub(target_word, regex_alt, pattern_to_parse, flags=re.IGNORECASE)

    # Convert placeholders to capture groups allowing optional filler words (und, ähm, der, etc.)
    regex_str = pattern_to_parse.replace("$n", r"([\w]+(?:\s+[a-zA-Z]\b)?)")

    # Split by commas or semicolons if multiple clauses exist in the pattern
    keywords = re.split(r"[,;]\s*", regex_str)
    return keywords

def convert_word_to_digit(val):
    if not val:
        return val

    parts = val.strip().lower().split()
    if not parts:
        return val

    digit = NUMBER_MAP.get(parts[0], parts[0].upper())

    if len(parts) > 1:
        suffix = "".join(parts[1:])
        return f"{digit}{suffix.upper()}"

    return digit

def rename_file(file_path, transcript, input_pattern=None):
    if not transcript:
        return

    text = transcript.lower()
    keywords = get_regex_pattern(input_pattern)

    extracted_values = []

    for keyword in keywords:
        clean_keyword = keyword.strip()

        flexible_keyword = clean_keyword.replace(
        " ", r"\s+(?:(?:und|ähm|der|die|nummer)\s+)*"
        )

        pattern = re.compile(flexible_keyword, re.IGNORECASE)

        match = pattern.search(text)
        print (match)
        if match:
            raw_val = match.group(1)
            converted_val = convert_word_to_digit(raw_val)
            extracted_values.append(converted_val)
            print (raw_val)
            print (converted_val)
        else:
            extracted_values.append(None)

    print(extracted_values)
    return extracted_values

def folder_selection(self):
    folder_path = QFileDialog.getExistingDirectory(
        self,
        caption="Select Folder to Import",
        directory=os.path.expanduser("~")
    )

    if folder_path:
        files, folder_path = process_folder(folder_path)
        return files, folder_path
    else:
        print("Error Folder")
        return None, None

def process_folder(folder_path):
    files = []
    folder_path = Path(folder_path)
    for item in folder_path.iterdir():
        if item.is_file() and is_media_file(item):
            filename = item.name
            files.append(filename)
    print (files)
    return files, folder_path

def is_media_file(file):
    try:

        kind = filetype.guess(file)
        if kind is not None:
            mime = kind.mime
            if mime.startswith('video/') or mime.startswith('audio/'):
                return True

        valid_extensions = {'.mxf', '.mp4', '.mov', '.mkv', '.webm', '.avi'}
        if isinstance(file, (str, Path)) and Path(file).suffix.lower() in valid_extensions:
            return True

        return False
    except Exception:
        return False
