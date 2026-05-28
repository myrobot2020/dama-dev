import sqlite3
import shutil
from pathlib import Path
from scripts.pipeline.streaming.db import DEFAULT_DB_PATH

def clean():
    db_path = Path(DEFAULT_DB_PATH)
    audio_dir = db_path.parent / "audio"
    trans_dir = db_path.parent / "transcripts"

    print(f"Cave man cleaning bones from {db_path} grunt.")

    if db_path.exists():
        conn = sqlite3.connect(db_path)
        tables = [
            "pipeline_events", "jobs", "stage_status", "artifact_records",
            "review_items", "worker_checkpoints", "source_records",
            "image_candidates", "image_selections", "sealed_runs",
            "resource_locks", "job_telemetry"
        ]
        for table in tables:
            try:
                conn.execute(f"DELETE FROM {table}")
            except sqlite3.OperationalError:
                pass # table might not exist
        conn.commit()
        conn.close()
        print("Tables cleared grunt.")

    if audio_dir.exists():
        shutil.rmtree(audio_dir)
        audio_dir.mkdir(parents=True, exist_ok=True)
        print("Audio cleared grunt.")

    if trans_dir.exists():
        shutil.rmtree(trans_dir)
        trans_dir.mkdir(parents=True, exist_ok=True)
        print("Transcripts cleared grunt.")

if __name__ == "__main__":
    clean()
