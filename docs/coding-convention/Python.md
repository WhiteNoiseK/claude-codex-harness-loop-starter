# Python Coding Convention

> Reference standard: PEP 8 — Style Guide for Python Code
> The canonical source for language-agnostic quality principles is [.clauderules](../../.clauderules).
> The docstring language is determined by the `.harness.toml [language].docstring_lang` parameter (default English; Korean or other projects set docstring_lang accordingly).

---

## 1. Naming Conventions

| Target | Rule | Example |
|------|------|------|
| Variable | `snake_case` | `user_name`, `total_count` |
| Function / method | `snake_case` | `calculate_total()`, `get_user_id()` |
| Class | `PascalCase` | `UserManager`, `DataProcessor` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_SIZE = 100` |
| Private attribute / method | `_snake_case` | `_internal_state`, `_validate()` |
| Name mangling (class-only) | `__snake_case` | `__private_field` |
| Magic method | `__method__` | `__init__`, `__str__`, `__repr__` |
| Module / package | `snake_case` | `user_service.py`, `data_utils/` |

**Forbidden single characters**: `l` (lowercase L), `O` (uppercase O), `I` (uppercase i) — easily confused with digits 0 and 1

### Function Naming Rules

Write function names as **verb + object** to clearly express the action performed.

| Pattern | Use | Example |
|------|------|------|
| `get_` | Read a value (no side effects) | `get_user()`, `get_total_count()` |
| `set_` | Set a value | `set_config()`, `set_timeout()` |
| `fetch_` | Request external data | `fetch_user()`, `fetch_orders()` |
| `create_` / `make_` | Create an object | `create_session()`, `make_request()` |
| `update_` | Modify | `update_user()`, `update_status()` |
| `delete_` / `remove_` | Delete | `delete_user()`, `remove_item()` |
| `is_` / `has_` / `can_` | Return a boolean | `is_valid()`, `has_permission()` |
| `calculate_` / `compute_` | Compute | `calculate_total()`, `compute_hash()` |
| `handle_` | Handle an event/error | `handle_error()`, `handle_request()` |
| `parse_` / `format_` | Convert | `parse_date()`, `format_price()` |
| `_` prefix | Internal-only helper | `_validate_email()`, `_build_query()` |

```python
# Examples of correct function names
def get_user_by_id(p_s_user_id: str) -> dict: ...
def calculate_discounted_price(p_v_price: float, p_v_rate: float) -> float: ...
def is_email_valid(p_s_email: str) -> bool: ...
def handle_payment_error(p_obj_error: Exception) -> None: ...
def _build_query(p_obj_filters: dict) -> str: ...  # Internal helper
```

---

## 2. Hybrid Naming Convention (Required)

Combine a variable's **origin (Scope)** and **data type (Type)** as a prefix so the name alone reveals both at a glance.

- **Format**: `[Scope]_[Type][Name]`
- **Scope**: `g_` (Global), `m_` (Member/Instance field), `p_` (Parameter); Local is omitted
- **Type**: `v` (Number/int/float), `s` (String), `b` (Boolean), `arr` (List/Array), `obj` (Object/dict/class), `fn` (Function/lambda)

| Example | Description |
|------|------|
| `g_vTotalCount` | Global numeric variable |
| `m_sUserName` | Instance member string |
| `p_objConfig` | Object/dict passed as a parameter |
| `vLocalIdx` | Local numeric variable |
| `fnCalculate` | Function variable / lambda |

```python
g_v_max_retry: int = 3


class UserService:
    def __init__(self):
        self.m_s_base_url: str = '/api/users'
        self.m_arr_cache: list = []

    def get_user(self, p_s_user_id: str, p_obj_options: dict = None):
        v_retry_count: int = 0
        fn_handle_error = lambda err: print(err)
        # ...
```

> **Note**: When combining with Python snake_case, connect the Scope/Type prefixes in snake_case as well.
> e.g. `g_v_count` (global), `m_s_name` (member), `p_obj_data` (parameter)

---

## 3. Indentation and Formatting

- **Indentation**: 4 spaces (never use tabs)
- **Max line length**: 79 chars for code, 72 chars for comments/docstrings
- **Blank lines**:
  - Between top-level function/class definitions: 2 lines
  - Between methods within a class: 1 line
- **Formatting tools**: `black`, `ruff`, `isort` recommended (configured in `pyproject.toml`)

```python
# Correct indentation and blank-line layout
class UserManager:
    """User management class."""

    def __init__(self, db_connection):
        self._db = db_connection
        self._cache = {}

    def get_user(self, user_id):
        """Look up a user."""
        return self._db.find(user_id)


def helper_function(param):
    """Helper function."""
    return param
```

---

## 3-A. Comment and Docstring Style

- **Intended readers**: Non-software engineers (mechanical, electrical, on-site QA, subcontractors) may also read the code. Therefore, docstrings should not overuse jargon, and should be written so that even a non-expert can grasp **"what this function does and where it is used."**
- **WHAT + WHY + WHEN**: Explain the function's role (WHAT), the design/choice rationale (WHY), and the call context/order (WHEN/WHERE) together.
- A docstring is required for every module, class, and function.
- **Docstring format**: Google Style, fixed (project standard).
- **Line counting**: The 50-line-per-function / 800-line-per-file limits are based on **executable code (SLOC)**. Docstrings, comments, and blank lines are excluded. Writing comments generously is encouraged.
- **Language parameter**: The prose above assumes the `.harness.toml [language].docstring_lang` default (English). Korean (or other) projects write the same structure in their chosen language by setting docstring_lang accordingly.

```python
# Single-line comment: placed above the code, stated clearly

def calculate_total(price, quantity):
    """Calculate the total from unit price and quantity.

    Args:
        price (float): Unit price (>= 0)
        quantity (int): Quantity (>= 1)

    Returns:
        float: Total amount

    Raises:
        ValueError: If price or quantity is negative
    """
    if price < 0 or quantity < 0:
        raise ValueError('price and quantity must be >= 0.')
    return price * quantity
```

### 3-1. Skeleton-First Principle (Mandatory in Phase 3 Implementation)

> Basis: [.clauderules](../../.clauderules) (Skeleton-First item), [docs/pm-guide/lifecycle-standard.md](../pm-guide/lifecycle-standard.md) (visibility first).

**Principle**: When starting a Phase 3 M-task, **before writing any body**, lay out all module/class/function **skeletons (docstring + signature)** first, pass an architect review, and only then enter the TDD RED stage.

**Why**:
1. The plan.md DoD and the actual structure (files, functions, signatures) can be cross-validated before work starts.
2. For safety-boundary tasks (`.harness.toml [safety_boundary]`), parallel security-reviewer review catches boundary distortions early.
3. Because the docstring contract (Args/Returns/Raises) is fixed, the test-writer can write RED tests accurately based on the DoD.

**Skeleton authoring rules**:
- Use only `...` or `pass` for the body (no `raise NotImplementedError` — it interferes with tests).
- Type hints are **mandatory** (both parameters and return values).
- Specify **Args/Returns/Raises/Note** in the Google Style docstring.
- Do not define constants at this stage; add them with the implementation during the GREEN stage.

```python
# Skeleton example (domain-neutral — a weighted-average calculator)
from __future__ import annotations


class WeightedAverager:
    """Component that computes the weighted average of samples within a window.

    From the input array, it weight-averages the values within +/-window
    around a reference point to compute a representative value.
    (Domain example — the actual responsibility is defined by the plan.md DoD.)

    Attributes:
        m_v_window (int): Half-width of samples to include on each side of the reference point
        m_v_center (int): Reference point index
    """

    def __init__(
        self,
        p_v_window: int = 20,
        p_v_center: int = 0,
    ) -> None:
        """Initialize WeightedAverager.

        Args:
            p_v_window: Sample half-width (>= 1)
            p_v_center: Reference point index (>= 0)

        Raises:
            ValueError: p_v_window or p_v_center out of range
        """
        ...

    def average(self, p_arr_values: list[float]) -> float:
        """Compute the weighted-average representative value from a value array.

        Args:
            p_arr_values: Input value array (float)

        Returns:
            Weighted-average representative value

        Raises:
            ValueError: len(p_arr_values) < 2*window+1

        Note:
            If the reference point falls outside the search window boundary,
            returns -1.0 so the caller can drop it.
        """
        ...
```

**Skeleton-First exemptions**:
- Configuration/build artifacts (dependency manifests, build scripts, service definitions, auto-generated models, and other self-documenting files) are exempt.
- Exempt items are **explicitly listed in the project plan.md** (the kit does not hardcode specific task IDs).

### 3-1-extension. "Programmable from comments alone" Template Level

> Background: Even if a skeleton docstring satisfies the non-engineer-reader principle,
> if it omits (a) a side-effect checklist, (b) failure paths, (c) the call graph, or (d) pseudo-code hints,
> the implementer can only orient themselves by cross-referencing plan.md. To resolve this, the following 4 sections
> are **made mandatory at the skeleton stage**.

**Required composition of the file-level docstring**:

```python
"""[One-line summary — what this file does, in one sentence for a non-engineer].

What this file does
------------------
[Plain explanation. Minimize domain terms; use analogies if needed.]

Where this module sits structurally
-------------------------
[If needed, show upstream/downstream call relationships with an ASCII diagram.]

What this file does NOT do
--------------------
[Boundaries. State responsibilities that would be a structure violation if pulled in here.]

Uses (modules this file calls):
    - {{SRC_ROOT_DOTTED}}.core.some_module
    - {{SRC_ROOT_DOTTED}}.services.config_service

Used by (modules that call this file):
    - {{SRC_ROOT_DOTTED}}.main (startup hook)
    - {{TESTS_ROOT}}.integration.test_lifespan

References:
    - research.md §<section>
    - plan.md <task ID> DoD
"""
```

**Required composition of the function/method docstring**:

```python
def on_startup() -> None:
    """[One-line summary — function purpose].

    What it does
    ---------------
    [Plain explanation. Make the whole behavior understandable even to a non-engineer.]

    When it is called
    -------------
    [Call timing/frequency. e.g. "once per process", "on every message received".]

    Args:
        name: [Description. Include units, range, and example values.]

    Returns:
        [Description. State it even if None.]

    Side Effects:
        - Binds an instance to one global state
        - Starts a background task

    Raises:
        ConfigLoadError: On missing config / parse failure — fail-fast (no retry)

    Uses:
        - services.config_service.load_config()

    Called by:
        - The startup hook registered by create_app() (once per process)

    Implementation hint (Pseudo-code):
        1. cfg = config_service.load_config(CONFIG_PATH)
        2. state.machine.transition(State.IDLE)
        3. asyncio.create_task(state.drain_loop())

    Why it is designed this way (optional):
        [Only when the design rationale is non-obvious.]

    References:
        research.md §<section> / plan.md <task ID> DoD
    """
    ...
```

**Required/optional determination per section**:

| Section | Required? | Omission condition |
|------|:-------:|---------|
| One-line summary | ✅ Required | None |
| What it does | ✅ Required | None |
| When it is called | ✅ Required | None |
| Args / Returns | ✅ Required (if a signature exists) | Omit Args if there are no parameters |
| **Side Effects** | ⭐ Required | A pure function (input → return only) states "None" |
| **Raises** | ⭐ Required | State no exceptions, or "None" |
| **Uses** | ⭐ Required | If only the standard library is used, state "Nothing beyond the standard library" |
| **Called by** | ⭐ Required | An entry function (main, etc.) states "external (uvicorn, cron, etc.)" |
| **Implementation hint** | ⭐ Required | Skeleton stage only. On GREEN completion, move 1:1 into inline comments on the right (do NOT delete — no information loss) |
| Why it is designed this way | Optional | When the design rationale is non-obvious |
| References | Optional | When the basis exists in research.md/plan.md |

⭐ = Section **made mandatory** beyond standard Google Style

**Verification method**:
- After writing the skeleton, run `code-reviewer` + `architect` in parallel review.
- Check that Uses / Called by are **bidirectionally consistent** (if A.Uses → B, then B.Called by → A must appear).
- Check that the pseudo-code steps in the implementation hint do not contradict the plan.md DoD.

---

## 4. File Organization

```python
#!/usr/bin/env python3
"""Module description.

This module provides functionality for processing user data.
"""

# 1. Standard library imports
import os
import sys
from typing import Dict, List, Optional

# 2. Third-party library imports
import requests

# 3. Internal module imports
from .models import User
from .utils import format_date

# 4. Constant definitions
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30


# 5. Class definitions
class UserService:
    """User service class."""

    def __init__(self):
        self._cache: Dict[str, User] = {}


# 6. Function definitions
def helper_function(param: str) -> str:
    """Helper function."""
    return param


# 7. Main block
if __name__ == '__main__':
    main()
```

- **Import order**: standard library → third-party → internal modules (one blank line between groups)
- File size 200-400 lines recommended, 800 lines max
- Define package boundaries clearly with `__init__.py`

---

## 5. Type Hints

- Based on Python 3.5+, type hints are recommended on all function signatures (goal: pass mypy strict)
- Use the `typing` module for complex types

```python
from typing import Dict, List, Optional

def get_users(role: str, limit: int = 10) -> List[Dict[str, str]]:
    """Return a list of users by role."""
    ...

def find_user(user_id: str) -> Optional[Dict]:
    """Look up a user (returns None if not found)."""
    ...
```

---

## 6. Function Design Rules

- Function length: **<= 50 lines of executable code (SLOC)**; if the logic exceeds 30 lines, extract a helper function and place it at the sibling level (docstrings/comments/blank lines are excluded from the count — [.clauderules](../../.clauderules))
- A function performs exactly one role (Single Responsibility Principle)
- **Function nesting max 1 level** (aim for 0 where possible) — extract nested functions to module level when possible
- When more than 3 parameters, group them into a `dataclass` or `dict`
- Prefer pure functions; minimize side effects
- **KISS principle**: no unnecessary design patterns or nested abstractions; keep the simplest structure

```python
from dataclasses import dataclass

@dataclass
class UserCreateRequest:
    name: str
    email: str
    role: str = 'user'

def create_user(request: UserCreateRequest) -> dict:
    """Create a user."""
    ...

# Extract a module-level helper instead of a nested function
def _validate_email(p_s_email: str) -> bool:
    """Validate email format."""
    return '@' in p_s_email and '.' in p_s_email.split('@')[-1]

def register_user(p_obj_data: UserCreateRequest) -> dict:
    """Register a user."""
    if not _validate_email(p_obj_data.email):
        raise ValueError('Invalid email')
    # ...
```

---

## 7. Flow Control (Early Return / Guard Clauses)

> Principle definition: [.clauderules](../../.clauderules) § Code Quality — Stability and Flow Control

Instead of deep nesting, handle invalid conditions first at the top of the function and return immediately.

```python
# Bad example — deep nesting
def process_order(order):
    if order:
        if order['items']:
            if order['is_paid']:
                # actual logic
                pass

# Good example — Guard Clauses (Early Return)
def process_order(p_obj_order: dict) -> None:
    """Process an order."""
    if not p_obj_order:
        raise ValueError('No order information.')
    if not p_obj_order.get('items'):
        raise ValueError('No order items.')
    if not p_obj_order.get('is_paid'):
        raise ValueError('Order has not been paid.')

    # actual logic — clean, with no nesting
```

---

## 8. Immutability Principle

> Principle definition: [.clauderules](../../.clauderules) § Code Quality — Stability and Flow Control

Do not modify objects/lists in place; always return a new copy to prevent side effects.

```python
from dataclasses import dataclass, replace

# Bad example — in-place modification (mutation)
def add_item(arr: list, item) -> list:
    arr.append(item)  # modifies the original
    return arr

# Good example — return a copy (immutability)
def add_item(p_arr_items: list, p_obj_item) -> list:
    return [*p_arr_items, p_obj_item]

# dataclass update — return a new instance with replace()
@dataclass(frozen=True)
class User:
    name: str
    age: int

def update_age(p_obj_user: User, p_v_new_age: int) -> User:
    return replace(p_obj_user, age=p_v_new_age)
```

---

## 9. Security

> Principle definition: [.clauderules](../../.clauderules) § Security

- **Never hardcode** secrets, API keys, or passwords in source code — use `os.environ` or a `.env` file
- Validate all external input (user input, API responses, file contents)
- Use parameterized queries for SQL (prevents SQL Injection)

```python
import os

# Bad example — hardcoding
API_KEY = 'sk-12345abcde'

# Good example — environment variable
API_KEY = os.environ.get('API_KEY')
if not API_KEY:
    raise EnvironmentError('The API_KEY environment variable is not set.')
```

---

## 10. Error Handling

```python
# Specify concrete exception types (do not use bare Exception)
try:
    result = process_data(input_data)
except ValueError as e:
    logger.error('Invalid input value: %s', e)
    raise
except IOError as e:
    logger.error('File processing error: %s', e)
    raise RuntimeError('Data processing failed') from e
```

---

## References

- [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Real Python PEP 8 Guide](https://realpython.com/python-pep8/)
