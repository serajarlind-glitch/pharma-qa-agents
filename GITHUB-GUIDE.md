# GitHub Setup & Terminal Usage Guide

## 🚀 Step-by-Step: Push to GitHub

### Step 1: Create GitHub Repository

1. Go to https://github.com
2. Click the **+** button (top right) → **New repository**
3. Fill in:
   - **Repository name:** `pharma-qa-agents`
   - **Description:** "AI agents for pharmaceutical quality assurance using local LLMs"
   - **Visibility:** 
     - ✅ **Private** (recommended - contains your work processes)
     - OR Public (if you want to share with community)
   - **DON'T** initialize with README (we already have one)
4. Click **Create repository**

### Step 2: Prepare Local Repository

On your Mac, open Terminal and navigate to the pharma-qa-agents folder:

```bash
# Navigate to the project folder
cd ~/Downloads/pharma-qa-agents  # Or wherever you saved it

# Initialize git repository
git init

# Add all files
git add .

# Check what will be committed (should NOT include knowledge/ or outputs/)
git status

# If you see knowledge/ or outputs/ in the list:
# Make sure .gitignore is present and correct
cat .gitignore

# Commit the files
git commit -m "Initial commit: Pharma QA Agents system"
```

### Step 3: Connect to GitHub

GitHub will show you commands after creating the repo. Use these:

```bash
# Connect to your GitHub repository (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/pharma-qa-agents.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**If you get authentication error:**

GitHub no longer accepts passwords. You need a Personal Access Token:

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name: "pharma-qa-agents"
4. Select scopes: ✅ repo (all)
5. Generate token → **COPY IT NOW** (you won't see it again)
6. When git asks for password, paste the token instead

**Alternative (easier): Use GitHub CLI:**

```bash
# Install GitHub CLI
brew install gh

# Authenticate
gh auth login

# Push
git push -u origin main
```

### Step 4: Verify Upload

Go to your GitHub repository page:
`https://github.com/YOUR_USERNAME/pharma-qa-agents`

You should see:
- ✅ README.md
- ✅ scripts/
- ✅ prompts/
- ✅ workflows/
- ✅ config.yaml
- ❌ NO knowledge/ (protected by .gitignore)
- ❌ NO outputs/ (protected by .gitignore)

---

## 💻 Using From Terminal

### Setup on Your Mac (First Time)

```bash
# Clone your repository
cd ~
git clone https://github.com/YOUR_USERNAME/pharma-qa-agents.git
cd pharma-qa-agents

# Run installation
chmod +x install.sh
./install.sh

# Add your prompts (IMPORTANT!)
# Open each file in prompts/ and replace with full prompts
nano prompts/02-quality-sentinel.txt
# Paste full prompt, save (Ctrl+O), exit (Ctrl+X)
# Repeat for all 9 prompt files

# Add your PDFs
cp ~/Documents/EudraLex-Vol4.pdf knowledge/
cp ~/Documents/FDA-21CFR211.pdf knowledge/
# etc.

# Test it works
python scripts/agent.py --list
```

### Setup on Another Machine (e.g., Work Computer)

```bash
# Clone from GitHub
git clone https://github.com/YOUR_USERNAME/pharma-qa-agents.git
cd pharma-qa-agents

# Install
./install.sh

# Add prompts and PDFs (same as above)
# These are NOT in GitHub, so you need to add them again
```

---

## 📱 Daily Usage Examples

### Basic Queries

```bash
# Ask orchestrator to route
python scripts/agent.py orchestrator "Batch 2024-0892 failed dissolution"

# Direct to specific agent
python scripts/agent.py quality "Temperature excursion: 12°C for 45 min"

# Get root cause analysis
python scripts/agent.py lean "Tablet press keeps jamming"

# Risk assessment
python scripts/agent.py risk "Evaluate risk of changing compression force"
```

### Interactive Sessions

```bash
# Start conversation with agent
python scripts/agent.py quality --interactive

# You can now chat back and forth:
You: What does EudraLex say about OOS?
Agent: [responds]
You: How often must we investigate?
Agent: [responds]
You: exit
```

### Workflows

```bash
# List available workflows
python scripts/workflow.py --list

# Run CAPA workflow
python scripts/workflow.py capa-workflow \
  --var deviation="Dissolution failure" \
  --var batch="2024-0892" \
  --var product="Aspirin 500mg tablets"

# Creates complete investigation package in outputs/
```

### Save Outputs

```bash
# Save to specific file
python scripts/agent.py document \
  "Write SOP for tablet compression" \
  --output outputs/SOP-PROD-012.md

# Agent responds and saves to file
# Then you can view it:
cat outputs/SOP-PROD-012.md

# Or open in editor:
nano outputs/SOP-PROD-012.md
```

---

## 🔄 Keeping GitHub Updated

### After Adding New Prompts or Workflows

```bash
# Check what changed
git status

# Add specific files
git add prompts/02-quality-sentinel.txt
git add workflows/my-new-workflow.yaml

# Or add all changes
git add .

# Commit with message
git commit -m "Updated quality sentinel prompt for company standards"

# Push to GitHub
git push
```

### Creating Versions/Releases

```bash
# Tag a stable version
git tag -a v1.0 -m "Initial stable release"
git push origin v1.0

# Later, create new version
git tag -a v1.1 -m "Added analytical method writer"
git push origin v1.1
```

### Branching for Experimentation

```bash
# Create branch for testing new prompts
git checkout -b experiment-new-prompts

# Make changes, test them
nano prompts/02-quality-sentinel.txt

# If it works well:
git add prompts/02-quality-sentinel.txt
git commit -m "Improved quality prompt"
git checkout main
git merge experiment-new-prompts

# If it doesn't work:
git checkout main
git branch -D experiment-new-prompts  # Discard changes
```

---

## ⚡ Command Shortcuts

### Create Aliases (Optional but Recommended)

Add to `~/.zshrc` (Mac default) or `~/.bash_profile`:

```bash
# Open the file
nano ~/.zshrc

# Add these lines at the end:
export PATH="$HOME/.local/bin:$PATH"

# Pharma QA shortcuts
alias qa="cd ~/pharma-qa-agents"
alias qa-agent="python ~/pharma-qa-agents/scripts/agent.py"
alias qa-workflow="python ~/pharma-qa-agents/scripts/workflow.py"
alias qa-quality="python ~/pharma-qa-agents/scripts/agent.py quality"
alias qa-lean="python ~/pharma-qa-agents/scripts/agent.py lean"
alias qa-doc="python ~/pharma-qa-agents/scripts/agent.py document"

# Save and exit (Ctrl+O, Ctrl+X)

# Reload
source ~/.zshrc

# Now you can use shortcuts:
qa-quality "Assess this deviation"
qa-workflow capa-workflow --var deviation="Test"
```

### Even Shorter (Function)

```bash
# Add to ~/.zshrc:
qaa() {
    python ~/pharma-qa-agents/scripts/agent.py "$@"
}

# Usage:
qaa quality "My query"
qaa lean --interactive
qaa document "Create SOP" --output file.md
```

---

## 🔒 Security Best Practices

### What to Commit to GitHub

✅ **DO commit:**
- Scripts (agent.py, workflow.py)
- Configuration templates (config.yaml)
- Workflow templates
- Documentation (README, SETUP.md)
- Prompt files (they're just text, no company data)

❌ **DON'T commit:**
- knowledge/ folder (PDFs with company/regulatory data)
- outputs/ folder (generated reports with batch numbers, etc.)
- Any files with:
  - Batch numbers
  - Product formulations
  - Audit findings
  - Actual CAPA data

### If You Accidentally Commit Sensitive Data

```bash
# Remove file from git history
git rm --cached knowledge/CompanyConfidential.pdf

# Commit the removal
git commit -m "Remove accidentally committed confidential file"

# If already pushed to GitHub, force push
git push --force

# For complete history cleanup (advanced):
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch knowledge/CompanyConfidential.pdf" \
  --prune-empty --tag-name-filter cat -- --all
```

### Private Repository vs Public

**Use Private if:**
- ✅ Prompts contain company-specific procedures
- ✅ Workflows reference internal systems
- ✅ You want to control who can see your work

**Use Public if:**
- ✅ You want to share with pharma community
- ✅ Prompts are generic (no company specifics)
- ✅ You want others to contribute improvements

---

## 🆘 Common Terminal Issues

### "command not found: python"
```bash
# Mac uses python3
python3 scripts/agent.py --list

# Create alias (add to ~/.zshrc):
alias python=python3
```

### "Permission denied"
```bash
# Make scripts executable
chmod +x scripts/agent.py
chmod +x scripts/workflow.py
chmod +x install.sh
```

### "Cannot connect to Ollama"
```bash
# Terminal 1: Start Ollama (keep this running)
ollama serve

# Terminal 2: Use agents
python scripts/agent.py quality "Query"
```

### "Git push rejected"
```bash
# Pull first, then push
git pull origin main
git push origin main

# If conflicts, resolve them:
git status  # See conflicted files
nano <conflicted-file>  # Fix conflicts
git add <conflicted-file>
git commit -m "Resolved merge conflicts"
git push
```

---

## 📊 Advanced Usage

### Running Agents in Background

```bash
# Run workflow in background, save to log
nohup python scripts/workflow.py capa-workflow \
  --var deviation="Test" \
  > outputs/workflow.log 2>&1 &

# Check progress
tail -f outputs/workflow.log

# Kill if needed
jobs  # See job number
kill %1  # Kill job 1
```

### Batch Processing

```bash
# Create file with multiple queries
cat > queries.txt << 'EOF'
Deviation: Temperature excursion 12°C
Deviation: Tablet weight variation 5%
Deviation: Dissolution failure 68%
EOF

# Process each line
while IFS= read -r line; do
    python scripts/agent.py quality "$line" \
      --output "outputs/$(date +%Y%m%d-%H%M%S).md"
    sleep 2  # Avoid overwhelming system
done < queries.txt
```

### Integration with Other Tools

```bash
# Use with jq for JSON processing
python scripts/agent.py quality "Query" \
  | jq -R -s '{"response": .}'

# Pipe to clipboard (Mac)
python scripts/agent.py document "Create SOP" \
  | pbcopy

# Then paste in Word, email, etc.
```

---

## 🎓 Learning Resources

### Understanding Git & GitHub
- GitHub Guide: https://guides.github.com/
- Git Cheat Sheet: https://education.github.com/git-cheat-sheet-education.pdf

### Terminal Commands
- Mac Terminal Guide: https://support.apple.com/guide/terminal/welcome/mac

### Python Basics (if you want to customize)
- Python Tutorial: https://docs.python.org/3/tutorial/

---

## ✅ Quick Reference Card

```bash
# DAILY COMMANDS

# Basic query
python scripts/agent.py <agent-name> "query"

# Interactive
python scripts/agent.py <agent-name> --interactive

# Workflow
python scripts/workflow.py <workflow-name> --var key=value

# List things
python scripts/agent.py --list
python scripts/workflow.py --list

# GIT COMMANDS

# Check status
git status

# Commit changes
git add .
git commit -m "message"
git push

# Update from GitHub
git pull

# Create branch
git checkout -b branch-name

# MAINTENANCE

# Update model
ollama pull qwen2.5:14b

# Check Ollama
curl http://127.0.0.1:11434/api/tags

# View logs
tail -f outputs/history/*.log
```

---

**You're all set! 🎉**

Start with simple queries, experiment with workflows, and gradually customize the prompts for your company's specific needs.
