# TestFlowAutomation - AI Agent Skills & SLM Knowledge Layer

This repository contains two components for the TestFlowAutomation QA workflow:

1. **Copilot Agent Skill Files** (`.github/agents/`) — Improved agent definitions with anti-hallucination guardrails
2. **SLM Knowledge Layer** (`slm/`) — A domain-grounded retrieval system that agents query to avoid hallucination

## Architecture

```
Copilot Agent (e.g. test-design-agent)
        |
        | "What are the valid Testing Types for Jira?"
        v
  SLM Knowledge Layer (API)
        |
        | Query embedded knowledge store
        v
  ChromaDB Vector Store
        |
        | Return source-attributed results
        v
  Agent gets grounded answer
  (not a hallucination)
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Bootstrap the knowledge store

```bash
python -m slm seed
```

This loads 30+ domain knowledge entries covering workflow rules, Jira field mappings, test patterns, templates, known limitations, and business rules.

### 3. Query the knowledge layer

```bash
# Natural language query
python -m slm query "What are the valid Testing Type values for Jira?"

# Filter by category
python -m slm query "How does assignee resolution work?" agent_rule

# Check stats
python -m slm stats
```

### 4. Start the API server (for agents to call)

```bash
python -m slm serve
```

The API runs on `http://localhost:8100` with interactive docs at `/docs`.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check + entry count |
| `/query` | POST | Query knowledge layer (main agent endpoint) |
| `/validate` | POST | Validate a field value against domain rules |
| `/knowledge` | POST | Add new knowledge entry |
| `/ingest/{story_key}` | POST | Ingest a completed workflow run |
| `/training/record` | POST | Record a training example |
| `/training/stats` | GET | Training data collection stats |
| `/stats` | GET | Knowledge store stats by category |

### Example: Agent queries the knowledge layer

```bash
curl -X POST http://localhost:8100/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What Testing Type should I use for Data Validation?",
    "agent_name": "test-design-agent",
    "story_key": "PULSE-3730"
  }'
```

Response:
```json
{
  "query": "What Testing Type should I use for Data Validation?",
  "grounding_statement": "Answer grounded in 3 knowledge entries. Top match (confidence=89%): [testing_type_mapping] from agent:publish-jira-agent.",
  "total_found": 3,
  "results": [
    {
      "text": "Jira Testing Type field supports exactly 5 values: Functional, Non Functional, Regression, End to End, Negative. Data Validation maps to Functional.",
      "category": "testing_type_mapping",
      "source": "agent:publish-jira-agent",
      "confidence": 0.89
    }
  ]
}
```

## Growing the Knowledge Base

### Automatic: After each workflow run

```bash
python -m slm ingest PULSE-3730 runs/PULSE-3730/
```

This extracts knowledge from discovery_context.json, quality_pack.json, review_pack.md, publish_report.json, and agent_bus.jsonl.

### Manual: Add specific knowledge

```bash
curl -X POST http://localhost:8100/knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "text": "PULSE-3730 uses a custom IRR calculation that requires Position ID",
    "category": "business_rule",
    "source": "manual:user-feedback"
  }'
```

## Path to Fine-Tuning (Phase 2)

The system automatically collects training data from agent interactions. Check progress:

```bash
python -m slm training-stats
```

When you have 500+ examples, export for fine-tuning:

```bash
python -m slm export-training training_data.jsonl
```

The exported format is compatible with fine-tuning frameworks like Axolotl and Unsloth for models such as Phi-3-mini, Mistral 7B, or Llama 3 8B.

## Knowledge Categories

| Category | Description |
|----------|-------------|
| `domain_rule` | Business domain rules (FOF, Private Markets, client-specific) |
| `jira_field_mapping` | CSV-to-Jira field mappings and custom field IDs |
| `test_pattern` | Test coverage patterns, technique selection rules |
| `template` | Test case templates, CSV formats, document formats |
| `workflow_rule` | 4-block workflow rules, gate tokens, handoff rules |
| `business_rule` | Business logic rules from stories and AC |
| `known_limitation` | Known bugs, workarounds (e.g., Jira subtask 404 bug) |
| `agent_rule` | Rules specific to individual agents |
| `data_schema` | JSON schemas for workflow artifacts |
| `testing_type_mapping` | Testing type normalization rules |

## Agent Skill Files

The `.github/agents/` directory contains 9 Copilot agent skill files with anti-hallucination guardrails. Copy these to your TestFlowAutomation repository.

See the individual agent files for detailed documentation of each agent's rules and constraints.
