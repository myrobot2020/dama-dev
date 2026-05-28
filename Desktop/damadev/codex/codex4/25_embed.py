#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import lancedb
import pandas as pd
from sentence_transformers import SentenceTransformer

try:
    from .utils import log_event
except (ImportError, ValueError):
    from utils import log_event

# Setup paths
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data"
DB_PATH = DATA_ROOT / "damalance"
MODEL_NAME = 'all-MiniLM-L6-v2'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    ap.add_argument("--vid", type=str, help="Only process files for this video ID")
    args = ap.parse_args()

    # 1. Initialize local embedding model
    print(f" -> Loading embedding model ({MODEL_NAME})...")
    model = SentenceTransformer(MODEL_NAME)

    # 2. Connect to LanceDB
    DB_PATH.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(DB_PATH))
    table_name = "sutta_knowledge"

    # Handle both old and new LanceDB API for table listing
    try:
        tables = db.table_names()
    except:
        res = db.list_tables()
        tables = res.tables if hasattr(res, 'tables') else res

    # Checkpoint check: Find what we already have
    existing_ids = set()
    if table_name in tables:
        tbl = db.open_table(table_name)
        existing_ids = set(tbl.to_pandas()["id"])
        print(f" -> DB currently has {len(existing_ids)} entries.")

    root = Path(__file__).parent
    files = list(root.glob(args.pattern))
    new_records = []

    print(f" -> Scanning {len(files)} files for new content...")
    for path in files:
        if "gt2Se9HmLEs" in path.name: continue
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)

        sid, vid = data.get("sutta_id"), data.get("vid")
        if not sid or not vid: continue

        if args.vid and vid != args.vid:
            continue

        aud_start, aud_end = data.get("aud_start"), data.get("aud_end")

        log_event(vid, "EMBED", "START", f"Embedding {sid}")

        try:
            # Check Sutta
            s_id = f"{sid}_sutta"
            s_text = data.get("sutta", "").strip()
            if s_text and s_id not in existing_ids:
                print(f"    [+] Embedding Sutta: {sid}")
                new_records.append({
                    "id": s_id, "sutta_id": sid, "vid": vid, "text": s_text, "type": "sutta",
                    "start_time": aud_start, "end_time": aud_end,
                    "vector": model.encode(s_text).tolist()
                })

            # Check Commentary
            c_id = f"{sid}_commentary"
            c_text = data.get("commentary", "").strip()
            if c_text and c_id not in existing_ids:
                print(f"    [+] Embedding Commentary: {sid}")
                new_records.append({
                    "id": c_id, "sutta_id": sid, "vid": vid, "text": c_text, "type": "commentary",
                    "start_time": data.get("mcq_aud_start") or aud_start, "end_time": aud_end,
                    "vector": model.encode(c_text).tolist()
                })
            log_event(vid, "EMBED", "DONE", f"Embedded {sid}")
        except Exception as e:
            log_event(vid, "EMBED", "FAIL", str(e))
            print(f"    [FAIL] {e}")

    # 3. Save new results
    if new_records:
        df = pd.DataFrame(new_records)
        if table_name not in tables:
            db.create_table(table_name, data=df)
        else:
            tbl = db.open_table(table_name)
            tbl.add(df)
        print(f"    [OK] Added {len(new_records)} new entries.")
    else:
        print("    [OK] DB is already up to date.")

if __name__ == "__main__":
    main()
