from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "codex"

DATA_ROOT = REPO_ROOT / "data"
RAW_ROOT = DATA_ROOT / "raw"
EXAMPLES_ROOT = DATA_ROOT / "examples"
VALIDATED_JSON_ROOT = DATA_ROOT / "validated-json"
WORK_ROOT = DATA_ROOT / "work"

STORES = {
    "damahdb": {
        "type": "gcs",
        "uri": "gs://damahdb-dama-492316",
        "purpose": "Warehouse for final sealed Sutta JSONs, MP3s, and Images",
    },
    "damabuffer": {
        "type": "gcs",
        "uri": "gs://damabuffer-dama-492316",
        "purpose": "Asset buffer for raw transcripts, full audio, and retry assets",
    },
    "damaprompts": {
        "type": "gcs",
        "uri": "gs://damaprompts-dama-492316",
        "purpose": "Versioned AI prompt library",
    },
    "damalance": {
        "type": "lancedb",
        "uri": str(DATA_ROOT / "mock_db" / "lancedb"),
        "purpose": "Local factory VDB for matching and retrieval",
    },
    "damaevents": {
        "type": "sqlite",
        "uri": str(WORK_ROOT / "streaming" / "pipeline.sqlite3"),
        "purpose": "Local operational brain for jobs, events, and stage state",
    },
}

DEFAULT_EXAMPLE_URL = "https://www.youtube.com/watch?v=f6d706b3"
DEFAULT_EXAMPLE_SUTTA_ID = "8.2.18"

CONTAINER_ROLES = {
    "container_1": "dashboard + CPU tasks + light GPU tasks",
    "container_2": "translation + medium GPU tasks",
    "container_3": "dubbing + heavy GPU tasks",
}
