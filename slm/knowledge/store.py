"""
Knowledge Store — vector database for domain knowledge.

Embeds and indexes all domain knowledge (QA, automation, Private Markets,
Jira/Xray) into a ChromaDB vector store for semantic retrieval.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

DEFAULT_STORE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "knowledge_base", ".vectordb"
)
DEFAULT_MODEL = "all-MiniLM-L6-v2"


class KnowledgeStore:
    """Persistent vector store for domain knowledge retrieval."""

    def __init__(
        self,
        store_dir: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self._store_dir = store_dir or os.environ.get("SLM_STORE_DIR", DEFAULT_STORE_DIR)
        os.makedirs(self._store_dir, exist_ok=True)

        self._embedder = SentenceTransformer(model_name or os.environ.get("SLM_MODEL", DEFAULT_MODEL))

        self._client = chromadb.PersistentClient(
            path=self._store_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name="slm_knowledge",
            metadata={"hnsw:space": "cosine"},
        )

    def add(
        self,
        text: str,
        category: str,
        source: str,
        tags: Optional[list[str]] = None,
        entry_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        now = datetime.now(timezone.utc).isoformat()
        doc_id = entry_id or f"{category}_{hash(text) & 0xFFFFFFFF:08x}"

        doc_meta = {
            "category": category,
            "source": source,
            "created_at": now,
        }
        if tags:
            doc_meta["tags"] = ",".join(tags)
        if metadata:
            doc_meta.update(metadata)

        self._collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[doc_meta],
        )
        return doc_id

    def search(
        self,
        query: str,
        n_results: int = 5,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        min_score: float = 0.25,
    ) -> list[dict]:
        where_filter = None
        if category and tags:
            where_filter = {
                "$and": [
                    {"category": category},
                    {"tags": {"$contains": tags[0]}},
                ]
            }
        elif category:
            where_filter = {"category": category}

        results = self._collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        entries = []
        for i, doc_id in enumerate(results["ids"][0]):
            score = 1.0 - results["distances"][0][i]
            if score < min_score:
                continue
            entries.append({
                "id": doc_id,
                "text": results["documents"][0][i],
                "score": round(score, 4),
                "category": results["metadatas"][0][i].get("category"),
                "source": results["metadatas"][0][i].get("source"),
                "tags": results["metadatas"][0][i].get("tags", "").split(","),
                "metadata": results["metadatas"][0][i],
            })
        return entries

    def get_by_category(self, category: str, limit: int = 100) -> list[dict]:
        results = self._collection.get(
            where={"category": category},
            limit=limit,
            include=["documents", "metadatas"],
        )
        return [
            {
                "id": results["ids"][i],
                "text": results["documents"][i],
                "metadata": results["metadatas"][i],
            }
            for i in range(len(results["ids"]))
        ]

    def count(self) -> int:
        return self._collection.count()

    def load_json_file(self, filepath: str, source: Optional[str] = None) -> int:
        with open(filepath) as f:
            entries = json.load(f)

        count = 0
        src = source or f"file:{os.path.basename(filepath)}"
        for entry in entries:
            self.add(
                text=entry["text"],
                category=entry.get("category", "general"),
                source=src,
                tags=entry.get("tags"),
                entry_id=entry.get("id"),
            )
            count += 1
        return count

    def load_all_knowledge(self) -> dict:
        """Load all JSON knowledge files from the knowledge directory."""
        knowledge_dir = os.path.dirname(__file__)
        summary = {}
        for filename in sorted(os.listdir(knowledge_dir)):
            if filename.endswith(".json"):
                filepath = os.path.join(knowledge_dir, filename)
                count = self.load_json_file(filepath)
                summary[filename] = count
        return summary

    def export(self, path: str) -> None:
        results = self._collection.get(include=["documents", "metadatas"])
        entries = [
            {"id": results["ids"][i], "text": results["documents"][i], "metadata": results["metadatas"][i]}
            for i in range(len(results["ids"]))
        ]
        with open(path, "w") as f:
            json.dump(entries, f, indent=2)
