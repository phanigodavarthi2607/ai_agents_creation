"""
FastAPI server — HTTP API for the standalone SLM.

Provides endpoints for:
  - Asking questions (RAG + local LLM)
  - Searching knowledge base
  - Adding new knowledge
  - Generating test artifacts
  - Health checks

Start with: python -m slm serve
Docs at: http://localhost:8100/docs
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from slm.knowledge.store import KnowledgeStore
from slm.rag.pipeline import RAGPipeline

app = FastAPI(
    title="SLM - QA & Test Automation Knowledge Model",
    description=(
        "A locally-deployed, domain-specific language model for QA testing, "
        "automation, Private Markets domain, and Jira/Xray integration."
    ),
    version="0.1.0",
)

_store = KnowledgeStore()
_pipeline = RAGPipeline(_store)


class AskRequest(BaseModel):
    question: str = Field(..., description="Your question")
    category: Optional[str] = Field(None, description="Filter by knowledge category")
    n_context: int = Field(5, ge=1, le=20, description="Number of context passages to retrieve")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    category: Optional[str] = Field(None, description="Filter by category")
    n_results: int = Field(5, ge=1, le=50)
    min_score: float = Field(0.25, ge=0.0, le=1.0)


class AddKnowledgeRequest(BaseModel):
    text: str = Field(..., description="Knowledge content")
    category: str = Field(..., description="Category (e.g., qa_methodology, domain_knowledge)")
    source: str = Field("manual", description="Source attribution")
    tags: Optional[list[str]] = Field(None, description="Optional tags")


@app.get("/health")
def health():
    total = _store.count()
    from slm.inference.ollama_client import OllamaClient
    client = OllamaClient()
    ollama_ok = client.is_available()
    return {
        "status": "ok",
        "knowledge_entries": total,
        "ollama_available": ollama_ok,
        "ollama_model": client.model if ollama_ok else None,
    }


@app.post("/ask")
def ask(req: AskRequest):
    """Ask a question using RAG (retrieval + LLM generation).

    Retrieves relevant domain knowledge, builds a context-enriched prompt,
    and generates a grounded response via the local LLM (Ollama).
    """
    from slm.inference.ollama_client import OllamaClient
    client = OllamaClient()

    if not client.is_available():
        context = _pipeline.retrieve(req.question, n_results=req.n_context, category=req.category)
        return {
            "answer": None,
            "error": "Ollama is not running. Install from https://ollama.com and run: ollama pull phi3:mini",
            "search_results": [
                {"text": p["text"], "category": p["category"], "source": p["source"], "score": p["score"]}
                for p in context.passages
            ],
        }

    try:
        response = _pipeline.generate(req.question, category=req.category, n_context=req.n_context)
        return {
            "answer": response.answer,
            "grounded": response.grounded,
            "confidence": response.confidence,
            "sources": response.sources,
            "context_used": response.context_used,
        }
    except Exception as e:
        raise HTTPException(500, f"Generation failed: {str(e)}")


@app.post("/search")
def search(req: SearchRequest):
    """Search the knowledge base without LLM generation.

    Returns ranked knowledge entries matching the query.
    """
    results = _store.search(
        query=req.query,
        n_results=req.n_results,
        category=req.category,
        min_score=req.min_score,
    )
    return {"query": req.query, "total": len(results), "results": results}


@app.post("/knowledge")
def add_knowledge(req: AddKnowledgeRequest):
    """Add a new knowledge entry to the store."""
    entry_id = _store.add(
        text=req.text,
        category=req.category,
        source=req.source,
        tags=req.tags,
    )
    return {"id": entry_id, "status": "added", "total_entries": _store.count()}


@app.get("/stats")
def stats():
    """Get knowledge store statistics."""
    total = _store.count()
    categories = {}
    for cat in ["qa_methodology", "qa_best_practice", "automation_framework",
                "automation_pattern", "domain_knowledge", "jira_integration"]:
        entries = _store.get_by_category(cat)
        if entries:
            categories[cat] = len(entries)
    return {"total": total, "by_category": categories}


@app.get("/categories")
def list_categories():
    """List all knowledge categories with descriptions."""
    return {
        "categories": {
            "qa_methodology": "Testing techniques (BVA, ECP, Decision Table, etc.)",
            "qa_best_practice": "QA best practices (test design, coverage, traceability)",
            "automation_framework": "Automation frameworks (Playwright, Selenium, etc.)",
            "automation_pattern": "Automation design patterns (POM, fixtures, data-driven)",
            "domain_knowledge": "Private Markets & FOF domain knowledge",
            "jira_integration": "Jira/Xray field mappings, formats, and workflows",
        }
    }


@app.post("/context")
def get_context(req: AskRequest):
    """Retrieve RAG context without calling the LLM.

    Useful for debugging or when using an external LLM.
    Returns the formatted context and prompt messages.
    """
    result = _pipeline.retrieve_and_format(req.question, n_context=req.n_context)
    return result
