# ENVIRONMENTS — Per-Environment Optimization (IDE · terminal · app)

> This kit assumes **collaboration with AI agents**, and a large part of its behavior depends on
> **local hooks + local scripts + the filesystem + a committed `.claude/settings.json`**. As a result, depending on the
> environment things split into "works as-is / needs adaptation / partly unavailable." Find your environment's section
> and optimize accordingly.
> ⚠ Claude Code evolves quickly, so confirm the detailed support in the table against the version you're using.

---

## 0. Quick Comparison — Based on This Kit's Core Dependencies

| What the kit uses | Terminal/CLI | IDE extension (VS Code · JetBrains) | Desktop app / web (claude.ai/code) |
|:--|:--:|:--:|:--:|
| local filesystem (clone · src · tests) | ✅ full | ✅ full | ⚠ limited (mostly up/download) |
| PreToolUse commit-guard hook (local script) | ✅ | ✅ | ⚠ local script execution restricted |
| local stdio MCP | ✅ | ✅ | ❌ (remote MCP only) |
| remote (HTTP) MCP | ✅ | ✅ | ✅ |
| loading project `.claude/settings.json` | ✅ | ✅ | ⚠ mostly user scope |
| background tasks / slash commands | ✅ full | ✅ most | ⚠ some |
| file-selection context · inline diff | — | ✅ (strength) | — |

> **Conclusion**: this kit's full power (local hook gate + scripts + filesystem) comes out as-is in the **CLI and IDE extension**.
> For the **app/web**, you *adapt* and work centered on remote MCP (§3).

---

## 1. IDE — VS Code / JetBrains Extension (this kit's recommended default)

**Why it fits**: the local filesystem, hooks, and MCP all work, plus file-selection context (`@file#5-10`), inline diff, the plan-mode sidebar, and the like make it strong for *design/review*.

**Setting locations**:
- Extension settings: VS Code `settings.json` (editor only)
- Harness settings: `~/.claude/settings.json` (user) + project `.claude/settings.json` (committed) — shared with the CLI

**Optimization tips (based on the gate quality workflow)**:
1. **Use plan mode for design/review** — for multi-stage harness work, receive the plan as markdown, run a memo loop with inline comments, then implement. (Aligns with your "separate planning from implementation" principle.)
2. **IDE diagnostics MCP whitelist** — the extension spins up an `ide` local MCP. If the PreToolUse hook filters MCP tools, allow `mcp__ide__*` so the agent can see Problems-panel diagnostics (errors/warnings).
3. **Actively use file-selection context** — selecting the relevant code during review/edit raises Stage 4 review accuracy.
4. **Auto-save on** — so the agent doesn't read stale files.

> This kit was extracted and verified in this environment (the user = VS Code extension).

## 2. Terminal / CLI — `claude` (strongest for automation/headless)

**Why it fits**: all slash commands, permission modes, background tasks, hooks, and session management are the most complete here. Best for CI / repeated loops / headless.

**Optimization tips**:
1. **Multi-step with the REPL (`claude`)** — chain `/plan` → test-writer/impl-coder → `/kit:harness-verify <task-id>` in a single session.
2. **Pre-approve permissions** (project `.claude/settings.json` `permissions.allow`) — pre-allow gate commands (pytest/mypy/ruff) to remove prompts. ⚠ Watch out for unbounded allowlist growth → [DRIFT_LOCK.md](pm-guide/DRIFT_LOCK.md) A.
3. **Headless verification**: turn it into a CI gate with `claude -p "..."` + `--output-format json`. Log with `2>&1 | tee session.log`.
4. **Model routing**: use a higher-tier model only for complex reasoning stages (`--model <model>`); use a lower-tier model for lightweight workers. (Aligns with the performance/cost policy.)

**Setting locations**: `~/.claude/settings.json` (user) · `.claude/settings.json` (project, committed) · `.claude/settings.local.json` (personal, gitignored) · managed (enterprise, read-only).

## 3. App / Web — Desktop App · claude.ai/code (adaptation needed)

**Constraints (important)**: local stdio MCP ❌ · local filesystem/background shell restricted · project `.claude/settings.json`/`.claude/agents` may not load · hooks that write to local disk are restricted. → **This kit's local hook gate does not fully work on app/web alone.**

**How to adapt**:
1. **Use remote (HTTP) MCP only** — register it in the user scope (`~/.claude/settings.json`). Examples: GitHub/Notion/Sentry, etc. ([AI_TOOLING.md](ai-tooling/AI_TOOLING.md)).
2. **Hybrid recommended** — do *design, research, and contracts (S0~S3 Gate P)* on app/web (a good fit since they're document-centric), and do *implementation and the gate (S4)* on CLI/IDE. Enforce the gate in the local environment.
3. **Manually inject the project guidelines** — if `.claude/CLAUDE.md` doesn't auto-load, paste the core conventions into the conversation or reference a public URL. Paste the `START_HERE.md` kickoff prompt as-is.
4. **Use plan mode for visibility** — review the steps before execution.

---

## 4. Setting Scopes — What Goes Where (kit-aligned)

| Scope | Location | Use | git |
|:--|:--|:--|:--:|
| managed (enterprise) | `/etc/claude-code/managed-settings.json`, etc. | org policy (highest priority, cannot be overridden) | N/A |
| user | `~/.claude/settings.json` | personal preferences · keys · global agents | gitignore |
| **project** | `.claude/settings.json` | **team-shared hooks · permissions · MCP** (← the kit's PreToolUse gate goes here) | **committed** |
| local | `.claude/settings.local.json` | personal overrides (test env, etc.) | gitignore |

- Priority (high→low): managed > CLI flags > local > project > user. **But permissions/hooks are merged, not overridden** (a deny can't be punched through by a lower layer).
- **Kit rule**: the PreToolUse commit-guard hook + the gate permissions go in the **project `.claude/settings.json` (committed)**. Per-machine values go in `settings.local.json`. (Rationale: anyone on the team who clones must have the gate work.)

> Whatever the environment, the **recommended entry**: settle in from the CLI or IDE with `python scripts/harness_init.py` → the gate goes active. If you're app/web only, use the §3 hybrid.
