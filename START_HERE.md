# START HERE — Kick off this kit with a single "apply it" to your agent

> **This document is for two readers.**
> 👤 **Human (developer)**: you only need §1–§2 — one copy-paste prompt starts your new project.
> 🤖 **AI agent**: perform the §3 "Activation Runbook" as written. If you were told to read this document, §3 is your execution procedure.
>
> For *what and why* the kit is, see [README.md](README.md); for the standard process, see [docs/pm-guide/lifecycle-standard.md](docs/pm-guide/lifecycle-standard.md).

---

## 1. What This Kit Does for You (one paragraph)

When you start a new project, clone this folder and tell the agent "apply it" — and you start out with a proven **8-stage development lifecycle** (PMBOK+Research+Feasibility), the **Gate P 3-contract freeze** (data-definition · output-sink · identifier/unit → blocking the "back to square one" trial-and-error), the **6-stage quality gate**, **Foam context recovery**, and **drift locking** all in place from day one. It is designed assuming you work alongside AI agents.

## 2. For Humans — Copy and Paste to Your Agent (Kickoff Prompt)

Copy the following, fill in only the `< >` parts, and give it to your agent (IDE/terminal/app, whichever):

```text
Apply the harness starter kit and start a new project.

  Kit location:        <path to the cloned kit>/harness-starter-kit/
  New project:         <path to the folder where the new project will live>
  Project description: <2–4 sentences on what you are building — domain / core technologies / final output / whether there are hardware/external dependencies>
  Working environment: <one of IDE | terminal | app>
  Language/stack:      <e.g. Python / TypeScript+React / Go ... (if unsure, say "recommend one")>

Follow §3 "AI Agent Activation Runbook" in START_HERE.md exactly.
Start with the §3.0 prerequisite check first, and if any MCP/skill is missing, ask whether to install it.
```

> Tip: the more concrete the project description (especially *the shape of the final output* and *external dependencies*), the more accurately Gate P's 3 contracts can be pinned down.

---

## 3. 🤖 AI Agent Activation Runbook

> The agent performs this procedure **in order**. Each step connects to a real file in the kit.
> Do not skip arbitrarily. For safety boundaries / hard-to-reverse actions, get human approval.

### §3.0 Prerequisite Check (first)
1. **Identify the environment**: confirm the working environment the user stated (IDE/terminal/app) and apply/advise the relevant-section optimizations in [docs/ENVIRONMENTS.md](docs/ENVIRONMENTS.md).
2. **AI tooling check**: use the checklist in [docs/ai-tooling/AI_TOOLING.md](docs/ai-tooling/AI_TOOLING.md) to confirm the **agents · commands · skills · MCP** you need exist. For anything missing, follow that document's install procedure and **ask the user whether to install** before proceeding (no auto-install — only after approval).
3. **Verify global prerequisites**: run `python scripts/harness_init.py --dry-run` to check hook registration + the global agents (code-reviewer/security-reviewer/planner/architect) + the vendored quality-gates exist. Report any missing items to the user.

### §3.1 Clone & Settle
4. Copy the kit to the new project path. (A clean copy unrelated to this project.)
5. Run `python scripts/harness_init.py` → finalize `.harness.toml` (SRC_ROOT/TESTS_ROOT/language profile/thresholds/task-id) + snapshot `.harness/baseline/`.
6. For a new project, `git init` + first commit (so the baseline-diff drift check works).
7. Fill the 🖊 placeholders in [TEMPLATE_MANIFEST.md](TEMPLATE_MANIFEST.md) with user input (product name, goals, etc.). For non-Python/non-Korean, swap the `.harness.toml [language]` profile.

### §3.2 Enter the Standard Lifecycle (never skip)
8. **S0 Research** → write [docs/ai-workflow/research.md](docs/ai-workflow/research.md) (PART A–F + 3+ risks). Investigate reusing existing implementations/libraries before building from scratch.
9. **S1 Initiating** → [docs/pm-guide/ProductProposal.md](docs/pm-guide/ProductProposal.md) charter (scope + **external-dependency boundaries**).
10. **S2 Feasibility** → spikes/trade studies for each core technology ([docs/experiments/_TEMPLATE_spike_report.md](docs/experiments/_TEMPLATE_spike_report.md), etc.). Prove physical achievability before integration.
11. **★ S3 Planning / Gate P (hard gate)** → before any pipeline code, **freeze the 3 contracts**:
    - Data definition: [docs/engineering/_TEMPLATE_data_spec.md](docs/engineering/_TEMPLATE_data_spec.md) v1.0
    - Output sink: [docs/engineering/_TEMPLATE_erd.md](docs/engineering/_TEMPLATE_erd.md) (or pin a facade)
    - Identifier/unit: [docs/engineering/_TEMPLATE_identifier_unit_contract.md](docs/engineering/_TEMPLATE_identifier_unit_contract.md)
    - (if clone-based) [docs/engineering/_TEMPLATE_assumption_leak_audit.md](docs/engineering/_TEMPLATE_assumption_leak_audit.md)
    - + [docs/ai-workflow/plan.md](docs/ai-workflow/plan.md) WBS+DoD. **No entering S4 before Gate P is green** ([docs/pm-guide/PHASE_GATES.md](docs/pm-guide/PHASE_GATES.md)).
12. **S4 Executing** → the 6-stage gate per task (`/kit:harness-verify` or the procedure in [docs/_harness/quality-gates.md](docs/_harness/quality-gates.md)). Record progress in [docs/ai-workflow/progress.md](docs/ai-workflow/progress.md).
13. **S6/S7** → Gate D (delivery QA) → **★ Gate S (pre-deployment security audit, [docs/pm-guide/security_gate.md](docs/pm-guide/security_gate.md))** → `[RELEASE APPROVED]` + retrospective/memory promotion.

### §3.3 Reporting
14. On passing each gate, report to the user the current coordinates (S-stage/gate) + the next task. If you lose context, run `context check`.

### §3.4 Feeding Improvements Back into the Kit
15. If you find a defect or improvement in the kit itself, instead of a stopgap, **feed it back into the kit** (with a version bump) and notify the user.

---

## 4. Further Reading
- Standard process: [docs/pm-guide/lifecycle-standard.md](docs/pm-guide/lifecycle-standard.md)
- Gate & risk examples: [docs/pm-guide/PHASE_GATES.md](docs/pm-guide/PHASE_GATES.md) · [docs/pm-guide/STAGE_DEFINITION_RISKS.md](docs/pm-guide/STAGE_DEFINITION_RISKS.md)
- Drift: [docs/pm-guide/DRIFT_LOCK.md](docs/pm-guide/DRIFT_LOCK.md)
- AI tooling (MCP/skills) install: [docs/ai-tooling/AI_TOOLING.md](docs/ai-tooling/AI_TOOLING.md)
- Per-environment optimization: [docs/ENVIRONMENTS.md](docs/ENVIRONMENTS.md)
- **Multi-agent collaboration (independent review — e.g. Claude ↔ Codex)**: [docs/ai-workflow/codex_claude_review_protocol.md](docs/ai-workflow/codex_claude_review_protocol.md) · activate via `.harness.toml [review_overlay]`
- **Human-review docs portal (md → HTML)**: `python scripts/build_docs_portal.py --serve` → http://localhost:8000 ([docs/PORTAL_README.md](docs/PORTAL_README.md)). Auto-nav, so new docs show up without config edits.
