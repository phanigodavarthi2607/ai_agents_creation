"""
Export fine-tuned model to Ollama format.

Converts the LoRA fine-tuned model to GGUF format and creates
an Ollama model that can be used locally.

Prerequisites:
    - Fine-tuned model in models/qa-slm-phi3-lora/
    - llama.cpp installed (for GGUF conversion)
    - Ollama installed

Usage:
    python slm/training/export_ollama.py
"""

import os
import subprocess
import sys


def export():
    model_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "models", "qa-slm-phi3-lora"
    )

    if not os.path.exists(model_dir):
        print(f"Fine-tuned model not found at {model_dir}")
        print("Run fine-tuning first: python slm/training/finetune.py")
        sys.exit(1)

    gguf_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models", "gguf")
    os.makedirs(gguf_dir, exist_ok=True)
    gguf_path = os.path.join(gguf_dir, "qa-slm.gguf")

    print("Step 1: Merge LoRA weights with base model...")
    try:
        from unsloth import FastLanguageModel
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_dir,
            max_seq_length=2048,
            load_in_4bit=False,
        )
        merged_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models", "merged")
        model.save_pretrained_merged(merged_dir, tokenizer)
        print(f"  Merged model saved to {merged_dir}")
    except ImportError:
        print("  Unsloth not available. Attempting manual merge...")
        print("  Install with: pip install unsloth")
        sys.exit(1)

    print("\nStep 2: Convert to GGUF format...")
    print("  This requires llama.cpp's convert script.")
    print(f"  Expected output: {gguf_path}")
    print()
    print("  If you have llama.cpp installed, run:")
    print(f"    python llama.cpp/convert_hf_to_gguf.py {merged_dir} --outfile {gguf_path} --outtype q4_k_m")
    print()

    modelfile_path = os.path.join(
        os.path.dirname(__file__), "..", "config", "modelfile_finetuned"
    )
    with open(modelfile_path, "w") as f:
        f.write(f"FROM {gguf_path}\n\n")
        f.write("PARAMETER temperature 0.1\n")
        f.write("PARAMETER top_p 0.9\n")
        f.write("PARAMETER num_predict 2048\n\n")
        f.write('SYSTEM """You are a QA and Test Automation expert specializing in Private Markets ')
        f.write("and Fund of Funds (FOF) investment domains. You work with Jira/Xray for test management.\n\n")
        f.write("CRITICAL RULES:\n")
        f.write("1. Answer using only verified facts from your training and the provided context.\n")
        f.write("2. If unsure, say so. Never fabricate information.\n")
        f.write("3. Cite sources when available.\n")
        f.write("4. For Jira fields and Testing Types, use only verified values.\n")
        f.write('5. Generate test cases using the standard template with structured steps."""\n')

    print(f"\nStep 3: Modelfile created at {modelfile_path}")
    print("\nStep 4: Create Ollama model:")
    print(f"  ollama create qa-slm -f {modelfile_path}")
    print("\nStep 5: Test the model:")
    print("  ollama run qa-slm 'What are the valid Testing Types for Jira?'")


if __name__ == "__main__":
    export()
