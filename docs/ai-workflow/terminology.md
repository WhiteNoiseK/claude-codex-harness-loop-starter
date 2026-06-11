# Terminology Glossary

<!-- ROLE BANNER: single source of truth for domain terminology — fixes the terms used by code/docs.
     What this document decides: "the exact terms and their meanings, and the mapping from legacy notation".
     Overloaded terms (one word, two meanings) must be split out into a checklist to prevent silent misunderstanding. -->

> Fixed on YYYY-MM-DD. All code/docs written afterward use the terms in this glossary **exactly**.
> For mixed/legacy notation in existing documents, refer to the mapping below.

---

## Core Terms (follow first)

| Term | Meaning | Symbol | Unit |
|:-----|:-----|:----:|:----:|
| **<Canonical Term>** | <exact meaning> | `sym` | <unit> |

### Relations (if applicable)

<!-- Derivation relations between terms. State which term it depends on and what it is independent of. -->
- `<derived> = f(<term>)` — **depends on <term>** (independent of <other>)

---

## Legacy notation → canonical mapping

| Legacy notation | Exact meaning | Canonical (code/docs) |
|:-----|:-----|:-----|
| `<legacy_name>` | <what it referred to> | `<canonical_name>` |

### Note

- Large-scale bulk substitution risks distorting meaning, so apply the canonical terms starting from **newly written code/docs**.
- Leave external (vendor) document originals as-is; in our own code, the glossary takes precedence.

---

## Commonly Confused Points (checklist)

<!-- Separate out traps where the same word is used with two meanings depending on context. -->
- [ ] When you say "<ambiguous expression>" — confirm which meaning:
  - <is it meaning 1?> → "<canonical expression 1>"
  - <is it meaning 2?> → "<canonical expression 2>"

---

## Change History

- YYYY-MM-DD — initial definition (user-confirmed). Related commit: <hash>.

---

## Related Files

- `{{SRC_ROOT}}/.../<module>.py` — <where this term appears as code>
- `{{TESTS_ROOT}}/unit/test_<module>.py` — <test parameter name>
