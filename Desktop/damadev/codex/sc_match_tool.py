#!/usr/bin/env python3
import json
import re
import argparse
from pathlib import Path
from urllib.request import Request, urlopen

def compress_sutta_id(sid):
    """Normalizes 4.20.199 -> an4.199"""
    sid = re.sub(r'^[a-zA-Z]+', '', sid.strip())
    parts = sid.split('.')
    if not parts: return sid
    book, sutta = parts[0], parts[-1]
    # Handle cases where middle parts were accidentally merged (e.g. 4.24232)
    if len(sutta) > 3 and len(parts) < 3:
        sutta = sutta[-3:]
    return f"an{book}.{sutta}"

def fetch_sc_info(uid):
    """Fetches metadata like titles and available translations."""
    url = f"https://suttacentral.net/api/suttaplex/{uid}"
    try:
        req = Request(url, headers={"accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data[0] if data and isinstance(data, list) else None
    except: return None

def fetch_sc_text(uid, author="sujato"):
    """Fetches full sutta text from segmented (Bilara) or legacy API."""
    # 1. Try segmented API (Modern)
    try:
        url = f"https://suttacentral.net/api/bilarasuttas/{uid}/{author}"
        req = Request(url, headers={"accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            trans = data.get("translation_text", {})
            order = data.get("keys_order", [])
            if order: return " ".join(trans.get(k, "") for k in order if trans.get(k))
    except: pass

    # 2. Try legacy API fallback
    try:
        url = f"https://suttacentral.net/api/suttas/{uid}/{author}?lang=en"
        req = Request(url, headers={"accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("translation", {}).get("text", "")
    except: return ""

def calculate_score(info, transcript_segment):
    """Calculates a matching score between SC metadata and the transcript."""
    if not info: return 0.0
    score = 0.5  # Found a valid SC ID
    text = transcript_segment.lower()

    # 1. Check for Sutta ID mention in text (e.g., "4.199" or "4.20.199")
    uid = info.get("uid", "").lower()
    m = re.search(r'(\d+)\.(\d+)', uid)
    if m:
        # Matches "4.199", "4.20.199", "4 199", etc.
        id_pattern = rf"\b{m.group(1)}(\s*\.?\s*\d+)?\s*\.?\s*{m.group(2)}\b"
        if re.search(id_pattern, text):
            score += 0.2

    # 2. Fuzzy Title Match (Check English and Pali)
    titles = [
        (info.get("translated_title") or "").lower(),
        (info.get("original_title") or "").lower()
    ]

    best_title_match = 0.0
    for title in titles:
        if not title: continue
        title_words = [w for w in re.findall(r'\w+', title) if len(w) > 3]
        if not title_words:
            if title and title in text: best_title_match = max(best_title_match, 0.3)
            continue

        matches = [w for w in title_words if w in text]
        if matches:
            match_ratio = len(matches) / len(title_words)
            best_title_match = max(best_title_match, match_ratio * 0.3)

    score += best_title_match
    return min(round(score, 2), 1.0)

def process_file(path):
    print(f"Processing: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return

    if "suttas" not in data: return

    for entry in data["suttas"]:
        sid = entry.get("suttaid")
        if not sid: continue

        sc_id = compress_sutta_id(sid)
        info = fetch_sc_info(sc_id)

        entry["sc_sutta_id"] = sc_id
        entry["sc_sutta_link"] = f"https://suttacentral.net/{sc_id}"

        # Determine best author (prefer Sujato)
        author = "sujato"
        if info:
            en_trans = [t for t in info.get("translations", []) if t.get("lang") == "en"]
            if en_trans and not any(t.get("author_uid") == "sujato" for t in en_trans):
                author = en_trans[0].get("author_uid")

        entry["sc_sutta"] = fetch_sc_text(sc_id, author)

        if info:
            entry["sutta_name_en"] = info.get("translated_title")
            entry["sutta_name_pali"] = info.get("original_title")

        entry["matching_score"] = calculate_score(info, entry.get("sutta", ""))

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to JSON file or directory")
    args = parser.parse_args()

    p = Path(args.path)
    if p.is_file():
        process_file(p)
    else:
        for f in p.rglob("*.json"):
            if f.name.startswith("_") or "node_modules" in str(f): continue
            process_file(f)

if __name__ == "__main__":
    main()
