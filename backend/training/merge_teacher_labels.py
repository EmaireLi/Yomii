from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_score_labels import validate_label_payload


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


def index_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = str(row.get("id", ""))
        if row_id:
            indexed[row_id] = row
    return indexed


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge teacher labels back into score dataset.")
    parser.add_argument("--requests", required=True, help="Teacher request JSONL")
    parser.add_argument("--labels", required=True, help="Teacher response JSONL")
    parser.add_argument("--output", required=True, help="Merged score_train JSONL")
    parser.add_argument("--rejected-output", required=True, help="Rejected teacher label JSONL")
    args = parser.parse_args()

    request_rows = read_jsonl(Path(args.requests))
    label_rows = read_jsonl(Path(args.labels))
    labels_by_id = index_by_id(label_rows)

    merged: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for request in request_rows:
        row_id = str(request.get("id", ""))
        label_row = labels_by_id.get(row_id)
        if not label_row:
            rejected.append({"id": row_id, "reason": "missing label", "raw": request})
            continue

        label_payload = label_row.get("label") if isinstance(label_row.get("label"), dict) else label_row
        ok, reason = validate_label_payload(label_payload)
        if not ok:
            rejected.append({"id": row_id, "reason": reason, "raw": label_row})
            continue

        merged.append(
            {
                "input": request["input"],
                "output": label_payload,
            }
        )

    write_jsonl(Path(args.output), merged)
    write_jsonl(Path(args.rejected_output), rejected)
    print(f"merged={len(merged)} rejected={len(rejected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
