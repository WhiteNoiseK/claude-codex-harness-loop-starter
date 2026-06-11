# docs Knowledge Base — Entry Point (Map of Content)

> When you lose context, **start here**. Document format conventions: [_knowledge-architecture.md](_knowledge-architecture.md)

## 🧭 Core entry points

- **[Most-recent catalog](_recent.md)** — recent work and high-trust documents first (auto-generated)
- **[Authority registry](_authority.md)** — single-authority documents (content authority is owned by [.claude/CLAUDE.md](../.claude/CLAUDE.md) §8)
- **[Field dependency map](_field_cascade.md)** — spec column → the documents that use that field (cascade tracking)

> 👀 **Reading this as a human?** Render the whole knowledge base to a searchable HTML site:
> `python scripts/build_docs_portal.py --serve` → http://localhost:8000 (see [PORTAL_README.md](PORTAL_README.md)). md stays the source; HTML is generated.

## 📁 Domains (folder = classification axis)

> Below is the **kit's default skeleton**. When you add a project domain folder, register it here as a single line
> (do not list individual files — that is the job of the `_recent.md` auto-catalog). The domain = folder convention is in
> [_knowledge-architecture.md §6](_knowledge-architecture.md).

- [pm-guide/](pm-guide/) — macro process: lifecycle, gates, drift locks, recommendation policy
- [_harness/](_harness/) — the 6-stage quality-gate engine spec, task-id grammar
- [ai-workflow/](ai-workflow/) — planning, research, progress, decisions, handoffs, reviews, scores
- [engineering/](engineering/) — specifications, ERD, identifier/unit contract (FREEZE gate deliverables)
- [coding-convention/](coding-convention/) · [coding-target/](coding-target/) · [experiments/](experiments/) · [retrospective/](retrospective/)
- `{{DOMAIN_FOLDER}}/` — {{DOMAIN_DESCRIPTION}}  <!-- duplicate this line when adding a project domain -->

---

> How to update: run `python scripts/foam_catalog.py` → `_recent.md` · `_authority.md` are regenerated automatically.
> Field map: `python scripts/field_cascade.py` → regenerates `_field_cascade.md` (requires the data spec's §3.1 header block).
> Foam graph: `Foam: Show Graph` / related documents: `Show Similar Notes`.
