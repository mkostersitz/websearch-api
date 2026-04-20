#!/bin/bash
# Quick start script for the WebSearch API Admin Dashboard

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$SCRIPT_DIR/admin-dashboard"

echo "🚀 WebSearch API Admin Dashboard - Quick Start"
echo "=============================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "Install Node.js from: https://nodejs.org/"
    exit 1
fi

echo "✓ Node.js $(node --version) detected"
echo "✓ npm $(npm --version) detected"
echo ""

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Warning: Backend API is not running"
    echo ""
    echo "Start the backend first:"
    echo "  cd $SCRIPT_DIR"
    echo "  ./run.sh api"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Backend API is running at http://localhost:8000"
fi

echo ""
echo "Starting Admin Dashboard..."
echo ""

cd "$DASHBOARD_DIR"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies (this may take a minute)..."
    npm install
    echo ""
fi

echo "🎨 Starting development server..."
echo ""
echo "Dashboard will be available at: http://localhost:3000"
echo "Admin API Key: GA_Incg4zEhpK-65G6PwL499t2kXvH2Cs-hWf6udtZU"
echo ""
echo "Press Ctrl+C to stop"
echo ""

npm run dev
