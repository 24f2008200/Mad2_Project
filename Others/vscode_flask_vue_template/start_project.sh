#!/usr/bin/env bash
set -e

# Go to project root
cd "$(dirname "$0")"

# Create venv if missing
if [ ! -d "venv" ]; then
    python -m venv venv
fi

# Activate venv
source venv/Scripts/activate || source venv/bin/activate

# Install requirements if available
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

echo "✅ Project ready in local venv"
