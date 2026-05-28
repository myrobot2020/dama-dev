#!/usr/bin/env python3
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path

# Config
DB_PATH = Path("C:/Users/ADMIN/Desktop/damadev/data/work/streaming/pipeline.sqlite3")
RUNNER_PATH = Path("C:/Users/ADMIN/Desktop/damadev/codex/codex4/runner.py")

# Resource Pool Mapping
POOLS = {
    "GPU": ["align", "mcq", "translate", "judge"],
    "CPU": ["dub"],
    "WRITE": ["embed", "seal"]
}

# The sequence of stages
STAGE_CHAIN = ["align", "mcq", "translate", "judge", "dub", "embed", "seal"]

def get_next_stage(current_stage):
    try:
        idx = STAGE_CHAIN.index(current_stage)
        if idx + 1 < len(STAGE_CHAIN):
            return STAGE_CHAIN[idx + 1]
    except ValueError:
        pass
    return None

def get_pending_job(pool_name):
    allowed_stages = POOLS.get(pool_name, [])
    placeholders = ", ".join(["?"] * len(allowed_stages))

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        query = f"""
            SELECT job_id, sutta_id, worker_type as stage
            FROM jobs
            WHERE status = 'PENDING' AND worker_type IN ({placeholders})
            ORDER BY created_at ASC LIMIT 1
        """
        cur.execute(query, allowed_stages)
        return cur.fetchone()

def update_job_status(job_id, status, error=None):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        if status == 'IN_PROGRESS':
            cur.execute("UPDATE jobs SET status=?, started_at=datetime('now') WHERE job_id=?", (status, job_id))
        elif status == 'FAILED':
            cur.execute("UPDATE jobs SET status=?, error_message=?, finished_at=datetime('now') WHERE job_id=?", (status, error, job_id))
        elif status == 'COMPLETED':
            cur.execute("UPDATE jobs SET status=?, finished_at=datetime('now') WHERE job_id=?", (status, job_id))
        conn.commit()

def tick_next_stage(sutta_id, current_stage):
    next_s = get_next_stage(current_stage)
    if not next_s:
        return

    job_id = f"tick_{uuid.uuid4().hex[:8]}"
    print(f"  [TICK] Queuing next stage: {next_s} for {sutta_id}")

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        # We use a dummy event_id or link it to a generic one
        cur.execute("""
            INSERT INTO jobs (job_id, event_id, worker_type, sutta_id, status)
            VALUES (?, 'manual_tick', ?, ?, 'PENDING')
        """, (job_id, next_s, sutta_id))
        conn.commit()

def run_subscriber(pool_name):
    print(f"--- Dama Subscriber Started: Pool={pool_name} ---")

    while True:
        job = get_pending_job(pool_name)
        if not job:
            time.sleep(2)
            continue

        job_id, sid, stage = job['job_id'], job['sutta_id'], job['stage']
        print(f"\n[EXEC] Pool {pool_name} -> {stage} for {sid}")

        update_job_status(job_id, 'IN_PROGRESS')

        try:
            # Run exactly one stage
            # Special case for ingest where sid is actually the URL
            if stage == "ingest":
                cmd = [sys.executable, str(RUNNER_PATH), "--url", sid]
            else:
                cmd = [sys.executable, str(RUNNER_PATH), "--sutta-id", sid, "--stages", stage]

            print(f"  -> Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"  [OK] Finished {stage}")
                update_job_status(job_id, 'COMPLETED')
                tick_next_stage(sid, stage)
            else:
                print(f"  [FAIL] {result.stderr or result.stdout}")
                update_job_status(job_id, 'FAILED', error=result.stderr or result.stdout)

        except Exception as e:
            print(f"  [CRITICAL] {str(e)}")
            update_job_status(job_id, 'FAILED', error=str(e))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dama_subscriber.py --pool [GPU|CPU|WRITE]")
        sys.exit(1)

    p_name = sys.argv[2] if sys.argv[1] == "--pool" else sys.argv[1]
    run_subscriber(p_name)
