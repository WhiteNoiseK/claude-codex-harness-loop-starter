---
description: "Recommendation under the kit's recommendation policy (4-column scorecard: stability / security / maintainability / visibility + no temporary fixes). Append a focus area after the command to weight that axis."
argument-hint: "[optional: an axis or target to weight — e.g. 'security-focused', 'performance of this file', 'migration risk']"
---

# /kit:recommend — recommendation under the recommendation policy

Produce a recommendation for the decision / options / target currently under discussion, using the
**recommendation policy**. If `$ARGUMENTS` is present, **weight that perspective/target**; otherwise balance
the four axes in priority order.

## 0. Fixed criteria (the recommendation policy — do not change)

- **4-column scorecard required**: **stability · security · maintainability · visibility (readability)**. Never omit an axis.
- **Priority (tiebreaker)**: **stability first** > security > maintainability > visibility.
- **No temporary fixes**: no deprecate-and-migrate that leaves two systems coexisting — discard the wrong thing
  and correct cleanly in one pass.
- **No "natural flow" hand-waving** — justify each axis with explicit grounds.
- **Single-authority spec values are not options** (they are to be complied with). Only open questions
  (process / wiring / spec refinement) become options.

Authority: `docs/pm-guide/recommendation_policy.md` (the scorecard + the auto-verification policy).

## 1. Output format

1. If there is more than one option — a per-option **4-column table** + a "temporary fix?" column:

   | Option | Stability | Security | Maintainability | Visibility | Temp fix? |
   |:--|:--|:--|:--|:--|:--|

2. **One recommendation** + grounds (which axis it wins on) + why the rejected options lose.
3. If `$ARGUMENTS` names a focus axis/target, **re-evaluate weighting it** — if the conclusion changes, say why.
4. **Stop / confirm needed** (if any, listed separately): trust-collapse (claimed != actual / no fact layer) ·
   safety boundary (schema/migration · secret · real-HW · single-authority spec) · judgmental decision
   (frozen test · scope expansion · contract reversal) · spec/authority conflict (defer to the architect — no auto-ranking).

## 2. Proceed rule (when code changes are involved)

- On an explicit "proceed as recommended" → run the internal 6-stage gate (REVIEW parallel + FIX loop + AUDIT)
  through to commit.
- **Severity is not a stop axis** — findings (incl. >= HIGH) self-heal in the FIX loop. Stops are only the
  §1.4 axes (trust-collapse · safety-boundary · judgmental · authority-conflict · retry-exhaustion 3x).

> Cross-refs: `docs/pm-guide/recommendation_policy.md` · `docs/ai-workflow/codex_loop_operating_policy.md` (the 5 stop axes).
