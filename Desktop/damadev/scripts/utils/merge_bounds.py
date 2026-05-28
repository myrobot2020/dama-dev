import csv
from pathlib import Path

def merge():
    p1 = Path(r"C:\Users\ADMIN\Desktop\dama all\mob app - Copy (2)\sutta_bounds_an_folders.csv")
    p2 = Path(r"C:\Users\ADMIN\Desktop\dama all\sutta_bounds_an_folders.updated.csv")
    p3 = Path(r"C:\Users\ADMIN\Desktop\dama all\sutta_bounds_with_offsets.csv")
    dest = Path("data/raw/bounds/sutta_bounds_consolidated.csv")

    if not dest.parent.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)

    data = {} # sutta_id -> dict

    # Helper to load and merge
    def load_and_merge(path):
        if not path.exists():
            print(f"Warning: {path} not found")
            return
        with path.open(encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get('sutta_id')
                if not sid: continue
                if sid in data:
                    data[sid].update(row)
                else:
                    data[sid] = row

    print(f"Loading {p1}...")
    load_and_merge(p1)
    print(f"Loading {p2} (updates)...")
    load_and_merge(p2)
    print(f"Loading {p3} (offsets)...")
    load_and_merge(p3)

    if not data:
        print("No data found to merge.")
        return

    # Determine all fieldnames
    all_keys = set()
    for row in data.values():
        all_keys.update(row.keys())

    # Priority ordering for fieldnames
    priority = ['sutta_id', 'source_path', 'source_txt_path', 'sutta_start', 'sutta_end', 'commentary_start', 'commentary_end']
    fieldnames = priority + sorted([k for k in all_keys if k not in priority])

    with dest.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        # Sort by sutta_id naturally (if possible) or just string sort
        def sort_key(sid):
            parts = re.split(r'(\d+)', sid)
            return [int(p) if p.isdigit() else p for p in parts]

        import re
        sorted_ids = sorted(data.keys(), key=sort_key)

        for sid in sorted_ids:
            writer.writerow(data[sid])

    print(f"Successfully merged {len(data)} records to {dest}")

if __name__ == "__main__":
    merge()
