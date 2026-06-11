#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────────────
# harness_run_verify.sh — Stage 3 VERIFY automation (Layer A)
#
# Usage:
#   scripts/harness_run_verify.sh <task_id> '<test_paths>' '<src_paths>'
#
# Example:
#   scripts/harness_run_verify.sh M3-RT-PERSIST-01 \
#       "tests/unit/test_foo.py tests/unit/test_bar.py" \
#       "src/feature/foo"
#
# Steps:
#   1) subset pytest -v                         → passed/failed/skipped/errors
#   2) pytest --cov=<dotted.module> --cov-fail-under=N → coverage_pct
#   3) mypy --strict <src>                      → 0 error
#   4) ruff check <src> <test>                  → 0 error
#   5) full regression pytest <tests_root>/ -q  → all pass (informational)
#
# Result → <SCORES_DIR>/<task_id>.verify.json (JSON structure)
#
# Exit codes:
#   0  all pass
#   1  fail (stderr message)
#
# ── DRIFT-FIX (vs the original project) ───────────────────────────────────
#   (A) --cov target = dotted-module. The original passed a file/directory path to
#       --cov, so coverage false-reported 0% and the AUDIT rerun reproduced the same
#       0% — passing it even though it was not forgery. Here we convert SRC_PATHS to a
#       dotted module.
#   (B) All paths/thresholds/commands unified via the *runtime config loader* (the
#       original used body literals; the first kit used {{TOKEN}} substitution). Now
#       _harness_config.py --sh merges .harness.toml + defaults, emits KEY='value', and
#       it is absorbed via eval. Even without python/.harness.toml, it runs end-to-end
#       on the literal defaults below (a double safety net).
# ────────────────────────────────────────────────────────────────────────
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ╔══════════════════════════════════════════════════════════════════════╗
# ║ CONFIG — literal sensible defaults. If _harness_config.py is present, its ║
# ║ merge of .harness.toml + defaults overrides the values below (eval). Even ║
# ║ if neither exists, these defaults apply → it still runs to completion with ║
# ║ zero config.                                                              ║
# ╚══════════════════════════════════════════════════════════════════════╝
SCORES_DIR="docs/ai-workflow/scores"    # .harness.toml [paths] scores_dir
SRC_ROOT="src"                          # .harness.toml [paths] src_root  (basis for dotted-module conversion)
TESTS_ROOT="tests"                      # .harness.toml [paths] tests_root (full-regression target)
COV_THRESHOLD=80                        # .harness.toml [gates] coverage_threshold
# Gate commands — must match .harness.toml [language]. Non-Python projects only swap .harness.toml.
TEST_CMD="python -m pytest"             # e.g. "python -m pytest"
TYPE_CMD="python -m mypy --strict --explicit-package-bases --ignore-missing-imports"
LINT_CMD="python -m ruff check"         # e.g. "python -m ruff check"

# Runtime merge: if python + _harness_config.py exist, overlay .harness.toml values on top of the defaults.
# Even on failure (no Python / parse failure), the literal defaults above remain in effect.
if command -v python >/dev/null 2>&1 && [[ -f "$SCRIPT_DIR/_harness_config.py" ]]; then
  _HARNESS_SH="$(python "$SCRIPT_DIR/_harness_config.py" --sh 2>/dev/null || true)"
  if [[ -n "$_HARNESS_SH" ]]; then
    eval "$_HARNESS_SH"
  fi
fi
# Backward-compatible aliases (the body uses the *_BIN names)
PYTEST_BIN="$TEST_CMD"
MYPY_BIN="$TYPE_CMD"
RUFF_BIN="$LINT_CMD"

if [[ $# -lt 3 ]]; then
  echo "usage: $0 <task_id> '<test_paths>' '<src_paths>'" >&2
  exit 1
fi

TASK_ID="$1"
TEST_PATHS="$2"
SRC_PATHS="$3"

# ─── Gate-integrity protection (SELFTEST lock — never remove) ────────────
# The HARNESS_*_CMD / HARNESS_VERIFY_OUT overrides are *self-test only*.
# If HARNESS_SELFTEST=1 is not set, they are force-disabled to block the path
# where a fake command is injected (accidentally or maliciously) to bypass the
# gate (record a fake command in verify.json → the commit guard reruns that fake
# command → pass).
if [[ "${HARNESS_SELFTEST:-0}" != "1" ]]; then
  unset HARNESS_SUBSET_CMD HARNESS_COV_CMD HARNESS_MYPY_CMD \
        HARNESS_RUFF_CMD HARNESS_FULL_CMD HARNESS_VERIFY_OUT
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT" || exit 1

mkdir -p "$SCORES_DIR"
# Output path — overridable via HARNESS_VERIFY_OUT for self-test injection
OUT="${HARNESS_VERIFY_OUT:-$SCORES_DIR/${TASK_ID}.verify.json}"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ─── DRIFT-FIX (A): SRC_PATHS (file/directory) → coverage dotted-module ───
# coverage measures accurately only if --cov receives an importable dotted-module name.
# Passing a file path (src/feature/foo.py) or directory path (src/feature/foo) false-reports 0%.
# Conversion rules:
#   - strip the SRC_ROOT prefix → dotted conversion from the first package segment
#   - drop the .py extension, / → .
#   - for multiple paths, use only the first token as the cov target (representative module); the rest are covered by mypy/ruff
to_dotted_module() {
  local p="$1"
  p="${p%/}"                       # strip trailing slash
  p="${p#./}"                      # strip leading ./
  # SRC_ROOT may be multi-segment like src/backend, so strip it on prefix match
  if [[ -n "$SRC_ROOT" && "$p" == "$SRC_ROOT"/* ]]; then
    p="${p#"$SRC_ROOT"/}"
  elif [[ -n "$SRC_ROOT" && "$p" == "$SRC_ROOT" ]]; then
    p=""
  fi
  p="${p%.py}"                     # if a file, drop the extension
  p="${p//\//.}"                   # path separators → dots
  # prefix SRC_ROOT's last segment as the package root (e.g. backend.feature.foo)
  local root_pkg="${SRC_ROOT##*/}"
  if [[ -n "$root_pkg" && -n "$p" ]]; then
    echo "${root_pkg}.${p}"
  elif [[ -n "$root_pkg" ]]; then
    echo "${root_pkg}"
  else
    echo "$p"
  fi
}
# convert the first src path to a dotted module (representative measurement target)
FIRST_SRC="$(echo "$SRC_PATHS" | awk '{print $1}')"
COV_MODULE="$(to_dotted_module "$FIRST_SRC")"

echo "[verify] task=$TASK_ID tests='$TEST_PATHS' src='$SRC_PATHS' cov_module='$COV_MODULE'" >&2

# Each gate command is overridable via a HARNESS_*_CMD env var (self-test injection only)
# ─── 1) subset pytest ────────────────────────────────────────────────
PYTEST_SUBSET_CMD="${HARNESS_SUBSET_CMD:-$PYTEST_BIN $TEST_PATHS -v --tb=short}"
SUBSET_OUT="$(bash -c "$PYTEST_SUBSET_CMD" 2>&1 || true)"
SUBSET_PASS="$(echo "$SUBSET_OUT" | grep -oE '[0-9]+ passed' | head -1 | grep -oE '[0-9]+' || echo 0)"
SUBSET_FAIL="$(echo "$SUBSET_OUT" | grep -oE '[0-9]+ failed' | head -1 | grep -oE '[0-9]+' || echo 0)"
SUBSET_SKIP="$(echo "$SUBSET_OUT" | grep -oE '[0-9]+ skipped' | head -1 | grep -oE '[0-9]+' || echo 0)"
# A collection error (import failure / bad path) prints as 'N error(s)' with no 'failed'.
# Missing this would make STATUS=pass a false positive, so count errors as failures too.
SUBSET_ERR="$(echo "$SUBSET_OUT" | grep -oE '[0-9]+ error' | head -1 | grep -oE '[0-9]+' || echo 0)"

# ─── 2) coverage (subset + --cov=dotted-module) ───────────────────────
# DRIFT-FIX (A): --cov=$COV_MODULE (dotted) — not a file path.
COV_CMD="${HARNESS_COV_CMD:-$PYTEST_BIN $TEST_PATHS --cov=$COV_MODULE --cov-report=term --cov-fail-under=$COV_THRESHOLD}"
COV_OUT="$(bash -c "$COV_CMD" 2>&1 || true)"
COV_PCT="$(echo "$COV_OUT" | grep -oE 'TOTAL[[:space:]]+[0-9]+[[:space:]]+[0-9]+[[:space:]]+[0-9]+%' | grep -oE '[0-9]+%' | head -1 | tr -d '%' || echo 0)"
COV_PASS_FAIL="pass"
echo "$COV_OUT" | grep -qE "Required test coverage of ${COV_THRESHOLD}%? not reached" && COV_PASS_FAIL="fail"

# ─── 3) mypy strict ────────────────────────────────────────────────────
MYPY_CMD="${HARNESS_MYPY_CMD:-$MYPY_BIN $SRC_PATHS}"
MYPY_OUT="$(bash -c "$MYPY_CMD" 2>&1 || true)"
MYPY_ERR="$(echo "$MYPY_OUT" | grep -cE 'error:' || true)"

# ─── 4) ruff ───────────────────────────────────────────────────────────
RUFF_CMD="${HARNESS_RUFF_CMD:-$RUFF_BIN $SRC_PATHS $TEST_PATHS}"
RUFF_OUT="$(bash -c "$RUFF_CMD" 2>&1 || true)"
RUFF_ERR="$(echo "$RUFF_OUT" | grep -cE '^[^[:space:]].*:.*:.*:' || true)"
echo "$RUFF_OUT" | grep -q 'All checks passed' && RUFF_ERR=0

# ─── 5) full regression (informational regression guard — does not affect STATUS) ──
FULL_CMD="${HARNESS_FULL_CMD:-$PYTEST_BIN $TESTS_ROOT/ -q}"
FULL_OUT="$(bash -c "$FULL_CMD" 2>&1 || true)"
FULL_PASS="$(echo "$FULL_OUT" | grep -oE '[0-9]+ passed' | head -1 | grep -oE '[0-9]+' || echo 0)"
FULL_FAIL="$(echo "$FULL_OUT" | grep -oE '[0-9]+ failed' | head -1 | grep -oE '[0-9]+' || echo 0)"

# ─── Overall status (module-scope gates only — quality-gates.md §1 Stage 3) ──────
# A full-suite failure does not flip STATUS (preventing an unrelated module's pre-existing
# fail/hang from false-failing this task's VERIFY). The full-suite result is recorded separately (not hidden).
STATUS="pass"
[[ "$SUBSET_FAIL" != "0" ]] && STATUS="fail"
[[ "$SUBSET_ERR" != "0" ]] && STATUS="fail"   # collection error is also a failure (blocks false positives)
[[ "$COV_PASS_FAIL" != "pass" ]] && STATUS="fail"
[[ "$MYPY_ERR" != "0" ]] && STATUS="fail"
[[ "$RUFF_ERR" != "0" ]] && STATUS="fail"

# On full-suite failure: informational → regression_detected (out-of-scope tracking signal)
FULL_GUARD_STATUS="informational"
[[ "$FULL_FAIL" != "0" ]] && FULL_GUARD_STATUS="regression_detected"

# ─── JSON output ──────────────────────────────────────────────────────
cat > "$OUT" <<EOF
{
  "task_id": "$TASK_ID",
  "stage": "VERIFY",
  "agent": "harness_run_verify.sh",
  "status": "$STATUS",
  "threshold": "binary_pass_fail",
  "artifacts": {
    "pytest_cmd": "$PYTEST_SUBSET_CMD",
    "pytest_result": {"passed": $SUBSET_PASS, "failed": $SUBSET_FAIL, "skipped": $SUBSET_SKIP, "errors": $SUBSET_ERR},
    "coverage_cmd": "$COV_CMD",
    "coverage_module": "$COV_MODULE",
    "coverage_pct": $COV_PCT,
    "coverage_fail_under": "$COV_PASS_FAIL",
    "mypy_cmd": "$MYPY_CMD",
    "mypy_errors": $MYPY_ERR,
    "ruff_cmd": "$RUFF_CMD",
    "ruff_errors": $RUFF_ERR,
    "full_suite_regression_guard": {
      "status": "$FULL_GUARD_STATUS",
      "cmd": "$FULL_CMD",
      "result": {"passed": $FULL_PASS, "failed": $FULL_FAIL},
      "note": "Full regression does not affect the Stage 3 close gate (module scope). On failure, it is tracked separately as an out-of-scope regression."
    }
  },
  "timestamp": "$TS"
}
EOF

echo "[verify] wrote $OUT (status=$STATUS)" >&2

if [[ "$STATUS" == "pass" ]]; then
  exit 0
else
  echo "[verify] FAIL — see $OUT" >&2
  echo "--- pytest subset tail ---" >&2
  echo "$SUBSET_OUT" | tail -10 >&2
  echo "--- mypy ---" >&2
  echo "$MYPY_OUT" | tail -10 >&2
  echo "--- ruff ---" >&2
  echo "$RUFF_OUT" | tail -10 >&2
  exit 1
fi
