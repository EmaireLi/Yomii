from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {
    "overall_score",
    "task_completion_score",
    "grammar_score",
    "vocabulary_score",
    "coherence_score",
    "naturalness_score",
    "jlpt_fit_score",
    "level_estimate",
    "summary",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def validate_label_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    missing = sorted(REQUIRED_KEYS.difference(payload.keys()))
    if missing:
        return False, f"missing keys: {', '.join(missing)}"
    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate score teacher labels.")
    parser.add_argument("--input", required=True, help="Teacher label JSONL")
    parser.add_argument("--valid-output", required=True, help="Accepted label JSONL")
    parser.add_argument("--rejected-output", required=True, help="Rejected label JSONL")
    args = parser.parse_args()

    rows = read_jsonl(Path(args.input))
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for row in rows:
        payload = row.get("label") if isinstance(row.get("label"), dict) else row
        ok, reason = validate_label_payload(payload)
        if ok:
            accepted.append({"id": row.get("id"), "label": payload})
        else:
            rejected.append({"id": row.get("id"), "reason": reason, "raw": row})

    write_jsonl(Path(args.valid_output), accepted)
    write_jsonl(Path(args.rejected_output), rejected)
    print(f"accepted={len(accepted)} rejected={len(rejected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
