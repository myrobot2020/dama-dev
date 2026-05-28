#!/usr/bin/env python3
"""Clean transcript text and commentary into publishable corpus strings."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from codex.utils import atomic_write_json


def compact_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description="Clean transcript/commentary fields.")
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()

    obj = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise SystemExit("input must contain a JSON object")
    obj["sutta"] = compact_text(str(obj.get("sutta") or ""))
    obj["commentary"] = compact_text(str(obj.get("commentary") or ""))
    out = args.output or args.input
    atomic_write_json(out, obj)
    print(f"OK {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

