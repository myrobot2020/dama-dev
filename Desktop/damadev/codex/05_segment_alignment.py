#!/usr/bin/env python3
import json
import re
import csv
import urllib.request
from pathlib import Path
from difflib import SequenceMatcher
from typing import Any

# Patterns from the project's logic
SUTTA_END_RE = re.compile(r"(?i)\b(?:that'?s\s+)?the\s+end\s+of\s+the\s+sut(?:ta|a|e|i)\b")
COMMENTARY_START_RE = re.compile(
    r"(?i)\b("
    r"i\s+just\s+stopped\s+here"
    r"|i'?ll\s+just\s+stop\s+here"
    r"|so\s+here\s+(?:the\s+)?buddha"
    r"|so\s+in\s+this\s+sut(?:ta|a|e|i)"
    r"|this\s+sut(?:ta|a|e|i)\s+is"
    r"|this\s+is\s+one\s+of\s+those\s+sut(?:tas|as|es|is)"
    r"|i\s+will\s+just\s+stop\s+here"
    r"|now\s+i'?ll\s+stop"
    r")\b"
)

DEFAULT_MODEL = "qwen2.5:14b"
OLLAMA_URL = "http://localhost:11434/api/generate"
CSV_BOUNDS_PATH = Path("data/raw/bounds/sutta_bounds_consolidated.csv")

def load_bounds_map():
    bounds = {}
    if not CSV_BOUNDS_PATH.exists():
        return bounds
    try:
        with open(CSV_BOUNDS_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get("sutta_id")
                if sid:
                    bounds[sid] = row
    except Exception as e:
        print(f"Error loading CSV bounds: {e}")
    return bounds

def call_ollama(prompt: str, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    payload = {
        "model": model,
        "prompt": prompt,
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
    except Exception as e:
        print(f"  Ollama error: {e}")
        return {}

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return " ".join(text.split())

def split_by_anchor(text, anchor):
    if not anchor: return None
    # Normalize anchor for searching
    anchor_clean = clean_text(anchor)
    words = text.split()
    # Sliding window search
    anchor_words = anchor_clean.split()
    for i in range(len(words) - len(anchor_words) + 1):
        window = clean_text(" ".join(words[i:i+len(anchor_words)]))
        if window == anchor_clean:
            # Map back to char index
            char_idx = text.find(" ".join(words[i:i+len(anchor_words)]))
            return char_idx
    return None

def segment_sutta(entry, transcript_text, bounds_map):
    sid = entry.get("suttaid", "")
    sc_id = entry.get("sc_sutta_id", "unknown")
    canonical_text = entry.get("sc_sutta", "")

    # 1. Try CSV Anchors
    if sid in bounds_map:
        row = bounds_map[sid]
        # Try commentary start anchor
        idx = split_by_anchor(transcript_text, row.get("commentary_first3"))
        if idx:
            print(f"  [{sid}] Found CSV Commentary Anchor")
            return transcript_text[:idx].strip(), transcript_text[idx:].strip(), "csv_anchor"
        # Try sutta end anchor
        idx = split_by_anchor(transcript_text, row.get("sutta_last3"))
        if idx:
            end_pos = idx + len(row.get("sutta_last3", ""))
            print(f"  [{sid}] Found CSV Sutta End Anchor")
            return transcript_text[:end_pos].strip(), transcript_text[end_pos:].strip(), "csv_anchor"

    # 2. Try Regex End Marker
    end_match = SUTTA_END_RE.search(transcript_text)
    if end_match:
        print(f"  [{sid}] Found Regex End Marker")
        return transcript_text[:end_match.end()].strip(), transcript_text[end_match.end():].strip(), "regex_end"

    # 3. Try Regex Commentary Start
    comm_match = COMMENTARY_START_RE.search(transcript_text)
    if comm_match and comm_match.start() > 100:
        print(f"  [{sid}] Found Regex Commentary Start")
        return transcript_text[:comm_match.start()].strip(), transcript_text[comm_match.start():].strip(), "regex_cue"

    # 4. Fallback to Ollama
    print(f"  [{sid}] Using Ollama fallback...")
    prompt = f"""
Split the following transcript into two parts:
1. The Sutta Reading (canonical text reading).
2. The Commentary (the explanation that follows).

The monk usually finishes reading and says something like "I just stopped here to comment" or "that's the end of the sutta".
Return ONLY a JSON object with "reading" and "commentary" keys.

TRANSCRIPT:
{transcript_text[:2500]}...

RESPONSE FORMAT:
{{
  "reading": "...",
  "commentary": "..."
}}
"""
    res = call_ollama(prompt)
    reading = res.get("reading")
    commentary = res.get("commentary")

    if reading and commentary:
        # Find where commentary starts in the original text
        c_anchor = commentary.strip()[:40]
        idx = transcript_text.find(c_anchor)
        if idx != -1:
            return transcript_text[:idx].strip(), transcript_text[idx:].strip(), "ollama_split"
        return reading, commentary, "ollama_split_raw"

    return transcript_text, "", "no_split_found"

def main():
    json_path = Path("codex/starter.json")
    if not json_path.exists(): return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    bounds_map = load_bounds_map()
    print(f"Loaded {len(bounds_map)} boundary patterns from CSV.")

    for entry in data.get("suttas", []):
        text = entry.get("sutta", "")
        if not text: continue

        reading, commentary, method = segment_sutta(entry, text, bounds_map)

        entry["sutta_reading"] = reading
        entry["commentary"] = commentary
        entry["segmentation_method"] = method
        # Update main sutta field to be just the reading
        entry["sutta"] = reading

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Segmentation complete.")

if __name__ == "__main__":
    main()
