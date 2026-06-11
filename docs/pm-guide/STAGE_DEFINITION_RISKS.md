# STAGE DEFINITION RISKS — Per-Stage [What Gets Defined · Blast Radius · Risk if Undefined (examples)]

> A catalog that organizes, **with examples**, "the risk that arises when the things meant to be defined at each
> stage are left undefined."
> If [PHASE_GATES.md](PHASE_GATES.md) is the one-page gate pass-conditions, this document explains *why each is a gate*
> using standard practice + concrete examples. The key insight: **when a definition is late, everything that depends on it gets reworked.**

---

## 0. We Didn't Invent This — A Restatement of Standard Development Procedure

Your intuition is right. There is an established standard procedure for developing data-producing/instrumentation services like this:

| Standard | Core principle | Connection to where we wobbled |
|:--|:--|:--|
| **V-model** (instrumentation/embedded/safety SW standard) | Each deliverable on the left side (requirements → design → implementation) is paired with the right side (verification). Finalize requirements/interfaces *first* | We finalized requirements/interfaces late → the right-side verification kept wobbling |
| **ISO/IEC/IEEE 12207** (SW lifecycle processes) | Requirements baseline → change control via Configuration Management | Proceeding without a baseline → changes propagated without control |
| **Data Dictionary** | Freeze the definition · unit · range · formula of every data item into a dictionary *before* implementation | The **output formulas** are exactly this. The v1.0 freeze came after the build → cascading rework |
| **Interface Control Document (ICD)** | Agree on and freeze the format · identifiers · units of system boundaries (storage/external I/F) *first* | The **DB sink · internal-index ↔ external-identifier · epoch ms/s** are exactly this. Finalized late → the whole structure wobbled |

> **Conclusion**: The feeling that "we regressed to square one" came because we did the standard-practice step of
> **"freeze the Data Dictionary + ICD as a baseline, then change control"** informally/late.
> This kit's **Gate P (three-contract freeze)** = the mechanism that enforces this standard step.

---

## 1. The "Blast Radius" Lens

As you correctly pointed out, even the same "undefined" varies in **how far it ripples**. That determines **what to freeze first**.

| Symbol | Blast radius | Meaning | → Freeze timing |
|:--:|:--|:--|:--|
| 🌍 | **Global** | A change reworks **every layer** — reconstruction · storage · output · frontend ("regress to square one") | **First** (S2–S3, Gate P) |
| 🔶 | **Structural** | A change propagates across several modules/boundaries | Early (S3) |
| 🔹 | **Local** | Within a single module/task | In that task (S4) |

> Rule: **the bigger the blast radius, the earlier you freeze it.** Changing a 🌍 item during S4 (mid-implementation) = full rework.

---

## 2. Per-Stage Definition-Target · Risk Catalog

Each row: **what to define/fix** · blast radius · **risk if undefined (general example + our case)** · standard-practice name.

### S0 — Research

| Definition target | Radius | If undefined (example) | Standard name |
|:--|:--:|:--|:--|
| Requirements scope | 🌍 | (general) Discovering missing requirements late → redesign. (ours) — | Requirements Elicitation |
| Applicable standards/specs | 🔶 | (general) Non-compliance discovered at the certification stage → rework. (ours) Had we checked conformance to the relevant industry standards/specs late, the measurement definition would nearly have wobbled | Regulatory/Standard Baseline |
| Whether to reuse existing assets | 🔹 | (general) Re-implementing a library that already exists = waste + bugs | Reuse Analysis |

### S1 — Initiating

| Definition target | Radius | If undefined (example) | Standard name |
|:--|:--:|:--|:--|
| Scope boundaries (in/out) | 🌍 | (general) Schedule/structure collapse from scope creep | Scope Statement |
| **External-dependency boundaries** (HW/vendor/subcontractor API) | 🌍 | (general) Building on an unfinalized API → rewrite when it's finalized. (ours) A hardware driver API (e.g., an accelerator like FPGA) was unfinalized → we fixed the adapter/protocol modules at a stub/mock boundary and deferred work beyond that boundary | Dependency/Interface Boundary |
| Stakeholders · success criteria | 🔹 | (general) A vague, "make it work"–style goal → endless re-checking | Stakeholder Register / Success Criteria |

### S2 — Feasibility (core-technology feasibility)

| Definition target | Radius | If undefined (example) | Standard name |
|:--|:--:|:--|:--|
| Physical achievability of the core technology (measurement range/SNR/timing) | 🌍 | (general) Discovering at integration time that it's "physically impossible" = the worst, most expensive failure. (ours) An external device's fixed latency (hundreds of ms) threatened the target measurement cycle (e.g., 1 Hz) → **discovered early in a spike** | Proof of Concept / Spike |
| Performance limits · alternatives | 🔶 | (general) Discovering late that an algorithm misses the required accuracy | Trade Study |

### ★ S3 — Planning / Gate P (the three contracts that shake the whole structure — this is the core)

| Definition target | Radius | If undefined (example) | Standard name |
|:--|:--:|:--|:--|
| **① Data-definition contract** (column · **output formula** · unit · range · normal/boundary/failure value) | 🌍 | (general) Change one formula and the code that computes it + the storage schema + the output format + the frontend all change in a **cascade**. (ours) Mis-defining one output column's formula · correcting the angle value range `[0,360)`→`[-180,180)` · correcting the column count (47→46) became multi-file rework | **Data Dictionary baseline** |
| **② Output-sink / storage contract** (CSV/DB/FTP, or facade) | 🌍 | (general) Change the sink and the whole persistence path is re-wired. (ours) **The CSV→DB switch = trial and error** → discovered the complete absence of a realtime persistence path, with retroactive repository/session FKs = the direct cause of the "regressed to square one" feeling | **ICD / Persistence Architecture baseline** |
| **③ Identifier/unit contract** (internal-ID ↔ external-ID, ts unit, angle range, anchor constants) | 🌍 | (general) A missing conversion at some boundary → data corruption. (ours) The internal-index ↔ external-identifier and epoch ms/s were only nailed down at M3-2x → a retroactive Mapper + 270° causing a DB CHECK violation that rolled back the INSERT = **data loss** | **ICD unit/coordinate/identifier convention** |
| ④ WBS + per-task DoD + verification commands | 🔶 | (general) A weak completion criterion → endless re-checking, missed regressions | Work Breakdown / DoD |
| ⑤ (When cloning) legacy-assumption audit | 🔶 | (general) A previous project's assumptions bleed into the new domain. (ours) Need to check for leakage of the prior domain's geometry/calibration constant assumptions | Configuration Audit |

> **The three 🌍 rows in this table are the "parts that shake the whole structure" you mentioned.** All three must be frozen at S3,
> and if genuinely undecided, **isolate them with a facade/placeholder + guard instead of a guessed real value** (e.g., leave a column whose formula is undecided as a `0.0` placeholder with a "do not persist as a real value" guard).

### S4 — Executing

| Definition target | Radius | If undefined (example) | Standard name |
|:--|:--:|:--|:--|
| Per-task gate thresholds · permission boundaries | 🔹 | (general) Gate forgery (fake "passed"), the reverse bias where tests are bent to fit the implementation | TDD / Quality Gate |

### S5 — Monitoring & Controlling

| Definition target | Radius | If undefined (example) | Standard name |
|:--|:--:|:--|:--|
| Progress ledger · score records · re-run audit | 🔶 | (general) claimed ≠ actual goes undetected, drift accumulates *silently* (← your central concern) | Configuration Control / Audit |

### S6 — Delivery / Deployment

| Definition target | Radius | If undefined (example) | Standard name |
|:--|:--:|:--|:--|
| Acceptance criteria · Monkey test · RTO/RPO · deployment approval gate | 🔶 | (general) An unverified production push → irrecoverable in a hard-to-access environment | Acceptance / Release Gate |

### S7 — Review / Assetization

| Definition target | Radius | If undefined (example) | Standard name |
|:--|:--:|:--|:--|
| Retrospective + memory promotion | 🔹 | (general) Learning evaporates → the next project repeats the same trial and error (= what this kit aims to prevent) | Lessons Learned / OPA |

---

## 3. One-Page Summary — "The 3 to Nail Down First"

```
🌍 Data-definition contract (output formula)   ┐
🌍 Output-sink / storage contract (CSV/DB)     ├─ shakes the whole structure → must be frozen at S3 Gate P (or facade)
🌍 Identifier / unit contract                  ┘   ← if these three are late, the "regressed to square one" feeling
```

> Standard practice in one line: **"Before implementation, freeze the Data Dictionary and ICD as a baseline, and after that, change only via configuration management."**
> Our kit in one line: **"No starting pipeline code until Gate P is green."**
