# TASK_ID_GRAMMAR — task-id grammar source of truth

> **Role (which Phase):** Phase 3 (Iterative Implementation) — defines the grammar of the key (task_id)
> that ties every [HARNESS] commit to its score JSON.
> **Defines:** the canonical grammar of WBS task-ids + the regex the commit guard uses to extract the ID.
> **Does not define:** how WBS is decomposed, what a task means, or milestone boundaries (those belong to plan.md).

This document is the **source of truth (SSOT)**. `scripts/harness_audit_rerun.py` follows this grammar,
and the operational regex is read from `.harness.toml [task_id] regex` (no literal duplication).

---

## 0. Why this document exists separately (a drift case)

The original project's commit guard extracted task-ids with `\((M\d+-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)?)\)`.
That regex matched only **1–2 segments** (`M3-RT`, `M3-RT-PERSIST`), and **3 or more**
(`M3-RT-PERSIST-01`) were either truncated at the end or failed to match depending on their shape.

Result: commits carrying the `[HARNESS]` tag but with a misaligned ID extraction would **silently bypass (silent no-op)** the guard.
The gate slipped not into "pass" but into "not checked" — the most dangerous failure mode.

**The kit's fix**: generalize to allow **1 or more** segments, and keep the regex in a single source,
`.harness.toml`. So `M3`, `M3-RT`, and `M3-RT-PERSIST-01` **all** match.

---

## 1. Canonical Grammar (EBNF)

```ebnf
task_id   = milestone , { "-" , segment } ;
milestone = "M" , digit , { digit } ;          (* M1, M3, M12 ... *)
segment   = alnum , { alnum } ;                 (* RT, PERSIST, 01, RECON ... *)
digit     = "0" | "1" | ... | "9" ;
alnum     = digit | "A"…"Z" | "a"…"z" ;
```

- The first token is always `M` + one or more digits (milestone).
- After that, **zero or more** hyphen-separated segments follow (i.e. a milestone alone is also valid).
- Segments are alphanumeric only (no hyphen/underscore/space — the hyphen is the separator).

---

## 2. Extraction Regex (from the commit message)

The value of `.harness.toml [task_id] regex` = source of truth:

```
\((M\d+(?:-[A-Za-z0-9]+)+)\)
```

- Captures the ID inside the `(...)` of the commit message: `feat(M3-RT-PERSIST-01): ... [HARNESS]`.
- `(?:-[A-Za-z0-9]+)+` = hyphen+segment repeated **one or more times** → multi-segment generalization.
- To also allow milestone-only IDs, change `+` to `*` (project policy — decided in `.harness.toml`).

> `harness_audit_rerun.py` imports/references this regex to extract the ID and locate
> `{{SCORES_DIR}}/<task_id>.json`. If the regex and grammar diverge, the silent no-op recurs.

---

## 3. Examples by Segment Count (1–4 segments)

| Segments | Example task-id | Example commit message | Score file |
|:--:|:--|:--|:--|
| 1 | `M3` | `feat(M3): ... [HARNESS]` | `{{SCORES_DIR}}/M3.json` |
| 2 | `M3-RT` | `feat(M3-RT): ... [HARNESS]` | `{{SCORES_DIR}}/M3-RT.json` |
| 3 | `M3-RT-PERSIST` | `fix(M3-RT-PERSIST): ... [HARNESS]` | `{{SCORES_DIR}}/M3-RT-PERSIST.json` |
| 4 | `M3-RT-PERSIST-01` | `feat(M3-RT-PERSIST-01): ... [HARNESS]` | `{{SCORES_DIR}}/M3-RT-PERSIST-01.json` |

> The default of `.harness.toml [task_id] example` = `M3-RT-PERSIST-01` (4 segments, the deepest case).

---

## 4. Non-Examples (do not match → commit guard BLOCKs)

| String | Why it fails |
|:--|:--|
| `feat(RT-01): ...` | Does not start with a milestone (`M<digit>`) |
| `feat(M3_RT): ...` | Segment separator is not a hyphen (underscore not allowed) |
| `feat(M-RT): ...` | No digit after `M` |
| `feat(M3 RT): ...` | Contains a space (alphanumeric only) |
| `feat: ... [HARNESS]` | No ID inside `(...)` at all |

If a commit carries the `[HARNESS]` tag but ID extraction fails as above, the commit guard **BLOCKs (exit 2) rather than passing through** —
turning a silent no-op into a loud failure.

---

## 5. To Change It

1. Modify only `.harness.toml [task_id] regex` (single source).
2. Update §1 EBNF / §2 regex / §3 examples in this document to the same meaning.
3. Confirm the regression with the task-id matching cases in `tests/test_harness_hardening.py`.
4. `harness_audit_rerun.py` reads `.harness.toml`, so no code change is needed (if a literal is hardcoded, that is the drift).
