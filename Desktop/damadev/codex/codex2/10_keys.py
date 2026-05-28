#!/usr/bin/env python3
import argparse
import json
import re
import urllib.request
from pathlib import Path

try:
    from .utils import atomic_write_json, log_event
except (ImportError, ValueError):
    from utils import atomic_write_json, log_event

DEFAULT_MODEL = "llama3.2:3b"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

SYSTEM_PROMPT = """You extract explicit doctrinal chains from Buddhist sutta records (Anguttara Nikaya).

Rules:
1. Primary source is the sutta text. Use commentary only to clarify wording or resolve ASR errors.
2. Anguttara is organized by number: Book N corresponds to N-fold sets. A valid chain must contain exactly N items.
3. If no single explicit list of exactly N items exists, return has_chain false.
4. Do not invent items. Preserve original wording with light cleanup.
5. Identify the "category" of the chain from one of these 10+ possibilities:
   - "factors/sets": Standard doctrinal groups (e.g. 5 Hindrances, 7 Awakening Factors).
   - "causal_sequence": A leads to B, which leads to C (Dependent Origination style).
   - "gradual_training": Sequential steps of practice or progress.
   - "qualities_of_person": Attributes defining a specific type of individual.
   - "simile_components": The specific parts of an analogy (e.g. parts of a harp, parts of a house).
   - "advantages/benefits": Lists of reasons why a practice is good.
   - "dangers/drawbacks": Lists of reasons why a behavior is bad.
   - "base/source": The origins or causes of certain states.
   - "mental_states": A sequence of meditative or emotional states.
   - "behavioral_precepts": Specific rules or ethical constraints.
   - "stages_of_attainment": Levels of progress (e.g. the 4 fruitions).
   - "powers/faculties": Internal strengths or sensory bases.

Required JSON shape:
{
  "has_chain": true,
  "chain": {
    "items": ["..."],
    "count": N,
    "is_ordered": true,
    "category": "one_of_the_above_labels"
  }
}

If no suitable chain:
{
  "has_chain": false
}
"""

def call_ollama(prompt):
    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0},
        "system": SYSTEM_PROMPT
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            outer = json.loads(resp.read().decode("utf-8"))
            return json.loads(outer.get("response", "{}"))
    except Exception as e:
        print(f"    [!] Ollama error: {e}")
        return {"has_chain": False}

def parse_book_num(sid):
    # Handles "6.6.55" -> 6 or "4.85" -> 4 or "AN 6.6.55" -> 6
    s = re.sub(r"^[A-Z]+\s+", "", sid, flags=re.I)
    parts = s.split(".")
    try: return int(parts[0])
    except: return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    args = ap.parse_args()

    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    print(f"1. Extracting doctrinal chains for {len(files)} files...")

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sid = data.get("sutta_id", "")
        book_num = parse_book_num(sid)
        if not book_num:
            print(f" -> Skipping {path.name}: Could not parse book number from {sid}")
            continue

        print(f" -> Processing {sid} (Book {book_num})...")

        prompt = f"Extract a single explicit chain of exactly {book_num} items from this sutta.\n\nsutta_id: {sid}\n\nSUTTA:\n{data.get('sutta', '')}\n\nCOMMENTARY:\n{data.get('commentary', '')}"

        res = call_ollama(prompt)

        if res.get("has_chain"):
            chain = res.get("chain", {})
            items = chain.get("items", [])
            if len(items) == book_num:
                data["chain"] = chain
                atomic_write_json(path, data)
                print(f"    [OK] Found {len(items)} items: {chain.get('category')}")
            else:
                print(f"    [!] Rejected: Model returned {len(items)} items, but Book {book_num} requires {book_num}.")
        else:
            print(f"    [.] No chain found.")

    print("\nChain Making Complete.")

if __name__ == "__main__":
    main()
