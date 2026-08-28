"""
FastAPI server — HTTP API for Copilot agents to query the knowledge layer.

Agents call this API to get grounded, source-attributed domain knowledge
instead of hallucinating. The API supports:
  - Natural language queries
  - Category-filtered lookups
  - Value validation
  - Knowledge ingestion from workflow runs
  - Training data recording

Start with: python -m slm serve
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from slm.core.knowledge_store import KnowledgeStore, VALID_CATEGORIES
from slm.core.query_engine import QueryEngine
from slm.ingestion.workflow_ingestor import WorkflowIngestor
from slm.training.data_collector import TrainingDataCollector

app = FastAPI(
    title="SLM Knowledge Layer API",
    description=(
        "Domain knowledge retrieval service for TestFlowAutomation Copilot agents. "
        "Query this API to get grounded facts instead of hallucinating."
    ),
    version="0.1.0",
)

_store = KnowledgeStore()
_engine = QueryEngine(_store)
_ingestor = WorkflowIngestor(_store)
_collector = TrainingDataCollector()


class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    category: Optional[str] = Field(None, description="Filter by knowledge category")
    agent_name: Optional[str] = Field(None, description="Name of the calling agent")
    story_key: Optional[str] = Field(None, description="Jira story key for context")
    n_results: int = Field(5, ge=1, le=20, description="Max results")
    min_confidence: float = Field(0.4, ge=0.0, le=1.0, description="Minimum confidence")


class QueryResponse(BaseModel):
    query: str
    grounding_statement: str
    total_found: int
    results: list[dict]


class ValidateRequest(BaseModel):
    field_name: str = Field(..., description="Field to validate")
    value: str = Field(..., description="Value to check")
    context: str = Field("", description="Additional context")


class AddKnowledgeRequest(BaseModel):
    text: str = Field(..., description="Knowledge content")
    category: str = Field(..., description=f"One of: {sorted(VALID_CATEGORIES)}")
    source: str = Field(..., description="Source attribution (e.g., 'jira:PULSE-3730')")
    entry_id: Optional[str] = Field(None, description="Optional explicit ID")
    metadata: Optional[dict] = Field(None, description="Optional extra metadata")


class RecordTrainingRequest(BaseModel):
    question: str
    answer: str
    category: str
    source: str
    agent_name: str
    story_key: Optional[str] = None
    user_approved: bool = False
    user_correction: Optional[str] = None


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "entries": _store.count()}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    """Query the knowledge layer for domain-grounded answers.

    This is the primary endpoint agents should call when they need
    factual information about the PULSE project, QA workflow, Jira
    field mappings, test patterns, etc.
    """
    if req.category and req.category not in VALID_CATEGORIES:
        raise HTTPException(
            400, f"Invalid category '{req.category}'. Valid: {sorted(VALID_CATEGORIES)}"
        )

    response = _engine.ask(
        question=req.question,
        category=req.category,
        agent_name=req.agent_name,
        story_key=req.story_key,
        n_results=req.n_results,
        min_confidence=req.min_confidence,
    )

    return QueryResponse(
        query=response.query,
        grounding_statement=response.grounding_statement,
        total_found=response.total_found,
        results=[
            {
                "text": r.text,
                "category": r.category,
                "source": r.source,
                "confidence": r.confidence,
            }
            for r in response.results
        ],
    )


@app.post("/validate")
def validate(req: ValidateRequest):
    """Validate a field value against stored domain rules.

    Agents call this before committing values to outputs — e.g., to
    check if a Testing Type value is valid before writing it to Jira.
    """
    return _engine.validate_value(req.field_name, req.value, req.context)


@app.post("/knowledge")
def add_knowledge(req: AddKnowledgeRequest):
    """Add a new knowledge entry to the store.

    Use this to grow the knowledge base with facts learned during
    workflow runs or manual corrections.
    """
    if req.category not in VALID_CATEGORIES:
        raise HTTPException(
            400, f"Invalid category '{req.category}'. Valid: {sorted(VALID_CATEGORIES)}"
        )

    entry_id = _store.add(
        text=req.text,
        category=req.category,
        source=req.source,
        entry_id=req.entry_id,
        metadata=req.metadata,
    )
    return {"id": entry_id, "status": "added"}


@app.post("/ingest/{story_key}")
def ingest_run(story_key: str, runs_dir: str):
    """Ingest outputs from a completed workflow run.

    Call this after a full workflow run completes to capture new
    domain knowledge from the outputs.
    """
    summary = _ingestor.ingest_run(story_key, runs_dir)
    return summary


@app.post("/training/record")
def record_training(req: RecordTrainingRequest):
    """Record a training example for future fine-tuning.

    Call this when a user approves or corrects an agent's output
    to capture high-quality training data.
    """
    _collector.record_example(
        question=req.question,
        answer=req.answer,
        category=req.category,
        source=req.source,
        agent_name=req.agent_name,
        story_key=req.story_key,
        user_approved=req.user_approved,
        user_correction=req.user_correction,
    )
    return {"status": "recorded"}


@app.get("/training/stats")
def training_stats():
    """Get training data collection statistics.

    Check this to see if you have enough data for fine-tuning (500+ examples).
    """
    return _collector.get_stats()


@app.get("/stats")
def store_stats():
    """Get knowledge store statistics by category."""
    total = _store.count()
    by_category = {}
    for cat in sorted(VALID_CATEGORIES):
        entries = _store.get_by_category(cat)
        if entries:
            by_category[cat] = len(entries)
    return {"total": total, "by_category": by_category}
