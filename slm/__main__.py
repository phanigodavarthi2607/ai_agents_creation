"""
CLI entry point for the SLM Knowledge Layer.

Usage:
    python -m slm seed              Bootstrap the knowledge store with domain knowledge
    python -m slm query "question"  Query the knowledge layer
    python -m slm stats             Show knowledge store and training data stats
    python -m slm ingest <storyKey> <runs_dir>  Ingest a completed workflow run
    python -m slm export <path>     Export knowledge store to JSON
    python -m slm serve             Start the HTTP API server
    python -m slm training-stats    Show training data collection stats
    python -m slm export-training <path>  Export training data for fine-tuning
"""

import json
import sys


def cmd_seed():
    from slm.seeds.seed_loader import main as seed_main
    seed_main()


def cmd_query(question: str, category: str = None, n: int = 5):
    from slm.core.query_engine import QueryEngine

    engine = QueryEngine()
    response = engine.ask(question, category=category, n_results=n)

    print(f"\nQuery: {response.query}")
    print(f"Grounding: {response.grounding_statement}")
    print(f"Results: {response.total_found}\n")

    for i, r in enumerate(response.results, 1):
        print(f"  [{i}] (confidence={r.confidence:.0%}) [{r.category}]")
        print(f"      Source: {r.source}")
        print(f"      {r.text[:200]}{'...' if len(r.text) > 200 else ''}")
        print()


def cmd_stats():
    from slm.core.knowledge_store import KnowledgeStore

    store = KnowledgeStore()
    total = store.count()
    print(f"\nKnowledge Store: {total} entries")

    if total > 0:
        from slm.core.knowledge_store import VALID_CATEGORIES
        for cat in sorted(VALID_CATEGORIES):
            entries = store.get_by_category(cat)
            if entries:
                print(f"  {cat}: {len(entries)}")
    print()


def cmd_ingest(story_key: str, runs_dir: str):
    from slm.ingestion.workflow_ingestor import WorkflowIngestor

    ingestor = WorkflowIngestor()
    summary = ingest_summary = ingestor.ingest_run(story_key, runs_dir)

    print(f"\nIngested workflow run for {story_key}")
    print(f"  Files processed: {', '.join(summary['files_processed'])}")
    print(f"  Entries added: {summary['entries_added']}")
    if summary["errors"]:
        print(f"  Errors: {len(summary['errors'])}")
        for err in summary["errors"]:
            print(f"    - {err}")
    print()


def cmd_export(path: str):
    from slm.core.knowledge_store import KnowledgeStore

    store = KnowledgeStore()
    store.export_all(path)
    print(f"\nExported {store.count()} entries to {path}")


def cmd_serve(host: str = "0.0.0.0", port: int = 8100):
    import uvicorn
    print(f"\nStarting SLM API server on {host}:{port}")
    print("Docs available at http://localhost:8100/docs\n")
    uvicorn.run("slm.api:app", host=host, port=port, reload=True)


def cmd_training_stats():
    from slm.training.data_collector import TrainingDataCollector

    collector = TrainingDataCollector()
    stats = collector.get_stats()
    print(f"\nTraining Data Stats:")
    print(f"  Total examples: {stats.get('total', 0)}")
    print(f"  High quality: {stats.get('high', 0)}")
    print(f"  Corrected: {stats.get('corrected', 0)}")
    print(f"  Unverified: {stats.get('unverified', 0)}")
    print(f"  Ready for fine-tuning: {stats.get('ready_for_finetuning', False)}")
    print()


def cmd_export_training(path: str, min_quality: str = "unverified"):
    from slm.training.data_collector import TrainingDataCollector

    collector = TrainingDataCollector()
    count = collector.export_for_finetuning(path, min_quality=min_quality)
    print(f"\nExported {count} training examples to {path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "seed":
        cmd_seed()
    elif command == "query":
        if len(sys.argv) < 3:
            print("Usage: python -m slm query 'your question'")
            sys.exit(1)
        question = sys.argv[2]
        category = sys.argv[3] if len(sys.argv) > 3 else None
        cmd_query(question, category)
    elif command == "stats":
        cmd_stats()
    elif command == "ingest":
        if len(sys.argv) < 4:
            print("Usage: python -m slm ingest <storyKey> <runs_dir>")
            sys.exit(1)
        cmd_ingest(sys.argv[2], sys.argv[3])
    elif command == "export":
        if len(sys.argv) < 3:
            print("Usage: python -m slm export <output_path>")
            sys.exit(1)
        cmd_export(sys.argv[2])
    elif command == "serve":
        host = sys.argv[2] if len(sys.argv) > 2 else "0.0.0.0"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 8100
        cmd_serve(host, port)
    elif command == "training-stats":
        cmd_training_stats()
    elif command == "export-training":
        if len(sys.argv) < 3:
            print("Usage: python -m slm export-training <output_path>")
            sys.exit(1)
        min_q = sys.argv[3] if len(sys.argv) > 3 else "unverified"
        cmd_export_training(sys.argv[2], min_q)
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
