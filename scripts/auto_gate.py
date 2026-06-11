"""auto_gate.py - Automated quality-gate decision engine (fact + logic layers).

Evaluates an independent-reviewer review JSON (e.g. Codex), local verification
results, and the set of changed file paths to decide whether a pipeline stage
can proceed automatically (auto_continue) or must stop for human review (stop).

Two gating layers combine here:
  * Fact layer  - local re-run results (pytest/ruff/black/mypy, claimed==actual).
  * Logic layer - the independent reviewer's verdict / severity / boundary flags.

The engine itself is project-agnostic. The only project-specific knobs are the
safety-boundary path patterns and content signals, which default to generic
placeholders and are overridable three ways (lowest to highest precedence):
  1. Module DEFAULT_* constants below (generic, safe placeholders).
  2. The repo's .harness.toml [safety_boundary] paths list (auto-loaded).
  3. Explicit arguments to scan_hard_boundaries() / scan_content_boundaries().

Configure per project in .harness.toml [safety_boundary]; see also the 6-stage
gate spec at docs/_harness/quality-gates.md and the independent-reviewer
protocol at docs/ai-workflow/codex_claude_review_protocol.md.

Public API:
    SEVERITY_ORDER      - ordered list of severity levels, lowest to highest
    DEFAULT_BOUNDARY_PATTERNS / DEFAULT_SAFE_PREFIXES / DEFAULT_SAFE_EXACT /
        DEFAULT_CONTENT_SIGNALS - generic, overridable defaults
    load_boundary_patterns()     -> list[str]
    validate_review_json(review) -> list[str]
    validate_local_verify(lv)    -> list[str]
    scan_hard_boundaries(changed_paths, patterns=None, safe_prefixes=None,
                         safe_exact=None) -> list[str]
    scan_content_boundaries(diff_text, signals=None) -> list[str]
    decide_gate(review, local_verify, changed_paths, *, ...) -> dict
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Severity ordering (lowest to highest risk)
# ---------------------------------------------------------------------------

SEVERITY_ORDER: list[str] = ["NONE", "INFO", "NIT", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
"""Ordered severity levels from lowest (NONE) to highest (CRITICAL)."""


def _severity_rank(sev: str) -> int:
    """Rank a severity string by SEVERITY_ORDER; unknown values rank highest (fail-safe)."""
    try:
        return SEVERITY_ORDER.index(sev)
    except ValueError:
        return len(SEVERITY_ORDER)


# ---------------------------------------------------------------------------
# Allowed enum values for review fields
# ---------------------------------------------------------------------------

_ALLOWED_VERDICTS: frozenset[str] = frozenset(
    ["PASS", "PASS_WITH_NITS", "CLOSE", "BLOCKED", "ADJUST", "RE_OPEN"]
)
_PASS_VERDICTS: frozenset[str] = frozenset(["PASS", "PASS_WITH_NITS", "CLOSE"])

# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

_REQUIRED_REVIEW_FIELDS: list[str] = [
    "prompt_id",
    "task_id",
    "stage",
    "verdict",
    "max_severity",
    "requires_user",
    "hard_boundary_violation",
    "findings",
    "next_action",
    "notes",
    "reply_prompt_id",
    "rerun_performed",
]

_REQUIRED_LV_FIELDS: list[str] = [
    "pytest",
    "ruff",
    "black",
    "mypy",
    "claimed_equals_actual",
    "commands_run",
    "scope",
]

_REQUIRED_LV_COMMANDS: list[str] = ["pytest", "ruff", "black", "mypy"]

# Values that indicate a tool ran successfully.
# Any value NOT in this set (case-insensitive) is treated as failure.
_TOOL_PASS_VALUES: frozenset[str] = frozenset(["ok", "pass", "passed", "success"])

# Tool fields whose string values must be success values.
_TOOL_RESULT_FIELDS: list[str] = ["ruff", "black", "mypy"]

# ---------------------------------------------------------------------------
# Hard boundary patterns (GENERIC DEFAULTS - override per project)
#
# These are deliberately generic placeholders that work for most repositories.
# Files matching these glob patterns require human review before proceeding.
# Real projects add their own (hardware drivers, schema/migration files, the
# shutdown path, secrets, ...) via .harness.toml [safety_boundary] paths or by
# passing patterns explicitly to scan_hard_boundaries().
# ---------------------------------------------------------------------------

DEFAULT_BOUNDARY_PATTERNS: list[str] = [
    "**/migrations/**",  # ORM/database migration scripts
    "alembic/**",  # Alembic migration tree
    "**/*schema*.py",  # data/DB schema definitions
    ".env*",  # environment / secret files (excluding .env.example)
    "**/*secret*",  # any file whose name signals a secret
    "deploy/release*",  # release/deploy entrypoints
    "**/order*",  # generic critical-domain example (configure per project)
]

# Paths that are explicitly NOT hard boundaries, regardless of glob matches.
# Checked as prefix/contains exclusions before applying boundary patterns.
DEFAULT_SAFE_PREFIXES: list[str] = [
    "scripts/",
    "tests/",
    "docs/ai-workflow/",
]

DEFAULT_SAFE_EXACT: frozenset[str] = frozenset(
    [
        ".env.example",  # template file: safe to modify without human review
    ]
)

# ---------------------------------------------------------------------------
# Content boundary signals (GENERIC DEFAULTS - override per project)
#
# Substrings whose presence in a diff indicates a safety-critical change that
# the path scan alone might miss (e.g. a safety-severity alarm or a shutdown
# state transition). Generic placeholders here; configure per project.
# ---------------------------------------------------------------------------

DEFAULT_CONTENT_SIGNALS: list[str] = [
    "SAFETY",  # safety-severity marker (generic placeholder)
    "SHUTDOWN",  # shutdown / stop transition (generic placeholder)
    "target_state",  # explicit state-machine target (generic placeholder)
]

# Backward/internal aliases used by the engine. These are the *active* defaults;
# load_boundary_patterns() may extend the boundary set from .harness.toml.
_BOUNDARY_PATTERNS: list[str] = list(DEFAULT_BOUNDARY_PATTERNS)
_SAFE_PREFIXES: list[str] = list(DEFAULT_SAFE_PREFIXES)
_SAFE_EXACT: frozenset[str] = frozenset(DEFAULT_SAFE_EXACT)
_CONTENT_SIGNALS: list[str] = list(DEFAULT_CONTENT_SIGNALS)


def load_boundary_patterns(start: Path | None = None) -> list[str]:
    """Return boundary glob patterns: module defaults plus .harness.toml entries.

    Reads the repo's .harness.toml [safety_boundary] paths list (if present) and
    merges it onto DEFAULT_BOUNDARY_PATTERNS. This keeps the safety boundary in a
    single per-project place (.harness.toml) instead of hardcoded in this engine.

    The read is best-effort and never raises: if the file is missing or cannot be
    parsed, only the generic defaults are returned. This mirrors the kit's
    stability-first rule that config must never be able to break the gate.

    Args:
        start: Optional path to begin the upward search for .harness.toml.

    Returns:
        The merged, de-duplicated list of boundary glob patterns.
    """
    patterns: list[str] = list(DEFAULT_BOUNDARY_PATTERNS)
    extra = _read_safety_boundary_paths(start)
    for pat in extra:
        if pat not in patterns:
            patterns.append(pat)
    return patterns


def load_severity_gate(start: Path | None = None) -> tuple[bool, str]:
    """Read (severity_is_stop_axis, severity_auto_max) from .harness.toml [review_overlay].

    Severity is NOT a stop axis by default: at detection the problem is already identified,
    so findings (incl. HIGH/CRITICAL) self-heal in the FIX loop. A high-stakes project may
    opt in (severity_is_stop_axis = true), after which a finding whose severity exceeds
    severity_auto_max stops for a human.

    Best-effort and never raises: on any failure returns (False, "MEDIUM") so the gate keeps
    running with severity disabled (the safe default).

    Args:
        start: Optional path to begin the upward search for .harness.toml.

    Returns:
        (severity_is_stop_axis, severity_auto_max).
    """
    is_stop = False
    auto_max = "MEDIUM"
    try:
        toml_path = _find_harness_toml(start)
        if toml_path is None:
            return is_stop, auto_max
        text = toml_path.read_text(encoding="utf-8")
    except OSError:
        return is_stop, auto_max
    try:
        section = re.search(
            r"^\[review_overlay\][^\[]*", text, flags=re.MULTILINE | re.DOTALL
        )
        if section is None:
            return is_stop, auto_max
        body = section.group(0)
        m_flag = re.search(
            r"^\s*severity_is_stop_axis\s*=\s*(\w+)", body, flags=re.MULTILINE
        )
        if m_flag:
            is_stop = m_flag.group(1).strip().lower() in ("true", "1", "yes", "on")
        m_max = re.search(
            r"""^\s*severity_auto_max\s*=\s*['"]?([A-Za-z]+)['"]?""",
            body,
            flags=re.MULTILINE,
        )
        if m_max:
            auto_max = m_max.group(1).strip().upper()
    except Exception:  # pragma: no cover - defensive: never break the gate
        return False, "MEDIUM"
    return is_stop, auto_max


def _read_safety_boundary_paths(start: Path | None = None) -> list[str]:
    """Read [safety_boundary] paths from .harness.toml; never raise.

    Tries the shared loader's TOML reader when available, then a tiny inline
    fallback parser. Returns an empty list on any failure so the gate keeps
    running on generic defaults alone.

    Args:
        start: Optional path to begin the upward search for .harness.toml.

    Returns:
        List of glob pattern strings from [safety_boundary].paths (possibly empty).
    """
    try:
        toml_path = _find_harness_toml(start)
        if toml_path is None:
            return []
        text = toml_path.read_text(encoding="utf-8")
    except OSError:
        return []
    try:
        return _extract_safety_paths(text)
    except Exception:  # pragma: no cover - defensive: never break the gate
        return []


def _find_harness_toml(start: Path | None) -> Path | None:
    """Walk upward from start looking for .harness.toml; return it or None."""
    here = (start or Path(__file__).resolve()).resolve()
    for base in (here, *here.parents):
        cand = base / ".harness.toml"
        if cand.is_file():
            return cand
    return None


def _extract_safety_paths(text: str) -> list[str]:
    """Parse only the [safety_boundary] paths = [...] array from TOML text.

    A minimal, dependency-free extractor: it isolates the [safety_boundary]
    section and collects quoted strings from a paths = [...] array, ignoring
    commented-out lines. Sufficient for the flat schema this kit ships.

    Args:
        text: Full .harness.toml file contents.

    Returns:
        List of pattern strings (empty when the section/array is absent).
    """
    # Isolate the [safety_boundary] section body (up to the next [section] header).
    section = re.search(
        r"^\[safety_boundary\][^\[]*", text, flags=re.MULTILINE | re.DOTALL
    )
    if section is None:
        return []
    body = section.group(0)
    # Grab the paths = [ ... ] array contents.
    arr = re.search(r"paths\s*=\s*\[(.*?)\]", body, flags=re.DOTALL)
    if arr is None:
        return []
    result: list[str] = []
    for raw_line in arr.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Strip trailing comments, then collect each quoted token on the line.
        for token in re.findall(r"""(['"])(.*?)\1""", line):
            value = token[1].strip()
            if value:
                result.append(value)
    return result


def _is_safe_path(
    path: str,
    safe_prefixes: list[str] | None = None,
    safe_exact: frozenset[str] | None = None,
) -> bool:
    """Return True if the path is explicitly excluded from boundary checks.

    Args:
        path: The file path to test.
        safe_prefixes: Optional override of safe path prefixes.
        safe_exact: Optional override of exact safe paths.

    Returns:
        True if the path should be skipped by boundary scanning.
    """
    prefixes = safe_prefixes if safe_prefixes is not None else _SAFE_PREFIXES
    exact = safe_exact if safe_exact is not None else _SAFE_EXACT
    if path in exact:
        return True
    norm = path.replace("\\", "/")
    for prefix in prefixes:
        if norm.startswith(prefix):
            return True
    return False


def _matches_boundary(path: str, patterns: list[str] | None = None) -> bool:
    """Return True if path matches any hard-boundary glob pattern.

    Args:
        path: The file path to test.
        patterns: Optional override of boundary glob patterns. When None, the
            merged defaults + .harness.toml patterns are used.

    Returns:
        True if the path matches a boundary pattern.
    """
    active_patterns = patterns if patterns is not None else load_boundary_patterns()
    norm = path.replace("\\", "/")
    for pat in active_patterns:
        # fnmatch on full path for ** patterns (simplified: treat ** as *)
        flat_pat = pat.replace("**", "*")
        if fnmatch.fnmatch(norm, flat_pat):
            return True
        # Also check basename for patterns like *secret*, *schema*.py and the
        # trailing component of directory-prefixed patterns like **/*secret*.
        # The tail check is skipped when the tail is a pure wildcard ("*"),
        # which would otherwise match every basename (e.g. from **/migrations/**).
        basename = norm.rsplit("/", 1)[-1]
        if fnmatch.fnmatch(basename, flat_pat):
            return True
        pat_tail = flat_pat.rsplit("/", 1)[-1]
        if pat_tail.strip("*") and fnmatch.fnmatch(basename, pat_tail):
            return True
        # Prefix match for directory globs like alembic/**
        if pat.endswith("/**") or pat.endswith("/*"):
            dir_prefix = pat.rstrip("*").rstrip("/")
            if norm.startswith(dir_prefix + "/") or norm == dir_prefix:
                return True
    return False


def scan_hard_boundaries(
    changed_paths: list[str],
    patterns: list[str] | None = None,
    safe_prefixes: list[str] | None = None,
    safe_exact: frozenset[str] | None = None,
) -> list[str]:
    """Return paths from changed_paths that match hard boundary patterns.

    Safe paths (scripts/, tests/, docs/ai-workflow/, plus any configured exact
    paths) are excluded even if they incidentally match a boundary pattern.

    Args:
        changed_paths: List of file paths changed in this diff.
        patterns: Optional override of boundary glob patterns. When None, the
            merged defaults + .harness.toml [safety_boundary] patterns are used.
        safe_prefixes: Optional override of safe path prefixes.
        safe_exact: Optional override of exact safe paths.

    Returns:
        List of paths that are hard boundary violations.
    """
    result: list[str] = []
    for path in changed_paths:
        if _is_safe_path(path, safe_prefixes, safe_exact):
            continue
        if _matches_boundary(path, patterns):
            result.append(path)
    return result


def scan_content_boundaries(
    diff_text: str,
    signals: list[str] | None = None,
) -> list[str]:
    """Return content signals found in diff_text that indicate safety-critical changes.

    The default signals are generic placeholders (SAFETY, SHUTDOWN, target_state);
    configure project-specific signals via the signals argument. Matching is
    case-insensitive to prevent a lowercase-variant bypass.

    Args:
        diff_text: Git diff text to scan.
        signals: Optional override of content signal substrings.

    Returns:
        List of matched signal strings (empty if clean).
    """
    active_signals = signals if signals is not None else _CONTENT_SIGNALS
    found: list[str] = []
    diff_lower = diff_text.lower()
    for signal in active_signals:
        if signal.lower() in diff_lower:
            found.append(signal)
    return found


def validate_review_json(review: dict[str, Any]) -> list[str]:
    """Validate an independent-reviewer review dict against the required schema.

    Checks:
    - All 12 required fields present
    - verdict is in the allowed enum
    - max_severity is in SEVERITY_ORDER
    - Each finding has severity, summary, required_action

    Args:
        review: The review dict to validate.

    Returns:
        List of error strings. Empty list means valid.
    """
    errors: list[str] = []

    for field in _REQUIRED_REVIEW_FIELDS:
        if field not in review:
            errors.append(f"missing required field: {field!r}")

    if errors:
        # Cannot safely access field values; return early.
        return errors

    verdict = review.get("verdict", "")
    if verdict not in _ALLOWED_VERDICTS:
        errors.append(f"invalid verdict: {verdict!r}")

    severity = review.get("max_severity", "")
    if severity not in SEVERITY_ORDER:
        errors.append(f"invalid max_severity: {severity!r}")

    findings = review.get("findings", [])
    if isinstance(findings, list):
        for i, finding in enumerate(findings):
            if not isinstance(finding, dict):
                errors.append(f"finding[{i}] is not a dict")
                continue
            for fkey in ("severity", "summary", "required_action"):
                if fkey not in finding:
                    errors.append(f"finding[{i}] missing field: {fkey!r}")

    return errors


def validate_local_verify(lv: dict[str, Any]) -> list[str]:
    """Validate a local verification result dict.

    Checks:
    - All 7 required fields present
    - claimed_equals_actual is True
    - commands_run contains pytest, ruff, black, mypy
    - ruff/black/mypy values are success values
    - pytest claimed counts match actual counts and have no failures/errors

    Args:
        lv: The local verification dict to validate.

    Returns:
        List of error strings. Empty list means valid.
    """
    errors: list[str] = []

    for field in _REQUIRED_LV_FIELDS:
        if field not in lv:
            errors.append(f"missing required field: {field!r}")

    if errors:
        return errors

    if not lv.get("claimed_equals_actual"):
        errors.append("claimed_equals_actual is False or missing")

    commands_run = lv.get("commands_run", [])
    for cmd in _REQUIRED_LV_COMMANDS:
        if cmd not in commands_run:
            errors.append(f"required command not in commands_run: {cmd!r}")

    # Check ruff/black/mypy result values: must be in _TOOL_PASS_VALUES.
    for tool in _TOOL_RESULT_FIELDS:
        val = lv.get(tool)
        if (
            val is None
            or not isinstance(val, str)
            or val.lower() not in _TOOL_PASS_VALUES
        ):
            errors.append(f"{tool!r} result is not a success value: {val!r}")

    # Check pytest claimed vs actual counts
    pytest_data = lv.get("pytest")
    if isinstance(pytest_data, dict):
        claimed = pytest_data.get("claimed", {})
        actual = pytest_data.get("actual", {})
        if isinstance(claimed, dict) and isinstance(actual, dict):
            if claimed != actual:
                errors.append(f"pytest claimed {claimed!r} != actual {actual!r}")
        # actual.failed > 0 or actual.errors > 0 is always a failure
        if isinstance(actual, dict):
            if actual.get("failed", 0) > 0:
                errors.append(f"pytest actual.failed={actual['failed']} > 0")
            if actual.get("errors", 0) > 0:
                errors.append(f"pytest actual.errors={actual['errors']} > 0")

    return errors


def _validate_review_input(
    review: Any,
    stop_causes: list[str],
) -> dict[str, Any] | None:
    """Validate review is a non-empty dict; return early-stop dict or None.

    Mutates stop_causes in place when a violation is found.

    Args:
        review: The review value to check.
        stop_causes: Running list of stop causes; appended to on violation.

    Returns:
        A stop-action dict if review is invalid; None if review is acceptable.
    """
    if review is None or not isinstance(review, dict):
        stop_causes.append(
            "non_json" if isinstance(review, str) else "reviewer_failure"
        )
        return {
            "action": "stop",
            "reason": "review is not a valid dict",
            "stop_causes": stop_causes,
        }
    if not review:
        stop_causes.append("malformed_review")
        return {
            "action": "stop",
            "reason": "review dict is empty",
            "stop_causes": stop_causes,
        }
    return None


def _check_local_verify_success(
    local_verify: Any,
    stop_causes: list[str],
) -> dict[str, Any] | None:
    """Validate local_verify is a dict and passes validate_local_verify.

    Mutates stop_causes in place when a violation is found.

    Args:
        local_verify: The local verification result to check.
        stop_causes: Running list of stop causes; appended to on violation.

    Returns:
        A stop-action dict if local_verify is invalid; None otherwise.
    """
    if local_verify is None or not isinstance(local_verify, dict):
        stop_causes.append("local_verify_fail")
        return {
            "action": "stop",
            "reason": "local_verify is not a valid dict",
            "stop_causes": stop_causes,
        }
    lv_errors = validate_local_verify(local_verify)
    if lv_errors:
        stop_causes.append("local_verify_fail")
        return {
            "action": "stop",
            "reason": f"local_verify errors: {lv_errors}",
            "stop_causes": stop_causes,
        }
    return None


def _check_review_schema(
    review: dict[str, Any],
    stop_causes: list[str],
) -> dict[str, Any] | None:
    """Run schema validation on review; return early-stop dict or None.

    Mutates stop_causes in place when a violation is found.

    Args:
        review: The review dict to validate.
        stop_causes: Running list of stop causes; appended to on violation.

    Returns:
        A stop-action dict if schema is invalid; None otherwise.
    """
    review_errors = validate_review_json(review)
    if review_errors:
        stop_causes.append("missing_schema_field")
        return {
            "action": "stop",
            "reason": f"review schema errors: {review_errors}",
            "stop_causes": stop_causes,
        }
    return None


def _check_review_policy(
    review: dict[str, Any],
    stop_causes: list[str],
    severity_is_stop_axis: bool,
    severity_auto_max: str,
) -> None:
    """Apply policy checks from review fields; append violations to stop_causes.

    Checks verdict, requires_user, hard_boundary_violation, and judgmental_decision.
    Severity is NOT a stop axis by default (the doctrine: at detection the problem is
    already identified, so findings self-heal in the FIX loop). Only an opted-in project
    (severity_is_stop_axis=True) turns a max_severity above severity_auto_max into a stop.

    Args:
        review: Validated review dict.
        stop_causes: Running list of stop causes; appended to on each violation.
        severity_is_stop_axis: When True, enable the opt-in severity gate.
        severity_auto_max: Highest severity that auto-proceeds when the gate is on.
    """
    verdict = review.get("verdict", "")
    if verdict not in _PASS_VERDICTS:
        stop_causes.append("verdict")

    if severity_is_stop_axis:
        max_severity = review.get("max_severity", "CRITICAL")
        if _severity_rank(max_severity) > _severity_rank(severity_auto_max):
            stop_causes.append("max_severity")

    if review.get("requires_user"):
        stop_causes.append("requires_user")

    if review.get("hard_boundary_violation"):
        stop_causes.append("hard_boundary")

    if review.get("judgmental_decision"):
        stop_causes.append("judgmental")


def _check_boundaries(
    changed_paths: list[str],
    diff_text: str | None,
    stop_causes: list[str],
) -> None:
    """Run path-based and content-based boundary scans; append to stop_causes.

    The gate's own scans override reviewer flags: if the gate detects a boundary
    violation, it appends a stop cause regardless of what the reviewer reported.

    Args:
        changed_paths: List of changed file paths for boundary scanning.
        diff_text: Raw diff text for content signal scanning.
        stop_causes: Running list of stop causes; appended to on each violation.
    """
    path_hits = scan_hard_boundaries(changed_paths)
    if path_hits:
        stop_causes.append("hard_boundary")

    diff_str = diff_text or ""
    content_hits = scan_content_boundaries(diff_str)
    if content_hits:
        stop_causes.append("content_boundary")


def _check_repeated_failure(
    prior_same_failures: int,
    stop_causes: list[str],
) -> None:
    """Append 'repeated_failure' to stop_causes if threshold exceeded.

    Args:
        prior_same_failures: Number of prior failures for the same task/stage.
        stop_causes: Running list of stop causes; appended to on violation.
    """
    if prior_same_failures >= 2:
        stop_causes.append("repeated_failure")


def _check_commit_stage(
    is_commit_stage: bool,
    allow_auto_commit: bool,
    stop_causes: list[str],
) -> None:
    """Append 'commit_stage' to stop_causes when commit guard is active.

    Args:
        is_commit_stage: True if this is a git commit gate check.
        allow_auto_commit: Must be True to allow auto_continue on commit stage.
        stop_causes: Running list of stop causes; appended to on violation.
    """
    if is_commit_stage and not allow_auto_commit:
        stop_causes.append("commit_stage")


def _apply_dry_run(
    would_auto: bool,
    stop_causes: list[str],
) -> dict[str, Any]:
    """Build and return the dry-run response dict (always action=stop).

    Appends 'dry_run' to stop_causes and returns the appropriate sentinel.

    Args:
        would_auto: Whether the gate would have returned auto_continue.
        stop_causes: Running list of stop causes (mutated: 'dry_run' appended).

    Returns:
        A stop-action dict with dry_run=True and would_action set accordingly.
    """
    stop_causes.append("dry_run")
    if would_auto:
        return {
            "action": "stop",
            "dry_run": True,
            "would_action": "auto_continue",
            "stop_causes": stop_causes,
            "reason": "dry_run mode: suppressing auto_continue",
        }
    return {
        "action": "stop",
        "dry_run": True,
        "would_action": "stop",
        "stop_causes": stop_causes,
        "reason": f"stop (dry_run): causes={stop_causes}",
    }


def decide_gate(
    review: Any,
    local_verify: Any,
    changed_paths: list[str],
    *,
    dry_run: bool = True,
    allow_auto_commit: bool = False,
    prior_same_failures: int = 0,
    is_commit_stage: bool = False,
    diff_text: str | None = None,
    severity_is_stop_axis: bool | None = None,
    severity_auto_max: str | None = None,
) -> dict[str, Any]:
    """Evaluate all gate conditions and return an action decision.

    Returns auto_continue only when ALL conditions are satisfied:
    - verdict in {PASS, PASS_WITH_NITS, CLOSE}
    - severity gate (opt-in only): when severity_is_stop_axis, max_severity <= severity_auto_max
    - requires_user is False
    - hard_boundary_violation is False
    - validate_review_json() returns no errors
    - validate_local_verify() returns no errors
    - local_verify.claimed_equals_actual is True
    - ruff/black/mypy values are success values
    - pytest actual.failed == 0 and actual.errors == 0
    - scan_hard_boundaries(changed_paths) is empty
    - scan_content_boundaries(diff_text) is empty
    - no judgmental_decision flag
    - prior_same_failures < 2
    - not (is_commit_stage and not allow_auto_commit)
    - dry_run is False

    Args:
        review: Reviewer review dict (or None/sentinel for failure cases).
        local_verify: Local verification result dict (or None).
        changed_paths: List of changed file paths for boundary scanning.
        dry_run: If True, suppresses auto_continue and returns would_action.
        allow_auto_commit: Must be True to auto_continue on commit stage.
        prior_same_failures: Count of repeated failures for same task/stage.
        is_commit_stage: True if this is a git commit gate check.
        diff_text: Raw diff text for content boundary scanning.
        severity_is_stop_axis: Opt-in severity gate switch. None -> read .harness.toml
            [review_overlay] (default False: severity is NOT a stop axis).
        severity_auto_max: Highest severity that auto-proceeds when the gate is on. None ->
            read .harness.toml (default "MEDIUM"). Only used when severity_is_stop_axis.

    Returns:
        Dict with keys: action, reason, stop_causes (always).
        When dry_run=True and would-be auto: also dry_run=True, would_action.
    """
    stop_causes: list[str] = []

    # Early-return guards (invalid inputs)
    early = _validate_review_input(review, stop_causes)
    if early is not None:
        return early

    early = _check_local_verify_success(local_verify, stop_causes)
    if early is not None:
        return early

    early = _check_review_schema(review, stop_causes)
    if early is not None:
        return early

    # Severity gate knobs: explicit args win; otherwise read .harness.toml (default: off,
    # i.e. severity is not a stop axis — findings self-heal in the FIX loop).
    if severity_is_stop_axis is None or severity_auto_max is None:
        cfg_is_stop, cfg_max = load_severity_gate()
        if severity_is_stop_axis is None:
            severity_is_stop_axis = cfg_is_stop
        if severity_auto_max is None:
            severity_auto_max = cfg_max

    # Policy checks - each appends to stop_causes but does NOT early-return,
    # so all stop causes are collected before the final decision.
    _check_review_policy(review, stop_causes, severity_is_stop_axis, severity_auto_max)
    _check_boundaries(changed_paths, diff_text, stop_causes)
    _check_repeated_failure(prior_same_failures, stop_causes)
    _check_commit_stage(is_commit_stage, allow_auto_commit, stop_causes)

    would_auto = len(stop_causes) == 0

    if dry_run:
        return _apply_dry_run(would_auto, stop_causes)

    if would_auto:
        return {
            "action": "auto_continue",
            "reason": "all gate conditions satisfied",
            "stop_causes": [],
        }

    return {
        "action": "stop",
        "reason": f"gate blocked: {stop_causes}",
        "stop_causes": stop_causes,
    }
