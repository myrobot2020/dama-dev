from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level JSON object")
    return data


def atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        delete=False,
        newline="\n",
    ) as tmp:
        json.dump(obj, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def has_nonempty_string(obj: dict[str, Any], key: str) -> bool:
    value = obj.get(key)
    return isinstance(value, str) and value.strip() != ""


def has_number(obj: dict[str, Any], key: str) -> bool:
    value = obj.get(key)
    return isinstance(value, (int, float))


def parse_anguttara_book_num(sutta_id: str) -> int | None:
    if not sutta_id or not isinstance(sutta_id, str):
        return None
    s = re.sub(r"^[A-Z]+\s+", "", sutta_id.strip(), flags=re.I)
    parts = s.split(".")
    if not parts:
        return None
    try:
        return int(parts[0])
    except ValueError:
        return None


def anguttara_chain_matches_book(obj: dict[str, Any], book_num: int | None) -> bool:
    if book_num is None or book_num < 1:
        return False
    ch = obj.get("chain")
    if not isinstance(ch, dict):
        return False
    items = ch.get("items")
    if not isinstance(items, list) or not items:
        return False
    if not all(isinstance(x, str) and x.strip() for x in items):
        return False
    if len(items) != book_num:
        return False
    count = ch.get("count")
    if isinstance(count, int) and count != len(items):
        return False
    return True


def eligible_record(obj: dict[str, Any], require_audio_times: bool) -> tuple[bool, str]:
    for key in ("sutta", "commentary", "aud_file"):
        if not has_nonempty_string(obj, key):
            return False, f"missing/non-empty {key}"
    if require_audio_times:
        for key in ("aud_start_s", "aud_end_s"):
            if not has_number(obj, key):
                return False, f"missing numeric {key}"
    return True, "ok"


def is_record_valid(obj: dict[str, Any]) -> bool:
    ok, _ = eligible_record(obj, require_audio_times=True)
    if not ok:
        return False
    if not has_nonempty_string(obj, "sutta_name_en"):
        return False
    sid = str(obj.get("sutta_id") or "").strip()
    if sid.lower().startswith("an"):
        return anguttara_chain_matches_book(obj, parse_anguttara_book_num(sid))
    return True

