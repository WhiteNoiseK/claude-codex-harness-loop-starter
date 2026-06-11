# DRIFT LOCK — The Answer Key to "I Can't Tell What's Drifting"

> Every time a project starts, the configuration drifts a little, but you can't tell *what* is drifting — this document
> **exhaustively identifies** that culprit and decides **how to lock down each one**. 22 kinds measured in a full dissection
> of the original project.
> Key insight: drift is mostly **"the same value scattered and duplicated across many places"** or **"accumulated unconsciously during a session"**.

The 3 locking principles: **(a) single source** (in one place only) · **(b) start empty** (prevent content accumulation) · **(c) make it visible via baseline diff**.

---

## 0. Know This First — Why Drift Is "Invisible"

In the original project the permission allowlist grew without limit simultaneously in **two places — global (56) + project (50)** —
and because of `defaultMode=bypassPermissions`, most of those entries kept piling up even while dead.
→ Two uncurated allowlists growing quietly = the primary cause of "I can't tell what's drifting."
**Mitigation: right after cloning, take a `.harness/baseline/` snapshot, then *see* the changes with your own eyes via a `live vs baseline` diff.**

---

## A. Configuration · Permissions (highest drift)

| What drifts | Why | 🔒 Lock |
|:--|:--|:--|
| **settings.json `permissions.allow[]`** | During a session, "always allow" clicks accumulate absolute-path and one-off shells (in the original project all 49 entries were external paths) | Ship with `allow:[]` **empty**. README rule: "allow[] is per-project scratch, never inherit." Curate with `/fewer-permission-prompts`, make it visible via baseline diff |
| **settings.json `hooks{}` block** | This is the core that carries the commit gate, yet it's a single piece of JSON buried next to the noise (allow[]) — start it by hand and it's often omitted → the whole 6-stage flow is *silently* disabled (the agent looks fine) | Keep hooks{} **fixed as-is**. `harness_init.py` verifies hook registration + checks against a baseline checksum on first run. If missing, warn loudly |
| **Scattered path/threshold literals** (SCORES_DIR, src/, tests/, cov 80, audit 95, mypy flags) | The same value is duplicated as literals across 6+ files (scripts · agents · CLAUDE.md · quality-gates.md). Fix one and miss the rest = partial silent drift | **A single `.harness.toml` seam** holds all of them. `harness_init.py` substitutes placeholders when cloning. Thresholds are cited once in `quality-gates.md` |
| **`additionalDirectories` absolute paths** | Per-machine, per-project absolute paths hardcoded | init generates them at the new path or empties them. No absolute paths shipped |
| **Language/docstring lock-in** | pytest/mypy/ruff/black + the doc/comment language baked into the global layer → a non-Python/English project inherits commands that don't exist | Swap via the `.harness.toml [language]` profile. The doc/comment language is a toggle (default English; Korean or other projects set docstring_lang accordingly) |
| **Build/runtime placeholders** (npm deploy, example.com URL) | A default deploy command / example URL that looks real → running the wrong command / example.com lingering in production records | `{{DEPLOY_STAGING_CMD}}`/`{{PROD_URL}}` tokens + a root fill-in checklist |

## B. Harness Gate Machinery (risk of silent disablement)

| What drifts | Why | 🔒 Lock |
|:--|:--|:--|
| **task-id regex vs WBS grammar** | The original project's guard supported only 1–2 segments → it failed to extract its own 3-segment IDs (M3-RT-PERSIST-01), and 9 commits bypassed the guard with `-F` | Generalize to multi-segment `\((M\d+(?:-[A-Za-z0-9]+)+)\)` + a single `.harness.toml` constant + `TASK_ID_GRAMMAR.md` + a 1–4 segment parameterized test |
| **Ghost script names** | `quality-gates.md` mentions `harness_commit_guard.py`/`harness_score.sh` but they **don't actually exist** (the real files are gate_check.sh + audit_rerun.py + run_verify.sh) → the clone expects missing files and the hook does nothing | Unify on the canonical names + add **a self-test that verifies the existence of every script path cited in the spec** |
| **Coverage `--cov` file path vs dotted-module** | Passing a file path makes coverage report 0%. Worse, the AUDIT re-run reproduces the same 0% → claimed == actual, so **a fake value passes** | Fix the script to derive the dotted-module target + a "known module cov > 0" hardening test |
| **Stage 4 reviewer write permission** | The security-reviewer front-matter holds Write/Edit → a read-only matrix violation (can disable the tests ↔ src separation) | Trim to `[Read,Grep,Glob,Bash]` + a "Stage 4 agents have no Write/Edit" lint |
| **Duplicate agent sets** | Project (test-writer/impl-coder/...) vs global (tdd-guide/code-reviewer/...) — which one owns which stage varies per project | Make `harness-verify.md` the single source for the stage → agent mapping. The 4 project agents = Stage 1/2/5/6 fixed, the global reviewers = a declared Stage 4 dependency |

## C. Contracts · Authority (Gate-P linkage)

| What drifts | Why | 🔒 Lock |
|:--|:--|:--|
| **Single-authority §8 table** | The domain-spec rows are 100% project-specific + every document carries a "correction notice" banner. Cloned as-is, they become dead pointers to a spec that doesn't exist | Keep the 5 enforcement rules + the Deprecated header, but **empty the table** (header row only, preserving the foam parser marker). Remove all correction banners |
| **Three contracts unfrozen** | The data/sink/identifier contracts are finalized later than the code (→ [PHASE_GATES.md](PHASE_GATES.md) Gate P) | The Gate P hard gate + 3 empty contract scaffolds |
| **research.md storing contracts** | If the research doc also holds data definitions, it becomes a second source alongside the spec later → §8/Foam has to resolve it after the fact | research.md = analysis/history only, contracts live only in the spec scaffold. §8 + foam wired up in advance |

## D. Document · Process Duplication

| What drifts | Why | 🔒 Lock |
|:--|:--|:--|
| **Two copies of the Phase 6 doc** | `ai-workflow/lessons_learned.md` (content) + `retrospective/lessons_learned.md` (template) coexist | Ship **only** `retrospective/`. State the MEMORY.md promotion explicitly |
| **Handoff protocol (inbox vs chat-paste)** | The README mandates inbox, but the actual adopted practice is chat-paste (inbox deprecated) → an inherited contradiction | One reconciled `handoffs/README.md` (chat-paste standard, with reviews/ + scores/ as the audit truth) |
| **Four copies of requirements** | root + src/backend with conflicting pins (pytest 9.0.3 vs >=8,<10, etc.) | Ship only one pair (root), delete the backend pair |
| **progress/scores/reviews/handoffs content** | Pure live state (a 503-line progress, 60+ JSON). Cloned, a new project starts with someone else's 'CLOSED' tasks | An empty skeleton + a convention README + 1 example. No live artifacts shipped |
| **scratch .gitignore tail** | Named project scratch files baked into .gitignore | Generalize to `*.tmp/*.bak/*.swp` wildcards |

## E. Knowledge Base (Foam)

| What drifts | Why | 🔒 Lock |
|:--|:--|:--|
| **Auto-generated catalogs** (_recent/_authority/_field_cascade) | Committing a stale copy is meaningless | Ship **an empty stub identical to the generator's zero-doc output** → the first regen is a no-op. A self-banner names the generator. Regen on PostToolUse/pre-commit |
| **Safety-boundary path list** | Hardware-driver/external-device/shutdown paths are repeated in 3 places — CLAUDE.md §3 · AGENTS.md §5 · .clauderules → edit one arbitrarily and the 3 files diverge | Define `{{SAFETY_BOUNDARY_PATHS}}` in **one place (.harness.toml)**, the rest reference it (no duplication) |

## F. Self-Containment · Portability

| What drifts | Why | 🔒 Lock |
|:--|:--|:--|
| **Global-layer dependency** (quality-gates.md + global agents) | Thresholds/schemas/Stage 4 reviewers live in the global layer, so a bare-machine clone *silently* drifts | **Vendor** quality-gates.md into `docs/_harness/` + have `TEMPLATE_MANIFEST.md` existence-check the global prerequisites. init fails loudly if any are missing |
| **Encoding/portability** | settings.json fails to decode as cp949/UTF-16. Scripts assume Bash-only + Windows paths | Force **UTF-8** for all shipped configs. Document the Git-Bash-on-Windows requirement. Parameterize the self-test's REPO_ROOT depth |
| **post-clone drift visibility** (← the user's central concern) | No tool to see "exactly what changed" | Commit a `.harness/baseline/` snapshot + a `live vs baseline` diff command (or `/harness-audit`) for a concrete "changes relative to the kit" report |

---

## Post-Clone Drift-Check Ritual (2 minutes)

```
1. python scripts/harness_init.py        # substitute placeholders + verify hooks/prerequisites (fail loudly if missing)
2. pytest tests/test_harness_hardening.py # acceptance test for gate behavior, forgery rejection, timeout, script existence
3. git diff --no-index .harness/baseline/ <live>   # "exactly what changed relative to the kit"
4. /harness-audit                          # (global) harness maturity scorecard
```
