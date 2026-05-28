import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scripts.pipeline.streaming.db import DEFAULT_DB_PATH, connect, init_db
from scripts.pipeline.streaming.events import publish_event, utc_now
from scripts.pipeline.streaming.artifacts import record_artifact
from scripts.pipeline.streaming.segmentation import project_sutta_and_commentary

DEFAULT_SEGMENT_MODEL = os.environ.get("OLLAMA_SEGMENT_MODEL", os.environ.get("OLLAMA_MODEL", "qwen2.5:14b"))
DEFAULT_YT_DLP = (
    os.environ.get("YT_DLP_BIN")
    or r"C:\Users\ADMIN\Miniconda3\Scripts\yt-dlp.exe"
    or shutil.which("yt-dlp")
    or "yt-dlp"
)

# Regex to find Sutta IDs like 8.2.18 or 1.1
SUTTA_ID_RE = re.compile(r"\b(\d{1,3})\.(\d{1,3})(?:\.(\d{1,3}))?\b")

def split_transcript_heuristic(text: str) -> tuple[str, str]:
    """First sutta block vs teacher commentary (intro + discussion)."""
    t = text.strip()
    if not t:
        return "", ""
    low = t.lower()
    start_phrase = "thus have i heard"
    # Match "end of the suta" or "end of the sutta"
    m_end = re.search(r"end\s+of\s+the\s+sut+a", low)
    i = low.find(start_phrase)
    if i >= 0:
        if m_end:
            j = m_end.start()
            end_len = m_end.end() - m_end.start()
            sutta = t[i : j + end_len].strip()
            before = t[:i].strip()
            after = t[j + end_len :].strip()
            commentary = (before + " " + after).strip()
            return sutta, commentary
        sutta = t[i : i + 3200]
        commentary = (t[:i].strip() + " " + t[i + 3200 :].strip()).strip()
        return sutta.strip(), commentary.strip()
    if len(t) <= 700:
        return t, ""
    return t[:550].strip(), t[550:].strip()

def chain_from_title(sutta_name_en: str, sutta: str) -> dict:
    name = (sutta_name_en or "").strip()
    first = (name.split()[0].lower() if name else "teaching").strip(".,;:")
    low_s = sutta.lower()
    if "crossing the flood" in low_s:
        items = ["crossing the flood"]
        cat = "simile"
    elif first and first not in ("part", "chapter", "introduction"):
        items = [first]
        cat = "single factor"
    else:
        items = [name[:48].lower() if name else "exposition"]
        cat = "teacher exposition"
    return {
        "items": items,
        "count": len(items),
        "is_ordered": True,
        "category": cat,
    }

def youtube_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "youtu.be" in host:
        return parsed.path.strip("/").split("/")[0] or None
    if "youtube.com" in host:
        query_id = parse_qs(parsed.query).get("v", [""])[0].strip()
        if query_id: return query_id
        parts = [p for p in parsed.path.split("/") if p]
        for marker in ("shorts", "embed", "live"):
            if marker in parts:
                idx = parts.index(marker)
                if idx + 1 < len(parts): return parts[idx + 1]
    return None

def parse_sutta_id_from_text(text: str, default="SUTTA") -> str:
    match = re.search(r"\b(AN|SN|DN|MN|KN)\s*(\d+)[\.\s]+(\d+(?:\.\d+)*)\b", text, re.IGNORECASE)
    if match:
        return f"{match.group(1).upper()} {match.group(2)}.{match.group(3)}"

    # Fallback to pure numbers if nikaya is missing but structure is there
    match = SUTTA_ID_RE.search(text)
    if match:
        return f"{default} {match.group(0)}"

    return f"{default}_{uuid.uuid4().hex[:8]}"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def download_audio_and_transcript(url: str, video_id: str) -> tuple[Path, Path]:
    out_dir = Path("data/work/streaming/audio")
    caption_dir = Path("data/work/streaming/transcripts")
    out_dir.mkdir(parents=True, exist_ok=True)
    caption_dir.mkdir(parents=True, exist_ok=True)

    stem = f"yt_{video_id}"
    audio_template = out_dir / f"{stem}.%(ext)s"
    caption_template = caption_dir / f"{stem}.%(ext)s"

    print(f"Cave man pull audio and transcript for {video_id} grunt.")

    # Download Audio
    subprocess.run(
        [DEFAULT_YT_DLP, "--ignore-config", "-f", "bestaudio[ext=m4a]/bestaudio/best", "--no-playlist", "-o", str(audio_template), url],
        check=True,
        timeout=600
    )

    # Download Captions (Transcript)
    subprocess.run(
        [
            DEFAULT_YT_DLP, "--ignore-config", "--skip-download", "--write-auto-subs", "--write-subs",
            "--sub-langs", "en.*", "--sub-format", "json3",
            "--no-playlist", "-o", str(caption_template), url
        ],
        check=True,
        timeout=180
    )

    audio_path = None
    for ext in [".m4a", ".webm", ".mp3", ".opus"]:
        p = out_dir / f"{stem}{ext}"
        if p.exists():
            audio_path = p
            break

    caption_path = None
    for p in caption_dir.glob(f"{stem}.*.json3"):
        caption_path = p
        break

    if not audio_path:
        raise FileNotFoundError(f"Audio fail for {video_id}")
    if not caption_path:
        raise FileNotFoundError(f"Transcript fail for {video_id}")

    return audio_path, caption_path

def detect_multi_sutta_boundaries(text: str) -> list[tuple[str, int, int]]:
    """Find segments in transcript. Returns list of (sutta_id, start_char, end_char)."""
    boundaries = []
    # We look for "end of the suta" as the primary splitter
    # and Sutta IDs as labels.

    # 1. Find all Sutta ID mentions
    id_matches = list(SUTTA_ID_RE.finditer(text))

    # 2. Find all "end of the suta" markers
    end_matches = list(re.finditer(r"end\s+of\s+the\s+sut+a", text, re.IGNORECASE))

    if not id_matches:
        return [("UNKNOWN", 0, len(text))]

    # Cave man logic: Each "end of the suta" marks the end of a segment.
    # The Sutta ID for that segment is the most recent ID mentioned before the end.
    last_pos = 0
    segments = []

    for end_m in end_matches:
        end_pos = end_m.end()
        # Find the ID just before this end
        best_id = "UNKNOWN"
        for id_m in id_matches:
            if id_m.start() < end_pos:
                best_id = id_m.group(0)
            else:
                break

        segments.append((best_id, last_pos, end_pos))
        last_pos = end_pos

    # Add trailing segment if exists
    if last_pos < len(text):
        # Look for an ID in the remaining text
        best_id = "UNKNOWN"
        for id_m in id_matches:
            if id_m.start() >= last_pos:
                best_id = id_m.group(0)
                break
        segments.append((best_id, last_pos, len(text)))

    return segments

def ingest_url(db_path: Path, url: str) -> list[str]:
    url = url.strip()
    vid = youtube_video_id(url)
    if not vid:
        print("Could not identify Video ID grunt.")
        return []

    uri = f"https://www.youtube.com/watch?v={vid}"
    print(f"Cave man ingesting URL: {uri} grunt.")

    # Tell the dashboard we started
    with connect(db_path) as conn:
        publish_event(
            conn,
            event_type="source.ingest.started",
            payload={"source_id": f"yt:{vid}", "source_uri": uri},
            publisher="01_ingest_script"
        )
        conn.commit()

    # 1. Fetch metadata (FAST)
    cmd = [DEFAULT_YT_DLP, "--ignore-config", "--dump-single-json", "--no-playlist", "--no-warnings", uri]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=60)
        metadata = json.loads(out.decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"Metadata fetch fail: {e}")
        return []

    title = metadata.get("title") or "Unknown Video"

    # 2. Download Audio & Transcript (SLOW)
    try:
        audio_path, transcript_path = download_audio_and_transcript(uri, vid)
        audio_hash = sha256_file(audio_path)
        transcript_hash = sha256_file(transcript_path)

        # Load transcript text
        raw_transcript_json = json.loads(transcript_path.read_text(encoding="utf-8"))
        full_text_parts = []
        for event in raw_transcript_json.get("events", []):
            if "segs" in event:
                for seg in event["segs"]:
                    if "utf8" in seg:
                        full_text_parts.append(seg["utf8"])
            elif "text" in event:
                full_text_parts.append(event["text"])

        # Preserve double newlines for segmentation
        full_text = "".join(full_text_parts)
        full_text = re.sub(r"[ \t]+", " ", full_text) # collapse horizontal space only
        full_text = full_text.replace("\n\n\n", "\n\n").strip()

        # 3. Detect Multiple Suttas
        segments = detect_multi_sutta_boundaries(full_text)
        print(f"Found {len(segments)} segments in transcript grunt.")

        sutta_results = []

        for sid_raw, start, end in segments:
            # Snap to a better ID format
            if len(segments) == 1:
                sutta_id = parse_sutta_id_from_text(title, sid_raw)
            else:
                prefix_match = re.search(r"\b(AN|SN|DN|MN|KN)\b", title, re.IGNORECASE)
                prefix = prefix_match.group(1).upper() if prefix_match else "AN"
                sutta_id = f"{prefix} {sid_raw}" if sid_raw != "UNKNOWN" else f"UNKNOWN_{uuid.uuid4().hex[:4]}"

            segment_text = full_text[start:end].strip()
            if len(segment_text) < 100:
                continue

            # --- COMMIT DISCOVERY ---
            with connect(db_path) as conn:
                conn.execute(
                    "insert or ignore into source_records (source_id, source_type, source_uri, dedupe_key, sutta_hint, status, metadata_json, created_at) values (?, ?, ?, ?, ?, 'discovered', ?, ?)",
                    (f"yt:{vid}:{sutta_id}", "youtube", uri, f"yt:{vid}:{sutta_id}", sutta_id, json.dumps({"title": title, "segment": sid_raw}), utc_now())
                )
                publish_event(
                    conn,
                    event_type="source.sutta.discovered",
                    payload={"sutta_id": sutta_id, "source_uri": uri, "source_id": f"yt:{vid}"},
                    publisher="01_ingest_script"
                )
                conn.commit()

            # 4. Separate Sutta vs Commentary (Heuristic only)
            sutta_text, commentary_text = split_transcript_heuristic(segment_text)

            # 5. Record Artifacts and Events (Background)
            with connect(db_path) as conn:
                record_artifact(
                    conn,
                    artifact_type="audio",
                    sutta_id=sutta_id,
                    local_uri=str(audio_path).replace("\\", "/"),
                    sha256=audio_hash,
                    created_by="01_ingest_script"
                )
                record_artifact(
                    conn,
                    artifact_type="transcript",
                    sutta_id=sutta_id,
                    local_uri=str(transcript_path).replace("\\", "/"),
                    sha256=transcript_hash,
                    created_by="01_ingest_script"
                )
                publish_event(
                    conn,
                    event_type="segments.completed",
                    payload={
                        "sutta_id": sutta_id,
                        "source_uri": uri,
                        "sutta_chars": len(sutta_text),
                    },
                    publisher="01_ingest_script"
                )
                conn.commit()

            sutta_results.append({
                "sutta_id": sutta_id,
                "sutta_text": sutta_text
            })

        return {
            "url": uri,
            "title": title,
            "suttas": sutta_results
        }

    except Exception as e:
        print(f"Ingest fail grunt: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()

    init_db(args.db)
    result = ingest_url(args.db, args.url)

    if result:
        print(f"JSON_OUTPUT:{json.dumps(result, ensure_ascii=False, indent=2)}")
    else:
        print("Ingest failed.")

if __name__ == "__main__":
    main()
