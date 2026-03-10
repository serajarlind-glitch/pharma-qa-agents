# Setup Guide - Pharma QA Agents

## Quick Setup (5 Steps)

### 1. Clone or Download Repository

```bash
# If on GitHub:
git clone https://github.com/YOUR_USERNAME/pharma-qa-agents.git
cd pharma-qa-agents

# Or download ZIP and extract
```

### 2. Add Complete Agent Prompts

The `prompts/` folder contains placeholder files. You need to replace them with the complete system prompts from your conversation.

**Files to update:**

```
prompts/
├── 01-orchestrator.txt ✅ (Already complete)
├── 02-quality-sentinel.txt ⚠️ (REPLACE with full prompt)
├── 03-lean-optimizer.txt ⚠️ (REPLACE with full prompt)
├── 04-project-architect.txt ⚠️ (REPLACE with full prompt)
├── 05-validation-specialist.txt ⚠️ (REPLACE with full prompt)
├── 06-risk-assessment.txt ⚠️ (REPLACE with full prompt)
├── 07-audit-readiness.txt ⚠️ (REPLACE with full prompt)
├── 08-document-production.txt ⚠️ (REPLACE with full prompt)
└── 09-analytical-method.txt ⚠️ (REPLACE with full prompt)
```

**How to add prompts:**

```bash
# Edit each file
nano prompts/02-quality-sentinel.txt

# Paste the complete prompt, save and exit (Ctrl+O, Ctrl+X)
```

**Where to find the prompts:**
Go back through this conversation and find each agent's complete system prompt. 
Copy the entire prompt text (everything between the ``` markers) and paste 
it into the corresponding file.

### 3. Run Installation Script

```bash
chmod +x install.sh
./install.sh
```

This will:
- Check Python and Ollama are installed
- Install required Python packages (requests, pyyaml)
- Download the AI model (qwen2.5:14b) if you confirm
- Create necessary directories
- Set up command shortcuts (optional)

### 4. Add Your Documents

Place your regulatory PDFs in the `knowledge/` folder:

```bash
knowledge/
├── EudraLex-Vol4-Part1.pdf
├── EudraLex-Annex15.pdf
├── FDA-21CFR211.pdf
├── ICH-Q10.pdf
├── ICH-Q9.pdf
└── Company-Documents/
    ├── Quality-Manual.pdf
    └── SOP-Templates/
```

**Where to download these:**
See the "Where to Find Regulatory PDFs" guide earlier in this conversation.

### 5. Test the System

```bash
# List agents
python scripts/agent.py --list

# Test a query
python scripts/agent.py orchestrator "I have a deviation to report"

# Try interactive mode
python scripts/agent.py quality --interactive
```

---

## Detailed Setup Instructions

### Prerequisites Installation

**Install Homebrew (if not installed):**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Install Ollama:**
```bash
brew install ollama
```

**Start Ollama:**
```bash
ollama serve
```
Keep this terminal window open.

**Install Python packages:**
```bash
pip3 install requests pyyaml
```

### Configuration Customization

Edit `config.yaml` if you want to:

**Use smaller model (for 16GB RAM):**
```yaml
ollama:
  model: "qwen2.5:7b"  # Changed from 14b
```

**Use different model for specific agent:**
```yaml
agents:
  lean:
    model: "deepseek-r1:14b"  # Better reasoning
```

**Adjust temperature:**
```yaml
ollama:
  temperature: 0.1  # More deterministic (default: 0.3)
```

### Prompt Customization

You can customize prompts for your company:

1. Edit prompt file: `nano prompts/08-document-production.txt`
2. Add company-specific sections:
   ```
   Company Standards:
   - Use XYZ SOP template format
   - Include approval chain: Author → QA → QA Director
   - Reference internal procedures: PROC-XXX
   ```
3. Save and test:
   ```bash
   python scripts/agent.py document "Create SOP" --reload-prompts
   ```

### Creating Custom Workflows

Create a new workflow file in `workflows/`:

```yaml
# workflows/my-custom-workflow.yaml

name: "My Custom Workflow"
description: "Description of what this workflow does"

steps:
  - name: "Step 1"
    agent: "quality"
    prompt: |
      Analyze this: ${input}
    save_as: "step1-output.md"
  
  - name: "Step 2"
    agent: "document"
    use_previous_output: true
    prompt: |
      Create report based on above analysis
    save_as: "final-report.md"
```

Run it:
```bash
python scripts/workflow.py my-custom-workflow --var input="Your input here"
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'yaml'"
```bash
pip3 install pyyaml
```

### "Cannot connect to Ollama"
```bash
# Check if Ollama is running
curl http://127.0.0.1:11434/api/tags

# If not, start it
ollama serve
```

### "Model not found"
```bash
# Download the model
ollama pull qwen2.5:14b

# Or smaller version
ollama pull qwen2.5:7b
```

### Agent gives generic responses (not using prompt)
- Check that you replaced the placeholder in `prompts/` with the full prompt
- Verify prompt file has content:
  ```bash
  wc -l prompts/02-quality-sentinel.txt
  # Should show 40+ lines, not just 10 lines of placeholder text
  ```

### PDF context not working
- Currently, the system shows PDF filenames as context but doesn't extract text
- Full PDF extraction requires additional libraries (PyPDF2, pdfplumber)
- For now, reference PDFs by describing their content in your query

---

## Next Steps

1. **Test each agent individually:**
   ```bash
   python scripts/agent.py quality "Test query"
   python scripts/agent.py lean "Test query"
   # etc.
   ```

2. **Run your first workflow:**
   ```bash
   python scripts/workflow.py capa-workflow \
     --var deviation="Temperature excursion" \
     --var batch="2024-0123" \
     --var product="Aspirin tablets"
   ```

3. **Create custom shortcuts:**
   ```bash
   # Add to ~/.zshrc:
   alias qa-agent="python ~/pharma-qa-agents/scripts/agent.py"
   alias qa-workflow="python ~/pharma-qa-agents/scripts/workflow.py"
   
   # Then use:
   qa-agent quality "My query"
   ```

4. **Explore advanced features:**
   - Interactive mode with conversation history
   - Batch processing multiple queries
   - Custom workflow creation
   - Prompt fine-tuning for your company

---

## Getting Help

- **Check prompt files:** Make sure you've replaced ALL placeholders
- **Review configuration:** Verify `config.yaml` has correct model names
- **Test Ollama:** `ollama run qwen2.5:14b "Hello"`
- **Read error messages:** They usually indicate the exact problem

---

Happy automating! 🚀
