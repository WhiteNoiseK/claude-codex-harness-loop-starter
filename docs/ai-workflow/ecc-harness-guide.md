# Harness Engineering Execution Guide (Phase × Agent/Skill Mapping)

<!-- ROLE BANNER: an execution guide that defines how to apply agents/skills to the 6-Phase workflow.
     What this document decides: "in each Phase, which agent/skill is used to produce which deliverable and how it is verified".
     What this document does NOT decide: the content of the deliverables (owned by each Phase document) · gate thresholds (quality-gates.md). -->

> **Applies to**: all harnesses (Claude Code, Codex, Cursor, Antigravity, etc.)
> **References**: `AGENTS.md` / `CLAUDE.md` (project top-level instructions) · `.clauderules` (code quality rules)

---

## 0. Overview

This project runs in harness engineering mode, where **AI agents code the entire SW except the safety boundary of the {{PROJECT_DOMAIN}} area**.
The user acts as architect/supervisor.

### 0.1 Integration Principles
1. **Phases define structure; agents/skills accelerate execution** — the Phase owns the deliverable, the agent is a tool.
2. **Deliverable first, tools are the means** — a Phase ends when "the deliverable is complete", not when "a command was run".
3. **No entering the next Phase without verification** — at each Phase's end, pass that DoD checklist.

---

## 1. Phase 1: Research

### 1.1 Goal
Resolve technical uncertainty, identify risks, collect feasibility-spike results.

### 1.2 Deliverables
- `docs/ai-workflow/research.md`
- `docs/experiments/<spike>_spike_report.md` (spikes)

### 1.3 Execution Chain (agents/skills)
```text
[1] codebase & reference analysis    agent: Explore (subagent)
[2] technical research               skill: deep-research / market-research / exa-search
[3] architecture design draft        agent: architect
[4] risk identification              agent: planner
[5] integrated writing of research.md agent: doc-updater or direct
```
Example instruction: "Deeply analyze the {{PROJECT_DOMAIN}} codebase and references and write a report in the PART A~F structure"

### 1.4 DoD Checklist
- [ ] PART A~F structure complete
- [ ] All CONFLICTs/open items stated as `[CONFLICT]` banners
- [ ] Measured data reflected
- [ ] External references cited
- [ ] Feasibility-spike results reflected in PART E/F

---

## 2. Phase 2: Planning

### 2.1 Goal
WBS breakdown (2~4h tasks), per-task DoD, functional spec.

### 2.2 Deliverables
- `docs/ai-workflow/plan.md`
- functional spec

### 2.3 Execution Chain
```text
[1] check functional spec templates  Read: functional spec templates
[2] WBS breakdown                    agent: planner / skill: tdd-workflow
[3] write each task's DoD            format: Given/When/Then + verification command
[4] architecture re-review           agent: architect
[5] write/update functional spec     direct
```

### 2.4 DoD Checklist
- [ ] Every M-task has a DoD + verification command (`--cov` is a dotted-module path)
- [ ] Each task split into one execution unit (2~4h) in size
- [ ] External-dependency tasks marked DEFER
- [ ] No entering Phase 3 before receiving **user approval** `[PLAN APPROVED]`

---

## 3. Phase 3: Iterative Implementation

### 3.1 Goal
DoD-based TDD implementation, incremental delivery per task.

### 3.2 Deliverables
- `{{SRC_ROOT}}/` (production code) · `{{TESTS_ROOT}}/` (tests)
- `implementation_log.md` · `progress.md` (updated in real time)

### 3.3 Per-Task Execution Loop
```text
[Pre-action] progress.md (active) → plan.md (DoD) → implementation_log (latest) → git log --grep=HARNESS -5
   ↓
[Step 1] RED   : write failing tests       agent: test-writer   verify: pytest → FAIL
[Step 2] GREEN : minimal implementation     agent: impl-coder    verify: pytest → PASS
[Step 3] VERIFY: automated verification     script: scripts/harness_run_verify.sh
[Step 4] REVIEW: code + security in parallel agent: code-reviewer + security-reviewer
[Step 5] FIX   : edit within review scope    agent: refactor-fixer
[Step 6] AUDIT : rerun and cross-check claims agent: score-auditor
   ↓
[Commit] <type>(<TASK-ID>): <description> [HARNESS]   (PreToolUse hook re-verifies)
   ↓
[Post-action] progress.md (active→done, update next) + implementation_log (done/issues/decisions)
```
> The 6-stage threshold scores, permission matrix, and JSON schema have a single source of truth in `docs/_harness/quality-gates.md`.
> Safety-boundary tasks apply the R0~R4 independent-review overlay in addition to the 6 stages above.

### 3.4 Error Recovery
| Situation | Response |
|------|------|
| test fails 1~2 times | retry the same agent (different approach) |
| build/type error | build-error-resolver |
| test fails 3 times in a row | **escalate to the user** (progress.md BLOCKER) |
| exceeds safety-boundary scope | **request user confirmation** (no self-directed implementation) |

---

## 4. Phase 4: Delivery

### 4.1 Goal
Staging deployment, automated QA verification, request production-deployment approval.

### 4.2 Deliverables
- `docs/ai-workflow/delivery_log.md`

### 4.3 Execution Chain
```text
[1] full test suite      pytest {{TESTS_ROOT}}/ --cov={{SRC_ROOT_DOTTED}} --cov-fail-under=80
[2] E2E tests            agent: e2e-runner / skill: e2e-testing, webapp-testing
[3] security review      agent: security-reviewer / skill: security-review
[4] coverage-gap report  command: /test-coverage
[5] quality gate         command: /quality-gate
[6] staging deployment   `{{DEPLOY_STAGING_CMD}}` → health check → smoke
[7] write delivery_log.md QA report + approval request
```

### 4.4 DoD Checklist
- [ ] Full tests 80%+ coverage
- [ ] E2E tests pass
- [ ] Security review with 0 CRITICAL/HIGH
- [ ] Staging health check passes
- [ ] **Request user approval** by submitting delivery_log.md

---

## 5. Phase 5: Deployment

### 5.1 Goal
Production deployment (only after explicit approval).

### 5.2 Deliverables
- `docs/ai-workflow/deployment_log.md`

### 5.3 Approval Gate
**The agent waits until the user explicitly gives `[RELEASE APPROVED]`.** No unauthorized production access.

### 5.4 Execution Chain
```text
[1] confirm approval received: [RELEASE APPROVED]
[2] pre-check          command: /verify (staging final pass + rollback plan confirmed)
[3] production deploy   `{{DEPLOY_PROD_CMD}}` / skill: deployment-patterns
[4] post-deploy watch  health check, error rate
[5] checkpoint         command: /checkpoint
[6] deployment_log.md   deploy version + reference to delivery_log verification number + observations
```

### 5.4 DoD Checklist
- [ ] `[RELEASE APPROVED]` receipt confirmed
- [ ] Rollback script prepared
- [ ] Post-deploy health check passes
- [ ] deployment_log.md recorded (referencing the delivery_log verification number)

---

## 6. Phase 6: Review & Assetization

### 6.1 Goal
Asset-ize failure/success patterns through a retrospective into knowledge.

### 6.2 Deliverables
- `docs/retrospective/lessons_learned.md` (single source of truth)

### 6.3 DoD Checklist
- [ ] AI misjudgments / effective prompts recorded
- [ ] Project-specific guidance accumulated
