<!-- ROLE BANNER ───────────────────────────────────────────────────────────
  Phase: S2 Feasibility (Gate F) — a spike that validates core-technology claims with a real prototype/measurement.
  What this document decides: whether the hypothesis meets the hard requirements
    (hypothesis-result matrix) + operational impact + the list of open vendor questions.
    Prevents discovering "the core technology can't meet the requirement" only at integration time.
  What this document does NOT decide: the data output contract (= data_spec) · implementation
    (a spike may be throwaway).
  How to fill: purpose → baseline (what to compare against) → environment → method+result →
    hypothesis matrix (adopt/reject) → operational impact → vendor questions → conclusion.
    pair-with: scripts/verify_*.py (reproduction script).
─────────────────────────────────────────────────────────────────────────── -->

# Experiment Report — {{SPIKE_TITLE}}

> **Experiment date**: {{YYYY-MM-DD}}
> **Target**: {{TARGET_DEVICE_OR_TECH}}
> **Verifier**: {{VERIFIER}}
> **Purpose**: {{SPIKE_PURPOSE}} <!-- e.g. promote simulation → real prototype / diagnose whether hard requirements are met -->
> **Conclusion summary**: {{HEADLINE_RESULT}} <!-- 1-2 lines: what succeeded / what is unresolved -->

---

## § 1. Experiment Purpose

### 1.1 Primary goal
{{PRIMARY_GOAL}}

### 1.2 Secondary goal (feasibility diagnosis)
{{SECONDARY_GOAL}} <!-- e.g. quantitatively measure the hard requirement (1 Hz / response ≤ X ms) -->

### 1.3 Baseline for comparison

> What are "sufficient/insufficient" judged against. Spec example values / prior measurements / code defaults.

| Baseline | Value | Source |
|:--|:--|:--|
| {{BASELINE_ITEM}} | {{VALUE}} | {{SOURCE}} |

---

## § 2. Experiment Environment (Env)

### 2.1 Hardware

| Item | Value |
|:--|:--|
| {{HW_ITEM}} | {{VALUE}} |

### 2.2 Software

| Item | Value |
|:--|:--|
| {{SW_ITEM}} | {{VALUE}} |
| Verification script | `scripts/verify_{{name}}.py` |

### 2.3 Operational settings (common to all experiments)

| Item | Value |
|:--|:--|
| {{SETTING}} | {{VALUE}} |

---

## § 3. Method + Result

> Pair the method and result for each experiment step. Report quantitative measurements with statistics (min/avg/max/p50/p95).

### 3.1 Experiment N — {{EXPERIMENT_NAME}}

**Method**:
1. {{STEP_1}}
2. {{STEP_2}}

**Result**:

| Statistic | min | avg | max | p50 | p95 |
|:--|:--:|:--:|:--:|:--:|:--:|
| {{METRIC}} | {{min}} | {{avg}} | {{max}} | {{p50}} | {{p95}} |

Observation: {{OBSERVATION}}

---

## § 4. Hypothesis Matrix

> Lay out every possible cause hypothesis and adopt/reject it with data. Prevents single-hypothesis confirmation bias.

| Hypothesis | Result | Basis |
|:--|:--:|:--|
| H1: {{HYPOTHESIS_1}} | ❌ reject \| ✅ adopt | {{EVIDENCE}} |
| H2: {{HYPOTHESIS_2}} | ❌ reject \| ✅ adopt | {{EVIDENCE}} |

### 4.1 Decisive conclusion

> {{DECISIVE_CONCLUSION}} <!-- the adopted hypothesis in 1 line + a basis summary -->

---

## § 5. Operational Impact Analysis

### 5.1 Requirement vs measurement

| Item | Required | Measured | Gap |
|:--|:--:|:--:|:--:|
| {{REQUIREMENT}} | {{REQUIRED}} | {{MEASURED}} | {{GAP}} |

### 5.2 Resolution paths

| Path | Description | Validation status |
|:--|:--|:--|
| A. {{PATH_A}} | {{DESC}} | {{STATUS}} |
| B. {{PATH_B}} | {{DESC}} | {{STATUS}} |
| C. {{PATH_C}} (adjust the requirement) | {{DESC}} | {{STATUS}} |

---

## § 6. Vendor/External Inquiry Items

> The open items to ask the external party/vendor after this experiment secures quantitative data.

| # | Item | Data from this experiment |
|:--:|:--|:--|
| 1 | {{VENDOR_QUESTION_1}} | {{SUPPORTING_DATA}} |

---

## § 7. Conclusion

| Aspect | Result |
|:--|:--|
| {{ASPECT_1}} | ✅ / ⚠ / 🟡 {{RESULT}} |

> {{FINAL_STATEMENT}}

---

## § 8. Deliverables

### 8.1 Code

| File | Content |
|:--|:--|
| `scripts/verify_{{name}}.py` | {{SCRIPT_PURPOSE}} (reproducible) |

### 8.2 Documents

| File | Content |
|:--|:--|
| `docs/experiments/{{this_file}}.md` | this report |

---

## § 9. User Review Items

1. {{REVIEW_ITEM_1}}
2. {{REVIEW_ITEM_2}}

---

> **This report can serve as the quantitative basis for the next step (vendor negotiation / requirement adjustment / additional validation).**
