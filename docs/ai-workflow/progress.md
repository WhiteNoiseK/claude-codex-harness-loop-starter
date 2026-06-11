# Harness Progress Status

<!-- ROLE BANNER: Monitoring & Control ledger — the #1 document to read on a cold restart (session recovery).
     When resuming after an interruption, read this first: current position / active task / next task / blockers.
     What this document decides: "what is being done now and what comes next".
     Keep long history in implementation_log.md, scores in scores/, reviews in reviews/. -->

## Single-Authority Specifications (mandatory reference)

| Domain | Spec | Version |
|:---|:---|:---:|
| <domain — e.g., output data definition> | `docs/engineering/<spec>.md` | v0.0 |

> For data-definition work, reference only the latest spec version (on conflict, the spec always wins).

## Current Status

- **Phase**: {{CURRENT_PHASE — e.g., Phase 3 Implementation}}
- **Milestone**: {{CURRENT_MILESTONE}}
- Latest checkpoint: `git log --oneline --grep=HARNESS -1`

## Active Task

- **{{ACTIVE_TASK_ID}}** — <one-line description>. Depends on: <status of prerequisite tasks>.

## Next Task

- **{{NEXT_TASK_ID}}** — <one-line description>. Depends on: <prerequisite>.

## Blockers

| # | Issue | Status | Blocked Task |
|:--|:--|:--|:--|
| — | none | — | — |

<!-- Status legend: ⚠ blocked / 🟡 caution (workaround possible) / ✅ resolved. A domain decision needed = route to decision_pending.md. -->
