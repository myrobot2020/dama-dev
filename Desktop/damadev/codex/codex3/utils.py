from __future__ import annotations
import json
import tempfile
import sqlite3
import time
from pathlib import Path
from typing import Any

try:
    from .config import EVENT_DB_PATH
except (ImportError, ValueError):
    from config import EVENT_DB_PATH

def atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        delete=False,
        newline="\n",
    ) as tmp:
        json.dump(obj, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)

def log_event(vid: str, stage: str, status: str, message: str = "") -> None:
    """Checkpoints pipeline progress into the damaevents SQLite DB."""
    EVENT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(EVENT_DB_PATH)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                vid TEXT,
                stage TEXT,
                status TEXT,
                message TEXT
            )
        """)
        conn.execute(
            "INSERT INTO events (vid, stage, status, message) VALUES (?, ?, ?, ?)",
            (vid, stage, status, message)
        )
        conn.commit()
    finally:
        conn.close()
