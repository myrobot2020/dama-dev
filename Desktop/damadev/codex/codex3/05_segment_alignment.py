#!/usr/bin/env python3
import argparse
import json
import urllib.request
from pathlib import Path

try:
    from .utils import atomic_write_json
except (ImportError, ValueError):
    from utils import atomic_write_json

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.2:3b"

def call_ollama(text):
    prompt = f"""You are a Buddhist text analyzer. Split the following Dhamma talk transcript into two distinct parts:
1. 'sutta': The literal recitation of the scripture (usually starts with 'monks...', 'there are these 5...', etc.)
2. 'commentary': The teacher's explanation and stories that follow the recitation.

Text to split:
{text}

Return ONLY a JSON object with keys "sutta" and "commentary"."""

    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0}
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            outer = json.loads(resp.read().decode("utf-8"))
            return json.loads(outer.get("response", "{}"))
    except Exception as e:
        print(f"    [!] AI Error: {e}")
        return {"sutta": text, "commentary": ""}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    ap.add_argument("--model", type=str, default=DEFAULT_MODEL)
    args = ap.parse_args()

    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    print(f"Splitting {len(files)} files using {args.model}...")
    for path in files:
        if "gt2Se9HmLEs" in path.name: continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Get text from raw block (new ingest) or current sutta field
        text = data.get("raw_transcript_block") or data.get("sutta", "")
        if not text: continue

        print(f" -> Splitting {path.name}...")
        res = call_ollama(text)

        # Overwrite with clean split
        data["sutta"] = res.get("sutta", text).strip()
        data["commentary"] = res.get("commentary", "").strip()

        # Remove any old junk
        if "raw_transcript_block" in data: del data["raw_transcript_block"]
        if "segments" in data: del data["segments"]
        if "split_method" in data: data["split_method"] = "llm_split"

        atomic_write_json(path, data)
        print(f"    -> Done.")

if __name__ == "__main__":
    main()
