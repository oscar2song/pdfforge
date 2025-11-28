#!/usr/bin/env bash
set -euo pipefail
echo "Running pre-commit checks (bash)..."

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

ok=0

# Run ruff if installed
if command -v ruff >/dev/null 2>&1; then
  echo "-> Running ruff --fix ."
  if ! ruff check --fix .; then ok=1; fi
else
  echo "-> ruff not found, skipping"
fi

if command -v isort >/dev/null 2>&1; then
  echo "-> Running isort ."
  if ! isort .; then ok=1; fi
else
  echo "-> isort not found, skipping"
fi

if command -v black >/dev/null 2>&1; then
  echo "-> Running black ."
  if ! black .; then ok=1; fi
else
  echo "-> black not found, skipping"
fi

if [ -f package.json ]; then
  if command -v npm >/dev/null 2>&1; then
    echo "-> Running npm lint (if present)"
    if ! npm run lint --silent --if-present; then ok=1; fi
  else
    echo "-> npm not found, skipping frontend lint"
  fi
else
  echo "-> No package.json at repo root; skipping npm lint"
fi

if [ "$ok" -ne 0 ]; then
  echo "Pre-commit checks failed. Fix issues and try again." >&2
  exit 1
fi

echo "Pre-commit checks passed."
exit 0
