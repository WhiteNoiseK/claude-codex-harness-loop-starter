"""<PLACEHOLDER> serial-device mock skeleton — mimics frame request/response.

ROLE (test fixture): instead of a real serial port (pyserial.Serial etc.), provides an injectable,
deterministic in-memory mock so the adapter can be verified in memory for (1) whether it assembles
bytes correctly, (2) how it interprets response/status bits, and (3) how well it handles the
NACK/checksum-error paths.
This file does NOT decide: the protocol's ground truth (checksum/frame building) — that is owned by the real protocol module.

Copy this skeleton and fill <PLACEHOLDER> with the actual device domain.

What this file does NOT do
--------------------------
- the frame-parsing/checksum-computation **logic itself** — handled by the production protocol module.
  This mock **calls** those functions to build the correct frames (see the single-source rule below).
- fixture wiring — handled by `tests/conftest.py`.

PROTOCOL-TRUTH-SINGLE-SOURCE rule (CRITICAL)
--------------------------------------------
The mock does **not** implement checksum/frame building directly. It must call the functions of the
real protocol module (e.g. `{{SRC_ROOT}}.adapters.<device>.protocol`) to build the correct values.
The truth must live in exactly one place (the protocol module) so that fixing the protocol
automatically carries through to the mock/tests; if it is duplicated in two places, they silently
diverge over time (drift).

Design principles
-----------------
- deterministic: same input → same response. No randomness inside.
- in-memory: no real port/disk. Returns immediately (no timeout).
- fully caller-compatible: the adapter can plug this mock in exactly where it uses a real Serial (duck typing).

Device API (mirrors the real driver signature — the subset the adapter calls)
-----------------------------------------------------------------------------
- ``write(data: bytes) -> int``    : feed a request frame. Immediately prepares the response in the internal buffer.
- ``read(n: int) -> bytes``        : the first n bytes of the prepared response.
- ``in_waiting -> int``            : number of bytes waiting (property).
- ``flush() -> None`` / ``close() -> None``

Test-control API (mock-only — absent from the real driver, separated as fail_next_*/inject_*)
---------------------------------------------------------------------------------------------
- ``set_alarm_bit(bit, on)``         : set a status bit in the next response.
- ``set_monitor(field, val)``        : pin a monitor field value.
- ``fail_next_nack(cmd, count=1)``   : respond with NACK to that cmd for the next N times.
- ``inject_checksum_error(count=1)`` : flip 1 checksum bit in the next N responses.

Uses:
    - {{SRC_ROOT}}.adapters.<device>.protocol  (parse_request / build_reply_for /
      build_nack_reply / flip_checksum_bit — the single source of the protocol truth)

Used by:
    - tests.conftest (fixture wiring)
    - tests.unit.test_<device>_adapter / test_<device>_protocol
"""

from __future__ import annotations


class SerialDeviceMock:
    """Serial-device mock — write(frame) accumulates the correct response in a buffer, consumed by read.

    What it does
    ------------
    When the adapter calls write(frame), it parses the frame and accumulates the "correct response"
    into `m_rx_buf`. read(n) then consumes it. The response is in the real format built by the real
    protocol module, so the adapter's parsing logic can be verified against the real protocol.

    Attributes:
        m_rx_buf: response byte queue that grows on write. read consumes from the front.
        m_v_alarm_bits: status/alarm bitmap. 0 = normal.
        m_dict_monitor: monitor field name → value.
        m_dict_next_nack: cmd number → remaining NACK count.
        m_v_checksum_error_count: remaining checksum-error injection count.
        m_b_is_open: whether the port is open. False after close().

    Side Effects:
        constructor: internal field initialization only.
    """

    def __init__(self) -> None:
        """Initialize in the normal state (alarm=0, ACK)."""
        # 1. initialize the response buffer + status bits + monitor/injection counters
        self.m_rx_buf = bytearray()
        self.m_v_alarm_bits = 0
        self.m_dict_monitor: dict[str, int] = {}
        self.m_dict_next_nack: dict[int, int] = {}
        self.m_v_checksum_error_count = 0
        self.m_b_is_open = True

    # ────────────────────────────────────────────────────────────────
    # Device API (mirrors the real driver signature)
    # ────────────────────────────────────────────────────────────────

    def write(self, p_data: bytes) -> int:
        """Take a request frame and accumulate the correct response frame in the internal buffer.

        What it does
        ------------
        Parses the byte sequence via the protocol module to extract CMD/DATA, then — depending on the
        test-control state (next_nack / checksum_error / alarm / monitor) — picks one of: a normal
        response / NACK / checksum-error response, and appends it to `m_rx_buf`.

        Args:
            p_data: request frame bytes. Length varies by protocol.

        Returns:
            int — number of bytes written (= len(p_data)). pyserial convention.

        Side Effects:
            - appends the response frame to `m_rx_buf`.
            - consumes the next_nack/checksum_error counters.

        Raises:
            IOError: write while the port is closed.
            ValueError: frame parsing failure.

        Uses:
            - {{SRC_ROOT}}.adapters.<device>.protocol.parse_request
            - {{SRC_ROOT}}.adapters.<device>.protocol.build_reply_for
            - {{SRC_ROOT}}.adapters.<device>.protocol.build_nack_reply
            - {{SRC_ROOT}}.adapters.<device>.protocol.flip_checksum_bit

        Implementation hint (Pseudo-code):
            1. if not self.m_b_is_open: raise IOError("port closed")
            2. cmd, data = protocol.parse_request(p_data)
            3. if self.m_dict_next_nack.get(cmd, 0) > 0:
                   self.m_dict_next_nack[cmd] -= 1
                   frame = protocol.build_nack_reply(cmd)
               else:
                   frame = protocol.build_reply_for(
                       cmd=cmd, req_data=data,
                       monitor=self.m_dict_monitor,
                       alarm_bits=self.m_v_alarm_bits)
            4. if self.m_v_checksum_error_count > 0:
                   self.m_v_checksum_error_count -= 1
                   frame = protocol.flip_checksum_bit(frame)
            5. self.m_rx_buf.extend(frame); return len(p_data)
        """
        ...

    def read(self, p_v_n: int) -> bytes:
        """Consume and return the first `p_v_n` bytes of the internal buffer (short read allowed).

        Args:
            p_v_n: number of bytes requested. >= 0.

        Returns:
            bytes — at most p_v_n long. Shorter if the buffer is insufficient.

        Side Effects:
            - removes (consumes) the leading bytes of `m_rx_buf`.

        Raises:
            IOError: port closed.
            ValueError: p_v_n is negative.

        Implementation hint (Pseudo-code):
            1. if not self.m_b_is_open: raise IOError("closed")
            2. if p_v_n < 0: raise ValueError("n must be >= 0")
            3. take = min(p_v_n, len(self.m_rx_buf))
            4. chunk = bytes(self.m_rx_buf[:take]); del self.m_rx_buf[:take]
            5. return chunk
        """
        ...

    @property
    def in_waiting(self) -> int:
        """Number of bytes currently waiting to be read (pyserial-compatible property).

        Returns:
            int — `len(self.m_rx_buf)`.

        Implementation hint (Pseudo-code):
            1. return len(self.m_rx_buf)
        """
        ...

    def flush(self) -> None:
        """flush compatibility — a no-op in the mock (responses are rebuilt per request).

        Implementation hint (Pseudo-code):
            1. return
        """
        ...

    def close(self) -> None:
        """Close the port — subsequent write/read raise IOError.

        Side Effects:
            - `m_b_is_open = False`; clears `m_rx_buf`.

        Implementation hint (Pseudo-code):
            1. self.m_b_is_open = False
            2. self.m_rx_buf.clear()
        """
        ...

    # ────────────────────────────────────────────────────────────────
    # Test-control API (mock-only, absent from the real driver)
    # ────────────────────────────────────────────────────────────────

    def set_alarm_bit(self, p_v_bit: int, p_b_on: bool) -> None:
        """Turn a specific bit of the status/alarm bitmap on/off.

        Args:
            p_v_bit: 0 <= bit (bitmap width is project-defined).
            p_b_on: True=set, False=clear.

        Side Effects:
            - applies an OR/AND mask to `m_v_alarm_bits`.

        Raises:
            ValueError: bit out of range.

        Implementation hint (Pseudo-code):
            1. if p_b_on: self.m_v_alarm_bits |= (1 << p_v_bit)
               else:      self.m_v_alarm_bits &= ~(1 << p_v_bit)
        """
        ...

    def set_monitor(self, p_s_field: str, p_v_val: int) -> None:
        """Pin a monitor field to a specific value (unregistered keys are allowed too — for test flexibility).

        Side Effects:
            - `m_dict_monitor[p_s_field] = p_v_val`.

        Implementation hint (Pseudo-code):
            1. self.m_dict_monitor[p_s_field] = p_v_val
        """
        ...

    def fail_next_nack(self, p_v_cmd: int, p_v_count: int = 1) -> None:
        """Respond with NACK to that cmd request for the next N times (cumulative).

        Args:
            p_v_cmd: the CMD number to NACK.
            p_v_count: count. Default 1. >= 0.

        Side Effects:
            - `m_dict_next_nack[p_v_cmd] += p_v_count`.

        Raises:
            ValueError: negative.

        Implementation hint (Pseudo-code):
            1. if p_v_count < 0: raise ValueError("count must be >= 0")
            2. self.m_dict_next_nack[p_v_cmd] = (
                   self.m_dict_next_nack.get(p_v_cmd, 0) + p_v_count)
        """
        ...

    def inject_checksum_error(self, p_v_count: int = 1) -> None:
        """Flip 1 checksum bit in the next N responses (exercises the adapter verification path).

        Args:
            p_v_count: count. Default 1. >= 0.

        Side Effects:
            - `m_v_checksum_error_count += p_v_count`.

        Raises:
            ValueError: negative.

        Implementation hint (Pseudo-code):
            1. if p_v_count < 0: raise ValueError("count must be >= 0")
            2. self.m_v_checksum_error_count += p_v_count
        """
        ...
