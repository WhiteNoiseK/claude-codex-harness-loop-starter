<!-- ROLE BANNER ───────────────────────────────────────────────────────────
  Phase: S2 Feasibility (Gate F) — a trade study of algorithm/technology options.
  What this document decides: the method matrix → quantitative comparison → assessment of
    the current implementation → a staged upgrade path + the adoption threshold for each stage.
  What this document does NOT decide: the data output contract (= data_spec) · immediate
    implementation (deferred if below threshold).
  How to fill: list every candidate (matrix) → quantitative basis (papers/measurements) →
    pros/cons of the current implementation → state the threshold as "at Phase N, if X then adopt Y".
    An upgrade with no threshold = endless tuning.
─────────────────────────────────────────────────────────────────────────── -->

# {{TRADE_STUDY_TITLE}} Trade Study

| Item | Value |
|:---|:---|
| Created | {{YYYY-MM-DD}} |
| Subject | {{SUBJECT}} |
| Trigger | {{TRIGGER}} <!-- the requirement/feature that triggered this study --> |
| Current implementation | `{{SRC_ROOT}}/{{current_impl}}` — {{CURRENT_METHOD}} |
| Conclusion | **Phase 1 = keep the current implementation**, with staged Phase 2 upgrade candidates ({{UPGRADE_PATH}}) |

---

## 1. Background — What {{SUBJECT}} Means

> What is being traded off. State the difference between "works correctly" and "works optimally" in 1-2 paragraphs.

{{BACKGROUND}}

---

## 2. Method Matrix (list every candidate)

| # | Method | Precision | Complexity | Real-time | Note |
|:---:|:---|:---:|:---:|:---:|:---|
| 1 | **{{METHOD_1}}** ← current implementation | {{P}} | {{C}} | {{RT}} | {{NOTE}} |
| 2 | {{METHOD_2}} | {{P}} | {{C}} | {{RT}} | {{NOTE}} |

### 2.1 Quantitative performance comparison (basis: {{QUANT_SOURCE}})

| Compared against | Improvement of {{BEST_METHOD}} |
|:---|:---|
| {{BASELINE_METHOD}} | {{IMPROVEMENT}} |

---

## 3. Detailed Assessment of the Current Implementation ({{CURRENT_METHOD}})

### 3.1 Algorithm

{{CURRENT_ALGORITHM}}

### 3.2 Strengths

| Item | Rating |
|:---|:---|
| {{STRENGTH}} | {{RATING}} |

### 3.3 Weaknesses

| Item | Impact |
|:---|:---|
| {{WEAKNESS}} | {{IMPACT}} |

### 3.4 Measured validation (if any)

- {{MEASURED_FINDING}}

---

## 4. Current Industry/Academic Practice (optional)

| Vendor/Research | System | Algorithm (public part) |
|:---|:---|:---|
| {{VENDOR}} | {{SYSTEM}} | {{ALGORITHM}} |

---

## 5. Upgrade Path + Adoption Thresholds

> ★ State a **quantitative adoption threshold** for each stage. An upgrade with no threshold is endless tuning.

### 5.1 Phase 1 ({{PHASE1_WINDOW}})

**Decision: keep the current {{CURRENT_METHOD}}**
- Reason: {{PHASE1_RATIONALE}} (proven code, schedule first, avoid change risk)
- Immediate tasks: {{PHASE1_IMMEDIATE_TASKS}}

### 5.2 Phase 2 ({{PHASE2_WINDOW}})

**Staged upgrade (conditional adoption)**:

#### Step 1 — {{UPGRADE_STEP_1}} (low-cost first pass)
- Method: {{STEP1_METHOD}}
- Cost: {{STEP1_COST}}
- **Adoption threshold**: {{STEP1_THRESHOLD}} <!-- e.g. 100-case A/B comparison → adopt if the metric improves by ≥ X -->

#### Step 2 — {{UPGRADE_STEP_2}} (after validation)
- Method: {{STEP2_METHOD}}
- Cost: {{STEP2_COST}}
- **Adoption threshold**: {{STEP2_THRESHOLD}}

#### Step 3 — {{UPGRADE_STEP_3}} (highest precision)
- Method: {{STEP3_METHOD}}
- Cost: {{STEP3_COST}}
- **Adoption threshold**: {{STEP3_THRESHOLD}}

---

## 6. Alignment with the Output Contract

> Changing the algorithm may shift the output values → check the impact on data_spec alignment.

- Definition of {{OUTPUT_FIELD}}: {{IMPACT_ON_OUTPUT}} (on change, verify alignment with [`_TEMPLATE_data_spec.md`](./_TEMPLATE_data_spec.md))

---

## 7. Decisions and Next Steps

### 7.1 Immediate decisions
- ✅ Phase 1: keep the current {{CURRENT_METHOD}}

### 7.2 External/vendor confirmation needed
- [ ] {{VENDOR_QUESTION}}

### 7.3 Phase 2 evaluation trigger conditions
- When {{TRIGGER_CONDITION}} → consider introducing {{UPGRADE_STEP}}

---

## 8. References

### Academic/standards
- {{ACADEMIC_REF}}

### Internal documents
- `{{SRC_ROOT}}/{{current_impl}}` — current implementation
- [`_TEMPLATE_data_spec.md`](./_TEMPLATE_data_spec.md) — output definition

---

## 9. Change History

| Date | Change | Author |
|:---|:---|:---|
| {{YYYY-MM-DD}} | v1.0 — method comparison and recommended Phase 1/2 path | {{AUTHOR}} |
