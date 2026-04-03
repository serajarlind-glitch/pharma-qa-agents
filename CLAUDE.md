# Pharma QA Agents — Claude Code Integration

## What This Is
A team of 9 specialized AI agents for pharmaceutical quality assurance, powered by Claude API.
Upgraded from a legacy Ollama-based CLI to a proper Claude-native multi-agent system.

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

## Predefined Workflows

### CAPA Investigation (`capa`)
Full deviation-to-resolution pipeline:
1. Quality → deviation classification
2. Lean + Risk (parallel) → root cause + risk assessment
3. Project → CAPA action plan
4. Document → investigation report

Variables: `deviation`, `batch`, `product`

### Validation Protocol (`validation`)
1. Validation → strategy & protocol design
2. Risk → scope assessment
3. Analytical → test method requirements
4. Document → complete protocol

Variables: `equipment`, `validation_type`, `process`

### Audit Readiness (`audit`)
1. Audit → gap analysis
2. Quality + Risk (parallel) → compliance & risk check
3. Project → remediation plan
4. Document → readiness pack

Variables: `audit_type`, `scope`, `timeline`

### SOP Creation (`sop`)
1. Quality → regulatory framework
2. Lean → process optimization
3. Document → complete SOP

Variables: `title`, `process`, `department`

### OOS Investigation (`oos`)
1. Analytical → Phase I lab investigation
2. Quality → OOS classification
3. Lean + Risk (parallel) → root cause + impact
4. Document → investigation report

Variables: `test_result`, `specification`, `method`, `batch`, `product`

## How to Use in Claude Code

### Single agent query (Python):
```python
from pharma_agents import PharmaAgent
agent = PharmaAgent("quality")
response = agent.query("Assess criticality of temperature excursion: 12°C for 45 minutes")
```

### Run a workflow (Python):
```python
from pharma_agents import run_workflow
result = run_workflow("capa", variables={
    "deviation": "Batch 2024-0892 failed dissolution test, 68% at 30 min (spec ≥80%)",
    "batch": "2024-0892",
    "product": "Aspirin 500mg tablets",
})
print(result.final_output)
```

### CLI:
```bash
# Single agent
python run.py agent quality "Assess temperature excursion"

# Workflow
python run.py workflow capa --var deviation="Dissolution failure" --var batch="2024-0892" --var product="Aspirin 500mg"
```

## Project Structure
```
pharma_agents/          # Core package
  __init__.py           # Public API
  agent.py              # PharmaAgent class (Claude API)
  prompts.py            # System prompts for all 9 agents
  team.py               # AgentTeam orchestration (parallel/sequential/synthesis)
  workflows.py          # Predefined workflow factories
run.py                  # CLI entry point
requirements.txt        # anthropic SDK dependency
```

## Dependencies
- `anthropic` Python SDK (requires ANTHROPIC_API_KEY env var)
- Python 3.10+

## Legacy Files
The original Ollama-based files (`agent.py`, `workflow.py`, `config.yaml`) are preserved
in the repo root for reference but are superseded by the `pharma_agents/` package.
