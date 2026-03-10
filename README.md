# Pharma QA Agents - Terminal CLI System

A command-line AI agent system for pharmaceutical quality assurance work using local LLMs via Ollama.

## 🎯 Features

- **9 Specialized AI Agents** for GxP compliance, validation, CAPA, risk assessment, and documentation
- **Terminal-based** - No GUI needed, works via command line
- **100% Local** - Uses Ollama, your data never leaves your Mac
- **GitHub-backed** - Version control for prompts and workflows
- **Workflow Automation** - Chain agents together for complex tasks
- **Document Integration** - Reference your PDFs (EudraLex, FDA, ISO) in queries

## 🚀 Quick Start

### Prerequisites

- macOS (tested on M4 MacBook Air)
- Ollama installed and running
- Python 3.9+ 
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/pharma-qa-agents.git
cd pharma-qa-agents

# Run installation script
chmod +x install.sh
./install.sh

# Verify installation
python scripts/agent.py --list
```

## 📚 Available Agents

1. **orchestrator** - Routes queries to appropriate agents
2. **quality** - Quality & Regulatory Sentinel (GMP compliance)
3. **lean** - Lean Production Optimizer (root cause, waste)
4. **project** - Project Architect (PRINCE2, timelines)
5. **validation** - Validation Specialist (IQ/OQ/PQ, GAMP 5)
6. **risk** - Risk Assessment Specialist (FMEA, ICH Q9)
7. **audit** - Audit & Inspection Readiness
8. **document** - Document Production Specialist (SOPs, CAPAs)
9. **analytical** - Analytical Method Writer (HPLC, GC, validation)

## 💻 Usage Examples

### Basic Query

```bash
# Ask the orchestrator to route your query
python scripts/agent.py orchestrator "New deviation: Batch failed dissolution test"

# Direct query to specific agent
python scripts/agent.py quality "Assess criticality of temperature excursion: 12°C for 45 minutes"

# Get root cause analysis
python scripts/agent.py lean "5 Whys analysis for tablet press failure"
```

### Interactive Mode

```bash
# Start conversation with an agent
python scripts/agent.py quality --interactive

# In interactive mode:
> What regulatory citations apply to cleaning validation?
> [Agent responds]
> How often must cleaning be revalidated?
> [Agent responds]
> exit
```

### With Document Context

```bash
# Reference a PDF document in your knowledge/ folder
python scripts/agent.py quality \
  --context knowledge/EudraLex-Vol4-Part1.pdf \
  "What does Annex 15 say about OOS investigations?"

# Multiple documents
python scripts/agent.py validation \
  --context knowledge/GAMP5.pdf,knowledge/FDA-Process-Validation.pdf \
  "Design IQ/OQ/PQ for tablet press"
```

### Save Output

```bash
# Save agent response to file
python scripts/agent.py document \
  "Create CAPA form for dissolution failure" \
  --output outputs/CAPA-2024-0892.md

# Generate multiple formats
python scripts/agent.py document \
  "Write SOP for tablet compression" \
  --output outputs/SOP-PROD-012 \
  --format markdown,docx
```

### Workflow Automation

```bash
# Run complete CAPA workflow (all agents in sequence)
python scripts/workflow.py capa-workflow \
  --input "Batch 2024-0892 failed dissolution test, 68% at 30 min (spec: ≥80%)" \
  --output outputs/CAPA-2024-0892/

# Creates:
# - quality-assessment.md
# - lean-analysis.md  
# - project-plan.md
# - investigation-report.docx
# - capa-form.docx
```

## 🔧 Configuration

Edit `config.yaml` to customize:

```yaml
ollama:
  base_url: "http://127.0.0.1:11434"
  model: "qwen2.5:14b"  # Default model
  temperature: 0.3       # Lower = more consistent
  
agents:
  quality:
    model: "qwen2.5:14b"
  lean:
    model: "deepseek-r1:14b"  # Better reasoning
  # ... customize per agent

output:
  default_format: "markdown"
  save_history: true
  history_dir: "outputs/history"
```

## 📋 Workflow Templates

### CAPA Workflow

```bash
python scripts/workflow.py run workflows/capa-workflow.yaml \
  --var deviation="Batch failed test" \
  --var batch="2024-0892"
```

Executes:
1. Quality Sentinel → Criticality assessment
2. Lean Optimizer → Root cause (5 Whys)
3. Project Architect → CAPA timeline
4. Document Production → Investigation report + CAPA form

### Validation Protocol Creation

```bash
python scripts/workflow.py run workflows/validation-workflow.yaml \
  --var equipment="HPLC Agilent 1260" \
  --var type="IQ/OQ/PQ"
```

### SOP Creation

```bash
python scripts/workflow.py run workflows/sop-creation-workflow.yaml \
  --var title="Tablet Compression Operations" \
  --var process="compression"
```

## 📁 Adding Your Documents

Place your regulatory PDFs in `knowledge/`:

```bash
knowledge/
├── EudraLex-Vol4-Part1.pdf
├── EudraLex-Annex15.pdf
├── FDA-21CFR211.pdf
├── ICH-Q10.pdf
├── Company-Quality-Manual.pdf
└── SOP-Templates/
```

**Note:** PDFs are NOT committed to GitHub (in .gitignore). 
Store them locally only.

## 🔒 Privacy & Security

- ✅ **100% Local**: All processing via Ollama on your Mac
- ✅ **No Cloud**: Data never sent to external APIs
- ✅ **Git-Ignored**: PDFs and outputs excluded from commits
- ✅ **HIPAA-Safe**: No patient data leaves your device

**Safe to use with:**
- Confidential company documents
- GMP deviation reports  
- Internal audit findings
- Proprietary formulations

**Do NOT commit to GitHub:**
- Company-specific PDFs
- Batch records with product data
- Any files in `knowledge/` or `outputs/`

## 🛠️ Advanced Usage

### Custom Agent Prompts

Edit prompt files in `prompts/`:

```bash
# Modify the quality agent
nano prompts/02-quality-sentinel.txt

# Test changes
python scripts/agent.py quality "Test query" --reload-prompts
```

### Chain Agents Manually

```bash
# Step 1: Quality assessment
python scripts/agent.py quality "Deviation X" > step1.txt

# Step 2: Use quality output in lean analysis  
cat step1.txt | python scripts/agent.py lean --stdin

# Step 3: Continue chain
...
```

### Batch Processing

```bash
# Process multiple deviations from CSV
python scripts/agent.py quality \
  --batch deviations.csv \
  --output-dir outputs/batch-2024-03/
```

## 🐛 Troubleshooting

### Agent not responding

```bash
# Check Ollama is running
ollama list

# If not running:
ollama serve

# Test connection
curl http://127.0.0.1:11434/api/tags
```

### Out of memory (16GB Mac)

```bash
# Use smaller model in config.yaml
model: "qwen2.5:7b"  # Instead of 14b

# Or close other apps and retry
```

### PDF not being referenced

```bash
# Verify PDF is in knowledge/ folder
ls -lh knowledge/

# Try absolute path
python scripts/agent.py quality \
  --context /Users/yourname/pharma-qa-agents/knowledge/EudraLex.pdf \
  "Query here"
```

## 📖 Documentation

- [Agent Prompts Reference](docs/agent-prompts.md)
- [Workflow Creation Guide](docs/workflows.md)
- [Integration with Other Tools](docs/integrations.md)
- [Examples Library](docs/examples.md)

## 🤝 Contributing

This is a personal repository, but improvements are welcome:

1. Fork the repo
2. Create feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add improvement'`)
4. Push to branch (`git push origin feature/improvement`)
5. Create Pull Request

## 📄 License

MIT License - Free to use for personal and commercial pharma QA work.

## 🙏 Acknowledgments

- Anthropic Claude for prompt engineering guidance
- Ollama team for local LLM infrastructure
- Pharmaceutical Quality community

## 📞 Support

Issues: https://github.com/YOUR_USERNAME/pharma-qa-agents/issues

---

**Built with ❤️ for pharmaceutical quality professionals**
