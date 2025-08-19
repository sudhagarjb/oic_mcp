#!/bin/sh
set -e
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJ_DIR=$(dirname "$DIR")
cd "$PROJ_DIR"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
pip install -r requirements.txt
uvicorn mcp_server.main:app --host 0.0.0.0 --port 8080 --ws websockets 