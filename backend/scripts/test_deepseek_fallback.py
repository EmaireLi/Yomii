"""
直接测试 DeepSeek V4 Flash 兜底接口。

运行前：
1. 在 backend/.env 中填写 DEEPSEEK_API_KEY
2. 在 backend 目录执行：
   python scripts/test_deepseek_fallback.py --task score
   python scripts/test_deepseek_fallback.py --task revision
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.ai_evaluation import DeepSeekEssayFallbackService


DEFAULT_CONTENT = (
    "昨日、友達と駅前のショッピングモールに行きました。"
    "セールをやっていて、服が安くなっていました。"
    "私は青いセーターを買いました。友達は靴を買いました。"
    "その後、カフェでお茶をしました。抹茶ラテが美味しかったです。"
    "値段はちょっと高かったですが、楽しい一日でした。"
)


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=["score", "revision"], default="score")
    parser.add_argument("--target-level", default="N4")
    parser.add_argument("--topic", default="daily-life")
    parser.add_argument("--content", default=DEFAULT_CONTENT)
    args = parser.parse_args()

    service = DeepSeekEssayFallbackService()
    if not service.enabled:
        raise SystemExit("DEEPSEEK_API_KEY 未配置，无法调用 DeepSeek 兜底接口。")

    if args.task == "score":
        result = await service.score_essay(
            content=args.content,
            topic=args.topic,
            target_level=args.target_level,
        )
    else:
        result = await service.revise_essay(
            content=args.content,
            topic=args.topic,
            target_level=args.target_level,
            score_report={
                "overall_score": 74,
                "task_completion_score": 76,
                "grammar_score": 70,
                "vocabulary_score": 76,
                "coherence_score": 73,
                "naturalness_score": 71,
                "jlpt_fit_score": 82,
                "level_estimate": args.target_level,
                "summary": "示例评分，仅用于触发修改接口。",
                "comments": "示例评分，仅用于触发修改接口。",
            },
        )

    print(json.dumps(
        {
            "model_version": result.model_version,
            "payload": result.payload,
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
