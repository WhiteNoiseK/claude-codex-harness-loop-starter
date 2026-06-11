# [Phase 1] Research Report — {{PROJECT_NAME}}

<!-- ROLE BANNER: Phase 1 (Research) deliverable — analysis / history / risk identification only.
     What this document decides: "what was discovered, what is uncertain, what risks exist".
     What this document does NOT decide: the data contract (columns, formulas, units, DB mapping) or the identifier/unit contract.
     => Those are frozen at Gate P (single authority) by docs/engineering/_TEMPLATE_data_spec.md /
        _TEMPLATE_erd.md / _TEMPLATE_identifier_unit_contract.md.
     If research.md conflicts with a single-authority spec => the spec always wins. -->

> First written: YYYY-MM-DD | Last updated: YYYY-MM-DD
> Analysis scope: {{ANALYSIS_SCOPE — e.g., product spec, legacy code, standards documents, measured data, external API}}
> Authoring language: English (docstring_lang; default English; Korean (or other) projects switch via .harness.toml [language])

---

## Convention: the [CONFLICT] banner

Contradictions or open items between sources must be stated **inline as banners** in the body. No silent assumptions.

```text
> [CONFLICT] <identifier> — <one-line summary>
>   Source A: ...
>   Source B: ...
>   Provisional judgment: ... (rationale) | or "Open — routed to decision_pending.md <ID>"
```

- Once decided, remove the `[CONFLICT]` banner and replace it with the decision (a leftover banner causes drift).
- A CONFLICT that requires a domain-level choice is routed to `decision_pending.md`.
- A CONFLICT in the data-definition area is promoted to the spec (increment the spec Changelog version) and then the banner is removed.

---

## Table of Contents

**PART A — Product and Standards**
- A1. Product/System Overview
- A2. Hardware/Platform Specifications
- A3. Brand/UX Guidelines
- A4. Comparison Against Relevant Standards (if applicable)

**PART B — Data Specification (analysis — contract is promoted to the spec)**
- B1. Functional Requirements and User-Configurable Parameters
- B2. Parameter Tier Classification (Tier 1~3)
- B3. Measured Output Data Format (analysis — source of truth is `_TEMPLATE_data_spec.md`)

**PART C — System Architecture**
- C1. Tech Stack and Architecture Decisions
- C2. System Architecture Design Draft
- C3. SW Control/Analysis Design Draft
- C4. External Dependencies (Hardware/Vendor API): Responsibility Boundary and Interfaces

**PART D — SW Implementation Guide**
- D1. End-to-End Operation Process
- D2. Coding Convention Linkage
- D3. External Interface (GUI/API) Integration Spec Draft

**PART E — Project Status and Risks**
- E1. Development Progress and Legacy Code Analysis
- E2. Comprehensive Project Risk Analysis

**PART F — Legacy/Reference Software Analysis**
- F1. Analysis Overview and Target File List
- F2. Core Algorithm Comparison
- F3. Operational Control Element Analysis
- F4. Data Processing Pipeline
- F5. Insights for This Project and Differences

---

# PART A — Product and Standards

## A1. Product/System Overview `<a id="a1"></a>`

<!-- Product name/brand/main use/core value, 1~2 lines each. -->

## A2. Hardware/Platform Specifications `<a id="a2"></a>`

<!-- Lineup table / performance parameter table / configuration details. State whether measured or vendor-sourced. -->

## A3. Brand/UX Guidelines `<a id="a3"></a>`

## A4. Comparison Against Relevant Standards `<a id="a4"></a>`

---

# PART B — Data Specification (analysis)

> ⚠ This PART is **analysis/history**. The **contract (source of truth)** for columns, formulas, units, and DB mapping
> is owned by `docs/engineering/_TEMPLATE_data_spec.md` (frozen to v1.0 at Gate P).
> On conflict, the spec wins.

## B1. Functional Requirements and User-Configurable Parameters `<a id="b1"></a>`

## B2. Parameter Tier Classification (Tier 1~3) `<a id="b2"></a>`

## B3. Measured Output Data Format (analysis) `<a id="b3"></a>`

---

# PART C — System Architecture

## C1. Tech Stack and Architecture Decisions `<a id="c1"></a>`

## C2. System Architecture Design Draft `<a id="c2"></a>`

## C3. SW Control/Analysis Design Draft `<a id="c3"></a>`

## C4. External Dependency Responsibility Boundary and Interfaces `<a id="c4"></a>`

<!-- Summarize the division of responsibility for external dependencies (hardware/vendor API)
     tied to the safety boundary (.harness.toml [safety_boundary].paths). Mark anything undecided with [CONFLICT]. -->

---

# PART D — SW Implementation Guide

## D1. End-to-End Operation Process `<a id="d1"></a>`

## D2. Coding Convention Linkage `<a id="d2"></a>`

## D3. External Interface Integration Spec Draft `<a id="d3"></a>`

---

# PART E — Project Status and Risks

## E1. Development Progress and Legacy Code Analysis `<a id="e1"></a>`

## E2. Comprehensive Project Risk Analysis `<a id="e2"></a>`

<!-- Risk table: ID / description / impact / likelihood / mitigation / whether a feasibility spike is needed. -->

| Risk ID | Description | Impact | Mitigation | Spike Needed |
|:---|:---|:---|:---|:---:|
| R-00 | <example — external API behavior may differ from the docs> | <high/med/low> | <contingency> | ✅ / — |

---

# PART F — Legacy/Reference Software Analysis

## F1. Analysis Overview and Target File List `<a id="f1"></a>`

## F2. Core Algorithm Comparison `<a id="f2"></a>`

## F3. Operational Control Element Analysis `<a id="f3"></a>`

## F4. Data Processing Pipeline `<a id="f4"></a>`

## F5. Insights for This Project and Differences `<a id="f5"></a>`

---

## Appendix: Feasibility Spike Tests (required)

> Technical uncertainties (real external API behavior, algorithm accuracy, performance limits, etc.) are **not closed by estimation**.
> Verify them with a small spike experiment, record the result in `docs/experiments/_TEMPLATE_spike_report.md`,
> then reflect that conclusion in PART E/F above.

| Spike ID | Goal (hypothesis to verify) | Pass Criteria | Result Report | Status |
|:---|:---|:---|:---|:---:|
| SPK-00 | <example — hypothesis> | <measurable criterion> | `docs/experiments/SPK-00_spike_report.md` | [Pending] |
