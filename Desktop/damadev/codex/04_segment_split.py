#!/usr/bin/env python3
"""Split identified segments into Sutta and Commentary using local Ollama."""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
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


def ollama_split_commentary(text: str, model: str = "llama3") -> dict:
    """Uses Ollama to split a segment into sutta and commentary."""
    url = "http://localhost:11434/api/generate"
    prompt = f"""
Split the following Dhamma talk segment into the original scripture (sutta) and the teacher's explanation (commentary).
The scripture usually ends with a phrase like "that is the end of the sutta" or "exalted one said this".

Text:
{text}

Return ONLY a JSON object with two keys: "sutta" and "commentary".
"""
    data = {"model": model, "prompt": prompt, "stream": False, "format": "json"}
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            raw_response = res_body.get("response", "")

            # Robust JSON extraction
            json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = json.loads(raw_response)

            # Ensure values are strings
            for key in ["sutta", "commentary"]:
                val = result.get(key, "")
                if isinstance(val, list):
                    result[key] = " ".join(map(str, val))
                else:
                    result[key] = str(val)
            return result
    except Exception as e:
        print(f"Ollama error: {e}")
        return {"sutta": text, "commentary": ""}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=Path(__file__).parent / "starter.json")
    ap.add_argument("--model", type=str, default="llama3")
    args = ap.parse_args()

    if not args.input.exists():
        return 1

    obj = json.loads(args.input.read_text(encoding="utf-8"))
    suttas = obj.get("suttas", [])
    audiolocation = obj.get("audio") or obj.get("audiolocation")

    vtt_blocks = []
    if audiolocation:
        vtt_files = list(Path(audiolocation).parent.glob("*.vtt"))
        if vtt_files:
            vtt_blocks = get_vtt_blocks(vtt_files[0])

    for s in suttas:
        segment_text = s.get("sutta", "")
        sid = s.get("suttaid")

        print(f"Splitting {sid} using Ollama...")
        split = ollama_split_commentary(segment_text, args.model)

        s["sutta"] = split.get("sutta", segment_text)
        s["commentary"] = split.get("commentary", "")

        # Map commentary start timestamp
        if s["commentary"] and vtt_blocks:
            anchor = s["commentary"][:20].lower()
            sutta_start_s = parse_vtt_timestamp(s.get("audio start", "00:00"))

            for b in vtt_blocks:
                if anchor in b["text"].lower() and b["start"] >= sutta_start_s:
                    s["commentary start"] = format_timestamp(b["start"])
                    break

            if "commentary start" not in s:
                s["commentary start"] = s.get("audio start")
        else:
            s["commentary start"] = s.get("audio start")

    atomic_write_json(args.input, obj)
    print(json.dumps(obj, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
