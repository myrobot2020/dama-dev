#!/usr/bin/env python3
"""Identify suttas within the transcript and map to VTT timestamps."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from codex.utils import atomic_write_json


def words_to_digits(text: str) -> str:
    """Standard normalization: Converts number words to digits."""
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
    text = re.sub(r'(\d+)\s+point\s+(\d+)', r'\1.\2', text, flags=re.IGNORECASE)
    text = re.sub(r'(\.\d+)\s+point\s+(\d+)', r'\1.\2', text, flags=re.IGNORECASE)
    for _ in range(3):
        text = re.sub(r'(\d+)\s*\.\s*(\d+)', r'\1.\2', text)
        text = re.sub(r'(\d+)\s+(\d+)', r'\1\2', text)
    return text


def format_timestamp(seconds: float) -> str:
    """Converts seconds to MM:SS format."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02}:{s:02}"


def parse_vtt_timestamp(ts_str: str) -> float:
    """Parses VTT timestamp into seconds."""
    parts = ts_str.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return 0.0


def get_vtt_blocks(vtt_path: Path) -> list[dict]:
    """Parses VTT and normalizes text for matching."""
    if not vtt_path.exists():
        return []
    content = vtt_path.read_text(encoding="utf-8", errors="replace")
    block_pattern = re.compile(
        r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3}).*?\n(.*?)(?=\n\n|\n\d{2}:|\Z)",
        re.DOTALL,
    )
    blocks = []
    for start, end, text in block_pattern.findall(content):
        clean_text = re.sub(r"<[^>]+>", "", text).strip().replace("\n", " ")
        blocks.append({
            "start": parse_vtt_timestamp(start),
            "end": parse_vtt_timestamp(end),
            "text": words_to_digits(clean_text)
        })
    return blocks


def identify_suttas_regex(transcript: str) -> list[dict]:
    """Identifies suttas by looking for decimal IDs like 4.20.199."""
    pattern = re.compile(r"(\b\d+(?:\.\d+)+\b)")
    matches = list(pattern.finditer(transcript))
    suttas = []
    for i, match in enumerate(matches):
        sid = match.group(1)
        start_pos = match.start()
        end_pos = matches[i+1].start() if i + 1 < len(matches) else len(transcript)
        suttas.append({
            "suttaid": sid,
            "sutta": transcript[start_pos:end_pos].strip()
        })
    return suttas


def map_suttas_to_timestamps(suttas: list[dict], vtt_blocks: list[dict]) -> list[dict]:
    """Maps identified sutta segments back to VTT timestamps."""
    results = []
    for s in suttas:
        sid = s.get("suttaid")
        text_segment = s.get("sutta", "")
        start_time = 0.0

        anchor = text_segment[:15].lower()
        for b in vtt_blocks:
            bt = b["text"].lower()
            if str(sid) in bt or anchor in bt:
                start_time = b["start"]
                break

        results.append({
            "suttaid": sid,
            "sutta": text_segment,
            "audio start": format_timestamp(start_time),
            "audio end": ""
        })

    for i in range(len(results)):
        if i + 1 < len(results):
            results[i]["audio end"] = results[i+1]["audio start"]
        elif vtt_blocks:
            results[i]["audio end"] = format_timestamp(vtt_blocks[-1]["end"])

    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=Path(__file__).parent / "starter.json")
    args = ap.parse_args()

    if not args.input.exists():
        return 1

    obj = json.loads(args.input.read_text(encoding="utf-8"))
    transcript = obj.get("text", "")
    audiolocation = obj.get("audiolocation") or obj.get("audio")

    vtt_blocks = []
    if audiolocation:
        vtt_files = list(Path(audiolocation).parent.glob("*.vtt"))
        if vtt_files:
            vtt_blocks = get_vtt_blocks(vtt_files[0])

    print("Identifying suttas using regex...")
    identified = identify_suttas_regex(transcript)
    suttas = map_suttas_to_timestamps(identified, vtt_blocks)

    output = {
        "url": obj.get("url"),
        "title": obj.get("title"),
        "text": transcript,
        "suttas": suttas,
        "audio": audiolocation,
        "valid": bool(suttas)
    }

    atomic_write_json(args.input, output)
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
