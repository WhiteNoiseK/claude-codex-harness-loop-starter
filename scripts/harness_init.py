#!/usr/bin/env python3
"""harness_init.py — harness starter-kit settling step (idempotent · dry-run-able).

Phase change (important)
------------------------
  init is no longer a "break-if-absent prerequisite". The scripts (harness_audit_rerun.py /
  harness_run_verify.sh / harness_status.sh) read .harness.toml at *runtime* via
  _harness_config.py, but still work on sensible defaults even if the file is missing.
  init is merely a "nice-to-have settling step", not a single point of failure.

What this script does (recommended to run once right after clone — the gate works even if you don't)
---------------------------------------------------------------------------------------------------
  (a) collect/derive config → create/update .harness.toml
        SRC_ROOT / TESTS_ROOT / SCORES_DIR / PROGRESS_FILE / TASK_ID_REGEX /
        COV_THRESHOLD (default 80) / AUDIT_THRESHOLD (default 95) / language profile.
        With --non-interactive, it uses the existing .harness.toml values/defaults as-is.
  (b) prerequisite check — verify the PreToolUse hook is registered in .claude/settings.json +
        the global prerequisites exist (a vendored copy of quality-gates.md + the global agents
        code-reviewer/security-reviewer/planner/architect).
        If any are missing, **fail loudly** (exit 3) — prevents silent neutralization.
  (c) baseline snapshot — copy the current config into .harness/baseline/
        (the drift-diff reference point; for the DRIFT_LOCK.md baseline ritual).

  Note: the first kit's {{PLACEHOLDER}} token in-place substitution step has been removed.
  Because the scripts read config at runtime, there is no longer any need to rewrite files
  (single point of failure removed).

Design principles
-----------------
  * Small: standard library only. TOML writes are line-by-line substitution (comment-preserving).
  * idempotent: same result no matter how many times you run it.
  * dry-run: --dry-run prints the plan without actually writing.

Usage
-----
    python scripts/harness_init.py                 # interactive
    python scripts/harness_init.py --non-interactive
    python scripts/harness_init.py --dry-run       # preview changes
    python scripts/harness_init.py --skip-prereq   # skip the prerequisite check (not recommended)

Exit codes
----------
    0  success   2  user input error   3  missing prerequisite (loud failure)
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

try:  # Python 3.11+ standard. If absent, fall back to the mini parser.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

# ── Path anchors (relative to this file — repo root = parent of scripts/) ──────
ROOT = Path(__file__).resolve().parent.parent
HARNESS_TOML = ROOT / ".harness.toml"
SETTINGS_JSON = ROOT / ".claude" / "settings.json"
VENDORED_QG = ROOT / "docs" / "_harness" / "quality-gates.md"
BASELINE_DIR = ROOT / ".harness" / "baseline"

# Global prerequisites — without them the harness is silently neutralized (aligns with the TEMPLATE_MANIFEST global-prerequisite table)
GLOBAL_AGENTS_DIR = Path.home() / ".claude" / "agents"
REQUIRED_GLOBAL_AGENTS = ("code-reviewer", "security-reviewer", "planner", "architect")

# Config defaults (defaults for the interactive prompts)
DEFAULTS = {
    "src_root": "src",
    "tests_root": "tests",
    "scores_dir": "docs/ai-workflow/scores",
    "progress_file": "docs/ai-workflow/progress.md",
    "task_id_regex": r"\((M\d+(?:-[A-Za-z0-9]+)+)\)",  # multi-segment (aligns with DRIFT-FIX)
    "coverage_threshold": "80",
    "audit_threshold": "95",
    "review_threshold": "95",
    "language_profile": "python",
    "docstring_lang": "en",  # default English; Korean (or other) projects set docstring_lang accordingly.
    "test_cmd": "python -m pytest",
    "type_cmd": "python -m mypy --strict --explicit-package-bases --ignore-missing-imports",
    "lint_cmd": "python -m ruff check",
}


# ════════════════════════════════════════════════════════════════════════════
#  read .harness.toml (tomllib or the mini parser)
# ════════════════════════════════════════════════════════════════════════════
def _mini_toml_read(text: str) -> dict[str, dict[str, str]]:
    """Minimal TOML reader handling only comments/strings (fallback when tomllib is absent).
    Recognizes only [section] key = "value" and key = 123. Sufficient — our schema is flat.
    """
    data: dict[str, dict[str, str]] = {}
    section = ""
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^\[([^\]]+)\]", s)
        if m:
            section = m.group(1)
            data.setdefault(section, {})
            continue
        m = re.match(r"^([A-Za-z0-9_]+)\s*=\s*(.+?)\s*(?:#.*)?$", s)
        if m and section:
            key, raw = m.group(1), m.group(2).strip()
            if raw.startswith(("'", '"')):
                raw = raw[1:-1]
            data[section][key] = raw
    return data


def read_toml(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if tomllib is not None:
        try:
            return dict(tomllib.loads(text))
        except Exception:
            pass
    return {sec: tbl for sec, tbl in _mini_toml_read(text).items()}


def toml_get(cfg: dict[str, object], section: str, key: str, default: str) -> str:
    sect = cfg.get(section, {})
    val = sect.get(key, default) if isinstance(sect, dict) else default
    return str(val)


# ════════════════════════════════════════════════════════════════════════════
#  collect config
# ════════════════════════════════════════════════════════════════════════════
def prompt(label: str, default: str, interactive: bool) -> str:
    if not interactive:
        return default
    raw = input(f"  {label} [{default}]: ").strip()
    return raw or default


def gather_config(interactive: bool) -> dict[str, str]:
    """Derive config values in order: existing .harness.toml (if any) → interactive input."""
    existing = read_toml(HARNESS_TOML)
    seed = {
        "src_root": toml_get(existing, "paths", "src_root", DEFAULTS["src_root"]),
        "tests_root": toml_get(existing, "paths", "tests_root", DEFAULTS["tests_root"]),
        "scores_dir": toml_get(existing, "paths", "scores_dir", DEFAULTS["scores_dir"]),
        "progress_file": toml_get(
            existing, "paths", "progress_file", DEFAULTS["progress_file"]
        ),
        "task_id_regex": toml_get(
            existing, "task_id", "regex", DEFAULTS["task_id_regex"]
        ),
        "coverage_threshold": toml_get(
            existing, "gates", "coverage_threshold", DEFAULTS["coverage_threshold"]
        ),
        "audit_threshold": toml_get(
            existing, "gates", "audit_threshold", DEFAULTS["audit_threshold"]
        ),
        "review_threshold": toml_get(
            existing, "gates", "review_threshold", DEFAULTS["review_threshold"]
        ),
        "language_profile": toml_get(
            existing, "language", "profile", DEFAULTS["language_profile"]
        ),
        "docstring_lang": toml_get(
            existing, "language", "docstring_lang", DEFAULTS["docstring_lang"]
        ),
        "test_cmd": toml_get(existing, "language", "test_cmd", DEFAULTS["test_cmd"]),
        "type_cmd": toml_get(existing, "language", "type_cmd", DEFAULTS["type_cmd"]),
        "lint_cmd": toml_get(existing, "language", "lint_cmd", DEFAULTS["lint_cmd"]),
    }
    if interactive:
        print("== .harness.toml config (Enter = existing/default) ==")
        seed["src_root"] = prompt("src_root", seed["src_root"], True)
        seed["tests_root"] = prompt("tests_root", seed["tests_root"], True)
        seed["scores_dir"] = prompt("scores_dir", seed["scores_dir"], True)
        seed["progress_file"] = prompt("progress_file", seed["progress_file"], True)
        seed["task_id_regex"] = prompt("task_id regex", seed["task_id_regex"], True)
        seed["coverage_threshold"] = prompt(
            "coverage_threshold", seed["coverage_threshold"], True
        )
        seed["audit_threshold"] = prompt(
            "audit_threshold", seed["audit_threshold"], True
        )
        seed["language_profile"] = prompt(
            "language profile", seed["language_profile"], True
        )
        seed["docstring_lang"] = prompt(
            "docstring_lang (ko/en)", seed["docstring_lang"], True
        )
    return seed


# ════════════════════════════════════════════════════════════════════════════
#  (a) write .harness.toml (line-by-line substitution — comment-preserving, idempotent)
# ════════════════════════════════════════════════════════════════════════════
# (section, key) → config dict key
_TOML_FIELD_MAP = [
    ("paths", "src_root", "src_root"),
    ("paths", "tests_root", "tests_root"),
    ("paths", "scores_dir", "scores_dir"),
    ("paths", "progress_file", "progress_file"),
    ("task_id", "regex", "task_id_regex"),
    ("gates", "coverage_threshold", "coverage_threshold"),
    ("gates", "audit_threshold", "audit_threshold"),
    ("gates", "review_threshold", "review_threshold"),
    ("language", "profile", "language_profile"),
    ("language", "docstring_lang", "docstring_lang"),
    ("language", "test_cmd", "test_cmd"),
    ("language", "type_cmd", "type_cmd"),
    ("language", "lint_cmd", "lint_cmd"),
]
_NUMERIC_KEYS = {"coverage_threshold", "audit_threshold", "review_threshold"}


def _toml_literal(key: str, value: str) -> str:
    if key in _NUMERIC_KEYS:
        return value
    if key == "task_id_regex":  # regex = single-quote literal (preserves escapes)
        return f"'{value}'"
    return f'"{value}"'


def update_toml_text(text: str, cfg: dict[str, str]) -> str:
    """Per-section, substitute each `key = ...` line with the cfg value (preserving comments/structure)."""
    lines = text.splitlines()
    cur = ""
    for i, line in enumerate(lines):
        m = re.match(r"^\s*\[([^\]]+)\]", line)
        if m:
            cur = m.group(1)
            continue
        for sec, tkey, ckey in _TOML_FIELD_MAP:
            if cur != sec:
                continue
            km = re.match(rf"^(\s*{re.escape(tkey)}\s*=\s*)(.+?)(\s*(?:#.*)?)$", line)
            if km:
                lit = _toml_literal(ckey, cfg[ckey])
                lines[i] = f"{km.group(1)}{lit}{km.group(3)}"
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def write_toml(cfg: dict[str, str], dry_run: bool) -> bool:
    if not HARNESS_TOML.exists():
        print(
            f"[init] .harness.toml not found — expected the canonical copy at the kit root: {HARNESS_TOML}",
            file=sys.stderr,
        )
        return False
    text = HARNESS_TOML.read_text(encoding="utf-8")
    new = update_toml_text(text, cfg)
    if new == text:
        print("[init] .harness.toml unchanged (idempotent)")
        return True
    if dry_run:
        print("[init] (dry-run) .harness.toml will be updated")
        return True
    HARNESS_TOML.write_text(new, encoding="utf-8")
    print("[init] .harness.toml updated")
    return True


# ════════════════════════════════════════════════════════════════════════════
#  (b) prerequisite check — loud failure
# ════════════════════════════════════════════════════════════════════════════
def check_hook_registered() -> list[str]:
    """Is the PreToolUse → harness_gate_check.sh hook present in .claude/settings.json?"""
    problems: list[str] = []
    if not SETTINGS_JSON.exists():
        problems.append(
            f"PreToolUse hook not registered: {SETTINGS_JSON} not found (commit guard neutralized)"
        )
        return problems
    text = SETTINGS_JSON.read_text(encoding="utf-8", errors="replace")
    if "PreToolUse" not in text:
        problems.append(
            "no PreToolUse block in .claude/settings.json (commit guard neutralized)"
        )
    if "harness_gate_check.sh" not in text:
        problems.append(
            ".claude/settings.json PreToolUse does not invoke harness_gate_check.sh"
        )
    return problems


def check_global_prereqs() -> list[str]:
    """Verify the global prerequisites (vendored quality-gates + the 4 global agents) exist."""
    problems: list[str] = []
    if not VENDORED_QG.exists():
        problems.append(
            f"vendored quality-gates not found: {VENDORED_QG.relative_to(ROOT).as_posix()} "
            "(loses the source of thresholds, permission matrix, and JSON schema)"
        )
    if not GLOBAL_AGENTS_DIR.is_dir():
        problems.append(
            f"global agents directory not found: {GLOBAL_AGENTS_DIR} (Stage 4 REVIEW etc. impossible)"
        )
    else:
        for agent in REQUIRED_GLOBAL_AGENTS:
            if not (GLOBAL_AGENTS_DIR / f"{agent}.md").exists():
                problems.append(f"global agent missing: ~/.claude/agents/{agent}.md")
    return problems


def check_safety_boundary(toml_path: Path | None = None) -> list[str]:
    """Return a first-run advisory when [safety_boundary].paths is empty.

    The gate ships with generic boundary defaults (migrations/secrets/schema/.env/...), but the
    PROJECT-SPECIFIC no-auto-edit paths — hardware drivers, external-device adapters, the shutdown
    path — start empty and are easy to forget. This advisory makes the operator confirm them before
    the first loop run rather than discovering a fail-open boundary later.

    Returns [] when paths are configured; a one-item advisory list when empty. Never raises.
    """
    cfg = read_toml(toml_path or HARNESS_TOML)
    sect = cfg.get("safety_boundary", {})
    paths = sect.get("paths", []) if isinstance(sect, dict) else []
    if isinstance(paths, str):
        paths = [paths] if paths.strip() else []
    if not paths:
        return [
            "safety_boundary.paths is EMPTY — declare your project's no-auto-edit paths "
            "(hardware / external-device / migration / secret / shutdown) in "
            ".harness.toml [safety_boundary] before the first loop run, or confirm none apply. "
            "The gate falls back to generic defaults only; project-specific boundaries are yours to set."
        ]
    return []


# ════════════════════════════════════════════════════════════════════════════
#  (c) baseline snapshot
# ════════════════════════════════════════════════════════════════════════════
_BASELINE_FILES = (
    ".harness.toml",
    ".claude/settings.json",
)


def snapshot_baseline(dry_run: bool) -> None:
    """Copy the current config into .harness/baseline/ (the drift-diff reference point)."""
    if dry_run:
        print(
            f"[init] (dry-run) baseline snapshot will be written → {BASELINE_DIR.relative_to(ROOT).as_posix()}/"
        )
        return
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    for rel in _BASELINE_FILES:
        src = ROOT / rel
        if not src.exists():
            continue
        dst = BASELINE_DIR / Path(rel).name
        shutil.copy2(src, dst)
        copied += 1
    print(
        f"[init] baseline snapshot: {copied} file(s) → {BASELINE_DIR.relative_to(ROOT).as_posix()}/"
    )


# ════════════════════════════════════════════════════════════════════════════
#  main
# ════════════════════════════════════════════════════════════════════════════
def main() -> int:
    # Reconfigure stdout/stderr to UTF-8 so non-ASCII (em-dash etc.) output does not
    # crash with UnicodeEncodeError on a Windows console (cp949 etc.) — only on runtimes
    # that support it; failures are ignored.
    for stream in (sys.stdout, sys.stderr):
        reconfig = getattr(stream, "reconfigure", None)
        if callable(reconfig):
            try:
                reconfig(encoding="utf-8")
            except (ValueError, OSError):  # pragma: no cover - defensive
                pass

    ap = argparse.ArgumentParser(description="harness starter-kit settling step")
    ap.add_argument(
        "--non-interactive",
        action="store_true",
        help="use existing/default values without prompting",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="print the change plan without actually writing",
    )
    ap.add_argument(
        "--skip-prereq",
        action="store_true",
        help="skip the prerequisite check (not recommended)",
    )
    args = ap.parse_args()

    # dry-run never prompts. If stdin is not a TTY (non-interactive runs: CI, pipes, agents,
    # etc.), automatically fall back to non-interactive to avoid input() blocking (stability principle).
    interactive = not args.non_interactive and not args.dry_run and sys.stdin.isatty()
    print("=" * 60)
    print(
        "  HARNESS INIT  (idempotent · "
        + ("DRY-RUN" if args.dry_run else "apply")
        + ")"
    )
    print("=" * 60)

    # (a)
    cfg = gather_config(interactive)
    if not write_toml(cfg, args.dry_run):
        return 2

    # (b) — prerequisite check (loud failure)
    if not args.skip_prereq:
        problems = check_hook_registered() + check_global_prereqs()
        if problems:
            print("", file=sys.stderr)
            print("!" * 60, file=sys.stderr)
            print(
                "  Missing prerequisites — the harness is silently neutralized. Fix the following:",
                file=sys.stderr,
            )
            for p in problems:
                print(f"   ✗ {p}", file=sys.stderr)
            print("!" * 60, file=sys.stderr)
            print(
                "  (to skip only the check, use --skip-prereq — at your own risk)",
                file=sys.stderr,
            )
            return 3
        print(
            "[init] prerequisite check passed (hook registered + vendored QG + 4 global agents)"
        )
    else:
        print("[init] (--skip-prereq) prerequisite check skipped")

    # Safety-boundary first-run advisory (non-blocking warning — the gate keeps working on generic
    # defaults, but project-specific boundaries must be consciously confirmed before the loop runs).
    boundary_advisory = check_safety_boundary()
    if boundary_advisory:
        print("", file=sys.stderr)
        print("~" * 60, file=sys.stderr)
        print("  SAFETY BOUNDARY — confirm before the first loop run:", file=sys.stderr)
        for advisory in boundary_advisory:
            print(f"   - {advisory}", file=sys.stderr)
        print("~" * 60, file=sys.stderr)

    # (c)
    snapshot_baseline(args.dry_run)

    print("=" * 60)
    print(
        "  INIT complete" + (" (dry-run — no actual changes)" if args.dry_run else "")
    )
    print(
        "  Next: pytest tests/test_harness_hardening.py  (post-clone acceptance test)"
    )
    print(
        "  Docs (human review): pip install -r requirements-docs.txt && python scripts/build_docs_portal.py --serve"
    )
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
