#!/usr/bin/env python3
import argparse
import json
import random
import urllib.request
import re
from pathlib import Path

try:
    from .utils import atomic_write_json
    from ..prompts import PRACTICE_GENERATION_SYSTEM_PROMPT, PRACTICE_GENERATION_PROMPT_TEMPLATE
except (ImportError, ValueError):
    from utils import atomic_write_json
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from prompts import PRACTICE_GENERATION_SYSTEM_PROMPT, PRACTICE_GENERATION_PROMPT_TEMPLATE

DEFAULT_MODEL = "qwen2.5:14b"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Categories that should generate MCQs (vs meditation)
MCQ_CATEGORIES = ["cautions", "life_of_monks_vinaya", "interpretation_of_sutta", 
                  "knowledge_about_india", "other_sects_teachings", "reference_to_other_suttas"]
MEDITATION_CATEGORIES = ["jhana_practices", "life_of_buddha"]

def call_ollama(prompt):
    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.3},
        "system": PRACTICE_GENERATION_SYSTEM_PROMPT
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw_response = json.loads(resp.read().decode("utf-8"))["response"]
            clean_json = re.sub(r'```json\n?|\n?```', '', raw_response).strip()
            return json.loads(clean_json)
    except Exception as e:
        print(f"Error: {e}")
        return None

def generate_mcq_from_segment(category, segment_text, aud_start, sutta_id):
    """Generate a single MCQ from one commentary segment."""
    prompt = f"""Generate an MCQ based ONLY on this commentary segment about {category}.

Segment text: "{segment_text}"

Rules:
- Question must test understanding of THIS SPECIFIC segment
- Correct answer must use the teacher's EXACT wording from the segment
- Provide 3 plausible but incorrect distractors
- Include the timestamp

Return JSON:
{{
  "type": "MCQ",
  "title": "Short title about {category}",
  "content": {{
    "question": "question text",
    "options": ["correct", "wrong1", "wrong2", "wrong3"],
    "correct_idx": 0,
    "source_quote": "exact wording from segment",
    "aud_start": "{aud_start}"
  }}
}}"""
    
    result = call_ollama(prompt)
    if result and "content" in result:
        result["sutta_id"] = sutta_id
        result["category"] = category
    return result

def generate_meditation_from_segment(category, segment_text, aud_start, sutta_id):
    """Generate a meditation instruction from one commentary segment."""
    prompt = f"""Generate a brief meditation instruction based ONLY on this commentary segment about {category}.

Segment text: "{segment_text}"

Create a 2-3 sentence guided meditation that directly applies the teaching from this segment.

Return JSON:
{{
  "type": "MEDITATION",
  "title": "Meditation on {category}",
  "content": {{
    "meditation_instruction": "your instruction here",
    "source_quote": "exact wording from segment",
    "aud_start": "{aud_start}"
  }}
}}"""
    
    result = call_ollama(prompt)
    if result and "content" in result:
        result["sutta_id"] = sutta_id
        result["category"] = category
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    ap.add_argument("--category", type=str, default=None, 
                    help="Specific category to generate (optional, generates all if not specified)")
    args = ap.parse_args()
    
    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    print(f"Generating category-specific practices for {len(files)} files...")

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        segments = data.get("commentary_segments", {})
        if not segments:
            print(f"  -> No commentary segments in {path.name}, skipping")
            continue

        sutta_id = data.get("sutta_id", path.stem)
        
        # If a specific category is requested, only process that one
        categories_to_process = [args.category] if args.category else list(segments.keys())
        
        practices = []
        
        for category in categories_to_process:
            if category not in segments:
                continue
                
            category_segments = segments[category]
            if not category_segments:
                continue
                
            # Process each segment in this category
            for seg in category_segments:
                seg_text = seg.get("text", "")
                aud_start = seg.get("aud_start", "00:00")
                
                if len(seg_text) < 20:
                    continue
                
                # Determine interaction type based on category
                if category in MCQ_CATEGORIES:
                    print(f"  -> Generating MCQ for {path.name} | {category}")
                    practice = generate_mcq_from_segment(category, seg_text, aud_start, sutta_id)
                elif category in MEDITATION_CATEGORIES:
                    print(f"  -> Generating Meditation for {path.name} | {category}")
                    practice = generate_meditation_from_segment(category, seg_text, aud_start, sutta_id)
                else:
                    # Default to MCQ for unknown categories
                    print(f"  -> Generating MCQ (default) for {path.name} | {category}")
                    practice = generate_mcq_from_segment(category, seg_text, aud_start, sutta_id)
                
                if practice:
                    practices.append(practice)
        
        # Store all practices for this file
        if practices:
            data["practices_by_category"] = practices
            atomic_write_json(path, data)
            print(f"  -> Saved {len(practices)} practices for {path.name}")

if __name__ == "__main__":
    main()