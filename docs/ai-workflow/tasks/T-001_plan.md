# T-001 Plan — <task title>

<!-- ROLE BANNER: per-task Phase 2 plan (trio 2/3: research → plan → design).
     What this document decides: WBS (2~4h work) + per-work DoD + verification command + execution order.
     What this document does NOT decide: factual analysis (research) · interface signature finalization (design). -->

> **Written**: YYYY-MM-DD
> **Version**: v0.1
> **Prerequisites (dependencies)**: <prerequisite task ID and status>
> **Risk level**: <R1+R2 default / safety boundary = all of R0~R4>
> **Single Writer**: implementer = <primary agent> · independent reviewer = <secondary agent> · final decision = user
> **Single authority**: `docs/engineering/<spec>.md` (on conflict, the spec wins)

---

## 1. Scope

**scope-in**: <to fill>
**scope-out (immutable contract)**: <what is never touched>

## 2. WBS

> Work unit = 2~4 hours. Execute in order. `--cov` is a dotted-module path (no file path).

| W | Work | File | DoD | Verify |
|:--|:--|:--|:--|:--|
| **W0** | <work> | `{{SRC_ROOT}}/.../<module>.py` | <verifiable completion condition> | `python -m pytest {{TESTS_ROOT}}/unit/test_<module>.py -v --cov=<dotted.module.path> --cov-fail-under=80` |
| **W1** | <work> | `{{TESTS_ROOT}}/unit/test_<module>.py` (RED) | <test catches the DoD failure> | `python -m pytest {{TESTS_ROOT}}/unit/test_<module>.py -v` |

Order: **W0 → W1 → ...**

## 3. R0~R4 Application

> Apply per risk level. If safety boundary, all of R0~R4. Details = `codex_claude_review_protocol.md`.

| Stage | Apply | Notes |
|:---|:---:|:---|
| R0 Skeleton | ☐ | |
| R1 RED | ☑ | mandatory |
| R2 GREEN | ☑ | mandatory |
| R3 FIX | ☐ | when findings exist |
| R4 AUDIT | ☐ | for safety boundary/schema |
