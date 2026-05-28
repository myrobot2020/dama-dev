#!/usr/bin/env python3
import json
import re
import os
import argparse
from pathlib import Path
from urllib.request import Request, urlopen

# SuttaCentral API endpoints
SC_SUTTAPLEX = "https://suttacentral.net/api/suttaplex/"
SC_BILARA = "https://suttacentral.net/api/bilarasuttas/"
SC_SUTTAS = "https://suttacentral.net/api/suttas/"

def get_grok_key():
    # Try environment variable first
    key = os.environ.get("XAI_API_KEY")
    if key:
        return key
    # Try grok.txt file
    p = Path("grok.txt")
    if p.exists():
        return p.read_text().strip()
    return None

def call_grok(prompt, api_key):
    url = "https://api.x.ai/v1/chat/completions"
    payload = {
        "model": "grok-beta", # or grok-2
        "messages": [
            {"role": "system", "content": "You are an expert in the Pali Canon (Nikayas). Your task is to map local sutta identifiers to canonical SuttaCentral UIDs (e.g., an4.199, sn1.20, mn10, dn1)."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"}
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    req = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return json.loads(data["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"Error calling Grok: {e}")
        return None

def fetch_sc_info(uid):
    url = f"{SC_SUTTAPLEX}{uid}"
    try:
        req = Request(url, headers={"accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data[0] if data and isinstance(data, list) else None
    except:
        return None

def fetch_sc_text(uid, author="sujato"):
    # 1. Try segmented API (Modern)
    try:
        url = f"{SC_BILARA}{uid}/{author}"
        req = Request(url, headers={"accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            trans = data.get("translation_text", {})
            order = data.get("keys_order", [])
            if order: return " ".join(trans.get(k, "") for k in order if trans.get(k))
    except: pass

    # 2. Try legacy API fallback
    try:
        url = f"{SC_SUTTAS}{uid}/{author}?lang=en"
        req = Request(url, headers={"accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("translation", {}).get("text", "")
    except: return ""

def resolve_sutta_id(entry, api_key):
    sid = entry.get("suttaid")
    text = entry.get("sutta", "")[:1000] # Use first 1000 chars for context

    prompt = f"""
I have a local sutta identifier: "{sid}"
And a snippet of the transcript: "{text}"

Please identify the most likely SuttaCentral canonical UID for this sutta.
The UID should be lowercase and follow the pattern like 'an4.199' or 'sn12.23'.
Return the result in JSON format with keys "sc_uid" and "reasoning".

Example:
{{
  "sc_uid": "an4.232",
  "reasoning": "The identifier 4.24232 likely refers to Book 4, Sutta 232, which matches the transcript content about deeds."
}}
"""
    result = call_grok(prompt, api_key)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="codex/starter.json", help="Path to JSON file")
    parser.add_argument("--key", help="Grok/xAI API Key")
    args = parser.parse_args()

    api_key = args.key or get_grok_key()
    if not api_key:
        print("Error: No Grok API key found. Use --key or put it in grok.txt or XAI_API_KEY env var.")
        return

    json_path = Path(args.input)
    if not json_path.exists():
        print(f"Error: {json_path} not found.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "suttas" not in data:
        print("No suttas found in JSON.")
        return

    for entry in data["suttas"]:
        print(f"Resolving {entry.get('suttaid')}...")
        res = resolve_sutta_id(entry, api_key)
        if not res or not res.get("sc_uid"):
            print(f"  Failed to resolve {entry.get('suttaid')}")
            continue

        sc_uid = res["sc_uid"]
        print(f"  Resolved to: {sc_uid} ({res.get('reasoning')})")

        info = fetch_sc_info(sc_uid)
        entry["sc_sutta_id"] = sc_uid
        entry["sc_sutta_link"] = f"https://suttacentral.net/{sc_uid}"

        # Determine best author (prefer Sujato)
        author = "sujato"
        if info:
            translations = info.get("translations", [])
            en_trans = [t for t in translations if t.get("lang") == "en"]
            if en_trans:
                if any(t.get("author_uid") == "sujato" for t in en_trans):
                    author = "sujato"
                else:
                    author = en_trans[0].get("author_uid")

        entry["sc_sutta"] = fetch_sc_text(sc_uid, author)

        if info:
            entry["sutta_name_en"] = info.get("translated_title")
            entry["sutta_name_pali"] = info.get("original_title")

        # Matching score (since LLM did the matching, we give it a high base)
        entry["matching_score"] = 0.95

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Done.")

if __name__ == "__main__":
    main()
