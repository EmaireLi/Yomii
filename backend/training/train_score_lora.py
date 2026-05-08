from __future__ import annotations

import argparse
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

from common import format_score_prompt, load_jsonl_dataset, load_yaml_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train score LoRA for JLPT essay scoring.")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).parent / "configs" / "score_lora.yaml"),
        help="Path to YAML config.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = load_yaml_config(args.config)

    tokenizer = AutoTokenizer.from_pretrained(cfg["model_name"], trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        cfg["model_name"],
        quantization_config=quant_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model)
    peft_config = LoraConfig(
        r=cfg["lora_r"],
        lora_alpha=cfg["lora_alpha"],
        lora_dropout=cfg["lora_dropout"],
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=cfg["target_modules"],
    )
    model = get_peft_model(model, peft_config)

    train_dataset = load_jsonl_dataset(cfg["train_file"]).map(
        lambda row: tokenizer(format_score_prompt(row), truncation=True, max_length=cfg["max_seq_length"]),
        remove_columns=["input", "output"],
    )
    eval_dataset = load_jsonl_dataset(cfg["eval_file"]).map(
        lambda row: tokenizer(format_score_prompt(row), truncation=True, max_length=cfg["max_seq_length"]),
        remove_columns=["input", "output"],
    )
    if cfg.get("max_train_samples"):
        train_dataset = train_dataset.select(range(min(int(cfg["max_train_samples"]), len(train_dataset))))
    if cfg.get("max_eval_samples"):
        eval_dataset = eval_dataset.select(range(min(int(cfg["max_eval_samples"]), len(eval_dataset))))

    training_args = TrainingArguments(
        output_dir=cfg["output_dir"],
        per_device_train_batch_size=cfg["per_device_train_batch_size"],
        per_device_eval_batch_size=cfg["per_device_eval_batch_size"],
        gradient_accumulation_steps=cfg["gradient_accumulation_steps"],
        learning_rate=cfg["learning_rate"],
        num_train_epochs=cfg["num_train_epochs"],
        warmup_ratio=cfg["warmup_ratio"],
        logging_steps=cfg["logging_steps"],
        save_strategy=cfg["save_strategy"],
        eval_strategy=cfg["evaluation_strategy"],
        save_total_limit=cfg["save_total_limit"],
        gradient_checkpointing=True,
        bf16=False,
        fp16=True,
        report_to="none",
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()
    trainer.save_model(cfg["output_dir"])
    tokenizer.save_pretrained(cfg["output_dir"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
