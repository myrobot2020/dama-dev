#!/usr/bin/env python3
import argparse
import json
import urllib.request
import re
from pathlib import Path

try:
    from .utils import atomic_write_json
except (ImportError, ValueError):
    from utils import atomic_write_json

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:0.5b-instruct"

def call_ollama(prompt):
    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1}
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw_response = json.loads(resp.read().decode("utf-8"))["response"]
            clean_json = re.sub(r'```json\n?|\n?```', '', raw_response).strip()
            return json.loads(clean_json)
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    ap.add_argument("--model", type=str, default=DEFAULT_MODEL)
    args = ap.parse_args()

    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    print(f"Generating minimal practice JSONs for {len(files)} files...")

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        commentary = data.get("commentary", "").strip()
        if not commentary:
            continue

        sutta_id = data.get("sutta_id")
        vid = data.get("vid")
        sutta_name_en = data.get("sutta_name_en")

        # Preserve or fetch timestamps
        aud_start = "00:00"
        aud_end = "00:00"
        if "practice" in data and "audio_range" in data["practice"]:
            aud_start, aud_end = data["practice"]["audio_range"]
        else:
            aud_start = data.get("aud_start") or "00:00"
            aud_end = data.get("aud_end") or "00:00"

        prompt = f"""Task: Create one MCQ from this text.
Text: "{commentary[:1500]}"

Output JSON:
{{
  "question": "question text",
  "options": ["choice 1", "choice 2", "choice 3", "choice 4"],
  "correct_idx": 0,
  "source_text": "verbatim quote"
}}"""

        print(f"  -> Generating MCQ for {path.name}...")
        mcq_data = call_ollama(prompt)

        if not mcq_data or "question" not in mcq_data:
            print(f"    [!] Failed to generate MCQ for {path.name}")
            continue

        # Minimal structure as requested
        minimal_data = {
            "sutta_id": sutta_id,
            "vid": vid,
            "sutta_name_en": sutta_name_en,
            "commentary": commentary,
            "practice": {
                "question": mcq_data["question"],
                "options": mcq_data["options"],
                "correct_idx": mcq_data["correct_idx"],
                "source_text": mcq_data.get("source_text", ""),
                "audio_range": [aud_start, aud_end]
            }
        }

        atomic_write_json(path, minimal_data)
        print(f"    [OK] Updated {path.name}")

if __name__ == "__main__":
    main()
