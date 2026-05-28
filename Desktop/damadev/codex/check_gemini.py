import urllib.request
import json
from pathlib import Path

key = Path("codex/apikey.txt").read_text().strip()
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"

try:
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")
