"""Field (column)-level document dependency reverse-reference map generator (docs only, read-only).

Automatically extracts field names from the §3.1 CSV-header code block (```text) of a
data-definition spec, then reverse-references the docs/ files that mention each field to
generate `docs/_field_cascade.md`.
→ Tracks, per column, "if this column changes, which *documents* use that field name".

Operational notes:
  - Documents refer to a field in two forms: CSV PascalCase (`FooBar`) + DB snake_case (`foo_bar`).
    → Each field's aliases (literal ∪ derived snake_case ∪ override) must be searched as a
      union to avoid misses.
  - Noise: short/common tokens are mostly handled by case-sensitive word boundaries (\\b).
    If an ambiguous field shows up in a project, add it to _AMBIGUOUS to flag it with ⚠️.
  - Deprecated documents (§8) are flagged with 🚫 (mentioned often but not authoritative).

Never touches code or the body of other documents (read-only scan).

── PARAM (vs the original project) ───────────────────────────────────────────
  The original hardcoded two spec paths (realtime/aggregate) and project-specific
  _AMBIGUOUS / _ALIAS_OVERRIDES. Here we replace the spec paths with auto-discovery
  under docs/engineering/ (any *_spec.md with a §3.1 ```text header is recognized as a
  spec), and we ship the two project-dependent sets empty. Projects fill them in as needed.
"""

from __future__ import annotations

import re
from pathlib import Path

import foam_catalog as fc  # same scripts/ — reuses DOCS, _excluded, parse_section8

# Spec auto-discovery root + filename pattern. A spec is a data-definition doc with a §3.1 ```text header.
SPEC_DIR = fc.DOCS / "engineering"
SPEC_GLOB = "*_spec.md"  # matches the _TEMPLATE_data_spec.md convention (real spec = <name>_spec.md)
OUT = fc.DOCS / "_field_cascade.md"

# For extracting the §3.1 header code block
_RE_SECTION31 = re.compile(r"###\s*3\.1.*?```text\s*(.*?)```", re.DOTALL)

# ── Project-specific tuning sets (shipped empty) ────────────────────────────
# Lingering ambiguous fields (short/common tokens) — flagged with ⚠️ since the count is approximate. Projects fill this.
#   e.g. _AMBIGUOUS = {"Distance", "Timestamp", "Value"}
_AMBIGUOUS: set[str] = set()

# Irregular snake/aliases the algorithm cannot derive (DB/backend notation). Projects fill this.
#   e.g. _ALIAS_OVERRIDES = {"DateAndTime": ["ts_start"], "Channel": ["channel_idx"]}
_ALIAS_OVERRIDES: dict[str, list[str]] = {}


def discover_specs(spec_dir: Path = SPEC_DIR) -> list[Path]:
    """Auto-discover data-definition specs with a §3.1 ```text header under docs/engineering/.

    Only documents that match the filename pattern (*_spec.md) and actually contain a §3.1
    code block are recognized as specs.
    Templates (_TEMPLATE_*) are excluded (their fields are placeholders, i.e. noise).
    """
    if not spec_dir.is_dir():
        return []
    specs: list[Path] = []
    for path in sorted(spec_dir.glob(SPEC_GLOB)):
        if path.name.startswith("_TEMPLATE"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if _RE_SECTION31.search(text):
            specs.append(path)
    return specs


def extract_fields(spec_text: str) -> list[str]:
    """spec §3.1 ```text block → list of CSV field names ('(trailing blank)' excluded)."""
    m = _RE_SECTION31.search(spec_text)
    if not m:
        return []
    raw = m.group(1).replace("\n", " ")
    fields = []
    for token in raw.split(","):
        f = token.strip()
        if not f or (f.startswith("(") and "blank" in f.lower()):
            continue
        fields.append(f)
    return fields


def derive_snake(field: str) -> str:
    """CSV/spec field name -> derived snake_case (approximation of DB/backend notation).

    The unit/suffix replacements below are EXAMPLE conventions -- adapt them to your project's
    field-naming quirks (or drop them). The CamelCase / acronym splitting is generic.
    """
    s = field
    # Example unit/suffix normalizations (illustrative -- customize per project):
    s = (
        s.replace("(m/s)", "")
        .replace("(deg)", "_deg")
        .replace("(dB)", "_db")
        .replace("(db)", "_db")
    )
    s = s.replace("status", "_status")
    s = re.sub(
        r"(?<=[a-z0-9])(?=[A-Z])", "_", s
    )  # camelCase boundary (myField -> my_Field)
    s = re.sub(
        r"(?<=[A-Z])(?=[A-Z][a-z])", "_", s
    )  # acronym boundary (XMLParser -> XML_Parser)
    s = re.sub(r"[^A-Za-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_").lower()
    return s


def field_patterns(field: str) -> set[str]:
    """Set of search aliases for a field: literal CSV ∪ derived snake ∪ override."""
    pats = {field, derive_snake(field)}
    pats |= set(_ALIAS_OVERRIDES.get(field, []))
    return {p for p in pats if p}


def field_regex(field: str) -> re.Pattern[str]:
    """Combine a field's aliases into one regex (case-sensitive). Tokens containing parentheses etc.
    are matched as literals; pure word tokens use \\b word boundaries to block noise."""
    parts = []
    for p in field_patterns(field):
        if re.search(r"[^\w]", p):  # contains parens/slash etc. → distinctive literal
            parts.append(re.escape(p))
        else:  # pure word → word boundary
            parts.append(r"\b" + re.escape(p) + r"\b")
    return re.compile("|".join(parts))


def scan(
    fields: list[str], spec_names: set[str], docs_dir: Path = fc.DOCS
) -> tuple[dict[str, list[str]], set[str]]:
    """field → mentioning documents (rel paths) map. Excludes noise dirs, the spec itself, and generated files."""
    _auth_set, dep_set = fc.parse_section8()  # use dep_set only (for 🚫 flagging)
    regexes = {f: field_regex(f) for f in fields}
    result: dict[str, list[str]] = {f: [] for f in fields}
    for path in sorted(docs_dir.rglob("*.md")):
        if fc._excluded(path, docs_dir) or path.name in spec_names:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(docs_dir).as_posix()
        for f, rx in regexes.items():
            if rx.search(text):
                result[f].append(rel)
    return result, dep_set


def _fmt_docs(docs: list[str], dep_set: set[str]) -> str:
    if not docs:
        return "_(no referencing documents)_"
    return " · ".join((f"🚫{d}" if d in dep_set else d) for d in docs)


def render(
    spec_fields: list[tuple[str, list[str]]],
    hits: dict[str, list[str]],
    dep_set: set[str],
) -> str:
    lines = [
        fc._BANNER.replace(
            "Convention: _knowledge-architecture.md",
            "Convention: _knowledge-architecture.md / regenerate: python scripts/field_cascade.py",
        ),
        "# Field (column)-level document dependency map\n",
        "> When one column of a spec changes, the **documents that mention that field name** "
        "appear here (union search of CSV-form + DB snake_case aliases). "
        "⚠️ = short/common token, so the count is approximate · 🚫 = deprecated (§8, not authoritative).\n",
    ]
    if not spec_fields:
        lines.append(
            "\n_(No data-definition spec found — this is populated automatically once a §3.1 ```text "
            "header appears in docs/engineering/<name>_spec.md. Template: docs/engineering/_TEMPLATE_data_spec.md)_\n"
        )
        return "\n".join(lines) + "\n"
    for title, fields in spec_fields:
        lines.append(f"\n## {title}\n")
        lines.append("| Field | #Docs | Referencing documents |")
        lines.append("|:---|:---:|:---|")
        for f in fields:
            docs = hits.get(f, [])
            flag = " ⚠️" if f in _AMBIGUOUS else ""
            lines.append(f"| `{f}`{flag} | {len(docs)} | {_fmt_docs(docs, dep_set)} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    specs = discover_specs()
    spec_names = {p.name for p in specs}
    # Extract each spec's fields (title = file stem). Scan all fields once with order-preserving dedup.
    spec_fields: list[tuple[str, list[str]]] = []
    all_fields: list[str] = []
    for path in specs:
        fields = extract_fields(path.read_text(encoding="utf-8", errors="replace"))
        spec_fields.append((path.stem, fields))
        for f in fields:
            if f not in all_fields:
                all_fields.append(f)
    hits, dep_set = scan(all_fields, spec_names)
    OUT.write_text(render(spec_fields, hits, dep_set), encoding="utf-8")
    n_amb = sum(1 for f in all_fields if f in _AMBIGUOUS)
    print(
        f"Generated: docs/_field_cascade.md ({len(specs)} specs, {len(all_fields)} unique fields, {n_amb} ambiguous)"
    )


if __name__ == "__main__":
    main()
