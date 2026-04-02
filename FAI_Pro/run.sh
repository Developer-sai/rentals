#!/bin/bash
# ═══════════════════════════════════════════
# IrishHome.AI — Quick Start Script
# ═══════════════════════════════════════════

echo ""
echo "🏡  IrishHome.AI — Starting up..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌  Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Install deps if needed
if [ ! -d ".venv" ]; then
    echo "📦  Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null

echo "📦  Installing dependencies..."
pip install -r requirements.txt -q

echo ""
echo "🚀  Starting FastAPI backend on http://localhost:8000"
echo "🖥️   Open http://localhost:8000 in your browser"
echo ""
echo "Press Ctrl+C to stop."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd backend
python3 main.py
