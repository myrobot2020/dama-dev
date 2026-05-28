from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - optional fallback
    SentenceTransformer = None  # type: ignore[assignment]

try:
    import requests
except ImportError:  # pragma: no cover - optional fallback
    requests = None  # type: ignore[assignment]

from scripts.pipeline.streaming.db import DEFAULT_DB_PATH
from scripts.pipeline.streaming.events import utc_now


LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/embeddings")

_MODEL_CACHE: SentenceTransformer | None = None


def normalize_text(parts: list[str]) -> str:
    cleaned = []
    for part in parts:
        text = " ".join(str(part or "").split()).strip()
        if text:
            cleaned.append(text)
    return "\n".join(cleaned)


def image_candidate_text(row: sqlite3.Row) -> str:
    tags_raw = row["tags_json"] or "{}"
    try:
        tags = json.loads(tags_raw)
    except json.JSONDecodeError:
        tags = {}

    parts = [
        row["panel_id"],
        row["source_book_id"],
        f"page {row['page']}" if row["page"] is not None else "",
        tags.get("caption", ""),
        tags.get("description", ""),
        tags.get("ocr_text", ""),
        tags.get("notes", ""),
    ]
    return normalize_text([str(part) for part in parts])


def compute_input_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_local_model(model_name: str = LOCAL_EMBEDDING_MODEL) -> SentenceTransformer:
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers is required for local embeddings")
        _MODEL_CACHE = SentenceTransformer(model_name)
    return _MODEL_CACHE


def embed_texts(
    texts: list[str],
    *,
    model: str = LOCAL_EMBEDDING_MODEL,
    provider: str = "local",
) -> list[list[float]]:
    if provider == "openai":
        if requests is None:
            raise RuntimeError("requests is required for OpenAI embeddings")
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI embeddings")
        payload = {"model": model, "input": texts}
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        resp = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return [item["embedding"] for item in sorted(data["data"], key=lambda item: item["index"])]

    local_model = load_local_model(model)
    embeddings = local_model.encode(texts, normalize_embeddings=True)
    return np.asarray(embeddings, dtype=float).tolist()


def load_candidates(conn: sqlite3.Connection, limit: int | None = None) -> list[dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    query = "select panel_id, source_book_id, page, tags_json from image_candidates where status != 'rejected' order by panel_id"
    params: tuple[Any, ...] = ()
    if limit is not None:
        query += " limit ?"
        params = (limit,)
    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        create table if not exists image_embeddings (
          panel_id text primary key references image_candidates(panel_id),
          model text not null,
          input_hash text not null,
          embedding_json text not null,
          content_text text not null,
          created_at text not null
        )
        """
    )


def upsert_embeddings(
    conn: sqlite3.Connection,
    records: list[dict[str, Any]],
    embeddings: list[list[float]],
    *,
    model: str,
) -> None:
    ensure_table(conn)
    for record, embedding in zip(records, embeddings, strict=True):
        content_text = record["content_text"]
        conn.execute(
            """
            insert into image_embeddings (
              panel_id, model, input_hash, embedding_json, content_text, created_at
            ) values (?, ?, ?, ?, ?, ?)
            on conflict(panel_id) do update set
              model=excluded.model,
              input_hash=excluded.input_hash,
              embedding_json=excluded.embedding_json,
              content_text=excluded.content_text,
              created_at=excluded.created_at
            """,
            (
                record["panel_id"],
                model,
                record["input_hash"],
                json.dumps(embedding),
                content_text,
                utc_now(),
            ),
        )


def build_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for row in candidates:
        # Reuse the same text assembly as the DB reader without coupling to a row factory.
        fake_row = {"panel_id": row["panel_id"], "source_book_id": row["source_book_id"], "page": row["page"], "tags_json": row["tags_json"]}
        text = image_candidate_text(fake_row)  # type: ignore[arg-type]
        if not text:
            continue
        records.append(
            {
                "panel_id": row["panel_id"],
                "content_text": text,
                "input_hash": compute_input_hash(text),
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="Embed image descriptions into local SQLite.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to the local pipeline sqlite db")
    parser.add_argument("--limit", type=int, default=None, help="Optional row limit for batch runs")
    parser.add_argument("--dry-run", action="store_true", help="Print the rows that would be embedded")
    parser.add_argument("--model", default=LOCAL_EMBEDDING_MODEL, help="Embedding model name")
    parser.add_argument(
        "--provider",
        choices=["local", "openai"],
        default="local",
        help="Embedding provider. Default is local and free.",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    with sqlite3.connect(db_path) as conn:
        candidates = load_candidates(conn, args.limit)
        records = build_records(candidates)
        if not records:
            print("No image descriptions found to embed.")
            return 0

        if args.dry_run:
            print(json.dumps(records[:5], indent=2, ensure_ascii=False))
            print(f"Dry run complete: {len(records)} records ready for embedding.")
            return 0

        embeddings = embed_texts(
            [record["content_text"] for record in records],
            model=args.model,
            provider=args.provider,
        )
        upsert_embeddings(conn, records, embeddings, model=f"{args.provider}:{args.model}")
        conn.commit()

    print(f"Embedded {len(records)} image descriptions with {args.provider}:{args.model}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
