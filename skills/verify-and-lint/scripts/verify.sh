#!/usr/bin/env bash
#
# verify.sh - Shell wrapper for the verify-and-lint diagnostic runner
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/verify.py"

if command -v python3 >/dev/null 2>&1; then
    exec python3 "${PYTHON_SCRIPT}" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "${PYTHON_SCRIPT}" "$@"
else
    echo "Warning: Python not found in PATH. Falling back to basic bash test/lint execution." >&2

    # Basic fallback discovery
    EXIT_CODE=0

    if [ -f "pyproject.toml" ] || [ -f "pytest.ini" ] || [ -d "tests" ]; then
        if command -v pytest >/dev/null 2>&1; then
            echo "Running pytest..."
            pytest -q || EXIT_CODE=$?
        fi
    elif [ -f "package.json" ]; then
        if command -v npm >/dev/null 2>&1; then
            echo "Running npm test..."
            npm test || EXIT_CODE=$?
        fi
    elif [ -f "Cargo.toml" ]; then
        if command -v cargo >/dev/null 2>&1; then
            echo "Running cargo test..."
            cargo test || EXIT_CODE=$?
        fi
    elif [ -f "go.mod" ]; then
        if command -v go >/dev/null 2>&1; then
            echo "Running go test..."
            go test ./... || EXIT_CODE=$?
        fi
    fi

    exit "${EXIT_CODE}"
fi
