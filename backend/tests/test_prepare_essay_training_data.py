import pytest

from scripts.prepare_essay_training_data import (
    _normalize_source_record,
    _split_records,
    build_teacher_scoring_prompt,
    normalize_revision_record,
    normalize_score_record,
)


def test_normalize_naist_revision_record():
    row = _normalize_source_record(
        {
            "source_text": "私は日本語を勉強する。",
            "corrected_text": "私は日本語を勉強しています。",
            "topic": "daily-life",
            "jlpt_level": "N3",
        },
        "naist-lang8",
    )
    normalized = normalize_revision_record(row)
    assert normalized["input"]["topic"] == "daily-life"
    assert normalized["input"]["target_level"] == "N3"
    assert normalized["output"]["full_revision"] == "私は日本語を勉強しています。"


def test_normalize_score_record_fills_defaults():
    normalized = normalize_score_record(
        {
            "topic": "travel",
            "target_level": "N2",
            "content": "旅行について書きます。",
            "score_report": {
                "overall_score": 80,
                "summary": "结构基本完整。",
            },
        }
    )
    output = normalized["output"]
    assert output["overall_score"] == 80
    assert output["summary"] == "结构基本完整。"
    assert output["grammar_score"] == 0
    assert output["level_estimate"] == "N5"


def test_teacher_prompt_contains_required_fields():
    prompt_payload = build_teacher_scoring_prompt(
        {
            "topic": "family",
            "target_level": "N4",
            "content": "私の家族を紹介します。",
        }
    )
    assert "overall_score" in prompt_payload["teacher_prompt"]
    assert "target_level" not in prompt_payload["teacher_prompt"]
    assert "目标等级：N4" in prompt_payload["teacher_prompt"]


def test_split_records_is_stable():
    records = [
        {"content": "A", "topic": "t1", "target_level": "N3"},
        {"content": "B", "topic": "t2", "target_level": "N3"},
        {"content": "C", "topic": "t3", "target_level": "N3"},
    ]
    first = _split_records(records, "train")
    second = _split_records(records, "train")
    assert first == second
    combined = _split_records(records, "train") + _split_records(records, "eval")
    assert sorted(item["content"] for item in combined) == ["A", "B", "C"]
