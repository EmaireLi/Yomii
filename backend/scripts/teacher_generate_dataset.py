"""
Teacher-guided synthetic dataset generation for Japanese essay scoring and revision.

Uses a strong LLM (Claude, GPT-4, etc.) to generate training data for fine-tuning
a smaller student model (Qwen3-1.7B). Each API call produces one complete sample:
learner essay + JLPT-style score report + revision output.

Usage:
    # Using Anthropic Claude
    python teacher_generate_dataset.py --api-type anthropic --api-key sk-ant-... --samples 1000

    # Using OpenAI-compatible API
    python teacher_generate_dataset.py --api-type openai --api-key sk-... --model gpt-4o-mini --samples 1000

    # Using a local OpenAI-compatible endpoint (vLLM, Ollama, etc.)
    python teacher_generate_dataset.py --api-type openai --api-key EMPTY --base-url http://localhost:8000/v1 --model local-model --samples 200

    # Resume from checkpoint
    python teacher_generate_dataset.py --api-type anthropic --api-key sk-ant-... --resume

Cost estimate (approximate):
    - Claude 3 Haiku:  ~1000 samples, ~$0.50
    - GPT-4o-mini:     ~1000 samples, ~$0.30
    - GPT-4o:          ~1000 samples, ~$4.00
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import random
import re
import time
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("teacher_gen")

# ── Topic categories per JLPT level ──────────────────────────────────────
# Each topic is a short prompt that the teacher model expands into a full essay topic.
TOPIC_CATEGORIES: dict[str, list[str]] = {
    "N5": [
        "自己紹介と家族",
        "毎日の習慣",
        "好きな食べ物",
        "私の部屋",
        "趣味",
        "ペット",
    ],
    "N4": [
        "休日の過ごし方",
        "旅行の思い出",
        "好きな季節",
        "大切な人",
        "私の町",
        "買い物",
    ],
    "N3": [
        "将来の夢",
        "健康と運動",
        "便利な技術",
        "読書の楽しみ",
        "学校生活",
        "食べ物の文化",
        "自然と環境",
        "アルバイト経験",
    ],
    "N2": [
        "情報社会の問題",
        "仕事と生活のバランス",
        "教育のあり方",
        "言語学習の意義",
        "観光と地域活性化",
        "ボランティア活動",
    ],
    "N1": [
        "グローバル化と文化の多様性",
        "少子高齢化社会の課題",
        "技術革新と人間らしさ",
        "持続可能な社会への道",
    ],
}

# ── Distribution of 1000 samples across JLPT levels ─────────────────────
SAMPLE_DISTRIBUTION: dict[str, int] = {
    "N5": 200,
    "N4": 200,
    "N3": 250,
    "N2": 200,
    "N1": 150,
}

TEACHER_SYSTEM_PROMPT = """你是日语教育和作文评分的双重专家。请为一个日语作文评分AI的训练数据生成样本。

每次生成一个完整的训练样本，包含以下三部分，以JSON格式输出：

1. **learner_essoy**: 一篇日语学习者作文。
   - 根据指定的目标等级（N5-N1），让作文包含该等级学习者典型特征：
     - N5: 极简句子，大量助词错误（は/が/を混同）、ます形只、基本词汇、几乎不用汉字
     - N4: 句子稍长，ている/ていた形错误、い形容词/な形容词混淆、少量汉字
     - N3: 尝试复杂句式有时出错、被动/使役/条件形错误、敬语错误、汉字使用中等
     - N2: 偶尔微妙助词错误、复句基本正确、少数搭配不当、汉字使用良好
     - N1: 极少明显错误、可能个别表达不自然、整体接近母语者
   - 长度：N5约80-150字，N4约150-300字，N3约250-450字，N2约350-600字，N1约400-700字
   - 让错误自然分布在全文中，不要过于密集也不要完全没有

2. **score_report**: 作为JLPT评分专家，按以下JSON字段评分：
   - overall_score (0-100)
   - task_completion_score (0-100)
   - grammar_score (0-100)
   - vocabulary_score (0-100)
   - coherence_score (0-100)
   - naturalness_score (0-100)
   - jlpt_fit_score (0-100)
   - level_estimate (string: "N5"/"N4"/"N3"/"N2"/"N1")
   - summary (string, 日语で要約)
   - comments (string, 日本語で具体的な改善アドバイス)

3. **revision_report**: 作为作文修改专家，按以下JSON字段输出：
   - issues: 数组，每项{source, suggestion, explanation, severity}
   - sentence_suggestions: 数组，每项{original, suggested, reason}（逐句修改建议）
   - full_revision: 字符串，全文修正版（保持原意只修正错误）
   - revision_notes: 字符串，日本語で修正内容まとめ

评分原则：
- 作文的分数应该与目标等级一致（N5作文应在20-40分区间，N1应在70-90区间）
- 各维度分数应有一定差异，不要全是相同分数
- level_estimate 应反映作文实际水平，可与目标等级不同

输出格式必须是严格的JSON对象，不要包含markdown代码块标记：
{
  "learner_essay": "...",
  "score_report": {...},
  "revision_report": {...}
}"""


def _build_teacher_prompt(topic_category: str, level: str) -> str:
    return (
        f"请生成一个 {level} 级别日语学习者的作文训练样本。\n\n"
        f"话题类别：{topic_category}\n"
        f"目标等级：{level}\n\n"
        f"请确保作文中的错误类型和频率符合 {level} 级学习者的典型特征。"
        f"评分和修改也要基于 {level} 级别的标准。\n\n"
        f"直接输出JSON对象，不要包含任何其他文字。"
    )


def _parse_teacher_response(text: str) -> dict[str, Any]:
    """Parse teacher model response, extracting JSON robustly."""
    # Try direct JSON parse first
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # Try extracting from code fences
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse JSON from teacher response")


def _validate_sample(data: dict[str, Any]) -> bool:
    """Validate that a generated sample has all required fields."""
    if not isinstance(data, dict):
        return False
    essay = data.get("learner_essay", "")
    if not isinstance(essay, str) or len(essay) < 20:
        return False

    score = data.get("score_report")
    if not isinstance(score, dict):
        return False
    required_score_keys = {
        "overall_score", "grammar_score", "vocabulary_score",
        "coherence_score", "naturalness_score", "level_estimate",
    }
    if not required_score_keys.issubset(score.keys()):
        return False

    revision = data.get("revision_report")
    if not isinstance(revision, dict):
        return False
    if "full_revision" not in revision:
        return False

    return True


def _format_score_record(data: dict[str, Any], topic: str, target_level: str) -> dict[str, Any]:
    """Convert teacher output to score training format."""
    score = data["score_report"]
    return {
        "input": {
            "topic": topic,
            "target_level": target_level,
            "content": data["learner_essay"],
        },
        "output": {
            "overall_score": int(score.get("overall_score", 50)),
            "task_completion_score": int(score.get("task_completion_score", 50)),
            "grammar_score": int(score.get("grammar_score", 50)),
            "vocabulary_score": int(score.get("vocabulary_score", 50)),
            "coherence_score": int(score.get("coherence_score", 50)),
            "naturalness_score": int(score.get("naturalness_score", 50)),
            "jlpt_fit_score": int(score.get("jlpt_fit_score", 50)),
            "level_estimate": str(score.get("level_estimate", "N3")),
            "summary": str(score.get("summary", "")),
            "comments": str(score.get("comments", "")),
        },
    }


def _format_revision_record(teacher_output: dict[str, Any], target_level: str, topic: str) -> dict[str, Any]:
    """Convert teacher output to revision training format."""
    revision = teacher_output["revision_report"]
    return {
        "input": {
            "topic": topic,
            "target_level": target_level,
            "content": teacher_output["learner_essay"],
        },
        "output": {
            "issues": revision.get("issues", []),
            "sentence_suggestions": revision.get("sentence_suggestions", []),
            "full_revision": str(revision.get("full_revision", "")),
            "revision_notes": str(revision.get("revision_notes", "")),
        },
    }


# ── API clients ──────────────────────────────────────────────────────────

class AnthropicClient:
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-latest", max_retries: int = 3):
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries

    def generate(self, topic: str, level: str) -> dict[str, Any]:
        import httpx

        prompt = _build_teacher_prompt(topic, level)
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": TEACHER_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        }

        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=120) as client:
                    resp = client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": self.api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json",
                        },
                        json=payload,
                    )
                    resp.raise_for_status()
                    result = resp.json()
                    content = result["content"][0]["text"]
                    parsed = _parse_teacher_response(content)
                    if _validate_sample(parsed):
                        return parsed
                    logger.warning("Invalid sample on attempt %d, retrying...", attempt + 1)
            except Exception as exc:
                last_error = exc
                logger.warning("API error on attempt %d: %s", attempt + 1, exc)
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

        raise RuntimeError(f"Failed after {self.max_retries} attempts. Last error: {last_error}")


class OpenAIClient:
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        max_retries: int = 3,
    ):
        from openai import OpenAI

        kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model = model
        self.max_retries = max_retries

    def generate(self, topic: str, level: str) -> dict[str, Any]:
        prompt = _build_teacher_prompt(topic, level)
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": TEACHER_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=4096,
                    response_format={"type": "json_object"},
                )
                content = resp.choices[0].message.content
                if not content:
                    raise ValueError("Empty response")
                parsed = _parse_teacher_response(content)
                if _validate_sample(parsed):
                    return parsed
                logger.warning("Invalid sample on attempt %d, retrying...", attempt + 1)
            except Exception as exc:
                last_error = exc
                logger.warning("API error on attempt %d: %s", attempt + 1, exc)
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

        raise RuntimeError(f"Failed after {self.max_retries} attempts. Last error: {last_error}")


# ── Main pipeline ────────────────────────────────────────────────────────

def _load_checkpoint(path: Path) -> set[str]:
    """Load already-generated sample fingerprints from output files."""
    fingerprints: set[str] = set()
    if not path.exists():
        return fingerprints
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                content = record.get("input", {}).get("content", "")
                fp = hashlib.md5(content.encode()).hexdigest()
                fingerprints.add(fp)
            except (json.JSONDecodeError, KeyError):
                continue
    return fingerprints


def _write_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _shuffle_and_split(input_path: Path, train_path: Path, eval_path: Path, eval_ratio: float = 0.1) -> None:
    """Read all records, shuffle, split into train/eval, write."""
    import hashlib

    if not input_path.exists():
        logger.warning("No records found at %s, skipping split.", input_path)
        return

    records: list[dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not records:
        return

    # Deterministic shuffle by content hash for reproducibility
    def _sort_key(r: dict[str, Any]) -> str:
        content = r.get("input", {}).get("content", "")
        return hashlib.md5(content.encode()).hexdigest()

    records.sort(key=_sort_key)
    split_idx = max(1, int(len(records) * eval_ratio))

    eval_records = records[:split_idx]
    train_records = records[split_idx:]

    train_path.parent.mkdir(parents=True, exist_ok=True)
    with train_path.open("w", encoding="utf-8") as fh:
        for record in train_records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    with eval_path.open("w", encoding="utf-8") as fh:
        for record in eval_records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info(
        "Split %s: %d train + %d eval -> %s, %s",
        input_path.name,
        len(train_records),
        len(eval_records),
        train_path.name,
        eval_path.name,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic essay training data using a teacher LLM."
    )
    parser.add_argument(
        "--api-type",
        required=True,
        choices=["openai", "anthropic"],
        help="Teacher API provider.",
    )
    parser.add_argument("--api-key", required=True, help="API key for the teacher model.")
    parser.add_argument(
        "--model",
        default=None,
        help="Model name (e.g., gpt-4o-mini, claude-3-5-haiku-latest). Defaults to provider default.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL for OpenAI-compatible endpoints (e.g., local vLLM).",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=1000,
        help="Total number of samples to generate (default: 1000).",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parents[1] / "data" / "essay_processed"),
        help="Output directory for generated JSONL files.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume generation from existing checkpoint files.",
    )
    parser.add_argument(
        "--eval-ratio",
        type=float,
        default=0.1,
        help="Ratio of data to use for evaluation (default: 0.1).",
    )
    return parser.parse_args()


def main() -> int:
    import hashlib

    args = parse_args()
    output_dir = Path(args.output_dir)

    # Determine sample distribution
    total_samples = args.samples
    levels = list(SAMPLE_DISTRIBUTION.keys())
    weights = [SAMPLE_DISTRIBUTION[level] / sum(SAMPLE_DISTRIBUTION.values()) for level in levels]
    samples_per_level = {level: max(1, int(total_samples * weight)) for level, weight in zip(levels, weights)}

    # Adjust rounding
    diff = total_samples - sum(samples_per_level.values())
    if diff > 0:
        samples_per_level["N3"] += diff

    logger.info("Sample distribution: %s", samples_per_level)
    logger.info("Total: %d samples", sum(samples_per_level.values()))

    # Init teacher client
    if args.api_type == "anthropic":
        model = args.model or "claude-3-5-haiku-latest"
        client = AnthropicClient(api_key=args.api_key, model=model)
    else:
        model = args.model or "gpt-4o-mini"
        client = OpenAIClient(api_key=args.api_key, model=model, base_url=args.base_url)

    logger.info("Teacher model: %s (%s)", model, args.api_type)

    # Checkpoint files (append-only)
    score_ckpt = output_dir / ".score_ckpt.jsonl"
    revision_ckpt = output_dir / ".revision_ckpt.jsonl"

    # Load existing fingerprints for resume
    existing_fingerprints = set()
    if args.resume:
        existing_fingerprints = _load_checkpoint(score_ckpt) | _load_checkpoint(revision_ckpt)
        logger.info("Resume mode: %d existing samples found", len(existing_fingerprints))

    # Generate samples
    total = sum(samples_per_level.values())
    generated = 0
    start_time = time.time()

    for level in levels:
        count = samples_per_level[level]
        topics = TOPIC_CATEGORIES[level]
        level_success = 0

        for i in range(count):
            # Pick a topic
            topic = random.choice(topics)
            # Create a unique variant per sample
            variant = random.choice([
                "日常生活の視点から",
                "個人的な経験を中心に",
                "賛成・反対の立場を明確に",
                "具体的な例を挙げながら",
                "比較対照を交えて",
                "時系列に沿って",
            ])
            full_topic = f"{topic}（{variant}）"

            # Progress
            pct = (generated) / total * 100
            elapsed = time.time() - start_time
            rate = generated / max(elapsed, 1)
            remaining = (total - generated) / max(rate, 0.01)
            logger.info(
                "[%3d%%] %s/%s | %s sample %d/%d | rate: %.1f/min | ETA: %.0fs",
                int(pct), level, level,
                level, i + 1, count,
                rate * 60,
                remaining,
            )

            # Generate
            try:
                data = client.generate(full_topic, level)
            except Exception as exc:
                logger.error("Failed to generate sample: %s", exc)
                continue

            # Check duplicate
            fp = hashlib.md5(data["learner_essay"].encode()).hexdigest()
            if fp in existing_fingerprints:
                logger.info("Skipping duplicate sample (already in checkpoint)")
                continue
            existing_fingerprints.add(fp)

            # Format and write
            score_record = _format_score_record(data)
            revision_record = _format_revision_record(data, level, topic)

            _write_record(score_ckpt, score_record)
            _write_record(revision_ckpt, revision_record)

            generated += 1
            level_success += 1

        logger.info("Level %s: %d/%d successful", level, level_success, count)

    # Summary
    elapsed = time.time() - start_time
    logger.info(
        "Generation complete: %d samples in %.0fs (%.1f/min). Checkpoint files: %s, %s",
        generated, elapsed, generated / max(elapsed, 1) * 60,
        score_ckpt, revision_ckpt,
    )

    if generated == 0:
        logger.error("No samples generated. Check API key and model access.")
        return 1

    # Split into train/eval
    logger.info("Splitting into train/eval sets...")
    _shuffle_and_split(
        score_ckpt,
        output_dir / "score_train.jsonl",
        output_dir / "score_eval.jsonl",
        args.eval_ratio,
    )
    _shuffle_and_split(
        revision_ckpt,
        output_dir / "revision_train.jsonl",
        output_dir / "revision_eval.jsonl",
        args.eval_ratio,
    )

    logger.info("Done! Data ready in %s", output_dir)
    logger.info("  score_train.jsonl + score_eval.jsonl")
    logger.info("  revision_train.jsonl + revision_eval.jsonl")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. cd backend")
    logger.info("  2. python training/train_score_lora.py")
    logger.info("  3. python training/train_revision_lora.py")
    logger.info("  4. python training/merge_and_quantize.py ...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
