"""
Seed Loader — populates the knowledge store with initial domain knowledge
extracted from agent definitions and workflow rules.

Run this once to bootstrap the knowledge base, then incrementally add
knowledge from workflow runs via the ingestion pipeline.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from slm.core.knowledge_store import KnowledgeStore


def load_seed_file(store: KnowledgeStore, seed_path: str) -> int:
    """Load a seed JSON file into the knowledge store.

    Args:
        store: The KnowledgeStore instance.
        seed_path: Path to the seed JSON file.

    Returns:
        Number of entries loaded.
    """
    with open(seed_path) as f:
        entries = json.load(f)

    count = 0
    for entry in entries:
        store.add(
            text=entry["text"],
            category=entry["category"],
            source=entry["source"],
            entry_id=entry.get("id"),
            metadata=entry.get("metadata"),
        )
        count += 1

    return count


def seed_all(store: KnowledgeStore) -> dict:
    """Load all seed files from the seeds directory.

    Returns:
        Summary dict with file names and entry counts.
    """
    seeds_dir = os.path.dirname(__file__)
    summary = {}

    for filename in sorted(os.listdir(seeds_dir)):
        if filename.endswith(".json"):
            path = os.path.join(seeds_dir, filename)
            count = load_seed_file(store, path)
            summary[filename] = count
            print(f"  Loaded {count} entries from {filename}")

    return summary


def main():
    print("Bootstrapping SLM Knowledge Store...")
    print()

    store = KnowledgeStore()

    existing = store.count()
    if existing > 0:
        print(f"  Store already has {existing} entries.")
        response = input("  Clear and re-seed? [y/N]: ").strip().lower()
        if response != "y":
            print("  Skipping seed. Use --force to override.")
            return

    summary = seed_all(store)

    total = sum(summary.values())
    print()
    print(f"Seeded {total} knowledge entries from {len(summary)} files.")
    print(f"Store now has {store.count()} total entries.")
    print()
    print("Knowledge store is ready. Agents can now query it via:")
    print("  python -m slm.query 'your question here'")


if __name__ == "__main__":
    if "--force" in sys.argv:
        store = KnowledgeStore()
        seed_all(store)
        print(f"\nForce-seeded. Store has {store.count()} entries.")
    else:
        main()
