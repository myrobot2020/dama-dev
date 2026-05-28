from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_SEGMENT_MODEL = os.environ.get("OLLAMA_SEGMENT_MODEL", os.environ.get("OLLAMA_MODEL", "qwen2.5:14b"))


@dataclass(frozen=True)
class Segment:
    label: str
    text: str
    confidence: float


SYSTEM_PROMPT = """You segment a long Buddhist discourse transcript into blocks.

Goal:
- Label each paragraph/block as either "sutta", "commentary", or "mixed".
- Preserve the original wording.
- Do not invent or paraphrase content.
- Use "sutta" for quoted teaching or canonical narration.
- Use "commentary" for teacher explanation, reflection, asides, and interpretation.
- Use "mixed" when a block clearly contains both and should be split later.
- Prefer conservative labels if uncertain.
- Return exactly one JSON object and nothing else.

Required JSON shape:
{
  "segments": [
    {
      "label": "sutta|commentary|mixed",
      "confidence": 0.0,
      "text": "..."
    }
  ]
}
""".strip()


USER_PROMPT = """Segment this transcript into ordered blocks.

Transcript:
{text}

Return JSON only.
""".strip()


def _split_paragraphs(text: str) -> list[str]:
    blocks = [blk.strip() for blk in text.replace("\r\n", "\n").split("\n\n")]
    return [blk for blk in blocks if blk]


def _heuristic_segments(text: str) -> list[Segment]:
    blocks = _split_paragraphs(text)
    if not blocks and text.strip():
        blocks = [text.strip()]
    out: list[Segment] = []
    for block in blocks:
        low = block.lower()
        if low.startswith(("so ", "now ", "because ", "in this ", "which means")):
            label = "commentary"
        elif "end of the sutta" in low or "end of the suta" in low or "the buddha said" in low:
            label = "sutta"
        else:
            label = "mixed" if len(block) > 800 else "commentary"
        out.append(Segment(label=label, text=block, confidence=0.5))
    return out


def _call_ollama(text: str, model: str | None = None, host: str | None = None) -> dict[str, Any]:
    host = (host or DEFAULT_OLLAMA_HOST).rstrip("/")
    model = model or DEFAULT_SEGMENT_MODEL
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT.format(text=text)},
        ],
    }
    req = urllib.request.Request(
        f"{host}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        raw = json.loads(resp.read().decode("utf-8", errors="replace"))
    content = raw.get("message", {}).get("content", "")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("ollama returned empty content")
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError("ollama returned non-object JSON")
    return parsed


def _normalize_segments(payload: dict[str, Any]) -> list[Segment]:
    segs = payload.get("segments")
    if not isinstance(segs, list):
        raise ValueError("missing segments list")
    out: list[Segment] = []
    for item in segs:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip().lower()
        if label not in {"sutta", "commentary", "mixed"}:
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        try:
            confidence = float(item.get("confidence") or 0.5)
        except Exception:
            confidence = 0.5
        out.append(Segment(label=label, text=text, confidence=max(0.0, min(1.0, confidence))))
    if not out:
        raise ValueError("no usable segments returned")
    return out


def segment_interwoven_text(text: str, *, model: str | None = None, host: str | None = None) -> list[Segment]:
    if not text.strip():
        return []
    try:
        payload = _call_ollama(text, model=model, host=host)
        return _normalize_segments(payload)
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return _heuristic_segments(text)


def project_sutta_and_commentary(text: str, *, model: str | None = None, host: str | None = None) -> tuple[str, str, list[dict[str, str | float]]]:
    segments = segment_interwoven_text(text, model=model, host=host)
    sutta_parts: list[str] = []
    commentary_parts: list[str] = []
    trace: list[dict[str, str | float]] = []
    for seg in segments:
        trace.append({"label": seg.label, "confidence": seg.confidence, "text": seg.text})
        if seg.label == "sutta":
            sutta_parts.append(seg.text)
        elif seg.label == "commentary":
            commentary_parts.append(seg.text)
        else:
            commentary_parts.append(seg.text)
    return "\n\n".join(sutta_parts).strip(), "\n\n".join(commentary_parts).strip(), trace

