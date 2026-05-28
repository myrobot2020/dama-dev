#!/usr/bin/env python3
"""Set `valid` based on the fork's validation rules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from codex.utils import atomic_write_json, is_record_valid


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate a single JSON record.")
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()

    obj = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise SystemExit("input must contain a JSON object")
    obj["valid"] = is_record_valid(obj)
    out = args.output or args.input
    atomic_write_json(out, obj)
    print(f"OK {out} valid={obj['valid']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

