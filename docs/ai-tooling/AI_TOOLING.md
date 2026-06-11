# AI_TOOLING — The AI Tooling This Kit Assumes (agents · commands · skills · MCP) and How to Install It

> This kit is designed to **collaborate with AI agents**. As a result, it only performs at its best when certain
> **agents · slash commands · skills · MCP** are present. This document defines *what you need, how to check whether
> it exists, and how to install it if it doesn't*. For per-environment (IDE/terminal/app) availability, see
> [../ENVIRONMENTS.md](../ENVIRONMENTS.md).
>
> 🤖 Agents: when applying the kit, run this checklist from [../../START_HERE.md](../../START_HERE.md) §3.0, and install
> anything missing **only after the user approves** (no auto-install).

---

## 0. The Four Categories

| Category | What it is | Its role in this kit |
|:--|:--|:--|
| **agents** | `.md` role-defined subagents | The performer for each stage of the 6-stage gate |
| **slash commands** | `/command` | Gate orchestration and inspection |
| **skills** | Task-specific executable knowledge | Depth boost for TDD, review, research, etc. |
| **MCP** | External tool servers | Research (docs/search/repo), E2E, data access |

---

## 1. Quick Checklist (confirm what exists)

Inspection commands:
```bash
# agents/commands/skills (file locations)
ls .claude/agents/      ~/.claude/agents/      # agents
ls .claude/commands/    ~/.claude/commands/    # commands
ls .claude/skills/      ~/.claude/skills/      # skills
# In-session: /help (command list)  ·  /mcp (MCP status)
claude mcp list                                # MCP servers
python scripts/harness_init.py --dry-run       # batch-check all global prerequisites (fails loudly)
```

What you need:

| Needed | Source | If missing |
|:--|:--|:--|
| **agents** test-writer · impl-coder · refactor-fixer · score-auditor | **bundled with the kit** (`.claude/agents/`, comes along on clone) | — |
| **agents** code-reviewer · security-reviewer · planner · architect (· tdd-guide · build-error-resolver) | **global** `~/.claude/agents/` | Stage 4 REVIEW / Phase 1~2 support unavailable |
| **commands** `/kit:harness-verify` · `/kit:auto-harness` · `/kit:recommend` · `/kit:resume-break` | **bundled with the kit** (`.claude/commands/kit/`) | — |
| **commands** harness-audit · quality-gate | global `~/.claude/commands/` | Loss of the drift/gate inspection tools |
| **skills** (optional) python-testing · tdd-workflow · verification-loop · security-review · deep-research, etc. | global/plugin | Weakened depth boost (not fatal) |
| **MCP** (optional, research/E2E) | user-installed | Weakened support for S0 research and S6 E2E |

> ⚠ **security-reviewer must be read-only** — if the global copy has Write/Edit permissions, it violates the Stage 4 permission matrix. Trim it to `tools: Read, Grep, Glob, Bash`. ([../pm-guide/DRIFT_LOCK.md](../pm-guide/DRIFT_LOCK.md) B)

---

## 2. Install — agents · commands · skills

### 2-1. All at once (recommended) — ECC plugin + configure-ecc
Many of this kit's global agents/commands/skills align with the **Everything Claude Code (ECC)** ecosystem.
```text
# Inside a Claude Code session:
/plugin install everything-claude-code     # (if the marketplace must be registered: /plugin marketplace add <repo>)
/reload-plugins
/configure-ecc                             # interactive: choose user/project scope + skill/rule categories
```
`/configure-ecc` installs the verified skills, rules, and agents into `.claude/` and checks the structure.

### 2-2. Manual (when plugins aren't available)
- The kit's 4 bundled agents + the 4 bundled `/kit:*` commands **already exist via the clone**.
- For the global agents (code-reviewer/security-reviewer/planner/architect), copy them from the ECC repo's `.claude/agents/` into `~/.claude/agents/`.
- Plugins/marketplace: `/plugin` (management UI) · `/plugin marketplace add <repo>` · `/plugin install <name>@<marketplace>`.

### 2-3. Scope
- **Project** `.claude/` (committed, shared by the team) ↔ **User** `~/.claude/` (personal, across all projects). Choose the scope at install time. (Details in [../ENVIRONMENTS.md](../ENVIRONMENTS.md) §4)

---

## 3. Install — MCP Servers

### 3-1. How
```bash
claude mcp add --transport http  <name> <url> --header "Authorization: Bearer ${TOKEN}"   # remote (recommended)
claude mcp add --transport stdio <name> -- npx -y <package>                                # local
claude mcp list   /   claude mcp get <name>   /   claude mcp remove <name>                  # management
```
- **Scope**: `--scope project` → root `.mcp.json` (committed, shared by the team) · default local (personal) · `--scope user` (global, personal).
- **Team-shared template**: copy the kit root's **[`.mcp.json.example`](../../.mcp.json.example)** to `.mcp.json` → keep only the servers you need and delete the `_README`/`_*` keys → approve in the `/mcp` panel. Use `${ENV}` expansion for tokens (no plaintext secrets).
- App/web environments support **remote (HTTP) MCP only** (local stdio ❌). ([../ENVIRONMENTS.md](../ENVIRONMENTS.md) §3)

### 3-2. Recommendations by Purpose (verification markers — confirm current details before adding)

| Purpose (lifecycle stage) | Server | Status | Add |
|:--|:--|:--|:--|
| code/repo search and reuse research (S0) | **GitHub** | ✅ verified | `claude mcp add --transport http github https://api.githubcopilot.com/mcp/ --header "Authorization: Bearer ${GITHUB_TOKEN}"` |
| browser / E2E (S6 Delivery) | **Playwright** | ✅ verified | `claude mcp add --transport stdio playwright -- npx -y @playwright/mcp@latest` |
| library/API documentation lookup (S2~S4) | **Context7** | ⚠ verify current | `claude mcp add --transport stdio context7 -- npx -y @upstash/context7-mcp` |
| web/neural search (S0, broad research) | **Exa** | ⚠ verify current | confirm the current endpoint in the official directory, then add |
| web scraping/extraction (S0) | **Firecrawl** | ⚠ verify current | package name changes — check the directory |
| errors/logs (operations) | **Sentry** | ✅ verified | `claude mcp add --transport http sentry https://mcp.sentry.dev/mcp` |
| DB queries (data-oriented projects) | **DBHub (Postgres, etc.)** | ✅ verified | `claude mcp add --transport stdio db -- npx -y @bytebase/dbhub --dsn "${DATABASE_URL}"` |

> ⚠ **Verification principle**: for anything other than ✅, confirm the **current package/URL in the official directory (claude.ai/directory) or vendor docs before adding**. Package names and endpoints change. No adding by guesswork.
> Research priority (aligned with the user rules): **GitHub code search → official docs (Context7) → Exa (broad research)**, in that order.

---

## 4. 🤖 Agent Code of Conduct (when installing)

1. Run the §1 checklist to identify what's missing.
2. If what's missing is **fatal (global agents/commands)**, proceed with the §2 install **after getting user approval**.
3. For **MCP**, add only what's needed for the purpose (the current lifecycle stage) via §3, **confirming current details for any ⚠ verification marker**, after getting approval.
4. Use `${ENV}` expansion for secrets only. Do not commit plaintext token files.
5. After installing, re-check prerequisites with `python scripts/harness_init.py --dry-run`.

---

## 5. Sources
- Claude Code official docs (MCP / settings / skills / plugins / VS Code / permissions), collected from claude-code-guide in 2026-06.
- Packages/endpoints are time-dependent → the ✅/⚠ markers make the verification responsibility explicit.
