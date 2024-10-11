from __future__ import annotations

import collections
import dataclasses
import enum
import sys
import types
import unittest
from typing import Any, NamedTuple

import pytest

from bencode2 import BencodeEncodeError, bencode


class EncodeTestCase(unittest.TestCase):
    def test_exception_when_strict(self):
        invalid_obj = None
        with self.assertRaises(TypeError):
            bencode(invalid_obj)

    def test_encode_str(self):
        coded = bencode("ThisIsAString")
        self.assertEqual(
            coded, b"13:ThisIsAString", msg="Failed to encode string from str."
        )

    def test_encode_int(self):
        coded = bencode(42)
        self.assertEqual(coded, b"i42e", msg="Failed to encode integer from int.")

    def test_encode_bytes(self):
        b = b"TheseAreSomeBytes"
        coded = bencode(b)
        s = bytes(str(len(b)), "utf-8")
        self.assertEqual(coded, s + b":" + b, msg="Failed to encode string from bytes.")

    def test_encode_list(self):
        s = ["a", "b", 3]
        coded = bencode(s)
        self.assertEqual(coded, b"l1:a1:bi3ee", msg="Failed to encode list from list.")

    def test_encode_tuple(self):
        t = ("a", "b", 3)
        coded = bencode(t)
        self.assertEqual(coded, b"l1:a1:bi3ee", msg="Failed to encode list from tuple.")

    def test_encode_dict(self):
        od = collections.OrderedDict()
        od["ka"] = "va"
        od["kb"] = 2
        coded = bencode(od)
        self.assertEqual(
            coded, b"d2:ka2:va2:kbi2ee", msg="Failed to encode dictionary from dict."
        )

    def test_encode_complex(self):
        od = collections.OrderedDict()
        od["KeyA"] = ["listitemA", {"k": "v"}, 3]
        od["KeyB"] = {"k": "v"}
        od["KeyC"] = 3
        od["KeyD"] = "AString"
        expected_result = (
            b"d4:KeyAl9:listitemAd1:k1:vei3ee4:KeyBd1:k1:ve4:KeyCi3e4:KeyD7:AStringe"
        )
        coded = bencode(od)
        self.assertEqual(coded, expected_result, msg="Failed to encode complex object.")


def test_encode():
    assert bencode(
        {
            "_id": "5973782bdb9a930533b05cb2",
            "isActive": True,
            "balance": "$1,446.35",
            "age": 32,
            "eyeColor": "green",
            "name": "Logan Keller",
            "gender": "male",
            "company": "ARTIQ",
            "email": "logankeller@artiq.com",
            "phone": "+1 (952) 533-2258",
            "friends": [
                {"id": 0, "name": "Colon Salazar"},
                {"id": 1, "name": "French Mcneil"},
                {"id": 2, "name": "Carol Martin"},
            ],
            "favoriteFruit": "banana",
        }
    ) == (
        b"d3:_id24:5973782bdb9a930533b05cb23:agei32e7:balance9"
        b":$1,446.357:company5:ARTIQ5:email21:logankeller@artiq.c"
        b"om8:eyeColor5:green13:favoriteFruit6:banana7:friendsld2"
        b":idi0e4:name13:Colon Salazared2:idi1e4:name13:French Mc"
        b"neiled2:idi2e4:name12:Carol Martinee6:gender4:male8:isA"
        b"ctivei1e4:name12:Logan Keller5:phone17:+1 (952) 533-2258e"
    )


def test_duplicated_type_keys():
    with pytest.raises(BencodeEncodeError):
        bencode({"string_key": 1, b"string_key": 2, "1": 2})


def test_dict_int_keys():
    with pytest.raises(TypeError):
        bencode({1: 2})
    with pytest.raises(TypeError):
        bencode(0.0)


@pytest.mark.parametrize(
    ["raw", "expected"],
    [
        (["", 1], b"l0:i1ee"),
        ({"": 2}, b"d0:i2ee"),
        ("", b"0:"),
        (True, b"i1e"),
        (False, b"i0e"),
        (-3, b"i-3e"),
        (-0, b"i0e"),
        (9223372036854775808, b"i9223372036854775808e"),  # longlong int +1
        (18446744073709551616, b"i18446744073709551616e"),  # unsigned long long +1
        (4927586304, b"i4927586304e"),
        (bytearray([1, 2, 3]), b"3:\x01\x02\x03"),
        (memoryview(b"\x01\x02\x03"), b"3:\x01\x02\x03"),
        ([b"spam", b"eggs"], b"l4:spam4:eggse"),
        ({b"cow": b"moo", b"spam": b"eggs"}, b"d3:cow3:moo4:spam4:eggse"),
        ({b"spam": [b"a", b"b"]}, b"d4:spaml1:a1:bee"),
        ({}, b"de"),
        (
            types.MappingProxyType({b"cow": b"moo", b"spam": b"eggs"}),
            b"d3:cow3:moo4:spam4:eggse",
        ),
        (types.MappingProxyType({b"spam": [b"a", b"b"]}), b"d4:spaml1:a1:bee"),
        (types.MappingProxyType({}), b"de"),
        (collections.OrderedDict(), b"de"),
    ],
)
def test_basic(raw: Any, expected: bytes):
    assert bencode(raw) == expected


def test_recursive_object():
    a = 1
    assert bencode([a, a, a, a])
    b = "test str"
    assert bencode([b, b, b, b])
    assert bencode({b: b})

    bencode([[1, 2, 3]] * 3)

    d = {}
    d["a"] = d
    with pytest.raises(BencodeEncodeError, match="circular reference found"):
        assert bencode(d)

    a = []
    a.append(a)
    with pytest.raises(BencodeEncodeError, match="circular reference found"):
        assert bencode(a)

    a = {}
    b = (a,)
    a["b"] = b
    with pytest.raises(BencodeEncodeError, match="circular reference found"):
        assert bencode(a)
    with pytest.raises(BencodeEncodeError, match="circular reference found"):
        assert bencode(b)

    a = collections.OrderedDict()
    b = (a,)
    a["b"] = b
    with pytest.raises(BencodeEncodeError, match="circular reference found"):
        assert bencode(a)

    d = {}
    p = types.MappingProxyType(d)
    d["p"] = d

    with pytest.raises(BencodeEncodeError, match="circular reference found"):
        assert bencode(d)
    with pytest.raises(BencodeEncodeError, match="circular reference found"):
        assert bencode(p)


def test_dataclasses():
    @dataclasses.dataclass
    class Obj:
        b: int
        a: str
        d: bool
        c: list[dict]

    o = Obj(b=1, a="1", d=True, c=[{}, {"a": 1}])

    assert (
        bencode(o)
        == bencode(dataclasses.asdict(o))
        == b"d1:a1:11:bi1e1:clded1:ai1eee1:di1ee"
    )

    @dataclasses.dataclass
    class C: ...

    c = C()

    assert bencode(c) == b"de"

    @dataclasses.dataclass
    class L:
        a: Any

    a = {}

    l1 = L(a=a)

    a["l"] = a

    with pytest.raises(BencodeEncodeError, match="circular reference found"):
        assert bencode(a)
    with pytest.raises(BencodeEncodeError, match="circular reference found"):
        assert bencode(l1)

    l2 = L(a=a)

    l2.a = l2

    with pytest.raises(BencodeEncodeError, match="circular reference found"):
        assert bencode(l2)


def test_enum():
    class Enum(enum.Enum):
        v = "a"

    with pytest.raises(TypeError):
        bencode(Enum.v)

    class StrEnum(str, enum.Enum):
        v = "a"

    assert bencode(StrEnum.v) == b"1:a"

    class EnumInt(enum.IntEnum):
        v = "1"

    assert bencode(EnumInt.v) == b"i1e"

    class IntEnum(int, enum.Enum):
        v = "1"

    assert bencode(IntEnum.v) == b"i1e"


@pytest.mark.skipif(sys.version_info < (3, 11), reason="enum.StrEnum need py>=3.11")
def test_str_enum():
    class EnumStr(enum.StrEnum):
        v = "s"

    assert bencode(EnumStr.v) == b"1:s"


def test_TypedDict():
    from typing import TypedDict

    class D(TypedDict):
        v: str

    assert bencode(D(v="s")) == b"d1:v1:se"


def test_NamedTuple():
    class UserNamedTuple(NamedTuple):
        v: str

    assert bencode(UserNamedTuple(v="s")) == b"l1:se"
