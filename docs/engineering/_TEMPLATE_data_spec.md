---
type: spec
---

<!-- ROLE BANNER ───────────────────────────────────────────────────────────
  Phase: S3 Planning / Gate P-1 (data-definition contract freeze).
  What this document decides: the output data's columns, formulas, units, ranges,
    and normal/boundary/failure values + DB schema mapping + the §3.1 CSV header
    (read by field_cascade.py) = single authority.
  What this document does NOT decide: the output sink (= erd template), the
    identifier/unit anchor constants (= identifier_unit_contract template), or the
    legacy-leak audit (= assumption_leak_audit template).
  How to fill: replace each {{PLACEHOLDER}} with the real domain value, freeze at
    v1.0, then enter Executing (pipeline code). If left blank, Gate P is blocked.
─────────────────────────────────────────────────────────────────────────── -->

# {{DATA_SPEC_TITLE}} Data Specification

> **This document is the single authoritative specification for the {{OUTPUT_NAME}} output data.**
> All future changes to the data definition are made in this file with a version increment in its Changelog.
> Other scattered materials (analysis reports, decision trackers, outsourced/vendor manuals, etc.) are demoted to **cited sources / historical references** of this specification,
> and **operational use refers only to the latest version of this specification**.

---

## Metadata

| Item | Value |
|:---|:---|
| Document ID | `{{SPEC_DOC_ID}}` |
| Current version | **{{VERSION}}** <!-- must be frozen at v1.0 to pass Gate P-1 --> |
| Created | {{YYYY-MM-DD}} |
| Last updated | {{YYYY-MM-DD}} |
| Authority level | **Authoritative — takes precedence over other materials** |
| Target output | {{OUTPUT_FILE_OR_STREAM}} ({{N_COLUMNS}} columns) |
| Applied at | {{WHERE_APPLIED}} <!-- e.g. DB schema / calculation engine / frontend --> |

---

## Changelog

> When changing, follow the §12 procedure and add a row to this table. **Do not update other materials as a workaround.**

| Version | Date | Change | Decided by |
|:---:|:---:|:---|:---|
| **v1.0** | {{YYYY-MM-DD}} | <!-- First consolidated specification. List the source materials that were merged. --> | {{DECIDER}} |

---

## 1. Overview

### 1.1 Authority of this specification

This specification is the **single authoritative definition** of the {{OUTPUT_NAME}} output data. The following principles apply.

1. **Authority precedence**: this specification > {{UPSTREAM_SOURCE_1}} > {{UPSTREAM_SOURCE_2}} > developer estimates
2. **On conflict with other materials**: the latest version of this specification wins
3. **For items not in this specification**: consult analysis/discussion materials → after a decision, merge into this specification with a version increment

### 1.2 What this specification defines

- The **complete definition of all {{N_COLUMNS}} columns** of {{OUTPUT_NAME}} (unit, meaning, formula, validity, measurement range, DB storage form)
- The distinction between columns we compute ourselves and columns **we do not compute** (kept only for compatibility)
- Operational constraints
- DB schema mapping (the `{{TABLE_NAME}}` table)

### 1.3 What this specification does not define

- {{OUT_OF_SCOPE_1}} — separate specification
- {{OUT_OF_SCOPE_2}} — separate material

---

## 2. Scope

### 2.1 Target

{{TARGET_DESCRIPTION}}

### 2.2 Output form

- Identifier: {{OUTPUT_FILE_OR_STREAM}}
- Column count: {{N_COLUMNS}}
- Output cadence: {{OUTPUT_CADENCE}}
- Encoding: UTF-8
- Header: 1:1 aligned with §3.1 (single source for code constants)

### 2.3 Data flow

```
{{SOURCE}} → {{TRANSFORM_1}} → {{TRANSFORM_2}} → {{SINK}} → {{CONSUMER}}
```

---

## 3. Output Format ({{N_COLUMNS}} columns)

<!-- ⚠ The "### 3.1" heading + the text code-fence block below are parsed by
     scripts/field_cascade.py via regex. Keep the heading and fence structure intact
     and separate column names with commas. Do not place any comment or sentence
     between the heading and the fence (the generator would mistake that text for a
     column). Mark an empty trailing column with the 'blank' token so the generator
     excludes it. -->

### 3.1 Header definition (fixed order)

```text
{{COLUMN_1}}, {{COLUMN_2}}, {{COLUMN_3}},
{{COLUMN_4}}, {{COLUMN_5}}
```

### 3.2 Alignment with external format (if applicable)

- {{COLUMN_RANGE_A}}: aligned with {{EXTERNAL_SPEC}} (format-adoption policy stated)
- {{COLUMN_RANGE_B}}: extension fields not present externally — own policy (see §10)

---

## 4. Measurement/Generation Geometry (if applicable)

> If the data is derived from physical measurement, put the coordinate system, geometry, and calibration model here. For pure SW output, omit this section.

| Item | Value | Source |
|:---|:---:|:---|
| {{GEOMETRY_PARAM}} | {{VALUE}} | {{SOURCE}} |

---

## 5. Per-Column Definitions ({{N_COLUMNS}} items)

### 5.1 Metadata

| # | field | Meaning | Unit | DB type | Note |
|:---:|:---|:---|:---|:---|:---|
| 1 | `{{COLUMN_1}}` | {{MEANING}} | {{UNIT}} | `{{DB_TYPE}}` | {{NOTE}} |

### 5.2 Measured values — formulas finalized

| # | field | Meaning | Unit | DB type | Formula | Validation |
|:---:|:---|:---|:---|:---|:---|:---|
| {{N}} | `{{COLUMN_X}}` | {{MEANING}} | {{UNIT}} | `{{DB_TYPE}} CHECK ({{RANGE}})` | {{FORMULA}} | {{VALIDATION_BASIS}} |

### 5.3 Validity Status

| # | field | Meaning | DB type | Meaning |
|:---:|:---|:---|:---|:---|
| {{N}} | `{{COLUMN_STATUS}}` | Validity state of {{MEANING}} | `INT (0/1)` | 1 = valid, 0 = invalid |

> **Condition for 0**: {{INVALID_CONDITIONS}}. The exact threshold is {{THRESHOLD_SOURCE}} (no hardcoding — supply externally as a config variable).

### 5.4 Not computed by us (kept only for compatibility, if applicable)

> **Policy**: not computed by our system. Keep the header for compatibility but always output NULL/0.
> If we add our own computation later, increment this specification's version and change the policy.

| # | field | Output policy | DB type |
|:---:|:---|:---|:---|
| {{N}} | `{{COLUMN_PLACEHOLDER}}` | Always NULL/0 | `{{DB_TYPE}} NULLABLE` |

---

## 6. Formula Collection (formula authority)

> Keep both the normal-value formulas and the **boundary/failure-value handling** in one place. Time-averaging windows and rolling windows are config parameters (§8.4).

### 6.1 {{FORMULA_GROUP_1}}

```
{{FORMULA_1}}
```

- Parameter source: {{PARAM_SOURCE}} (no hardcoding — injected via config)
- Validation basis: {{VALIDATION_BASIS}}

---

## 7. Validity / Status Policy

### 7.1 General principles

- Every status: `1 = valid`, `0 = invalid`
- Condition for 0: {{INVALID_CONDITIONS}}
- Threshold source: {{THRESHOLD_SOURCE}} (external config variable)

### 7.2 Missing-data gate policy (if applicable)

{{SYNC_GATE_POLICY}} — on missing input, suspend computation + value NULL + status 0.

---

## 8. Operational Constraints

### 8.1 Boundary/safety constraints

{{BOUNDARY_CONSTRAINTS}}

### 8.2 Measurement ranges

| Item | Range | DB CHECK |
|:---|:---:|:---|
| `{{COLUMN_X}}` | {{RANGE}} | `{{CHECK_EXPR}}` |

### 8.3 Time/cadence model (if applicable)

{{TIMING_MODEL}} — explicitly separate the evaluation instant, the window, and the clock (monotonic vs epoch).

### 8.4 Operational input parameters (Config) — single authority

> This table is the **single authoritative definition** of operational parameters. Other documents/code **reference** this table and must not redefine it
> (double definition = drift). All are injected via settings/UI → Config (no hardcoding).

| Parameter | Config field | Definition | Unit | Default | Applied output (formula) | Basis |
|:---|:---|:---|:---:|:---:|:---|:---|
| {{PARAM_NAME}} | `{{config_field}}` | {{DEFINITION}} | {{UNIT}} | {{DEFAULT}} | {{APPLIED_TO}} | {{BASIS}} |

---

## 9. DB Schema Mapping (the `{{TABLE_NAME}}` table)

### 9.1 Column mapping

Output column name → DB column name (snake_case):

| Output | DB | Type | CHECK |
|:---|:---|:---|:---|
| `{{COLUMN_1}}` | `{{db_column_1}}` | `{{DB_TYPE}}` | {{CHECK}} |

### 9.2 PK / Index

- PK: `({{PK_COLUMNS}})` — {{PK_RATIONALE}}
- Index: `({{INDEX_COLUMNS}})` {{INDEX_PURPOSE}}

> Identifier-layer authority (internal-ID ↔ external-ID Mapper) and the ts unit anchor are owned by [`_TEMPLATE_identifier_unit_contract.md`](./_TEMPLATE_identifier_unit_contract.md). Table relationships and the Mapper doctrine are in [`_TEMPLATE_erd.md`](./_TEMPLATE_erd.md).

---

## 10. Open Items

| ID | Item | Status | Impact |
|:---|:---|:---:|:---|
| {{ID}} | {{ITEM}} | ⏳ {{STATUS}} | {{IMPACT}} |

> Entering Executing is safe only when these items are empty. If any remain open, isolate them with a placeholder/facade + guard.

---

## 11. Authoritative Sources (cited materials)

> This specification is based on the following materials. However, since this specification is the authority apex, it takes precedence over the cited materials on conflict.

| Material | Location | Cited part |
|:---|:---|:---|
| {{SOURCE_NAME}} | {{SOURCE_LOCATION}} | {{CITED_PART}} |

---

## 12. Change Procedure

When modifying this specification, apply the following procedure:

1. Confirm the change reason + supporting material
2. Add a new version row to the §Changelog in this file (date + change + decided by)
3. Modify the affected sections
4. Verify code/document synchronization per the §12.2 synchronization checklist
5. Add a reference link to the latest version of this specification in the affected scattered materials

### 12.1 Version increment rules

| Change type | Version increment |
|:---|:---:|
| Simple typo/wording fix | patch (v1.0 → v1.0.1) |
| Add/change a column definition, formula, or CHECK constraint | minor (v1.0 → v1.1) |
| Add/remove a header column, or change the data flow | major (v1.0 → v2.0) |

### 12.2 Synchronization checklist on change (impact scope)

> The concrete list for §12 step 4. When this spec's definition changes, **be sure to synchronize the code below so it does not diverge from the spec**
> (directly tied to data reliability). Path roots follow `.harness.toml` [paths] (`{{SRC_ROOT}}` / `{{TESTS_ROOT}}`).

**Synchronization code by trigger** (spec change → must update):

| Change type | Code to synchronize |
|:---|:---|
| Add/remove a column | `{{SRC_ROOT}}/{{header_constants}}` · `{{SRC_ROOT}}/{{db_schema}}` · `{{SRC_ROOT}}/{{repository}}` |
| Change a range/type/CHECK | `{{SRC_ROOT}}/{{db_schema}}` (CHECK constraint) |
| Change a formula | `{{SRC_ROOT}}/{{calc_engine}}` |
| Row assembly / storage path | `{{SRC_ROOT}}/{{row_builder}}` · `{{SRC_ROOT}}/{{storage_service}}` |
| Validation (tests) | `{{TESTS_ROOT}}/unit/{{test_row_builder}}` · `{{TESTS_ROOT}}/unit/{{test_calc_engine}}` |

**Key dependent documents**: [`_TEMPLATE_erd.md`](./_TEMPLATE_erd.md) (DB schema mapping) · [`_TEMPLATE_identifier_unit_contract.md`](./_TEMPLATE_identifier_unit_contract.md). For the full dependent-document list: `docs/_field_cascade.md` or grep `{{SPEC_DOC_ID}}`.

---

**[END OF SPECIFICATION {{VERSION}}]**
