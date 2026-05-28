#!/usr/bin/env python3
import argparse
import json
import urllib.request
import re
from pathlib import Path

try:
    from .utils import atomic_write_json, log_event
except (ImportError, ValueError):
    from utils import atomic_write_json, log_event

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.2:3b"

def call_ollama(text):
    prompt = f"""You are a mechanical text splitter. Split the following Dhamma talk transcript into two parts.
DO NOT SUMMARIZE. DO NOT ADD NEW WORDS. Use the EXACT verbatim text from the input.

1. 'sutta': The literal recitation of the scripture (usually starts with 'monks...', 'there are these 5...', etc.)
2. 'commentary': The teacher's explanation and stories that follow the recitation.

Text to split:
{text}

Return ONLY a JSON object with keys "sutta" and "commentary". Ensure all input text is preserved in one of the two fields."""

    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0}
    }
    try:
        data_enc = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data_enc, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            outer = json.loads(resp.read().decode("utf-8"))
            return json.loads(outer.get("response", "{}"))
    except Exception as e:
        print(f"    [!] AI Error: {e}")
        return {"sutta": text, "commentary": ""}

def heuristic_split(text):
    """Fallback split if AI fails or returns junk."""
    markers = [
        r"\bso in this\b",
        r"\bthis is the end of the sutta\b",
        r"\bnow the commentary\b",
        r"\bthe teacher says\b",
        r"\bmonks\b.*\bso\b"
    ]
    for marker in markers:
        match = re.search(marker, text, re.IGNORECASE)
        if match:
            split_point = match.start()
            return {"sutta": text[:split_point].strip(), "commentary": text[split_point:].strip()}
    return {"sutta": text, "commentary": ""}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    ap.add_argument("--model", type=str, default=DEFAULT_MODEL)
    ap.add_argument("--vid", type=str, help="Only process files for this video ID")
    args = ap.parse_args()

    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    print(f"Splitting {len(files)} files using {args.model}...")
    for path in files:
        if "gt2Se9HmLEs" in path.name: continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        vid = data.get("vid", "unknown")
        if args.vid and vid != args.vid:
            continue

        text = data.get("raw_transcript_block") or data.get("sutta", "")
        if not text: continue

        print(f" -> Splitting {path.name}...")
        log_event(vid, "ALIGN", "START", f"Splitting sutta/commentary for {path.name}")

        try:
            res = call_ollama(text)

            # If AI failed to find commentary, try heuristic
            if not res.get("commentary") or len(res.get("commentary")) < 20:
                print(f"    [?] AI found no commentary, trying heuristic...")
                h_res = heuristic_split(text)
                if h_res.get("commentary"):
                    res = h_res
                    print(f"    [OK] Heuristic split found commentary.")

            # Overwrite with clean split
            data["sutta"] = res.get("sutta", text).strip()
            data["commentary"] = res.get("commentary", "").strip()

            # Remove any old junk
            if "raw_transcript_block" in data: del data["raw_transcript_block"]
            if "segments" in data: del data["segments"]
            data["split_method"] = "llm_split"

            atomic_write_json(path, data)
            log_event(vid, "ALIGN", "DONE", f"Aligned {path.stem}")
            print(f"    -> Done.")
        except Exception as e:
            log_event(vid, "ALIGN", "FAIL", str(e))
            print(f"    -> Failed: {e}")

if __name__ == "__main__":
    main()
