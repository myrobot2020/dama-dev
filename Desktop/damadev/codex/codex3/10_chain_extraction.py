#!/usr/bin/env python3
import argparse
import json
import urllib.request
from pathlib import Path

try:
    from .utils import atomic_write_json
    from ..prompts import CHAIN_EXTRACTION_PROMPT
except (ImportError, ValueError):
    from utils import atomic_write_json
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from prompts import CHAIN_EXTRACTION_PROMPT

DEFAULT_MODEL = "qwen2.5:14b"
OLLAMA_URL = "http://localhost:11434/api/generate"

def call_ollama(prompt):
    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0},
        "system": "You are a Buddhist text analyzer. Return valid JSON only."
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            outer = json.loads(resp.read().decode("utf-8"))
            return json.loads(outer.get("response", "{}"))
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    args = ap.parse_args()
    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    print(f"Extracting doctrinal chains for {len(files)} files...")

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sutta_text = data.get("sutta", "")
        commentary_text = data.get("commentary", "")
        sid = data.get("sutta_id", "5.0")

        # Calculate target count from Book number (e.g., AN 5.9.89 -> 5)
        try:
            target_count = int(sid.split('.')[0])
        except:
            target_count = 5

        if not sutta_text: continue

        print(f" -> Analyzing {path.name} (Target: {target_count} items)...")
        prompt = CHAIN_EXTRACTION_PROMPT.format(
            sutta=sutta_text,
            commentary=commentary_text,
            target_count=target_count
        )
        res = call_ollama(prompt)

        if res and "chain" in res:
            data["doctrinal_chain"] = res["chain"]
            atomic_write_json(path, data)
            print(f"    [OK] Extracted {len(res['chain'].get('items', []))} items.")

if __name__ == "__main__":
    main()
