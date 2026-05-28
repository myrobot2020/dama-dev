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
    from config import DEFAULT_EXAMPLE_URL
    from utils import atomic_write_json, log_event
    from ingest_utils import words_to_digits

def get_sc_info(uid):
    url = f"https://suttacentral.net/api/suttaplex/{uid}"
    try:
        req = urllib.request.Request(url, headers={"accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data[0] if data else None
    except: return None

def get_sc_text(uid, author="sujato"):
    try:
        url = f"https://suttacentral.net/api/bilarasuttas/{uid}/{author}"
        req = urllib.request.Request(url, headers={"accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            trans = data.get("translation_text", {})
            order = data.get("keys_order", [])
            if order: return " ".join(trans.get(k, "") for k in order if trans.get(k))
    except: pass
    return ""

def get_legacy_sc_text(uid, author, lang):
    try:
        url = f"https://suttacentral.net/api/suttas/{uid}/{author}?lang={lang}"
        req = urllib.request.Request(url, headers={"accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data.get("translation", {}).get("text", "")
            if text:
                return re.sub(r'<[^>]+>', '', text).strip()
    except: pass
    return ""

def format_sc_uid(sid):
    parts = sid.split('.')
    if len(parts) >= 2:
        return f"an{parts[0]}.{parts[-1]}"
    return sid

def format_timestamp(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02}:{s:02}"

def parse_vtt_timestamp(ts_str):
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
            "start": parse_vtt_timestamp(start),
            "end": parse_vtt_timestamp(end),
            "text": norm_text
        })
    return blocks

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    args = ap.parse_args()
    if not args.input.exists(): return
    with open(args.input, "r", encoding="utf-8") as f: data = json.load(f)

    vid = data.get("vid", "unknown")
    log_event(vid, "IDENTIFY", "START", f"Starting identification stage for video ID: {vid}")

    try:
        print("1. Parsing VTT Timestamps...")
        log_event(vid, "IDENTIFY", "RUNNING", "Parsing auto-transcript VTT timestamps to align with audio tracks")
        asset_dir = Path(__file__).parent / "assets" / vid
        vtt_files = list(asset_dir.glob("transcript*.vtt"))
        vtt_blocks = get_vtt_blocks(vtt_files[0]) if vtt_files else []

        transcript = data.get("transcript", "")
        pattern = re.compile(r"(\b\d+(?:\.\d+)+\b)")
        matches = list(pattern.finditer(transcript))
        suttas = []

        print(f"2. Mapping {len(matches)} Suttas to Audio...")
        log_event(vid, "IDENTIFY", "RUNNING", f"Found {len(matches)} Sutta reference matches in transcript. Starting alignment...")
        current_time = 0.0

        for i, match in enumerate(matches):
            sid = match.group(1)
            print(f" -> Processing {sid}...")
            log_event(vid, "IDENTIFY", "RUNNING", f"Aligning Sutta {sid} audio timestamps and looking up SuttaCentral metadata")

            # Check if we already have a manual mapping for this sutta_id in the input data
            existing_sutta = next((s for s in data.get("suttas", []) if s.get("sutta_id") == sid), {})
            sc_uid = existing_sutta.get("sc_uid") or format_sc_uid(sid)

            start_pos = match.start()
            end_pos = matches[i+1].start() if i + 1 < len(matches) else len(transcript)
            sutta_text = transcript[start_pos:end_pos].strip()

            words = sutta_text.split()
            hook = " ".join(words[1:10]).lower() if len(words) > 10 else words[0]

            aud_start = current_time
            for b in vtt_blocks:
                if b["start"] < current_time: continue
                if sid in b["text"] or hook in b["text"]:
                    aud_start = b["start"]
                    current_time = aud_start
                    break

            sc_uid = format_sc_uid(sid)
            info = get_sc_info(sc_uid)

            sc_text_en = get_sc_text(sc_uid)
            sc_text_ja = ""
            if info and "translations" in info:
                ja_trans = next((t for t in info["translations"] if t.get("lang") in ["jpn", "ja"] and t.get("segmented")), None)
                if not ja_trans:
                    ja_trans = next((t for t in info["translations"] if t.get("lang") in ["jpn", "ja"]), None)

                if ja_trans:
                    author_uid = ja_trans.get("author_uid")
                    if ja_trans.get("segmented"):
                        sc_text_ja = get_sc_text(sc_uid, author_uid)
                    else:
                        sc_text_ja = get_legacy_sc_text(sc_uid, author_uid, ja_trans.get("lang"))

            suttas.append({
                "sutta_id": sid,
                "sc_uid": sc_uid,
                "sutta_name_en": info.get("translated_title") if info else "",
                "sutta_name_pali": info.get("original_title") if info else "",
                "sc_text": sc_text_en,
                "sc_text_ja": sc_text_ja,
                "sc_url": f"https://suttacentral.net/{sc_uid}/en/sujato",
                "aud_start_s_tmp": aud_start,
                "aud_start": format_timestamp(aud_start),
                "sutta_block": sutta_text
            })

        for i in range(len(suttas)):
            end_s = suttas[i+1]["aud_start_s_tmp"] if i+1 < len(suttas) else (vtt_blocks[-1]["end"] if vtt_blocks else 0)
            suttas[i]["aud_end"] = format_timestamp(end_s)
            del suttas[i]["aud_start_s_tmp"]

        data["suttas"] = suttas
        atomic_write_json(args.input, data)
        log_event(vid, "IDENTIFY", "DONE", f"Completed Sutta alignment. Successfully mapped {len(suttas)} Suttas to audio tracks.")

        print(f"\nIdentify Complete: {args.input}")
        # Print final JSON to stdout so that it is returned
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        log_event(vid, "IDENTIFY", "FAIL", f"Failed to identify and align Suttas: {str(e)}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    main()
