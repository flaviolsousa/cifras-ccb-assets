#!/usr/bin/env python

"""
Usage:
    python3 src/mp3_duration_scan.py "../mp3" "gen/mp3_duration_scan_output.json"   
"""

import json
import shutil, sys
from pathlib import Path

from mutagen import File as MutagenFile
from pydub import AudioSegment, silence
from tqdm import tqdm

# Parâmetros de detecção
INTRO_MIN_MS      = 5_000     # início da janela onde buscamos silêncio
INTRO_MAX_MS      = 25_000    # fim da janela
MIN_SILENCE_LEN   = 1_000     # ≥ 1 s
SILENCE_THRESH_DB = 16        # consideramos silêncio se volume ≤ (dBFS - 16)

if shutil.which("ffmpeg") is None and not AudioSegment.converter:
    sys.exit(
        "FFmpeg not founded. Install or Configure AudioSegment.converter "
        "before execute the script."
    )

def intro_duration(audio: AudioSegment) -> float:
    silences = silence.detect_silence(
        audio,
        min_silence_len=MIN_SILENCE_LEN,
        silence_thresh=audio.dBFS - SILENCE_THRESH_DB,
    )
    for start_ms, _ in silences:
        if INTRO_MIN_MS <= start_ms <= INTRO_MAX_MS:
            return round(start_ms / 1000.0, 3)
    return 0.0

def analyze_file(path: Path) -> dict:
    print(f"[INFO] Processing {path.absolute()}")
    audio = AudioSegment.from_file(path)
    print(f"[INFO] {path.name} - {audio.channels} channels, {audio.frame_rate} Hz")
    total_duration = round(audio.duration_seconds, 3)
    intro_dur = intro_duration(audio)
    item = {
        "filename": path.name,
        "duration_sec": total_duration,
        "intro_duration_sec": intro_dur,
    }
    print(f"[INFO] {item}")
    return item

def main(folder: str, out_json: str):
    mp3_files = sorted(Path(folder).glob("*.mp3"))
    results = []
    print(f"[INFO] Found {len(mp3_files)} MP3 files in {folder}")
    for mp3 in tqdm(mp3_files, desc="Processing MP3"):
        try:
            results.append(analyze_file(mp3))
            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[WARN] Fail to process {mp3.name}: {e}")

    # with open(out_json, "w", encoding="utf-8") as f:
    #     json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nReady! {len(results)} processed files. Output: {out_json}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python mp3_duration_scan.py <mp3_folder> <json_output>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
