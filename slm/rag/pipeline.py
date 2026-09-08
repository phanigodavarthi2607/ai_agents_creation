"""
RAG Pipeline — Retrieval-Augmented Generation for grounded SLM responses.

Retrieves relevant domain knowledge from the vector store, constructs
a context-enriched prompt, and sends it to the local LLM (via Ollama)
to generate accurate, source-attributed responses.
"""

import json
from dataclasses import dataclass, field
from typing import Optional

from slm.knowledge.store import KnowledgeStore


@dataclass
class RAGContext:
    """Retrieved context for prompt augmentation."""
    passages: list[dict]
    total_found: int
    categories_covered: list[str]

    def to_prompt_context(self) -> str:
        """Format retrieved passages as context for the LLM prompt."""
        if not self.passages:
            return (
                "NO RELEVANT KNOWLEDGE FOUND. You must state that you don't have "
                "verified information for this query. Do not guess or fabricate an answer."
            )

        lines = ["## Retrieved Domain Knowledge (use ONLY this for your answer)\n"]
        for i, p in enumerate(self.passages, 1):
            lines.append(f"### Source {i} [{p['category']}] (confidence: {p['score']:.0%})")
            lines.append(p["text"])
            lines.append(f"_Source: {p['source']}_\n")

        return "\n".join(lines)


@dataclass
class RAGResponse:
    """Complete RAG response with answer and attribution."""
    answer: str
    sources: list[dict]
    confidence: float
    grounded: bool
    context_used: int


SYSTEM_PROMPT = """You are a QA and Test Automation expert specializing in Private Markets and Fund of Funds (FOF) investment domains. You work with Jira/Xray for test management.

CRITICAL RULES:
1. ONLY use the retrieved domain knowledge provided below to answer questions.
2. If the retrieved knowledge does not contain the answer, say "I don't have verified information about this. This should be flagged as an open question."
3. NEVER invent facts, URLs, field names, API endpoints, or data values.
4. ALWAYS cite which source(s) your answer is based on.
5. If you are uncertain, say so explicitly. Uncertainty is better than a wrong answer.
6. When providing test cases, templates, or code, follow the exact patterns from the knowledge base.
7. For Jira field mappings and Testing Type values, use ONLY the verified values from the knowledge base.

You help with:
- QA testing methodologies (BVA, ECP, Decision Table, etc.)
- Test automation (Playwright, API testing, data pipeline testing)
- Private Markets domain (FOF, investments, Pantheon, BlackRock)
- Jira/Xray test management (field mappings, CSV formats, workflows)
- Test case design and review
- Data quality testing"""


class RAGPipeline:
    """Orchestrates retrieval + generation for grounded responses."""

    def __init__(self, store: Optional[KnowledgeStore] = None):
        self._store = store or KnowledgeStore()

    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        category: Optional[str] = None,
        min_score: float = 0.3,
    ) -> RAGContext:
        """Retrieve relevant knowledge for a query."""
        results = self._store.search(
            query=query,
            n_results=n_results,
            category=category,
            min_score=min_score,
        )

        categories = list(set(r["category"] for r in results))

        return RAGContext(
            passages=results,
            total_found=len(results),
            categories_covered=categories,
        )

    def build_prompt(self, query: str, context: RAGContext) -> list[dict]:
        """Build the complete prompt with system instructions and retrieved context."""
        context_text = context.to_prompt_context()

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"{context_text}\n\n---\n\n## Question\n{query}",
            },
        ]

    def generate(
        self,
        query: str,
        category: Optional[str] = None,
        n_context: int = 5,
    ) -> RAGResponse:
        """Full RAG pipeline: retrieve context -> build prompt -> call LLM.

        Note: This method builds the prompt but requires an LLM backend
        (Ollama) to generate the response. Use the inference module to
        connect to Ollama and complete the generation.
        """
        context = self.retrieve(query, n_results=n_context, category=category)
        prompt = self.build_prompt(query, context)

        from slm.inference.ollama_client import OllamaClient
        client = OllamaClient()
        answer = client.chat(prompt)

        avg_confidence = (
            sum(p["score"] for p in context.passages) / len(context.passages)
            if context.passages
            else 0.0
        )

        return RAGResponse(
            answer=answer,
            sources=[
                {"text": p["text"][:100], "source": p["source"], "score": p["score"]}
                for p in context.passages
            ],
            confidence=round(avg_confidence, 4),
            grounded=len(context.passages) > 0,
            context_used=context.total_found,
        )

    def retrieve_and_format(self, query: str, n_context: int = 5) -> dict:
        """Retrieve context and return it formatted (without LLM call).

        Useful for debugging or when calling an external LLM.
        """
        context = self.retrieve(query, n_results=n_context)
        prompt = self.build_prompt(query, context)

        return {
            "query": query,
            "context": context.to_prompt_context(),
            "messages": prompt,
            "passages_found": context.total_found,
            "categories": context.categories_covered,
        }
