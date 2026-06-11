<!-- ROLE BANNER ───────────────────────────────────────────────────────────
  Phase: S3 Planning / Gate P-3 (identifier & unit contract freeze).
  What this document decides: the per-layer Object-Identifier authority
    (Hardware/Object = internal-id, DB/External = external-id, Repository = Mapper)
    + anchor constants (timestamp unit, id base) — the single set of values nailed
    down before entering Executing.
  What this document does NOT decide: column formulas (= data_spec) · table
    relationships (= erd).
  How to fill: fill the anchor-constant table with real values and freeze at v{{X}}.
    If left blank, you risk retrofitting the Mapper and a DB CHECK violation
    (e.g. an angle exceeding its range → INSERT rollback = data loss).
─────────────────────────────────────────────────────────────────────────── -->

# {{PROJECT_NAME}} Identifier & Unit Contract

> **This document is the single authoritative contract for {{PROJECT_NAME}}'s identifier-layer authority + unit anchor constants.**
> [`_TEMPLATE_data_spec.md`](./_TEMPLATE_data_spec.md) (column definitions) and [`_TEMPLATE_erd.md`](./_TEMPLATE_erd.md) (table relationships)
> **reference** this contract's anchor values and must not redefine them.

---

## Metadata

| Item | Value |
|:---|:---|
| Document ID | `{{CONTRACT_DOC_ID}}` |
| Current version | **{{VERSION}}** |
| Created | {{YYYY-MM-DD}} |
| Authority level | **Authoritative (anchor constants — code/schema follow this table)** |
| Freeze point | **Before entering Executing (pipeline code)** (Gate P-3) |

---

## Changelog

| Version | Date | Change | Decided by |
|:---:|:---:|:---|:---|
| **{{VERSION}}** | {{YYYY-MM-DD}} | <!-- First contract. Freeze the layer authority + anchor constants. --> | {{DECIDER}} |

---

## 1. Layered Object-Identifier Authority

> **Principle**: each layer of the system uses the **natural identifier** of its own domain as the authority. Forcing one
> identifier across all layers creates an unnatural conversion somewhere. Instead, **the Repository takes the conversion responsibility as a Mapper.**

| Layer | Identifier kind | Identifier | Authority source |
|:---|:---|:---|:---|
| 1. Source / Hardware | **internal-id** | `{{internal_id}}` | {{SOURCE_AUTHORITY}} |
| 2. Backend Object Model | **internal-id** (kept) | `{{internal_id}}` | natural flow from Source |
| 3. Database Schema | **external-id** | `{{external_id}}` | spec §9 (Primary Key) |
| 4. External Interface | **external-id** (output) | `{{external_id}}` | spec §3.1 header |

- **internal-id** = the identifier the source/hardware/object model naturally uses (e.g. an index, a handle).
- **external-id** = the identifier the DB/external interface uses meaningfully (e.g. a measured distance, a domain key).
- **Repository = Mapper**: a single point in the Repository handles the Layer 2 ↔ Layer 3 conversion.

```
Layer1 internal-id → Layer2 internal-id ──[Repository Mapper]──→ Layer3 external-id → Layer4 external-id
                                          ←──[reverse conversion (query)]────
```

### 1.1 Mapper conversion point (single point)

| Direction | Location | Conversion |
|:---|:---|:---|
| Store (internal → external) | `{{SRC_ROOT}}/{{repository}}.insert(...)` | `{{MAP_TABLE}}[{{internal_id}}] → {{external_id}}` |
| Query (external → internal) | `{{SRC_ROOT}}/{{repository}}.query(...)` | `{{external_id}} → index → {{internal_id}}` |

### 1.2 Why this separation is not a stopgap

| Review item | Assessment |
|:---|:---|
| Keep deprecated + run new structure in parallel? | ❌ — both identifiers are legitimate authorities |
| Work around a wrong assumption? | ❌ — respects the natural flow of each layer |
| Two systems coexisting? | ❌ — responsibility is explicitly separated by the Mapper |
| Accumulating future correction cost? | ❌ — only a single conversion point in the Repository to manage |

---

## 2. Anchor Constants (frozen before entering Executing)

> **The values in this table are nailed down before coding begins.** Changing them later cascades rework across the Mapper, DB CHECK, formats, and the frontend.
> If undecided, use a **documented placeholder + guard** instead of a guessed real value.

### 2.1 Timestamp unit anchors

| Context | Unit | Constant/field | Note |
|:---|:---|:---|:---|
| DB store (high-resolution table) | {{epoch_ms_or_s}} | `{{TS_UNIT_CONST}}` | absolute time (UTC) |
| DB store (aggregate table) | {{epoch_ms_or_s}} | `{{TS_UNIT_CONST_AGG}}` | bin start time |
| External output representation | {{ISO_OR_EPOCH}} | — | conversion at the display stage only |
| **Internal timing control** | monotonic (unit-agnostic) | `{{MONOTONIC_SRC}}` | elapsed/evict decisions. **Unaffected by wall-clock going backward** |

> **Dual-timestamp principle**: the clock for window elapsed/evict decisions = **monotonic**, the ts stored in the DB = **epoch**. Never mix them.

### 2.2 Identifier base / range anchors

| Item | Value | Constant | Note |
|:---|:---|:---|:---|
| {{internal_id}} base | {{ID_BASE}} (0-based / 1-based) | `{{ID_BASE_CONST}}` | single source to prevent off-by-one |
| {{external_id}} valid range | {{EXTERNAL_RANGE}} | `{{RANGE_CONST}}` | must match the DB CHECK |

### 2.3 Numeric range / angle normalization anchors (if applicable)

| Item | canonical range | Normalization rule | Note |
|:---|:---|:---|:---|
| {{ANGLE_FIELD}} | {{ANGLE_RANGE}} | {{NORMALIZE_RULE}} | DB CHECK ⊇ canonical (compatible). Separate conversion at the display stage only |

> ⚠ If the canonical range and the DB CHECK diverge, an INSERT rolls back at a boundary value (e.g. an endpoint) = **data loss**.
> Keep the normalization helper as a single function (`{{normalize_helper}}`); do not reimplement it per module.

---

## 3. Unit Consistency Rules

- Pick **one standard unit** per physical quantity and convert only at the boundaries (input/store/output).
- Conversion functions are a single source. Do not mix deg↔rad, m↔km, ms↔s.
- Normalize external data (API/file/vendor) to the standard unit immediately at the boundary.

| Quantity | Standard unit | Conversion boundary |
|:---|:---|:---|
| {{QUANTITY}} | {{STD_UNIT}} | {{CONVERSION_BOUNDARY}} |

---

## 4. Related Authoritative Materials

| Area | Authoritative document |
|:---|:---|
| Column definitions/formulas | [`_TEMPLATE_data_spec.md`](./_TEMPLATE_data_spec.md) |
| Table relationships/Mapper flow | [`_TEMPLATE_erd.md`](./_TEMPLATE_erd.md) §2.2 |

---

**End of document.**
