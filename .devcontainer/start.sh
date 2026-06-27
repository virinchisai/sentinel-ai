#!/usr/bin/env bash
# Starts backend (port 8000) and frontend (port 3000) in the background.
# Logs land in /tmp/backend.log and /tmp/frontend.log

set -e

echo "→ Starting backend on :8000..."
nohup uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 \
    > /tmp/backend.log 2>&1 &

echo "→ Starting frontend on :3000..."
cd frontend
nohup npm run dev > /tmp/frontend.log 2>&1 &
cd ..

sleep 3
echo
echo "═══════════════════════════════════════════════════════════════"
echo "  SentinelAI is running."
echo
echo "  Frontend (try this!) → http://localhost:3000"
echo "  Backend API          → http://localhost:8000/docs"
echo
echo "  Demo login → alice / sentinel-demo"
echo
echo "  Logs: tail -f /tmp/backend.log /tmp/frontend.log"
echo "═══════════════════════════════════════════════════════════════"
