#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import lancedb
import pandas as pd
from sentence_transformers import SentenceTransformer


REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "data" / "damalance"
MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_PANEL_TABLE = "manga_knowledge"
DEFAULT_SUTTA_TABLE = "sutta_knowledge"


def load_table(db: lancedb.DB, table_name: str) -> pd.DataFrame:
    tbl = db.open_table(table_name)
    return tbl.to_pandas()


def cosine_from_lancedb_distance(distance: float) -> float:
    # LanceDB vector search on normalized vectors returns cosine distance in [0, 2].
    return 1.0 - float(distance)


def main() -> int:
    ap = argparse.ArgumentParser(description="Match manga descriptions to sutta vectors in the shared LanceDB.")
    ap.add_argument("--panel-table", default=DEFAULT_PANEL_TABLE)
    ap.add_argument("--sutta-table", default=DEFAULT_SUTTA_TABLE)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--output", type=Path, default=None, help="Optional JSON output file for matches")
    args = ap.parse_args()

    print(f" -> Loading embedding model ({MODEL_NAME})...")
    model = SentenceTransformer(MODEL_NAME)

    print(f" -> Connecting to LanceDB at {DB_PATH}...")
    db = lancedb.connect(str(DB_PATH))

    # Handle both old and new LanceDB API for table listing
    try:
        tables = db.table_names()
    except:
        res = db.list_tables()
        tables = res.tables if hasattr(res, 'tables') else res

    if args.panel_table not in tables:
        raise SystemExit(f"Panel table not found: {args.panel_table}")
    if args.sutta_table not in tables:
        raise SystemExit(f"Sutta table not found: {args.sutta_table}")

    panel_tbl = db.open_table(args.panel_table)
    sutta_tbl = db.open_table(args.sutta_table)

    panel_df = panel_tbl.to_pandas()
    if args.limit is not None:
        panel_df = panel_df.head(args.limit)

    results: list[dict] = []
    print(f" -> Matching {len(panel_df)} panel descriptions...")
    for _, row in panel_df.iterrows():
        panel_id = str(row.get("panel_id") or row.get("id") or "").strip()
        text = str(row.get("text") or row.get("description") or "").strip()
        if not panel_id or not text:
            continue

        query_vec = model.encode(text).tolist()
        matches = sutta_tbl.search(query_vec).limit(args.top_k).to_pandas()

        top_matches = []
        for _, srow in matches.iterrows():
            dist = float(srow["_distance"])
            top_matches.append(
                {
                    "sutta_id": str(srow.get("sutta_id") or srow.get("id") or ""),
                    "type": str(srow.get("type") or ""),
                    "text": str(srow.get("text") or ""),
                    "distance": dist,
                    "similarity": cosine_from_lancedb_distance(dist),
                }
            )

        results.append(
            {
                "panel_id": panel_id,
                "image_path": row.get("image_path", ""),
                "description": text,
                "top_matches": top_matches,
            }
        )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f" -> Wrote {len(results)} panel match records to {args.output}")

    for item in results[: min(10, len(results))]:
        best = item["top_matches"][0] if item["top_matches"] else None
        if best:
            print(
                f"{item['panel_id']} -> {best['sutta_id']} | sim={best['similarity']:.4f} | dist={best['distance']:.4f}"
            )

    print(f" -> Matched {len(results)} panels.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
