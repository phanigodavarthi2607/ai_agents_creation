"""
Knowledge Store — persistent storage and retrieval of domain knowledge.

Uses ChromaDB for vector storage with sentence-transformer embeddings.
Supports adding, querying, and categorizing knowledge entries.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

STORE_DIR = os.environ.get(
    "SLM_STORE_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base", ".vectordb"),
)

EMBEDDING_MODEL = os.environ.get("SLM_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

VALID_CATEGORIES = {
    "domain_rule",
    "jira_field_mapping",
    "test_pattern",
    "template",
    "workflow_rule",
    "business_rule",
    "known_limitation",
    "agent_rule",
    "data_schema",
    "testing_type_mapping",
}


class KnowledgeStore:
    """Embeds and stores domain knowledge for retrieval by agents."""

    def __init__(
        self,
        store_dir: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        self._store_dir = store_dir or STORE_DIR
        os.makedirs(self._store_dir, exist_ok=True)

        model_name = embedding_model or EMBEDDING_MODEL
        self._embedder = SentenceTransformer(model_name)

        self._client = chromadb.PersistentClient(
            path=self._store_dir,
            settings=Settings(anonymized_telemetry=False),
        )

        self._collection = self._client.get_or_create_collection(
            name="domain_knowledge",
            metadata={"hnsw:space": "cosine"},
        )

    def add(
        self,
        text: str,
        category: str,
        source: str,
        metadata: Optional[dict] = None,
        entry_id: Optional[str] = None,
    ) -> str:
        """Add a knowledge entry to the store.

        Args:
            text: The knowledge content to store.
            category: One of the VALID_CATEGORIES.
            source: Where this knowledge came from (e.g., "agent:conductor-agent",
                    "jira:PULSE-3730", "artifact:quality_pack.json").
            metadata: Optional extra metadata.
            entry_id: Optional explicit ID. Auto-generated if omitted.

        Returns:
            The ID of the stored entry.
        """
        if category not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. Must be one of: {sorted(VALID_CATEGORIES)}"
            )

        now = datetime.now(timezone.utc).isoformat()
        doc_id = entry_id or f"{category}_{now}_{hash(text) & 0xFFFFFFFF:08x}"

        doc_metadata = {
            "category": category,
            "source": source,
            "created_at": now,
        }
        if metadata:
            doc_metadata.update(metadata)

        self._collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[doc_metadata],
        )
        return doc_id

    def query(
        self,
        question: str,
        n_results: int = 5,
        category: Optional[str] = None,
        min_score: float = 0.3,
    ) -> list[dict]:
        """Query the knowledge store for relevant entries.

        Args:
            question: Natural language query.
            n_results: Max number of results to return.
            category: Optional filter by category.
            min_score: Minimum similarity score (0-1, cosine). Lower = more permissive.

        Returns:
            List of dicts with keys: id, text, category, source, score, metadata.
        """
        where_filter = {"category": category} if category else None

        results = self._collection.query(
            query_texts=[question],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        entries = []
        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            score = 1.0 - distance

            if score < min_score:
                continue

            entries.append(
                {
                    "id": doc_id,
                    "text": results["documents"][0][i],
                    "score": round(score, 4),
                    "category": results["metadatas"][0][i].get("category"),
                    "source": results["metadatas"][0][i].get("source"),
                    "metadata": results["metadatas"][0][i],
                }
            )

        return entries

    def get_by_category(self, category: str, limit: int = 100) -> list[dict]:
        """Retrieve all entries for a given category."""
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category '{category}'.")

        results = self._collection.get(
            where={"category": category},
            limit=limit,
            include=["documents", "metadatas"],
        )

        entries = []
        for i, doc_id in enumerate(results["ids"]):
            entries.append(
                {
                    "id": doc_id,
                    "text": results["documents"][i],
                    "category": results["metadatas"][i].get("category"),
                    "source": results["metadatas"][i].get("source"),
                    "metadata": results["metadatas"][i],
                }
            )
        return entries

    def count(self) -> int:
        """Return total number of knowledge entries."""
        return self._collection.count()

    def export_all(self, path: str) -> None:
        """Export all entries to a JSON file for backup or inspection."""
        results = self._collection.get(include=["documents", "metadatas"])
        entries = []
        for i, doc_id in enumerate(results["ids"]):
            entries.append(
                {
                    "id": doc_id,
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i],
                }
            )
        with open(path, "w") as f:
            json.dump(entries, f, indent=2)
