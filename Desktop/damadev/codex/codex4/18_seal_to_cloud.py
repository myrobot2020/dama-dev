#!/usr/bin/env python3
import argparse
import json
import os
import re
from pathlib import Path
from google.cloud import storage

try:
    from .utils import log_event
    from .config import GCS_HDB_BUCKET, GOOGLE_APPLICATION_CREDENTIALS
except (ImportError, ValueError):
    from utils import log_event
    from config import GCS_HDB_BUCKET, GOOGLE_APPLICATION_CREDENTIALS

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--vid", type=str, help="Only process files for this video ID")
    args = ap.parse_args()

    if not GOOGLE_APPLICATION_CREDENTIALS.exists():
        print(f"Error: Credentials not found at {GOOGLE_APPLICATION_CREDENTIALS}")
        return

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(GOOGLE_APPLICATION_CREDENTIALS)
    client = storage.Client()
    bucket = client.bucket(GCS_HDB_BUCKET)

    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    print(f"Sealing {len(files)} files to cloud storage ({GCS_HDB_BUCKET})...")

    for path in files:
        if "gt2Se9HmLEs" in path.name: continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sutta_id = data.get("sutta_id")
        vid = data.get("vid")
        if not sutta_id or not vid: continue

        if args.vid and vid != args.vid:
            continue

        # Parse Nikaya and Book for Hive-style partitioning
        # Example: AN 5.213 or 5.213 -> nikaya=AN, book=05
        # Support both 'AN 5.213' and '5.213' formats
        match = re.match(r"(?:(AN)\s+)?(\d+)\.", sutta_id)
        if match:
            nikaya = match.group(1) or "AN" # Default to AN if not specified
            book = match.group(2).zfill(2)
        else:
            nikaya = "UNKNOWN"
            book = "00"

        # 1. Upload JSON
        # Path: hdb/nikaya=AN/book=05/sutta=5.213/5.213.json
        sutta_slug = sutta_id.replace(" ", "_")
        json_blob_path = f"hdb/nikaya={nikaya}/book={book}/sutta={sutta_slug}/{sutta_slug}.json"

        print(f" -> Sealing {sutta_id}...")
        log_event(vid, "SEAL", "START", f"Uploading {sutta_id} to GCS")

        if not args.dry_run:
            blob = bucket.blob(json_blob_path)
            blob.upload_from_filename(str(path), content_type="application/json")

        # 2. Upload Assets (MP3s)
        # We look for audio_ja in the JSON
        assets_to_upload = []
        if "audio_ja" in data:
            assets_to_upload.append(data["audio_ja"])

        for asset_rel in assets_to_upload:
            # asset_rel is usually "assets/vid/filename.mp3"
            asset_local_path = root / asset_rel
            if asset_local_path.exists():
                asset_blob_path = f"assets/{vid}/{asset_local_path.name}"
                print(f"    [+] Uploading Asset: {asset_local_path.name}")
                if not args.dry_run:
                    a_blob = bucket.blob(asset_blob_path)
                    a_blob.upload_from_filename(str(asset_local_path), content_type="audio/mpeg")

        log_event(vid, "SEAL", "DONE", f"Sealed to gs://{GCS_HDB_BUCKET}/{json_blob_path}")
        print(f"    [OK] Sealed to GCS")

if __name__ == "__main__":
    main()
