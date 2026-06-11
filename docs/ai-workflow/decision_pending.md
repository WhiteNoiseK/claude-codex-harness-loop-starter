# Issues Awaiting User Decision (Decision Pending)

<!-- ROLE BANNER: architect (user) decision queue — collects domain-level choices before starting Phase 3.
     What this document decides: "what is awaiting a user decision, and where the decision is reflected once made".
     Each item: once decided, immediately remove the [CONFLICT] banner in research.md + reflect in plan.md DoD + log it. -->

> **Purpose**: gather, in one place, the domain-level choices that require the user (architect)'s explicit decision before implementation starts.
>
> **Status legend**: ⚠ blocked (cannot start before decision) / 🟡 caution (can proceed with a workaround) / ✅ resolved (kept for reference)

---

## 1. [Example] <DECISION-ID> — <one-line title> ⚠ blocked

**Location**: `research.md` <§ or line>

<!-- Present options as a table. However, do NOT present a value already defined by a single-authority spec as an option
     (it is to be followed; if code ≠ spec, the code is wrong). Only ask about what is open (process/wiring/spec refinement). -->

| Option | Content | Stability | Maintainability | Code Visibility | Security |
|:---|:---|:---|:---|:---|:---|
| A | <option A> | <assessment> | <assessment> | <assessment> | <assessment> |
| B | <option B> | <assessment> | <assessment> | <assessment> | <assessment> |

<!-- 4-axis scorecard per docs/pm-guide/recommendation_policy.md §1 (Security = attack surface / input validation / secret exposure). -->


**Blocked task**: <M-task ID>

---

## 2. Decision Intake Process

The user adds a **[DECISION XXX]** line directly to this document, or delivers it in a separate message:

```text
Example:
[DECISION D-01] Option = B, initial implementation scope = single, applies to task = M1-02
```

Upon receiving a decision, the AI agent automatically:
1. Removes the [CONFLICT] / [implementation stub] banner in `research.md` + reflects the decision
2. Updates the DoD of the relevant M-task in `plan.md`
3. Records the decision date/content in `implementation_log.md`
4. Removes the item from the "Blockers" section of `progress.md`

---

## 3. Blocker Summary

| # | Issue | Status | Blocked Milestone |
|---|------|-----|-------------------|
| — | none | — | — |

**Resolution history**:
- (none)
