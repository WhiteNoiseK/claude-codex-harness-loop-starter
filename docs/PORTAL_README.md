# Docs Portal — markdown rendered to HTML for human review

> Last Updated: 2026-06-08
> This portal renders the `docs/` markdown knowledge base into a searchable static website so a **human
> reviewer** can follow it comfortably (TOC, search, dark/light, mermaid diagrams, Foam wikilinks).
> **The markdown stays the single source of truth — HTML is a generated view, never hand-authored.**

## Why render instead of authoring HTML

- Agent handoffs and the Foam tooling (`scripts/foam_catalog.py`, `scripts/field_cascade.py`) all read `.md`.
  If a human wrote HTML by hand, the source would split in two and **drift** (forbidden — see `docs/pm-guide/recommendation_policy.md` §4).
- Keeping `.md` as the source means git diffs stay reviewable and agents stay able to edit the docs.
- The portal regenerates from the same markdown, so a human gets readability **without** a second source to maintain.

## One-time setup

```bash
pip install -r requirements-docs.txt
```

## Build / preview

```bash
python scripts/build_docs_portal.py            # refresh the Foam catalog, then build to site/
python scripts/build_docs_portal.py --serve     # live-reload preview at http://localhost:8000
python scripts/build_docs_portal.py --strict     # fail on warnings (broken links, etc.)
```

## Navigation is automatic (no maintenance as files grow)

- The left-hand navigation is **auto-generated** from the `docs/` folder tree (the `awesome-pages` plugin).
  **Add a `.md` file → it appears in the portal by itself.** No `nav:` list to keep in sync.
- Only the top entry points are pinned, in [`docs/.pages`](.pages); the `...` line means "everything else, automatically".
  To curate the order/title of a specific folder, drop a small `.pages` file into that folder (optional).

## Notes / limitations

1. This is a documentation portal only — entirely separate from any application under `src/`.
2. **Never** hardcode spec values or tables into HTML or `mkdocs.yml`; author them in the markdown under `docs/` (drift prevention).
3. `site/` is gitignored (a build artifact — do not commit it).
4. The portal covers `docs/`. A few top-level entry files (`AGENTS.md`, `.clauderules`, `.claude/CLAUDE.md`) live **outside**
   `docs/` by design; links to them resolve in the repo/editor, not inside the portal. Read those in the repo.
5. Hosting/serving the built `site/` externally may expose internal notes — get the owner's approval before sharing it,
   and treat the build as covered by [Gate S](pm-guide/security_gate.md) if it ships as a deliverable.
