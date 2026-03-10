#!/bin/bash
# Pharma QA Agents - Installation Script for macOS

set -e

echo "========================================="
echo "Pharma QA Agents - Installation"
echo "========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "⚠️  Warning: This script is designed for macOS"
fi

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION found"

# Check Ollama
echo ""
echo "📋 Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed."
    echo "Please install Ollama:"
    echo "  brew install ollama"
    echo "Or download from: https://ollama.ai"
    exit 1
fi
echo "✅ Ollama found"

# Check if Ollama is running
if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is installed but not running."
    echo "Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
    if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama started successfully"
    else
        echo "❌ Could not start Ollama. Please run manually: ollama serve"
        exit 1
    fi
else
    echo "✅ Ollama is running"
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install --quiet --upgrade pip
pip3 install --quiet requests pyyaml

echo "✅ Dependencies installed"

# Create necessary directories
echo ""
echo "📁 Creating directory structure..."
mkdir -p knowledge
mkdir -p outputs
mkdir -p outputs/history

echo "✅ Directories created"

# Check for required models
echo ""
echo "📋 Checking Ollama models..."

REQUIRED_MODEL="qwen2.5:14b"

if ollama list | grep -q "$REQUIRED_MODEL"; then
    echo "✅ $REQUIRED_MODEL is installed"
else
    echo "⚠️  $REQUIRED_MODEL not found"
    echo ""
    read -p "Would you like to download $REQUIRED_MODEL now? (recommended) [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📥 Downloading $REQUIRED_MODEL (this may take several minutes)..."
        ollama pull $REQUIRED_MODEL
        echo "✅ Model downloaded"
    else
        echo "⚠️  You can download it later with: ollama pull $REQUIRED_MODEL"
    fi
fi

# Make scripts executable
echo ""
echo "🔧 Setting script permissions..."
chmod +x scripts/agent.py
chmod +x scripts/workflow.py
echo "✅ Scripts are executable"

# Create symlinks for easier access (optional)
echo ""
read -p "Create command shortcuts? (adds 'pharma-agent' and 'pharma-workflow' to PATH) [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
    
    ln -sf "$(pwd)/scripts/agent.py" "$INSTALL_DIR/pharma-agent"
    ln -sf "$(pwd)/scripts/workflow.py" "$INSTALL_DIR/pharma-workflow"
    
    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo ""
        echo "⚠️  Add the following to your ~/.zshrc or ~/.bash_profile:"
        echo ""
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
    fi
    
    echo "✅ Shortcuts created:"
    echo "   pharma-agent"
    echo "   pharma-workflow"
fi

# Test installation
echo ""
echo "🧪 Testing installation..."
if python3 scripts/agent.py --list > /dev/null 2>&1; then
    echo "✅ Installation test passed"
else
    echo "❌ Installation test failed"
    exit 1
fi

# Summary
echo ""
echo "========================================="
echo "✅ Installation Complete!"
echo "========================================="
echo ""
echo "📚 Next Steps:"
echo ""
echo "1. Add your regulatory PDFs to knowledge/ folder:"
echo "   - EudraLex Volume 4"
echo "   - FDA 21 CFR 211"
echo "   - ICH Q10, etc."
echo ""
echo "2. List available agents:"
echo "   python scripts/agent.py --list"
echo ""
echo "3. Try your first query:"
echo "   python scripts/agent.py orchestrator \"Help me with a deviation\""
echo ""
echo "4. Run interactive mode:"
echo "   python scripts/agent.py quality --interactive"
echo ""
echo "5. Execute a workflow:"
echo "   python scripts/workflow.py --list"
echo ""
echo "📖 Documentation: README.md"
echo ""
