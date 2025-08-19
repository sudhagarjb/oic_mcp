#!/bin/sh
set -e
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJ_DIR=$(dirname "$DIR")
cd "$PROJ_DIR"

if [ ! -d .venv ]; then
	python3 -m venv .venv
fi
. .venv/bin/activate
pip -q install -r requirements.txt > /dev/null 2>&1 || true
# Ensure websockets for the client
pip -q install websockets > /dev/null 2>&1 || true

exec python scripts/ws-call.py "$@" 