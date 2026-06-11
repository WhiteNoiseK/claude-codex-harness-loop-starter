"""pytest shared fixtures — auto-loaded by every test module (reusable skeleton).

ROLE: a single-place catalog of fixtures to share across the project. This kit empties all
domain fixtures and keeps only two patterns reusable anywhere —
  (1) `p_tmp_data_dir`     : tmp_path + monkeypatch environment isolation (for disk-I/O tests)
  (2) `p_managed_resource` : an async/resource fixture example whose teardown is guaranteed via yield-finally
This file does NOT decide: HW protocol details or domain object construction — the project fills those.

What this file does
-------------------
On run, pytest auto-discovers `conftest.py` and makes its fixtures usable from any test function
via "name injection (DI)". A test function just names the argument, and pytest finds and injects
the fixture of the same name.

    tests/unit/test_xxx.py
        │   def test_foo(p_tmp_data_dir): ...
        ▼  (pytest DI)
    tests/conftest.py   ← this file
        │   @pytest.fixture
        │   def p_tmp_data_dir(...): ...
        ▼
    tests/fixtures/*.py  (real mock implementations — filled by the project)

What this file does NOT do
--------------------------
- HW/external protocol implementation details — handled by `tests/fixtures/_TEMPLATE_*.py`.
- the integration-only autouse env-guard — handled by `tests/integration/conftest.py`.
- global pytest config (markers/timeout/asyncio_mode) — handled by `pyproject.toml`.

fixture dependency graph
------------------------
    tmp_path (pytest built-in)
        └── p_tmp_data_dir
    monkeypatch (pytest built-in)
        └── p_tmp_data_dir        (sets the {{PROJECT_PREFIX}}_DATA_DIR env var)
    (standalone)
        └── p_managed_resource    (guaranteed cleanup via finally after yield)

teardown rules
--------------
- tmp_path is auto-cleaned by pytest, so no explicit deletion is needed.
- env vars changed via monkeypatch are also auto-restored by pytest at test end.
- resources that need explicit shutdown (async tasks/queues/connections) **must** be cleaned up
  via yield-finally. Skip this rule and CI floods with "task destroyed while pending" warnings and
  becomes a source of flakiness. (See the `p_managed_resource` example.)

TYPE_CHECKING guard
-------------------
Do not import project domain types at runtime; import them only inside `if TYPE_CHECKING:`.
Runtime-importing real modules during the skeleton phase can break pytest collection.
When you fill in the actual fixture body, move that import inside the function.

Uses (modules this file calls):
    - pytest
    - pathlib.Path
    # add project domain types in the TYPE_CHECKING block below (no runtime imports)

Used by (modules that call this file):
    - tests/unit/test_*            (just name the fixture to get it auto-injected)
    - tests/integration/test_*
    - tests/e2e/test_*
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    # Import project domain types here (not loaded at runtime — collection-safe).
    # e.g. from {{SRC_ROOT}}.core.models import SomeConfig
    pass


# ────────────────────────────────────────────────────────────────────────
# Environment fixture — temporary directory / env-var isolation
# ────────────────────────────────────────────────────────────────────────


@pytest.fixture
def p_tmp_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Disposable data root — replaces the production data directory only during the test.

    What it does
    ------------
    Replaces the data directory where output/log/persistent files accumulate in production with a
    temporary path used only during the test run. It creates a subfolder under pytest's built-in
    `tmp_path` and at the same time sets the data-path env var to this path. Production code reads
    this env var to decide its output path, so when the test ends all files remain inside the
    isolated space and never dirty the real system.

    When it is called
    -----------------
    Every test that performs disk I/O (file writes/logging/persistence) takes this fixture as a
    parameter. Created once per test; pytest auto-deletes tmp_path at the end.

    Args:
        tmp_path: pytest built-in fixture. A per-test unique `pathlib.Path`.
        monkeypatch: pytest built-in fixture. For temporary env-var changes.

    Returns:
        Path — `<tmp_path>/data`, already created via `mkdir()`.

    Side Effects:
        - creates the `<tmp_path>/data` directory.
        - sets the `{{PROJECT_PREFIX}}_DATA_DIR` env var (auto-restored by monkeypatch at the end).

    Raises:
        None. (tmp_path creation and monkeypatch are guaranteed internally by pytest)
    """
    # 1. create the isolated data root
    root = tmp_path / "data"
    root.mkdir()
    # 2. temporarily substitute the data-path env var that production code reads (auto-restored at the end)
    monkeypatch.setenv("{{PROJECT_PREFIX}}_DATA_DIR", str(root))
    # 3. return the isolated path
    return root


# ────────────────────────────────────────────────────────────────────────
# Resource fixture — yield-finally teardown guarantee pattern (async/queue/connection example)
# ────────────────────────────────────────────────────────────────────────


@pytest.fixture
def p_managed_resource() -> Iterator[object]:
    """Example yield-finally teardown for a resource that needs explicit shutdown (skeleton).

    What it does
    ------------
    Demonstrates the standard cleanup pattern for resources that must not be left to GC and must
    have close/stop called — like an async dispatcher, multiprocessing.Queue, or network connection.
    setup → yield → (test) → deterministic cleanup in finally.

    When it is called
    -----------------
    A test that handles such a resource takes this fixture as a parameter. The project copies this
    skeleton and fills it with the real resource (e.g. bus/queue/client).

    Yields:
        object — the resource handle for the test (replace with the real type).

    Side Effects:
        - setup: create/start the resource.
        - teardown: **always clean up in finally** (prevents pending tasks / fd leaks).

    Raises:
        None. (if creation/shutdown fails, pytest marks the test as an error)

    Why yield-finally is required
    -----------------------------
    If stop()/close() is omitted, pytest prints "task destroyed while pending" or resource-leak
    warnings and becomes a source of CI flakiness. Clean up deterministically with a fixture-level
    try-finally.
    """
    # 1. create/start the resource (e.g. resource = SomeResource(); resource.start())
    resource: object = object()
    try:
        # 2. hand the handle to the test
        yield resource
    finally:
        # 3. always clean up — close/stop/join (replace to match the real resource)
        #    e.g. resource.stop(); resource.close()
        pass
