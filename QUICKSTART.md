# Quick Start (5 Minutes)

## 1. Install (One Time)
```bash
cd pharma-qa-agents
chmod +x install.sh
./install.sh
```

## 2. Add Prompts (One Time)
Copy the full prompts from your conversation into each file in `prompts/`:
- `prompts/02-quality-sentinel.txt` ← Quality Sentinel prompt
- `prompts/03-lean-optimizer.txt` ← Lean Optimizer prompt  
- `prompts/04-project-architect.txt` ← Project Architect prompt
- `prompts/05-validation-specialist.txt` ← Validation Specialist prompt
- `prompts/06-risk-assessment.txt` ← Risk Assessment prompt
- `prompts/07-audit-readiness.txt` ← Audit Readiness prompt
- `prompts/08-document-production.txt` ← Document Production prompt
- `prompts/09-analytical-method.txt` ← Analytical Method prompt

## 3. Test
```bash
# List agents
python scripts/agent.py --list

# Try first query
python scripts/agent.py orchestrator "I have a deviation to report"
```

## 4. Daily Use

```bash
# Basic query
python scripts/agent.py quality "Temperature excursion 12°C for 30 minutes"

# Interactive mode
python scripts/agent.py lean --interactive

# Full workflow
python scripts/workflow.py capa-workflow \
  --var deviation="Batch failed dissolution" \
  --var batch="2024-0892" \
  --var product="Aspirin tablets"
```

## 5. Push to GitHub (Optional)

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/pharma-qa-agents.git
git push -u origin main
```

---

**That's it!** See README.md for full documentation.

**Important:** Make sure Ollama is running before using agents:
```bash
# In a separate terminal, keep this running:
ollama serve
```
