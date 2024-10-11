from typing import Any

import pytest

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
        b"i-0e",
        b"i01e",
        b"iabce",
        b"1a2:qwer",  # invalid str length
        b"i123",  # invalid int
        b"01:q",  # invalid str length
        b"10:q",  # str length too big
        b"a",
        # directory keys not sorted for {'foo': 1, 'spam': 2}
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
        (b"0:", b""),
        (b"4:spam", b"spam"),
        (b"i-3e", -3),
        # (b"i9223372036854775808e", 9223372036854775808),  # longlong int +1
        # (b"i18446744073709551616e", 18446744073709551616),  # unsigned long long +1
        (b"i4927586304e", 4927586304),
        (b"le", []),
        (b"de", {}),
        (b"l4:spam4:eggse", [b"spam", b"eggs"]),
        # (b"de", {}),
        (b"d3:cow3:moo4:spam4:eggse", {b"cow": b"moo", b"spam": b"eggs"}),
        (b"d4:spaml1:a1:bee", {b"spam": [b"a", b"b"]}),
        (b"d0:4:spam3:fooi42ee", {b"": b"spam", b"foo": 42}),
    ],
)
def test_basic(raw: bytes, expected: Any):
    assert bdecode(raw) == expected


def test_decode1():
    assert bdecode(b"d1:ad2:id20:abcdefghij0123456789e1:q4:ping1:t2:aa1:y1:qe") == {
        b"a": {b"id": b"abcdefghij0123456789"},
        b"q": b"ping",
        b"t": b"aa",
        b"y": b"q",
    }
