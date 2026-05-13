"""
AI 评测服务 - 日语作文双模型编排
"""
from __future__ import annotations

import json
import logging
import re
import difflib
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from openai import AsyncOpenAI

from app.core.config import settings


LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
BACKEND_DEBUG_LOG = LOG_DIR / "essay_backend_debug.log"

logger = logging.getLogger("essay_backend_debug")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(BACKEND_DEBUG_LOG, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False

def _clamp_score(value: float, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, int(round(value))))


def _jlpt_rank(level: str) -> int:
    mapping = {"N5": 1, "N4": 2, "N3": 3, "N2": 4, "N1": 5}
    return mapping.get((level or "N3").upper(), 3)


def _score_to_level(score: float) -> str:
    if score >= 88:
        return "N1"
    if score >= 80:
        return "N2"
    if score >= 70:
        return "N3"
    if score >= 60:
        return "N4"
    return "N5"


def _estimate_level_from_metrics(
    *,
    grammar_score: int,
    vocabulary_score: int,
    coherence_score: int,
    naturalness_score: int,
    word_count: int,
    sentence_count: int,
) -> str:
    complexity_score = (
        grammar_score * 0.28
        + vocabulary_score * 0.3
        + coherence_score * 0.22
        + naturalness_score * 0.2
        + min(word_count, 260) * 0.02
        + min(sentence_count, 10) * 1.5
    )
    return _score_to_level(complexity_score)


def _compute_jlpt_fit_score(estimated_level: str, target_level: str) -> int:
    gap = _jlpt_rank(target_level) - _jlpt_rank(estimated_level)
    base = 82 - gap * 12 if gap >= 0 else 82 + min(abs(gap) * 5, 10)
    return _clamp_score(base, 35, 95)


def _compute_overall_score(
    *,
    task_completion_score: int,
    grammar_score: int,
    vocabulary_score: int,
    coherence_score: int,
    naturalness_score: int,
    jlpt_fit_score: int,
) -> int:
    return _clamp_score(
        task_completion_score * 0.18
        + grammar_score * 0.22
        + vocabulary_score * 0.2
        + coherence_score * 0.16
        + naturalness_score * 0.12
        + jlpt_fit_score * 0.12
    )


def _safe_json_loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str) or not value.strip():
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _truncate_text(value: Any, limit: int = 2000) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}...<truncated>"


def _normalize_sentence(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _split_sentences(content: str) -> list[str]:
    fragments = re.split(r"(?<=[。！？!?])", content)
    sentences = [_normalize_sentence(item) for item in fragments if _normalize_sentence(item)]
    if sentences:
        return sentences
    stripped = _normalize_sentence(content)
    return [stripped] if stripped else []


def _rewrite_sentence(sentence: str) -> tuple[str, str]:
    suggested = _normalize_sentence(sentence)
    if not suggested:
        return suggested, ""

    reasons: list[str] = []

    # ── 固定短语修正 ──
    rewrites: list[tuple[str, str, str]] = [
        ("朝ごはんは主に", "朝ごはんには主に", "「朝ごはんは」より「朝ごはんには」の方が自然です。"),
        ("パンと牛乳を食べます", "パンを食べて、牛乳を飲みます", "「牛乳を食べます」は不自然です。「牛乳を飲みます」が正しいです。"),
        ("簡単ですが、一日のエネルギーになります", "簡単ですが、一日を始めるためのエネルギーになります", "「一日のエネルギー」より「一日を始めるためのエネルギー」の方が明確です。"),
        ("ラーメンを飲みます", "ラーメンを食べます", "「ラーメンを飲みます」は不自然です。「ラーメンを食べます」が適切です。"),
        ("ラーメンを飲みました", "ラーメンを食べました", "「ラーメンを飲みました」は不自然です。「ラーメンを食べました」が適切です。"),
        ("映画を見てました", "映画を見ていました", "「見てました」は口語的です。「見ていました」が書き言葉として適切です。"),
        ("学校に行かなくちゃ", "学校に行かなければなりません", "「行かなくちゃ」は口語的です。作文では「行かなければなりません」が適切です。"),
        # ── な形容詞過去形 ──
        ("綺麗かった", "綺麗だった", "「綺麗」はな形容詞なので過去形は「綺麗だった」です。"),
        ("好きかった", "好きだった", "「好き」はな形容詞なので過去形は「好きだった」です。"),
        ("元気かった", "元気だった", "「元気」はな形容詞なので過去形は「元気だった」です。"),
        ("便利かった", "便利だった", "「便利」はな形容詞なので過去形は「便利だった」です。"),
        ("有名かった", "有名だった", "「有名」はな形容詞なので過去形は「有名だった」です。"),
        ("静かかった", "静かだった", "「静か」はな形容詞なので過去形は「静かだった」です。"),
        ("簡単かった", "簡単だった", "「簡単」はな形容詞なので過去形は「簡単だった」です。"),
        ("大好きかった", "大好きだった", "「大好き」はな形容詞なので過去形は「大好きだった」です。"),
        ("大変かった", "大変だった", "「大変」はな形容詞なので過去形は「大変だった」です。"),
        ("上手かった", "上手だった", "「上手」はな形容詞なので過去形は「上手だった」です。"),
        ("下手かった", "下手だった", "「下手」はな形容詞なので過去形は「下手だった」です。"),
        # ── 可能形の簡略化（〜することができる → 〜できる） ──
        ("起きることができます", "起きられます", "「起きることができます」より可能形「起きられます」の方が簡潔です。"),
        ("起きることができません", "起きられません", "可能形を使うと簡潔になります。"),
        ("食べることができます", "食べられます", "「食べることができます」より可能形「食べられます」の方が簡潔です。"),
        ("食べることができません", "食べられません", "可能形を使うと簡潔になります。"),
        ("見ることができます", "見られます", "「見ることができます」より可能形「見られます」の方が簡潔です。"),
        ("来ることができます", "来られます", "「来ることができます」より可能形「来られます」の方が簡潔です。"),
        ("することができます", "できます", "「することができます」より「できます」の方が簡潔です。"),
        ("勉強することができます", "勉強できます", "「勉強する」は「勉強できます」と可能形にできます。"),
        ("勉強することができません", "勉強できません", "可能形を使うと簡潔になります。"),
        ("旅行することができます", "旅行できます", "「旅行する」は「旅行できます」と可能形にできます。"),
        ("買い物することができます", "買い物できます", "「買い物する」は「買い物できます」と可能形にできます。"),
        ("散歩することができます", "散歩できます", "「散歩する」は「散歩できます」と可能形にできます。"),
        ("料理することができます", "料理できます", "「料理する」は「料理できます」と可能形にできます。"),
        ("洗濯することができます", "洗濯できます", "「洗濯する」は「洗濯できます」と可能形にできます。"),
        ("掃除することができます", "掃除できます", "「掃除する」は「掃除できます」と可能形にできます。"),
        ("練習することができます", "練習できます", "「練習する」は「練習できます」と可能形にできます。"),
        ("予約することができます", "予約できます", "「予約する」は「予約できます」と可能形にできます。"),
        # ── 可能形の対象「を」→「が」 ──
        ("日本語を話せます", "日本語が話せます", "可能形の対象には「が」を使います。"),
        ("漢字を書けます", "漢字が書けます", "可能形の対象には「が」を使います。"),
        ("料理を作れます", "料理が作れます", "可能形の対象には「が」を使います。"),
        ("車を運転できます", "車が運転できます", "可能形の対象には「が」を使います。"),
        # ── 場所「に」→「で」（動作） ──
        ("教室に勉強します", "教室で勉強します", "動作の場所には「で」を使います。"),
        ("図書館に本を読みます", "図書館で本を読みます", "動作の場所には「で」を使います。"),
        ("公園に遊びます", "公園で遊びます", "動作の場所には「で」を使います。"),
        ("レストランに食べます", "レストランで食べます", "動作の場所には「で」を使います。"),
        ("カフェに勉強します", "カフェで勉強します", "動作の場所には「で」を使います。"),
        # ── 生き物に「あります」→「います」 ──
        ("猫があります", "猫がいます", "生き物には「います」を使います。"),
        ("犬があります", "犬がいます", "生き物には「います」を使います。"),
        ("友達があります", "友達がいます", "人には「います」を使います。"),
        ("家族があります", "家族がいます", "人には「います」を使います。"),
        ("先生があります", "先生がいます", "人には「います」を使います。"),
        ("彼女があります", "彼女がいます", "人には「います」を使います。"),
        ("彼氏があります", "彼氏がいます", "人には「います」を使います。"),
        # ── 口語→書き言葉 ──
        ("すごい", "とても", "「すごい」は口語的です。「とても」が書き言葉として適切です。"),
        ("すごく", "非常に", "「すごく」は口語的です。「非常に」が書き言葉として適切です。"),
        ("ちょっと", "少し", "「ちょっと」より「少し」の方が書き言葉として適切です。"),
        ("やっぱり", "やはり", "「やっぱり」より「やはり」の方が書き言葉として適切です。"),
        ("じゃない", "ではない", "「じゃない」より「ではない」の方が書き言葉として適切です。"),
        ("ちゃダメ", "てはいけません", "「ちゃダメ」は口語的です。「てはいけません」が適切です。"),
        ("なくちゃ", "なければなりません", "「なくちゃ」は口語的です。「なければなりません」が適切です。"),
        ("なきゃ", "なければなりません", "「なきゃ」は口語的です。「なければなりません」が適切です。"),
        ("ちゃった", "てしまいました", "「ちゃった」は口語的です。「てしまいました」が書き言葉として適切です。"),
        ("とっても", "とても", "「とっても」は口語的です。「とても」が書き言葉として適切です。"),
        ("すごく美味しい", "とても美味しい", "「すごく」は口語的です。「とても」が適切です。"),
        ("たくさん", "多く", "「たくさん」より「多く」の方が書き言葉として適切です。"),
        ("いっぱい", "たくさん", "「いっぱい」より「たくさん」の方が書き言葉として適切です。"),
        ("ほんとに", "本当に", "「ほんとに」より「本当に」の方が書き言葉として適切です。"),
        ("ありがとう", "ありがとうございます", "丁寧な表現にしましょう。"),
        ("ごめん", "すみません", "「ごめん」は口語的です。「すみません」が適切です。"),
        ("バイト", "アルバイト", "「バイト」より「アルバイト」の方が書き言葉として適切です。"),
        # ── 「ですけど」→「ですが」 ──
        ("楽しいですけど", "楽しいですが", "「ですけど」より「ですが」の方が書き言葉として適切です。"),
        ("美味しいですけど", "美味しいですが", "「ですけど」より「ですが」の方が書き言葉として適切です。"),
        ("嬉しいですけど", "嬉しいですが", "「ですけど」より「ですが」の方が書き言葉として適切です。"),
        ("面白いですけど", "面白いですが", "「ですけど」より「ですが」の方が書き言葉として適切です。"),
        ("大変ですけど", "大変ですが", "「ですけど」より「ですが」の方が書き言葉として適切です。"),
        # ── 列挙 ──
        ("私は朝ごはんは", "私は朝ごはんを", "二重主語になっています。「朝ごはんを」が適切です。"),
        ("私は昼ごはんは", "私は昼ごはんを", "二重主語になっています。「昼ごはんを」が適切です。"),
        ("私は晩ごはんは", "私は晩ごはんを", "二重主語になっています。「晩ごはんを」が適切です。"),
        # ── 「あまり」+ 肯定 → 否定 ──
        ("あまり好きです", "あまり好きではありません", "「あまり」は否定形と一緒に使います。"),
        ("あまり美味しい", "あまり美味しくない", "「あまり」は否定形と一緒に使います。"),
        # ── 語彙の自然さ ──
        ("だいたいわかります", "だいたい分かります", "漢字を使うと読みやすくなります。"),
        ("つかいます", "使います", "漢字を使うと読みやすくなります。"),
        ("おなか", "お腹", "「おなか」より「お腹」の方が書き言葉として適切です。"),
        ("きもちいい", "気持ちいい", "漢字を使うと読みやすくなります。"),
        ("きれい", "綺麗", "「きれい」より「綺麗」の方が書き言葉として適切です。"),
        ("はなし", "話", "漢字を使うと読みやすくなります。"),
        ("べんきょう", "勉強", "漢字を使うと読みやすくなります。"),
        ("りょこう", "旅行", "漢字を使うと読みやすくなります。"),
        ("しゅみ", "趣味", "漢字を使うと読みやすくなります。"),
        ("たべもの", "食べ物", "漢字を使うと読みやすくなります。"),
        ("のみもの", "飲み物", "漢字を使うと読みやすくなります。"),
        ("まいにち", "毎日", "漢字を使うと読みやすくなります。"),
        ("ときどき", "時々", "「ときどき」より「時々」の方が適切です。"),
    ]
    for old, new, reason in rewrites:
        if old in suggested:
            suggested = suggested.replace(old, new)
            if reason:
                reasons.append(reason)

    if suggested.startswith("毎日平凡な一日ですが"):
        suggested = suggested.replace(
            "毎日平凡な一日ですが",
            "毎日は平凡に見えるかもしれませんが",
            1,
        )
        reasons.append("句首表达调整，避免「毎日平凡な一日」这种不自然的搭配。")

    # ── い形容詞の過去形ミス：面白いかった → 面白かった ──
    adj_past_fix2 = re.search(r"([^い\s])いかった", suggested)
    if adj_past_fix2 and "いいかった" not in suggested:
        fixed_str = suggested.replace(adj_past_fix2.group(0), adj_past_fix2.group(1) + "かった")
        if fixed_str != suggested:
            reasons.append(f"「{adj_past_fix2.group(0)}」は形容詞の過去形の誤りです。「{adj_past_fix2.group(1)}かった」が正しい形です。")
            suggested = fixed_str

    if not suggested.endswith(("。", "！", "？", "!", "?")):
        suggested = f"{suggested}。"

    return suggested, "；".join(reasons)


def _sort_suggestions_by_position(
    suggestions: list[dict[str, Any]], content: str, source_key: str = "original"
) -> list[dict[str, Any]]:
    """按句子在原文中出现的位置排序，确保前端展示顺序与原文一致。"""
    def _sort_key(item: dict[str, Any]) -> int:
        text = _normalize_sentence(str(item.get(source_key, "")))
        if not text:
            return len(content)
        pos = content.find(text)
        return pos if pos >= 0 else len(content)
    return sorted(suggestions, key=_sort_key)


def _build_full_revision(content: str, suggestions: list[dict[str, str]]) -> str:
    if not suggestions:
        return content

    suggestion_map: dict[str, str] = {}
    for item in suggestions:
        original = _normalize_sentence(str(item.get("original", "")))
        suggested = _normalize_sentence(str(item.get("suggested", "")))
        if original and suggested:
            suggestion_map[original] = suggested

    # 按段落切分，保留原文段落结构
    para_parts = re.split(r"(\n+)", content)
    revised_parts: list[str] = []
    for part in para_parts:
        if not part.strip() or not re.search(r"[^\s]", part):
            revised_parts.append(part)
            continue
        sentences = _split_sentences(part)
        revised_sents: list[str] = []
        for sentence in sentences:
            cleaned = _normalize_sentence(sentence)
            if not cleaned:
                continue
            revised_sents.append(suggestion_map.get(cleaned, cleaned))
        revised_parts.append("".join(revised_sents))

    full_revision = "".join(revised_parts).strip()
    return full_revision or content


def _derive_suggestions_from_revision(content: str, revised_content: str) -> list[dict[str, str]]:
    original_sentences = _split_sentences(content)
    revised_sentences = _split_sentences(revised_content)
    matcher = difflib.SequenceMatcher(a=original_sentences, b=revised_sentences, autojunk=False)
    suggestions: list[dict[str, str]] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            pair_count = min(i2 - i1, j2 - j1)
            for offset in range(pair_count):
                original = _normalize_sentence(original_sentences[i1 + offset])
                suggested = _normalize_sentence(revised_sentences[j1 + offset])
                if original and suggested and original != suggested:
                    suggestions.append(
                        {
                            "original": original,
                            "suggested": suggested,
                            "reason": "根据整篇修正版自动提取出的逐句改动。",
                        }
                    )
            continue
        if tag == "insert":
            inserted = "".join(revised_sentences[j1:j2]).strip()
            if inserted:
                suggestions.append(
                    {
                        "original": "",
                        "suggested": inserted,
                        "reason": "根据整篇修正版自动提取出的补充内容。",
                    }
                )
            continue
        if tag == "delete":
            for sentence in original_sentences[i1:i2]:
                original = _normalize_sentence(sentence)
                if original:
                    suggestions.append(
                        {
                            "original": original,
                            "suggested": "",
                            "reason": "根据整篇修正版自动提取出的删除内容。",
                        }
                    )
            continue

    return suggestions


def _effective_change_count(content: str, revision_payload: dict[str, Any]) -> int:
    suggestions = revision_payload.get("sentence_suggestions", [])
    if isinstance(suggestions, list):
        count = 0
        for item in suggestions:
            if not isinstance(item, dict):
                continue
            original = _normalize_sentence(str(item.get("original", "")))
            suggested = _normalize_sentence(str(item.get("suggested", "")))
            if original != suggested and (original or suggested):
                count += 1
        if count > 0:
            return count

    full_revision = _normalize_sentence(str(revision_payload.get("full_revision", "")))
    original = _normalize_sentence(content)
    if full_revision and full_revision != original:
        return 1
    return 0


def _content_token_set(text: str) -> set[str]:
    normalized = re.sub(r"[^\w\u3040-\u30ff\u3400-\u9fff]+", " ", text.lower())
    return {token for token in normalized.split() if len(token) >= 2}


def _revision_similarity_metrics(content: str, revised_content: str) -> dict[str, float]:
    original = _normalize_sentence(content)
    revised = _normalize_sentence(revised_content)
    if not original or not revised:
        return {"sequence_ratio": 0.0, "token_overlap": 0.0, "length_ratio": 0.0}

    sequence_ratio = difflib.SequenceMatcher(a=original, b=revised, autojunk=False).ratio()
    original_tokens = _content_token_set(original)
    revised_tokens = _content_token_set(revised)
    if not original_tokens:
        token_overlap = 1.0 if not revised_tokens else 0.0
    else:
        token_overlap = len(original_tokens & revised_tokens) / len(original_tokens)
    length_ratio = len(revised) / max(len(original), 1)
    return {
        "sequence_ratio": round(sequence_ratio, 4),
        "token_overlap": round(token_overlap, 4),
        "length_ratio": round(length_ratio, 4),
    }


def _is_revision_candidate_plausible(content: str, revision_payload: dict[str, Any]) -> tuple[bool, str, dict[str, float]]:
    revised_content = str(revision_payload.get("full_revision", "")).strip()
    metrics = _revision_similarity_metrics(content, revised_content)
    if not revised_content:
        return False, "empty_full_revision", metrics
    if _normalize_sentence(revised_content) == _normalize_sentence(content):
        return False, "unchanged_full_revision", metrics
    if metrics["length_ratio"] < 0.55:
        return False, "revision_too_short", metrics
    if metrics["length_ratio"] > 1.55:
        return False, "revision_too_long", metrics
    if metrics["sequence_ratio"] < 0.38:
        return False, "revision_low_sequence_similarity", metrics
    if metrics["token_overlap"] < 0.28:
        return False, "revision_low_token_overlap", metrics
    return True, "ok", metrics


@dataclass
class EssayServiceResult:
    payload: dict[str, Any]
    model_version: str


def _extract_json_dict(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("模型返回为空")

    candidates: list[str] = []
    fenced_matches = re.findall(r"```json\s*(\{.*?\})\s*```", text, flags=re.S | re.I)
    candidates.extend(fenced_matches)
    if text.startswith("{") and text.endswith("}"):
        candidates.append(text)

    stack = 0
    start = -1
    for idx, char in enumerate(text):
        if char == "{":
            if stack == 0:
                start = idx
            stack += 1
        elif char == "}":
            if stack > 0:
                stack -= 1
                if stack == 0 and start >= 0:
                    candidates.append(text[start:idx + 1])

    for candidate in sorted(candidates, key=len, reverse=True):
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    raise ValueError("未能从模型输出中提取有效 JSON")


class DeepSeekEssayFallbackService:
    """第三方兜底：DeepSeek V4 Flash"""

    def __init__(self) -> None:
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL.rstrip("/")
        self.model_name = settings.DEEPSEEK_MODEL
        self.timeout = settings.DEEPSEEK_TIMEOUT_SECONDS

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.model_name)

    def _build_client(self) -> AsyncOpenAI:
        if not self.enabled:
            raise RuntimeError("DeepSeek fallback is not configured")
        return AsyncOpenAI(
            api_key=self.api_key,
            base_url=f"{self.base_url}/v1",
            timeout=self.timeout,
        )

    async def score_essay(self, *, content: str, topic: str, target_level: str) -> EssayServiceResult:
        client = self._build_client()
        system_prompt = (
            "你是 JLPT 日语作文评分器。"
            "只返回一个 JSON 对象，不要 markdown，不要解释，不要代码块。"
            "字段必须包含：task_completion_score, grammar_score, vocabulary_score, "
            "coherence_score, naturalness_score, level_estimate, summary, comments。"
            "所有分数范围 0-100，level_estimate 只能是 N5/N4/N3/N2/N1。"
        )
        user_prompt = (
            f"目标等级：{target_level}\n"
            f"话题：{topic}\n"
            "请按 JLPT 风格评分下列日语作文，并严格输出 JSON：\n"
            f"{content}"
        )
        response = await client.chat.completions.create(
            model=self.model_name,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = response.choices[0].message.content or ""
        logger.info(
            "deepseek_score_raw model=%s target=%s topic=%s raw=%s",
            self.model_name,
            target_level,
            topic,
            _truncate_text(text),
        )
        payload = _extract_json_dict(text)
        return EssayServiceResult(payload=payload, model_version=self.model_name)

    async def revise_essay(
        self,
        *,
        content: str,
        topic: str,
        target_level: str,
        score_report: dict[str, Any],
    ) -> EssayServiceResult:
        client = self._build_client()
        system_prompt = (
            "你是 JLPT 日语作文修改器。"
            "只返回一个 JSON 对象，不要 markdown，不要解释，不要代码块。"
            "字段必须包含：issues, sentence_suggestions, full_revision, expanded_revision, polished_revision, revision_notes。"
            "issues 是数组，元素字段：source, suggestion, explanation, severity。"
            "sentence_suggestions 是数组，元素字段：original, suggested, reason。"
            "full_revision 必须是完整日语修正版，不能换题，不能编造与原文无关内容。"
            "expanded_revision 必须是在不跑题的前提下，围绕原题进行自然扩写。"
            "polished_revision 必须是在不改变原意的前提下，做更自然、更高级的润色。"
            "如果原文整体可接受，也必须保留原题与原意，仅做最小必要修改。"
        )
        user_prompt = (
            f"目标等级：{target_level}\n"
            f"话题：{topic}\n"
            f"当前评分：{json.dumps(score_report, ensure_ascii=False)}\n"
            "请修改下列日语作文，并严格输出 JSON：\n"
            f"{content}"
        )
        response = await client.chat.completions.create(
            model=self.model_name,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = response.choices[0].message.content or ""
        logger.info(
            "deepseek_revision_raw model=%s target=%s topic=%s raw=%s",
            self.model_name,
            target_level,
            topic,
            _truncate_text(text),
        )
        payload = _extract_json_dict(text)
        return EssayServiceResult(payload=payload, model_version=self.model_name)


class EssayScoringService:
    """作文评分模型服务"""

    def __init__(self) -> None:
        self.url = settings.ESSAY_SCORE_MODEL_URL
        self.model_name = settings.ESSAY_SCORE_MODEL_NAME
        self.timeout = settings.ESSAY_MODEL_TIMEOUT_SECONDS
        self.deepseek_fallback = DeepSeekEssayFallbackService()

    async def evaluate_essay(self, *, content: str, topic: str, target_level: str) -> EssayServiceResult:
        candidates: list[tuple[str, EssayServiceResult]] = []

        async def collect_local_candidate() -> tuple[str, EssayServiceResult] | None:
            if not self.url:
                return None
            try:
                payload = await self._call_remote_model(content=content, topic=topic, target_level=target_level)
                logger.info(
                    "score_remote_success url=%s target=%s topic=%s payload=%s",
                    self.url,
                    target_level,
                    topic,
                    _truncate_text(payload),
                )
                return (
                    "local",
                    EssayServiceResult(
                        payload=self._normalize_remote_payload(payload, target_level),
                        model_version=str(payload.get("model_version") or self.model_name),
                    ),
                )
            except Exception as exc:
                logger.exception(
                    "score_remote_failed url=%s target=%s topic=%s error=%s",
                    self.url,
                    target_level,
                    topic,
                    exc,
                )
                return None

        async def collect_deepseek_candidate() -> tuple[str, EssayServiceResult] | None:
            if not self.deepseek_fallback.enabled:
                return None
            try:
                result = await self.deepseek_fallback.score_essay(
                    content=content,
                    topic=topic,
                    target_level=target_level,
                )
                logger.info(
                    "score_deepseek_fallback_success target=%s topic=%s payload=%s",
                    target_level,
                    topic,
                    _truncate_text(result.payload),
                )
                return (
                    "deepseek",
                    EssayServiceResult(
                        payload=self._normalize_remote_payload(result.payload, target_level),
                        model_version=result.model_version,
                    ),
                )
            except Exception as exc:
                logger.exception(
                    "score_deepseek_fallback_failed target=%s topic=%s error=%s",
                    target_level,
                    topic,
                    exc,
                )
                return None

        results = await asyncio.gather(collect_local_candidate(), collect_deepseek_candidate())
        candidates.extend(candidate for candidate in results if candidate is not None)

        if candidates:
            best_label = ""
            best_result: EssayServiceResult | None = None
            best_quality = float("-inf")
            for label, candidate in candidates:
                quality = self._score_candidate_quality(candidate.payload, target_level=target_level, preferred=label == "deepseek")
                logger.info(
                    "score_candidate_quality label=%s target=%s topic=%s quality=%.2f payload=%s",
                    label,
                    target_level,
                    topic,
                    quality,
                    _truncate_text(candidate.payload),
                )
                if quality > best_quality:
                    best_quality = quality
                    best_label = label
                    best_result = candidate
            assert best_result is not None
            logger.info(
                "score_candidate_selected label=%s target=%s topic=%s quality=%.2f model=%s",
                best_label,
                target_level,
                topic,
                best_quality,
                best_result.model_version,
            )
            return best_result

        fallback = self._generate_mock_score(content=content, topic=topic, target_level=target_level)
        logger.info(
            "score_backend_fallback target=%s topic=%s payload=%s",
            target_level,
            topic,
            _truncate_text(fallback),
        )
        return EssayServiceResult(
            payload=fallback,
            model_version=self.model_name,
        )

    async def _call_remote_model(self, *, content: str, topic: str, target_level: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout, transport=httpx.AsyncHTTPTransport(retries=0)) as client:
            response = await client.post(
                self.url,
                json={
                    "task": "jlpt_essay_scoring",
                    "topic": topic,
                    "target_level": target_level,
                    "content": content,
                },
            )
        logger.info(
            "score_http_response url=%s status=%s body=%s",
            self.url,
            response.status_code,
            _truncate_text(response.text),
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("评分模型返回格式错误")
        return data

    def _normalize_remote_payload(self, payload: dict[str, Any], target_level: str) -> dict[str, Any]:
        task_completion_score = _clamp_score(payload.get("task_completion_score", payload.get("taskCompletionScore", 0)))
        grammar_score = _clamp_score(payload.get("grammar_score", payload.get("grammarScore", 0)))
        vocabulary_score = _clamp_score(payload.get("vocabulary_score", payload.get("vocabularyScore", 0)))
        coherence_score = _clamp_score(payload.get("coherence_score", payload.get("coherenceScore", 0)))
        naturalness_score = _clamp_score(payload.get("naturalness_score", payload.get("naturalnessScore", 0)))
        estimated_level = str(payload.get("level_estimate", payload.get("levelEstimate", ""))) or _score_to_level(
            (grammar_score + vocabulary_score + coherence_score + naturalness_score) / 4
        )
        jlpt_fit_score = _compute_jlpt_fit_score(estimated_level, target_level)
        overall_score = _compute_overall_score(
            task_completion_score=task_completion_score,
            grammar_score=grammar_score,
            vocabulary_score=vocabulary_score,
            coherence_score=coherence_score,
            naturalness_score=naturalness_score,
            jlpt_fit_score=jlpt_fit_score,
        )
        normalized = {
            "overall_score": overall_score,
            "task_completion_score": task_completion_score,
            "grammar_score": grammar_score,
            "vocabulary_score": vocabulary_score,
            "coherence_score": coherence_score,
            "naturalness_score": naturalness_score,
            "jlpt_fit_score": jlpt_fit_score,
            "level_estimate": estimated_level,
            "summary": str(payload.get("summary", "")),
            "comments": str(payload.get("comments", payload.get("summary", ""))),
            "ai_evaluated": True,
        }
        logger.info(
            "score_normalized target=%s payload=%s",
            target_level,
            _truncate_text(normalized),
        )
        return normalized

    def _score_candidate_quality(self, payload: dict[str, Any], *, target_level: str, preferred: bool = False) -> float:
        quality = 0.0
        if payload.get("ai_evaluated"):
            quality += 20.0
        summary = str(payload.get("summary", "")).strip()
        comments = str(payload.get("comments", "")).strip()
        quality += min(len(summary), 120) / 8.0
        quality += min(len(comments), 120) / 10.0
        if "已根据 JLPT 风格维度给出结构化评分与总评" in comments:
            quality -= 8.0
        if str(payload.get("level_estimate", "")) in {"N5", "N4", "N3", "N2", "N1"}:
            quality += 6.0
        for key in (
            "task_completion_score",
            "grammar_score",
            "vocabulary_score",
            "coherence_score",
            "naturalness_score",
            "jlpt_fit_score",
            "overall_score",
        ):
            value = int(payload.get(key, 0) or 0)
            if 0 <= value <= 100:
                quality += 2.0
        quality += min(int(payload.get("jlpt_fit_score", 0) or 0), 100) / 10.0
        if preferred:
            quality += 2.5
        return quality

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
        level_estimate = _estimate_level_from_metrics(
            grammar_score=grammar,
            vocabulary_score=vocabulary,
            coherence_score=coherence,
            naturalness_score=naturalness,
            word_count=word_count,
            sentence_count=sentence_count,
        )
        jlpt_fit = _compute_jlpt_fit_score(level_estimate, target_level)
        overall = _compute_overall_score(
            task_completion_score=task_completion,
            grammar_score=grammar,
            vocabulary_score=vocabulary,
            coherence_score=coherence,
            naturalness_score=naturalness,
            jlpt_fit_score=jlpt_fit,
        )
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

class EssayRevisionService:
    """作文修改模型服务"""

    def __init__(self) -> None:
        self.url = settings.ESSAY_REVISION_MODEL_URL
        self.model_name = settings.ESSAY_REVISION_MODEL_NAME
        self.timeout = settings.ESSAY_MODEL_TIMEOUT_SECONDS
        self.deepseek_fallback = DeepSeekEssayFallbackService()

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
                logger.info(
                    "revision_remote_success url=%s target=%s topic=%s payload=%s",
                    self.url,
                    target_level,
                    topic,
                    _truncate_text(payload),
                )
                return EssayServiceResult(
                    payload=self._normalize_remote_payload(payload, content),
                    model_version=str(payload.get("model_version") or self.model_name),
                )
            except Exception as exc:
                logger.exception(
                    "revision_remote_failed url=%s target=%s topic=%s error=%s",
                    self.url,
                    target_level,
                    topic,
                    exc,
                )
        if self.deepseek_fallback.enabled:
            try:
                result = await self.deepseek_fallback.revise_essay(
                    content=content,
                    topic=topic,
                    target_level=target_level,
                    score_report=score_report,
                )
                logger.info(
                    "revision_deepseek_fallback_success target=%s topic=%s payload=%s",
                    target_level,
                    topic,
                    _truncate_text(result.payload),
                )
                return EssayServiceResult(
                    payload=self._normalize_remote_payload(result.payload, content),
                    model_version=result.model_version,
                )
            except Exception as exc:
                logger.exception(
                    "revision_deepseek_fallback_failed target=%s topic=%s error=%s",
                    target_level,
                    topic,
                    exc,
                )

        fallback = self._generate_mock_revision(
            content=content,
            topic=topic,
            target_level=target_level,
            score_report=score_report,
        )
        logger.info(
            "revision_backend_fallback target=%s topic=%s payload=%s",
            target_level,
            topic,
            _truncate_text(fallback),
        )
        return EssayServiceResult(
            payload=fallback,
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
        async with httpx.AsyncClient(timeout=self.timeout, transport=httpx.AsyncHTTPTransport(retries=0)) as client:
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
        logger.info(
            "revision_http_response url=%s status=%s body=%s",
            self.url,
            response.status_code,
            _truncate_text(response.text),
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("修改模型返回格式错误")
        return data

    def _normalize_remote_payload(self, payload: dict[str, Any], content: str) -> dict[str, Any]:
        raw_suggestions = _safe_json_loads(payload.get("sentence_suggestions", payload.get("sentenceSuggestions")), [])
        suggestions: list[dict[str, Any]] = []
        if isinstance(raw_suggestions, list):
            for item in raw_suggestions:
                if not isinstance(item, dict):
                    continue
                normalized = {
                    **item,
                    "original": _normalize_sentence(str(item.get("original", ""))),
                    "suggested": _normalize_sentence(str(item.get("suggested", item.get("suggestion", "")))),
                    "reason": str(item.get("reason", item.get("explanation", ""))).strip(),
                }
                if normalized["original"] and normalized["suggested"] and normalized["suggested"] != normalized["original"]:
                    suggestions.append(normalized)
        suggestions = _sort_suggestions_by_position(suggestions, content, source_key="original")
        raw_issues = _safe_json_loads(payload.get("issues"), [])
        raw_issues_list = raw_issues if isinstance(raw_issues, list) else []
        # 过滤掉没有实际修改的 issue（suggestion == source）
        meaningful_issues = [
            item for item in raw_issues_list
            if isinstance(item, dict)
            and str(item.get("suggestion", "")).strip()
            and str(item.get("suggestion", "")).strip() != str(item.get("source", "")).strip()
        ]
        issues = _sort_suggestions_by_position(
            meaningful_issues,
            content,
            source_key="source",
        )
        if not suggestions and issues:
            for item in issues:
                source = _normalize_sentence(str(item.get("source", "")))
                suggestion = _normalize_sentence(str(item.get("suggestion", "")))
                if source and suggestion and source != suggestion:
                    suggestions.append(
                        {
                            "original": source,
                            "suggested": suggestion,
                            "reason": str(item.get("explanation", "")).strip(),
                            "severity": item.get("severity", "medium"),
                        }
                    )
            suggestions = _sort_suggestions_by_position(suggestions, content, source_key="original")
        built = _build_full_revision(content, suggestions)
        if built and built != content:
            full_revision = built
        else:
            model_fr = str(payload.get("full_revision", payload.get("fullRevision", ""))).strip()
            # 仅当模型 full_revision 不短于原文 50% 时才使用（防止截断丢失内容）
            if model_fr and len(model_fr) >= len(content) * 0.5:
                full_revision = model_fr
            else:
                full_revision = content

        if not suggestions and full_revision and _normalize_sentence(full_revision) != _normalize_sentence(content):
            suggestions = _derive_suggestions_from_revision(content, full_revision)
            suggestions = _sort_suggestions_by_position(suggestions, content, source_key="original")

        if not issues and suggestions:
            issues = [
                {
                    "source": item.get("original", ""),
                    "suggestion": item.get("suggested", ""),
                    "explanation": item.get("reason", "根据整篇修正版自动提取出的改动。"),
                    "severity": "medium",
                }
                for item in suggestions
                if item.get("original") != item.get("suggested")
            ]
        normalized = {
            "issues": issues,
            "sentence_suggestions": suggestions,
            "full_revision": full_revision,
            "expanded_revision": str(payload.get("expanded_revision", payload.get("expandedRevision", ""))).strip(),
            "polished_revision": str(payload.get("polished_revision", payload.get("polishedRevision", ""))).strip(),
            "revision_notes": str(payload.get("revision_notes", payload.get("revisionNotes", ""))),
            "ai_evaluated": True,
        }

        logger.info(
            "revision_normalized payload=%s",
            _truncate_text(normalized),
        )
        return normalized

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

        for sentence in sentences:
            cleaned = sentence.strip()
            if not cleaned:
                continue
            suggested, reason = _rewrite_sentence(cleaned)
            if suggested != cleaned:
                suggestions.append(
                    {
                        "original": cleaned,
                        "suggested": suggested,
                        "reason": reason or "这句做了更自然的表达调整。",
                    }
                )
                issues.append(
                    {
                        "source": cleaned,
                        "suggestion": suggested,
                        "explanation": reason or "建议改成更自然的日语表达。",
                        "severity": "medium",
                    }
                )

        full_revision = _build_full_revision(content, suggestions)
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
            "expanded_revision": "",
            "polished_revision": "",
            "revision_notes": revision_notes,
            "ai_evaluated": False,
        }


class EssayOrchestratorService:
    """作文评测编排服务"""

    def __init__(self) -> None:
        self.scoring_service = EssayScoringService()
        self.revision_service = EssayRevisionService()

    async def select_best_revision(
        self,
        *,
        content: str,
        topic: str,
        target_level: str,
        original_score_report: dict[str, Any],
        model_revision_report: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        baseline_score = int(original_score_report.get("overall_score", 0))
        candidates: list[tuple[str, dict[str, Any]]] = []

        model_full_revision = str((model_revision_report or {}).get("full_revision", "")).strip()
        if model_full_revision and model_full_revision != content.strip():
            model_change_count = _effective_change_count(content, model_revision_report)
            is_plausible, reject_reason, similarity_metrics = _is_revision_candidate_plausible(content, model_revision_report)
            logger.info(
                "revision_candidate_prepare label=model target=%s topic=%s changes=%s plausible=%s reason=%s metrics=%s",
                target_level,
                topic,
                model_change_count,
                is_plausible,
                reject_reason,
                similarity_metrics,
            )
            if model_change_count > 0 and is_plausible:
                candidates.append(("model", model_revision_report))
        else:
            model_change_count = 0

        fallback_revision = self.revision_service._generate_mock_revision(
            content=content,
            topic=topic,
            target_level=target_level,
            score_report=original_score_report,
        )
        fallback_full_revision = str(fallback_revision.get("full_revision", "")).strip()
        fallback_plausible = False
        if fallback_full_revision and fallback_full_revision != content.strip():
            fallback_plausible, fallback_reason, fallback_metrics = _is_revision_candidate_plausible(content, fallback_revision)
            logger.info(
                "revision_candidate_prepare label=fallback target=%s topic=%s changes=%s plausible=%s reason=%s metrics=%s",
                target_level,
                topic,
                _effective_change_count(content, fallback_revision),
                fallback_plausible,
                fallback_reason,
                fallback_metrics,
            )
            if fallback_full_revision != model_full_revision:
                if fallback_plausible:
                    candidates.append(("fallback", fallback_revision))

        if self.revision_service.deepseek_fallback.enabled:
            try:
                deepseek_result = await self.revision_service.deepseek_fallback.revise_essay(
                    content=content,
                    topic=topic,
                    target_level=target_level,
                    score_report=original_score_report,
                )
                deepseek_revision = self.revision_service._normalize_remote_payload(deepseek_result.payload, content)
                deepseek_full_revision = str(deepseek_revision.get("full_revision", "")).strip()
                if deepseek_full_revision and deepseek_full_revision != content.strip():
                    deepseek_change_count = _effective_change_count(content, deepseek_revision)
                    is_plausible, reject_reason, similarity_metrics = _is_revision_candidate_plausible(content, deepseek_revision)
                    logger.info(
                        "revision_candidate_prepare label=deepseek target=%s topic=%s changes=%s plausible=%s reason=%s metrics=%s",
                        target_level,
                        topic,
                        deepseek_change_count,
                        is_plausible,
                        reject_reason,
                        similarity_metrics,
                    )
                    if deepseek_change_count > 0 and is_plausible and deepseek_full_revision not in {model_full_revision, fallback_full_revision}:
                        candidates.append(
                            (
                                "deepseek",
                                {
                                    **deepseek_revision,
                                    "model_version": deepseek_result.model_version,
                                },
                            )
                        )
            except Exception as exc:
                logger.exception(
                    "revision_deepseek_prepare_failed target=%s topic=%s error=%s",
                    target_level,
                    topic,
                    exc,
                )

        if not candidates:
            logger.info(
                "revision_candidate_none target=%s topic=%s baseline=%s",
                target_level,
                topic,
                baseline_score,
            )
            existing = str(fallback_revision.get("revision_notes", "")).strip()
            if fallback_plausible:
                note = "模型修正版被判定为无效或跑题，系统已切换到规则增强修正版。"
            else:
                note = "模型修正版被判定为无效或跑题，且未找到足够可信的自动改写，已保留原文并返回保守建议。"
            fallback_revision["revision_notes"] = f"{note}\n{existing}" if existing else note
            fallback_revision["full_revision"] = fallback_full_revision or content
            return fallback_revision, None

        best_label = "model"
        best_revision = model_revision_report
        best_score_report: dict[str, Any] | None = None
        best_score = -1

        async def rescore_candidate(label: str, candidate: dict[str, Any]) -> tuple[str, dict[str, Any], int, dict[str, Any]] | None:
            revised_content = str(candidate.get("full_revision", "")).strip()
            if not revised_content:
                return None
            try:
                rescored = await self.scoring_service.evaluate_essay(
                    content=revised_content,
                    topic=topic,
                    target_level=target_level,
                )
                score_payload = rescored.payload
                overall = int(score_payload.get("overall_score", 0))
                logger.info(
                    "revision_candidate_score label=%s target=%s topic=%s baseline=%s revised=%s payload=%s",
                    label,
                    target_level,
                    topic,
                    baseline_score,
                    overall,
                    _truncate_text(score_payload),
                )
                return label, candidate, overall, score_payload
            except Exception as exc:
                logger.exception(
                    "revision_candidate_rescore_failed label=%s target=%s topic=%s error=%s",
                    label,
                    target_level,
                    topic,
                    exc,
                )
                return None

        rescore_results = await asyncio.gather(
            *(rescore_candidate(label, candidate) for label, candidate in candidates)
        )
        for result in rescore_results:
            if result is None:
                continue
            label, candidate, overall, score_payload = result
            if overall > best_score:
                best_score = overall
                best_label = label
                best_revision = {
                    **candidate,
                    "model_version": candidate.get("model_version", self.revision_service.model_name),
                }
                best_score_report = score_payload

        if best_score_report is None:
            return model_revision_report, None

        if best_label != "model":
            label_display = {
                "fallback": "规则增强修正版",
                "deepseek": "DeepSeek 兜底修正版",
            }.get(best_label, best_label)
            note = f"系统已切换到{label_display}，因为该版本复评分更高。"
            existing = str(best_revision.get("revision_notes", "")).strip()
            best_revision["revision_notes"] = f"{note}\n{existing}" if existing else note

        gain = best_score - baseline_score
        minimum_expected_gain = 5
        if gain < minimum_expected_gain:
            existing = str(best_revision.get("revision_notes", "")).strip()
            warn = (
                f"注意：修正版复评分({best_score})相较原文评分({baseline_score})提升不足 {minimum_expected_gain} 分。"
                "当前已返回候选中分数最高的版本，建议人工复核后再采纳。"
            )
            if self.revision_service.deepseek_fallback.enabled:
                warn += " 本次已纳入 DeepSeek 修订候选，但仍未达到预期提升。"
            best_revision["revision_notes"] = f"{warn}\n{existing}" if existing else warn
        else:
            existing = str(best_revision.get("revision_notes", "")).strip()
            note = f"复评分提升 {gain} 分（{baseline_score} → {best_score}）。"
            best_revision["revision_notes"] = f"{note}\n{existing}" if existing else note

        return best_revision, best_score_report

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

        result = {
            "score_report": score_result.payload,
            "revision_report": revision_result.payload,
            "score_model_version": score_result.model_version,
            "revision_model_version": revision_result.model_version,
        }

        # 对修改后的全文重新评分，对比修改前后的分数
        full_revision = (revision_result.payload or {}).get("full_revision", "")
        if full_revision and full_revision.strip() != content.strip():
            try:
                revised_score = await self.scoring_service.evaluate_essay(
                    content=full_revision,
                    topic=topic,
                    target_level=target_level,
                )
                result["revised_score_report"] = revised_score.payload
                result["revised_score_model_version"] = revised_score.model_version
            except Exception as exc:
                logger.exception("revised_scoring_failed error=%s", exc)
                result["revised_score_report"] = None

        return result


essay_orchestrator_service = EssayOrchestratorService()
