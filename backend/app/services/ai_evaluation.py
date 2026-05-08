"""
AI 评测服务 - 日语作文双模型编排
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings


def _clamp_score(value: float, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, int(round(value))))


def _safe_json_loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str) or not value.strip():
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _normalize_sentence(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _split_sentences(content: str) -> list[str]:
    fragments = re.split(r"(?<=[。！？!?])", content)
    sentences = [_normalize_sentence(item) for item in fragments if _normalize_sentence(item)]
    if sentences:
        return sentences
    stripped = _normalize_sentence(content)
    return [stripped] if stripped else []


@dataclass
class EssayServiceResult:
    payload: dict[str, Any]
    model_version: str


class EssayScoringService:
    """作文评分模型服务"""

    def __init__(self) -> None:
        self.url = settings.ESSAY_SCORE_MODEL_URL or settings.AI_API_URL
        self.model_name = settings.ESSAY_SCORE_MODEL_NAME
        self.timeout = settings.ESSAY_MODEL_TIMEOUT_SECONDS

    async def evaluate_essay(self, *, content: str, topic: str, target_level: str) -> EssayServiceResult:
        if self.url:
            try:
                payload = await self._call_remote_model(content=content, topic=topic, target_level=target_level)
                return EssayServiceResult(
                    payload=self._normalize_remote_payload(payload, target_level),
                    model_version=str(payload.get("model_version") or self.model_name),
                )
            except Exception:
                pass

        return EssayServiceResult(
            payload=self._generate_mock_score(content=content, topic=topic, target_level=target_level),
            model_version=self.model_name,
        )

    async def _call_remote_model(self, *, content: str, topic: str, target_level: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.url,
                json={
                    "task": "jlpt_essay_scoring",
                    "topic": topic,
                    "target_level": target_level,
                    "content": content,
                },
            )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("评分模型返回格式错误")
        return data

    def _normalize_remote_payload(self, payload: dict[str, Any], target_level: str) -> dict[str, Any]:
        return {
            "overall_score": _clamp_score(payload.get("overall_score", payload.get("overallScore", 0))),
            "task_completion_score": _clamp_score(payload.get("task_completion_score", payload.get("taskCompletionScore", 0))),
            "grammar_score": _clamp_score(payload.get("grammar_score", payload.get("grammarScore", 0))),
            "vocabulary_score": _clamp_score(payload.get("vocabulary_score", payload.get("vocabularyScore", 0))),
            "coherence_score": _clamp_score(payload.get("coherence_score", payload.get("coherenceScore", 0))),
            "naturalness_score": _clamp_score(payload.get("naturalness_score", payload.get("naturalnessScore", 0))),
            "jlpt_fit_score": _clamp_score(payload.get("jlpt_fit_score", payload.get("jlptFitScore", 0))),
            "level_estimate": str(payload.get("level_estimate", payload.get("levelEstimate", target_level))),
            "summary": str(payload.get("summary", "")),
            "comments": str(payload.get("comments", payload.get("summary", ""))),
            "ai_evaluated": True,
        }

    def _generate_mock_score(self, *, content: str, topic: str, target_level: str) -> dict[str, Any]:
        sentences = _split_sentences(content)
        word_count = len(content)
        unique_chars_ratio = len(set(content.replace(" ", ""))) / max(len(content.replace(" ", "")), 1)
        sentence_count = len(sentences)

        task_completion = _clamp_score(55 + min(word_count, 260) * 0.14)
        grammar = _clamp_score(52 + sentence_count * 5 + unique_chars_ratio * 12)
        vocabulary = _clamp_score(50 + unique_chars_ratio * 28 + min(word_count, 220) * 0.06)
        coherence = _clamp_score(48 + min(sentence_count, 6) * 7)
        naturalness = _clamp_score((grammar + coherence) / 2 - 3)
        target_bonus = 6 if target_level in {"N2", "N1"} and word_count >= 160 else 0
        jlpt_fit = _clamp_score(50 + min(word_count, 240) * 0.12 + target_bonus)
        overall = _clamp_score(
            task_completion * 0.2
            + grammar * 0.22
            + vocabulary * 0.2
            + coherence * 0.16
            + naturalness * 0.12
            + jlpt_fit * 0.1
        )
        level_estimate = self._estimate_level(overall, target_level)
        summary = (
            f"该作文围绕“{topic}”完成了基本表达，"
            f"在 {target_level} 目标下整体评定为 {level_estimate} 水平。"
            "建议继续提升语法准确性和表达自然度。"
        )
        return {
            "overall_score": overall,
            "task_completion_score": task_completion,
            "grammar_score": grammar,
            "vocabulary_score": vocabulary,
            "coherence_score": coherence,
            "naturalness_score": naturalness,
            "jlpt_fit_score": jlpt_fit,
            "level_estimate": level_estimate,
            "summary": summary,
            "comments": "已根据 JLPT 风格维度给出结构化评分与总评。",
            "ai_evaluated": False,
        }

    def _estimate_level(self, overall_score: int, target_level: str) -> str:
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
        return target_level if target_level else "N5"


class EssayRevisionService:
    """作文修改模型服务"""

    def __init__(self) -> None:
        self.url = settings.ESSAY_REVISION_MODEL_URL
        self.model_name = settings.ESSAY_REVISION_MODEL_NAME
        self.timeout = settings.ESSAY_MODEL_TIMEOUT_SECONDS

    async def revise_essay(
        self,
        *,
        content: str,
        topic: str,
        target_level: str,
        score_report: dict[str, Any],
    ) -> EssayServiceResult:
        if self.url:
            try:
                payload = await self._call_remote_model(
                    content=content,
                    topic=topic,
                    target_level=target_level,
                    score_report=score_report,
                )
                return EssayServiceResult(
                    payload=self._normalize_remote_payload(payload, content),
                    model_version=str(payload.get("model_version") or self.model_name),
                )
            except Exception:
                pass

        return EssayServiceResult(
            payload=self._generate_mock_revision(
                content=content,
                topic=topic,
                target_level=target_level,
                score_report=score_report,
            ),
            model_version=self.model_name,
        )

    async def _call_remote_model(
        self,
        *,
        content: str,
        topic: str,
        target_level: str,
        score_report: dict[str, Any],
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.url,
                json={
                    "task": "jlpt_essay_revision",
                    "topic": topic,
                    "target_level": target_level,
                    "content": content,
                    "score_report": score_report,
                },
            )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("修改模型返回格式错误")
        return data

    def _normalize_remote_payload(self, payload: dict[str, Any], content: str) -> dict[str, Any]:
        return {
            "issues": _safe_json_loads(payload.get("issues"), []),
            "sentence_suggestions": _safe_json_loads(payload.get("sentence_suggestions", payload.get("sentenceSuggestions")), []),
            "full_revision": str(payload.get("full_revision", payload.get("fullRevision", content))),
            "revision_notes": str(payload.get("revision_notes", payload.get("revisionNotes", ""))),
        }

    def _generate_mock_revision(
        self,
        *,
        content: str,
        topic: str,
        target_level: str,
        score_report: dict[str, Any],
    ) -> dict[str, Any]:
        sentences = _split_sentences(content)
        issues: list[dict[str, str]] = []
        suggestions: list[dict[str, str]] = []

        if sentences:
            first_sentence = sentences[0]
            issues.append(
                {
                    "source": first_sentence,
                    "suggestion": first_sentence.replace("です", "だと思います") if "です" in first_sentence else first_sentence,
                    "explanation": "开头句可以增加主观判断或背景信息，使论述更完整。",
                    "severity": "medium",
                }
            )

        for sentence in sentences[:3]:
            cleaned = sentence.strip()
            if not cleaned:
                continue
            suggested = cleaned
            if not re.search(r"(しかし|また|そして|そのため|一方で)", cleaned):
                suggested = f"また、{cleaned}"
            suggestions.append(
                {
                    "original": cleaned,
                    "suggested": suggested,
                    "reason": "补充连接词可以让句子之间更连贯，符合 JLPT 作文阅卷偏好。",
                }
            )

        full_revision = "\n".join(item["suggested"] for item in suggestions) if suggestions else content
        if not full_revision.strip():
            full_revision = content

        revision_notes = (
            f"此次修改围绕 {target_level} 目标，重点提升连贯性、语法自然度和话题展开。"
            f"评分模型当前给出的总分为 {score_report.get('overall_score', 0)}。"
        )
        return {
            "issues": issues,
            "sentence_suggestions": suggestions,
            "full_revision": full_revision,
            "revision_notes": revision_notes,
        }


class EssayOrchestratorService:
    """作文评测编排服务"""

    def __init__(self) -> None:
        self.scoring_service = EssayScoringService()
        self.revision_service = EssayRevisionService()

    async def evaluate_essay(self, *, content: str, topic: str, target_level: str) -> dict[str, Any]:
        score_result = await self.scoring_service.evaluate_essay(
            content=content,
            topic=topic,
            target_level=target_level,
        )
        revision_result = await self.revision_service.revise_essay(
            content=content,
            topic=topic,
            target_level=target_level,
            score_report=score_result.payload,
        )
        return {
            "score_report": score_result.payload,
            "revision_report": revision_result.payload,
            "score_model_version": score_result.model_version,
            "revision_model_version": revision_result.model_version,
        }


essay_orchestrator_service = EssayOrchestratorService()
