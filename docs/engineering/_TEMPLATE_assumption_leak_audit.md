<!-- ROLE BANNER ───────────────────────────────────────────────────────────
  Phase: S3 Planning / Gate P-4 (legacy-leak audit) — ★ MANDATORY when this kit is cloned.
  What this document decides: whether assumptions from a previous project/domain
    (coordinate systems, formulas, constants, identifiers) have leaked into the new
    domain's code/docs → the classification of each finding (RESOLVED|OK|CONTAMINATED).
  What this document does NOT decide: new feature design (= data_spec/erd) — this
    document is solely for contamination removal.
  How to fill: fix the authority baseline → state the search keywords/scope → fill the
    findings table → there must be 0 CONTAMINATED findings to enter Executing.
    (Especially mandatory if any reused/ported code exists.)
─────────────────────────────────────────────────────────────────────────── -->

# Legacy Assumption Residue Audit Report ({{SCOPE_LABEL}} Sweep)

> **★ This audit is MANDATORY when this kit is cloned into a new project (or when porting previous code/references).**
> Confirm whether assumptions from the previous domain (coordinate system, geometry, formulas, constants, identifiers) remain in the new domain's code/docs.
> Any root-level contamination found (CONTAMINATED) must be **fixed immediately before entering Executing**.

---

## Metadata

| Item | Value |
|:---|:---|
| Document ID | `{{AUDIT_DOC_ID}}` |
| Audit date | {{YYYY-MM-DD}} |
| Audit scope | {{AUDIT_SCOPE}} <!-- e.g. root-assumption contamination (coordinate system, formulas, constants, identifiers) --> |
| Audit exclusions | {{DEFERRED_SCOPE}} <!-- e.g. Deep Audit (units, NaN, boundaries) — follow-up --> |
| Authority baseline | {{AUTHORITY_BASIS}} <!-- e.g. data_spec §x + identifier_unit_contract + vendor materials --> |
| Result | <!-- ✅ clean — 0 CONTAMINATED / ⚠ N found → correction needed --> |

---

## 1. Audit Motivation

> Why audit now. (e.g. reused/ported code may carry assumptions from a previous domain.)

{{AUDIT_MOTIVATION}}

---

## 2. Audit Method

### 2.1 Authority baseline (the ground truth)

> The single authoritative documents that serve as the "ground truth" of the audit. If the code diverges from these, the code is wrong.

- {{AUTHORITY_DOC_1}} — {{CITED_SECTION}}
- {{AUTHORITY_DOC_2}} — {{CITED_SECTION}}

### 2.2 Search keywords

> Keywords that reveal previous-domain assumptions. Three groups: direct keywords + suspected coordinate systems/constants + latent assumption expressions.

**Direct**: {{KW_DIRECT}}

**Suspected constants/identifiers**: {{KW_SUSPECT}}

**Latent assumption expressions**: {{KW_LATENT}}

### 2.3 Search scope (code + docs)

- **Code** (`{{SRC_ROOT}}/`): {{N_CODE_FILES}} files (read-only scan)
- **Docs** (`docs/`): research.md / plan.md / progress.md / *_design.md / engineering/ (excluding the authoritative spec) / external materials

---

## 3. Findings

> Classification legend: **RESOLVED** = a past correction is documented (not residue) · **OK** = legitimate in the new domain (false positive) ·
> **CONTAMINATED** = active contamination (immediate correction target).

### 3.1 Code (`{{SRC_ROOT}}/`)

| # | Location | Keyword | Classification | Note |
|:-:|:---|:---|:---:|:---|
| 1 | `{{SRC_ROOT}}/{{file}}` L{{line}} | {{keyword}} | RESOLVED \| OK \| CONTAMINATED | {{note}} |

**Active contamination (CONTAMINATED): {{N}}**
**False positives/already corrected: {{N}}**

### 3.2 Docs (`docs/`)

| # | Location | Keyword | Classification | Note |
|:-:|:---|:---|:---:|:---|
| 1 | `docs/{{file}}` L{{line}} | {{keyword}} | RESOLVED \| OK \| CONTAMINATED | {{note}} |

**Active contamination (CONTAMINATED): {{N}}**

### 3.3 Single-authority specification

- {{SPEC_FILE}} — {{KW_DIRECT}} {{N}} found

---

## 4. Analysis — How the Contamination Got In (trace-back, if found)

> If there is any CONTAMINATED finding, trace back how it got mixed into the new domain (to prevent recurrence).

1. {{LEAK_PATH_STEP_1}}
2. {{LEAK_PATH_STEP_2}}

**Correction trigger**: {{CORRECTION_TRIGGER}}

---

## 5. Conclusion

### 5.1 Sweep result (all areas)

<!-- ✅ active contamination: 0  /  ⚠ N → correct before entering -->

| Area | Authority | Result |
|:---|:---|:---|
| {{AREA}} | {{AUTHORITY}} | {{RESULT}} |

### 5.2 Gaps found (not contamination)

> "Incompleteness of in-progress work" or "external dependency" is not contamination — distinguish and record it.

| Area | Gap | Classification | Handling plan |
|:---|:---|:---|:---|
| {{AREA}} | {{GAP}} | in-progress \| external-dependency | {{PLAN}} |

### 5.3 Whether Executing can be entered

<!-- ✅ can enter (0 CONTAMINATED) / ❌ blocked (N CONTAMINATED need correction) -->

Basis:
1. {{REASON_1}}
2. {{REASON_2}}

### 5.4 Items deferred to the follow-up (Deep Audit)

- {{DEFERRED_ITEM_1}}
- {{DEFERRED_ITEM_2}}

---

## 6. Recommendations

### 6.1 Immediate corrections

- {{IMMEDIATE_FIX}} <!-- "none" if 0 CONTAMINATED -->

### 6.2 Next steps

- {{NEXT_STEP}}

---

## 7. Related Materials

- Authoritative spec: [`_TEMPLATE_data_spec.md`](./_TEMPLATE_data_spec.md)
- Identifier/unit contract: [`_TEMPLATE_identifier_unit_contract.md`](./_TEMPLATE_identifier_unit_contract.md)

---

**End of document.**
