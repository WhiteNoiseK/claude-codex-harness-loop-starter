# [Phase 2] Detailed Implementation Plan and DoD

<!-- ROLE BANNER: Phase 2 (Planning) deliverable — WBS + per-task DoD + verification commands + functional spec.
     What this document decides: "what to implement, in what order, and what determines completion".
     What this document does NOT decide: the data contract (owned by the spec) or the actual test code (written in each task's RED step). -->

> {{PROJECT_NAME}} implementation plan
> First written: YYYY-MM-DD | Last updated: YYYY-MM-DD
> Basis: research.md (Phase 1) + functional spec templates
> Single-authority data contract: `docs/engineering/_TEMPLATE_data_spec.md` etc. (on conflict, the spec wins)

---

## 1. Requirements and Business Goals

- **Goal**: {{BUSINESS_GOAL — one sentence: what is being built and why}}
- **Core value**:
  - {{VALUE_1}}
  - {{VALUE_2}}
- **Target/platform**: {{TARGET_PLATFORM}}
- **Key performance/quality goals**:
  - {{NFR_1 — e.g., stability, recovery, performance targets}}
  - {{NFR_2}}

---

## 2. Functional Specification

> Write this based on the functional spec templates (SW/Web). Split tables by Target (area).
> For items not in the template, adapt a similar template or confirm with the architect.

### 2.1 SW Functional Specification

| Func ID | Function Name | Description | Input | Output | Priority | Notes |
|:---|:---|:---|:---|:---|:---|:---|
| S-01 | <function name> | <one-line description> | <input> | <output> | Critical/High/Medium/Low | <notes> |

### 2.2 Web Functional Specification

| Func ID | Function Name | Description | Input | Output | Priority | Notes |
|:---|:---|:---|:---|:---|:---|:---|
| W-01 | <page/screen> | <one-line description> | <linked API> | <displayed result> | High | <notes> |

---

## 3. Approach Strategy (Solution Design)

### 3.1 Tech Stack

### 3.2 Directory Structure

> The path roots follow `.harness.toml [paths]`: `{{SRC_ROOT}}` / `{{TESTS_ROOT}}`.

### 3.3 Architecture Decisions (layer/process separation)

### 3.4 External Dependency Isolation Strategy

> External dependencies falling under the safety boundary (`.harness.toml [safety_boundary].paths`)
> (hardware/vendor API/payments, etc.) are isolated as stub/mock and not actually implemented until confirmed.

---

## 4. WBS (work breakdown structure)

> **Task size = 2~4 hours** (a size that can be executed and verified as one pytest unit).
> Order by dependency (forward along the data flow). No parallel execution (single-developer basis).
> Task ID syntax follows `.harness.toml [task_id].regex` (e.g., `{{TASK_ID_EXAMPLE}}`).
>
> **Defer external-dependency tasks**: tasks tied to the safety boundary or an unconfirmed vendor API
> stay at stub level until the contract is confirmed, then are filled in as a separate task.
> (e.g., tasks depending on unresolved [CONFLICT]/decision_pending items from research.)

### Milestone 1: {{MILESTONE_1_NAME}} (est. N days)

**Goal**: {{MILESTONE_1_GOAL}}

- [ ] **M1-01** <task name>
  - File: `{{SRC_ROOT}}/.../<module>.py`
  - DoD: <a completion condition verifiable as Given/When/Then. Must be measurable.>
  - Verify: `python -m pytest {{TESTS_ROOT}}/unit/test_<module>.py -v --cov=<dotted.module.path> --cov-fail-under=80`
    <!-- ⚠ --cov must be given as a DOTTED MODULE path (e.g., src.backend.core.models).
         Giving a file path (src/.../models.py) makes coverage report a false 0% (the AUDIT rerun reproduces this too). -->
  - Notes: <dependency / handover / whether external dependency is deferred>

- [ ] **M1-02** <task name — external dependency example (defer)>
  - File: `{{SRC_ROOT}}/.../adapters/<vendor>_stub.py`
  - DoD: abstract interface + mock implementation only. Real vendor calls go to a separate task after the contract is confirmed.
  - Verify: `python -m pytest {{TESTS_ROOT}}/unit/test_<module>.py -v`
  - Notes: **DEFER** — {{EXTERNAL_DEP}} contract unconfirmed (decision_pending <ID>). Do not exceed stub scope.

---

## 5. R0~R4 Execution Template (per task)

> Run each M-task in the order below. R1/R2 are mandatory; R0/R3/R4 are optional depending on risk.
> **Safety-boundary tasks (external dependency/schema/migration/shutdown sequence) run all of R0~R4.**
> See `codex_claude_review_protocol.md` for the independent-reviewer overlay details.

| Stage | Trigger | Output/Verification |
|:---|:---|:---|
| **R0 Skeleton** | right after the file skeleton + docstring commit | review whether the skeleton fully reflects the DoD and authority docs. Hold RED on CRITICAL/HIGH |
| **R1 RED** | after writing failing tests, before implementing | whether the tests actually catch the DoD failure (intended RED). Hold GREEN if a core DoD is unverified |
| **R2 GREEN** | after minimal implementation + unit verification | review the code/test diff. No commit on CRITICAL/HIGH |
| **R3 FIX** | after fixing review findings | confirm 100% of CRITICAL/HIGH are resolved. Re-fix if not (max 3 times) |
| **R4 Checkpoint AUDIT** | just before/after commit | rerun and cross-check claimed numbers + scope/log/progress sync. Hold on mismatch |

The internal 6-stage gates (RED/GREEN/VERIFY/REVIEW/FIX/AUDIT) and their threshold scores
have a single source of truth in `docs/_harness/quality-gates.md`.

---

## 6. Quality/Test Plan

> See `test_plan.md` for test-level (L1~L5) and coverage-gate details.
> This § only holds the link between plan and test_plan.

- Code quality limits: function ≤ 50 lines, file ≤ 800 lines, nesting ≤ 3 levels (source of truth: `.clauderules`).
- Coverage gate: each M-task ≥ `.harness.toml [gates].coverage_threshold`%.
