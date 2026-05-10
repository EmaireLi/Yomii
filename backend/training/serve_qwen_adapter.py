from __future__ import annotations

import argparse
import json
import logging
import re
import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import uvicorn


def patch_gptqmodel_awq_compat() -> None:
    try:
        import gptqmodel.nn_modules.qlinear.gemm_awq as gemm_awq
    except Exception:
        return

    if not hasattr(gemm_awq, "AwqGEMMQuantLinear") and hasattr(gemm_awq, "AwqGEMMLinear"):
        gemm_awq.AwqGEMMQuantLinear = gemm_awq.AwqGEMMLinear


patch_gptqmodel_awq_compat()
from peft import PeftModel


LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DEBUG_LOG = LOG_DIR / "essay_model_debug.log"

logger = logging.getLogger("essay_model_debug")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(MODEL_DEBUG_LOG, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


class InferRequest(BaseModel):
    task: str
    topic: str
    target_level: str
    content: str
    score_report: dict[str, Any] | None = None


def build_messages(task: str, payload: InferRequest) -> list[dict[str, str]]:
    if task == "score":
        system = (
            "你是日语作文评分专家。请按 JLPT 风格输出严格 JSON。"
            "不要输出解释、不要输出 markdown、不要输出代码块，只输出一个 JSON 对象。"
            "字段必须包含 overall_score, task_completion_score, grammar_score, "
            "vocabulary_score, coherence_score, naturalness_score, jlpt_fit_score, "
            "level_estimate, summary, comments。"
            "示例："
            '{"overall_score":78,"task_completion_score":80,"grammar_score":76,'
            '"vocabulary_score":77,"coherence_score":79,"naturalness_score":74,'
            '"jlpt_fit_score":72,"level_estimate":"N3","summary":"......","comments":"......"}'
        )
        user = (
            f"题目：{payload.topic}\n"
            f"目标等级：{payload.target_level}\n"
            f"作文：{payload.content}\n"
        )
    else:
        system = (
            "あなたは日本語作文の添削専門家です。以下のJSON形式で添削結果を出力してください。\n"
            "重要なルール：\n"
            "- すべての文字列フィールドは日本語で記述し、英語は絶対に使用しないでください\n"
            "- 出力はJSONオブジェクトのみで、Markdownやコードブロックは使用しないでください\n"
            "- **修正は元の作文の構造を維持した上で、不自然な表現のみを修正し、採点スコアが向上するように添削してください**\n"
            "- 大幅な書き換えは避け、必要最小限の修正にとどめてください（元の良さを残す）\n"
            "- 元の作文で正しい部分は変更しないでください\n"
            "出力フィールド：\n"
            "- issues: 配列、各要素は source（原文の抜粋）, suggestion（修正案）, explanation（日本語での説明）, severity（\"low\" / \"medium\" / \"high\"）\n"
            "- sentence_suggestions: 配列、各要素は original（原文）, suggested（修正文）, reason（日本語での理由）\n"
            "- full_revision: 文字列、全文を修正したバージョン（原文の良さを残しつつ不自然な箇所のみ修正）\n"
            "- revision_notes: 文字列、修正内容の日本語でのまとめ\n"
            "例（不自然な表現「牛乳を食べます」→「牛乳を飲みます」に修正し、スコアが向上する例）：\n"
            '{"issues":[{"source":"朝ごはんにパンと牛乳を食べます。","suggestion":"朝ごはんにパンを食べて、牛乳を飲みます。","explanation":"「牛乳を食べます」は不自然です。「牛乳を飲みます」が正しい表現です。","severity":"medium"}],"sentence_suggestions":[{"original":"朝ごはんにパンと牛乳を食べます。","suggested":"朝ごはんにパンを食べて、牛乳を飲みます。","reason":"「食べる」と「飲む」の使い分けをしましょう。「パンを食べる」「牛乳を飲む」が自然です。"}],"full_revision":"朝ごはんにパンを食べて、牛乳を飲みます。簡単ですが、一日を始めるためのエネルギーになります。","revision_notes":"不自然な動詞の使い分け（食べる・飲む）を修正しました。この修正により文法スコアと自然度スコアが向上します。"}'
        )
        user = (
            f"题目：{payload.topic}\n"
            f"目标等级：{payload.target_level}\n"
            f"作文：{payload.content}\n"
            f"评分参考：{json.dumps(payload.score_report or {}, ensure_ascii=False)}\n"
        )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def extract_json(text: str, required_keys: set[str]) -> dict[str, Any]:
    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if fenced_match:
        try:
            parsed = json.loads(fenced_match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    decoder = json.JSONDecoder()
    candidates: list[dict[str, Any]] = []
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            candidates.append(parsed)

    for candidate in reversed(candidates):
        if required_keys.issubset(candidate.keys()):
            return candidate

    if candidates:
        return candidates[-1]
    raise ValueError("model output does not contain valid JSON")


def extract_json_with_trace(text: str, required_keys: set[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    trace: dict[str, Any] = {
        "required_keys": sorted(required_keys),
        "fenced_found": False,
        "fenced_parse_ok": False,
        "candidate_count": 0,
        "matched_required_keys": False,
    }

    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if fenced_match:
        trace["fenced_found"] = True
        fenced_text = fenced_match.group(1)
        trace["fenced_preview"] = fenced_text[:800]
        try:
            parsed = json.loads(fenced_text)
            trace["fenced_parse_ok"] = isinstance(parsed, dict)
            if isinstance(parsed, dict):
                trace["selected_source"] = "fenced"
                trace["selected_keys"] = sorted(parsed.keys())
                return parsed, trace
        except json.JSONDecodeError as exc:
            trace["fenced_error"] = str(exc)

    decoder = json.JSONDecoder()
    candidates: list[dict[str, Any]] = []
    previews: list[dict[str, Any]] = []
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            candidates.append(parsed)
            previews.append(
                {
                    "index": index,
                    "keys": sorted(parsed.keys()),
                    "preview": text[index:index + 400],
                }
            )

    trace["candidate_count"] = len(candidates)
    trace["candidate_previews"] = previews[-3:]
    for candidate in reversed(candidates):
        if required_keys.issubset(candidate.keys()):
            trace["matched_required_keys"] = True
            trace["selected_source"] = "candidate_with_required_keys"
            trace["selected_keys"] = sorted(candidate.keys())
            return candidate, trace

    if candidates:
        trace["selected_source"] = "last_candidate"
        trace["selected_keys"] = sorted(candidates[-1].keys())
        return candidates[-1], trace

    raise ValueError("model output does not contain valid JSON")


def _split_sentences(content: str) -> list[str]:
    normalized = content.replace("。", "。\n").replace("！", "！\n").replace("？", "？\n")
    return [item.strip() for item in normalized.splitlines() if item.strip()]


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


def _rewrite_sentence(sentence: str) -> tuple[str, str]:
    suggested = sentence.strip()
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
        ("有名かった", "有名だった", "「有名」はな形容詞なので過去形は「有名だった」です。"),
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
        ("お腹が空きました", "お腹が空きました", ""),
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

    # 「毎日平凡な一日ですが」→「毎日は平凡に見えるかもしれませんが」
    if suggested.startswith("毎日平凡な一日ですが"):
        suggested = suggested.replace(
            "毎日平凡な一日ですが",
            "毎日は平凡に見えるかもしれませんが",
            1,
        )
        reasons.append("句首表达调整，避免「毎日平凡な一日」这种不自然的搭配。")

    # ── い形容詞の過去形ミス：面白いかった → 面白かった ──
    adj_past_fix = re.search(r"[く](?=いかった)", suggested)
    if adj_past_fix:
        suggested = re.sub(r"くいかった", "かった", suggested)
    # 更广匹配：任何「~~いかった」（应该是~~かった）
    adj_past_fix2 = re.search(r"([^い\s])いかった", suggested)
    if adj_past_fix2 and "いいかった" not in suggested:
        fixed_str = suggested.replace(adj_past_fix2.group(0), adj_past_fix2.group(1) + "かった")
        if fixed_str != suggested:
            reasons.append(f"「{adj_past_fix2.group(0)}」は形容詞の過去形の誤りです。「{adj_past_fix2.group(1)}かった」が正しい形です。")
            suggested = fixed_str

    if not suggested.endswith(("。", "！", "？")):
        suggested = f"{suggested}。"

    return suggested, "；".join(reasons)


def _build_full_revision(content: str, suggestions: list[dict[str, str]]) -> str:
    if not suggestions:
        return content

    suggestion_map: dict[str, str] = {}
    for item in suggestions:
        original = str(item.get("original", "")).strip()
        suggested = str(item.get("suggested", "")).strip()
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
            cleaned = sentence.strip()
            if not cleaned:
                continue
            revised_sents.append(suggestion_map.get(cleaned, cleaned))
        revised_parts.append("".join(revised_sents))

    full_revision = "".join(revised_parts).strip()
    return full_revision or content


def _extract_balanced_segment(text: str, start_index: int, open_char: str, close_char: str) -> str | None:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start_index, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return text[start_index:index + 1]
    return None


def _extract_json_value_for_key(text: str, key: str) -> str | None:
    pattern = re.compile(rf'"{re.escape(key)}"\s*:\s*', re.S)
    match = pattern.search(text)
    if not match:
        return None
    index = match.end()
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text):
        return None
    if text[index] == "[":
        return _extract_balanced_segment(text, index, "[", "]")
    if text[index] == "{":
        return _extract_balanced_segment(text, index, "{", "}")
    if text[index] == '"':
        end = index + 1
        escaped = False
        while end < len(text):
            char = text[end]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                return text[index:end + 1]
            end += 1
    return None


def recover_revision_payload(text: str) -> tuple[dict[str, Any], dict[str, Any]]:
    recovered: dict[str, Any] = {}
    trace: dict[str, Any] = {"recovered_keys": []}
    for key in ("issues", "sentence_suggestions", "full_revision", "revision_notes"):
        raw_value = _extract_json_value_for_key(text, key)
        if not raw_value:
            continue
        try:
            recovered[key] = json.loads(raw_value)
            trace["recovered_keys"].append(key)
        except json.JSONDecodeError as exc:
            trace[f"{key}_error"] = str(exc)
    return recovered, trace


def _truncate_text(value: Any, limit: int = 2000) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}...<truncated>"


_ENGLISH_PATTERN = re.compile(r"[a-zA-Z]{4,}")
_NON_JAPANESE_RATIO_THRESHOLD = 0.15


def _has_excessive_english(text: str) -> bool:
    """检测文本中是否包含过多英文字符（4字母以上英文词），用于回退兜底。"""
    if not text:
        return False
    matches = _ENGLISH_PATTERN.findall(text)
    if not matches:
        return False
    total_eng_chars = sum(len(m) for m in matches)
    return total_eng_chars / max(len(text), 1) > _NON_JAPANESE_RATIO_THRESHOLD


def _validate_revision_output(parsed: dict[str, Any], payload: InferRequest) -> dict[str, Any]:
    """检查修改输出，如有英文仅记录警告，不再回退内置兜底。"""
    for field in ("full_revision", "revision_notes"):
        value = parsed.get(field)
        if isinstance(value, str) and _has_excessive_english(value):
            logger.warning(
                "revision_english_detected field=%s value=%s, keeping model output",
                field,
                _truncate_text(value),
            )
    for field in ("issues", "sentence_suggestions"):
        items = parsed.get(field)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    for text_val in item.values():
                        if isinstance(text_val, str) and _has_excessive_english(text_val):
                            logger.warning(
                                "revision_english_detected field=%s value=%s, keeping model output",
                                field,
                                _truncate_text(text_val),
                            )
    return parsed


def _merge_score_payload(parsed: dict[str, Any], payload: InferRequest) -> dict[str, Any]:
    fallback = build_fallback_score(payload)
    merged = dict(fallback)

    for key in (
        "overall_score",
        "task_completion_score",
        "grammar_score",
        "vocabulary_score",
        "coherence_score",
        "naturalness_score",
        "jlpt_fit_score",
    ):
        if key in parsed:
            merged[key] = _clamp_score(parsed.get(key, merged[key]))

    for key in ("level_estimate", "summary", "comments"):
        value = parsed.get(key)
        if isinstance(value, str) and value.strip():
            merged[key] = value.strip()

    return merged


def _sort_suggestions_by_position(
    suggestions: list[dict[str, Any]], content: str, source_key: str = "original"
) -> list[dict[str, Any]]:
    def _sort_key(item: dict[str, Any]) -> int:
        text = str(item.get(source_key, "")).strip()
        if not text:
            return len(content)
        pos = content.find(text)
        return pos if pos >= 0 else len(content)
    return sorted(suggestions, key=_sort_key)


def _merge_revision_payload(parsed: dict[str, Any], payload: InferRequest) -> dict[str, Any]:
    fallback = build_fallback_revision(payload)
    merged = dict(fallback)

    issues = parsed.get("issues")
    if isinstance(issues, list) and issues:
        merged["issues"] = issues

    suggestions = parsed.get("sentence_suggestions")
    if isinstance(suggestions, list) and suggestions:
        normalized_suggestions: list[dict[str, Any]] = []
        for item in suggestions:
            if not isinstance(item, dict):
                continue
            normalized_suggestions.append(
                {
                    **item,
                    "original": str(item.get("original", "")).strip(),
                    "suggested": str(item.get("suggested", item.get("suggestion", ""))).strip(),
                    "reason": str(item.get("reason", item.get("explanation", ""))).strip(),
                }
            )
        merged["sentence_suggestions"] = _sort_suggestions_by_position(
            [item for item in normalized_suggestions if item["original"] and item["suggested"] and item["suggested"] != item["original"]],
            payload.content,
            source_key="original",
        )

    raw_issues = parsed.get("issues")
    if isinstance(raw_issues, list):
        # 过滤掉没有实际修改的 issue（suggestion 与 source 相同）
        meaningful_issues = [
            item for item in raw_issues
            if isinstance(item, dict)
            and str(item.get("suggestion", "")).strip()
            and str(item.get("suggestion", "")).strip() != str(item.get("source", "")).strip()
        ]
        merged["issues"] = _sort_suggestions_by_position(meaningful_issues, payload.content, source_key="source")

    built = _build_full_revision(payload.content, merged["sentence_suggestions"])
    if built and built != payload.content:
        merged["full_revision"] = built
    else:
        model_fr = parsed.get("full_revision")
        if isinstance(model_fr, str) and model_fr.strip():
            # 仅当模型 full_revision 不短于原文时才使用（防止截断丢失内容）
            if len(model_fr.strip()) >= len(payload.content.strip()) * 0.5:
                merged["full_revision"] = model_fr.strip()
    revision_notes = parsed.get("revision_notes")
    if isinstance(revision_notes, str) and revision_notes.strip():
        merged["revision_notes"] = revision_notes.strip()

    # 如果模型没有产出任何有效修改，回退到内置兜底
    if (not merged.get("issues") and not merged.get("sentence_suggestions")
            and merged.get("full_revision", "").strip() == payload.content.strip()):
        logger.warning(
            "revision_no_effective_changes falling_back_to_builtin content_len=%d",
            len(payload.content),
        )
        return build_fallback_revision(payload)

    return merged


def build_fallback_score(payload: InferRequest) -> dict[str, Any]:
    sentences = _split_sentences(payload.content)
    word_count = len(payload.content.strip())
    sentence_count = len(sentences)
    unique_ratio = len(set(payload.content.replace(" ", ""))) / max(len(payload.content.replace(" ", "")), 1)

    task_completion = _clamp_score(52 + min(word_count, 260) * 0.14)
    grammar = _clamp_score(50 + min(sentence_count, 8) * 4 + unique_ratio * 10)
    vocabulary = _clamp_score(48 + unique_ratio * 25 + min(word_count, 220) * 0.05)
    coherence = _clamp_score(50 + min(sentence_count, 6) * 6)
    naturalness = _clamp_score((grammar + coherence) / 2 - 4)
    level_estimate = _estimate_level_from_metrics(
        grammar_score=grammar,
        vocabulary_score=vocabulary,
        coherence_score=coherence,
        naturalness_score=naturalness,
        word_count=word_count,
        sentence_count=sentence_count,
    )
    jlpt_fit = _compute_jlpt_fit_score(level_estimate, payload.target_level)
    overall = _compute_overall_score(
        task_completion_score=task_completion,
        grammar_score=grammar,
        vocabulary_score=vocabulary,
        coherence_score=coherence,
        naturalness_score=naturalness,
        jlpt_fit_score=jlpt_fit,
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
        "summary": f"围绕“{payload.topic}”完成了基本表达，整体达到 {level_estimate} 参考水平。",
        "comments": "当前为 GPTQ 推理服务的结构化兜底评分结果。",
    }


def build_fallback_revision(payload: InferRequest) -> dict[str, Any]:
    sentences = _split_sentences(payload.content)
    issues: list[dict[str, str]] = []
    suggestions: list[dict[str, str]] = []

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

    full_revision = _build_full_revision(payload.content, suggestions)
    revision_notes = (
        f"此次修改围绕 {payload.target_level} 目标，重点提升连贯性、语法自然度和话题展开。"
        f"评分模型当前给出的总分为 {(payload.score_report or {}).get('overall_score', 0)}。"
    )
    return {
        "issues": issues,
        "sentence_suggestions": suggestions,
        "full_revision": full_revision,
        "revision_notes": revision_notes,
    }


def create_app(
    task: str,
    model_path: str,
    model_version: str | None,
    adapter_path: str | None,
    device_map: str,
    quantize: str | None = None,
) -> FastAPI:
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs: dict[str, Any] = {
        "device_map": device_map,
        "trust_remote_code": True,
    }
    if quantize == "bnb-nf4":
        from transformers import BitsAndBytesConfig
        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
    elif quantize == "bnb-fp4":
        from transformers import BitsAndBytesConfig
        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="fp4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
    else:
        model_kwargs["torch_dtype"] = torch.float16

    model = AutoModelForCausalLM.from_pretrained(model_path, **model_kwargs)
    if adapter_path:
        model = PeftModel.from_pretrained(model, adapter_path)
    model.eval()
    version = model_version or (Path(adapter_path).name if adapter_path else Path(model_path).name)
    app = FastAPI(title=f"qwen-gptq-{task}")

    @app.post("/infer")
    async def infer(payload: InferRequest) -> dict[str, Any]:
        expected_task = f"jlpt_essay_{'scoring' if task == 'score' else 'revision'}"
        if payload.task != expected_task:
            raise HTTPException(status_code=400, detail="task mismatch")

        messages = build_messages(task, payload)
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        model_device = next(model.parameters()).device
        inputs = {key: value.to(model_device) for key, value in tokenizer(text, return_tensors="pt").items()}
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512 if task == "score" else 1024,
                do_sample=False,
                temperature=0.2,
                pad_token_id=tokenizer.eos_token_id,
            )
        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        decoded = tokenizer.decode(generated_ids, skip_special_tokens=True)
        logger.info(
            "model_output task=%s target=%s topic=%s raw=%s",
            task,
            payload.target_level,
            payload.topic,
            _truncate_text(decoded),
        )

        required_keys = (
            {
                "overall_score",
                "task_completion_score",
                "grammar_score",
                "vocabulary_score",
                "coherence_score",
                "naturalness_score",
                "jlpt_fit_score",
                "level_estimate",
                "summary",
            }
            if task == "score"
            else {"issues", "sentence_suggestions", "full_revision", "revision_notes"}
        )

        try:
            parsed, trace = extract_json_with_trace(decoded, required_keys)
            logger.info(
                "model_parse task=%s selected_source=%s matched_required_keys=%s selected_keys=%s trace=%s",
                task,
                trace.get("selected_source"),
                trace.get("matched_required_keys"),
                trace.get("selected_keys"),
                _truncate_text(trace),
            )
            if task == "revision" and not required_keys.issubset(parsed.keys()):
                recovered, recovery_trace = recover_revision_payload(decoded)
                logger.info(
                    "model_revision_recovery recovered_keys=%s trace=%s",
                    recovery_trace.get("recovered_keys"),
                    _truncate_text(recovery_trace),
                )
                if recovered:
                    parsed = recovered

            if task == "revision":
                parsed = _validate_revision_output(parsed, payload)
        except Exception as exc:
            logger.exception(
                "model_parse_failed task=%s target=%s topic=%s error=%s",
                task,
                payload.target_level,
                payload.topic,
                exc,
            )
            parsed = build_fallback_score(payload) if task == "score" else build_fallback_revision(payload)
            logger.info(
                "model_fallback task=%s payload=%s",
                task,
                _truncate_text(parsed),
            )

        if task == "score":
            parsed = _merge_score_payload(parsed, payload)
            task_completion_score = _clamp_score(parsed.get("task_completion_score", 0))
            grammar_score = _clamp_score(parsed.get("grammar_score", 0))
            vocabulary_score = _clamp_score(parsed.get("vocabulary_score", 0))
            coherence_score = _clamp_score(parsed.get("coherence_score", 0))
            naturalness_score = _clamp_score(parsed.get("naturalness_score", 0))
            estimated_level = str(parsed.get("level_estimate", "")) or _score_to_level(
                (grammar_score + vocabulary_score + coherence_score + naturalness_score) / 4
            )
            jlpt_fit_score = _compute_jlpt_fit_score(estimated_level, payload.target_level)
            parsed["task_completion_score"] = task_completion_score
            parsed["grammar_score"] = grammar_score
            parsed["vocabulary_score"] = vocabulary_score
            parsed["coherence_score"] = coherence_score
            parsed["naturalness_score"] = naturalness_score
            parsed["jlpt_fit_score"] = jlpt_fit_score
            parsed["level_estimate"] = estimated_level
            parsed["overall_score"] = _compute_overall_score(
                task_completion_score=task_completion_score,
                grammar_score=grammar_score,
                vocabulary_score=vocabulary_score,
                coherence_score=coherence_score,
                naturalness_score=naturalness_score,
                jlpt_fit_score=jlpt_fit_score,
            )
        else:
            parsed = _merge_revision_payload(parsed, payload)

        parsed["ai_evaluated"] = True
        parsed["model_version"] = version
        logger.info(
            "model_response task=%s payload=%s",
            task,
            _truncate_text(parsed),
        )
        return parsed

    return app


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve Qwen model as an HTTP inference service.")
    parser.add_argument("--task", choices=["score", "revision"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter", default="")
    parser.add_argument("--model-version", default="")
    parser.add_argument("--device-map", default="cpu")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument(
        "--quantize",
        default=None,
        choices=["bnb-nf4", "bnb-fp4"],
        help="Quantization mode for merged models (no adapter needed at inference). Overrides torch_dtype.",
    )
    args = parser.parse_args()

    app = create_app(
        args.task,
        args.model,
        args.model_version or None,
        args.adapter or None,
        args.device_map,
        quantize=args.quantize,
    )
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
