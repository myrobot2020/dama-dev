#!/usr/bin/env python3
import argparse
import json
import re
import urllib.request
from pathlib import Path
from difflib import SequenceMatcher

try:
    from .utils import atomic_write_json
    from ..prompts import SUTTA_COMMENTARY_SPLIT_REGEX, SUTTA_COMMENTARY_SPLIT_SYSTEM_PROMPT
except (ImportError, ValueError):
    from utils import atomic_write_json
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from prompts import SUTTA_COMMENTARY_SPLIT_REGEX, SUTTA_COMMENTARY_SPLIT_SYSTEM_PROMPT

SUTTA_END_RE = re.compile(SUTTA_COMMENTARY_SPLIT_REGEX)
DEFAULT_MODEL = "qwen2.5:14b"
OLLAMA_URL = "http://localhost:11434/api/generate"

SYSTEM_PROMPT = SUTTA_COMMENTARY_SPLIT_SYSTEM_PROMPT

def call_ollama(prompt):
    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0}
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            outer = json.loads(resp.read().decode("utf-8"))
            return json.loads(outer.get("response", "{}"))
    except: return {}

def find_best_match_end(canonical_text, transcript_segment):
    if not canonical_text: return None
    c_clean = " ".join(re.sub(r'[^a-z0-9\s]', '', canonical_text.lower()).split())
    t_clean = " ".join(re.sub(r'[^a-z0-9\s]', '', transcript_segment.lower()).split())
    suffix = c_clean[-80:] if len(c_clean) > 80 else c_clean
    s = SequenceMatcher(None, t_clean, suffix)
    match = s.find_longest_match(0, len(t_clean), 0, len(suffix))
    if match.size > 15:
        clean_end_pos = match.a + match.size
        curr_clean_idx = 0
        for i, char in enumerate(transcript_segment):
            if re.match(r'[a-z0-9]', char.lower()): curr_clean_idx += 1
            if curr_clean_idx >= clean_end_pos: return i + 1
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    args = ap.parse_args()
    if not args.input.exists(): return
    with open(args.input, "r", encoding="utf-8") as f: data = json.load(f)

    aud_file_name = Path(data.get("aud_file", "")).name

    print("1. Aligning Sutta Content...")
    vid = data.get("vid", "unknown")
    for entry in data.get("suttas", []):
        text = entry.get("sutta_block", "")
        sc_text = entry.get("sc_text", "")
        sid = entry.get("sutta_id", "Unknown")
        print(f" -> Splitting {sid}...")

        reading, commentary, method = text, "", "none"
        end_match = SUTTA_END_RE.search(text)
        if end_match:
            reading, commentary, method = text[:end_match.end()].strip(), text[end_match.end():].strip(), "regex_end_marker"
        else:
            end_idx = find_best_match_end(sc_text, text)
            if end_idx:
                reading, commentary, method = text[:end_idx].strip(), text[end_idx:].strip(), "fuzzy_alignment"
            else:
                print(f"    [!] No match found for {sid}. Using Ollama...")
                res = call_ollama(f"Split into 'sutta' and 'commentary'. Text: {text[:2000]}")
                reading, commentary, method = res.get("sutta", text), res.get("commentary", ""), "ollama_split"

        sutta_obj = {
            "sutta_id": sid,
            "vid": vid,
            "sutta_name_en": entry.get("sutta_name_en", ""),
            "sutta_name_pali": entry.get("sutta_name_pali", ""),
            "sutta": reading,
            "commentary": commentary,
            "sc_text": sc_text,
            "sc_text_ja": entry.get("sc_text_ja", ""),
            "aud_file": f"{vid}.webm",
            "aud_start": entry.get("aud_start"),
            "aud_end": entry.get("aud_end"),
            "sc_uid": entry.get("sc_uid"),
            "sc_url": entry.get("sc_url"),
            "valid": True
        }
        out_path = Path(__file__).parent / f"AN {sid}.json"
        atomic_write_json(out_path, sutta_obj)
        print(f"    -> Exported AN {sid}.json")

    print("\nAlignment Complete.")

if __name__ == "__main__":
    main()
