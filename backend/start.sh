#!/bin/bash
# HedgeOS Backend — always runs inside the venv
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f "venv/bin/python" ]; then
  echo "ERROR: venv not found. Run: python3 -m venv venv && venv/bin/pip install -r requirements.txt"
  exit 1
fi

echo "[HedgeOS] Starting Flask API on port 5000 (venv python)"
exec venv/bin/python api.py
