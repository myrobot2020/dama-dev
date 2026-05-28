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
    text = re.sub(r'\b100\s+(?:and\s+)?(\d{1,2})\b', lambda m: f"1{int(m.group(1)):02d}", text)

    # 2.6. Fix partially dotted space-separated sequences
    text = re.sub(r'\b(\d+)\.(\d+)\s+(\d+)\b', r'\1.\2.\3', text)
    text = re.sub(r'\b(\d+)\s+(\d+)\.(\d+)\b', r'\1.\2.\3', text)

    # 3. Collapse space-separated digits
    for _ in range(3):
        text = re.sub(r'\b(\d+)\s+(\d+)\b', r'\1\2', text)

    # 4. Apply 1-2-3 Rule Logic
    def force_three_segments(match):
        parts = match.group(0).split('.')
        if len(parts) > 3:
            return f"{parts[0]}.{parts[1]}.{''.join(parts[2:])}"
        return match.group(0)

    text = re.sub(r'\b\d+(?:\.\d+){2,}\b', force_three_segments, text)
    text = re.sub(r'\b(\d)\s+(\d{1,2})\s+(\d{1,3})\b', r'\1.\2.\3', text)

    # 5. Common Cleanup
    text = re.sub(r'(?i)\bsultana\b', 'sutta', text)

    # Transcription error fixes
    text = re.sub(r'(?i)\bvagina\b', 'jhana', text)
    text = re.sub(r'(?i)\bvangina\b', 'jhana', text)
    text = re.sub(r'(?i)\bjanus\b', 'jhanas', text)
    text = re.sub(r'(?i)\bjana\b', 'jhana', text)
    text = re.sub(r'(?i)\bgenres\b', 'jhanas', text)
    text = re.sub(r'(?i)\bganas\b', 'jhanas', text)

    return " ".join(text.split())
