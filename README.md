# Organization-Level QA Agent Suite

An AI-powered, multi-project QA agent ecosystem providing end-to-end quality assurance automation — from individual story testing to organization-wide release readiness across any number of projects, domains, and teams. **37 specialized agents** covering the full QA lifecycle: story processing, automation, security, predictive intelligence, self-healing tests, exploratory testing, performance, accessibility, data quality, and organizational learning.

## Key Design Principle: One System, Any Project

Every project in the organization can have its own:
- **Domain** (finance, data pipelines, UI platforms, etc.)
- **Workflow** (different blocks, gates, and agents per project)
- **Coverage requirements** (different mandatory test categories)
- **Quality thresholds** (stricter gates for critical projects)
- **Jira configuration** (different custom fields, CSV formats, link types)
- **Domain knowledge** (project-specific knowledge base JSON files)

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
│  │ Release     │ │Cross-Team│ │ Defect   │ │ Test Metrics    │   │
│  │ Readiness   │ │Dependency│ │ Triage   │ │ & Reporting     │   │
│  └─────────────┘ └──────────┘ └──────────┘ └─────────────────┘   │
│  ┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────┐   │
│  │ Regression  │ │ Security │ │Environmt │ │ API Contract    │   │
│  │ Impact      │ │ Testing  │ │Validation│ │ Testing         │   │
│  └─────────────┘ └──────────┘ └──────────┘ └─────────────────┘   │
│  ┌─────────────┐                                                  │
│  │ Automation  │                                                  │
│  └─────────────┘                                                  │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│              PROJECT LEVEL (per project, configurable)              │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │ Project A   │  │ Project B   │  │ Project C   │  ...           │
│  │ (PULSE)     │  │ (GXNG)      │  │ (ALPHA)     │                │
│  │ 5-block     │  │ 3-block     │  │ 6-block     │                │
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
│  ┌──────▼──┐ ┌─────▼────┐ ┌──▼───────┐ ┌──────────┐              │
│  │KB Agent │ │Test      │ │Automate  │ │Publish   │              │
│  │Story    │ │Design    │ │Scripts   │ │Jira      │              │
│  │Analysis │ │Review    │ │          │ │          │              │
│  └─────────┘ └──────────┘ └──────────┘ └──────────┘              │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                    KNOWLEDGE LAYER (per project)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                         │
│  │ PULSE    │  │ GXNG     │  │ ALPHA    │  Project-specific       │
│  │ knowledge│  │ knowledge│  │ knowledge│  domain knowledge       │
│  └──────────┘  └──────────┘  └──────────┘  (JSON files read       │
│                                             directly by agents)    │
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

**Option A** — Use the org default 5-block workflow:

```yaml
story_workflow:
  mode: "inherit"    # Uses KB → Discovery → Quality → Automation → Release
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
[
  {
    "id": "myproj_rule_1",
    "text": "In MyProject, the reconciliation process requires matching on 3 keys: Account, Security, and Date.",
    "category": "domain_knowledge",
    "tags": ["reconciliation", "matching"]
  }
]
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

automation:
  minimum_automation_rate: 80.0    # Stricter than org default 60%
```

---

## Agent Inventory

### Team-Level Story Agents (9 agents)

| Agent | File | Used In |
|-------|------|---------|
| Team Conductor | `conductor-agent.md` | Reads project config, runs the right workflow |
| Knowledge Base | `KnowledgeBase-agent.md` | Uses project's domain routing rules |
| Story | `story-agent.md` | Works with any Jira project key |
| Analysis | `analysis-agent.md` | Builds discovery context |
| Test Planning | `test-planning-agent.md` | Selects techniques based on story |
| Test Design | `test-design-agent.md` | Generates automation-ready test cases per project's coverage reqs |
| Test Data | `TestData-agent.md` | Generates realistic test data |
| Test Review | `test-review-agent.md` | Reviews against project's standards + automation readiness |
| Publish Jira | `publish-jira-agent.md` | Uses project's Jira field mappings |

### Organization-Level Agents (10 agents)

| Agent | File | Key Capability |
|-------|------|---------------|
| Organization Conductor | `org-conductor-agent.md` | Orchestrates cross-project workflows |
| Release Readiness | `release-readiness-agent.md` | 9-gate go/no-go, uses strictest thresholds across projects |
| Security Testing | `security-testing-agent.md` | SAST, DAST, dependency scan, secrets detection, OWASP, pentest coordination |
| Automation | `automation-agent.md` | Candidacy analysis, script generation, CI/CD integration, flaky test management |
| Cross-Team Dependency | `cross-team-dependency-agent.md` | Intra- and cross-project dependency tracking |
| Test Metrics | `test-metrics-agent.md` | Per-project and org-wide dashboards |
| Regression Impact | `regression-impact-agent.md` | Cross-project service dependency analysis |
| Defect Triage | `defect-triage-agent.md` | Auto-detects project from defect key |
| Environment Validation | `environment-validation-agent.md` | Validates per project's environment config |
| API Contract Testing | `api-contract-testing-agent.md` | Cross-project consumer impact analysis |

### Intelligent Test Execution Agents (3 agents)

| Agent | File | Key Capability |
|-------|------|---------------|
| Test Prioritization | `test-prioritization-agent.md` | Ranks tests by failure probability using historical data + code change analysis |
| Self-Healing Test | `self-healing-test-agent.md` | Detects locator/API shifts, generates patched scripts as PRs |
| Visual Regression | `visual-regression-agent.md` | Compares UI screenshots across builds, classifies changes |

### Predictive Quality Intelligence Agents (3 agents)

| Agent | File | Key Capability |
|-------|------|---------------|
| Defect Prediction | `defect-prediction-agent.md` | Risk heatmap per module using complexity, churn, and defect history |
| Release Risk Prediction | `release-risk-prediction-agent.md` | Incident probability score for upcoming releases |
| Flaky Test Prediction | `flaky-test-prediction-agent.md` | Predicts flakiness in new tests before they enter CI |

### Intelligent Test Generation Agents (3 agents)

| Agent | File | Key Capability |
|-------|------|---------------|
| Mutation Testing | `mutation-testing-agent.md` | Introduces code mutations to reveal hidden coverage gaps |
| Exploratory Testing | `exploratory-testing-agent.md` | Autonomous UI exploration with anomaly detection |
| Chaos/Resilience Testing | `chaos-resilience-agent.md` | Controlled failure injection with resilience scoring |

### Data & AI-Powered Analysis Agents (3 agents)

| Agent | File | Key Capability |
|-------|------|---------------|
| Root Cause Analysis | `root-cause-analysis-agent.md` | Correlates failures with code changes, deployments, and past patterns |
| Test Impact Analysis | `test-impact-analysis-agent.md` | Function-level code-to-test mapping, minimal test set selection |
| Log Analysis | `log-analysis-agent.md` | Monitors logs during test execution for anomalies |

### Knowledge & Learning Agents (3 agents)

| Agent | File | Key Capability |
|-------|------|---------------|
| Test Knowledge Graph | `test-knowledge-graph-agent.md` | Queryable graph connecting requirements, tests, defects, code, teams |
| QA Copilot | `qa-copilot-agent.md` | Interactive AI assistant routing queries to specialist agents |
| Lessons Learned | `lessons-learned-agent.md` | Extracts actionable lessons from sprint/release patterns |

### Performance & Specialized Testing Agents (3 agents)

| Agent | File | Key Capability |
|-------|------|---------------|
| Performance Testing | `performance-testing-agent.md` | Load/stress/soak/spike testing with SLA validation |
| Accessibility Testing | `accessibility-testing-agent.md` | WCAG 2.1/2.2 compliance scanning and remediation guidance |
| Data Quality Testing | `data-quality-testing-agent.md` | Source-to-target validation across 6 data quality dimensions |

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

Resolves participating projects → dependency analysis → environment validation → team conductors execute 5-block workflows in parallel (including automation script generation per story) → **security scanning (SAST)** → regression → metrics → readiness.

### 2. Release QA

```
@org-conductor-agent Release QA for PFPM Release 3.2
@org-conductor-agent Release QA for Q3 2026 Release [PULSE, GXNG, ALPHA]
```

Cross-project dependency scan → API contract validation → **full security assessment (SAST + dependencies + secrets + OWASP)** → **automation health check (cross-project)** → regression → metrics → go/no-go.

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

Analyzes test cases for automation ROI, generates scripts in the project's framework, and tracks automation health. For Playwright + JavaScript projects, uses the **Playwright Automation Skill** to generate production-ready code with:
- **UI tests** — Page Object Model, auto-wait, semantic locators
- **API tests** — BaseApiClient, schema validation, auth handling
- **Data comparison tests** — DataComparisonEngine, field mappings, aggregation reconciliation

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

Per-project and aggregated metrics → environment health → risk summary.

---

## Quality Gates

9 mandatory gates evaluated by the Release Readiness Agent:

| Gate | Threshold (org default) | Can override per project? |
|------|------------------------|--------------------------|
| G1: Test Execution | Pass rate ≥ 95% | Yes (stricter only) |
| G2: Critical Defects | Zero open S1 | No (org minimum) |
| G3: Regression | All P1 suites passed | No (org minimum) |
| G4: Coverage | ≥ 85% requirements | Yes (stricter only) |
| G5: API Contracts | No breaking changes | No (org minimum) |
| G6: Dependencies | No blocked deps | No (org minimum) |
| G7: Environment | Prod-like validated | No (org minimum) |
| G8: Rollback | Documented + tested | No (org minimum) |
| G9: Sign-off | All leads signed | No (org minimum) |

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
  security-testing-agent.md         # SAST, DAST, OWASP, secrets, pentest
  automation-agent.md               # Script generation, CI/CD, flaky tests
  cross-team-dependency-agent.md
  test-metrics-agent.md
  regression-impact-agent.md
  defect-triage-agent.md
  environment-validation-agent.md
  api-contract-testing-agent.md

  # Intelligent test execution agents
  test-prioritization-agent.md      # Rank tests by failure probability
  self-healing-test-agent.md        # Auto-patch broken selectors/endpoints
  visual-regression-agent.md        # Screenshot comparison across builds

  # Predictive quality intelligence agents
  defect-prediction-agent.md        # Risk heatmap per code module
  release-risk-prediction-agent.md  # Incident probability for releases
  flaky-test-prediction-agent.md    # Predict flakiness before CI

  # Intelligent test generation agents
  mutation-testing-agent.md         # Code mutations to find coverage gaps
  exploratory-testing-agent.md      # Autonomous UI exploration
  chaos-resilience-agent.md         # Controlled failure injection

  # Data & AI-powered analysis agents
  root-cause-analysis-agent.md      # Correlate failures with changes
  test-impact-analysis-agent.md     # Function-level code-to-test mapping
  log-analysis-agent.md             # Log anomaly detection during tests

  # Knowledge & learning agents
  test-knowledge-graph-agent.md     # Queryable requirement-test-defect graph
  qa-copilot-agent.md               # Interactive QA assistant
  lessons-learned-agent.md          # Sprint/release lessons extraction

  # Performance & specialized testing agents
  performance-testing-agent.md      # Load/stress/soak/spike testing
  accessibility-testing-agent.md    # WCAG compliance scanning
  data-quality-testing-agent.md     # Source-to-target data validation

  # Skills (detailed code generation blueprints used by agents)
  skills/
    playwright-automation.md        # Playwright UI + API + Data Comparison skill

knowledge_base/
  projects/
    _template/                      # Template for project knowledge
      domain_knowledge.json
    pulse/                          # PULSE-specific domain knowledge
      qa_testing.json
      qa_automation.json
      private_markets_domain.json
      jira_xray.json
```

---

## How to Use This System (Detailed Guide)

### Prerequisites

You need only two things:

1. **GitHub Copilot** — your company's AI assistant (chat or IDE integration)
2. **This repository** — cloned or accessible in your IDE (VS Code with Copilot)

No servers, no databases, no Python, no Docker. The entire system is a set of **markdown instruction files** and **JSON knowledge files** that Copilot reads and follows.

### How It Works

The agent `.md` files are **Copilot custom instructions** (also called "agent definitions" or "custom agents" depending on your Copilot setup). When you invoke an agent by name in Copilot Chat, Copilot reads the corresponding `.md` file and follows its instructions — using your Jira data, project config, and knowledge files as context.

```
You type in Copilot Chat:
    @conductor-agent Process PULSE-3730

What happens:
    1. Copilot reads conductor-agent.md
    2. conductor-agent.md tells it to extract "PULSE" from "PULSE-3730"
    3. It reads org-config.yaml to find PULSE's config_path
    4. It reads projects/pulse/project-config.yaml
    5. It determines the workflow blocks (KB → Discovery → Quality → Release)
    6. It runs each block's agents in sequence, gating on your approval
```

### Setup in VS Code with Copilot

#### Option A: GitHub Copilot Agents (if your org has Copilot Agents enabled)

Each `.md` file in `.github/agents/` is automatically available as a Copilot agent. You invoke them with `@agent-name` in Copilot Chat.

#### Option B: Copilot Chat with file references

If your org uses standard Copilot Chat without custom agents, you reference the instruction files manually:

```
# In Copilot Chat, attach the agent file as context:
@workspace /explain #file:.github/agents/conductor-agent.md

Then type your prompt:
"Follow the instructions in the attached conductor-agent.md file. Process story PULSE-3730."
```

#### Option C: Copilot Custom Instructions (`.github/copilot-instructions.md`)

Create a `.github/copilot-instructions.md` file that points Copilot to the agent system:

```markdown
When I mention an agent by name (e.g., "conductor-agent", "story-agent"),
read the corresponding file from .github/agents/<agent-name>.md and follow
its instructions precisely.

Always resolve the project from the Jira key prefix using org-config.yaml.
Always read the project's project-config.yaml before taking action.
```

---

### Day-to-Day Usage: Common Scenarios

#### Scenario 1: Process a Jira Story (Team-Level)

This is the most common operation. It runs the full test case lifecycle for a single story.

```
@conductor-agent Process PULSE-3730
```

**What happens step by step:**

1. **Knowledge Base block** — The KB Agent fetches the story from Jira, collects domain knowledge from `knowledge_base/projects/pulse/`, and creates `PFPT/PULSE-3730_knowledge_base.md`
2. Copilot asks you for the gate token: `KB_APPROVED`
3. **Discovery block** — Analysis Agent and Test Planning Agent analyze the story, select testing techniques, and produce `runs/PULSE-3730/discovery_context.json`
4. You approve: `DISCOVERY_APPROVED`
5. **Quality block** — Test Design Agent generates automation-ready test cases (with locator hints, parameterized data, machine-verifiable assertions), Test Data Agent creates data, Test Review Agent reviews. Output: `runs/PULSE-3730/quality_pack.json` and `runs/PULSE-3730/PULSE-3730_testcases.csv`
6. You approve: `QUALITY_APPROVED`
7. **Automation block** — Automation Agent scores every test case for automation candidacy, generates Playwright scripts for high-scoring candidates, and produces the candidacy report + scripts. Output: `runs/PULSE-3730/automation_candidacy.json`, `runs/PULSE-3730/automation_scripts/`, `runs/PULSE-3730/automation_map.json`
8. You approve: `AUTOMATION_APPROVED`
9. **Release block** — Publish Jira Agent creates test cases in Jira, links them to the story with "is tested by", and produces `runs/PULSE-3730/publish_report.json`
10. You approve: `APPROVE_FOR_JIRA`

**Files created during this flow:**

```
PFPT/PULSE-3730_knowledge_base.md          # Domain knowledge document
runs/PULSE-3730/discovery_context.json      # Analysis + test techniques
runs/PULSE-3730/quality_pack.json           # All test cases (structured JSON with automation hints)
runs/PULSE-3730/PULSE-3730_testcases.csv    # Test cases in Jira CSV format
runs/PULSE-3730/review_pack.md              # Review feedback
runs/PULSE-3730/automation_candidacy.json   # Candidacy scores for every test case
runs/PULSE-3730/automation_scripts/         # Generated Playwright test scripts
  ui/                                       #   UI test scripts
  api/                                      #   API test scripts
  data/                                     #   Data comparison test scripts
runs/PULSE-3730/automation_map.json         # Test case ID → script path mapping
runs/PULSE-3730/publish_report.json         # Jira publishing results
runs/PULSE-3730/agent_bus.jsonl             # Communication log between agents
runs/PULSE-3730/status_dashboard.md         # Visual status of each block
```

#### Scenario 2: Sprint Coordination (Org-Level)

Coordinate QA across teams and projects for a sprint.

```
@org-conductor-agent Sprint coordination for PFPT Sprint 24
```

This triggers a sequence of org-level agents:
1. Cross-Team Dependency Agent checks for blockers between teams
2. Environment Validation Agent verifies QA environments
3. Team Conductors process stories in parallel (each running the 5-block workflow including automation)
4. Security Testing Agent runs SAST scan on sprint code changes
5. Regression Impact Agent scopes cross-team regression
6. Test Metrics Agent produces a sprint dashboard (includes automation coverage)
7. Release Readiness Agent evaluates 9 quality gates

#### Scenario 3: Release Go/No-Go (Org-Level)

Before a release, get a formal assessment.

```
@org-conductor-agent Release QA for PFPM Release 3.2
```

Or for a multi-project release:

```
@org-conductor-agent Release QA for Q3 2026 Release [PULSE, GXNG, ALPHA]
```

The Release Readiness Agent evaluates all 9 gates and produces a GO / NO_GO / CONDITIONAL_GO recommendation with evidence for each gate.

#### Scenario 4: Generate Automation Scripts (Standalone)

Automation scripts are generated automatically as part of every story workflow (the Automation block). But you can also invoke the Automation Agent directly for existing test cases:

```
@automation-agent Generate scripts for PULSE-3730
```

The Automation Agent reads `quality_pack.json`, loads the Playwright Automation Skill (`.github/agents/skills/playwright-automation.md`), and generates:
- Page Object classes (`src/pages/`)
- API client classes (`src/api/`)
- Test files (`tests/ui/`, `tests/api/`, `tests/data/`)
- Fixtures and test data (`src/fixtures/`)
- CI/CD pipeline config (`.github/workflows/`)

All generated code is JavaScript with Playwright.

#### Scenario 5: Defect Triage

When a critical defect is found:

```
@org-conductor-agent Defect escalation for PULSE-4521
```

The system auto-detects the project from the key, triages severity, analyzes cross-project impact, notifies affected teams, and updates release readiness.

#### Scenario 6: Security Scan

```
@security-testing-agent Full security assessment for project PULSE
```

Runs SAST, dependency scanning, secrets detection, and OWASP compliance checks. Critical findings are flagged as release blockers.

#### Scenario 7: Quality Assessment (On-Demand)

```
@org-conductor-agent Quality assessment for all projects
```

Produces an executive dashboard with per-project metrics, environment health, and overall risk posture.

---

### Using Individual Agents Directly

You don't always need the full workflow. Each agent can be invoked independently:

| What you want to do | Command |
|---------------------|---------|
| Fetch story details from Jira | `@story-agent PULSE-3730` |
| Build knowledge base for a story | `@KnowledgeBase-agent PULSE-3730` |
| Analyze a story for testing approach | `@analysis-agent Analyze PULSE-3730` |
| Select testing techniques | `@test-planning-agent Plan for PULSE-3730` |
| Generate test cases | `@test-design-agent Generate for PULSE-3730` |
| Generate test data | `@TestData-agent Generate data for PULSE-3730` |
| Review test cases | `@test-review-agent Review PULSE-3730` |
| Publish to Jira | `@publish-jira-agent Publish PULSE-3730` (requires `APPROVE_FOR_JIRA`) |
| Check automation candidacy | `@automation-agent Analyze PULSE-3730 for automation candidacy` |
| Run automation health check | `@automation-agent Health check for project PULSE` |
| Find flaky tests | `@automation-agent Flaky test analysis for project PULSE` |
| Check dependencies | `@cross-team-dependency-agent Check dependencies for PFPT Sprint 24` |
| Validate environment | `@environment-validation-agent Validate PULSE QA environment` |
| Get test metrics | `@test-metrics-agent Dashboard for project PULSE` |
| Check regression impact | `@regression-impact-agent Analyze impact of PULSE-4521` |
| Triage a defect | `@defect-triage-agent Triage PULSE-4521` |
| Validate API contracts | `@api-contract-testing-agent Check contracts for PULSE` |
| Prioritize tests for CI | `@test-prioritization-agent Prioritize tests for PULSE sprint scope` |
| Diagnose broken tests | `@self-healing-test-agent Diagnose failures in PULSE UI suite` |
| Compare UI screenshots | `@visual-regression-agent Compare build 4.2 against baseline for PULSE` |
| Predict defect-prone modules | `@defect-prediction-agent Predict risks for PULSE current sprint` |
| Predict release incidents | `@release-risk-prediction-agent Predict risk for PFPM Release 3.2` |
| Scan new tests for flakiness | `@flaky-test-prediction-agent Scan PR #142 for flakiness risk` |
| Run mutation testing | `@mutation-testing-agent Mutate src/services/position-calculator for PULSE` |
| Run exploratory testing | `@exploratory-testing-agent Explore /dashboard for PULSE` |
| Test resilience | `@chaos-resilience-agent Test fund-valuation-service resilience for PULSE` |
| Find root cause of failure | `@root-cause-analysis-agent Analyze failures in pipeline run #4521` |
| Get minimal test set | `@test-impact-analysis-agent Analyze impact of PR #142 for PULSE` |
| Analyze test logs | `@log-analysis-agent Analyze logs from PULSE QA environment last 24h` |
| Query knowledge graph | `@test-knowledge-graph-agent Which requirements have no test coverage?` |
| Ask QA questions | `@qa-copilot-agent What testing techniques for currency conversion?` |
| Extract lessons learned | `@lessons-learned-agent Extract lessons from PFPT Sprint 24` |
| Run performance tests | `@performance-testing-agent Load test /api/positions for PULSE` |
| Check accessibility | `@accessibility-testing-agent Scan /dashboard for WCAG AA for PULSE` |
| Validate data quality | `@data-quality-testing-agent Validate fund-positions pipeline for PULSE` |

---

### The Gate System (Human-in-the-Loop)

Every workflow block requires your explicit approval before the next block starts. This is the "gate" system:

```
Conductor: "Knowledge Base block complete. Files created:
  - PFPT/PULSE-3730_knowledge_base.md
  Please provide gate token: KB_APPROVED"

You: "KB_APPROVED"

Conductor: "Starting Discovery block..."
```

**You control the pace.** No test cases get published to Jira without your explicit `APPROVE_FOR_JIRA` token. You can review, ask questions, request changes, or reject at any gate.

Gate tokens for the default 5-block workflow:
1. `KB_APPROVED` — after knowledge base is built
2. `DISCOVERY_APPROVED` — after analysis and test planning
3. `QUALITY_APPROVED` — after test case design, data, and review
4. `AUTOMATION_APPROVED` — after candidacy analysis and script generation
5. `APPROVE_FOR_JIRA` — before publishing to Jira

---

### Customizing for Your Team

#### Add a new project

Follow the 6-step onboarding guide in the "How to Onboard a New Project" section above.

#### Change a project's workflow

Edit the project's `project-config.yaml` — change the `story_workflow` section. You can add/remove blocks, change which agents run in each block, and set different gate tokens.

#### Add domain knowledge

Drop JSON files into `knowledge_base/projects/<your-project-id>/`. The Knowledge Base Agent reads them for domain context. No setup command needed — just add the files.

#### Make quality gates stricter

Add overrides in your project config:

```yaml
quality_gates_overrides:
  G1_test_execution:
    pass_rate_threshold: 99.0
  G4_coverage:
    requirements_coverage_threshold: 95.0
```

#### Use a different automation framework

Update your project config:

```yaml
automation:
  framework: "Cypress"
  language: "JavaScript"
```

The Automation Agent will adapt. The Playwright Automation Skill only activates when `framework: "Playwright"` and `language: "JavaScript"`.

---

### What You Need vs What You Don't

| You need | You do NOT need |
|----------|----------------|
| VS Code with Copilot | Ollama or any local LLM |
| Access to your Jira instance | ChromaDB or any vector database |
| This repository cloned locally | Python, pip, or any Python packages |
| Node.js (only for running Playwright tests) | Docker (unless your CI requires it) |
| | GPU or fine-tuning infrastructure |

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
