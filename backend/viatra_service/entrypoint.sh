#!/bin/bash
set -e

echo "🚀 Starting Viatra Service Entrypoint..."

# 1. Sync Tables & Seed Demo Data
echo "📦 Running Seeding operations..."
python scripts/seed_demo.py

# 2. Start Application
echo "📡 Launching Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
