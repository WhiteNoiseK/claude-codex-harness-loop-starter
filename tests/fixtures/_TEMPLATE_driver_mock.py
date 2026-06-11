"""<PLACEHOLDER> driver/register mock skeleton — mimics an in-memory C-API/SDK.

ROLE (test fixture): in a dev/CI environment without the real driver (C bindings/vendor SDK/register
R/W), deterministically mimics in memory the driver API the adapter calls. Reproduces side effects
like init-sequence failures, completion-poll delays, and register stubs via fault/delay injection, so
that the measurement/control loop can be observed running one full cycle without real hardware — a "lens".
This file does NOT decide: validation of the "meaning" of the driver data — that is the caller-side test's job.

Copy this skeleton and fill <PLACEHOLDER> with the actual driver domain.

What this file does NOT do
--------------------------
- the real driver-protocol implementation — handled by the production adapter/SDK bindings.
- validation of data "meaning" — this mock only relays bytes/registers; correctness comparison is the caller-side test.
- fixture wiring — handled by `tests/conftest.py`.

Design principles
-----------------
- deterministic: same input → same output. Time dependence is reproducible via monotonic comparison.
- in-memory: only a register dict + timer. No real device.
- per-test isolation: the fixture creates a new instance per test → no state leakage.
- separated fault/delay injection: a `fail_next()`/`elapse_complete_delay()` control API distinct from the normal API.

Driver API (mirrors the real signatures — an example subset the adapter calls)
------------------------------------------------------------------------------
    driver.init(...)              → mock.init(...)
    driver.soft_reset()           → mock.soft_reset()
    driver.set_reg(reg, val)      → mock.set_reg(reg, val)
    driver.get_reg(reg)           → mock.get_reg(reg)
    driver.start_acquire()        → mock.start_acquire()
    driver.check_complete()       → mock.check_complete()
    driver.read_buffer(buf, n)    → mock.read_buffer(buf, n)

Uses:
    - time (monotonic clock — reproduces completion-poll delay)
    - typing

Used by:
    - tests.conftest (fixture wiring)
    - tests.unit.test_<driver>_adapter / test_<driver>_init_sequence
"""

from __future__ import annotations


class DriverMock:
    """in-memory driver mock — register dict + completion timer + fault/delay injection.

    What it does
    ------------
    Reproduces the driver's functions as methods with the same signatures. Return values are computed
    only from in-memory state (register dict · timer · preloaded buffer), so the control loop can be
    observed running without a real device. Provides error injection (`fail_next`) and delay injection
    (`elapse_complete_delay`) as a test-control API.

    Attributes:
        m_dict_regs: register stub for set_reg/get_reg.
        m_v_complete_at_mono: reference time compared against `time.monotonic()`. None means before acquire.
        m_v_complete_delay_sec: default delay until completion (seconds). Default 0.001.
        m_dict_fail_flags: key="init"/"read" etc. → exception to throw on the next call. Consumed once.
        m_b_init_done: whether init completed (detects ordering violations).
        m_buf_preloaded: predefined bytes/array that read_buffer returns. None means synthesize.

    Side Effects:
        constructor: state initialization only.
    """

    def __init__(self) -> None:
        """Initialize to a clean state."""
        # 1. initialize the register stub + timer + fault flags + status bits
        self.m_dict_regs: dict[int, int] = {}
        self.m_v_complete_at_mono: float | None = None
        self.m_v_complete_delay_sec = 0.001
        self.m_dict_fail_flags: dict[str, Exception] = {}
        self.m_b_init_done = False
        self.m_buf_preloaded: object | None = None

    # ────────────────────────────────────────────────────────────────
    # Driver API mimicry — Init / Reset
    # ────────────────────────────────────────────────────────────────

    def init(self, *p_args: object, **p_kw: object) -> int:
        """Init sequence — returns 0 on success, raises on fault injection.

        What it does
        ------------
        Mimics driver initialization. If `fail_next("init")` is queued, throws that exception and
        consumes the flag once. On success, `m_b_init_done = True`.

        Returns:
            int — 0 (success).

        Side Effects:
            - on success, `m_b_init_done = True`.
            - if `m_dict_fail_flags["init"]` is present, consume it then raise.

        Raises:
            the injected exception (default is the project's InitError).

        Implementation hint (Pseudo-code):
            1. if "init" in self.m_dict_fail_flags:
                   raise self.m_dict_fail_flags.pop("init")
            2. self.m_b_init_done = True
            3. return 0
        """
        ...

    def soft_reset(self) -> int:
        """Reset registers/timer/init flag → 0 (fault flags are preserved).

        Side Effects:
            - clears `m_dict_regs`; `m_v_complete_at_mono = None`;
              `m_b_init_done = False`. (`m_dict_fail_flags` is preserved to keep the test intent)

        Implementation hint (Pseudo-code):
            1. self.m_dict_regs.clear()
            2. self.m_v_complete_at_mono = None
            3. self.m_b_init_done = False
            4. return 0
        """
        ...

    # ────────────────────────────────────────────────────────────────
    # Driver API mimicry — register R/W
    # ────────────────────────────────────────────────────────────────

    def set_reg(self, p_v_reg: int, p_v_val: int) -> int:
        """Register write stub.

        Side Effects:
            - `m_dict_regs[p_v_reg] = p_v_val`.

        Implementation hint (Pseudo-code):
            1. self.m_dict_regs[p_v_reg] = p_v_val
            2. return 0
        """
        ...

    def get_reg(self, p_v_reg: int) -> int:
        """Register read stub — returns 0 if absent.

        Returns:
            int — the stored value or 0 (default).

        Implementation hint (Pseudo-code):
            1. return self.m_dict_regs.get(p_v_reg, 0)
        """
        ...

    # ────────────────────────────────────────────────────────────────
    # Driver API mimicry — acquire/control cycle
    # ────────────────────────────────────────────────────────────────

    def start_acquire(self) -> int:
        """Start acquisition — restart the completion timer.

        What it does
        ------------
        A signal to start one acquisition cycle. The mock sets the completion time to
        `time.monotonic() + m_v_complete_delay_sec` so that `check_complete()` returns True after the delay.

        Side Effects:
            - `m_v_complete_at_mono = time.monotonic() + m_v_complete_delay_sec`.

        Implementation hint (Pseudo-code):
            1. import time
            2. self.m_v_complete_at_mono = time.monotonic() + self.m_v_complete_delay_sec
            3. return 0
        """
        ...

    def check_complete(self) -> bool:
        """Poll for acquisition completion — True/False via monotonic comparison.

        Returns:
            bool — False if `m_v_complete_at_mono` is None or in the future, True if it has passed.

        Implementation hint (Pseudo-code):
            1. if self.m_v_complete_at_mono is None: return False
            2. import time
            3. return time.monotonic() >= self.m_v_complete_at_mono
        """
        ...

    def read_buffer(self, p_buf: object, p_v_n: int) -> int:
        """Copy acquired data into the caller's buffer (preloaded first, else synthesized).

        Args:
            p_buf: a writable buffer (length >= p_v_n).
            p_v_n: number of samples to copy.

        Returns:
            int — actual number of samples copied (= p_v_n).

        Side Effects:
            - overwrites `p_buf[:p_v_n]`.
            - if `m_dict_fail_flags["read"]` is present, consume it then raise.

        Raises:
            the injected exception (default ReadError); ValueError: when the buffer is smaller than p_v_n.

        Implementation hint (Pseudo-code):
            1. if "read" in self.m_dict_fail_flags:
                   raise self.m_dict_fail_flags.pop("read")
            2. if len(p_buf) < p_v_n: raise ValueError("buffer too small")
            3. src = self.m_buf_preloaded or _synthesize(p_v_n)
            4. p_buf[:p_v_n] = src[:p_v_n]; return p_v_n
        """
        ...

    # ────────────────────────────────────────────────────────────────
    # Test-control API (mock-only, absent from the real driver — fault/delay injection)
    # ────────────────────────────────────────────────────────────────

    def fail_next(self, p_s_op: str, p_obj_exc: Exception) -> None:
        """Queue the next call of that operation to throw an exception (consumed once).

        Args:
            p_s_op: operation keyword such as "init"/"read".
            p_obj_exc: the exception instance to throw.

        Side Effects:
            - `m_dict_fail_flags[p_s_op] = p_obj_exc`.

        Implementation hint (Pseudo-code):
            1. self.m_dict_fail_flags[p_s_op] = p_obj_exc
        """
        ...

    def set_preloaded_buffer(self, p_buf: object) -> None:
        """Pin the data that `read_buffer` returns (deterministic input).

        Side Effects:
            - `m_buf_preloaded = p_buf`.

        Implementation hint (Pseudo-code):
            1. self.m_buf_preloaded = p_buf
        """
        ...

    def elapse_complete_delay(self, p_v_ms: float) -> None:
        """Adjust the delay until completion in milliseconds (exercises the timeout path).

        Args:
            p_v_ms: milliseconds. >= 0.

        Side Effects:
            - `m_v_complete_delay_sec = p_v_ms / 1000`.

        Raises:
            ValueError: negative.

        Implementation hint (Pseudo-code):
            1. if p_v_ms < 0: raise ValueError("delay must be >= 0")
            2. self.m_v_complete_delay_sec = p_v_ms / 1000.0
        """
        ...
