#!/usr/bin/env python3
import sys
import lancedb
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Setup paths
REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "data" / "damalance"
MODEL_NAME = 'all-MiniLM-L6-v2'

def main():
    if len(sys.argv) < 2:
        print("Usage: python 26_search.py \"your question here\"")
        return

    query = sys.argv[1]

    # 1. Load model and DB
    model = SentenceTransformer(MODEL_NAME)
    db = lancedb.connect(str(DB_PATH))
    tbl = db.open_table("sutta_knowledge")

    # 2. Vector Search
    query_vec = model.encode(query).tolist()
    results = tbl.search(query_vec).limit(3).to_pandas()

    print(f"\n--- TOP 3 SEARCH RESULTS FOR: '{query}' ---")
    for i, row in results.iterrows():
        print(f"\n[{i+1}] SUTTA: {row['sutta_id']} | TYPE: {row['type']} | DIST: {row['_distance']:.4f}")
        # Print a snippet of the text
        text_snippet = row['text'][:300].replace('\n', ' ') + "..."
        print(f"    TEXT: {text_snippet}")

if __name__ == "__main__":
    main()
