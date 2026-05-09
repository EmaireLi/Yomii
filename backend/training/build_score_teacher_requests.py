from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


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


def build_prompt(sample: dict[str, Any]) -> str:
    input_payload = sample["input"]
    return (
        "请按 JLPT 风格对下面的日语作文评分，并严格输出 JSON。"
        "必须包含 overall_score, task_completion_score, grammar_score, vocabulary_score, "
        "coherence_score, naturalness_score, jlpt_fit_score, level_estimate, summary。\n"
        f"题目：{input_payload['topic']}\n"
        f"目标等级：{input_payload['target_level']}\n"
        f"作文：{input_payload['content']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build teacher scoring requests from score input dataset.")
    parser.add_argument("--input", required=True, help="Path to score_train or score_eval JSONL")
    parser.add_argument("--output", required=True, help="Path to teacher request JSONL")
    args = parser.parse_args()

    rows = read_jsonl(Path(args.input))
    requests = []
    for index, row in enumerate(rows):
        requests.append(
            {
                "id": f"score_req_{index}",
                "input": row["input"],
                "teacher_prompt": build_prompt(row),
            }
        )
    write_jsonl(Path(args.output), requests)
    print(f"built {len(requests)} teacher requests -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
