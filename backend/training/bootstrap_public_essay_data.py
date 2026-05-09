from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from datasets import load_dataset
from huggingface_hub import hf_hub_download


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "essay_raw"


def _normalize_text(value: Any) -> str:
    return str(value or "").replace("\r\n", "\n").strip()


def _clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _split_sentences(content: str) -> list[str]:
    normalized = content.replace("。", "。\n").replace("！", "！\n").replace("？", "？\n")
    return [item.strip() for item in normalized.splitlines() if item.strip()]


def _estimate_level(overall_score: int, target_level: str) -> str:
    if overall_score >= 88:
        return "N1"
    if overall_score >= 80:
        return "N2"
    if overall_score >= 70:
        return "N3"
    if overall_score >= 60:
        return "N4"
    if overall_score >= 45:
        return "N5"
    return target_level or "N5"


def build_mock_score(*, content: str, topic: str, target_level: str) -> dict[str, Any]:
    sentences = _split_sentences(content)
    char_count = len(content)
    unique_chars_ratio = len(set(content.replace(" ", ""))) / max(len(content.replace(" ", "")), 1)
    sentence_count = len(sentences)

    task_completion = _clamp_score(55 + min(char_count, 260) * 0.14)
    grammar = _clamp_score(52 + sentence_count * 5 + unique_chars_ratio * 12)
    vocabulary = _clamp_score(50 + unique_chars_ratio * 28 + min(char_count, 220) * 0.06)
    coherence = _clamp_score(54 + min(sentence_count, 8) * 5 + min(char_count, 240) * 0.04)
    naturalness = _clamp_score(48 + unique_chars_ratio * 22 + min(char_count, 240) * 0.05)
    jlpt_fit = _clamp_score(50 + min(char_count, 220) * 0.07 + min(sentence_count, 7) * 4)
    overall = _clamp_score(
        task_completion * 0.17
        + grammar * 0.18
        + vocabulary * 0.17
        + coherence * 0.16
        + naturalness * 0.14
        + jlpt_fit * 0.18
    )
    level_estimate = _estimate_level(overall, target_level)
    return {
        "overall_score": overall,
        "task_completion_score": task_completion,
        "grammar_score": grammar,
        "vocabulary_score": vocabulary,
        "coherence_score": coherence,
        "naturalness_score": naturalness,
        "jlpt_fit_score": jlpt_fit,
        "level_estimate": level_estimate,
        "summary": (
            f"该作文围绕“{topic}”完成了基本表达，"
            f"在 {target_level} 目标下整体评定为 {level_estimate} 水平。"
            "建议继续提升语法准确性和表达自然度。"
        ),
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def download_revision_rows(limit: int) -> list[dict[str, Any]]:
    dataset = load_dataset("huytd189/japanese-grammar-correction", split="train")
    rows: list[dict[str, Any]] = []
    for row in dataset.select(range(min(limit, len(dataset)))):
        difficulty = _normalize_text(row.get("difficulty_level")) or "intermediate"
        target_level = {
            "beginner": "N5",
            "elementary": "N4",
            "intermediate": "N3",
            "advanced": "N2",
        }.get(difficulty.lower(), "N3")
        rows.append(
            {
                "topic": "grammar-correction",
                "target_level": target_level,
                "content": _normalize_text(row.get("incorrect_text")),
                "corrected_text": _normalize_text(row.get("correct_text")),
                "revision_notes": _normalize_text(row.get("explanation")),
                "issues": [
                    {
                        "type": _normalize_text(row.get("error_type")) or "grammar",
                        "original": _normalize_text(row.get("error_location")),
                        "suggestion": _normalize_text(row.get("correct_text")),
                        "explanation": _normalize_text(row.get("explanation")),
                    }
                ],
                "sentence_suggestions": [],
            }
        )
    return rows


def download_score_rows_from_creative_writing(limit: int, *, target_level: str) -> list[dict[str, Any]]:
    parquet_path = Path(
        hf_hub_download(
            repo_id="Aratako/Japanese-Creative-Writing-39.6k",
            repo_type="dataset",
            filename="data/train-00000-of-00002.parquet",
        )
    )
    frame = pd.read_parquet(parquet_path).head(limit)
    rows: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        topic = _normalize_text(row.get("instruction_1")) or _normalize_text(row.get("instruction_2")) or "creative-writing"
        content = _normalize_text(row.get("output_1")) or _normalize_text(row.get("output_2"))
        if not content:
            continue
        rows.append(
            {
                "topic": topic[:120],
                "target_level": target_level,
                "content": content,
                "score_report": build_mock_score(content=content, topic=topic[:120], target_level=target_level),
            }
        )
    return rows


def download_score_rows_from_revision(limit: int, *, target_level: str) -> list[dict[str, Any]]:
    dataset = load_dataset("huytd189/japanese-grammar-correction", split="train")
    rows: list[dict[str, Any]] = []
    for row in dataset.select(range(min(limit, len(dataset)))):
        topic = _normalize_text(row.get("error_type")) or "grammar-correction"
        content = _normalize_text(row.get("correct_text")) or _normalize_text(row.get("incorrect_text"))
        if not content:
            continue
        rows.append(
            {
                "topic": topic,
                "target_level": target_level,
                "content": content,
                "score_report": build_mock_score(content=content, topic=topic, target_level=target_level),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Download public essay corpora into local raw JSONL files.")
    parser.add_argument("--revision-limit", type=int, default=256)
    parser.add_argument("--score-limit", type=int, default=128)
    parser.add_argument("--target-level", default="N3")
    parser.add_argument(
        "--score-source",
        choices=["grammar-correction", "creative-writing"],
        default="grammar-correction",
    )
    parser.add_argument(
        "--hf-home",
        default=str(ROOT / ".cache" / "huggingface"),
        help="Hugging Face cache directory on D:.",
    )
    args = parser.parse_args()

    Path(args.hf_home).mkdir(parents=True, exist_ok=True)

    revision_rows = download_revision_rows(args.revision_limit)
    if args.score_source == "creative-writing":
        score_rows = download_score_rows_from_creative_writing(args.score_limit, target_level=args.target_level)
    else:
        score_rows = download_score_rows_from_revision(args.score_limit, target_level=args.target_level)

    revision_path = RAW_DIR / "public_revision.jsonl"
    score_path = RAW_DIR / "public_score.jsonl"
    _write_jsonl(revision_path, revision_rows)
    _write_jsonl(score_path, score_rows)

    print(json.dumps({"revision_rows": len(revision_rows), "score_rows": len(score_rows), "revision_path": str(revision_path), "score_path": str(score_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
