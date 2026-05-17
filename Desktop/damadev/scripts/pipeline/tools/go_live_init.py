import json
import os
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT_ID = "dama-492316"
BUCKETS = ["damabuffer-dama-492316", "damaprompts-dama-492316"]
LOCAL_STORES = {
    "damalance": "data/mock_db/lancedb",
    "damaevents": "data/work/streaming"
}

SUTTA_8_2_18 = {
  "sutta_id": "8.2.18",
  "sutta_name_en": "Binding",
  "sutta_name_pali": "Bandhana Sutta",
  "content": {
    "text": "monks a man enslaves a woman in 8 ways 1 a man enslaves a woman by appearance by laughter by speech by song by tears by attire or dress by garlands from the forest and by touch monks in these 8 ways a man enslaves a woman and being scorned by these are verily called as though in a snare that's the end of the suta",
    "commentary": "so these 2 sutas are a bit similar to the first suta...",
    "raw_transcript_path": f"gs://damabuffer-{PROJECT_ID}/work-units/8.2.18/SUTTA_f6d706b3.en.json3",
    "translation_ja": ""
  },
  "audio": {
    "url": f"gs://damahdb-{PROJECT_ID}/audio/072_Anguttara_Nikaya_8C.mp3",
    "start_s": 772.78,
    "end_s": 907.54,
    "duration_s": 134.76
  },
  "visuals": {
    "manga_panels": [
      {
        "id": "panel_an8_2_18_01",
        "url": f"gs://damahdb-{PROJECT_ID}/images/manga/buddha_v02/panel_842.png",
        "caption": "Shadowed by the finery of dress, she is bound by the snare of attraction.",
        "segment_id": "8.2.18:seg1",
        "relevance_score": 0.98
      }
    ]
  },
  "search": {
    "embeddings": [0.0123, -0.0456, 0.0789],
    "keywords": ["enslavement", "8 ways", "attraction", "opposite sex", "snare"]
  },
  "chain": {
    "items": ["appearance", "laughter", "speech", "song", "tears", "attire or dress", "garlands from the forest", "touch"],
    "count": 8,
    "is_ordered": True,
    "category": "ways to enslave a woman"
  },
  "metadata": {
    "pipeline_version": "2.3-philosophical-max-variety",
    "prompt_id": f"gs://damaprompts-{PROJECT_ID}/prompts/segmentation/v3.json",
    "valid": True,
    "last_updated": datetime.now().isoformat()
  }
}

def run_cmd(cmd):
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result.stdout

def init_gcs():
    print("--- Initializing GCS Buckets ---")
    for b in BUCKETS:
        run_cmd(["gsutil", "mb", "-p", PROJECT_ID, f"gs://{b}"])

    # Upload seed sutta
    temp_file = Path("temp_8.2.18.json")
    temp_file.write_text(json.dumps(SUTTA_8_2_18, indent=2))
    run_cmd(["gsutil", "cp", str(temp_file), f"gs://damahdb-{PROJECT_ID}/hdb/nikaya=AN/book=08/sutta=8.2.18/run=001/8.2.18.json"])
    temp_file.unlink()
    print("GCS setup complete.")

def init_local():
    print("--- Initializing Local Stores ---")
    for name, path in LOCAL_STORES.items():
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        print(f"Created {name} at {path}")

    # Seed damaevents
    db_path = Path("data/work/streaming/pipeline.sqlite3")
    schema_path = Path("scripts/pipeline/streaming/schema.sql")
    if schema_path.exists():
        with sqlite3.connect(db_path) as conn:
            conn.executescript(schema_path.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO pipeline_events (event_id, event_type, occurred_at, publisher, pipeline_run_id, correlation_id, idempotency_key, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         ("evt_init", "system.init", datetime.now().isoformat(), "go_live_script", "run_001", "init", "key_init", json.dumps({"status": "live"})))
            conn.commit()
    print("Local setup complete.")

def create_service_account():
    print("--- Creating Factory Bot Service Account ---")
    sa_name = "dama-factory-bot"
    run_cmd(["gcloud", "iam", "service-accounts", "create", sa_name, "--display-name", "Dama Factory Bot"])
    run_cmd(["gcloud", "projects", "add-iam-policy-binding", PROJECT_ID, "--member", f"serviceAccount:{sa_name}@{PROJECT_ID}.iam.gserviceaccount.com", "--role", "roles/storage.admin"])
    run_cmd(["gcloud", "iam", "service-accounts", "keys", "create", "factory-bot-key.json", "--iam-account", f"{sa_name}@{PROJECT_ID}.iam.gserviceaccount.com"])
    print("Service Account created. Key saved to factory-bot-key.json")

if __name__ == "__main__":
    init_gcs()
    init_local()
    create_service_account()
    print("\n--- ALL STORES INITIALIZED ---")
