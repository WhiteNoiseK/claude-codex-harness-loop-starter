#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────────────
# harness_status.sh — harness-engineering session-recovery diagnostic script
#
# Role: on resume after an interruption (cold restart), show "where am I now" on one screen.
#   1) progress.md head (current/active task)  2) recent [HARNESS] commits
#   3) uncommitted changes  4) test status  5) type check
#
# Usage: bash scripts/harness_status.sh
#
# ── PARAM (vs the original project) ───────────────────────────────────────
#   The original hardcoded the progress.md path, src/, and tests/ in the body. The
#   first kit used {{TOKEN}} substitution. Now _harness_config.py merges .harness.toml
#   + defaults and emits them at runtime, and it works on the literal defaults even
#   with no config.
# ────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ╔══════════════════════════════════════════════════════════════════════╗
# ║ CONFIG — literal sensible defaults. Overridden if _harness_config.py exists. ║
# ╚══════════════════════════════════════════════════════════════════════╝
PROGRESS_FILE="docs/ai-workflow/progress.md"   # .harness.toml [paths] progress_file
SRC_ROOT="src"                                 # .harness.toml [paths] src_root
TESTS_ROOT="tests"                             # .harness.toml [paths] tests_root

# Runtime merge: even on failure the defaults above remain (works with zero config).
if command -v python >/dev/null 2>&1 && [[ -f "$SCRIPT_DIR/_harness_config.py" ]]; then
  _HARNESS_SH="$(python "$SCRIPT_DIR/_harness_config.py" --sh 2>/dev/null || true)"
  if [[ -n "$_HARNESS_SH" ]]; then
    eval "$_HARNESS_SH"
  fi
fi

# If not in a git context, fall back to the .harness.toml location (or the current directory if missing).
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo "$SCRIPT_DIR/..")"

echo "========================================="
echo "  HARNESS STATUS REPORT"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="

echo ""
echo "--- 1. Progress (current state) ---"
if [ -f "$PROGRESS_FILE" ]; then
    head -15 "$PROGRESS_FILE"
else
    echo "[WARNING] $PROGRESS_FILE not found"
fi

echo ""
echo "--- 2. Last HARNESS Commits ---"
HARNESS_COMMITS=$(git log --oneline --grep=HARNESS -5 2>/dev/null || true)
if [ -z "$HARNESS_COMMITS" ]; then
    echo "[INFO] no HARNESS commits (implementation not started yet)"
else
    echo "$HARNESS_COMMITS"
fi

echo ""
echo "--- 3. Uncommitted Changes ---"
CHANGES=$(git status --short 2>/dev/null || true)
if [ -z "$CHANGES" ]; then
    echo "[OK] no uncommitted changes"
else
    echo "$CHANGES"
fi

echo ""
echo "--- 4. Test Status ---"
if command -v python &> /dev/null && python -c "import pytest" 2>/dev/null && [ -d "$TESTS_ROOT" ]; then
    python -m pytest "$TESTS_ROOT/" -x --tb=line -q 2>/dev/null || echo "[FAIL] tests failed — check the output above"
else
    echo "[SKIP] pytest not installed or $TESTS_ROOT/ directory not found"
fi

echo ""
echo "--- 5. Type Check ---"
if command -v python &> /dev/null && python -c "import mypy" 2>/dev/null && [ -d "$SRC_ROOT" ]; then
    python -m mypy "$SRC_ROOT/" --ignore-missing-imports --no-error-summary 2>/dev/null || echo "[FAIL] type errors — check the output above"
else
    echo "[SKIP] mypy not installed or $SRC_ROOT/ directory not found"
fi

echo ""
echo "========================================="
echo "  Diagnostics complete"
echo "========================================="
