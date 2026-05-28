#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

try:
    from .config import DEFAULT_EXAMPLE_URL
    from .utils import atomic_write_json, log_event
    from .ingest_utils import words_to_digits
except (ImportError, ValueError):
    from config import DEFAULT_EXAMPLE_URL
    from utils import atomic_write_json, log_event
    from ingest_utils import words_to_digits

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

def fetch_assets(url: str, out_dir: Path, vid: str) -> tuple[str, str]:
    if out_dir.exists(): shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(" -> Downloading Audio...")
    log_event(vid, "INGEST", "RUNNING", "Downloading video audio stream via YouTube downloader")
    audio_tmpl = str(out_dir / f"{vid}.%(ext)s")
    subprocess.run(["yt-dlp", "-f", "ba", "-o", audio_tmpl, "--no-playlist", url], check=True, capture_output=True)
    audio_files = list(out_dir.glob(f"{vid}.*"))
    audio_file = str(audio_files[0]) if audio_files else ""

    print(" -> Fetching & Cleaning Transcript...")
    log_event(vid, "INGEST", "RUNNING", "Downloading automated English transcript subtitles from YouTube")
    subprocess.run(["yt-dlp", "--write-auto-subs", "--sub-lang", "en", "--skip-download",
                    "-o", str(out_dir / "transcript.%(ext)s"), "--no-playlist", url], check=True, capture_output=True)
    vtt_files = list(out_dir.glob("transcript*.vtt"))
    transcript = ""
    if vtt_files:
        raw_vtt = vtt_files[0].read_text(encoding="utf-8", errors="replace")
        transcript = clean_vtt(raw_vtt)
    return audio_file, transcript

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_EXAMPLE_URL)
    args = ap.parse_args()

    # Pre-log with unknown/url first
    log_event("unknown", "INGEST", "START", f"Starting ingestion pipeline for URL: {args.url}")

    try:
        print("1. Extracting Metadata...")
        out = subprocess.check_output(["yt-dlp", "--dump-single-json", "--no-playlist", "--no-warnings", args.url], text=True)
        meta = json.loads(out)
        title, vid = str(meta.get("title")).strip(), str(meta.get("id")).strip()

        # Re-log with the resolved video ID
        log_event(vid, "INGEST", "RUNNING", f"Extracted metadata: '{title}' (ID: {vid})")

        out_file = Path(__file__).parent / f"{vid}.json"
        asset_dir = Path(__file__).parent / "assets" / vid

        audio_path, raw_transcript = fetch_assets(args.url, asset_dir, vid)

        print("2. Normalizing Numbers...")
        log_event(vid, "INGEST", "RUNNING", "Cleaning raw transcript text and normalizing number sequences")
        record = {
            "url": args.url,
            "title": title,
            "vid": vid,
            "transcript": words_to_digits(raw_transcript),
            "aud_file": str(audio_path),
            "valid": False
        }
        record["valid"] = all(bool(str(record[k]).strip()) for k in ["url", "title", "transcript", "aud_file"])

        atomic_write_json(out_file, record)
        log_event(vid, "INGEST", "DONE", f"Saved ingested video record to {out_file.name}")

        print(f"\nIngest Complete: {out_file}")
        # Print the final JSON so the caller receives the JSON result
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        log_event("error", "INGEST", "FAIL", f"Failed to ingest URL: {str(e)}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    main()
