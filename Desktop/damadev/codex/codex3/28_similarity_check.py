#!/usr/bin/env python3
import lancedb
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Setup paths
REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "data" / "damalance"
MODEL_NAME = 'all-MiniLM-L6-v2'

def cosine_similarity_from_dist(distance: float) -> float:
    # LanceDB returns L2 distance by default if not specified,
    # but for normalized vectors and cosine search it's often 1 - distance or similar.
    # In this project's context (see 27_match_panels_to_suttas.py), it uses 1.0 - distance.
    return 1.0 - float(distance)

def main():
    import sys

    query_text = None
    if len(sys.argv) > 1:
        query_text = " ".join(sys.argv[1:])

    print(f" -> Connecting to LanceDB at {DB_PATH}...")
    db = lancedb.connect(str(DB_PATH))

    # Handle both old and new LanceDB API for table listing
    try:
        tables = db.table_names()
    except:
        res = db.list_tables()
        tables = res.tables if hasattr(res, 'tables') else res

    if "sutta_knowledge" not in tables:
        print("Error: Table 'sutta_knowledge' not found.")
        return

    sutta_tbl = db.open_table("sutta_knowledge")

    print(f" -> Loading model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    if query_text:
        print(f"\n--- Similarity Check for: \"{query_text}\" ---")
        query_vec = model.encode(query_text).tolist()
        matches = sutta_tbl.search(query_vec).limit(5).to_pandas()

        for i, row in matches.iterrows():
            sim = cosine_similarity_from_dist(row['_distance'])
            print(f"[{i+1}] Sutta: {row['sutta_id']} | Type: {row['type']} | Score: {sim:.4f}")
            print(f"    Text: {row['text'][:200]}...")
        return

    # Fallback to checking manga_knowledge if it exists and has data
    if "manga_knowledge" in tables:
        manga_tbl = db.open_table("manga_knowledge")
        manga_df = manga_tbl.to_pandas()

        if len(manga_df) > 0:
            print(f" -> Found {len(manga_df)} manga panels in 'manga_knowledge'.")
            results = []
            print("\n--- Similarity Report: Manga Descriptions vs Suttas ---\n")
            for _, row in manga_df.head(20).iterrows():
                panel_id = row.get('panel_id') or row.get('id')
                description = row.get('description') or row.get('text')
                if not description: continue

                query_vec = row['vector'] if 'vector' in row and row['vector'] is not None else model.encode(description).tolist()
                matches = sutta_tbl.search(query_vec).limit(1).to_pandas()

                if not matches.empty:
                    best_match = matches.iloc[0]
                    similarity = cosine_similarity_from_dist(best_match['_distance'])
                    print(f"Panel: {panel_id} | Match: {best_match['sutta_id']} | Score: {similarity:.4f}")
                    results.append({"similarity_score": similarity})

            if results:
                avg_score = pd.DataFrame(results)['similarity_score'].mean()
                print(f"\nAverage Similarity Score: {avg_score:.4f}")
        else:
            print(" -> Table 'manga_knowledge' is empty.")
    else:
        print(" -> Table 'manga_knowledge' not found. Pass a description as an argument to test.")
        print("    Usage: python 28_similarity_check.py \"A man sitting under a tree\"")

if __name__ == "__main__":
    main()
