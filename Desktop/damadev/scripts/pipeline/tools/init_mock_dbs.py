import sqlite3
import json
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parents[3]
MOCK_DIR = REPO_ROOT / "data" / "mock_db"
SQLITE_PATH = MOCK_DIR / "harness_mock.sqlite3"
SCHEMA_PATH = REPO_ROOT / "scripts" / "pipeline" / "streaming" / "schema.sql"

def init_sqlite():
    """Initialize the SQLite Harness DB with the existing schema."""
    print(f"--- Initializing SQLite Harness at {SQLITE_PATH} ---")
    MOCK_DIR.mkdir(parents=True, exist_ok=True)

    if not SCHEMA_PATH.exists():
        print(f"Error: Schema file not found at {SCHEMA_PATH}")
        return

    with sqlite3.connect(SQLITE_PATH) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
    print("SQLite initialized successfully.")

def init_lancedb_mock():
    """Create a placeholder for the LanceDB structure."""
    print(f"--- Preparing LanceDB Mock Directory at {MOCK_DIR / 'lancedb'} ---")
    (MOCK_DIR / "lancedb").mkdir(parents=True, exist_ok=True)

    # We create a README to describe the tables since Lance is a folder-based DB
    info = {
        "tables": {
            "manga_index": ["panel_id", "image_uri", "vector", "description", "top_10_sutta_matches", "matched_sutta_id"],
            "sutta_index": ["sutta_id", "vector", "metadata"]
        },
        "status": "ready_for_lance_initialization"
    }
    (MOCK_DIR / "lancedb" / "structure_info.json").write_text(json.dumps(info, indent=2))
    print("LanceDB placeholders created.")

def generate_gcs_prep_manifest():
    """Generate a manifest to prep the GCS schema later."""
    print("--- Generating GCS Prep Manifest ---")
    manifest = {
        "buckets": [
            {"name": "dama-corpus", "purpose": "Sealed Sutta Data (JSON/MP3)"},
            {"name": "dama-images", "purpose": "Manga Panels and Assets"},
            {"name": "dama-logs", "purpose": "Pipeline Execution Logs"}
        ],
        "prefix_structure": "hdb/nikaya={nikaya}/book={book}/sutta={sutta_id}/run={run_id}/",
        "required_files": [
            "manifest.json", "sutta.json", "audio.json", "segments.json", "images.json"
        ]
    }
    (MOCK_DIR / "gcs_prep_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"GCS Prep Manifest written to {MOCK_DIR / 'gcs_prep_manifest.json'}")

if __name__ == "__main__":
    init_sqlite()
    init_lancedb_mock()
    generate_gcs_prep_manifest()
    print("\nAll mock schemas prepared locally in data/mock_db/")
