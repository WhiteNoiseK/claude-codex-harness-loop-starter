"""Integration-test shared fixtures — autouse env-guard example (limited to this test tree).

ROLE: an environment guard auto-applied only in the integration-test directory. When some code
path requires a "guard that must be on only during tests" (e.g. a flag allowing the
synthetic/fault-injection path), this auto-sets and restores that env var across the whole directory.
This file does NOT decide: the guard's meaning/name is the project's call — here it is only the mechanism.

Why it is needed
----------------
For security, synthetic/fault-injection code paths must be disabled in production (RuntimeError if
the guard env var is absent). But integration tests must use those paths without real hardware, so
this conftest turns the guard on only during the test session and restores it at the end. Production
has no such conftest, so the guard works normally there.

Declared with autouse=True, it is auto-applied to every test in this directory (no need to name the argument).

References:
    - tests/conftest.py (project-wide fixtures)
    - {{SRC_ROOT}}/.../<module where the guard is defined> (where the guard env var is checked)
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

# Name of the guard env var turned on only during tests (the project substitutes the real name).
# Example: a flag allowing the synthetic-data / fault-injection code path.
_GUARD_ENV = "{{PROJECT_PREFIX}}_FAULT_INJECT_ENABLED"


@pytest.fixture(autouse=True)
def env_guard() -> Iterator[None]:
    """Turn the guard env var on, limited to the integration-test scope, and restore it at the end.

    Yields:
        None — performs setup only, no return value.

    Behavior:
        - before the test: set `_GUARD_ENV=1`.
        - after the test: restore the original value (delete it if originally absent — prevents leaks).
    """
    # 1. preserve the original value (None if it was absent)
    original = os.environ.get(_GUARD_ENV)
    # 2. turn the guard on only within the test scope
    os.environ[_GUARD_ENV] = "1"
    try:
        yield
    finally:
        # 3. deterministic restore — remove the key if originally absent, otherwise restore the original value
        if original is None:
            os.environ.pop(_GUARD_ENV, None)
        else:
            os.environ[_GUARD_ENV] = original
