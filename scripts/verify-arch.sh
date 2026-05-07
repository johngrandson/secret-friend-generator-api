#!/usr/bin/env bash
# verify-arch.sh — run the full architecture-enforcement bundle.
#
# Use as a pre-push gate or before declaring an implementation complete.
# Each step exits non-zero on failure so the script as a whole signals a
# clean (0) or dirty (>0) architecture state.
#
# See .claude/rules/clean-architecture-enforcement.md for the rationale.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
red() { printf "\033[31m%s\033[0m\n" "$*"; }

run_step() {
  local label="$1"; shift
  bold ">>> $label"
  if "$@"; then
    green "    OK"
  else
    red "    FAIL: $label"
    exit 1
  fi
}

run_step "1/5 import-linter (architectural contracts)" \
  poetry run lint-imports

run_step "2/5 architecture fitness functions" \
  poetry run pytest tests/architecture/ -q --no-header

run_step "3/5 ruff (lint + import order)" \
  poetry run ruff check src/

run_step "4/5 mypy (type check)" \
  poetry run mypy src/

run_step "5/5 full test suite" \
  poetry run pytest -q --no-header

green ""
green "All architecture checks passed."
