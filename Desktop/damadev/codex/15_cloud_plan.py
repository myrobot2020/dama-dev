#!/usr/bin/env python3
"""Emit the proposed cloud split for the pipeline."""

from __future__ import annotations

import json

from codex.config import CONTAINER_ROLES


def main() -> int:
    print(json.dumps(CONTAINER_ROLES, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

