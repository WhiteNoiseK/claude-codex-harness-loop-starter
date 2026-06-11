# Review Artifacts

<!-- ROLE BANNER: the single source of truth directory for independent-reviewer results (full findings).
     What this README decides: the review artifact filename convention + required sections.
     implementation_log.md is the timeline, scores/ is the score/audit summary — the originals live here. -->

This directory holds the originals of independent-reviewer (R0~R4) results. Put detailed findings here
that must not disappear from chat history. `implementation_log.md` keeps only a path + summary, and `scores/` keeps only scores/audits.

## Filename Convention

```text
<task_id>_<review_stage>_review.md
```

Examples:

```text
{{TASK_ID_EXAMPLE}}_R1_review.md
{{TASK_ID_EXAMPLE}}_R3_fix_verification.md
{{TASK_ID_EXAMPLE}}_R4_checkpoint_audit.md
```

> The task_id syntax follows `.harness.toml [task_id].regex` (multi-segment allowed).

## Required Sections

- `Verdict` (PASS | BLOCKED)
- `Stage` (R0 | R1 | R2 | R3 | R4)
- `Task`
- `Findings` (by severity)
- `Test Gaps`
- `Authority Conflicts`
- `Scope Notes`
- `Recheck Command`

A `BLOCKED` review must include `Evidence` and `Required fix` for every blocking finding.

> See `docs/ai-workflow/codex_claude_review_protocol.md` §6 for format details.
