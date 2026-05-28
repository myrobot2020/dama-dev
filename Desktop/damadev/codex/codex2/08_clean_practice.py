import json
import argparse
from pathlib import Path

def clean_practice(obj):
    if "practice" not in obj:
        return obj

    p = obj["practice"]
    p_type = p.get("type", "quiz")
    title = p.get("title", "Practice Reflection")
    content = p.get("content", "")

    # If content is a dict with the type as a key, or has 'rules', etc.
    if isinstance(content, dict):
        # Look for the key matching the type or generic 'prompt' / 'task'
        keys = [p_type, "prompt", "task", "rules", "steps", "question"]
        for k in keys:
            if k in content:
                content = content[k]
                break
        else:
            # Fallback: just take the first string value or first item
            val = next(iter(content.values()))
            content = val

    # Final structure
    obj["practice"] = {
        "type": p_type,
        "title": title,
        "content": content
    }
    return obj

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    args = ap.parse_args()
    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "practice" in data:
            data = clean_practice(data)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Cleaned {path.name}")

if __name__ == "__main__":
    main()
