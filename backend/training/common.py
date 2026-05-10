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
        "<|im_start|>system\n"
        "你是日语作文评分专家。请按 JLPT 风格输出严格 JSON。"
        "不要输出解释、不要输出 markdown、不要输出代码块，只输出一个 JSON 对象。"
        "字段必须包含 overall_score, task_completion_score, grammar_score, "
        "vocabulary_score, coherence_score, naturalness_score, jlpt_fit_score, "
        "level_estimate, summary, comments。<|im_end|>\n"
        "<|im_start|>user\n"
        f"题目：{input_payload['topic']}\n"
        f"目标等级：{input_payload['target_level']}\n"
        f"作文：{input_payload['content']}<|im_end|>\n"
        "<|im_start|>assistant\n"
        f"{json.dumps(output_payload, ensure_ascii=False)}<|im_end|>"
    )


def format_revision_prompt(sample: dict[str, Any]) -> str:
    input_payload = sample["input"]
    output_payload = sample["output"]
    return (
        "<|im_start|>system\n"
        "你是日语作文修改专家。请输出严格 JSON，字段必须包含 "
        "issues, sentence_suggestions, full_revision, revision_notes。"
        "不要输出解释、不要输出 markdown、不要输出代码块，只输出一个 JSON 对象。"
        "issues 必须是数组；sentence_suggestions 必须是数组；full_revision 必须是整篇修正版；"
        "revision_notes 必须是总结。"
        "所有 suggestion、suggested、full_revision、revision_notes 都必须使用日语，不要使用英语。<|im_end|>\n"
        "<|im_start|>user\n"
        f"题目：{input_payload['topic']}\n"
        f"目标等级：{input_payload['target_level']}\n"
        f"作文：{input_payload['content']}<|im_end|>\n"
        "<|im_start|>assistant\n"
        f"{json.dumps(output_payload, ensure_ascii=False)}<|im_end|>"
    )


def ensure_parent_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
