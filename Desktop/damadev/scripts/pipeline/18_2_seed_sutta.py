from 18_1_storage import DamaStorage
from pathlib import Path
import json

def seed():
    store = DamaStorage()
    sutta = "AN1.1"

    # 1. Pipeline State
    store.upload_json(sutta, "json", "state.json", {
        "status": "in-progress",
        "current_stage": "03_alignment",
        "percent_complete": 45,
        "last_update": "2023-10-27T12:00:00Z"
    })

    # 2. Sutta Metadata
    store.upload_json(sutta, "json", "metadata.json", {
        "sutta_id": sutta,
        "title": "AN 1.1: Keeping it Simple",
        "nikaya": "AN",
        "original_source": "https://www.youtube.com/watch?v=f6d706b3"
    })

    # 3. Transcript Snippet (Based on your real data in data/work/streaming)
    # Taking a few lines from the transcript I read earlier
    store.upload_json(sutta, "json", "transcript.json", {
        "segments": [
            {"start": 1.12, "end": 4.56, "text": "and today we start with suta number eight point two point thirteen"},
            {"start": 7.04, "end": 10.00, "text": "the buddha said monks as a goodly thoroughbred steed"},
            {"start": 10.00, "end": 15.20, "text": "belonging to a raja when possessed of eight points is worthy of a rajya"}
        ]
    })

    # 4. Mock Embeddings
    store.upload_json(sutta, "embeddings", "vector_v1.json", {
        "model": "text-embedding-3-small",
        "dimensions": 1536,
        "values": [0.01, -0.02, 0.05] * 512 # Placeholder
    })

    # 5. Mock Panels (Manga data)
    store.upload_json(sutta, "json", "panels.json", {
        "volume": "buddha_v01",
        "mappings": [
            {"panel_id": "p001", "segment_id": "s1", "confidence": 0.98},
            {"panel_id": "p002", "segment_id": "s2", "confidence": 0.85}
        ]
    })

    # 6. Create Empty Directories for binaries
    (store.base_path / "work-units" / sutta / "audio").mkdir(parents=True, exist_ok=True)
    (store.base_path / "work-units" / sutta / "images").mkdir(parents=True, exist_ok=True)

    print(f"\n✅ Simulation Ready!")
    print(f"Location: {store.base_path}/work-units/{sutta}")
    print("Files created: state.json, metadata.json, transcript.json, vector_v1.json, panels.json")

if __name__ == "__main__":
    seed()
