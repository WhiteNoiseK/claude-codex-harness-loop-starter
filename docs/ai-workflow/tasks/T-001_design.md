# T-001 Design — <task title>

<!-- ROLE BANNER: per-task design (trio 3/3: research → plan → design).
     What this document decides: interface signatures/data flow/contract (Args·Returns·Raises).
     What this document does NOT decide: factual analysis (research) · WBS order (plan) · data definition (owned by the spec). -->

> **Written**: YYYY-MM-DD
> **Version**: v0.1
> **Prerequisites (dependencies)**: <prerequisite task ID and status>
> **Risk level**: <R1+R2 default / safety boundary = all of R0~R4>
> **Single Writer**: implementer = <primary agent> · independent reviewer = <secondary agent> · final decision = user
> **Single authority**: `docs/engineering/<spec>.md` (on conflict, the spec wins)

---

## 1. Interface Contract

```text
def <function_name>(<args>) -> <return>:
    Args:
      <arg>: <meaning·unit·range>
    Returns:
      <meaning·unit·range>
    Raises:
      <Exception>: <condition>
```

## 2. Data Flow

```text
<input> → <transform/compute> → <output sink>
```

## 3. Invariants / Safety Guards

<!-- No data loss · boundary validation · no silent drop, etc. For the safety boundary, no changes without user approval. -->
- <invariant 1>

## 4. Verification Strategy (what RED must catch)

<!-- The intent of the RED tests corresponding to each contract/invariant in design. The actual code is written in the RED step. -->
- <contract X> → `test_<subject>_<condition>_<expected>`
