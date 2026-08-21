#!/usr/bin/env bash
# verify.sh - Wrapper for verify.py diagnostic runner
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(which python3 || which python || echo "python3")"

exec "${PYTHON_BIN}" "${SCRIPT_DIR}/verify.py" "$@"
