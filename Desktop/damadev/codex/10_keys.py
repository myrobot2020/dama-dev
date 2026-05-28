#!/usr/bin/env python3
"""Derive or validate the doctrinal chain for a record.

This stage is intentionally kept as a thin fork point so it can later be routed
to a CPU or light-GPU worker depending on model availability.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from codex.utils import atomic_write_json, is_record_valid


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate or attach chain data.")
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

