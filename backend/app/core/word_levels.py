"""
词汇级别映射
统一测试难度与学习计划使用的词级别规则。
"""

from __future__ import annotations

from typing import Sequence

LEVEL_TAGS: dict[str, tuple[str, ...]] = {
    "easy": ("N5", "N4"),
    "medium": ("N3",),
    "hard": ("N2", "N1"),
}

DICTIONARY_LEVEL_MAP: dict[str, str] = {
    "common": "easy",
    "daily": "medium",
    "jlpt3": "medium",
    "jlpt2": "hard",
    "jlpt1": "hard",
    "business": "hard",
}

DICTIONARY_CATALOG: list[dict[str, str | int]] = [
    {"id": "common", "name": "常用词典", "description": "基础级别（N5-N4）", "wordCount": 1500, "level": "easy"},
    {"id": "daily", "name": "日常词典", "description": "中等级别（N3）", "wordCount": 2500, "level": "medium"},
    {"id": "jlpt3", "name": "JLPT N3", "description": "中等级别（N3）", "wordCount": 3700, "level": "medium"},
    {"id": "jlpt2", "name": "JLPT N2", "description": "高级别（N2-N1）", "wordCount": 6000, "level": "hard"},
    {"id": "jlpt1", "name": "JLPT N1", "description": "高级别（N2-N1）", "wordCount": 10000, "level": "hard"},
    {"id": "business", "name": "商务词典", "description": "高级别（N2-N1）", "wordCount": 2000, "level": "hard"},
]


def get_tags_by_difficulty(difficulty: str) -> Sequence[str]:
    return LEVEL_TAGS.get(difficulty, ())


def get_tags_by_dictionary(dictionary_id: str) -> Sequence[str]:
    level = DICTIONARY_LEVEL_MAP.get(dictionary_id)
    if not level:
        return ()
    return LEVEL_TAGS.get(level, ())
