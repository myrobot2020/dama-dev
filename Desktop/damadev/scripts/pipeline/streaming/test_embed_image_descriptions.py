from __future__ import annotations

import json
import sqlite3

from scripts.pipeline.streaming.embed_image_descriptions import (
    build_records,
    compute_input_hash,
    image_candidate_text,
    normalize_text,
)


def test_normalize_text_collapses_whitespace():
    assert normalize_text(["  hello   world  ", "", "line two"]) == "hello world\nline two"


def test_image_candidate_text_uses_caption_and_description():
    row = {
        "panel_id": "panel_1",
        "source_book_id": "book_1",
        "page": 12,
        "tags_json": json.dumps(
            {
                "caption": "A monk walks.",
                "description": "A quiet scene in a forest.",
                "ocr_text": "monk forest",
            }
        ),
    }
    text = image_candidate_text(row)  # type: ignore[arg-type]
    assert "panel_1" in text
    assert "A monk walks." in text
    assert "A quiet scene in a forest." in text


def test_build_records_skips_empty_rows():
    candidates = [
        {"panel_id": "p1", "source_book_id": "b1", "page": 1, "tags_json": "{}"},
        {"panel_id": "p2", "source_book_id": "b2", "page": 2, "tags_json": json.dumps({"description": "A panel"})},
    ]
    records = build_records(candidates)
    assert len(records) == 2
    assert records[1]["panel_id"] == "p2"
    assert records[1]["input_hash"] == compute_input_hash(records[1]["content_text"])
