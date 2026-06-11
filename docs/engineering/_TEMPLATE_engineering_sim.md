<!-- ROLE BANNER ───────────────────────────────────────────────────────────
  Phase: S2 Feasibility (Gate F) — validate core-technology claims with quantitative simulation.
  What this document decides: the model + assumptions + quantitative results + candidate
    (part/design) comparison + conclusion (adopted option).
  What this document does NOT decide: the data output contract (= data_spec) · implementation code.
  How to fill: requirements → model → assumptions (with basis) → results (tables/numbers) →
    candidates → conclusion, in that order.
    pair-with: scripts/simulate_*.py (reproducible computation script).
─────────────────────────────────────────────────────────────────────────── -->

# {{SIMULATION_TITLE}} Simulation ({{YYYY-MM-DD}})

> **Purpose**: {{SIMULATION_PURPOSE}}
>
> **Decision summary**: {{HEADLINE_DECISION}} <!-- latest decision, 1-3 lines -->

---

## § 1. Requirements

| Item | Value | Note |
|:--|:--|:--|
| {{REQUIREMENT}} | {{VALUE}} | {{NOTE}} |

---

## § 2. Model

> Governing equations / equivalent circuit / numerical scheme. State which physical/mathematical model is used to solve it.

```
{{GOVERNING_EQUATION}}
```

| Term | Expression | Meaning |
|:--|:--|:--|
| {{TERM}} | {{EXPRESSION}} | {{MEANING}} |

---

## § 3. Assumptions

> Attach a **basis** to every assumption. An assumption with no basis = 0 confidence in the result.

| # | Item | Value | Basis |
|:--|:--|:--|:--|
| 1 | {{ASSUMPTION}} | {{VALUE}} | {{BASIS}} |

---

## § 4. Results

### 4.1 {{RESULT_MATRIX_NAME}}

| {{VAR_1}} | {{VAR_2}} | {{OUTPUT}} | Assessment |
|:--:|:--:|:--:|:--:|
| {{v1}} | {{v2}} | {{out}} | {{eval}} |

> Worst-case / nominal-case summary: {{RESULT_SUMMARY}}

### 4.2 Sensitivity / scenario comparison (if applicable)

| Scenario | Condition | Result | Assessment |
|:--|:--|:--:|:--:|
| {{SCENARIO}} | {{CONDITION}} | {{RESULT}} | {{EVAL}} |

---

## § 5. Candidates

> Off-the-shelf parts/design options that meet the requirement. Prefer proven options over building your own (adopt after research).

| Option | Description | Pros | Cons | Availability |
|:--|:--|:--|:--|:--|
| {{OPTION}} | {{DESC}} | {{PRO}} | {{CON}} | {{SOURCE}} |

---

## § 6. Conclusion

### 6.1 Recommended specification

> {{RECOMMENDED_SPEC}}

### 6.2 Performance summary

| Condition | Result | Assessment |
|:--|:--:|:--:|
| {{CONDITION}} | {{RESULT}} | {{EVAL}} |

### 6.3 Next steps

1. {{NEXT_STEP_1}}
2. {{NEXT_STEP_2}}

---

## § 7. Deliverables

- `scripts/simulate_{{name}}.py` — {{SCRIPT_PURPOSE}} (reproducible)
- `docs/engineering/{{this_file}}.md` — this report

## § 8. References

- {{REFERENCE_1}}
- {{REFERENCE_2}}

---

## § 9. Change History (in-doc changelog)

| Date | Change | Author |
|:---|:---|:---|
| {{YYYY-MM-DD}} | v1.0 — first draft | {{AUTHOR}} |
