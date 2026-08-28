"""
Query Engine — the interface Copilot agents use to get grounded answers.

Agents send a natural-language question + optional context, and the engine
returns relevant knowledge entries with source attribution. This prevents
agents from hallucinating by giving them verified domain facts.
"""

from dataclasses import dataclass, field
from typing import Optional

from .knowledge_store import KnowledgeStore


@dataclass
class QueryResult:
    """A single knowledge result returned to an agent."""

    text: str
    category: str
    source: str
    confidence: float
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentQueryResponse:
    """Complete response to an agent query."""

    query: str
    results: list[QueryResult]
    total_found: int
    grounding_statement: str


class QueryEngine:
    """Processes agent queries against the knowledge store and returns
    source-attributed, confidence-scored results."""

    def __init__(self, store: Optional[KnowledgeStore] = None):
        self._store = store or KnowledgeStore()

    def ask(
        self,
        question: str,
        category: Optional[str] = None,
        agent_name: Optional[str] = None,
        story_key: Optional[str] = None,
        n_results: int = 5,
        min_confidence: float = 0.4,
    ) -> AgentQueryResponse:
        """Query the knowledge layer for grounded domain answers.

        Args:
            question: The agent's question in natural language.
            category: Optional category filter (e.g., "domain_rule", "test_pattern").
            agent_name: Which agent is asking (for audit/logging).
            story_key: Optional story context for relevance boosting.
            n_results: Maximum results to return.
            min_confidence: Minimum confidence threshold (0-1).

        Returns:
            AgentQueryResponse with ranked, source-attributed results.
        """
        raw_results = self._store.query(
            question=question,
            n_results=n_results,
            category=category,
            min_score=min_confidence,
        )

        results = [
            QueryResult(
                text=r["text"],
                category=r["category"],
                source=r["source"],
                confidence=r["score"],
                metadata=r["metadata"],
            )
            for r in raw_results
        ]

        if results:
            top = results[0]
            grounding = (
                f"Answer grounded in {len(results)} knowledge entries. "
                f"Top match (confidence={top.confidence:.0%}): "
                f"[{top.category}] from {top.source}."
            )
        else:
            grounding = (
                "No matching knowledge found. Agent should flag this as an "
                "open question rather than guessing."
            )

        return AgentQueryResponse(
            query=question,
            results=results,
            total_found=len(results),
            grounding_statement=grounding,
        )

    def get_domain_rules(self, domain: Optional[str] = None) -> list[QueryResult]:
        """Retrieve all domain rules, optionally filtered by domain name."""
        entries = self._store.get_by_category("domain_rule")
        results = [
            QueryResult(
                text=e["text"],
                category=e["category"],
                source=e["source"],
                confidence=1.0,
                metadata=e["metadata"],
            )
            for e in entries
        ]
        if domain:
            results = [r for r in results if domain.lower() in r.text.lower()]
        return results

    def get_field_mappings(self) -> list[QueryResult]:
        """Retrieve all Jira field mappings."""
        entries = self._store.get_by_category("jira_field_mapping")
        return [
            QueryResult(
                text=e["text"],
                category=e["category"],
                source=e["source"],
                confidence=1.0,
                metadata=e["metadata"],
            )
            for e in entries
        ]

    def get_test_patterns(self, coverage_type: Optional[str] = None) -> list[QueryResult]:
        """Retrieve test patterns, optionally filtered by coverage type."""
        entries = self._store.get_by_category("test_pattern")
        results = [
            QueryResult(
                text=e["text"],
                category=e["category"],
                source=e["source"],
                confidence=1.0,
                metadata=e["metadata"],
            )
            for e in entries
        ]
        if coverage_type:
            results = [r for r in results if coverage_type.lower() in r.text.lower()]
        return results

    def validate_value(
        self, field_name: str, value: str, context: str = ""
    ) -> dict:
        """Check if a value is valid for a given field based on stored rules.

        Returns a dict with 'valid' (bool), 'reason' (str), and 'suggestion' (str).
        Agents use this to validate outputs before committing them.
        """
        question = f"What are the valid values for {field_name}? Context: {context}"
        response = self.ask(question, category="domain_rule", n_results=3)

        if not response.results:
            return {
                "valid": False,
                "reason": f"No validation rules found for field '{field_name}'.",
                "suggestion": "Flag as open question — no domain rule exists for this field.",
            }

        top = response.results[0]
        value_lower = value.lower()
        text_lower = top.text.lower()

        if value_lower in text_lower:
            return {
                "valid": True,
                "reason": f"Value '{value}' matches domain rule from {top.source}.",
                "suggestion": "",
            }

        return {
            "valid": False,
            "reason": f"Value '{value}' not found in domain rule: {top.text[:200]}",
            "suggestion": f"Check rule from {top.source} for valid values.",
        }
