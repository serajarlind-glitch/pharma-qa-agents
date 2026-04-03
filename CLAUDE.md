# Pharma QA Agents — Claude Code Integration

## What This Is
A team of 9 specialized AI agents for pharmaceutical quality assurance, powered by Claude API.
Upgraded from a legacy Ollama-based CLI to a Claude-native multi-agent system with precision layers.

## Agent Team

| Role | Agent Name | Specialty |
|------|-----------|-----------|
| `orchestrator` | Workflow Orchestrator | Routes queries to the right specialist(s) |
| `quality` | Quality & Regulatory Sentinel | FDA/EMA/ICH compliance, deviations, OOS, change control |
| `lean` | Lean Production Optimizer | Root cause (5 Whys, Ishikawa), DMAIC, process optimization |
| `project` | Project Architect | PRINCE2 project plans, timelines, resource allocation |
| `validation` | Validation Specialist | IQ/OQ/PQ, CSV, GAMP 5, cleaning validation |
| `risk` | Risk Assessment Specialist | FMEA, ICH Q9, risk matrices, hazard analysis |
| `audit` | Audit & Inspection Readiness | FDA/EMA inspection prep, gap analysis, 483 responses |
| `document` | Document Production Specialist | SOPs, CAPA forms, protocols, investigation reports |
| `analytical` | Analytical Method Writer | HPLC, dissolution, method validation, ICH Q2 |

## Precision Layers (99.99% Target)

### 1. QA Reviewer Agent (`reviewer.py`)
Cross-validates every agent output. Scores on 4 axes:
- **Citation Accuracy** (1-10): Are regulatory references real and correctly numbered?
- **Completeness** (1-10): Are all required deliverables present?
- **Compliance** (1-10): Does output meet GMP documentation standards?
- **Consistency** (1-10): No internal contradictions?

Quality gate decisions: Pass / Pass with Comments / Revise / Reject.
If review fails, the agent auto-revises with specific feedback.

### 2. Structured Output Schemas (`schemas.py`)
Every agent response includes mandatory JSON metadata:
- Severity classification (Critical/Major/Minor)
- Confidence level (High/Medium/Low) with basis
- GxP impact categories
- Regulatory references with authority
- Action items with owners, deadlines, verification methods
- Assumptions and limitations declared

### 3. Regulatory Standards Database (`standards.py`)
Embedded reference index for 18+ regulations:
- FDA 21 CFR Parts 11, 210, 211
- EU GMP Parts I, Annexes 1, 11, 15
- ICH Q1A, Q2, Q3C, Q7, Q8, Q9, Q10, Q12
- GAMP 5, ALCOA+ Data Integrity
- USP General Chapters

Auto-injected into agent context based on topic.

### 4. ALCOA+ Audit Trail (`audit_trail.py`)
Full GxP traceability for every agent interaction:
- SHA-256 hash of every output (tamper detection)
- Timestamps (UTC), agent attribution, model used
- Review scores and gate decisions
- Append-only JSONL log files

### 5. Precision Prompt Standards
Every agent prompt includes mandatory rules:
- Citation accuracy (never fabricate section numbers)
- Confidence declaration for each conclusion
- Assumptions & limitations disclosure
- Controlled vocabulary (shall/should/may/must)
- Anti-hallucination: "I don't have sufficient information" > guess
- Human review flag for safety-critical decisions

## Running Modes

### Standard Mode (fast, single-pass):
```python
from pharma_agents import run_workflow
result = run_workflow("capa", variables={
    "deviation": "Batch 2024-0892 failed dissolution, 68% at 30 min (spec >=80%)",
    "batch": "2024-0892",
    "product": "Aspirin 500mg tablets",
})
```

### Precision Mode (full quality layers):
```python
from pharma_agents import run_workflow
from pathlib import Path

result = run_workflow(
    "capa",
    variables={
        "deviation": "Batch 2024-0892 failed dissolution, 68% at 30 min (spec >=80%)",
        "batch": "2024-0892",
        "product": "Aspirin 500mg tablets",
    },
    enable_review=True,              # QA reviewer cross-validation
    enable_structured_output=True,   # Mandatory JSON metadata
    enable_audit_trail=True,         # ALCOA+ traceability
    enable_regulatory_context=True,  # Auto-inject regulatory references
    audit_log_dir=Path("outputs/audit"),
)
print(result.summary())              # Step table with review scores
print(result.audit_trail_summary)    # Full ALCOA+ audit trail
print(result.final_output)           # Final document
```

### CLI:
```bash
# Standard mode
python run.py workflow capa --var deviation="Dissolution failure" --var batch="2024-0892" --var product="Aspirin"

# Precision mode
python run.py workflow capa --precision --var deviation="Dissolution failure" --var batch="2024-0892" --var product="Aspirin" -o outputs/capa-report.md
```

## Predefined Workflows

| Workflow | Agents Used | Steps | Key Variables |
|----------|------------|-------|---------------|
| `capa` | quality, lean, risk, project, document | 4 (incl. parallel) | deviation, batch, product |
| `validation` | validation, risk, analytical, document | 4 | equipment, validation_type, process |
| `audit` | audit, quality, risk, project, document | 4 (incl. parallel) | audit_type, scope, timeline |
| `sop` | quality, lean, document | 3 | title, process, department |
| `oos` | analytical, quality, lean, risk, document | 4 (incl. parallel) | test_result, specification, method, batch, product |

## Project Structure
```
pharma_agents/              # Core package
  __init__.py               # Public API
  agent.py                  # PharmaAgent class (Claude API)
  prompts.py                # System prompts + precision preamble for all 9 agents
  team.py                   # AgentTeam orchestration with quality gates
  workflows.py              # 5 predefined workflow factories
  reviewer.py               # QA Reviewer agent (cross-validation)
  schemas.py                # Structured output schemas + extraction
  standards.py              # Regulatory reference database (18+ regulations)
  audit_trail.py            # ALCOA+ audit trail system
run.py                      # CLI entry point
requirements.txt            # anthropic SDK dependency
```

## Dependencies
- `anthropic` Python SDK (requires ANTHROPIC_API_KEY env var)
- `pyyaml` (for legacy config compat)
- Python 3.10+

## Legacy Files
The original Ollama-based files (`agent.py`, `workflow.py`, `config.yaml`) are preserved
in the repo root for reference but are superseded by the `pharma_agents/` package.
