"""
将公开日语作文/纠错数据统一整理为双模型训练样本。

支持来源：
- naist-lang8: 纠错/改写数据，主要用于 revision
- w-coleja: 学习者作文原文池，主要用于 score
- local-essay: 项目内或人工整理的作文样本，可同时用于 score / revision

输入：
- 支持 JSONL 或 JSON 数组文件
- 输入路径既可以是文件，也可以是目录；目录下会递归收集 .json/.jsonl

输出：
- revision: {"input": {...}, "output": {...}}
- score: {"input": {...}, "output": {...}}
- teacher-prompt-only: {"topic": "...", "target_level": "...", "content": "...", "teacher_prompt": "..."}
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_SCORE_REPORT = {
    "overall_score": 0,
    "task_completion_score": 0,
    "grammar_score": 0,
    "vocabulary_score": 0,
    "coherence_score": 0,
    "naturalness_score": 0,
    "jlpt_fit_score": 0,
    "level_estimate": "N5",
    "summary": "",
}

SUPPORTED_SOURCES = {"naist-lang8", "w-coleja", "local-essay"}
SUPPORTED_TASKS = {"score", "revision"}
SUPPORTED_SPLITS = {"train", "eval", "all"}


def _read_json_file(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    if path.suffix.lower() == ".jsonl":
        rows: list[dict[str, Any]] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
        return rows

    parsed = json.loads(text)
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        if isinstance(parsed.get("data"), list):
            return [item for item in parsed["data"] if isinstance(item, dict)]
        return [parsed]
    return []


def _iter_input_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    for pattern in ("*.jsonl", "*.json"):
        yield from path.rglob(pattern)


def _read_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for file_path in _iter_input_files(path):
        records.extend(_read_json_file(file_path))
    return records


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _pick(record: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return default


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\r\n", "\n").strip()


def _stable_bucket(record: dict[str, Any]) -> int:
    seed_text = "|".join(
        [
            _normalize_text(_pick(record, "content", "source_text", "original_text", "essay_text")),
            _normalize_text(_pick(record, "topic", "prompt", "title", default="")),
            _normalize_text(_pick(record, "target_level", "jlpt_level", default="N3")),
        ]
    )
    digest = hashlib.md5(seed_text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def _split_records(records: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    if split == "all":
        return records
    if split == "train":
        return [record for record in records if _stable_bucket(record) >= 10]
    return [record for record in records if _stable_bucket(record) < 10]


def _normalize_source_record(record: dict[str, Any], source: str) -> dict[str, Any]:
    if source == "naist-lang8":
        return {
            "topic": _pick(record, "topic", "prompt", "title", default=""),
            "target_level": _pick(record, "target_level", "jlpt_level", default="N3"),
            "content": _pick(record, "content", "source_text", "original_text", "essay_text"),
            "corrected_text": _pick(
                record,
                "corrected_text",
                "revision_text",
                "full_revision",
                "target_text",
                default="",
            ),
            "issues": record.get("issues", []),
            "sentence_suggestions": record.get("sentence_suggestions", []),
            "revision_notes": _pick(record, "revision_notes", "comments", default=""),
            "score_report": record.get("score_report", {}),
        }
    if source == "w-coleja":
        return {
            "topic": _pick(record, "topic", "prompt", "title", default=""),
            "target_level": _pick(record, "target_level", "jlpt_level", default="N3"),
            "content": _pick(record, "content", "essay_text", "source_text", "original_text"),
            "score_report": record.get("score_report", {}),
        }
    return {
        "topic": _pick(record, "topic", "prompt", "title", default=""),
        "target_level": _pick(record, "target_level", "jlpt_level", default="N3"),
        "content": _pick(record, "content", "essay_text", "source_text", "original_text"),
        "corrected_text": _pick(record, "corrected_text", "revision_text", "full_revision", default=""),
        "issues": record.get("issues", []),
        "sentence_suggestions": record.get("sentence_suggestions", []),
        "revision_notes": _pick(record, "revision_notes", "comments", default=""),
        "score_report": _pick(record, "score_report", "teacher_score", "labels", default={}),
    }


def normalize_revision_record(record: dict[str, Any]) -> dict[str, Any]:
    content = _normalize_text(record.get("content"))
    topic = _normalize_text(record.get("topic"))
    target_level = _normalize_text(record.get("target_level")) or "N3"
    full_revision = _normalize_text(record.get("corrected_text")) or content
    issues = record.get("issues", [])
    sentence_suggestions = record.get("sentence_suggestions", [])
    revision_notes = _normalize_text(record.get("revision_notes"))

    return {
        "input": {
            "topic": topic,
            "target_level": target_level,
            "content": content,
        },
        "output": {
            "issues": issues if isinstance(issues, list) else [],
            "sentence_suggestions": sentence_suggestions if isinstance(sentence_suggestions, list) else [],
            "full_revision": full_revision,
            "revision_notes": revision_notes,
        },
    }


def normalize_score_record(record: dict[str, Any]) -> dict[str, Any]:
    content = _normalize_text(record.get("content"))
    topic = _normalize_text(record.get("topic"))
    target_level = _normalize_text(record.get("target_level")) or "N3"
    score_report = record.get("score_report", {})
    if not isinstance(score_report, dict):
        score_report = {}

    normalized_report = {**DEFAULT_SCORE_REPORT, **score_report}
    normalized_report["summary"] = _normalize_text(normalized_report.get("summary"))
    normalized_report["level_estimate"] = _normalize_text(normalized_report.get("level_estimate")) or "N5"
    return {
        "input": {
            "topic": topic,
            "target_level": target_level,
            "content": content,
        },
        "output": normalized_report,
    }


def build_teacher_scoring_prompt(record: dict[str, Any]) -> dict[str, Any]:
    topic = _normalize_text(record.get("topic"))
    target_level = _normalize_text(record.get("target_level")) or "N3"
    content = _normalize_text(record.get("content"))
    prompt = (
        "请按 JLPT 风格对下面的日语作文评分，并严格输出 JSON。"
        "JSON 字段必须包含 overall_score, task_completion_score, grammar_score, "
        "vocabulary_score, coherence_score, naturalness_score, jlpt_fit_score, "
        "level_estimate, summary。\n"
        f"题目：{topic}\n目标等级：{target_level}\n作文：{content}"
    )
    return {
        "topic": topic,
        "target_level": target_level,
        "content": content,
        "teacher_prompt": prompt,
    }


def _validate_args(args: argparse.Namespace) -> None:
    if args.source not in SUPPORTED_SOURCES:
        raise ValueError(f"unsupported source: {args.source}")
    if args.task not in SUPPORTED_TASKS:
        raise ValueError(f"unsupported task: {args.task}")
    if args.split not in SUPPORTED_SPLITS:
        raise ValueError(f"unsupported split: {args.split}")
    if args.source == "naist-lang8" and args.task == "score" and not args.teacher_prompt_only:
        raise ValueError("naist-lang8 默认不用于 score 标签样本，只能用于 teacher prompt 或 revision")
    if args.source == "w-coleja" and args.task == "revision":
        raise ValueError("w-coleja 默认不用于 revision")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare essay datasets for score/revision SFT.")
    parser.add_argument("--input", required=True, help="Input JSON/JSONL file or directory")
    parser.add_argument("--output", required=True, help="Output JSONL path")
    parser.add_argument("--source", required=True, choices=sorted(SUPPORTED_SOURCES), help="Dataset source")
    parser.add_argument("--task", choices=sorted(SUPPORTED_TASKS), required=True, help="Target training task")
    parser.add_argument("--split", choices=sorted(SUPPORTED_SPLITS), default="all", help="train/eval/all split")
    parser.add_argument(
        "--teacher-prompt-only",
        action="store_true",
        help="For score task, emit teacher scoring prompts instead of normalized labels",
    )
    args = parser.parse_args()
    _validate_args(args)

    records = [_normalize_source_record(row, args.source) for row in _read_records(Path(args.input))]
    records = [row for row in records if _normalize_text(row.get("content"))]
    records = _split_records(records, args.split)

    if args.task == "revision":
        normalized = [normalize_revision_record(row) for row in records]
    elif args.teacher_prompt_only:
        normalized = [build_teacher_scoring_prompt(row) for row in records]
    else:
        normalized = [normalize_score_record(row) for row in records]

    _write_jsonl(Path(args.output), normalized)
    print(f"prepared {len(normalized)} rows -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
