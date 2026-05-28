import json
import os
import shutil
from pathlib import Path

class DamaStorage:
    """
    Unified storage provider for the Dama pipeline.
    Simulates GCS locally by default under data/gcs_mock/
    """
    def __init__(self, sutta_id: str, bucket_name="damalight-dama-pipeline", mock_root="data/gcs_mock"):
        self.sutta_id = sutta_id
        self.bucket_name = bucket_name
        # In the future, check an ENV var to use real GCS
        self.use_gcs = os.getenv("USE_GCS", "false").lower() == "true"
        self.base_path = Path(mock_root) / bucket_name / "work-units" / sutta_id

        if not self.use_gcs:
            self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, category: str, filename: str) -> Path:
        # category examples: 'json', 'audio', 'images', 'embeddings'
        return self.base_path / category / filename

    def upload_json(self, filename: str, data: any):
        category = "json"
        # Simple heuristic to separate embeddings
        if "embedding" in filename.lower() or "vector" in filename.lower():
            category = "embeddings"

        if self.use_gcs:
            print(f"[Storage] GCS Upload (STUB): {self.sutta_id}/{category}/{filename}")
        else:
            target = self._get_path(category, filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(data, (dict, list)):
                target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            else:
                target.write_text(str(data), encoding="utf-8")
            print(f"[Storage] Mock GCS Upload: {self.sutta_id}/{category}/{filename}")

    def upload_image(self, filename: str, image_bytes: bytes):
        if self.use_gcs:
            print(f"[Storage] GCS Image Upload (STUB): {self.sutta_id}/images/{filename}")
        else:
            target = self._get_path("images", filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(image_bytes)
            print(f"[Storage] Mock GCS Image Upload: {self.sutta_id}/images/{filename}")

    def upload_audio(self, filename: str, audio_bytes: bytes):
        if self.use_gcs:
            print(f"[Storage] GCS Audio Upload (STUB): {self.sutta_id}/audio/{filename}")
        else:
            target = self._get_path("audio", filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(audio_bytes)
            print(f"[Storage] Mock GCS Audio Upload: {self.sutta_id}/audio/{filename}")

    def upload_file(self, category: str, filename: str, source_path: Path):
        if self.use_gcs:
            print(f"[Storage] GCS File Upload (STUB): {self.sutta_id}/{category}/{filename}")
        else:
            target = self._get_path(category, filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source_path, target)
            print(f"[Storage] Mock GCS File Copy: {self.sutta_id}/{category}/{filename}")

    def clear_all(self):
        """Warning: This clears the entire work-unit for this sutta"""
        if not self.use_gcs and self.base_path.exists():
            shutil.rmtree(self.base_path)
            self.base_path.mkdir(parents=True, exist_ok=True)
            print(f"[Storage] Cleared work-unit: {self.sutta_id}")
