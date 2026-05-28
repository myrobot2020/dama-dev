from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import datetime
from pathlib import Path
from sqlite3 import Connection, Row
from typing import Any

import psutil

from scripts.pipeline.streaming.db import DEFAULT_DB_PATH, connect, init_db


def print_rows(rows: list[Row], columns: list[str]) -> None:
    if not rows:
        print("(none)")
        return
    widths = {
        col: max(len(col), *(len(str(row[col] if row[col] is not None else "")) for row in rows))
        for col in columns
    }
    print("  ".join(col.ljust(widths[col]) for col in columns))
    print("  ".join("-" * widths[col] for col in columns))
    for row in rows:
        print("  ".join(str(row[col] if row[col] is not None else "").ljust(widths[col]) for col in columns))


def table_counts(conn: Connection) -> list[Row]:
    tables = [
        "source_records",
        "pipeline_events",
        "jobs",
        "stage_status",
        "artifact_records",
        "review_items",
        "worker_checkpoints",
        "image_candidates",
        "image_selections",
        "sealed_runs",
    ]
    parts = [f"select '{table}' as table_name, count(*) as rows from {table}" for table in tables]
    return conn.execute(" union all ".join(parts)).fetchall()


def resource_snapshot() -> dict[str, Any]:
    """Gather system resources grunt."""
    try:
        ram = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=None)

        # GPU grunt
        gpu = {"used": 0, "total": 0, "temp": 0, "available": False}
        try:
            cmd = "nvidia-smi"
            out = subprocess.check_output(
                [cmd, "--query-gpu=memory.used,memory.total,temperature.gpu", "--format=csv,noheader,nounits"],
                encoding="utf-8", timeout=2
            ).strip().split(",")
            gpu = {
                "used": int(out[0].strip()),
                "total": int(out[1].strip()),
                "temp": int(out[2].strip()),
                "available": True
            }
        except:
            pass

        disk = shutil.disk_usage(".")
        net = psutil.net_io_counters()

        return {
            "ram": {"used": ram.used, "total": ram.total, "percent": ram.percent},
            "cpu": {"percent": cpu_percent},
            "gpu": gpu,
            "disk": {"used": disk.used, "total": disk.total, "percent": round((disk.used / disk.total) * 100, 1)},
            "network": {"sent": net.bytes_sent, "recv": net.bytes_recv},
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        return {"error": str(e)}

def budget_snapshot(conn: Connection) -> dict[str, Any]:
    """Count calls and estimate gold coins grunt with granular detail."""
    now = datetime.datetime.utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"

    # 1. GenAI Costs (Gemini/Ollama)
    genai_events = ["align.done", "mcq.done", "translate.done", "judge.done"]
    placeholders = ",".join(["?"] * len(genai_events))
    genai_calls = conn.execute(
        f"select count(*) from pipeline_events where event_type in ({placeholders}) and occurred_at > ?",
        (*genai_events, start_of_day)
    ).fetchone()[0]

    # 2. TTS Costs (ElevenLabs)
    tts_calls = conn.execute(
        "select count(*) from pipeline_events where event_type = 'dub.done' and occurred_at > ?",
        (start_of_day,)
    ).fetchone()[0]

    # 3. I/O Costs (GCS/YouTube - estimated)
    io_events = ["download.done", "seal.done"]
    io_calls = conn.execute(
        f"select count(*) from pipeline_events where event_type in ('download.done', 'seal.done') and occurred_at > ?",
        (start_of_day,)
    ).fetchone()[0]

    costs = {
        "genai": round(genai_calls * 0.01, 4), # $0.01 per AI operation
        "tts": round(tts_calls * 0.05, 4),     # $0.05 per Sutta dub
        "storage": round(io_calls * 0.002, 4)  # $0.002 per transfer
    }

    return {
        "llm_calls_today": genai_calls + tts_calls,
        "estimated_cost_usd": sum(costs.values()),
        "breakdown": costs,
        "api_status": "healthy"
    }

def cmd_summary(conn: Connection) -> None:
    print("table counts")
    print_rows(table_counts(conn), ["table_name", "rows"])
    print()
    print("events by type")
    print_rows(
        conn.execute(
            """
            select event_type, count(*) as rows
            from pipeline_events
            group by event_type
            order by event_type
            """
        ).fetchall(),
        ["event_type", "rows"],
    )
    print()
    print("jobs by worker/status")
    print_rows(
        conn.execute(
            """
            select worker_type, status, count(*) as rows
            from jobs
            group by worker_type, status
            order by worker_type, status
            """
        ).fetchall(),
        ["worker_type", "status", "rows"],
    )

def cmd_jobs(conn: Connection, *, status: str | None = None) -> None:
    params: tuple[str, ...] = ()
    where = ""
    if status:
        where = "where status = ?"
        params = (status,)
    rows = conn.execute(
        f"""
        select job_id, worker_type, sutta_id, status, attempt_count, error_type
        from jobs
        {where}
        order by created_at, job_id
        """,
        params,
    ).fetchall()
    print_rows(rows, ["job_id", "worker_type", "sutta_id", "status", "attempt_count", "error_type"])

def cmd_sutta(conn: Connection, sutta_id: str) -> None:
    print(f"stages for {sutta_id}")
    print_rows(
        conn.execute(
            """
            select stage, status, artifact_id, error_type, updated_at
            from stage_status
            where sutta_id = ?
            order by stage
            """,
            (sutta_id,),
        ).fetchall(),
        ["stage", "status", "artifact_id", "error_type", "updated_at"],
    )

def cmd_events(conn: Connection, sutta_id: str | None = None, limit: int = 20, as_json: bool = False) -> None:
    params: list[object] = []
    where = ""
    if sutta_id:
        where = "where correlation_id = ?"
        params.append(f"sutta:{sutta_id}")
    params.append(limit)
    rows = conn.execute(
        f"""
        select event_id, occurred_at, event_type, publisher, correlation_id, payload_json
        from pipeline_events
        {where}
        order by occurred_at desc, event_id desc
        limit ?
        """,
        tuple(params),
    ).fetchall()

    if as_json:
        out = []
        for r in rows:
            payload = json.loads(r["payload_json"])
            # Try to get vid/job_id from payload
            job_id = payload.get("vid") or payload.get("job_id") or "—"
            out.append({
                "id": r["event_id"],
                "ts": r["occurred_at"],
                "verb": r["event_type"],
                "job_id": job_id,
                "sutta_id": r["correlation_id"].split(":")[-1],
                "wave": 0, # Derived in UI
                "payload": payload
            })
        print(json.dumps(out))
        return

    for row in rows:
        payload = json.loads(row["payload_json"])
        print(f"{row['occurred_at']} {row['event_type']} publisher={row['publisher']} correlation={row['correlation_id']}")
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))

def cmd_sources(conn: Connection) -> None:
    print_rows(
        conn.execute(
            """
            select source_id, source_type, nikaya, book, sutta_hint, status
            from source_records
            order by created_at, source_id
            """
        ).fetchall(),
        ["source_id", "source_type", "nikaya", "book", "sutta_hint", "status"],
    )

def clean_path(p: str | None) -> str | None:
    if not p: return None
    p = str(p).replace('\\', '/')
    p = re.sub(r'^.*?data/work/', '', p, flags=re.IGNORECASE)
    return p

def snapshot(conn: Connection) -> dict[str, object]:
    # Group stages by sutta_id for the UI
    # Join with telemetry to get duration and data metrics grunt
    stages_raw = conn.execute(
        """
        select ss.sutta_id, ss.stage, ss.status, jt.time_s,
               jt.input_size_bytes, jt.output_size_bytes, jt.input_count, jt.output_count
        from stage_status ss
        left join (
            select sutta_id, worker_type, max(job_id) as job_id
            from jobs where status = 'completed'
            group by sutta_id, worker_type
        ) j on j.sutta_id = ss.sutta_id and j.worker_type = ss.stage
        left join job_telemetry jt on jt.job_id = j.job_id
        order by ss.stage
        """
    ).fetchall()

    stages_by_sutta: dict[str, list[dict]] = {}
    for row in stages_raw:
        sid = row["sutta_id"]
        if sid not in stages_by_sutta:
            stages_by_sutta[sid] = []
        stages_by_sutta[sid].append({
            "stage": row["stage"],
            "status": row["status"],
            "duration": row["time_s"],
            "metrics": {
                "input_size": row["input_size_bytes"],
                "output_size": row["output_size_bytes"],
                "input_count": row["input_count"],
                "output_count": row["output_count"]
            }
        })

    # Group artifacts by sutta_id grunt
    artifacts_raw = conn.execute(
        "select sutta_id, artifact_type, local_uri, created_at from artifact_records order by created_at desc"
    ).fetchall()

    artifacts_by_sutta: dict[str, list[dict]] = {}
    for row in artifacts_raw:
        sid = row["sutta_id"]
        if sid not in artifacts_by_sutta:
            artifacts_by_sutta[sid] = []
        artifacts_by_sutta[sid].append({
            "type": row["artifact_type"],
            "uri": row["local_uri"],
            "at": row["created_at"]
        })

    # Get sealed info grunt
    sealed_raw = conn.execute("select sutta_id, manifest_uri from sealed_runs").fetchall()
    manifests_by_sutta = {r["sutta_id"]: r["manifest_uri"] for r in sealed_raw}

    # Get image selection info grunt
    image_sel_raw = conn.execute("select sutta_id, panel_id, selection_word from image_selections").fetchall()
    image_sel_by_sutta = {r["sutta_id"]: {"id": r["panel_id"], "word": r["selection_word"]} for r in image_sel_raw}

    # Resource and budget snapshots grunt
    resources = resource_snapshot()
    budgets = budget_snapshot(conn)

    # Queue counts grunt
    job_counts = conn.execute("select status, count(*) from jobs group by status").fetchall()
    queues = {row[0]: row[1] for row in job_counts}
    queues["sealed"] = len(sealed_raw)
    queues["waiting_human"] = conn.execute("select count(*) from review_items where status = 'pending'").fetchone()[0]
    queues["bad_quality"] = conn.execute("select count(*) from stage_status where status = 'failed'").fetchone()[0]

    # Stage global counts grunt
    stage_counts_raw = conn.execute("select stage, count(*) from stage_status where status = 'completed' group by stage").fetchall()
    stages_global = {row[0]: row[1] for row in stage_counts_raw}

    # Artifact global counts grunt
    art_counts_raw = conn.execute("select artifact_type, count(*) from artifact_records group by artifact_type").fetchall()
    artifacts_global = {row[0]: row[1] for row in art_counts_raw}

    # Plant config grunt
    config_raw = conn.execute("select config_key, config_value from plant_config").fetchall()
    config = {row[0]: row[1] for row in config_raw}

    # Active jobs for real-time waves grunt
    active_jobs_raw = conn.execute(
        """
        select job_id, worker_type, sutta_id, status, started_at
        from jobs
        where status in ('running', 'in_progress', 'locked')
        """
    ).fetchall()
    active_jobs = [
        {
            "jobId": r["job_id"],
            "workerType": r["worker_type"],
            "suttaId": r["sutta_id"],
            "status": r["status"],
            "startedAt": r["started_at"]
        }
        for r in active_jobs_raw
    ]

    return {
        "resources": resources,
        "budgets": budgets,
        "queues": queues,
        "active_jobs": active_jobs,
        "stages_global": stages_global,
        "artifacts_global": artifacts_global,
        "config": config,
        "tableCounts": [
            {"label": row["table_name"], "count": row["rows"]}
            for row in table_counts(conn)
        ],
        "sources": [
            {
                "sourceId": row["source_id"],
                "suttaHint": row["sutta_hint"],
                "status": row["status"],
                "sourceUri": row["source_uri"],
                "title": json.loads(row["metadata_json"]).get("title", ""),
                "updatedAt": row["updated_at"],
                "updatedAtMs": int(datetime.datetime.fromisoformat(row["updated_at"].replace('Z', '')).timestamp() * 1000) if row["updated_at"] else None,
                "imageSelection": image_sel_by_sutta.get(row["sutta_hint"]),
                "stages": stages_by_sutta.get(row["sutta_hint"], []) or stages_by_sutta.get(row["source_id"], []),
                "artifacts": artifacts_by_sutta.get(row["sutta_hint"], []) or artifacts_by_sutta.get(row["source_id"], []),
                "proofs": {
                    "validation": clean_path(next((a["uri"] for a in (artifacts_by_sutta.get(row["sutta_hint"], []) or []) if a["type"] == "validation"), None)),
                    "manifest": clean_path(manifests_by_sutta.get(row["sutta_hint"])),
                    "receipt": clean_path(next((a["uri"] for a in (artifacts_by_sutta.get(row["sutta_hint"], []) or []) if a["type"] == "upload_receipt"), None))
                }
            }
            for row in conn.execute(
                """
                select source_id, sutta_hint, status, metadata_json, source_uri, created_at,
                       (select max(updated_at) from stage_status where sutta_id = source_id) as updated_at
                from source_records
                order by created_at desc
                """
            ).fetchall()
        ],
        "workers": [
            {
                "name": row["worker_name"],
                "status": row["status"],
                "isStale": (conn.execute("select (julianday('now') - julianday(?)) * 86400 > 60", (row["updated_at"],)).fetchone()[0] == 1)
            }
            for row in conn.execute("select worker_name, status, updated_at from worker_checkpoints").fetchall()
        ]
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query local streaming pipeline status.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("summary")
    jobs = sub.add_parser("jobs")
    jobs.add_argument("--status", choices=["queued", "running", "completed", "failed", "cancelled"])

    sutta = sub.add_parser("sutta")
    sutta.add_argument("sutta_id")

    events = sub.add_parser("events")
    events.add_argument("sutta_id", nargs="?")
    events.add_argument("--limit", type=int, default=20)
    events.add_argument("--json", action="store_true")

    sub.add_parser("sources")
    sub.add_parser("snapshot")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = init_db(args.db)
    with connect(db_path) as conn:
        if args.command == "summary":
            cmd_summary(conn)
        elif args.command == "jobs":
            cmd_jobs(conn, status=args.status)
        elif args.command == "sutta":
            cmd_sutta(conn, args.sutta_id)
        elif args.command == "events":
            cmd_events(conn, sutta_id=args.sutta_id, limit=args.limit, as_json=args.json)
        elif args.command == "sources":
            cmd_sources(conn)
        elif args.command == "snapshot":
            print(json.dumps(snapshot(conn), ensure_ascii=False, sort_keys=True))
        else:
            raise AssertionError(args.command)
    return 0


if __name__ == "__main__":
    main()
