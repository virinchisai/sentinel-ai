#!/usr/bin/env bash
set -euo pipefail
pip install -e ".[dev]"
(cd frontend && npm ci)
python -m backend.migrate
echo "Register a personal account in the UI; connect Ollama before chatting."
