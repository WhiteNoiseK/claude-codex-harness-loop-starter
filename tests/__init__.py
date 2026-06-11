"""Test package root — "tests start here" marker + directory map.

What this file does
-------------------
It is the `__init__.py` marker that lets pytest recognize the directory as a Python package,
and at the same time it documents which subfolders exist and how to run the tests. In other
words, it serves as a "map of the test directory + how-to-run guide".

What this file does NOT do
--------------------------
- fixture definitions — handled by `tests/conftest.py`.
- mock implementations — handled by `tests/fixtures/*.py`.
- the tests themselves — `tests/unit/*`, `tests/integration/*`, `tests/e2e/*`.
- import-time side effects (env-var injection etc.) are strictly forbidden — a hidden side
  effect in a package `__init__.py` is the most common cause of broken pytest collection.

Directory layout
----------------
    {{TESTS_ROOT}}/
    ├── __init__.py           ← this file (documentation, no code)
    ├── conftest.py           ← project-shared fixture declarations (env isolation + async teardown)
    ├── fixtures/             ← hardware/external-resource mock skeletons
    ├── unit/                 ← per-module unit tests (no I/O)
    ├── integration/          ← interaction tests wiring several modules/adapter mocks together
    └── e2e/                  ← full-pipeline integration scenarios (slow)

How to run
----------
Quickly run only the unit tests ::
    python -m pytest {{TESTS_ROOT}}/unit -v

Integration tests ::
    python -m pytest {{TESTS_ROOT}}/integration -v

Full run with coverage ::
    python -m pytest --cov={{SRC_ROOT}} --cov-report=term-missing --cov-fail-under=80

Verify only a specific module (--cov takes a DOTTED module path — no file paths) ::
    python -m pytest {{TESTS_ROOT}}/unit/test_<module>.py -v \\
           --cov={{SRC_ROOT}}.<package>.<module> \\
           --cov-fail-under=80

Coverage threshold
------------------
- On single-task completion: enforce 80%+ for that module (`--cov-fail-under=80`)
- On milestone completion: 80%+ overall + `mypy` passing
- Single source of the threshold: `.harness.toml [gates].coverage_threshold` / pyproject [tool.coverage.report]

pytest config location
----------------------
Global settings (markers/timeout/asyncio_mode etc.) live in the project root's `pyproject.toml`
[tool.pytest.ini_options], which is the single home (no separate pytest.ini shipped).

Uses (modules this file calls):
    - none (imports forbidden — pure documentation file)

Used by (modules that call this file):
    - pytest collection (to recognize the directory as a package)
    - the `from tests.fixtures import ...` relative imports of the test submodules
"""
