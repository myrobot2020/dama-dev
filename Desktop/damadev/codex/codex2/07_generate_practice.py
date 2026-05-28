#!/usr/bin/env python3
import argparse
import json
import urllib.request
from pathlib import Path

try:
    from .utils import atomic_write_json
    from ..prompts import PRACTICE_GENERATION_SYSTEM_PROMPT, PRACTICE_GENERATION_PROMPT_TEMPLATE
except (ImportError, ValueError):
    from utils import atomic_write_json
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from prompts import PRACTICE_GENERATION_SYSTEM_PROMPT, PRACTICE_GENERATION_PROMPT_TEMPLATE

DEFAULT_MODEL = "llama3.2:3b"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

PRIORITY = [
    "practice", "caution", "similes", "contemporary_examples",
    "history", "interpretation", "pali_terms", "other_sects_teachings"
]

TYPE_MAP = {
    "practice": "daily_challenge",
    "caution": "pitfall_detector",
    "similes": "guided_visualization",
    "contemporary_examples": "scenario_simulator",
    "history": "personal_connector",
    "interpretation": "quiz",
    "pali_terms": "quiz",
    "other_sects_teachings": "quiz"
}

def call_ollama(prompt):
    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.8},
        "system": PRACTICE_GENERATION_SYSTEM_PROMPT
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

    print(f"Generating practice interactions for {len(files)} files...")

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        segments = data.get("commentary_segments", [])
        if not segments:
            print(f" -> Skipping {path.name}: No commentary segments found.")
            continue

        best_seg = None
        for p_type in PRIORITY:
            match = next((s for s in segments if s["type"] == p_type), None)
            if match:
                best_seg = match
                break

        if not best_seg:
            print(f" -> Skipping {path.name}: No matching segment types found.")
            continue

        interaction_type = TYPE_MAP.get(best_seg["type"], "quiz")
        print(f" -> Generating {interaction_type} from '{best_seg['type']}' for {path.name}...")

        prompt = PRACTICE_GENERATION_PROMPT_TEMPLATE.format(
            interaction_type=interaction_type,
            seg_type=best_seg["type"],
            text=best_seg["text"]
        )
        interaction_obj = call_ollama(prompt)

        if interaction_obj:
            data["practice"] = interaction_obj
            atomic_write_json(path, data)
            print(f"    [OK] Added: {interaction_obj.get('title', interaction_type)}")
        else:
            print(f"    [!] Failed to generate interaction for {path.name}")

if __name__ == "__main__":
    main()
