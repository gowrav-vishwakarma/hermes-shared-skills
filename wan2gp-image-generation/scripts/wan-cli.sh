#!/bin/bash
# Quick-start script for WanGP CLI
# Ensures you're using the correct Python environment.
#
# Required env vars (loaded from $PROFILE_ROOT/.env):
#   WAN_APP_DIR  -- WanGP app directory containing wgp.py and env/bin/python
#   WAN_PYTHON   -- (optional) override for the interpreter path

set -euo pipefail

: "${WAN_APP_DIR:?WAN_APP_DIR must be set in profile .env (run: set -a; source \$PROFILE_ROOT/.env; set +a)}"

cd "$WAN_APP_DIR"

PYTHON_BIN="${WAN_PYTHON:-$WAN_APP_DIR/env/bin/python}"
exec "$PYTHON_BIN" wgp.py "$@"
