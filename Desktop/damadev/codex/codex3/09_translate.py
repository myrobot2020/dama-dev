#!/usr/bin/env python3
import argparse
import json
import re
import urllib.request
from pathlib import Path

try:
    from .utils import atomic_write_json
except (ImportError, ValueError):
    from utils import atomic_write_json

DEFAULT_MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"

def split_sentences(text):
    if not text: return []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def call_ollama_chunk(text, target_lang):
    if not text: return ""

    # We add a very strong system instruction to prevent Hindi drift
    system_instruction = "You are a professional Japanese translator. You MUST output ONLY Japanese text (Kanji, Hiragana, Katakana). NEVER use Hindi, Sanskrit, or Indic scripts."

    prompt = f"""
INSTRUCTION: Translate the following English text into JAPANESE.
LANGUAGE: Japanese (日本語)
RULES: Use natural Japanese phrasing. Keep the teacher's tone.

TEXT:
{text}
"""

    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "system": system_instruction,
        "stream": False,
        "options": {"temperature": 0.0, "num_ctx": 2048}
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            outer = json.loads(resp.read().decode("utf-8"))
            result = outer.get("response", "").strip()

            # Simple check for Hindi/Indic characters (U+0900 to U+097F)
            if any("\u0900" <= char <= "\u097f" for char in result):
                print(f"    [!] Detected Hindi drift, retrying with stricter rule...")
                return call_ollama_chunk(text + " (STRICTLY JAPANESE ONLY!!)", target_lang)

            return result
    except Exception as e:
        print(f"    [!] AI Error: {e}")
        return text

def translate_long_text(text, target_lang):
    if not text: return ""
    chunks = split_sentences(text)
    translated_chunks = []
    for chunk in chunks:
        res = call_ollama_chunk(chunk, target_lang)
        translated_chunks.append(res)
    return "".join(translated_chunks) # Japanese doesn't need spaces between sentences

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    ap.add_argument("--lang", type=str, default="ja")
    args = ap.parse_args()

    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    print(f"Translating {len(files)} files to Japanese (Force Mode)...")

    for path in files:
        if "gt2Se9HmLEs" in path.name: continue
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)

        print(f" -> {path.name}...")

        sutta_ja = translate_long_text(data.get("sutta"), args.lang)
        commentary_ja = translate_long_text(data.get("commentary"), args.lang)
        mcq_ja = call_ollama_chunk(data.get("mcq"), args.lang)
        answer_quote_ja = call_ollama_chunk(data.get("commentarywordsanswer"), args.lang)

        options_ja = []
        for opt in data.get("options", []):
            options_ja.append(call_ollama_chunk(opt, args.lang))

        trans_obj = {
            "sutta": sutta_ja,
            "commentary": commentary_ja,
            "mcq": mcq_ja,
            "options": options_ja,
            "answer_index": data.get("answer_index"),
            "commentarywordsanswer": answer_quote_ja
        }

        if "translations" not in data: data["translations"] = {}
        data["translations"][args.lang] = trans_obj

        atomic_write_json(path, data)
        print(f"    [OK] Translated {path.stem}")

if __name__ == "__main__":
    main()
