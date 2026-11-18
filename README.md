[readme.md](https://github.com/user-attachments/files/35054748/readme.md)

**TakeNamer** is a cross-platform desktop utility designed for film productions, editors, and sound recordists. It automatically transcribes the audio slate (clapperboard announcement) at the beginning of video and audio clips using OpenAI's Whisper (`faster-whisper`) and renames the files based on spoken Scene, Shot, and Take numbers.

---

## Features

* **Automated Audio Slate Transcription:** Extracts the first few seconds of audio from media files and transcribes spoken slates locally using `faster-whisper`.
* **Customizable Matching & Renaming Patterns:** Define custom regex/keyword patterns (e.g., `Szene $n, Shot $n, Take $n`) and output naming schemes (e.g., `$n1-$n2-$n3.file_ending`).
* **Smart Number & Phonetic Parsing:** Automatically converts spoken German and English number words (e.g., *"zwo"*, *"eins A"*, *"three"*) into standardized digits and handles common transcription variations.
* **Non-Destructive Workflow:** Copies and renames files into a designated output directory (defaulting to `/renamed`) so original camera/audio files remain untouched.
* **Interactive Review Table:** Inspect transcripts, verify extracted metadata, and manually adjust Scene, Shot, or Take numbers directly within the PyQt6 interface.
* **Cross-Platform Support:** Runs natively on Linux, macOS, and Windows.

---

## Prerequisites

Before running TakeNamer, ensure you have the following installed on your system:

1. **Python 3.10 or higher**
2. **FFmpeg** (Must be installed and accessible via your system `PATH`):
   * **Linux (Arch/Debian/Ubuntu):** `sudo pacman -S ffmpeg` or `sudo apt install ffmpeg`
   * **macOS:** `brew install ffmpeg`
   * **Windows:** `winget install Gyan.FFmpeg` (or download from [ffmpeg.org](https://ffmpeg.org/) and add the `bin` folder to your System Environment Variables).

---

## Installation & Quick Start

TakeNamer includes automated startup scripts that create a virtual environment (`.venv`), install all required Python dependencies from `requirements.txt`, and launch the application.

### Linux & macOS
1. Open a terminal in the project directory.
2. Make the startup script executable and run it:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

### Windows
1. Open Command Prompt or PowerShell in the project directory (or double-click the file in File Explorer):
   ```cmd
   start.bat
   ```

*(Note: On the first run, downloading the selected Whisper model will require an active internet connection. Once cached, TakeNamer works completely offline.)*

---

## Usage Guide

1. **Select Folder:** Click **Select Folder** and choose the directory containing your raw video or audio clips (`.mp4`, `.mov`, `.mxf`, `.mkv`, `.avi`, `.wav`, `.aac`, etc.).
2. **Configure Settings (Top Bar):**
   * **Renaming Regex:** The spoken pattern to listen for. Default: `Szene $n, Shot $n, Take $n`
   * **Whisper Model:** Choose between speed (`tiny`, `base`) and higher accuracy (`small`, `medium`, `large-v3`, `turbo`).
   * **Time to Scan (s):** How many seconds from the start of each clip to analyze (default: `15` seconds).
3. **Configure Output (Bottom Bar):**
   * **Output Folder:** Where renamed copies will be saved (`$d` represents the source folder; defaults to `$d/renamed`).
   * **Output Filename Format:** How files should be named (`$n1` = Scene, `$n2` = Shot, `$n3` = Take, `.file_ending` = original extension).
4. **Process Clips:** Click **Rename** to begin batch transcription and copying.
5. **Manual Corrections:** Click any row in the table to view its full transcript. If a number was misheard, edit the **Scene**, **Shot**, or **Take** fields at the bottom and click **Update** to rename the output file immediately.

---

## Project Structure

* `main.py` — Main PyQt6 GUI application logic and table management.
* `classes.py` — Background worker thread (`TakeRenameWorker`) handling batch processing and progress signals.
* `scripts.py` — Core utilities for FFmpeg audio extraction, Whisper transcription, regex parsing, and number conversion.
* `main.ui` — Qt Designer XML layout file.
* `style.qss` — Qt stylesheet for UI spacing and margins.
* `requirements.txt` — Python package dependencies.
* `start.sh` / `start.bat` — Cross-platform environment setup and launch scripts.e.md…]()
