---
description: "Analyze the break point and resume safely with no damage/omission. Restores the unfinished stage, uncommitted/half-applied edits, and test state via the fact layer, then continues from that point."
argument-hint: "[optional: a hint about what you were doing before the break]"
---

# /kit:resume-break — analyze the break point + safe resume

When a session was cut off mid-work, **restore how far it got, verify nothing was damaged or left half-done,
then continue from that point** — never restart from scratch (no duplicate work), never re-run an
already-passed stage. If `$ARGUMENTS` has a hint, use it first.

## 1. Restore state (in order, read-only)

1. End of `docs/ai-workflow/progress.md` → the current active task + the pending stage/verdict
2. `docs/ai-workflow/scores/<task_id>.json` → the last recorded stage (RED→GREEN→VERIFY→REVIEW→FIX→AUDIT)
3. `git log --oneline --grep=HARNESS -5` → the last checkpoint SHA
4. `git status --short` + `git diff --name-only` → uncommitted / stragglers (if the working tree is shared,
   separate your files from others')
5. (if any) a queued handoff (`docs/ai-workflow/handoffs/*.md`) / a next prompt enclosed in the reviewer's last reply

`scripts/harness_status.sh` gives the same progress + git + pytest diagnostics in one call.

## 2. Damage/omission check (fact layer — distrust self-reports)

- **Re-verify claimed == actual**: if the last stage claimed "done/passed", **re-run directly** to compare —
  `pytest <scope> -x --tb=short` · `mypy <src>` · `ruff check <scope>`. Compare per-test-name, not just totals.
- **Scan for half-applied edits**: partially-modified files / duplicated blocks / orphan imports / unused
  symbols / broken syntax — incomplete changes left by the break.
- **Working-tree pass != committed clean**: check whether an uncommitted in-scope straggler becomes a defect once committed.
- If a file differs from intent, fix it in place and continue (**do not change the tests** — fix the implementation).

## 3. Safety branch (before resuming)

If any of the following, **do NOT resume → stop + one-line report**:
- Trust collapse: claimed != actual / no fact layer / mojibake-broken payload
- Unresolved safety boundary: schema/migration · secret · real-HW · single-authority spec conflict
- Unapproved judgmental decision: frozen-test edit · scope expansion · contract reversal
- 3 cumulative self-heal failures at the same stage

Otherwise → resume **from the broken stage**. Do not re-run already-passed/committed stages.

## 4. Resume report (once, before continuing)

`[restored coordinate (task/stage)] · [what is unfinished] · [check result OK / N issues] · [what to do next]`.
If break-induced damage is found, **fix that first**, then proceed.

> Concurrent sessions: when a working tree is shared, never `git add .` / `-A` — check/stage only your own files.
> Stop axes: `docs/ai-workflow/codex_loop_operating_policy.md` §3.
