"""
SLM — Standalone QA & Test Automation Knowledge Model

Usage:
    python -m slm setup                      First-time setup: load knowledge + check Ollama
    python -m slm ask "your question"        Ask a question (RAG + local LLM)
    python -m slm search "query"             Search knowledge base (no LLM)
    python -m slm stats                      Show knowledge store statistics
    python -m slm serve                      Start HTTP API server
    python -m slm generate-training          Generate fine-tuning training data
    python -m slm export <path>              Export knowledge base to JSON
    python -m slm add "text" <category>      Add knowledge entry manually
"""

import json
import sys
import os


def cmd_setup():
    """First-time setup: load knowledge and verify Ollama."""
    print("=== SLM Setup ===\n")

    print("1. Loading domain knowledge...")
    from slm.knowledge.store import KnowledgeStore
    store = KnowledgeStore()
    summary = store.load_all_knowledge()
    total = store.count()
    for fname, count in summary.items():
        print(f"   {fname}: {count} entries")
    print(f"   Total: {total} entries loaded\n")

    print("2. Checking Ollama...")
    from slm.inference.ollama_client import OllamaClient
    client = OllamaClient()
    if client.is_available():
        models = client.list_models()
        print(f"   Ollama is running. Available models: {', '.join(models) or 'none'}")
        if not any("phi3" in m or "phi-3" in m or "mistral" in m or "llama" in m for m in models):
            print(f"   Recommended: ollama pull phi3:mini")
    else:
        print("   Ollama is not running.")
        print("   Install: https://ollama.com/download")
        print("   Then run: ollama pull phi3:mini")

    print("\n=== Setup complete ===")
    print(f"Knowledge store: {total} entries")
    print("Run 'python -m slm ask \"your question\"' to get started")


def cmd_ask(question: str):
    """Ask a question using RAG + local LLM."""
    from slm.rag.pipeline import RAGPipeline
    from slm.inference.ollama_client import OllamaClient

    client = OllamaClient()
    if not client.is_available():
        print("Ollama is not running. Starting search-only mode...\n")
        cmd_search(question)
        print("\nTo get full answers, install and start Ollama:")
        print("  https://ollama.com/download")
        print("  ollama pull phi3:mini")
        return

    pipeline = RAGPipeline()

    try:
        response = pipeline.generate(question)

        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"{'='*60}")
        print(f"\n{response.answer}")
        print(f"\n{'─'*60}")
        print(f"Grounded: {'Yes' if response.grounded else 'No'}")
        print(f"Confidence: {response.confidence:.0%}")
        print(f"Sources used: {response.context_used}")
        for s in response.sources:
            print(f"  - [{s['source']}] (score: {s['score']:.0%})")
    except Exception as e:
        print(f"LLM error: {e}")
        print("Falling back to knowledge search...\n")
        cmd_search(question)


def cmd_search(query: str, category: str = None, n: int = 5):
    """Search the knowledge base without LLM."""
    from slm.knowledge.store import KnowledgeStore

    store = KnowledgeStore()
    results = store.search(query, n_results=n, category=category)

    print(f"\nSearch: {query}")
    print(f"Found: {len(results)} results\n")

    for i, r in enumerate(results, 1):
        print(f"  [{i}] (score: {r['score']:.0%}) [{r['category']}]")
        print(f"      Source: {r['source']}")
        text = r['text']
        print(f"      {text[:200]}{'...' if len(text) > 200 else ''}")
        print()


def cmd_stats():
    """Show knowledge store statistics."""
    from slm.knowledge.store import KnowledgeStore

    store = KnowledgeStore()
    total = store.count()
    print(f"\nKnowledge Store: {total} entries\n")

    categories = [
        "qa_methodology", "qa_best_practice",
        "automation_framework", "automation_pattern",
        "domain_knowledge", "jira_integration",
    ]
    for cat in categories:
        entries = store.get_by_category(cat)
        if entries:
            print(f"  {cat}: {len(entries)}")
    print()


def cmd_serve(host: str = "0.0.0.0", port: int = 8100):
    """Start the HTTP API server."""
    import uvicorn
    print(f"\nStarting SLM API server on {host}:{port}")
    print(f"Docs: http://localhost:{port}/docs\n")
    uvicorn.run("slm.api:app", host=host, port=port, reload=True)


def cmd_generate_training():
    """Generate fine-tuning training data from knowledge base."""
    from slm.training.dataset_generator import DatasetGenerator

    output_dir = os.path.join(
        os.path.dirname(__file__), "..", "knowledge_base", "training_data"
    )
    os.makedirs(output_dir, exist_ok=True)

    gen = DatasetGenerator()

    alpaca_path = os.path.join(output_dir, "train_alpaca.jsonl")
    chatml_path = os.path.join(output_dir, "train_chatml.jsonl")
    sharegpt_path = os.path.join(output_dir, "train_sharegpt.jsonl")

    n1 = gen.export_alpaca(alpaca_path)
    n2 = gen.export_chatml(chatml_path)
    n3 = gen.export_sharegpt(sharegpt_path)

    print(f"\nGenerated training data:")
    print(f"  Alpaca format:  {alpaca_path} ({n1} examples)")
    print(f"  ChatML format:  {chatml_path} ({n2} examples)")
    print(f"  ShareGPT format: {sharegpt_path} ({n3} examples)")
    print(f"\nTo fine-tune: python slm/training/finetune.py")


def cmd_export(path: str):
    """Export knowledge base to JSON."""
    from slm.knowledge.store import KnowledgeStore
    store = KnowledgeStore()
    store.export(path)
    print(f"\nExported {store.count()} entries to {path}")


def cmd_add(text: str, category: str, source: str = "manual"):
    """Add a knowledge entry manually."""
    from slm.knowledge.store import KnowledgeStore
    store = KnowledgeStore()
    entry_id = store.add(text=text, category=category, source=source)
    print(f"\nAdded entry: {entry_id}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "setup":
        cmd_setup()
    elif command == "ask":
        if len(sys.argv) < 3:
            print("Usage: python -m slm ask 'your question'")
            sys.exit(1)
        cmd_ask(sys.argv[2])
    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: python -m slm search 'query' [category]")
            sys.exit(1)
        category = sys.argv[3] if len(sys.argv) > 3 else None
        cmd_search(sys.argv[2], category)
    elif command == "stats":
        cmd_stats()
    elif command == "serve":
        host = sys.argv[2] if len(sys.argv) > 2 else "0.0.0.0"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 8100
        cmd_serve(host, port)
    elif command == "generate-training":
        cmd_generate_training()
    elif command == "export":
        if len(sys.argv) < 3:
            print("Usage: python -m slm export <output_path>")
            sys.exit(1)
        cmd_export(sys.argv[2])
    elif command == "add":
        if len(sys.argv) < 4:
            print("Usage: python -m slm add 'text' <category> [source]")
            sys.exit(1)
        source = sys.argv[4] if len(sys.argv) > 4 else "manual"
        cmd_add(sys.argv[2], sys.argv[3], source)
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
