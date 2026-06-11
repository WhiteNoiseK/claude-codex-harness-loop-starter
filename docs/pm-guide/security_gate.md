# Gate S — Pre-deployment Security Audit

> Last Updated: 2026-06-08
> A **separate, release-blocking security sector** that runs once per release, *after* delivery QA (Gate D) and
> *before* the production push (`[RELEASE APPROVED]`). It is the single home for the pre-deployment security checklist.
> Macro lifecycle: [lifecycle-standard.md](lifecycle-standard.md) S6 · gate map: [PHASE_GATES.md](PHASE_GATES.md) Gate S.

---

## 0. What this gate is — and is NOT

| | Per-task security (already in the kit) | **Gate S — Pre-deployment Security Audit (this doc)** |
|:--|:--|:--|
| When | Every task, inside the 6-stage loop | **Once per release**, right before the production push |
| Scope | The diff of one task | **The whole system as it will actually ship** (full attack surface) |
| Who | Stage 4 `security-reviewer` (parallel with code-reviewer) | A holistic security pass over the release candidate |
| Owner | [_harness/quality-gates.md](../_harness/quality-gates.md) Stage 4 | **This document** |

> Per-task review catches *local* issues in each change. Gate S catches what only becomes visible when the pieces are
> assembled into a deployable whole — leaked secrets in build artifacts, a newly exposed endpoint, a vulnerable
> transitive dependency, an auth gap at a seam between two task-clean modules. **Passing every Stage 4 does not imply
> Gate S passes.**

---

## 1. The Checklist (all must be ✅ to pass)

Group items by concern. For each, record evidence (command output / file:line / "N/A — reason") — an unchecked or
hand-waved item **blocks the release**.

### 1.1 Secrets & configuration
- [ ] No hardcoded secrets/API keys/passwords/tokens **anywhere in the repo or build artifacts** (run a secret scanner over the tree, not just the latest diff).
- [ ] All secrets come from environment variables / a secret manager; `.env.example` lists the names with no real values.
- [ ] Required secrets are validated at startup (fail-fast if missing), and error paths never echo secret values.

### 1.2 Dependencies & supply chain
- [ ] Dependency vulnerability scan run on the **final** lockfile/manifest → 0 unresolved CRITICAL/HIGH advisories (or each is documented with an accepted-risk rationale + ticket).
- [ ] Dependencies are pinned (no floating ranges that could pull a different build into production).
- [ ] No unexpected/unvetted new dependency was introduced since the last release.

### 1.3 Input & boundaries
- [ ] Every system boundary (user input, API response, file content, device/serial frame) validates input before use — schema-based where possible, fail-fast with a clear message.
- [ ] External data is never trusted; size/range/type limits are enforced.

### 1.4 AuthN / AuthZ
- [ ] Every endpoint/operation that needs it enforces authentication **and** authorization (no endpoint left open by omission).
- [ ] Default-deny: a missing/blank role or permission is treated as denied.

### 1.5 Injection & output
- [ ] SQL/queries are parameterized (no string-built queries).
- [ ] No shell/command injection (no untrusted input concatenated into a command line).
- [ ] Output that reaches a browser/markup is escaped/sanitized (XSS); CSRF protection enabled where applicable.

### 1.6 Errors & logging
- [ ] Error messages and responses do not leak sensitive data, stack traces, or internal paths to untrusted callers.
- [ ] Logs do not record secrets/PII; an audit trail exists for security-relevant actions.

### 1.7 Transport & storage
- [ ] Sensitive data is encrypted in transit (TLS) and, where required, at rest.
- [ ] Rate limiting / abuse protection is in place on exposed endpoints.

### 1.8 Attack surface
- [ ] Only the intended ports/services/endpoints are exposed; debug/admin/diagnostic surfaces are disabled or protected in the production profile.
- [ ] File/directory permissions and CORS/headers are set to least privilege.

### 1.9 Residual findings
- [ ] **Zero deferred CRITICAL/HIGH security findings** from any prior per-task Stage 4 review remain open.
- [ ] Any accepted MEDIUM/LOW residual risk is listed with rationale in the release record.

> **Project tailoring**: not every line applies to every project (e.g. an offline CLI has no endpoints). Mark
> inapplicable items `N/A — <reason>`; do **not** silently drop them. Add domain-specific items (e.g. device/firmware
> safety interlocks) as needed.

---

## 2. Suggested tooling (project-adjustable)

These are defaults, not mandates — pin the actual commands per project (e.g. in `.harness.toml` or the delivery script).

| Concern | Python default | Notes |
|:--|:--|:--|
| Static security lint | `bandit -r {{SRC_ROOT}}` | already in `requirements-dev.txt` |
| Dependency vulnerabilities | `pip-audit` (or `safety check`) | run against the final lockfile |
| Secret scan (whole tree) | `gitleaks detect` / `trufflehog` | scan history + working tree, not just the diff |
| (JS/TS projects) | `npm audit --omit=dev` + `eslint-plugin-security` | see `docs/coding-convention/JavaScript.md` §9 |

---

## 3. Pass condition & evidence

**Pass** = every applicable §1 item ✅ (with recorded evidence) **AND** 0 unresolved CRITICAL/HIGH.

Record the result as a **Gate S sign-off** in [../ai-workflow/delivery_log.md](../ai-workflow/delivery_log.md) for the
release candidate (scanner outputs, the verification number, who signed off, and any accepted-risk notes). The
production deployment's `[RELEASE APPROVED]` **must cite a passed Gate S** for that delivery verification number.

> No stopgaps: if Gate S finds a real issue, fix it properly and re-run the relevant gates — do not ship with a
> "we'll patch it right after" promise (in a hard-to-access/high-availability target, post-ship patching is exactly the
> cost this kit exists to avoid).

---

## 4. Relationship to other gates

```
S4 Executing ── per task ──→ Stage 4 REVIEW (code + security-reviewer)   ← local, every change
        │
S6 Closing ──→ Gate D (staging QA: tests/coverage/mypy/Monkey Testing)   ← delivery_log.md
        │
        └────→ ★ Gate S (this doc: whole-system security audit)          ← delivery_log.md sign-off
                       │
                       └──→ [RELEASE APPROVED] → production               ← deployment_log.md
```

---

## 5. Sources

- Codifies the global memory `security` checklist (`~/.claude/rules/common/security.md`) + `feedback_recommendation_review_criteria`
  (security added as the 4th review axis, 2026-06-06) as a **release-blocking project gate**.
- Per-language code-level security rules: [.clauderules](../../.clauderules) § Security · `docs/coding-convention/<language>.md` §9 ·
  `docs/coding-target/webCodingProtocol.md` §9.
- Per-task (in-loop) security: [_harness/quality-gates.md](../_harness/quality-gates.md) Stage 4.
