# Organization-Level QA Agent Suite

An AI-powered, multi-project QA agent ecosystem providing end-to-end quality assurance automation — from individual story testing to organization-wide release readiness across any number of projects, domains, and teams.

## Key Design Principle: One System, Any Project

Every project in the organization can have its own:
- **Domain** (finance, data pipelines, UI platforms, etc.)
- **Workflow** (different blocks, gates, and agents per project)
- **Coverage requirements** (different mandatory test categories)
- **Quality thresholds** (stricter gates for critical projects)
- **Compliance controls** (project-specific regulatory requirements)
- **Jira configuration** (different custom fields, CSV formats, link types)
- **Domain knowledge** (project-specific SLM knowledge base)

No code changes needed. Register a project config file and go.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ORGANIZATION LEVEL                                │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Organization Conductor Agent                     │  │
│  │       Coordinates across ALL projects and teams               │  │
│  └──────────┬──────────┬──────────┬──────────┬──────────────────┘  │
│             │          │          │          │                       │
│  ┌──────────▼──┐ ┌─────▼────┐ ┌──▼───────┐ ┌▼────────────────┐   │
│  │ Release     │ │Compliance│ │Cross-Team│ │ Test Metrics    │   │
│  │ Readiness   │ │& Audit   │ │Dependency│ │ & Reporting     │   │
│  └─────────────┘ └──────────┘ └──────────┘ └─────────────────┘   │
│  ┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────┐   │
│  │ Regression  │ │ Defect   │ │Environmt │ │ API Contract    │   │
│  │ Impact      │ │ Triage   │ │Validation│ │ Testing         │   │
│  └─────────────┘ └──────────┘ └──────────┘ └─────────────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│              PROJECT LEVEL (per project, configurable)              │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │ Project A   │  │ Project B   │  │ Project C   │  ...           │
│  │ (PULSE)     │  │ (GXNG)      │  │ (ALPHA)     │                │
│  │ 4-block     │  │ 3-block     │  │ 5-block     │                │
│  │ workflow    │  │ workflow    │  │ workflow    │                │
│  │             │  │             │  │             │                │
│  │ Team PFPT   │  │ Team GX1    │  │ Team Core   │                │
│  │ Team PFPM   │  │ Team GX2    │  │ Team UI     │                │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │
│         │                │                │                        │
│  ┌──────▼──────────────────────────────────▼──────┐                │
│  │           Team Conductor Agent                  │                │
│  │   Reads project config → runs the right workflow│                │
│  └──────┬──────────┬──────────┬───────────────────┘                │
│         │          │          │                                     │
│  ┌──────▼──┐ ┌─────▼────┐ ┌──▼───────┐  (+ more per config)      │
│  │KB Agent │ │Test      │ │Publish   │                             │
│  │Story    │ │Design    │ │Jira      │                             │
│  │Analysis │ │Review    │ │          │                             │
│  └─────────┘ └──────────┘ └──────────┘                             │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                    KNOWLEDGE LAYER (per project)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                         │
│  │ PULSE    │  │ GXNG     │  │ ALPHA    │  Project-specific       │
│  │ knowledge│  │ knowledge│  │ knowledge│  domain knowledge       │
│  └──────────┘  └──────────┘  └──────────┘                         │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  SLM (Small Language Model) - Local RAG + All Knowledge       │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## How to Onboard a New Project (Step-by-Step)

### Step 1: Copy the template

```bash
# Create your project config
cp -r .github/agents/projects/_template .github/agents/projects/<your-project-id>

# Create your knowledge directory
cp -r knowledge_base/projects/_template knowledge_base/projects/<your-project-id>
```

### Step 2: Edit your project config

Open `.github/agents/projects/<your-project-id>/project-config.yaml` and fill in:

```yaml
project:
  id: "MYPROJ"                    # Must match your Jira project key
  name: "My Project Full Name"
  jira_project_key: "MYPROJ"

teams:
  my_team:
    name: "My Team"
    domain: "MyDomain"
    sprint_prefix: "MT"
    lead: "john.doe"
    environments: ["QA", "Staging"]

domain_routing:
  rules:
    - match_sprint_prefix: "MT"
      domain_folder: "MyDomain"
  fallback: "ask_conductor"
```

### Step 3: Choose your workflow

**Option A** — Use the org default 4-block workflow:

```yaml
story_workflow:
  mode: "inherit"    # Uses KB → Discovery → Quality → Release
```

**Option B** — Define a custom workflow for your project:

```yaml
story_workflow:
  mode: "custom"
  blocks:
    - id: "data_discovery"
      name: "Data Discovery"
      agents: ["story-agent", "analysis-agent"]
      gate: "DISCOVERY_APPROVED"
      description: "Discover schemas, DQ rules, transformation logic"

    - id: "test_generation"
      name: "Test Generation"
      agents: ["test-planning-agent", "test-design-agent", "test-data-agent"]
      gate: "TESTS_APPROVED"
      description: "Generate DQ, reconciliation, and pipeline tests"

    - id: "publish"
      name: "Publish"
      agents: ["publish-jira-agent"]
      gate: "APPROVE_FOR_JIRA"
      description: "Publish to Jira"

  mandatory_coverage_categories: ["DataIngestion", "Transformation", "DQ", "Reconciliation"]
```

### Step 4: Register in org-config.yaml

Add your project to the registry:

```yaml
project_registry:
  MYPROJ:
    name: "My Project Full Name"
    config_path: ".github/agents/projects/myproj/project-config.yaml"
    active: true
```

### Step 5: Add domain knowledge (optional but recommended)

Create JSON files in `knowledge_base/projects/<your-id>/` with domain-specific knowledge:

```json
{
  "metadata": {
    "project": "MYPROJ",
    "category": "domain_knowledge"
  },
  "entries": [
    {
      "id": "myproj_rule_1",
      "text": "In MyProject, the reconciliation process requires matching on 3 keys: Account, Security, and Date.",
      "category": "domain_knowledge",
      "source": "architecture-doc"
    }
  ]
}
```

Then reload the SLM:

```bash
python -m slm setup
```

### Step 6: Start using it

```bash
# Process a story
@conductor-agent Process MYPROJ-1234

# Sprint coordination
@org-conductor-agent Sprint coordination for MT Sprint 1

# Release readiness
@release-readiness-agent Assess MYPROJ Release 1.0
```

---

## Custom Workflow Examples

### Example 1: Data Pipeline Project (3 blocks)

A project focused on ETL/data pipelines doesn't need a separate "Knowledge Base" block.

```yaml
story_workflow:
  mode: "custom"
  blocks:
    - id: "data_discovery"
      name: "Data Discovery"
      agents: ["story-agent", "analysis-agent"]
      gate: "DISCOVERY_APPROVED"

    - id: "test_generation"
      name: "Test Generation"
      agents: ["test-planning-agent", "test-design-agent", "test-data-agent"]
      gate: "TESTS_APPROVED"

    - id: "publish"
      name: "Publish"
      agents: ["publish-jira-agent"]
      gate: "APPROVE_FOR_JIRA"

  mandatory_coverage_categories: ["DataIngestion", "Transformation", "DQ", "Reconciliation"]
```

### Example 2: UI Platform Project (5 blocks)

A UI-heavy project needs UX review and accessibility checks.

```yaml
story_workflow:
  mode: "custom"
  blocks:
    - id: "requirements"
      name: "Requirements"
      agents: ["story-agent"]
      gate: "REQUIREMENTS_APPROVED"

    - id: "ux_review"
      name: "UX Review"
      agents: ["analysis-agent"]
      gate: "UX_APPROVED"

    - id: "test_design"
      name: "Test Design"
      agents: ["test-planning-agent", "test-design-agent"]
      gate: "DESIGN_APPROVED"

    - id: "test_review"
      name: "Test Review"
      agents: ["test-review-agent"]
      gate: "REVIEW_APPROVED"

    - id: "publish"
      name: "Publish"
      agents: ["publish-jira-agent"]
      gate: "APPROVE_FOR_JIRA"

  mandatory_coverage_categories: ["UI", "Accessibility", "CrossBrowser", "API"]
```

### Example 3: API-First Project (4 blocks with contract focus)

A microservices project needs contract testing baked into the workflow.

```yaml
story_workflow:
  mode: "custom"
  blocks:
    - id: "discovery"
      name: "API Discovery"
      agents: ["story-agent", "analysis-agent"]
      gate: "DISCOVERY_APPROVED"

    - id: "contract_validation"
      name: "Contract Validation"
      agents: ["api-contract-testing-agent"]
      gate: "CONTRACTS_APPROVED"

    - id: "test_generation"
      name: "Test Generation"
      agents: ["test-planning-agent", "test-design-agent", "test-review-agent"]
      gate: "TESTS_APPROVED"

    - id: "publish"
      name: "Publish"
      agents: ["publish-jira-agent"]
      gate: "APPROVE_FOR_JIRA"

  mandatory_coverage_categories: ["API", "Contract", "Integration", "ErrorHandling"]
```

### Example 4: Inheriting default with stricter gates

Some projects just need the standard workflow but with higher quality bars:

```yaml
story_workflow:
  mode: "inherit"
  mandatory_coverage_categories: ["UI", "API", "Backend", "DataComparison", "Performance"]

quality_gates_overrides:
  G1_test_execution:
    pass_rate_threshold: 99.0    # Stricter than org default 95%
  G4_coverage:
    requirements_coverage_threshold: 95.0   # Stricter than org default 85%
```

---

## Agent Inventory

### Organization-Level Agents (cross-project)

| Agent | File | Key Capability |
|-------|------|---------------|
| Organization Conductor | `org-conductor-agent.md` | Orchestrates cross-project workflows |
| Release Readiness | `release-readiness-agent.md` | 10-gate go/no-go, uses strictest thresholds across projects |
| Compliance & Audit | `compliance-audit-agent.md` | Org frameworks + project-specific controls |
| Security Testing | `security-testing-agent.md` | SAST, DAST, dependency scan, secrets detection, OWASP, pentest coordination |
| Automation | `automation-agent.md` | Candidacy analysis, script generation, CI/CD integration, flaky test management |
| Cross-Team Dependency | `cross-team-dependency-agent.md` | Intra- and cross-project dependency tracking |
| Test Metrics | `test-metrics-agent.md` | Per-project and org-wide dashboards |
| Regression Impact | `regression-impact-agent.md` | Cross-project service dependency analysis |
| Defect Triage | `defect-triage-agent.md` | Auto-detects project from defect key |
| Environment Validation | `environment-validation-agent.md` | Validates per project's environment config |
| API Contract Testing | `api-contract-testing-agent.md` | Cross-project consumer impact analysis |

### Team-Level Agents (per project, configurable)

| Agent | File | Used In |
|-------|------|---------|
| Team Conductor | `conductor-agent.md` | Reads project config, runs the right workflow |
| Knowledge Base | `KnowledgeBase-agent.md` | Uses project's domain routing rules |
| Story | `story-agent.md` | Works with any Jira project key |
| Analysis | `analysis-agent.md` | Builds discovery context |
| Test Planning | `test-planning-agent.md` | Selects techniques based on story |
| Test Design | `test-design-agent.md` | Generates test cases per project's coverage reqs |
| Test Data | `TestData-agent.md` | Generates realistic test data |
| Test Review | `test-review-agent.md` | Reviews against project's standards |
| Publish Jira | `publish-jira-agent.md` | Uses project's Jira field mappings |

---

## Configuration Hierarchy

Settings are resolved in this priority order:

```
1. Project config (highest priority)
   └── .github/agents/projects/<id>/project-config.yaml

2. Organization defaults (fallback)
   └── .github/agents/org-config.yaml → defaults

3. Agent built-in defaults (last resort)
   └── Only for truly universal behavior
```

**For cross-project operations**, the strictest value wins. If Project A requires 95% pass rate and Project B requires 98%, a release containing both uses 98%.

---

## Organization Workflows

### 1. Sprint Coordination

```
@org-conductor-agent Sprint coordination for PFPT Sprint 24
@org-conductor-agent Sprint coordination for [PFPT Sprint 24, GX Sprint 12]
```

Resolves participating projects → dependency analysis → environment validation → team conductors execute in parallel → **automation candidacy analysis** → **security scanning (SAST)** → regression → metrics → readiness.

### 2. Release QA

```
@org-conductor-agent Release QA for PFPM Release 3.2
@org-conductor-agent Release QA for Q3 2026 Release [PULSE, GXNG, ALPHA]
```

Cross-project dependency scan → API contract validation → **full security assessment (SAST + dependencies + secrets + OWASP)** → compliance audit → **automation health check** → regression → metrics → go/no-go.

### 3. Security Scanning

```
@security-testing-agent SAST scan for PULSE-3730
@security-testing-agent Full security assessment for project GXNG
@security-testing-agent Dependency scan for ALPHA release 2.0
@security-testing-agent Secrets detection for project PULSE
```

Scans code, dependencies, secrets, and OWASP compliance. CRITICAL findings block release.

### 4. Automation Management

```
@automation-agent Analyze PULSE-3730 for automation candidacy
@automation-agent Generate scripts for PULSE-3730
@automation-agent Health check for project GXNG
@automation-agent Flaky test analysis for project ALPHA
@automation-agent Automation report for all projects
```

Analyzes test cases for automation ROI, generates scripts in the project's framework, and tracks automation health.

### 5. Defect Escalation

```
@org-conductor-agent Defect escalation for PULSE-4521
@org-conductor-agent Defect escalation for GXNG-892
```

Auto-detects project → triage → cross-project impact → notification → release impact.

### 4. Quality Assessment

```
@org-conductor-agent Quality assessment for all projects
@org-conductor-agent Quality assessment for PULSE project
```

Per-project and aggregated metrics → compliance → environment health → risk summary.

---

## Quality Gates

10 mandatory gates evaluated by the Release Readiness Agent:

| Gate | Threshold (org default) | Can override per project? |
|------|------------------------|--------------------------|
| G1: Test Execution | Pass rate ≥ 95% | Yes (stricter only) |
| G2: Critical Defects | Zero open S1 | No (org minimum) |
| G3: Regression | All P1 suites passed | No (org minimum) |
| G4: Coverage | ≥ 85% requirements | Yes (stricter only) |
| G5: API Contracts | No breaking changes | No (org minimum) |
| G6: Compliance | No CRITICAL findings | No (org minimum) |
| G7: Dependencies | No blocked deps | No (org minimum) |
| G8: Environment | Prod-like validated | No (org minimum) |
| G9: Rollback | Documented + tested | No (org minimum) |
| G10: Sign-off | All leads signed | No (org minimum) |

---

## File Structure

```
.github/agents/
  # Organization config
  org-config.yaml                   # Org defaults, project registry, pipeline definitions

  # Per-project configs
  projects/
    _template/
      project-config.yaml           # Template — copy this for new projects
    pulse/
      project-config.yaml           # PULSE project configuration
    # gxng/
    #   project-config.yaml         # Add more projects here
    # alpha/
    #   project-config.yaml

  # Team-level agents
  conductor-agent.md                # Project-aware team workflow orchestrator
  KnowledgeBase-agent.md
  story-agent.md
  analysis-agent.md
  test-planning-agent.md
  test-design-agent.md
  TestData-agent.md
  test-review-agent.md
  publish-jira-agent.md

  # Organization-level agents
  org-conductor-agent.md            # Cross-project orchestrator
  release-readiness-agent.md
  compliance-audit-agent.md
  security-testing-agent.md         # SAST, DAST, OWASP, secrets, pentest
  automation-agent.md               # Script generation, CI/CD, flaky tests
  cross-team-dependency-agent.md
  test-metrics-agent.md
  regression-impact-agent.md
  defect-triage-agent.md
  environment-validation-agent.md
  api-contract-testing-agent.md

knowledge_base/
  projects/
    _template/                      # Template for project knowledge
      domain_knowledge.json
    pulse/                          # PULSE-specific domain knowledge
      qa_testing.json
      qa_automation.json
      private_markets_domain.json
      jira_xray.json

slm/                               # Small Language Model (local RAG)
requirements.txt                    # Python dependencies
```

---

## Anti-Hallucination Guardrails

Every agent includes strict rules:

1. **No fabricated data** — facts trace to real sources
2. **No invented identifiers** — keys come from actual systems
3. **No assumed status** — verified by checks, not guessed
4. **No inflated metrics** — numbers from data sources only
5. **No silent failures** — errors reported, never hidden
6. **Mandatory source attribution** — every claim cites its source
7. **No hardcoded project values** — always read from project config
