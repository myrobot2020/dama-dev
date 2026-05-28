from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data"
VALIDATED_JSON_ROOT = DATA_ROOT / "validated-json"
WORK_ROOT = DATA_ROOT / "work"

# The "Operational Brain" for checkpointing
EVENT_DB_PATH = WORK_ROOT / "streaming" / "pipeline.sqlite3"

# Cloud Stores (from STORES_REGISTRY.md)
GCS_HDB_BUCKET = "damahdb-dama-492316"
GCS_BUFFER_BUCKET = "damabuffer-dama-492316"
GOOGLE_APPLICATION_CREDENTIALS = REPO_ROOT / "factory-bot-key.json"

DEFAULT_EXAMPLE_URL = "https://www.youtube.com/watch?v=6IRquOK6_nA"
