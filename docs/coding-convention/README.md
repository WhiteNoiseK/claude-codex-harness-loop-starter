# Coding Convention Guide

This folder defines the per-language coding conventions used in the project.
All code follows the convention for its language to ensure readability and maintainability.

> The **canonical source** for language-agnostic code quality principles (function/file size,
> nesting limits, immutability, Fail-Fast, no hardcoding) is **[.clauderules](../../.clauderules)**,
> while the macro-level process is owned by
> [docs/pm-guide/lifecycle-standard.md](../pm-guide/lifecycle-standard.md).

## Per-Language Guides

| Language | File | Primary Standard | Adoption |
|------|------|----------|:--:|
| Python | [Python.md](./Python.md) | PEP 8 | Always |
| JavaScript / TypeScript | [JavaScript.md](./JavaScript.md) | Airbnb, Google, StandardJS | Optional (web) |
| C | [C.md](./C.md) | MISRA C:2025, Linux Kernel, NASA JPL | Optional (firmware) |

> The default language profile is set via `.harness.toml [language].profile`. Non-Python projects
> adopt the corresponding language convention file as their canonical source and update the "Adoption" column in the table above.

## Naming Conventions at a Glance

| Target | Python | JavaScript | C |
|------|--------|-----------|---|
| Variable | `snake_case` | `camelCase` | `snake_case` |
| Function | `snake_case` | `camelCase` | `snake_case` |
| Class | `PascalCase` | `PascalCase` | `struct_name_t` |
| Constant | `UPPER_SNAKE` | `UPPER_SNAKE` | `UPPER_SNAKE` |
| Indentation | 4 spaces | 2 spaces | 8-wide tab |
| Max line | 79 chars | 80-100 chars | 80-100 chars |

## Project-Wide Common Principles

Always apply the project-wide common principles alongside the per-language conventions.

> For the definition of the common principles, see **[.clauderules](../../.clauderules) § Code Quality and Clean Code Principles**.
> (function/file size, Nested Function limits, Control Flow Nesting limits, Early Return, Immutability, no hardcoding, security, etc.)
