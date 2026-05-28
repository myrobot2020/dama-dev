def main():
    # ... existing setup code ...
    
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        segments = data.get("commentary_segments", {})
        if not segments:
            print(f"  -> No commentary segments in {path.name}, skipping")
            continue

        # Collect all potential practice material
        all_texts = []
        for category, items in segments.items():
            for item in items:
                all_texts.append({
                    "text": item["text"],
                    "aud_start": item["aud_start"],
                    "category": category
                })
        
        if not all_texts:
            continue
        
        # Pick one segment to generate practice from (or combine related ones)
        # Prioritize 'cautions' or 'jhana_practices' for MCQs
        selected = None
        for priority in ["cautions", "jhana_practices", "life_of_monks_vinaya"]:
            for item in all_texts:
                if item["category"] == priority:
                    selected = item
                    break
            if selected:
                break
        
        if not selected:
            selected = all_texts[0]
        
        # Determine practice type based on category
        if selected["category"] in ["cautions", "life_of_monks_vinaya"]:
            practice_type = "MCQ"
        else:
            practice_type = random.choice(["MCQ", "MEDITATION"])
        
        print(f"  -> Generating {practice_type} for {path.name} from category: {selected['category']}")
        
        # Build prompt using ONLY the selected segment
        prompt = f"""Generate a {practice_type} based ONLY on this Buddhist commentary segment.

Category: {selected['category']}
Text: "{selected['text']}"
Timestamp: {selected['aud_start']}

Rules:
- Question/instruction must be based ONLY on this text
- Correct answer must use the teacher's EXACT wording
- Include the timestamp

Return JSON with:
- type: "{practice_type}"
- title: Short title
- content: {{
    "question": "..." (for MCQ),
    "options": ["...", "...", "...", "..."] (for MCQ),
    "correct_idx": 0-3 (for MCQ),
    "meditation_instruction": "..." (for MEDITATION),
    "source_quote": "exact wording",
    "aud_start": "{selected['aud_start']}"
  }}"""
        
        practice_obj = call_ollama(prompt)
        
        if practice_obj:
            data["practice"] = practice_obj
            atomic_write_json(path, data)
            print(f"    [OK] Added practice for {selected['category']}")