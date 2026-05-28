#!/usr/bin/env python3
import argparse
import subprocess
import sys
import json
import time
from pathlib import Path

try:
    from .utils import log_event
except (ImportError, ValueError):
    from utils import log_event

def run_script(script_name, args=None):
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)

    print(f"\n>>> RUNNING: {script_name} {' '.join(args or [])}")
    process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
    process.wait()
    return process.returncode

def main():
    parser = argparse.ArgumentParser(description="Full Codex4 Pipeline Runner")
    parser.add_argument("--url", help="YouTube URL to ingest")
    parser.add_argument("--sutta-id", help="Only process this specific Sutta ID (skips ingest/identify)")
    parser.add_argument("--stages", help="Comma-separated list of stages to run (e.g., 'align,translate,dub')")
    args = parser.parse_args()

    root = Path(__file__).parent

    # Define the pipeline steps mapping
    steps_map = {
        "ingest": ("01_ingest.py", ["--url", args.url] if args.url else []),
        "identify": ("03_identify.py", []),
        "align": ("05_segment_alignment.py", []),
        "mcq": ("06_commentary_analysis.py", []),
        "translate": ("09_translate.py", ["--lang", "ja"]),
        "judge": ("12_judge.py", []),
        "dub": ("22_dub.py", []),
        "embed": ("25_embed.py", []),
        "seal": ("18_seal_to_cloud.py", [])
    }

    # Default order for a full run or sutta replay
    default_processing_stages = ["align", "mcq", "translate", "judge", "dub", "embed", "seal"]

    if args.sutta_id:
        # REPLAY MODE: Skip ingest and identification
        sid = args.sutta_id
        selected_stages = args.stages.split(",") if args.stages else default_processing_stages

        # Ensure 'judge' always runs after any replay to verify the fix
        if "judge" not in selected_stages:
            selected_stages.append("judge")

        print(f"\n>>> REPLAY MODE: {sid} (Stages: {', '.join(selected_stages)})")
        log_event(sid, "REPLAY", "START", f"Replaying stages {', '.join(selected_stages)} for {sid}")

        # Determine pattern for single file
        # Most files are named "AN {sutta_id}.json"
        pattern = f"AN {sid}.json"

        # Check if file exists
        if not (root / pattern).exists():
            # Try without "AN " prefix
            pattern = f"{sid}.json"
            if not (root / pattern).exists():
                print(f"Error: Could not find JSON file for {sid}")
                log_event(sid, "REPLAY", "FAIL", f"JSON file not found for {sid}")
                return

        # Run processing steps
        for stage_key in selected_stages:
            if stage_key not in steps_map:
                print(f"Warning: Unknown stage '{stage_key}', skipping.")
                continue

            script, script_args = steps_map[stage_key]
            # Use specific pattern and no global --vid to ensure we target ONLY this file
            full_args = ["--pattern", pattern] + script_args
            if run_script(str(root / script), full_args) != 0:
                log_event(sid, "REPLAY", "FAIL", f"FAILED at {script}")
                print(f"FAILED at {script}")
                return

        log_event(sid, "REPLAY", "DONE", f"REPLAY COMPLETE ({', '.join(selected_stages)})")
        print(f"\n>>> REPLAY COMPLETE for {sid}")
        return

    # FULL MODE (Original logic)
    if not args.url:
        print("Error: --url is required for full pipeline mode")
        return

    log_event("pipeline", "RUNNER", "START", f"Starting full pipeline for {args.url}")
    # ... rest of original logic ...
    if run_script(str(root / "01_ingest.py"), ["--url", args.url]) != 0:
        log_event("pipeline", "RUNNER", "FAIL", "FAILED at 01_ingest")
        print("FAILED at 01_ingest")
        return

    # Find the newly created JSON (master file)
    json_files = [f for f in root.glob("*.json") if not f.name.startswith("AN ")]
    if not json_files:
        log_event("pipeline", "RUNNER", "FAIL", "No ingest JSON found")
        print("Error: No ingest JSON found")
        return

    master_json = max(json_files, key=lambda p: p.stat().st_mtime)
    vid = master_json.stem # The filename is the vid

    # 2. IDENTIFY (Splits master into AN files)
    if run_script(str(root / "03_identify.py"), ["--input", str(master_json)]) != 0:
        log_event(vid, "IDENTIFY", "FAIL", "FAILED at 03_identify")
        print("FAILED at 03_identify")
        return

    # Update steps with --vid
    vid_args = ["--vid", vid]

    # 3-9. Process individual files
    # Instead of running them linearly, we "Tick" them into the Tickerplant
    # so the Subscribers can pick them up in parallel.
    sutta_files = list(root.glob("AN *.json"))
    # Only tick files modified in the last few minutes to avoid double-queuing old ones
    new_suttas = [f for f in sutta_files if (time.time() - f.stat().st_mtime) < 300]

    if not new_suttas:
        print("No new suttas identified to queue.")
        return

    print(f" -> Queuing {len(new_suttas)} suttas for the Tickerplant...")

    import sqlite3, uuid
    db_path = "C:/Users/ADMIN/Desktop/damadev/data/work/streaming/pipeline.sqlite3"
    conn = sqlite3.connect(db_path)

    for f in new_suttas:
        # Extract sutta_id from filename "AN 4.20.194.json"
        sid = f.name.replace("AN ", "").replace(".json", "")
        job_id = f"tick_{uuid.uuid4().hex[:8]}"

        try:
            conn.execute("""
                INSERT INTO jobs (job_id, event_id, worker_type, sutta_id, status)
                VALUES (?, ?, 'align', ?, 'PENDING')
            """, (job_id, f"auto_{sid}_{int(time.time())}", sid))
            print(f"    [+] Queued {sid} for alignment")
        except Exception as e:
            print(f"    [!] Failed to queue {sid}: {e}")

    conn.commit()
    conn.close()

    log_event(vid, "RUNNER", "DONE", f"INGEST COMPLETE. {len(new_suttas)} suttas queued for parallel processing.")
    print("\n>>> INGEST & IDENTIFY COMPLETE. Suttas are now in the Tickerplant queue.")

if __name__ == "__main__":
    main()
