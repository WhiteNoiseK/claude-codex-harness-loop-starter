# scripts/ — harness engine + generators + feasibility-script inventory

> **ROLE BANNER:** This directory holds the 6-stage quality-gate engine (Layer A/C), the Foam
> knowledge-catalog generators, and the one-off verification/simulation scripts of the
> Feasibility phase.
> It *makes no decisions* — **values** such as thresholds, paths, and task-id grammar are all
> owned by [`../.harness.toml`](../.harness.toml), and the scripts **read those values at runtime**
> via `_harness_config.py`.

To change a value, edit the single `.harness.toml` file rather than the scripts. The scripts read,
at runtime, the values that `_harness_config.py` merges from `.harness.toml` + sensible defaults,
so **even without `.harness.toml`** they run end-to-end on the defaults (init is not a single point
of failure). The first kit's `{{TOKEN}}` substitution approach has been dropped — removing the path
where an unsubstituted token broke the commit guard.

---

## 1. Bootstrap (once, right after clone)

| Script | Role | Notes |
|:--|:--|:--|
| `harness_init.py` | create/update `.harness.toml` → verify hook & global prerequisites (loud failure) → snapshot to `.harness/baseline/` | idempotent · `--dry-run` · `--non-interactive` · settling step (not a single point of failure) |

```bash
python scripts/harness_init.py            # interactive
python scripts/harness_init.py --dry-run  # preview changes
```

Prerequisites (loud `exit 3` if absent): PreToolUse hook registration, a vendored copy of
`docs/_harness/quality-gates.md`, and the global agents
`code-reviewer`/`security-reviewer`/`planner`/`architect`.

## 2. The 6-stage quality-gate engine

| Script | Layer / Stage | Role |
|:--|:--|:--|
| `_harness_config.py` | shared config loader | merges `.harness.toml` + sensible defaults (runtime). With `--sh`, emits `KEY='value'` for bash to `eval`. Works on defaults even with zero files (never propagates exceptions) |
| `harness_gate_check.sh` | hook shim | PreToolUse entry point — `exec`s into `harness_audit_rerun.py` (3 lines) |
| `harness_audit_rerun.py` | **Layer C** (commit guard) | On a `[HARNESS]` commit, **reruns and compares** the score JSON's claimed pytest/mypy/ruff/coverage values. Blocks with `exit 2` on forgery |
| `harness_run_verify.sh` | **Layer A** (Stage 3 VERIFY) | subset pytest + coverage + mypy + ruff → `<scores>/<task_id>.verify.json` |
| `harness_status.sh` | session recovery | progress + recent HARNESS commits + uncommitted changes + test/type status on one screen |

### Integrity-critical (must not change)

- The **SELFTEST lock** in `harness_run_verify.sh`: unless `HARNESS_SELFTEST=1`, `HARNESS_*_CMD`
  injection is force-disabled (blocks bypassing the gate via fake-command injection).
- The `_is_pytest_cmd` **anti-forgery** in `harness_audit_rerun.py`: rejects forging counts via
  `echo "7 passed"` or shell chains (`pytest x & echo 7 passed`).
- The `_normalize_tool_cmd` **venv-safe rerun** in `harness_audit_rerun.py`: reruns bare
  `pytest`/`mypy`/`ruff` with the current interpreter (`sys.executable -m …`) → blocks false
  positives from a different venv.

### Drift bugs the kit fixed (vs the original project)

1. **task-id multi-segment** — `TASK_ID_RE` allows one or more segments, so `M3`, `M3-RT`, and
   `M3-RT-PERSIST-01` all match. The original matched only 1-2 segments and silently no-op'd
   (bypassed the guard) on 3-segment IDs. Canonical grammar →
   [`../docs/_harness/TASK_ID_GRAMMAR.md`](../docs/_harness/TASK_ID_GRAMMAR.md)
   and `.harness.toml [task_id].regex`.
2. **coverage `--cov` = dotted-module** — `harness_run_verify.sh` converts `SRC_PATHS`
   (file/directory) into a dotted module and passes it to `--cov=`. The original passed a file
   path, so coverage false-reported 0% and the AUDIT rerun reproduced the same 0%.
3. **reference only real script names** — the engine points only at `harness_gate_check.sh` (shim)
   → `harness_audit_rerun.py`, plus `harness_run_verify.sh`. (`harness_commit_guard.py` and
   `harness_score.sh` are nonexistent phantoms — never reference them anywhere.)

## 3. Foam knowledge-catalog generators

| Script | Output | Role |
|:--|:--|:--|
| `foam_catalog.py` | `docs/_recent.md`, `docs/_authority.md` | most-recent-first catalog + authority registry (parses `.claude/CLAUDE.md` §8) |
| `field_cascade.py` | `docs/_field_cascade.md` | field (column)→document dependency map. **auto-discovers spec paths** (a §3.1 ```text header in `docs/engineering/*_spec.md`) |

```bash
python scripts/foam_catalog.py
python scripts/field_cascade.py
```

The `_AMBIGUOUS` / `_ALIAS_OVERRIDES` in `field_cascade.py` ship empty — a project fills them in
once it discovers ambiguous tokens / irregular aliases (see the usage examples in the file's
top docstring).

## 4. Feasibility scripts — naming convention

> The one-off verification/simulation scripts of the Feasibility phase reveal their intent in the
> filename via a **verb-prefix naming** scheme. This kit **ships no samples** — a project creates
> them as needed.

| Prefix | Meaning | Example (project-created) |
|:--|:--|:--|
| `verify_*.py` | **verify a hypothesis** against real measurements/hardware/data (quantitative measurement + pass/fail) | `verify_<subject>_<aspect>.py` |
| `simulate_*.py` | **predict before operation** with a physical/numerical model (scenario sweep) | `simulate_<subject>_<aspect>.py` |
| `analyze_*.py` | **post-hoc analysis** of collected data/logs (e.g. inverting a formula) | `analyze_<subject>_<aspect>.py` |
| `aggregate_*.py` | **aggregate/summarize** raw data | `aggregate_<subject>_<window>.py` |
| `validate_*.py` | **consistency check** of a spec formula vs real data | `validate_<artifact>_<rule>.py` |

Recommendation: each script keeps a 3-block **"what this script does / model & assumptions / usage"**
at the top of its module docstring (readable by non-specialists — `.harness.toml [language] docstring_lang`).
Results are folded back into a spike report under `docs/experiments/` (template: `_TEMPLATE_spike_report.md`).

## 5. task-id grammar pointer

Commit message format: `<type>(<TASK-ID>): <description> [HARNESS]`

- **Canonical** grammar: [`../docs/_harness/TASK_ID_GRAMMAR.md`](../docs/_harness/TASK_ID_GRAMMAR.md)
- Operational regex: `.harness.toml [task_id].regex` (read by the commit guard)
- Examples: `M3`, `M3-RT`, `M3-RT-PERSIST-01` — all match (multi-segment generalization).
