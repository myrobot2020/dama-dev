from __future__ import annotations
import json
import tempfile
import sqlite3
import uuid
import datetime
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

def log_telemetry(vid: str, job_id: str, tokens: int = 0, time_s: float = 0.0) -> None:
    """Logs resource usage for the Performance tab."""
    db_path = Path("C:/Users/ADMIN/Desktop/damadev/data/work/streaming/pipeline.sqlite3")
    conn = sqlite3.connect(str(db_path))
    try:
        # Schema uses job_id as primary key
        # We'll use a string composed of vid and stage as a pseudo job_id for codex4
        conn.execute("""
            INSERT INTO job_telemetry (job_id, tokens, time_s, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(job_id) DO UPDATE SET tokens=tokens+excluded.tokens, time_s=time_s+excluded.time_s
        """, (job_id, tokens, time_s))
        conn.commit()
    except Exception as e:
        print(f"DEBUG: log_telemetry failed: {e}")
    finally:
        conn.close()

def log_event(vid: str, stage: str, status: str, message: str = "") -> None:
    """Checkpoints pipeline progress into the damaevents SQLite DB."""
    # Force absolute path to ensure scripts and dashboard share the same DB
    db_path = Path("C:/Users/ADMIN/Desktop/damadev/data/work/streaming/pipeline.sqlite3")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Use a shorter timeout to avoid blocking if multiple scripts log at once
    conn = sqlite3.connect(str(db_path), timeout=30)
    try:
        # 1. Update the 'events' table (Legacy/Explorer)
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
            (str(vid), str(stage), str(status), str(message))
        )

        # 2. Update 'pipeline_events' (Plant Dashboard Tape)
        # All columns must be provided to satisfy the NOT NULL constraints in schema.sql
        verb = f"{str(stage).lower()}.{str(status).lower()}"
        evt_id = str(uuid.uuid4())
        now_iso = datetime.datetime.utcnow().isoformat() + "Z"

        conn.execute("""
            INSERT INTO pipeline_events
            (event_id, event_type, occurred_at, publisher, pipeline_run_id, correlation_id, idempotency_key, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            evt_id,
            verb,
            now_iso,
            f"codex4.{str(stage).lower()}",
            "codex4-manual-run",
            f"sutta:{vid}",
            evt_id,
            json.dumps({"message": str(message), "vid": str(vid)})
        ))

        # 3. Update 'source_records' (Plant Dashboard Waves)
        plant_status = "running"
        s_upper = str(status).upper()
        st_upper = str(stage).upper()

        if s_upper == "START":
            if st_upper == "INGEST": plant_status = "discovered"
            elif st_upper == "TRANSLATE": plant_status = "translating"
            elif st_upper == "DUB": plant_status = "dubbing"
            elif st_upper == "ALIGN": plant_status = "aligning"
            elif st_upper == "MCQ": plant_status = "generating_mcq"
            elif st_upper == "JUDGE": plant_status = "judging"
        elif s_upper == "DONE" and st_upper == "SEAL":
            plant_status = "sealed"
        elif s_upper == "FAIL":
            plant_status = "failed"
        elif s_upper == "DONE":
            # If a middle stage is done, keep it in "running" or transition to next inferred state
            plant_status = "running"

        conn.execute("""
            INSERT INTO source_records (source_id, source_type, source_uri, dedupe_key, status, metadata_json)
            VALUES (?, 'youtube', ?, ?, ?, ?)
            ON CONFLICT(dedupe_key) DO UPDATE SET status=excluded.status
        """, (str(vid), f"https://youtu.be/{vid}", str(vid), plant_status, json.dumps({"title": str(message) or str(vid)})))

        # 4. Update 'stage_status' (Plant Dashboard Sutta Detail)
        s_status = "completed" if s_upper == "DONE" else ("failed" if s_upper == "FAIL" else "running")
        conn.execute("""
            INSERT INTO stage_status (sutta_id, stage, status, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(sutta_id, stage) DO UPDATE SET status=excluded.status, updated_at=excluded.updated_at
        """, (str(vid), str(stage).lower(), s_status))

        conn.commit()
    except Exception as e:
        # Don't crash the pipeline just because logging failed, but do print it
        print(f"DEBUG: log_event failed for {vid}/{stage}/{status}: {e}")
    finally:
        conn.close()
