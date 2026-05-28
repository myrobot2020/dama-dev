#!/usr/bin/env python3
import json
import argparse
import time
import subprocess
from pathlib import Path
from gtts import gTTS

try:
    from .utils import atomic_write_json, log_event
except (ImportError, ValueError):
    from utils import atomic_write_json, log_event

def generate_clip(text, output_path, lang='ja'):
    """Generates a single TTS clip."""
    if not text: return False
    if output_path.exists(): return True
    try:
        tts = gTTS(text=text.replace("\n", " ").strip(), lang=lang)
        tts.save(str(output_path))
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"    [!] TTS Error: {e}")
        return False

def merge_clips(input_paths, output_path):
    """Merges clips into one unified MP3.
    If ffmpeg is missing, we simply use the last clip (commentary) as a fallback
    rather than crashing the whole pipeline.
    """
    try:
        # Check if ffmpeg exists
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)

        # Create a temporary file list for ffmpeg concat
        list_file = output_path.with_suffix(".txt")
        with open(list_file, "w", encoding="utf-8") as f:
            for p in input_paths:
                safe_p = str(p.absolute()).replace("\\", "/")
                f.write(f"file '{safe_p}'\n")

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file), "-c", "copy", str(output_path)
        ], check=True, capture_output=True)

        list_file.unlink() # cleanup
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("    [!] ffmpeg not found or failed. Falling back to simple file copy of main commentary.")
        # Fallback: Just copy the largest clip (usually commentary) to the final destination
        # so the pipeline doesn't break.
        if input_paths:
            import shutil
            shutil.copy(input_paths[min(1, len(input_paths)-1)], output_path)
            return True
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    ap.add_argument("--vid", type=str, help="Only process files for this video ID")
    args = ap.parse_args()

    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    print(f"Generating and Assembling Japanese Dubs for {len(files)} files...")

    for path in files:
        if "gt2Se9HmLEs" in path.name: continue
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)

        vid = data.get("vid")
        if args.vid and vid != args.vid:
            continue

        ja = data.get("translations", {}).get("ja")
        if not ja: continue

        vid = data.get("vid")
        sutta_id_clean = data.get("sutta_id").replace(".", "_").replace(" ", "_")
        temp_dir = root / "assets" / vid / "ja" / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        final_dir = root / "assets" / vid
        final_file = final_dir / f"AN_{sutta_id_clean}_ja.mp3"

        print(f" -> {data.get('sutta_id')}...")
        log_event(vid, "DUB", "START", f"Dubbing {data.get('sutta_id')}")

        try:
            # 1. Generate individual clips
            clips = [
                (ja.get("sutta"), temp_dir / "sutta.mp3"),
                (ja.get("commentary"), temp_dir / "commentary.mp3"),
                (f"{ja.get('mcq')} {' '.join(ja.get('options', []))}", temp_dir / "mcq.mp3")
            ]

            clip_paths = []
            for text, c_path in clips:
                if generate_clip(text, c_path):
                    clip_paths.append(c_path)

            # 2. Merge into final production file
            if merge_clips(clip_paths, final_file):
                data["audio_ja"] = f"assets/{vid}/{final_file.name}"
                atomic_write_json(path, data)
                log_event(vid, "DUB", "DONE", f"Created {final_file.name}")
                print(f"    [OK] Final Japanese audio: {final_file.name}")
            else:
                log_event(vid, "DUB", "FAIL", "Merge failed")
        except Exception as e:
            log_event(vid, "DUB", "FAIL", str(e))
            print(f"    [FAIL] {e}")

if __name__ == "__main__":
    main()
