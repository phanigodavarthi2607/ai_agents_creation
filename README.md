# QA & Test Automation SLM

A standalone, locally-deployed Small Language Model (SLM) for QA testing, test automation, and investment domain knowledge. Runs entirely on your machine — no cloud API keys needed.

## What It Does

```
You: "What testing techniques should I use for a data pipeline with DQ rules?"

SLM: Based on verified domain knowledge:

1. Data Quality Testing - validate source-to-target field mapping, record count
   reconciliation, null handling, and business rule compliance
2. BVA - test threshold values at boundaries (min, max, min-1, max+1)
3. Negative Testing - invalid data types, out-of-range values, missing fields
4. End-to-End - trace data from source file through transformation to target

Sources: [qa_methodology] qa_testing.json, [domain_knowledge] private_markets_domain.json
```

## Architecture

```
                    ┌─────────────────────────────┐
                    │     Your Question            │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │     RAG Pipeline             │
                    │                              │
                    │  1. Embed question           │
                    │  2. Search vector store      │
                    │  3. Retrieve top-N matches   │
                    │  4. Build grounded prompt    │
                    └──────────┬──────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
   ┌──────────▼───────┐  ┌────▼─────┐  ┌──────▼──────────┐
   │  Knowledge Store  │  │  Ollama  │  │  API Server     │
   │  (ChromaDB)       │  │  (Local  │  │  (FastAPI)      │
   │                   │  │   LLM)   │  │                 │
   │  - QA Methods     │  │  Phi-3   │  │  /ask           │
   │  - Automation     │  │  Mistral │  │  /search        │
   │  - Private Mkts   │  │  Llama   │  │  /knowledge     │
   │  - Jira/Xray      │  │          │  │  /stats         │
   └───────────────────┘  └──────────┘  └─────────────────┘
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Ollama (local LLM runtime)

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: download from https://ollama.com/download
```

### 3. Pull a model

```bash
# Recommended for most machines (3.8B parameters, ~2.3GB)
ollama pull phi3:mini

# Alternative: Mistral 7B (better quality, needs more RAM)
ollama pull mistral

# Alternative: Llama 3 8B (best quality, needs 8GB+ RAM)
ollama pull llama3
```

### 4. Setup the SLM

```bash
python -m slm setup
```

This loads 48+ domain knowledge entries and verifies Ollama connectivity.

### 5. Start asking questions

```bash
# Full RAG mode (retrieval + LLM)
python -m slm ask "What are the valid Testing Type values for Jira?"

# Knowledge search only (no LLM needed)
python -m slm search "boundary value analysis"

# Start API server
python -m slm serve
```

## Domain Knowledge Included

| Category | Entries | Covers |
|----------|---------|--------|
| QA Methodology | 14 | BVA, ECP, Decision Table, Negative, Integration, Regression, E2E, DQ Testing, test design practices |
| Automation | 12 | Playwright, API testing, data pipeline testing, POM, fixtures, CI/CD, reporting |
| Private Markets | 10 | FOF, IRR, Pantheon, BlackRock, transactions, Position ID, data pipelines, PFPT/PFPM |
| Jira/Xray | 10 | Field mappings, Testing Types, PULSE-3336 CSV, AC handling, idempotent operations |

## CLI Commands

| Command | Description |
|---------|-------------|
| `python -m slm setup` | First-time setup: load knowledge + check Ollama |
| `python -m slm ask "question"` | Ask question with RAG + LLM |
| `python -m slm search "query"` | Search knowledge base (no LLM) |
| `python -m slm stats` | Show knowledge store statistics |
| `python -m slm serve` | Start HTTP API on port 8100 |
| `python -m slm generate-training` | Generate fine-tuning training data |
| `python -m slm add "text" category` | Add knowledge entry |
| `python -m slm export output.json` | Export knowledge to JSON |

## API Endpoints

Start the server with `python -m slm serve`, then:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check + Ollama status |
| `/ask` | POST | Full RAG: retrieval + LLM generation |
| `/search` | POST | Knowledge search (no LLM) |
| `/knowledge` | POST | Add new knowledge entry |
| `/context` | POST | Get RAG context without LLM call |
| `/stats` | GET | Knowledge store statistics |
| `/categories` | GET | List knowledge categories |

### Example API call

```bash
curl -X POST http://localhost:8100/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I test Contribution transactions in Private Markets?"}'
```

## Adding Your Own Knowledge

```bash
# Via CLI
python -m slm add "Custom field XYZ maps to customfield_12345 in Jira" jira_integration

# Via API
curl -X POST http://localhost:8100/knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "text": "For PULSE project, regression testing must include IRR recalculation after any transaction modification",
    "category": "domain_knowledge",
    "source": "team-knowledge"
  }'
```

## Path to Fine-Tuning

When you're ready to create a custom fine-tuned model:

### 1. Generate training data

```bash
python -m slm generate-training
```

This creates training datasets in three formats (Alpaca, ChatML, ShareGPT) from the knowledge base.

### 2. Fine-tune (requires GPU)

```bash
# Install fine-tuning dependencies
pip install unsloth transformers datasets peft trl

# Run fine-tuning (Google Colab free tier works)
python slm/training/finetune.py
```

### 3. Export to Ollama

```bash
python slm/training/export_ollama.py
ollama create qa-slm -f slm/config/modelfile_finetuned
```

### 4. Use your custom model

```bash
SLM_OLLAMA_MODEL=qa-slm python -m slm ask "your question"
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SLM_OLLAMA_MODEL` | `phi3:mini` | Ollama model to use |
| `SLM_OLLAMA_URL` | `http://localhost:11434` | Ollama API URL |
| `SLM_STORE_DIR` | `knowledge_base/.vectordb` | Vector store path |
| `SLM_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |

## Copilot Agent Skills

The `.github/agents/` directory contains 9 improved Copilot agent skill files with anti-hallucination guardrails. These are independent of the SLM but complement it — agents can call the SLM API for grounded answers.
