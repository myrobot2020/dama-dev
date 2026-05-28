#!/usr/bin/env python3
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

def compress_sutta_id(sid):
    sid = re.sub(r'^[a-zA-Z]+', '', sid.strip())
    parts = sid.split('.')
    if not parts:
        return sid
    book = parts[0]
    sutta = parts[-1]
    if len(sutta) > 3 and len(parts) < 3:
        sutta = sutta[-3:]
    return f"an{book}.{sutta}"

def fetch_sc_info(uid):
    url = f"https://suttacentral.net/api/suttaplex/{uid}"
    req = Request(url, headers={"accept": "application/json"})
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and isinstance(data, list):
                return data[0]
    except Exception:
        return None
    return None

def fetch_sc_text(uid, author="sujato"):
    # Try bilarasuttas first (segmented)
    url = f"https://suttacentral.net/api/bilarasuttas/{uid}/{author}"
    req = Request(url, headers={"accept": "application/json"})
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translation = data.get("translation_text", {})
            keys_order = data.get("keys_order", [])
            if keys_order and translation:
                return " ".join(translation.get(k, "") for k in keys_order if translation.get(k))
            elif translation:
                return " ".join(translation.values())
    except Exception:
        pass

    # Try legacy suttas API
    url = f"https://suttacentral.net/api/suttas/{uid}/{author}?lang=en"
    req = Request(url, headers={"accept": "application/json"})
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("translation", {}).get("text", "")
    except Exception:
        pass

    return ""

def calculate_score(sutta_data, transcript_segment):
    if not sutta_data:
        return 0.0

    score = 0.5
    transcript_lower = transcript_segment.lower()

    title_en = (sutta_data.get("translated_title") or "").lower().strip()
    title_pali = (sutta_data.get("original_title") or "").lower().strip()

    for word in re.findall(r'\w+', title_en):
        if len(word) > 3 and word in transcript_lower:
            score += 0.1
            break

    for word in re.findall(r'\w+', title_pali):
        if len(word) > 3 and word in transcript_lower:
            score += 0.1
            break

    if title_en and title_en in transcript_lower:
        score += 0.2

    return min(score, 1.0)

def main():
    json_path = Path("codex/starter.json")
    if not json_path.exists():
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "suttas" not in data:
        return

    for sutta in data["suttas"]:
        original_id = sutta.get("suttaid")
        if not original_id:
            continue

        sc_id = compress_sutta_id(original_id)
        sc_info = fetch_sc_info(sc_id)

        sutta["sc_sutta_id"] = sc_id
        sutta["sc_sutta_link"] = f"https://suttacentral.net/{sc_id}"

        # Find author
        author = "sujato"
        if sc_info:
            translations = sc_info.get("translations", [])
            en_trans = [t for t in translations if t.get("lang") == "en"]
            if en_trans:
                # Prefer sujato if available
                if any(t.get("author_uid") == "sujato" for t in en_trans):
                    author = "sujato"
                else:
                    author = en_trans[0].get("author_uid")

        sutta["sc_sutta"] = fetch_sc_text(sc_id, author)

        score = calculate_score(sc_info, sutta.get("sutta", ""))
        sutta["matching_score"] = score

        if sc_info:
            sutta["sutta_name_en"] = sc_info.get("translated_title")
            sutta["sutta_name_pali"] = sc_info.get("original_title")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
