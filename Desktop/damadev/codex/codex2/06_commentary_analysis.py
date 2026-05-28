#!/usr/bin/env python3
import argparse
import json
import re
import urllib.request
from pathlib import Path

try:
    from .utils import atomic_write_json
    from .ingest_utils import words_to_digits
    from ..prompts import COMMENTARY_ANALYSIS_SYSTEM_PROMPT
except (ImportError, ValueError):
    from utils import atomic_write_json
    from ingest_utils import words_to_digits
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from prompts import COMMENTARY_ANALYSIS_SYSTEM_PROMPT

DEFAULT_MODEL = "llama3.2:3b"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

SYSTEM_PROMPT = COMMENTARY_ANALYSIS_SYSTEM_PROMPT

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
        return {"segments": []}

def parse_vtt_timestamp(ts_str):
    if not ts_str or ts_str == "...": return 0.0
    parts = ts_str.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return 0.0

def get_vtt_blocks(vtt_path):
    if not vtt_path.exists(): return []
    content = vtt_path.read_text(encoding="utf-8", errors="replace")
    block_pattern = re.compile(r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3}).*?\n(.*?)(?=\n\n|\n\d{2}:|\Z)", re.DOTALL)
    blocks = []
    for start, end, text in block_pattern.findall(content):
        clean_text = re.sub(r"<[^>]+>", "", text).strip().replace("\n", " ")
        norm_text = words_to_digits(clean_text.lower())
        blocks.append({
            "start": start.split('.')[0],
            "start_s": parse_vtt_timestamp(start),
            "text": norm_text
        })
    return blocks

def find_timestamp(segment_text, vtt_blocks, start_after_s=0.0):
    if not segment_text or not vtt_blocks: return None
    # Clean the segment text for better matching
    clean_seg = " ".join(re.sub(r'[^a-z0-9\s]', '', segment_text.lower()).split())
    # Try a few anchors from the start of the segment
    anchors = [clean_seg[:50], clean_seg[10:60], clean_seg[20:70]]
    for b in vtt_blocks:
        if b["start_s"] < start_after_s - 2.0: continue
        for anchor in anchors:
            if len(anchor) > 15 and anchor in b["text"]:
                return b["start"]
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    args = ap.parse_args()

    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        commentary = data.get("commentary", "").strip()
        if not commentary or not data.get("vid"): continue

        asset_dir = root / "assets" / data["vid"]
        vtt_files = list(asset_dir.glob("*.vtt"))
        vtt_blocks = get_vtt_blocks(vtt_files[0]) if vtt_files else []

        print(f" -> Segmenting commentary for {path.name}...")
        res = call_ollama(f"Segment this commentary text:\n\n{commentary}")
        raw_segments = res.get("segments", [])

        commentary_segments = []
        last_s = parse_vtt_timestamp(data.get("aud_start", "00:00"))

        for seg in raw_segments:
            text = seg["text"].strip()
            # 1. Quality Filter: Discard short segments and boilerplate
            if len(text) < 45: continue
            if any(p in text.lower() for p in ["the next suta", "i'll stop here", "well done well done"]): continue

            # 2. Timestamp Filter: Only keep if we can find it in the audio
            t = find_timestamp(text, vtt_blocks, start_after_s=last_s)
            if not t:
                print(f"    [!] Skipping segment (no timestamp): {text[:40]}...")
                continue

            commentary_segments.append({
                "type": seg["type"],
                "text": text,
                "aud_start": t
            })
            last_s = parse_vtt_timestamp(t)

        # 3. Final Step: Calculate aud_end based on valid transitions
        for i in range(len(commentary_segments)):
            if i + 1 < len(commentary_segments):
                commentary_segments[i]["aud_end"] = commentary_segments[i+1]["aud_start"]
            else:
                commentary_segments[i]["aud_end"] = data.get("aud_end")

        if commentary_segments:
            data["commentary_segments"] = commentary_segments
            atomic_write_json(path, data)
            found_types = set(s["type"] for s in commentary_segments)
            print(f"    [OK] Kept {len(commentary_segments)} valid segments. Types: {', '.join(found_types)}")
        else:
            data["commentary_segments"] = []
            atomic_write_json(path, data)
            print(f"    [OK] No high-value segments found for {path.name}. List cleared.")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
