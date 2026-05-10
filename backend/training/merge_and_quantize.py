"""
Merge LoRA adapter into base model and quantize to 4-bit for standalone deployment.
Produces a model that needs NO PEFT/adapters at inference time.

Usage:
  python training/merge_and_quantize.py \\
    --base-model Qwen/Qwen3-1.7B \\
    --adapter models/score-lora \\
    --output-dir models/qwen3-1.7b-score-merged \\
    --mirror
"""
from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── Force HF settings before any HF library import ──────────────────
# Use hf-mirror.com for faster downloads in China (override with HF_ENDPOINT env var)
_DEFAULT_MIRROR = "https://hf-mirror.com"
os.environ.setdefault("HF_ENDPOINT", _DEFAULT_MIRROR)
# Store HF_HOME under backend/training/ to keep C drive clean
_HERE = Path(__file__).resolve().parent
os.environ["HF_HOME"] = str(_HERE / "hf_cache")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# hf_transfer (Rust) causes SSL issues on Windows; disable it
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

import torch


def _patch_gptqmodel_awq_compat() -> None:
    """PEFT's LoRA dispatcher tries to import gptqmodel classes that may
    have been renamed between versions. Apply compat shim before PEFT loads."""
    try:
        import gptqmodel.nn_modules.qlinear.gemm_awq as gemm_awq
    except Exception:
        return
    if not hasattr(gemm_awq, "AwqGEMMQuantLinear") and hasattr(gemm_awq, "AwqGEMMLinear"):
        gemm_awq.AwqGEMMQuantLinear = gemm_awq.AwqGEMMLinear


_patch_gptqmodel_awq_compat()
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

logger = logging.getLogger("merge_quantize")
logger.setLevel(logging.INFO)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(console)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge LoRA into base model and quantize for deployment."
    )
    parser.add_argument("--base-model", required=True, help="Base model name or path")
    parser.add_argument("--adapter", required=True, help="LoRA adapter path")
    parser.add_argument("--output-dir", required=True, help="Output directory for merged+quantized model")
    parser.add_argument(
        "--quantize",
        default="bnb-nf4",
        choices=["bnb-nf4", "fp16"],
        help="Quantization mode for output model (default: bnb-nf4)",
    )
    parser.add_argument(
        "--device-map",
        default="auto",
        help="Device map for model loading (default: auto)",
    )
    parser.add_argument(
        "--clean-cache",
        action="store_true",
        help="Remove HF cache after merge+quantize completes",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    cache_dir = Path(os.environ["HF_HOME"])
    logger.info("HF cache dir: %s", cache_dir)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Load base model in FP16 ──────────────────────────────────
    logger.info("Loading base model: %s (FP16) ...", args.base_model)
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16,
        device_map=args.device_map,
        trust_remote_code=True,
    )
    logger.info("Base model loaded. Parameters: %.0fM", model.num_parameters() / 1e6)

    # ── Step 2: Load and merge LoRA adapter ──────────────────────────────
    logger.info("Loading LoRA adapter: %s ...", args.adapter)
    model = PeftModel.from_pretrained(model, args.adapter)
    logger.info("Merging LoRA weights into base model ...")
    model = model.merge_and_unload()
    logger.info("LoRA merged successfully.")

    # ── Step 3: Quantize (if requested) ──────────────────────────────────
    if args.quantize == "bnb-nf4":
        logger.info("Quantizing to BNB 4-bit NF4 ...")
        temp_dir = output_dir / "_tmp_fp16"
        temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Saving temporary FP16 checkpoint to %s ...", temp_dir)
        model.save_pretrained(temp_dir, safe_serialization=True)
        del model
        torch.cuda.empty_cache()

        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
        logger.info("Reloading with BNB 4-bit quantization ...")
        model = AutoModelForCausalLM.from_pretrained(
            temp_dir,
            quantization_config=quant_config,
            device_map=args.device_map,
            trust_remote_code=True,
        )

        # Clean up temp
        shutil.rmtree(temp_dir, ignore_errors=True)
    else:
        logger.info("Skipping quantization, keeping FP16.")

    # ── Step 4: Save tokenizer and final model ───────────────────────────
    logger.info("Loading tokenizer ...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    logger.info("Saving to %s ...", output_dir)
    tokenizer.save_pretrained(output_dir)
    model.save_pretrained(output_dir, safe_serialization=True)
    logger.info("Done! Model saved to %s", output_dir)

    # ── Step 5: Clean HF cache ──────────────────────────────────────────
    if args.clean_cache and cache_dir.exists():
        logger.info("Cleaning HF cache at %s ...", cache_dir)
        shutil.rmtree(cache_dir, ignore_errors=True)
        logger.info("Cache cleaned.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
