#!/bin/bash
#
# Pharma QA Agents — Mac Launcher
# Starts the local web app and opens it in your default browser.
#
# Usage:
#   chmod +x launch.sh
#   ./launch.sh
#
# Requirements:
#   - Python 3.10+
#   - ANTHROPIC_API_KEY environment variable set
#

set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8000

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   Pharma QA Agents — Local App       ║"
echo "  ║   12 Agents · 6 Workflows · v2.1.0   ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "  [ERROR] Python 3 not found. Install from https://python.org"
    exit 1
fi

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "  [WARNING] ANTHROPIC_API_KEY not set."
    echo ""
    echo "  Set it with:"
    echo "    export ANTHROPIC_API_KEY='sk-ant-...'"
    echo ""
    echo "  Or add to ~/.zshrc for persistence:"
    echo "    echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.zshrc"
    echo ""
    read -p "  Enter your API key now (or press Enter to skip): " key
    if [ -n "$key" ]; then
        export ANTHROPIC_API_KEY="$key"
    fi
fi

# Install dependencies if needed
echo "  [1/3] Checking dependencies..."
cd "$APP_DIR"
pip3 install -q anthropic fastapi uvicorn jinja2 python-multipart pyyaml 2>/dev/null || {
    echo "  Installing dependencies..."
    pip3 install anthropic fastapi uvicorn jinja2 python-multipart pyyaml
}

# Initialize database
echo "  [2/3] Initializing database..."
python3 -c "from app.database import init_db; init_db()"

# Start server
echo "  [3/3] Starting server on http://localhost:$PORT"
echo ""
echo "  ──────────────────────────────────────"
echo "  App running at: http://localhost:$PORT"
echo "  Press Ctrl+C to stop"
echo "  ──────────────────────────────────────"
echo ""

# Open browser (after short delay to let server start)
(sleep 1.5 && open "http://localhost:$PORT" 2>/dev/null || xdg-open "http://localhost:$PORT" 2>/dev/null) &

# Run server
python3 -m uvicorn app.server:app --host 0.0.0.0 --port $PORT --reload
