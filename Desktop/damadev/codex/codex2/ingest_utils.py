import re

def words_to_digits(text: str) -> str:
    mapping = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
        "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
        "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
        "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30",
        "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
        "eighty": "80", "ninety": "90", "hundred": "100"
    }

    # 0. Preprocess: normalize "one hundred" / "a hundred" to "hundred"
    text = re.sub(r'(?i)\b(?:one|a)\s+hundred\b', 'hundred', text)

    # 1. Convert words to digits
    pattern = re.compile(r'\b(' + '|'.join(mapping.keys()) + r')\b', re.IGNORECASE)
    text = pattern.sub(lambda m: mapping[m.group(0).lower()], text)

    # 2. Normalize separators
    text = re.sub(r'(?i)\bpoint\b|\bdot\b', '.', text)
    text = re.sub(r'(?i)\boh\b', '0', text)
    text = re.sub(r'\s*\.\s*', '.', text)

    # 2.5. Merge hundreds (e.g., "100 and 12" or "100 12" -> "112")
    # This must run before collapse to avoid turning "100 12" into "10012"
    text = re.sub(r'\b100\s+(?:and\s+)?(\d{1,2})\b', lambda m: f"1{int(m.group(1)):02d}", text)

    # 2.6. Fix partially dotted space-separated sequences (e.g., "3.12 111" -> "3.12.111")
    # This must run before collapse to avoid turning "3.12 111" into "3.12111"
    text = re.sub(r'\b(\d+)\.(\d+)\s+(\d+)\b', r'\1.\2.\3', text)
    text = re.sub(r'\b(\d+)\s+(\d+)\.(\d+)\b', r'\1.\2.\3', text)

    # 3. Collapse space-separated digits (e.g., "1 0 5" -> "105")
    # This handles cases where the speaker says "one zero five"
    for _ in range(3):
        text = re.sub(r'\b(\d+)\s+(\d+)\b', r'\1\2', text)

    # 4. Apply 1-2-3 Rule Logic
    # We look for a 1-digit start, a dot/space, a 1-2 digit mid, a dot/space, and a 1-3 digit end.

    # First: Fix over-dotted sequences (3.11.10.5 -> 3.11.105)
    def force_three_segments(match):
        # Remove all dots then re-apply based on your 1-2-3 rule
        raw = match.group(0).replace('.', '')
        # We assume the first digit is the book, the next 1-2 are the nipata
        # But for AN, usually it's Book.Nipata.Sutta.
        # If we have 3.11.105, we want to keep that structure.
        parts = match.group(0).split('.')
        if len(parts) > 3:
            return f"{parts[0]}.{parts[1]}.{''.join(parts[2:])}"
        return match.group(0)

    # Match any sequence of digits with 2 or more dots
    text = re.sub(r'\b\d+(?:\.\d+){2,}\b', force_three_segments, text)

    # Second: Fix space-separated sequences (3 11 105 -> 3.11.105)
    # This follows your: 1 max start, 2 max mid, 3 max end
    text = re.sub(r'\b(\d)\s+(\d{1,2})\s+(\d{1,3})\b', r'\1.\2.\3', text)

    # 5. Common Cleanup
    text = re.sub(r'(?i)\bsultana\b', 'sutta', text)

    return " ".join(text.split())
