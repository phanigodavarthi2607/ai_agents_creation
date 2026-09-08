# State Street Organization-Level QA Agent Suite

An AI-powered QA agent ecosystem for State Street, providing end-to-end quality assurance automation from individual story testing to organization-wide release readiness across all teams.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ORGANIZATION LEVEL                                │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Organization Conductor Agent                     │  │
│  │  Orchestrates cross-team workflows, aggregates org metrics    │  │
│  └──────────┬───────────────┬──────────────┬────────────────────┘  │
│             │               │              │                        │
│  ┌──────────▼──┐  ┌────────▼───┐  ┌──────▼──────┐  ┌──────────┐  │
│  │ Release     │  │ Compliance │  │ Cross-Team  │  │ Test     │  │
│  │ Readiness   │  │ & Audit    │  │ Dependency  │  │ Metrics  │  │
│  └─────────────┘  └────────────┘  └─────────────┘  └──────────┘  │
│                                                                     │
│  ┌─────────────┐  ┌────────────┐  ┌─────────────┐  ┌──────────┐  │
│  │ Regression  │  │ Defect     │  │ Environment │  │ API      │  │
│  │ Impact      │  │ Triage     │  │ Validation  │  │ Contract │  │
│  └─────────────┘  └────────────┘  └─────────────┘  └──────────┘  │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                    TEAM LEVEL (per team/story)                       │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Team Conductor Agent                              │  │
│  │  KB → Discovery → Quality → Release (per story)               │  │
│  └──────────┬──────────┬──────────┬──────────┬──────────────────┘  │
│             │          │          │          │                       │
│  ┌──────────▼──┐ ┌─────▼────┐ ┌──▼───────┐ ┌▼────────────────┐   │
│  │ Knowledge   │ │ Story    │ │ Analysis │ │ Test Planning   │   │
│  │ Base        │ │ Agent    │ │ Agent    │ │ Agent           │   │
│  └─────────────┘ └──────────┘ └──────────┘ └─────────────────┘   │
│                                                                     │
│  ┌─────────────┐  ┌───────────┐  ┌────────────┐  ┌────────────┐  │
│  │ Test Design │  │ Test      │  │ Test Data  │  │ Publish    │  │
│  │ Agent       │  │ Review    │  │ Agent      │  │ Jira Agent │  │
│  └─────────────┘  └───────────┘  └────────────┘  └────────────┘  │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                    KNOWLEDGE LAYER                                   │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  SLM (Small Language Model) - Local RAG + Domain Knowledge    │  │
│  │  ChromaDB Vector Store  │  Ollama LLM  │  FastAPI Server      │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Agent Inventory

### Organization-Level Agents (NEW)

These agents operate across teams and provide organization-wide QA capabilities:

| Agent | Purpose | Key Capability |
|-------|---------|---------------|
| **Organization Conductor** | Top-level orchestrator for cross-team workflows | Coordinates sprint, release, and defect escalation workflows |
| **Release Readiness** | Go/no-go assessment for releases | Aggregates 10 quality gates from all agents |
| **Compliance & Audit** | Regulatory compliance validation | SOX, SEC, OCC, GDPR compliance checks |
| **Cross-Team Dependency** | Inter-team dependency management | Tracks blocking/soft/data/environment/contract dependencies |
| **Test Metrics & Reporting** | Organization-wide QA dashboards | Quality Health Score, trend analysis, executive reports |
| **Regression Impact** | Cross-team regression scope analysis | Dependency graph traversal, prioritized test suite selection |
| **Defect Triage** | Automated defect classification and routing | Severity assessment, root cause taxonomy, duplicate detection |
| **Environment Validation** | Pre-execution environment health checks | Service health, config validation, data readiness, security |
| **API Contract Testing** | Cross-service API contract validation | Breaking change detection, consumer impact, compliance scoring |

### Team-Level Agents (existing, enhanced)

These agents handle the per-story QA workflow within a single team:

| Agent | Purpose | Workflow Block |
|-------|---------|---------------|
| **Conductor** | Team-level story workflow orchestrator | All blocks |
| **Knowledge Base** | Collects and documents domain knowledge | Knowledge Base |
| **Story** | Fetches and normalizes Jira story data | Knowledge Base |
| **Analysis** | Merges story + artifacts for discovery context | Discovery |
| **Test Planning** | Defines test strategy and techniques | Discovery |
| **Test Design** | Generates template-compliant test cases | Quality |
| **Test Data** | Generates realistic test data for scenarios | Quality |
| **Test Review** | Reviews and refines test cases | Quality |
| **Publish Jira** | Publishes approved tests to Jira/Xray | Release |

## Workflows

### 1. Team Story Workflow (per story)

```
User provides storyKey
        │
        ▼
[Knowledge Base Block]
  KB Agent → Story Agent
        │
   KB_APPROVED (user gate)
        │
        ▼
[Discovery Block]
  Analysis Agent + Test Planning Agent
        │
   DISCOVERY_APPROVED (user gate)
        │
        ▼
[Quality Block]
  Test Design Agent → Test Data Agent → Test Review Agent
        │
   QUALITY_APPROVED (user gate)
        │
        ▼
[Release Block]
  Publish Jira Agent
        │
   APPROVE_FOR_JIRA (user gate)
        │
        ▼
  Tests published to Jira/Xray
```

### 2. Sprint Coordination (organization level)

```
Sprint Start
     │
     ▼
Cross-Team Dependency Agent → Identify dependencies & conflicts
     │
     ▼
Environment Validation Agent → Validate all team environments
     │
     ▼
Team Conductors execute story workflows (parallel)
     │
     ▼
Regression Impact Agent → Cross-team regression scope
     │
     ▼
Test Metrics Agent → Sprint dashboard & quality scores
     │
     ▼
Release Readiness Agent → Sprint go/no-go
```

### 3. Release Workflow (organization level)

```
Release Planning
     │
     ▼
Cross-Team Dependency Agent → Full release dependency scan
     │
     ▼
API Contract Testing Agent → Validate all modified service contracts
     │
     ▼
Compliance & Audit Agent → Regulatory compliance verification
     │
     ▼
Regression Impact Agent → Full release regression scope
     │
     ▼
Test Metrics Agent → Release quality report
     │
     ▼
Release Readiness Agent → Final GO / NO_GO / CONDITIONAL_GO
     │
     ├── GO → Proceed to production deployment
     ├── CONDITIONAL_GO → Proceed with monitoring plan
     └── NO_GO → Block and resolve blockers
```

### 4. Defect Escalation (triggered by S1/S2 defect)

```
S1/S2 Defect Reported
     │
     ▼
Defect Triage Agent → Classify, assess severity, route to team
     │
     ▼
Regression Impact Agent → What else might be affected?
     │
     ▼
Cross-Team Dependency Agent → Which teams need notification?
     │
     ▼
Release Readiness Agent → Update go/no-go assessment
```

## Quality Gates

The Release Readiness Agent evaluates 10 mandatory gates:

| Gate | Criteria | Threshold |
|------|----------|-----------|
| G1: Test Execution | All tests executed | Pass rate ≥ 95% |
| G2: Critical Defects | No blockers | Zero open S1, S2 have workarounds |
| G3: Regression | P1 suites complete | All passed |
| G4: Coverage | Requirements mapped | ≥ 85%, all categories covered |
| G5: API Contracts | No breaking changes | All compatible |
| G6: Compliance | Regulatory checks | No CRITICAL findings |
| G7: Dependencies | Team coordination | No blocked dependencies |
| G8: Environment | Production-ready | Validated and healthy |
| G9: Rollback | Safety net | Documented and tested |
| G10: Sign-off | Team leads | All signed off |

## Configuration

Organization-wide settings are in `.github/agents/org-config.yaml`:

- Team registry and domain mapping
- Service registry with dependencies
- Quality gate thresholds
- Severity matrix and SLAs
- Defect root cause taxonomy
- API standards
- Compliance frameworks
- Agent pipeline definitions

## Quick Start

### For a Single Story (Team Level)

Invoke the **Conductor Agent** with a Jira story key:

```
@conductor-agent Process PULSE-3730
```

The conductor will guide you through all 4 blocks with approval gates.

### For Sprint Coordination (Organization Level)

Invoke the **Organization Conductor**:

```
@org-conductor-agent Sprint coordination for PFPT Sprint 24
```

### For Release Readiness

```
@release-readiness-agent Assess PFPM Release 3.2 targeting 2026-09-15
```

### For Defect Triage

```
@defect-triage-agent Triage PULSE-4521
```

### For Compliance Audit

```
@compliance-audit-agent Regulatory audit for PFPM Release 3.2
```

### For Cross-Team Dependencies

```
@cross-team-dependency-agent Analyze dependencies for PFPT Sprint 24
```

## SLM (Small Language Model)

The knowledge layer provides domain-grounded answers without cloud API keys:

```bash
# Setup
pip install -r requirements.txt
ollama pull phi3:mini
python -m slm setup

# Ask questions
python -m slm ask "What testing techniques for data pipeline DQ rules?"

# Search knowledge
python -m slm search "boundary value analysis"

# Start API server
python -m slm serve
```

See the `slm/` directory for full documentation.

## Anti-Hallucination Guardrails

Every agent in this suite includes strict anti-hallucination rules:

1. **No fabricated data** — Every fact must trace to a real source (Jira, artifacts, API responses)
2. **No invented identifiers** — Story keys, defect keys, team names, service names must come from actual systems
3. **No assumed status** — Every status (green/red/amber) must be backed by verified checks
4. **No inflated metrics** — Numbers come from data sources, not estimates
5. **No silent failures** — Errors are reported, never hidden or ignored
6. **Mandatory source attribution** — Every claim links to its source
7. **Explicit uncertainty** — Assumptions are labeled as assumptions, not presented as facts

## File Structure

```
.github/
  agents/
    # Team-level agents (story workflow)
    conductor-agent.md          # Team story workflow orchestrator
    KnowledgeBase-agent.md      # Knowledge collection from Jira/Confluence
    story-agent.md              # Jira story fetching and normalization
    analysis-agent.md           # Discovery context builder
    test-planning-agent.md      # Test strategy and technique selection
    test-design-agent.md        # Test case generation
    TestData-agent.md           # Test data generation
    test-review-agent.md        # Test case review and refinement
    publish-jira-agent.md       # Jira/Xray publishing

    # Organization-level agents (cross-team)
    org-conductor-agent.md      # Organization workflow orchestrator
    release-readiness-agent.md  # Go/no-go assessment
    compliance-audit-agent.md   # Regulatory compliance validation
    cross-team-dependency-agent.md  # Inter-team dependency tracking
    test-metrics-agent.md       # Organization-wide metrics & dashboards
    regression-impact-agent.md  # Cross-team regression analysis
    defect-triage-agent.md      # Defect classification and routing
    environment-validation-agent.md  # Environment health validation
    api-contract-testing-agent.md    # API contract validation

    # Configuration
    org-config.yaml             # Organization-wide settings

knowledge_base/                 # Domain knowledge for SLM
slm/                           # Small Language Model (local RAG)
requirements.txt               # Python dependencies
```

## Teams & Domains

| Team | Domain Folder | Sprint Prefix | Focus Area |
|------|--------------|---------------|------------|
| PFPT | `FOF/` | PFPT | Private Fund Processing Technology |
| PFPM | `Private_Markets/` | PFPM | Private Markets Investment Operations |

## Contributing

When adding new agents or modifying existing ones:

1. Follow the existing agent template format (YAML frontmatter + markdown body)
2. Include anti-hallucination rules specific to the agent's domain
3. Define strict input validation
4. Define strict output JSON schema
5. Document handoff to downstream agents
6. Update `org-config.yaml` if the agent participates in a pipeline
7. Test with real Jira stories before merging
