from typing import Any

import pytest

from bencode2 import bdecode


def test_decode1():
    assert bdecode(b"d1:ad2:id20:abcdefghij0123456789e1:q4:ping1:t2:aa1:y1:qe") == {
        b"a": {b"id": b"abcdefghij0123456789"},
        b"q": b"ping",
        b"t": b"aa",
        b"y": b"q",
    }


@pytest.mark.parametrize(
    ["raw", "expected"],
    [
        (b"4:spam", b"spam"),
        (b"i-3e", -3),
        (b"l4:spam4:eggse", [b"spam", b"eggs"]),
        (b"d3:cow3:moo4:spam4:eggse", {b"cow": b"moo", b"spam": b"eggs"}),
        (b"d4:spaml1:a1:bee", {b"spam": [b"a", b"b"]}),
    ],
)
def test_basic(raw: bytes, expected: Any):
    assert bdecode(raw) == expected


@pytest.mark.parametrize(
    ["raw", "expected"],
    [
        (b"d3:cow3:moo4:spam4:eggse", {"cow": b"moo", "spam": b"eggs"}),
        (b"d4:spaml1:a1:bee", {"spam": [b"a", b"b"]}),
    ],
)
def test_dict_str_key(raw: bytes, expected: Any):
    assert bdecode(raw, str_key=True) == expected
