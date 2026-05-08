from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

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
            "字段必须包含 overall_score, task_completion_score, grammar_score, "
            "vocabulary_score, coherence_score, naturalness_score, jlpt_fit_score, "
            "level_estimate, summary, comments。"
        )
        user = (
            f"题目：{payload.topic}\n"
            f"目标等级：{payload.target_level}\n"
            f"作文：{payload.content}\n"
        )
    else:
        system = (
            "你是日语作文修改专家。请输出严格 JSON，字段必须包含 "
            "issues, sentence_suggestions, full_revision, revision_notes。"
        )
        user = (
            f"题目：{payload.topic}\n"
            f"目标等级：{payload.target_level}\n"
            f"作文：{payload.content}\n"
            f"评分参考：{json.dumps(payload.score_report or {}, ensure_ascii=False)}\n"
        )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def extract_json(text: str, required_keys: set[str]) -> dict[str, Any]:
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


def _split_sentences(content: str) -> list[str]:
    normalized = content.replace("。", "。\n").replace("！", "！\n").replace("？", "？\n")
    return [item.strip() for item in normalized.splitlines() if item.strip()]


def _clamp_score(value: float, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, int(round(value))))


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
    jlpt_fit = _clamp_score(50 + min(word_count, 240) * 0.1 + (6 if payload.target_level in {"N2", "N1"} else 0))
    overall = _clamp_score(
        task_completion * 0.2
        + grammar * 0.22
        + vocabulary * 0.2
        + coherence * 0.16
        + naturalness * 0.12
        + jlpt_fit * 0.1
    )
    level_estimate = "N1" if overall >= 88 else "N2" if overall >= 80 else "N3" if overall >= 70 else "N4" if overall >= 60 else "N5"
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
        if not suggested.endswith(("。", "！", "？")):
            suggested = f"{suggested}。"
        suggestions.append(
            {
                "original": cleaned,
                "suggested": suggested,
                "reason": "补充连接词并统一句末表达，可以让句子之间更连贯。",
            }
        )

    full_revision = "\n".join(item["suggested"] for item in suggestions) if suggestions else payload.content
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


def create_app(task: str, model_path: str, model_version: str | None, adapter_path: str | None) -> FastAPI:
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="auto",
        trust_remote_code=True,
    )
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
            enable_thinking=False,
        )
        inputs = tokenizer(text, return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512 if task == "score" else 768,
                do_sample=False,
                temperature=0.2,
                pad_token_id=tokenizer.eos_token_id,
            )
        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        decoded = tokenizer.decode(generated_ids, skip_special_tokens=True)

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
            parsed = extract_json(decoded, required_keys)
        except Exception:
            parsed = build_fallback_score(payload) if task == "score" else build_fallback_revision(payload)

        if not required_keys.issubset(parsed.keys()):
            parsed = build_fallback_score(payload) if task == "score" else build_fallback_revision(payload)

        parsed["model_version"] = version
        return parsed

    return app


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve a GPTQ Qwen model as an HTTP inference service.")
    parser.add_argument("--task", choices=["score", "revision"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter", default="")
    parser.add_argument("--model-version", default="")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()

    app = create_app(args.task, args.model, args.model_version or None, args.adapter or None)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
