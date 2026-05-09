"""
词汇级别映射
统一测试难度、学习计划与数据库 word_tags 的真实标签规则。
"""

from __future__ import annotations

from typing import Any, Sequence

COMMON_TAGS: tuple[str, ...] = ("N4+N5",)
N3_TAGS: tuple[str, ...] = ("N3-高频", "N3-中低频")
N2_TAGS: tuple[str, ...] = ("N2-高频", "N2-中低频")
N1_TAGS: tuple[str, ...] = ("N1-高频", "N1-中频", "N1-低频")

LEVEL_TAGS: dict[str, tuple[str, ...]] = {
    "easy": COMMON_TAGS,
    "medium": N3_TAGS,
    "hard": (*N2_TAGS, *N1_TAGS),
    "foundation": COMMON_TAGS,
    "n3_high": ("N3-高频",),
    "n3_full": N3_TAGS,
    "n2_high": ("N2-高频",),
    "n2_full": N2_TAGS,
    "n1_high": ("N1-高频",),
    "n1_mid": ("N1-中频",),
    "n1_low": ("N1-低频",),
}

QUIZ_DIFFICULTY_CATALOG: list[dict[str, Any]] = [
    {"value": "foundation", "label": "基础（N4+N5）", "tags": list(COMMON_TAGS), "weight": 0.58, "targetSeconds": 28},
    {"value": "n3_high", "label": "N3 高频", "tags": ["N3-高频"], "weight": 0.72, "targetSeconds": 32},
    {"value": "n3_full", "label": "N3 全量", "tags": list(N3_TAGS), "weight": 0.82, "targetSeconds": 36},
    {"value": "n2_high", "label": "N2 高频", "tags": ["N2-高频"], "weight": 0.92, "targetSeconds": 42},
    {"value": "n2_full", "label": "N2 全量", "tags": list(N2_TAGS), "weight": 1.02, "targetSeconds": 48},
    {"value": "n1_high", "label": "N1 高频", "tags": ["N1-高频"], "weight": 1.12, "targetSeconds": 54},
    {"value": "n1_mid", "label": "N1 中频", "tags": ["N1-中频"], "weight": 1.2, "targetSeconds": 60},
    {"value": "n1_low", "label": "N1 低频挑战", "tags": ["N1-低频"], "weight": 1.3, "targetSeconds": 66},
]

QUIZ_DIFFICULTY_META: dict[str, dict[str, Any]] = {
    item["value"]: item for item in QUIZ_DIFFICULTY_CATALOG
}

DICTIONARY_TAG_MAP: dict[str, tuple[str, ...]] = {
    "common": COMMON_TAGS,
    "daily": ("N3-高频",),
    "jlpt3": N3_TAGS,
    "jlpt2": N2_TAGS,
    "jlpt1": N1_TAGS,
    "business": ("N2-高频", "N1-高频", "N1-中频"),
}

DICTIONARY_CATALOG: list[dict[str, Any]] = [
    {
        "id": "common",
        "name": "常用词典",
        "description": "基础级别（N4+N5）",
        "wordCount": 0,
        "level": "easy",
        "tags": list(COMMON_TAGS),
    },
    {
        "id": "daily",
        "name": "日常高频",
        "description": "N3 高频词",
        "wordCount": 0,
        "level": "medium",
        "tags": ["N3-高频"],
    },
    {
        "id": "jlpt3",
        "name": "JLPT N3",
        "description": "N3 全量（高频 + 中低频）",
        "wordCount": 0,
        "level": "medium",
        "tags": list(N3_TAGS),
    },
    {
        "id": "jlpt2",
        "name": "JLPT N2",
        "description": "N2 全量（高频 + 中低频）",
        "wordCount": 0,
        "level": "hard",
        "tags": list(N2_TAGS),
    },
    {
        "id": "jlpt1",
        "name": "JLPT N1",
        "description": "N1 全量（高频 + 中频 + 低频）",
        "wordCount": 0,
        "level": "hard",
        "tags": list(N1_TAGS),
    },
    {
        "id": "business",
        "name": "高阶高频",
        "description": "兼容旧计划，使用 N2/N1 高频标签",
        "wordCount": 0,
        "level": "hard",
        "tags": list(DICTIONARY_TAG_MAP["business"]),
    },
]


def get_tags_by_difficulty(difficulty: str) -> Sequence[str]:
    return LEVEL_TAGS.get(difficulty, COMMON_TAGS)


def get_tags_by_dictionary(dictionary_id: str) -> Sequence[str]:
    return DICTIONARY_TAG_MAP.get(dictionary_id, COMMON_TAGS)


def get_quiz_difficulty_catalog() -> Sequence[dict[str, Any]]:
    return QUIZ_DIFFICULTY_CATALOG


def get_difficulty_label(difficulty: str) -> str:
    if difficulty in QUIZ_DIFFICULTY_META:
        return str(QUIZ_DIFFICULTY_META[difficulty]["label"])
    legacy_labels = {
        "easy": "基础（N4+N5）",
        "medium": "综合（N3）",
        "hard": "综合（N2+N1）",
    }
    return legacy_labels.get(difficulty, difficulty)


def get_difficulty_weight(difficulty: str) -> float:
    if difficulty in QUIZ_DIFFICULTY_META:
        return float(QUIZ_DIFFICULTY_META[difficulty]["weight"])
    legacy_weights = {
        "easy": 0.58,
        "medium": 0.82,
        "hard": 1.06,
    }
    return legacy_weights.get(difficulty, 0.72)


def get_difficulty_target_seconds(difficulty: str) -> int:
    if difficulty in QUIZ_DIFFICULTY_META:
        return int(QUIZ_DIFFICULTY_META[difficulty]["targetSeconds"])
    legacy_targets = {
        "easy": 28,
        "medium": 36,
        "hard": 48,
    }
    return legacy_targets.get(difficulty, 40)
