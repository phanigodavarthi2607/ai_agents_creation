"""
Fine-tuning script for the QA Domain SLM.

Uses Unsloth for efficient LoRA fine-tuning of Phi-3-mini on the
generated domain training data. Runs on Google Colab free tier GPU
or any machine with 16GB+ VRAM.

Prerequisites:
    pip install unsloth transformers datasets peft trl

Usage:
    python slm/training/finetune.py

After training:
    python slm/training/export_ollama.py
"""

import json
import os
import sys


def check_gpu():
    """Check if GPU is available."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_mem = torch.cuda.get_device_properties(0).total_mem / 1e9
            print(f"GPU detected: {gpu_name} ({gpu_mem:.1f} GB)")
            return True
        else:
            print("No GPU detected. Fine-tuning requires GPU access.")
            print("Options:")
            print("  1. Use Google Colab (free tier provides T4 GPU)")
            print("  2. Use cloud GPU (Azure ML, AWS SageMaker, Lambda Labs)")
            print("  3. Use a local machine with NVIDIA GPU (16GB+ VRAM)")
            return False
    except ImportError:
        print("PyTorch not installed. Run: pip install torch")
        return False


def load_training_data(path: str) -> list[dict]:
    """Load training data from JSONL file."""
    data = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    print(f"Loaded {len(data)} training examples")
    return data


def train():
    """Run the fine-tuning pipeline."""
    if not check_gpu():
        print("\nTo proceed without GPU (very slow), set SLM_FORCE_CPU=1")
        if not os.environ.get("SLM_FORCE_CPU"):
            sys.exit(1)

    training_data_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "knowledge_base", "training_data", "train_chatml.jsonl"
    )

    if not os.path.exists(training_data_path):
        print(f"Training data not found at {training_data_path}")
        print("Generate it first: python -m slm generate-training")
        sys.exit(1)

    print("\n--- Loading dependencies ---")
    try:
        from unsloth import FastLanguageModel
        from trl import SFTTrainer
        from transformers import TrainingArguments
        from datasets import Dataset
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install unsloth transformers datasets peft trl")
        sys.exit(1)

    print("\n--- Loading model ---")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Phi-3-mini-4k-instruct",
        max_seq_length=2048,
        load_in_4bit=True,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )

    print("\n--- Loading training data ---")
    raw_data = load_training_data(training_data_path)

    def format_chatml(example):
        messages = example["messages"]
        text = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            text += f"<|{role}|>\n{content}\n"
        text += "<|assistant|>\n"
        return {"text": text}

    dataset = Dataset.from_list(raw_data).map(format_chatml)

    output_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "models", "qa-slm-phi3-lora"
    )
    os.makedirs(output_dir, exist_ok=True)

    print("\n--- Starting training ---")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        args=TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=3,
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            learning_rate=2e-4,
            warmup_steps=10,
            fp16=True,
            logging_steps=10,
            save_steps=50,
            save_total_limit=3,
        ),
    )

    trainer.train()

    print("\n--- Saving model ---")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model saved to {output_dir}")
    print("\nNext steps:")
    print("  1. Export to GGUF: python slm/training/export_ollama.py")
    print("  2. Load in Ollama: ollama create qa-slm -f slm/config/modelfile_finetuned")


if __name__ == "__main__":
    train()
