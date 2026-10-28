#!/usr/bin/env bash
set -euo pipefail
export OPENCLAW_STATE_DIR="${MYMIND_ROOT:-$HOME/.openclaw-mymind}"
export OPENCLAW_CONFIG_PATH="$OPENCLAW_STATE_DIR/openclaw.json"
runtime="$HOME/.local/share/mymind-runtime/bin/openclaw"
if [[ ! -x "$runtime" ]]; then
  echo 'Run bash install-mac.sh first.' >&2
  exit 1
fi
exec "$runtime" --profile mymind "$@"
