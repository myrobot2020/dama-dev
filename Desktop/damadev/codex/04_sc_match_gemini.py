#!/usr/bin/env python3
import json
import re
import time
import argparse
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

def get_gemini_key():
    p = Path("codex/apikey.txt")
    return p.read_text().strip() if p.exists() else None

def call_gemini(prompt, api_key):
    # Using 2.0-flash-lite for stability and speed
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "You are an expert in the Pali Canon. Identify the SuttaCentral UID for the following identifier and text. Return ONLY a JSON object with 'sc_uid' and 'reasoning'. Context: " + prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    headers = {"Content-Type": "application/json"}

    for attempt in range(5):
        try:
            req = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        except HTTPError as e:
            if e.code == 429:
                wait = (attempt + 1) * 30
                print(f"  Rate limited, waiting {wait}s... (attempt {attempt+1}/5)")
                time.sleep(wait)
                continue
            print(f"  Error: {e.code} {e.reason}")
            return None
        except Exception as e:
            print(f"  Error: {e}")
            return None
    return None

def fetch_sc_info(uid):
    url = f"https://suttacentral.net/api/suttaplex/{uid}"
    try:
        req = Request(url, headers={"accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data[0] if data and isinstance(data, list) else None
    except: return None

def fetch_sc_text(uid, author="sujato"):
    try:
        url = f"https://suttacentral.net/api/bilarasuttas/{uid}/{author}"
        req = Request(url, headers={"accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            trans = data.get("translation_text", {})
            order = data.get("keys_order", [])
            if order: return " ".join(trans.get(k, "") for k in order if trans.get(k))
    except: pass
    try:
        url = f"https://suttacentral.net/api/suttas/{uid}/{author}?lang=en"
        req = Request(url, headers={"accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("translation", {}).get("text", "")
    except: return ""

def main():
    api_key = get_gemini_key()
    if not api_key: return
    json_path = Path("codex/starter.json")
    if not json_path.exists(): return
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "suttas" not in data: return

    print(f"Resolving {len(data['suttas'])} suttas using Gemini...")
    for entry in data["suttas"]:
        sid = entry.get("suttaid")
        text = entry.get("sutta", "")[:1200]
        print(f"Resolving {sid}...")

        res = call_gemini(f"ID {sid}, context: {text}", api_key)
        if not res:
            print(f"  Failed resolving {sid}")
            continue

        sc_uid = res.get("sc_uid")
        print(f"  -> {sc_uid}")

        info = fetch_sc_info(sc_uid)
        entry["sc_sutta_id"] = sc_uid
        entry["sc_sutta_link"] = f"https://suttacentral.net/{sc_uid}"

        author = "sujato"
        if info:
            en_trans = [t for t in info.get("translations", []) if t.get("lang") == "en"]
            if en_trans and not any(t.get("author_uid") == "sujato" for t in en_trans):
                author = en_trans[0].get("author_uid")
            entry["sutta_name_en"] = info.get("translated_title")
            entry["sutta_name_pali"] = info.get("original_title")

        entry["sc_sutta"] = fetch_sc_text(sc_uid, author)
        entry["matching_score"] = 0.95

        # Save after each sutta in case of crash
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Small sleep to be nice to API
        time.sleep(2)

    print("Done Matching.")

if __name__ == "__main__":
    main()
