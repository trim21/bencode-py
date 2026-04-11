from typing import Any

import pytest
from typing_extensions import Buffer

from bencode2 import BencodeDecodeError, bdecode


def test_non_bytes_input():
    with pytest.raises(TypeError):
        bdecode("s")  # type: ignore

    with pytest.raises(TypeError):
        bdecode(1)  # type: ignore


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"1",
        b"1:",
        b"1a:",
        b"1 :",
        b"i-0e",
        b"i01e",
        b"iae",
        b"i.e",
        b"ie",
        b"i-ae",
        b"iae",
        b"iabce",
        b"1a2:qwer",  # invalid str length
        b"i123",  # invalid int
        b"01:q",  # invalid str length
        b"10:q",  # str length too big
        b"a",
        # directory keys not sorted for {'foo': 1, 'spam': 2}
        b"di1ei2ee",
        b"d3:foo4:spam3:bari42ee",
        b"d4:spaml1:a1:be",
        b"d3:keyi1e3:keyi2ee",  # duplicated keys
        b"d-3:keyi1e3:keai2ee",  # duplicated keys
        b"di1ei1e3:keai2ee",  # duplicated keys
        b"l",
        b"lee",
        b"dee",
    ],
)
def test_bad_case(raw: bytes):
    with pytest.raises(BencodeDecodeError):
        bdecode(raw)


@pytest.mark.parametrize(
    ["raw", "expected"],
    [
        (memoryview(b"0:"), b""),
        (bytearray(b"0:"), b""),
        (b"0:", b""),
        (b"4:spam", b"spam"),
        (b"i-3e", -3),
        (b"i49e", 49),
        (b"i4927586304e", 4927586304),
        (b"i9223372036854775806e", 9223372036854775806),
        (b"i9223372036854775807e", 9223372036854775807),
        (b"i9223372036854775808e", 9223372036854775808),
        (b"i-9223372036854775807e", -9223372036854775807),
        (b"i-9223372036854775808e", -9223372036854775808),
        (b"i-9223372036854775809e", -9223372036854775809),
        (b"i9223372036854775808e", 9223372036854775808),  # longlong int +1
        (b"i18446744073709551616e", 18446744073709551616),  # unsigned long long +1
        (b"i-9223372036854775808e", -9223372036854775808),
        (b"i-18446744073709551616e", -18446744073709551616),
        (b"le", []),
        (b"de", {}),
        (b"l4:spam4:eggse", [b"spam", b"eggs"]),
        # (b"de", {}),
        (b"d3:cow3:moo4:spam4:eggse", {b"cow": b"moo", b"spam": b"eggs"}),
        (b"d4:spaml1:a1:bee", {b"spam": [b"a", b"b"]}),
        (b"d0:4:spam3:fooi42ee", {b"": b"spam", b"foo": 42}),
    ],
)
def test_basic(raw: Buffer, expected: Any):
    assert bdecode(raw) == expected


def test_decode1():
    assert bdecode(b"d1:ad2:id20:abcdefghij0123456789e1:q4:ping1:t2:aa1:y1:qe") == {
        b"a": {b"id": b"abcdefghij0123456789"},
        b"q": b"ping",
        b"t": b"aa",
        b"y": b"q",
    }


def test_reject_i_dash_e():
    """i-e should not be parsed as 0, it's a malformed int (no digits after minus)."""
    with pytest.raises(BencodeDecodeError):
        bdecode(b"i-e")


def test_decode_depth_limit():
    """Deeply nested input should raise an error instead of crashing with stack overflow."""
    deep = b"l" * 5000 + b"e" * 5000
    with pytest.raises(BencodeDecodeError):
        bdecode(deep)


def test_bytes_length_overflow():
    """A crafted length prefix that would overflow Py_ssize_t should be rejected."""
    # 20-digit number that exceeds PY_SSIZE_T_MAX
    payload = b"99999999999999999999:"
    with pytest.raises(BencodeDecodeError):
        bdecode(payload)
