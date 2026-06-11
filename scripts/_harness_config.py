#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────────────────────
# _harness_config.py — shared harness config loader (runtime read + literal fallback)
#
# Purpose (stability-first NFR):
#   The earlier kit required harness_init.py to substitute {{TOKEN}} values before
#   the scripts would work. If init was never run, or some tokens were left
#   unsubstituted, harness_audit_rerun.py would crash at import time with a
#   NameError — neutralizing the "last line of defense" (the commit guard).
#   → We drop the substitution approach. This loader reads .harness.toml at
#     *runtime*, but still runs end-to-end on hardcoded sensible defaults even if
#     the file is missing entirely or fails to parse.
#
# Design principles:
#   * Standard library only (tomllib — Python 3.11+; if absent or it fails,
#     silently fall back).
#   * Every value is merged over DEFAULTS → all keys are populated even with a
#     zero-entry .harness.toml.
#   * Never raise out of this module — config loading must not be able to break
#     the gate.
#
# bash integration:
#   `python scripts/_harness_config.py --sh` emits KEY='value' shell assignments
#   to stdout. A bash script absorbs them with `eval "$(...)"`, giving both sides a
#   single source of the same merge logic. (If Python is absent, bash falls back to
#   its own literal defaults — a double safety net.)
# ────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path

try:  # Python 3.11+ standard. If absent or import fails, fall back to the mini parser.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - only reached on 3.10 or below
    tomllib = None  # type: ignore[assignment]

# ── Hardcoded sensible defaults (single source — the answer for a zero-entry .harness.toml) ──
# To change a value, edit .harness.toml; even without that file the values below apply.
DEFAULTS: dict[str, object] = {
    "src_root": "src",
    "tests_root": "tests",
    "scores_dir": "docs/ai-workflow/scores",
    "progress_file": "docs/ai-workflow/progress.md",
    "coverage_threshold": 80,
    "audit_threshold": 95,
    "review_threshold": 95,
    "red_threshold": 90,
    "green_threshold": 85,
    # Multi-segment task-id regex — matches M3, M3-RT, and M3-RT-PERSIST-01 alike.
    # (Must-not-change asset — matching only 1-2 segments regresses into a guard bypass.)
    "task_id_regex": r"\((M\d+(?:-[A-Za-z0-9]+)+)\)",
    # Gate commands — must match .harness.toml [language]. Non-Python projects only swap these.
    "test_cmd": "python -m pytest",
    "type_cmd": "python -m mypy --strict --explicit-package-bases --ignore-missing-imports",
    "lint_cmd": "python -m ruff check",
    # Independent-reviewer overlay. Severity is NOT a stop axis by default (the doctrine): at detection
    # the problem is already identified, so findings (incl. HIGH/CRITICAL) self-heal in the FIX loop.
    # A high-stakes project opts in via .harness.toml [review_overlay] severity_is_stop_axis = true.
    "severity_is_stop_axis": False,
    "severity_auto_max": "MEDIUM",
}

# (config key) → (.harness.toml section, key). The schema is flat, so a simple mapping suffices.
_FIELD_MAP: tuple[tuple[str, str, str], ...] = (
    ("src_root", "paths", "src_root"),
    ("tests_root", "paths", "tests_root"),
    ("scores_dir", "paths", "scores_dir"),
    ("progress_file", "paths", "progress_file"),
    ("coverage_threshold", "gates", "coverage_threshold"),
    ("audit_threshold", "gates", "audit_threshold"),
    ("review_threshold", "gates", "review_threshold"),
    ("red_threshold", "gates", "red_threshold"),
    ("green_threshold", "gates", "green_threshold"),
    ("task_id_regex", "task_id", "regex"),
    ("test_cmd", "language", "test_cmd"),
    ("type_cmd", "language", "type_cmd"),
    ("lint_cmd", "language", "lint_cmd"),
    ("severity_is_stop_axis", "review_overlay", "severity_is_stop_axis"),
    ("severity_auto_max", "review_overlay", "severity_auto_max"),
)
_NUMERIC_KEYS = frozenset(
    {
        "coverage_threshold",
        "audit_threshold",
        "review_threshold",
        "red_threshold",
        "green_threshold",
    }
)
_BOOL_KEYS = frozenset({"severity_is_stop_axis"})


def find_harness_toml(start: Path | None = None) -> Path | None:
    """Walk upward from start (default = this file's location) looking for .harness.toml.

    Lets the config be found even when a script is run from a subdirectory rather than
    the kit root. Returns None if not found (callers then fall back to defaults)."""
    here = (start or Path(__file__).resolve()).resolve()
    for base in (here, *here.parents):
        cand = base / ".harness.toml"
        if cand.is_file():
            return cand
    return None


def _mini_toml_read(text: str) -> dict[str, dict[str, str]]:
    """Fallback used when tomllib is absent/fails — recognizes only [section] key = "value" / key = 123.
    Our schema is flat, so this minimal parser is sufficient."""
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
            if raw and raw[0] in "'\"" and raw[-1] == raw[0]:
                raw = raw[1:-1]
            data[section][key] = raw
    return data


def _read_toml(path: Path) -> dict[str, object]:
    """Read the file into a dict. Never raises out — falls back to an empty dict on any exception."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if tomllib is not None:
        try:
            return dict(tomllib.loads(text))
        except Exception:
            pass  # parse failure → retry with the mini parser
    try:
        return {sec: tbl for sec, tbl in _mini_toml_read(text).items()}
    except Exception:  # pragma: no cover - defensive
        return {}


def _coerce(key: str, raw: object) -> object:
    """Coerce a raw TOML value to the type the key expects.

    Numeric keys -> int and boolean keys -> bool (the mini parser returns strings),
    everything else -> str. On numeric failure, fall back to the default."""
    if key in _NUMERIC_KEYS:
        try:
            return int(str(raw).strip())
        except (TypeError, ValueError):
            return DEFAULTS[key]
    if key in _BOOL_KEYS:
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in ("true", "1", "yes", "on")
    return str(raw)


def load_config(start: Path | None = None) -> dict[str, object]:
    """Return a config dict with .harness.toml values merged over DEFAULTS.

    Even if .harness.toml is missing or fails to parse, every key comes back filled
    with its default. Never raises under any circumstances (config must never take
    priority over gate integrity)."""
    cfg: dict[str, object] = dict(DEFAULTS)
    toml_path = find_harness_toml(start)
    if toml_path is None:
        return cfg
    data = _read_toml(toml_path)
    for ckey, section, tkey in _FIELD_MAP:
        sect = data.get(section)
        if isinstance(sect, dict) and tkey in sect:
            cfg[ckey] = _coerce(ckey, sect[tkey])
    return cfg


def _emit_sh(cfg: dict[str, object]) -> str:
    """Emit KEY='value' lines for bash to eval (single-quote-safe quoting).
    Numbers are emitted without quotes so they can be used directly in arithmetic/comparison.
    """
    lines: list[str] = []
    sh_names = {
        "src_root": "SRC_ROOT",
        "tests_root": "TESTS_ROOT",
        "scores_dir": "SCORES_DIR",
        "progress_file": "PROGRESS_FILE",
        "coverage_threshold": "COV_THRESHOLD",
        "audit_threshold": "AUDIT_THRESHOLD",
        "review_threshold": "REVIEW_THRESHOLD",
        "test_cmd": "TEST_CMD",
        "type_cmd": "TYPE_CMD",
        "lint_cmd": "LINT_CMD",
    }
    for ckey, sh in sh_names.items():
        val = cfg[ckey]
        if ckey in _NUMERIC_KEYS:
            lines.append(f"{sh}={int(str(val))}")
        else:
            lines.append(f"{sh}={shlex.quote(str(val))}")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    """CLI: with --sh, print shell assignments; otherwise a human-readable KEY=value dump."""
    cfg = load_config()
    if "--sh" in argv:
        sys.stdout.write(_emit_sh(cfg))
    else:
        for k in sorted(cfg):
            sys.stdout.write(f"{k}={cfg[k]!r}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
