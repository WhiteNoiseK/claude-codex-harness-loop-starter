"""Unit tests for scripts/auto_gate.py - the automated quality-gate engine.

Covers decide_gate policy (15+ rules), scan_hard_boundaries,
scan_content_boundaries, validate_review_json, validate_local_verify.

These tests exercise the GENERIC defaults the kit ships
(DEFAULT_BOUNDARY_PATTERNS / DEFAULT_CONTENT_SIGNALS). Projects override the
boundary list via .harness.toml [safety_boundary] paths or by passing patterns
explicitly; that override path is covered by the parametrized scan tests.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

# scripts/ import path - this test lives at tests/unit/, so the kit root is parents[2].
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from auto_gate import (  # noqa: E402  (scripts/ on sys.path above; not an installed package)
    SEVERITY_ORDER,
    decide_gate,
    scan_content_boundaries,
    scan_hard_boundaries,
    validate_local_verify,
    validate_review_json,
)

# ---------------------------------------------------------------------------
# Shared minimal fixtures
# ---------------------------------------------------------------------------

PASS_REVIEW: dict[str, Any] = {
    "prompt_id": "M1-EXAMPLE-01_RED_20260101_01",
    "task_id": "M1-EXAMPLE-01",
    "stage": "RED",
    "verdict": "PASS",
    "max_severity": "LOW",
    "requires_user": False,
    "hard_boundary_violation": False,
    "findings": [],
    "next_action": "auto_continue",
    "notes": "all good",
    "reply_prompt_id": "M1-EXAMPLE-01_RED_20260101_02",
    "rerun_performed": True,
}

PASS_LOCAL_VERIFY: dict[str, Any] = {
    "pytest": {
        "claimed": {"passed": 10, "failed": 0},
        "actual": {"passed": 10, "failed": 0},
    },
    "ruff": "ok",
    "black": "ok",
    "mypy": "ok",
    "claimed_equals_actual": True,
    "commands_run": ["pytest", "ruff", "black", "mypy"],
    "scope": "tests/unit/test_auto_gate.py",
}

# Safe (non-boundary) paths under the kit's default safe prefixes.
NON_BOUNDARY_PATHS = [
    "src/services/widget_service.py",
    "docs/ai-workflow/progress.md",
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_review(**overrides: Any) -> dict[str, Any]:
    """Return a copy of PASS_REVIEW with overrides applied."""
    r = dict(PASS_REVIEW)
    r.update(overrides)
    return r


def _make_lv(**overrides: Any) -> dict[str, Any]:
    """Return a copy of PASS_LOCAL_VERIFY with overrides applied."""
    lv = dict(PASS_LOCAL_VERIFY)
    # deep-copy the nested pytest dict so mutations don't bleed
    lv["pytest"] = dict(lv["pytest"])
    lv["pytest"]["claimed"] = dict(lv["pytest"]["claimed"])
    lv["pytest"]["actual"] = dict(lv["pytest"]["actual"])
    lv.update(overrides)
    return lv


# ===========================================================================
# Section A - decide_gate (15+ policies)
# ===========================================================================


@pytest.mark.unit
def test_decide_gate_pass_low_local_verify_ok_returns_auto_continue() -> None:
    """Policy 1: PASS + LOW severity + local_verify OK -> auto_continue."""
    result = decide_gate(
        PASS_REVIEW,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
    )
    assert result["action"] == "auto_continue"


@pytest.mark.unit
def test_decide_gate_pass_low_local_verify_fail_claimed_not_equal_actual_returns_stop() -> (
    None
):
    """Policy 2: PASS + LOW + local_verify claimed != actual -> stop."""
    lv = _make_lv(
        claimed_equals_actual=False,
    )
    lv["pytest"]["actual"] = {"passed": 9, "failed": 1}
    result = decide_gate(
        PASS_REVIEW,
        lv,
        NON_BOUNDARY_PATHS,
        dry_run=False,
    )
    assert result["action"] == "stop"


@pytest.mark.unit
def test_decide_gate_pass_low_hard_boundary_path_touched_returns_stop() -> None:
    """Policy 3: PASS + LOW + changed_paths includes hard boundary -> stop."""
    boundary_path = "src/db/migrations/0001_init.py"
    result = decide_gate(
        PASS_REVIEW,
        PASS_LOCAL_VERIFY,
        [boundary_path],
        dry_run=False,
    )
    assert result["action"] == "stop"


@pytest.mark.unit
def test_decide_gate_review_hard_boundary_false_but_changed_paths_boundary_returns_stop() -> (
    None
):
    """Policy 4: review.hard_boundary_violation=False but gate scans paths -> stop."""
    review = _make_review(hard_boundary_violation=False)
    boundary_path = "alembic/versions/001_init.py"
    result = decide_gate(
        review,
        PASS_LOCAL_VERIFY,
        [boundary_path],
        dry_run=False,
    )
    assert result["action"] == "stop"


@pytest.mark.unit
@pytest.mark.parametrize("severity", ["MEDIUM", "HIGH", "CRITICAL"])
def test_decide_gate_high_severity_default_off_returns_auto_continue(
    severity: str,
) -> None:
    """Policy 5 (doctrine): severity is NOT a stop axis by default. At detection the
    problem is already identified, so even CRITICAL findings self-heal in the FIX loop;
    a PASS review with high max_severity auto-continues when severity_is_stop_axis=False.
    """
    review = _make_review(max_severity=severity)
    result = decide_gate(
        review,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
        severity_is_stop_axis=False,
    )
    assert result["action"] == "auto_continue"


@pytest.mark.unit
@pytest.mark.parametrize("severity", ["HIGH", "CRITICAL"])
def test_decide_gate_severity_gate_optin_above_threshold_returns_stop(
    severity: str,
) -> None:
    """Opt-in: with severity_is_stop_axis=True and severity_auto_max='MEDIUM', a finding
    above the threshold (HIGH/CRITICAL) pauses for a human via the 'max_severity' stop.
    """
    review = _make_review(max_severity=severity)
    result = decide_gate(
        review,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
        severity_is_stop_axis=True,
        severity_auto_max="MEDIUM",
    )
    assert result["action"] == "stop"
    assert "max_severity" in result["stop_causes"]


@pytest.mark.unit
@pytest.mark.parametrize("severity", ["LOW", "MEDIUM"])
def test_decide_gate_severity_gate_optin_at_or_below_threshold_auto_continues(
    severity: str,
) -> None:
    """Opt-in: a finding at or below severity_auto_max still auto-continues."""
    review = _make_review(max_severity=severity)
    result = decide_gate(
        review,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
        severity_is_stop_axis=True,
        severity_auto_max="MEDIUM",
    )
    assert result["action"] == "auto_continue"


@pytest.mark.unit
@pytest.mark.parametrize("verdict", ["BLOCKED", "ADJUST", "RE_OPEN"])
def test_decide_gate_non_pass_verdict_returns_stop(verdict: str) -> None:
    """Policy 6: verdict BLOCKED/ADJUST/RE_OPEN -> stop."""
    review = _make_review(verdict=verdict)
    result = decide_gate(
        review,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
    )
    assert result["action"] == "stop"


@pytest.mark.unit
def test_decide_gate_requires_user_true_returns_stop() -> None:
    """Policy 7: requires_user=True -> stop."""
    review = _make_review(requires_user=True)
    result = decide_gate(
        review,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
    )
    assert result["action"] == "stop"


@pytest.mark.unit
def test_decide_gate_malformed_review_returns_stop() -> None:
    """Policy 8: malformed/None review -> stop."""
    result_none = decide_gate(
        None,  # type: ignore[arg-type]
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
    )
    assert result_none["action"] == "stop"

    result_empty = decide_gate(
        {},
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
    )
    assert result_empty["action"] == "stop"


@pytest.mark.unit
def test_decide_gate_reviewer_exec_failure_review_none_returns_stop() -> None:
    """Policy 9: reviewer exec failure represented as review=None -> stop."""
    result = decide_gate(
        None,  # type: ignore[arg-type]
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
    )
    assert result["action"] == "stop"
    assert len(result["stop_causes"]) >= 1


@pytest.mark.unit
def test_decide_gate_prior_same_failures_ge_2_returns_stop() -> None:
    """Policy 10: prior_same_failures >= 2 -> stop."""
    result = decide_gate(
        PASS_REVIEW,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
        prior_same_failures=2,
    )
    assert result["action"] == "stop"


@pytest.mark.unit
def test_decide_gate_judgmental_decision_flag_true_returns_stop() -> None:
    """Policy 11: judgmental_decision flag in review -> stop."""
    review = _make_review(judgmental_decision=True)
    result = decide_gate(
        review,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
    )
    assert result["action"] == "stop"


# ---------------------------------------------------------------------------
# B1 - dry_run contract hardening
# decide_gate with dry_run=True on an otherwise-auto case must:
#   1. result["action"] == "stop"  (no real auto_continue ever fires)
#   2. result["dry_run"] is True
#   3. result["would_action"] == "auto_continue"
#   4. "dry_run" in result["stop_causes"]
#   5. no files written (tmp_path remains empty)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_decide_gate_dry_run_action_is_stop() -> None:
    """B1-1: dry_run=True on otherwise-auto case -> action==stop (not auto_continue)."""
    result = decide_gate(
        PASS_REVIEW,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=True,
    )
    assert (
        result["action"] == "stop"
    ), "dry_run=True must suppress auto_continue and return action=stop"


@pytest.mark.unit
def test_decide_gate_dry_run_flag_present_in_result() -> None:
    """B1-2: dry_run=True -> result['dry_run'] is True."""
    result = decide_gate(
        PASS_REVIEW,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=True,
    )
    assert result.get("dry_run") is True


@pytest.mark.unit
def test_decide_gate_dry_run_would_action_is_auto_continue() -> None:
    """B1-3: dry_run=True on otherwise-auto case -> would_action==auto_continue."""
    result = decide_gate(
        PASS_REVIEW,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=True,
    )
    assert (
        result.get("would_action") == "auto_continue"
    ), "dry_run result must expose the action that would have been taken"


@pytest.mark.unit
def test_decide_gate_dry_run_stop_causes_contains_dry_run() -> None:
    """B1-4: dry_run=True -> 'dry_run' in result['stop_causes']."""
    result = decide_gate(
        PASS_REVIEW,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=True,
    )
    assert "dry_run" in result.get(
        "stop_causes", []
    ), "stop_causes must contain 'dry_run' when dry_run=True"


@pytest.mark.unit
def test_decide_gate_dry_run_no_side_effects(tmp_path: Path) -> None:
    """B1-5: dry_run=True -> no files written (tmp_path stays empty)."""
    result = decide_gate(
        PASS_REVIEW,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=True,
    )
    assert "action" in result
    assert list(tmp_path.iterdir()) == []


@pytest.mark.unit
def test_decide_gate_is_commit_stage_allow_auto_commit_false_returns_stop() -> None:
    """Policy 13: is_commit_stage=True + allow_auto_commit=False -> stop."""
    result = decide_gate(
        PASS_REVIEW,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
        allow_auto_commit=False,
        is_commit_stage=True,
    )
    assert result["action"] == "stop"


@pytest.mark.unit
def test_decide_gate_non_json_reviewer_output_returns_stop() -> None:
    """Policy 14: non-JSON reviewer output sentinel -> stop."""
    # Simulate non-JSON as a special sentinel string in review
    non_json_review = "<<< NOT VALID JSON: parse error >>>"
    result = decide_gate(
        non_json_review,  # type: ignore[arg-type]
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
    )
    assert result["action"] == "stop"


@pytest.mark.unit
def test_decide_gate_missing_required_schema_fields_returns_stop() -> None:
    """Policy 15: review missing required schema fields -> stop."""
    incomplete_review = {"verdict": "PASS"}  # missing most required fields
    result = decide_gate(
        incomplete_review,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
    )
    assert result["action"] == "stop"


# ===========================================================================
# Section B - scan_hard_boundaries (generic default patterns)
# ===========================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    "boundary_path",
    [
        "src/db/migrations/0001_init.py",
        "app/migrations/0002_add.py",
        "alembic/versions/0001_init.py",
        "alembic/env.py",
        "src/core/db_schema.py",
        "src/models/user_schema.py",
        ".env",
        ".env.production",
        "config_secret.yaml",
        "src/secrets_loader.py",
        "deploy/release.sh",
        "src/services/order_processor.py",
    ],
)
def test_scan_hard_boundaries_boundary_path_returns_match(boundary_path: str) -> None:
    """Boundary paths must be detected as hard boundary violations."""
    matches = scan_hard_boundaries([boundary_path])
    assert len(matches) >= 1, f"Expected match for boundary path: {boundary_path}"


@pytest.mark.unit
@pytest.mark.parametrize(
    "safe_path",
    [
        "src/services/widget_service.py",
        "docs/ai-workflow/progress.md",
        "docs/ai-workflow/handoffs/codex_R0_DESIGN_M1-EXAMPLE-01_20260101.md",
        "tests/unit/test_auto_gate.py",
        "scripts/auto_gate.py",
        ".env.example",
    ],
)
def test_scan_hard_boundaries_non_boundary_path_returns_no_match(
    safe_path: str,
) -> None:
    """Non-boundary paths must not trigger hard boundary detection."""
    matches = scan_hard_boundaries([safe_path])
    assert matches == [], f"Expected no match for safe path: {safe_path}"


@pytest.mark.unit
def test_scan_hard_boundaries_mixed_paths_returns_only_boundary_matches() -> None:
    """Only boundary paths from a mixed list should be returned."""
    paths = [
        "src/services/widget_service.py",  # safe
        "src/core/db_schema.py",  # boundary
        "docs/ai-workflow/progress.md",  # safe
        "alembic/versions/0001_init.py",  # boundary
    ]
    matches = scan_hard_boundaries(paths)
    assert "src/core/db_schema.py" in matches
    assert "alembic/versions/0001_init.py" in matches
    assert "src/services/widget_service.py" not in matches
    assert "docs/ai-workflow/progress.md" not in matches


@pytest.mark.unit
def test_scan_hard_boundaries_empty_list_returns_empty() -> None:
    """Empty changed_paths must return empty list (no crash)."""
    assert scan_hard_boundaries([]) == []


@pytest.mark.unit
def test_scan_hard_boundaries_explicit_patterns_override_defaults() -> None:
    """Custom patterns argument must override the generic defaults.

    Projects supply their own safety boundary via .harness.toml or by passing
    patterns explicitly; this confirms the override seam works.
    """
    custom = ["src/hw_driver/**"]
    # A path that is NOT in the generic defaults but matches the custom pattern.
    matches = scan_hard_boundaries(["src/hw_driver/fpga_adapter.py"], patterns=custom)
    assert matches == ["src/hw_driver/fpga_adapter.py"]
    # A generic-default boundary is NOT flagged when custom patterns replace it.
    assert scan_hard_boundaries(["alembic/env.py"], patterns=custom) == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "boundary_path",
    [
        "src/core/db_schema.py",
        "alembic/versions/0001_init.py",
    ],
)
def test_decide_gate_boundary_path_returns_stop(boundary_path: str) -> None:
    """A boundary path in changed_paths forces stop regardless of reviewer flag.

    Even when the reviewer says hard_boundary_violation=False, the gate's own
    path scan must catch safety-critical files.
    """
    review = _make_review(hard_boundary_violation=False)
    result = decide_gate(
        review,
        PASS_LOCAL_VERIFY,
        [boundary_path],
        dry_run=False,
    )
    assert (
        result["action"] == "stop"
    ), f"Boundary path {boundary_path!r} must force stop regardless of reviewer flag"


# ===========================================================================
# Section B2b - scan_content_boundaries (content-based safety detection)
# ===========================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    "signal",
    [
        "SAFETY",
        "SHUTDOWN",
        "target_state",
    ],
)
def test_scan_content_boundaries_safety_signal_returns_match(signal: str) -> None:
    """diff_text containing a safety signal must return a non-empty match list."""
    diff_text = f"- old line\n+ new line with {signal} here\n"
    matches = scan_content_boundaries(diff_text)
    assert len(matches) >= 1, f"Expected content boundary match for signal: {signal!r}"


@pytest.mark.unit
@pytest.mark.parametrize(
    "clean_diff",
    [
        "- old_value = 42\n+ old_value = 43\n",
        "+ def process_widget():\n+     pass\n",
        "- logging.info('start')\n+ logging.info('begin')\n",
    ],
)
def test_scan_content_boundaries_clean_diff_returns_empty(clean_diff: str) -> None:
    """diff_text without safety signals must return an empty match list."""
    matches = scan_content_boundaries(clean_diff)
    assert matches == [], "Expected no content boundary match for clean diff"


@pytest.mark.unit
def test_scan_content_boundaries_empty_string_returns_empty() -> None:
    """scan_content_boundaries on empty string must return empty list (no crash)."""
    assert scan_content_boundaries("") == []


@pytest.mark.unit
def test_scan_content_boundaries_explicit_signals_override_defaults() -> None:
    """Custom signals argument must override the generic defaults."""
    custom = ["AlarmSeverity.CRITICAL"]
    diff_text = "+ raise AlarmSeverity.CRITICAL\n"
    assert scan_content_boundaries(diff_text, signals=custom) == [
        "AlarmSeverity.CRITICAL"
    ]
    # A generic-default signal is NOT flagged when custom signals replace it.
    assert scan_content_boundaries("+ SHUTDOWN now\n", signals=custom) == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "signal",
    [
        "SAFETY",
        "SHUTDOWN",
        "target_state",
    ],
)
def test_decide_gate_diff_text_safety_signal_returns_stop(signal: str) -> None:
    """diff_text with a safety signal -> stop even if reviewer flag is False."""
    review = _make_review(hard_boundary_violation=False)
    diff_text = f"+ modified_field = {signal}\n"
    result = decide_gate(
        review,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
        diff_text=diff_text,
    )
    assert (
        result["action"] == "stop"
    ), f"Safety content signal {signal!r} must force stop regardless of reviewer flag"


@pytest.mark.unit
def test_decide_gate_reviewer_flag_false_but_content_safety_signal_gate_wins() -> None:
    """Reviewer hard_boundary_violation=False is overridden by gate content scan."""
    review = _make_review(hard_boundary_violation=False, verdict="PASS")
    diff_text = "- normal_path()\n+ enter SHUTDOWN sequence\n"
    result = decide_gate(
        review,
        PASS_LOCAL_VERIFY,
        NON_BOUNDARY_PATHS,
        dry_run=False,
        diff_text=diff_text,
    )
    assert result["action"] == "stop"


# ===========================================================================
# Section C - validate_review_json
# ===========================================================================

REQUIRED_REVIEW_FIELDS = [
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


@pytest.mark.unit
def test_validate_review_json_valid_review_returns_empty_errors() -> None:
    """A fully valid review dict must return zero errors."""
    errors = validate_review_json(PASS_REVIEW)
    assert errors == []


@pytest.mark.unit
@pytest.mark.parametrize("missing_field", REQUIRED_REVIEW_FIELDS)
def test_validate_review_json_missing_required_field_returns_error(
    missing_field: str,
) -> None:
    """Each missing required field must produce at least one error."""
    review = dict(PASS_REVIEW)
    del review[missing_field]
    errors = validate_review_json(review)
    assert len(errors) >= 1, f"Expected error for missing field: {missing_field}"


@pytest.mark.unit
@pytest.mark.parametrize("bad_verdict", ["OK", "SKIPPED", "UNKNOWN", "", "pass"])
def test_validate_review_json_invalid_verdict_enum_returns_error(
    bad_verdict: str,
) -> None:
    """Verdict values outside the allowed enum must produce an error."""
    review = _make_review(verdict=bad_verdict)
    errors = validate_review_json(review)
    assert len(errors) >= 1, f"Expected error for invalid verdict: {bad_verdict!r}"


@pytest.mark.unit
@pytest.mark.parametrize("bad_severity", ["EXTREME", "BLOCKER", "", "low"])
def test_validate_review_json_invalid_max_severity_enum_returns_error(
    bad_severity: str,
) -> None:
    """max_severity values outside the allowed enum must produce an error."""
    review = _make_review(max_severity=bad_severity)
    errors = validate_review_json(review)
    assert len(errors) >= 1, f"Expected error for invalid severity: {bad_severity!r}"


@pytest.mark.unit
def test_validate_review_json_finding_missing_severity_returns_error() -> None:
    """A finding without 'severity' must produce an error."""
    review = _make_review(findings=[{"summary": "oops", "required_action": "fix it"}])
    errors = validate_review_json(review)
    assert len(errors) >= 1


@pytest.mark.unit
def test_validate_review_json_finding_missing_summary_returns_error() -> None:
    """A finding without 'summary' must produce an error."""
    review = _make_review(findings=[{"severity": "HIGH", "required_action": "fix it"}])
    errors = validate_review_json(review)
    assert len(errors) >= 1


@pytest.mark.unit
def test_validate_review_json_finding_missing_required_action_returns_error() -> None:
    """A finding without 'required_action' must produce an error."""
    review = _make_review(findings=[{"severity": "HIGH", "summary": "something bad"}])
    errors = validate_review_json(review)
    assert len(errors) >= 1


@pytest.mark.unit
def test_validate_review_json_rerun_performed_false_is_allowed() -> None:
    """rerun_performed=False alone must not produce a validation error."""
    review = _make_review(rerun_performed=False)
    errors = validate_review_json(review)
    assert errors == []


# ===========================================================================
# Section D - validate_local_verify (parametrize each missing command)
# ===========================================================================

REQUIRED_LV_FIELDS = [
    "pytest",
    "ruff",
    "black",
    "mypy",
    "claimed_equals_actual",
    "commands_run",
    "scope",
]


@pytest.mark.unit
def test_validate_local_verify_valid_returns_empty_errors() -> None:
    """A fully valid local_verify dict must return zero errors."""
    errors = validate_local_verify(PASS_LOCAL_VERIFY)
    assert errors == []


@pytest.mark.unit
@pytest.mark.parametrize("missing_field", REQUIRED_LV_FIELDS)
def test_validate_local_verify_missing_field_returns_error(missing_field: str) -> None:
    """Each missing required field must produce at least one error."""
    lv = dict(PASS_LOCAL_VERIFY)
    del lv[missing_field]
    errors = validate_local_verify(lv)
    assert len(errors) >= 1, f"Expected error for missing field: {missing_field}"


@pytest.mark.unit
def test_validate_local_verify_claimed_equals_actual_false_returns_error() -> None:
    """claimed_equals_actual=False must produce at least one error."""
    lv = _make_lv(claimed_equals_actual=False)
    errors = validate_local_verify(lv)
    assert len(errors) >= 1


@pytest.mark.unit
@pytest.mark.parametrize(
    "missing_cmd,remaining",
    [
        ("pytest", ["ruff", "black", "mypy"]),
        ("ruff", ["pytest", "black", "mypy"]),
        ("black", ["pytest", "ruff", "mypy"]),
        ("mypy", ["pytest", "ruff", "black"]),
    ],
)
def test_validate_local_verify_missing_required_command_each_returns_error(
    missing_cmd: str,
    remaining: list[str],
) -> None:
    """Each of pytest/ruff/black/mypy absent from commands_run -> error."""
    lv = _make_lv(commands_run=remaining)
    errors = validate_local_verify(lv)
    assert (
        len(errors) >= 1
    ), f"Expected error when required command '{missing_cmd}' is absent"


@pytest.mark.unit
def test_validate_local_verify_missing_required_command_returns_error() -> None:
    """commands_run missing 'pytest' must produce an error (backward compat)."""
    lv = _make_lv(commands_run=["ruff", "black"])  # pytest and mypy both missing
    errors = validate_local_verify(lv)
    assert len(errors) >= 1


@pytest.mark.unit
def test_validate_local_verify_pytest_claimed_actual_mismatch_returns_error() -> None:
    """pytest claimed vs actual count mismatch must produce an error."""
    lv = _make_lv()
    lv["pytest"]["claimed"] = {"passed": 10, "failed": 0}
    lv["pytest"]["actual"] = {"passed": 8, "failed": 2}
    errors = validate_local_verify(lv)
    assert len(errors) >= 1


@pytest.mark.unit
@pytest.mark.parametrize(
    "missing_cmd,remaining",
    [
        ("pytest", ["ruff", "black", "mypy"]),
        ("ruff", ["pytest", "black", "mypy"]),
        ("black", ["pytest", "ruff", "mypy"]),
        ("mypy", ["pytest", "ruff", "black"]),
    ],
)
def test_decide_gate_missing_required_command_returns_stop(
    missing_cmd: str,
    remaining: list[str],
) -> None:
    """decide_gate stops when any of pytest/ruff/black/mypy is absent."""
    lv = _make_lv(commands_run=remaining)
    result = decide_gate(PASS_REVIEW, lv, NON_BOUNDARY_PATHS, dry_run=False)
    assert (
        result["action"] == "stop"
    ), f"Missing command '{missing_cmd}' must cause decide_gate to stop"


# ===========================================================================
# Section E - SEVERITY_ORDER sanity
# ===========================================================================


@pytest.mark.unit
def test_severity_order_contains_all_levels() -> None:
    """SEVERITY_ORDER must contain NONE, INFO, NIT, LOW, MEDIUM, HIGH, CRITICAL in order."""
    expected = ["NONE", "INFO", "NIT", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    for level in expected:
        assert level in SEVERITY_ORDER, f"Missing severity level: {level}"


@pytest.mark.unit
def test_severity_order_is_strictly_ascending() -> None:
    """CRITICAL must rank higher than LOW; LOW must rank higher than NONE."""
    assert SEVERITY_ORDER.index("CRITICAL") > SEVERITY_ORDER.index("HIGH")
    assert SEVERITY_ORDER.index("HIGH") > SEVERITY_ORDER.index("MEDIUM")
    assert SEVERITY_ORDER.index("MEDIUM") > SEVERITY_ORDER.index("LOW")
    assert SEVERITY_ORDER.index("LOW") > SEVERITY_ORDER.index("NONE")


# ===========================================================================
# Section F - decide_gate boundary/timeout edge cases
# ===========================================================================


@pytest.mark.unit
@pytest.mark.timeout(5)
def test_decide_gate_returns_within_timeout_with_large_paths_list() -> None:
    """decide_gate must complete within 5 seconds even with 1000 paths."""
    paths = ["src/services/widget_service.py"] * 1000
    result = decide_gate(PASS_REVIEW, PASS_LOCAL_VERIFY, paths, dry_run=False)
    assert result["action"] == "auto_continue"


@pytest.mark.unit
def test_decide_gate_result_always_has_required_keys() -> None:
    """decide_gate result must always contain action, reason, stop_causes."""
    result = decide_gate(PASS_REVIEW, PASS_LOCAL_VERIFY, NON_BOUNDARY_PATHS)
    assert "action" in result
    assert "reason" in result
    assert "stop_causes" in result
    assert isinstance(result["stop_causes"], list)


@pytest.mark.unit
def test_decide_gate_stop_causes_populated_when_action_is_stop() -> None:
    """When action==stop, stop_causes must be non-empty."""
    review = _make_review(verdict="BLOCKED")
    result = decide_gate(review, PASS_LOCAL_VERIFY, NON_BOUNDARY_PATHS, dry_run=False)
    assert result["action"] == "stop"
    assert len(result["stop_causes"]) >= 1


@pytest.mark.unit
def test_decide_gate_local_verify_none_returns_stop() -> None:
    """local_verify=None (no verification data) must cause stop."""
    result = decide_gate(
        PASS_REVIEW,
        None,  # type: ignore[arg-type]
        NON_BOUNDARY_PATHS,
        dry_run=False,
    )
    assert result["action"] == "stop"


# ===========================================================================
# Section G - local_verify tool-result value validation
# validate_local_verify must reject failure values for ruff/black/mypy.
# decide_gate must stop when any tool reports failure.
# ===========================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("ruff", "failed"),
        ("black", "failed"),
        ("mypy", "failed"),
        ("ruff", "fail"),
        ("ruff", "error"),
        ("ruff", "unknown"),
        ("ruff", ""),
        ("ruff", None),
    ],
)
def test_validate_local_verify_tool_failure_value_returns_error(
    field: str, bad_value: Any
) -> None:
    """G1: ruff/black/mypy failure values must produce at least one error."""
    lv = _make_lv(**{field: bad_value})
    errors = validate_local_verify(lv)
    assert len(errors) >= 1, (
        f"Expected error when {field}={bad_value!r} (failure value) "
        "but validate_local_verify returned no errors"
    )


@pytest.mark.unit
def test_validate_local_verify_success_value_does_not_produce_error() -> None:
    """G1 positive: ruff/black/mypy = 'ok' must produce zero errors (regression)."""
    lv = _make_lv(ruff="ok", black="ok", mypy="ok")
    errors = validate_local_verify(lv)
    assert errors == [], f"Expected no errors for all-ok values but got: {errors}"


@pytest.mark.unit
@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("ruff", "failed"),
        ("black", "failed"),
        ("mypy", "failed"),
    ],
)
def test_decide_gate_tool_failure_value_returns_stop(
    field: str, bad_value: Any
) -> None:
    """G1: decide_gate must stop when ruff/black/mypy reports a failure value."""
    lv = _make_lv(**{field: bad_value})
    result = decide_gate(
        PASS_REVIEW,
        lv,
        NON_BOUNDARY_PATHS,
        dry_run=False,
    )
    assert result["action"] == "stop", (
        f"Expected stop when {field}={bad_value!r} but got action="
        f"{result['action']!r} (tool failure not checked)"
    )


@pytest.mark.unit
def test_decide_gate_pytest_actual_failed_nonzero_returns_stop() -> None:
    """G1: decide_gate must stop when pytest actual failed count > 0.

    _make_lv sets claimed==actual by default; we change actual.failed=1 and
    keep claimed_equals_actual=True to isolate the value check.
    """
    lv = _make_lv()
    lv["pytest"]["actual"] = {"passed": 9, "failed": 1}
    lv["pytest"]["claimed"] = {"passed": 9, "failed": 1}
    lv["claimed_equals_actual"] = True
    result = decide_gate(
        PASS_REVIEW,
        lv,
        NON_BOUNDARY_PATHS,
        dry_run=False,
    )
    assert result["action"] == "stop", (
        "Expected stop when pytest actual.failed=1 even if claimed==actual "
        f"but got action={result['action']!r}"
    )


@pytest.mark.unit
def test_decide_gate_pytest_actual_errors_nonzero_returns_stop() -> None:
    """G1: decide_gate must stop when pytest actual errors count > 0.

    The errors key is distinct from failed.
    """
    lv = _make_lv()
    lv["pytest"]["actual"] = {"passed": 10, "failed": 0, "errors": 1}
    lv["pytest"]["claimed"] = {"passed": 10, "failed": 0, "errors": 1}
    lv["claimed_equals_actual"] = True
    result = decide_gate(
        PASS_REVIEW,
        lv,
        NON_BOUNDARY_PATHS,
        dry_run=False,
    )
    assert result["action"] == "stop", (
        "Expected stop when pytest actual.errors=1 "
        f"but got action={result['action']!r}"
    )
