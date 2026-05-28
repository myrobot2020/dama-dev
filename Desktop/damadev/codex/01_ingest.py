#!/usr/bin/env python3
"""Ingest a single source URL and emit a minimal normalized JSON record."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from codex.config import DEFAULT_EXAMPLE_URL
from codex.utils import atomic_write_json


def words_to_digits(text: str) -> str:
    """Converts number words to digits and collapses points/sequences."""
    mapping = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
        "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
        "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
        "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30",
        "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
        "eighty": "80", "ninety": "90", "hundred": "100"
    }
    pattern = re.compile(r'\b(' + '|'.join(mapping.keys()) + r')\b', re.IGNORECASE)
    text = pattern.sub(lambda m: mapping[m.group(0).lower()], text)

    # Collapse "point" and handle space-separated digits (e.g., "1 9 9" -> "199")
    text = re.sub(r'(\d+)\s+point\s+(\d+)', r'\1.\2', text, flags=re.IGNORECASE)
    text = re.sub(r'(\.\d+)\s+point\s+(\d+)', r'\1.\2', text, flags=re.IGNORECASE)

    for _ in range(3):
        text = re.sub(r'(\d+)\s*\.\s*(\d+)', r'\1.\2', text)
        text = re.sub(r'(\d+)\s+(\d+)', r'\1\2', text)

    return text


def clean_vtt(vtt_text: str) -> str:
    """Robust VTT cleaning for YouTube auto-subs."""
    lines = vtt_text.splitlines()
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line or "-->" in line or line.isdigit() or line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        clean_line = re.sub(r"<[^>]+>", "", line).strip()
        if not clean_line:
            continue
        if text_lines and clean_line.startswith(text_lines[-1]):
            text_lines[-1] = clean_line
        elif not text_lines or clean_line != text_lines[-1]:
            text_lines.append(clean_line)
    return " ".join(text_lines)


def fetch_assets(url: str, out_dir: Path) -> tuple[str, str]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Audio - Raw (no conversion needed)
    audio_tmpl = str(out_dir / "audio.%(ext)s")
    subprocess.run(["yt-dlp", "-f", "ba", "-o", audio_tmpl, "--no-playlist", url],
                   check=True, capture_output=True)
    audio_files = list(out_dir.glob("audio.*"))
    audio_file = str(audio_files[0]) if audio_files else ""

    # Transcript
    subprocess.run(["yt-dlp", "--write-auto-subs", "--sub-lang", "en", "--skip-download",
                    "-o", str(out_dir / "transcript.%(ext)s"), "--no-playlist", url],
                   check=True, capture_output=True)

    vtt_files = list(out_dir.glob("transcript*.vtt"))
    transcript = ""
    if vtt_files:
        raw_vtt = vtt_files[0].read_text(encoding="utf-8", errors="replace")
        transcript = clean_vtt(raw_vtt)

    return audio_file, transcript


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_EXAMPLE_URL)
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "starter.json")
    args = ap.parse_args()

    # Metadata
    out = subprocess.check_output(["yt-dlp", "--dump-single-json", "--no-playlist", "--no-warnings", args.url], text=True)
    meta = json.loads(out)
    title, vid = str(meta.get("title")).strip(), str(meta.get("id")).strip()

    # Assets
    asset_dir = args.out.parent / "assets" / vid
    audio_path, raw_transcript = fetch_assets(args.url, asset_dir)

    record = {
        "url": args.url,
        "title": title,
        "text": words_to_digits(raw_transcript),
        "audiolocation": str(audio_path),
        "valid": False
    }
    record["valid"] = all(bool(str(record[k]).strip()) for k in ["url", "title", "text", "audiolocation"])

    atomic_write_json(args.out, record)
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
