#!/bin/bash
# Stock Dashboard - Linux/macOS Run Script

echo "================================"
echo "🤖 Stock Analysis Dashboard"
echo "================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt -q

# Run the app
echo ""
echo "🚀 Starting application..."
echo "📍 Open http://127.0.0.1:5000 in your browser"
echo ""

python app.py
