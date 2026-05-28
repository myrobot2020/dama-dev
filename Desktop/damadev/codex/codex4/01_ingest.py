#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from .utils import atomic_write_json, log_event
    from .ingest_utils import words_to_digits
except (ImportError, ValueError):
    from utils import atomic_write_json, log_event
    from ingest_utils import words_to_digits

def fetch_assets(url: str, out_dir: Path, vid: str) -> tuple[str, str]:
    if out_dir.exists(): shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f" -> Downloading Audio for {vid} (m4a fallback)...")
    log_event(vid, "DOWNLOAD", "START", f"Downloading audio for {vid}")

    try:
        # We remove --extract-audio and --audio-format mp3 to avoid the ffmpeg requirement.
        # We download the best audio format directly (usually m4a or webm).
        subprocess.run([
            sys.executable, "-m", "yt_dlp",
            "-f", "ba",
            "-o", str(out_dir / f"{vid}.%(ext)s"),
            "--no-playlist",
            "--no-warnings",
            url
        ], check=True, capture_output=True)

        # Find what we actually downloaded
        downloaded_files = list(out_dir.glob(f"{vid}.*"))
        final_audio = downloaded_files[0] if downloaded_files else Path("")
        log_event(vid, "DOWNLOAD", "DONE", f"Downloaded {final_audio.name}")
    except Exception as e:
        log_event(vid, "DOWNLOAD", "FAIL", f"Audio download failed: {str(e)[:100]}")
        raise

    print(" -> Fetching Transcript...")
    try:
        subprocess.run([
            sys.executable, "-m", "yt_dlp",
            "--write-auto-subs", "--sub-lang", "en", "--skip-download",
            "-o", str(out_dir / "transcript.%(ext)s"), "--no-playlist", url
        ], check=True, capture_output=True)

        vtt_files = list(out_dir.glob("transcript*.vtt"))
        transcript = ""
        if vtt_files:
            transcript = clean_vtt(vtt_files[0].read_text(encoding="utf-8", errors="replace"))
        return str(final_audio), transcript
    except Exception as e:
        log_event(vid, "TRANSCRIPT", "FAIL", f"Transcript fetch failed: {str(e)[:100]}")
        return str(final_audio), ""

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
        out = subprocess.check_output([
            sys.executable, "-m", "yt_dlp",
            "--dump-single-json", "--no-playlist", args.url
        ], text=True)
        meta = json.loads(out)
        title, vid = str(meta.get("title")).strip(), str(meta.get("id")).strip()

        log_event(vid, "INGEST", "START", title)

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
        log_event(vid, "INGEST", "DONE", f"Saved {out_file.name}")
        print(f"\nIngest Complete: {out_file}")
    except Exception as e:
        v = locals().get("vid", "unknown")
        log_event(v, "INGEST", "FAIL", str(e))
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
