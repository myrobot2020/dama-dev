#!/usr/bin/env python3
import argparse
import json
import urllib.request
from pathlib import Path

try:
    from .utils import atomic_write_json
except (ImportError, ValueError):
    from utils import atomic_write_json

DEFAULT_MODEL = "qwen2.5:14b"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

def build_translation_prompt(target_lang, data_to_translate):
    return f"""
Translate the following Buddhist sutta data into {target_lang}.

### CRITICAL INSTRUCTIONS:
1. Translate the teacher's segments, reading, and practice instructions faithfully.
2. Preserve his personal tone, emphasis, and every specific detail mentioned.
3. Use standard, respectful Buddhist terminology in {target_lang}.
4. Maintain the exact JSON structure provided.
5. Return ONLY the translated JSON object.

Data:
{json.dumps(data_to_translate, ensure_ascii=False, indent=2)}
""".strip()

def call_ollama(prompt):
    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0},
        "system": "You are a professional academic translator specializing in Buddhist teachings. You provide exhaustive, faithful translations of a teacher's words and NEVER summarize. Return valid JSON only."
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            outer = json.loads(resp.read().decode("utf-8"))
            return json.loads(outer.get("response", "{}"))
    except Exception as e:
        print(f"    [!] Ollama error: {e}")
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    ap.add_argument("--lang", type=str, default="ja")
    args = ap.parse_args()

    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    print(f"Translating Bhante's words for {len(files)} files to {args.lang}...")

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f" -> Processing {path.name}...")

        # Prepare ONLY Bhante's words for machine translation
        to_translate = {
            "title": data.get("sutta_name_en"),
            "bhante_reading": data.get("sutta"),
            "commentary_segments": [
                {"type": seg.get("type"), "text": seg.get("text")}
                for seg in data.get("commentary_segments", [])
            ],
            "practice": data.get("practice")
        }

        translated = call_ollama(build_translation_prompt(args.lang, to_translate))

        if translated:
            # Reconstruct segments with original timestamps
            final_segments = []
            orig_segments = data.get("commentary_segments", [])
            trans_segments = translated.get("commentary_segments", [])

            for i, orig in enumerate(orig_segments):
                text = trans_segments[i].get("text") if i < len(trans_segments) else ""
                final_segments.append({
                    "type": orig.get("type"),
                    "text": text,
                    "aud_start": orig.get("aud_start"),
                    "aud_end": orig.get("aud_end")
                })

            if "translations" not in data:
                data["translations"] = {}

            # Determine the sc_text for this language
            # Use official translation if we have it in the JSON (pre-fetched by identify script)
            official_text = data.get(f"sc_text_{args.lang}") or data.get("sc_text_ja") if args.lang == "ja" else ""

            data["translations"][args.lang] = {
                "title": translated.get("title"),
                "sutta": translated.get("bhante_reading"),
                "sc_text": official_text, # This is the official version from SC
                "practice": translated.get("practice"),
                "commentary_segments": final_segments
            }

            atomic_write_json(path, data)
            print(f"    [OK] Translation saved (Official SC text + Machine-translated Bhante).")
        else:
            print(f"    [!] Failed to translate {path.name}")

if __name__ == "__main__":
    main()
