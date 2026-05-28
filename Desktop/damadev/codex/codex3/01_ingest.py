#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
import av
from pathlib import Path

try:
    from .utils import atomic_write_json, log_event
    from .ingest_utils import words_to_digits
except (ImportError, ValueError):
    from utils import atomic_write_json, log_event
    from ingest_utils import words_to_digits

def convert_to_mp3(input_path, output_path):
    """Converts any audio format to MP3 using PyAV (av library)."""
    print(f"    -> Transcoding to MP3: {output_path.name}")
    try:
        container = av.open(str(input_path))
        output = av.open(str(output_path), 'w')
        stream = output.add_stream('mp3', rate=44100)

        for frame in container.decode(audio=0):
            for packet in stream.encode(frame):
                output.mux(packet)
        for packet in stream.encode():
            output.mux(packet)
        output.close()
        return True
    except Exception as e:
        print(f"    [!] Transcode error: {e}")
        return False

def fetch_assets(url: str, out_dir: Path, vid: str) -> tuple[str, str]:
    if out_dir.exists(): shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(" -> Downloading Audio...")
    temp_tmpl = str(out_dir / f"temp_{vid}.%(ext)s")
    subprocess.run(["yt-dlp", "-f", "ba", "-o", temp_tmpl, "--no-playlist", url], check=True, capture_output=True)

    # Find what yt-dlp downloaded
    temp_files = list(out_dir.glob(f"temp_{vid}.*"))
    if not temp_files: return "", ""

    # Convert to final MP3
    final_audio = out_dir / f"{vid}.mp3"
    convert_to_mp3(temp_files[0], final_audio)

    # Cleanup temp file
    temp_files[0].unlink()

    print(" -> Fetching Transcript...")
    subprocess.run(["yt-dlp", "--write-auto-subs", "--sub-lang", "en", "--skip-download",
                    "-o", str(out_dir / "transcript.%(ext)s"), "--no-playlist", url], check=True, capture_output=True)
    vtt_files = list(out_dir.glob("transcript*.vtt"))
    transcript = ""
    if vtt_files:
        from .01_ingest import clean_vtt # Recursion safety
        transcript = clean_vtt(vtt_files[0].read_text(encoding="utf-8", errors="replace"))
    return str(final_audio), transcript

def clean_vtt(vtt_text: str) -> str:
    lines = vtt_text.splitlines()
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line or "-->" in line or line.isdigit() or line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        clean_line = re.sub(r"<[^>]+>", "", line).strip()
        if not clean_line: continue
        if text_lines and clean_line.startswith(text_lines[-1]):
            text_lines[-1] = clean_line
        elif not text_lines or clean_line != text_lines[-1]:
            text_lines.append(clean_line)
    return " ".join(text_lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    args = ap.parse_args()

    try:
        print("1. Extracting Metadata...")
        out = subprocess.check_output(["yt-dlp", "--dump-single-json", "--no-playlist", args.url], text=True)
        meta = json.loads(out)
        title, vid = str(meta.get("title")).strip(), str(meta.get("id")).strip()

        out_file = Path(__file__).parent / f"{vid}.json"
        asset_dir = Path(__file__).parent / "assets" / vid

        audio_path, raw_transcript = fetch_assets(args.url, asset_dir, vid)

        record = {
            "url": args.url,
            "title": title,
            "vid": vid,
            "transcript": words_to_digits(raw_transcript),
            "aud_file": str(audio_path),
            "valid": bool(audio_path and raw_transcript)
        }

        atomic_write_json(out_file, record)
        print(f"\nIngest Complete: {out_file}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
