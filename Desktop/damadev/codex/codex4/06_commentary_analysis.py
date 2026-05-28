#!/usr/bin/env python3
import argparse
import json
import re
import urllib.request
from pathlib import Path

try:
    from .utils import atomic_write_json, log_event
    from .ingest_utils import words_to_digits
except (ImportError, ValueError):
    from utils import atomic_write_json, log_event
    from ingest_utils import words_to_digits

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.2:3b"

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
    clean_seg_words = re.sub(r'[^a-z0-9]', ' ', segment_text.lower()).split()
    if not clean_seg_words: return None
    anchor_words = clean_seg_words[:6]
    if len(anchor_words) < 2: return None

    words_flat, block_indices = [], []
    for i, b in enumerate(vtt_blocks):
        if b["start_s"] < start_after_s - 10.0: continue
        b_words = re.sub(r'[^a-z0-9]', ' ', b["text"].lower()).split()
        for w in b_words:
            words_flat.append(w)
            block_indices.append(i)

    for idx in range(len(words_flat) - len(anchor_words) + 1):
        if all(words_flat[idx + j] == anchor_words[j] for j in range(len(anchor_words))):
            return vtt_blocks[block_indices[idx]]["start"]
    return None

def call_ollama(prompt):
    payload = {"model": DEFAULT_MODEL, "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0.0}}
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            outer = json.loads(resp.read().decode("utf-8"))
            return json.loads(outer.get("response", "{}"))
    except: return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    ap.add_argument("--model", type=str, default=DEFAULT_MODEL)
    ap.add_argument("--vid", type=str, help="Only process files for this video ID")
    args = ap.parse_args()

    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    print(f"Generating MCQs with {args.model}...")

    for path in files:
        if "gt2Se9HmLEs" in path.name: continue
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)

        vid = data.get("vid", "unknown")
        if args.vid and vid != args.vid:
            continue

        commentary = data.get("commentary", "").strip()
        if not commentary: continue

        print(f" -> Analyzing {path.name}...")
        log_event(vid, "MCQ", "START", f"Generating MCQ for {path.name}")

        prompt = f"""Extract ONE MCQ from this Dhamma commentary.
The 'commentarywordsanswer' field MUST be the exact verbatim quote of the teacher's words.

Text:
{commentary}

Return JSON:
{{
  "mcq": "question",
  "options": ["opt1", "opt2", "opt3", "opt4"],
  "answer_index": 0,
  "commentarywordsanswer": "verbatim quote"
}}"""

        try:
            res = call_ollama(prompt)
            if not res or "mcq" not in res:
                log_event(vid, "MCQ", "FAIL", "Failed to generate MCQ JSON")
                continue

            asset_dir = root / "assets" / data["vid"]
            vtt_files = list(asset_dir.glob("*.vtt"))
            vtt_blocks = get_vtt_blocks(vtt_files[0]) if vtt_files else []

            quote = res.get("commentarywordsanswer", "")
            ts_start = find_timestamp(quote, vtt_blocks, start_after_s=parse_vtt_timestamp(data.get("aud_start")))

            # Add/Update MCQ fields
            data["mcq"] = res.get("mcq")
            data["options"] = res.get("options")
            data["answer_index"] = res.get("answer_index")
            data["commentarywordsanswer"] = quote
            data["mcq_aud_start"] = ts_start or data.get("aud_start")
            data["mcq_aud_end"] = data.get("aud_end")

            # FINAL VALIDATION CHECK
            data["valid"] = bool(data.get("sutta") and commentary and data["mcq"])

            # Cleanup redundant fields if they exist
            if "full_commentary" in data: del data["full_commentary"]

            atomic_write_json(path, data)
            log_event(vid, "MCQ", "DONE", f"Added MCQ for {path.stem}")
            print(f"    [OK] Added MCQ. Valid: {data['valid']}")
        except Exception as e:
            log_event(vid, "MCQ", "FAIL", str(e))
            print(f"    [FAIL] {e}")

if __name__ == "__main__":
    main()
