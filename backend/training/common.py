from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from datasets import Dataset


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_jsonl_dataset(path: str | Path) -> Dataset:
    rows = _read_jsonl(path)
    return Dataset.from_list(rows)


def format_score_prompt(sample: dict[str, Any]) -> str:
    input_payload = sample["input"]
    output_payload = sample["output"]
    return (
        "<|system|>\n"
        "你是日语作文评分专家。请按 JLPT 风格输出严格 JSON。\n"
        "<|user|>\n"
        f"题目：{input_payload['topic']}\n"
        f"目标等级：{input_payload['target_level']}\n"
        f"作文：{input_payload['content']}\n"
        "<|assistant|>\n"
        f"{json.dumps(output_payload, ensure_ascii=False)}"
    )


def format_revision_prompt(sample: dict[str, Any]) -> str:
    input_payload = sample["input"]
    output_payload = sample["output"]
    return (
        "<|system|>\n"
        "你是日语作文修改专家。请输出严格 JSON，包含 issues, sentence_suggestions, full_revision, revision_notes。\n"
        "<|user|>\n"
        f"题目：{input_payload['topic']}\n"
        f"目标等级：{input_payload['target_level']}\n"
        f"作文：{input_payload['content']}\n"
        "<|assistant|>\n"
        f"{json.dumps(output_payload, ensure_ascii=False)}"
    )


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
