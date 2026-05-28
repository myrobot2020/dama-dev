#!/usr/bin/env python3
import argparse
import json
import urllib.request
from pathlib import Path

try:
    from .utils import atomic_write_json
except (ImportError, ValueError):
    from utils import atomic_write_json

# We use the 14b model for the judge because it is much "smarter" than the 3b translator
DEFAULT_MODEL = "qwen2.5:14b"
OLLAMA_URL = "http://localhost:11434/api/generate"

def call_judge(en_data, ja_data):
    """Asks the 14b model to audit the translation quality."""
    prompt = f"""
You are an expert Japanese-English Buddhist scholar.
Audit this translation from English to Japanese.

### ORIGINAL ENGLISH:
Sutta: {en_data.get('sutta')}
Commentary: {en_data.get('commentary')}
MCQ: {en_data.get('mcq')}
Correct Answer Quote: {en_data.get('commentarywordsanswer')}

### GENERATED JAPANESE:
Sutta: {ja_data.get('sutta')}
Commentary: {ja_data.get('commentary')}
MCQ: {ja_data.get('mcq')}
Correct Answer Quote: {ja_data.get('commentarywordsanswer')}

### CRITERIA:
1. ACCURACY: Is the meaning preserved?
2. TERMINOLOGY: Are Buddhist terms (Mindfulness, Buddha, Sangha) correct?
3. MCQ COHERENCE: Does the Japanese MCQ answer actually exist in the Japanese commentary?
4. REPETITION: Is there any looping or glitching in the Japanese?
5. SCRIPT: Is it pure Japanese? (No Hindi, No unexpected English)

Return JSON ONLY:
{{
  "score": (1-10),
  "issues": ["list of specific errors found, or empty"],
  "verdict": "PASS" or "FAIL",
  "reasoning": "Brief explanation of why it passed or failed"
}}
"""
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
        with urllib.request.urlopen(req, timeout=300) as resp:
            outer = json.loads(resp.read().decode("utf-8"))
            return json.loads(outer.get("response", "{}"))
    except Exception as e:
        return {"score": 0, "verdict": "FAIL", "reasoning": str(e)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    args = ap.parse_args()

    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    print(f"Judging {len(files)} translations using {DEFAULT_MODEL}...")

    for path in files:
        if "gt2Se9HmLEs" in path.name: continue
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)

        ja_trans = data.get("translations", {}).get("ja")
        if not ja_trans: continue

        print(f" -> Auditing {data.get('sutta_id')}...")

        # We compare the English fields against the Japanese translations
        audit = call_judge(data, ja_trans)

        data["judge_report"] = audit

        # If the judge says FAIL, we mark the whole record as invalid
        if audit.get("verdict") == "FAIL":
            data["valid"] = False
            print(f"    [!] FAILED: {audit.get('reasoning')}")
        else:
            print(f"    [OK] PASSED (Score: {audit.get('score')}/10)")

        atomic_write_json(path, data)

if __name__ == "__main__":
    main()
