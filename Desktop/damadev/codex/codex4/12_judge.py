#!/usr/bin/env python3
import argparse
import json
import urllib.request
from pathlib import Path

try:
    from .utils import atomic_write_json, log_event
except (ImportError, ValueError):
    from utils import atomic_write_json, log_event

# We use the 14b model for the judge because it is much "smarter" than the 3b translator
DEFAULT_MODEL = "qwen2.5:14b"
OLLAMA_URL = "http://localhost:11434/api/generate"

import time

def call_judge(data, ja_trans):
    """Asks the 14b model to audit the entire production quality with retry."""
    prompt = f"""
You are a Quality Control (QC) Officer for a Dhamma factory.
Audit the following Sutta package and determine if it meets production standards.

### SOURCE DATA:
Suttacentral Reference: {data.get('sc_text')}
Extracted Sutta: {data.get('sutta')}
Extracted Commentary: {data.get('commentary')}

### TRANSLATION:
Japanese Sutta: {ja_trans.get('sutta')}
Japanese Commentary: {ja_trans.get('commentary')}

### AUDIT CRITERIA:
1. COMMENTARY CHECK: Is the commentary empty or too short (< 50 words)?
2. PRACTICE QUALITY: Grade the teacher's explanation (GOOD, AVERAGE, or BAD) based on relevance to actual meditation/practice.
3. COPYCAT CHECK: Is the "Japanese Sutta" just a copy of the SuttaCentral reference? It should be a fresh translation of the TEACHER'S words.
4. SPLIT LOGIC: Did the extractor correctly separate the Sutta (scripture) from the Commentary (explanation)?
5. SCRIPT: Is it pure Japanese? (No Hindi drift, no English glitches)

Return JSON ONLY:
{{
  "score": (1-10),
  "practice_grade": "GOOD" | "AVERAGE" | "BAD",
  "issues": ["list of specific errors found, or empty"],
  "verdict": "PASS" | "FAIL",
  "reasoning": "Brief explanation of the split logic and quality"
}}
"""
    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0}
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            data_enc = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(OLLAMA_URL, data=data_enc, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as resp:
                outer = json.loads(resp.read().decode("utf-8"))
                return json.loads(outer.get("response", "{}"))
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"    [!] Judge retry {attempt+1}/{max_retries} (Ollama might be busy or down)...")
                time.sleep(5)
                continue
            return {"score": 0, "verdict": "FAIL", "reasoning": f"Ollama Connection Error: {e}"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    ap.add_argument("--vid", type=str, help="Only process files for this video ID")
    args = ap.parse_args()

    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    print(f"QC Audit of {len(files)} files using {DEFAULT_MODEL}...")

    for path in files:
        if "gt2Se9HmLEs" in path.name: continue
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)

        vid = data.get("vid", "unknown")
        if args.vid and vid != args.vid:
            continue

        ja_trans = data.get("translations", {}).get("ja")
        if not ja_trans: continue

        print(f" -> Auditing {data.get('sutta_id')}...")
        log_event(vid, "JUDGE", "START", f"QC Audit of {data.get('sutta_id')}")

        try:
            audit = call_judge(data, ja_trans)
            data["judge_report"] = audit

            # Strict rules for passing
            if audit.get("verdict") == "FAIL" or not data.get("commentary"):
                data["valid"] = False
                log_event(vid, "JUDGE", "FAIL", f"QC Failed: {audit.get('reasoning')}")
                print(f"    [!] FAILED: {audit.get('reasoning')}")
            else:
                data["valid"] = True
                log_event(vid, "JUDGE", "DONE", f"QC Passed: {audit.get('practice_grade')} quality")
                print(f"    [OK] PASSED (Grade: {audit.get('practice_grade')})")

            atomic_write_json(path, data)
        except Exception as e:
            log_event(vid, "JUDGE", "FAIL", str(e))
            print(f"    [FAIL] {e}")

if __name__ == "__main__":
    main()
