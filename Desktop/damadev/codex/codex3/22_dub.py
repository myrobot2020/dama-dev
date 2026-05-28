#!/usr/bin/env python3
import json
import argparse
import time
import av
from pathlib import Path
from gtts import gTTS

try:
    from .utils import atomic_write_json
except (ImportError, ValueError):
    from utils import atomic_write_json

def generate_clip(text, output_path, lang='ja'):
    """Generates a single TTS clip."""
    if not text: return False
    if output_path.exists(): return True
    try:
        tts = gTTS(text=text.replace("\n", " ").strip(), lang=lang)
        tts.save(str(output_path))
        time.sleep(1)
        return True
    except Exception as e:
        print(f"    [!] TTS Error: {e}")
        return False

def merge_clips(input_paths, output_path):
    """Merges clips into one unified MP3 using PyAV."""
    try:
        out = av.open(str(output_path), mode='w')
        stream = out.add_stream('mp3', rate=44100)
        for p in input_paths:
            if not Path(p).exists(): continue
            container = av.open(str(p))
            for frame in container.decode(audio=0):
                for packet in stream.encode(frame):
                    out.mux(packet)
            container.close()
        for packet in stream.encode():
            out.mux(packet)
        out.close()
        return True
    except Exception as e:
        print(f"    [!] Merge Error: {e}")
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", type=str, default="AN *.json")
    args = ap.parse_args()

    root = Path(__file__).parent
    files = list(root.glob(args.pattern))

    print(f"Generating and Assembling Japanese Dubs for {len(files)} files...")

    for path in files:
        if "gt2Se9HmLEs" in path.name: continue
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)

        ja = data.get("translations", {}).get("ja")
        if not ja: continue

        vid = data.get("vid")
        sutta_id_clean = data.get("sutta_id").replace(".", "_")
        temp_dir = root / "assets" / vid / "ja" / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        final_dir = root / "assets" / vid
        final_file = final_dir / f"AN_{sutta_id_clean}_ja.mp3"

        print(f" -> {data.get('sutta_id')}...")

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
            # Update JSON with the single final track
            data["audio_ja"] = f"assets/{vid}/{final_file.name}"
            atomic_write_json(path, data)
            print(f"    [OK] Final Japanese audio: {final_file.name}")

if __name__ == "__main__":
    main()
