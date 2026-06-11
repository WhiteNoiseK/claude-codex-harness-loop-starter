# Agent Handoff Prompts (RECONCILED)

<!-- ROLE BANNER: directory for agent-to-agent handoff prompts — a supplementary medium.
     What this README decides: the standard handoff medium, and where the single source of truth for audit truth lives.
     Audit truth is NOT here — reviews/ (originals) and scores/ (scores/audits) are the single source of truth. -->

## Standard = Pasting a Chat Prompt

The handoff's **standard flow is pasting a chat prompt**. The user directly passes the Review Request /
Action Prompt produced by one agent to the next agent.

```text
implementer → (chat prompt) → user → (paste) → reviewer → (chat prompt) → user → implementer
```

## Inbox Files Are Deprecated

Inbox files like `CODEX_INBOX.md` / `CLAUDE_INBOX.md` are **not used in the default flow**.
Use them as a temporary aid only when the user explicitly requests "leave it as an inbox file".

- Inbox files are an operational aid only, **not the source of audit truth**.
- Read such a file only when the user explicitly says "check the inbox".

## Single Source of Truth for Audit Truth

| Type | Single Source of Truth |
|:---|:---|
| Review originals (full findings) | `docs/ai-workflow/reviews/` |
| Score / audit meta (claimed-vs-actual) | `docs/ai-workflow/scores/` |
| Timeline summary | `docs/ai-workflow/implementation_log.md` (path + summary only) |

> Do not copy a full handoff prompt into `implementation_log.md`.
> Judgments/Evidence that need long-term retention go into a `reviews/` artifact.
