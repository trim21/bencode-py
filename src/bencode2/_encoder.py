from __future__ import annotations

import io
from collections import OrderedDict
from dataclasses import fields, is_dataclass
from types import MappingProxyType
from typing import Any, Mapping


class BencodeEncodeError(ValueError):
    """Bencode encode error."""


def bencode(value: Any, /) -> bytes:
    """Encode value into the bencode format."""
    with io.BytesIO() as r:
        __encode(value, r, set())
        return r.getvalue()


def __encode(value: Any, r: io.BytesIO, seen: set[int]) -> None:
    if isinstance(value, str):
        return __encode_bytes(value.encode("UTF-8"), r)

    if isinstance(value, int):
        r.write(b"i")
        # will handle bool and enum.IntEnum
        r.write(str(int(value)).encode())
        r.write(b"e")
        return

    if isinstance(value, bytes):
        return __encode_bytes(value, r)

    i = id(value)
    if isinstance(value, (dict, OrderedDict, MappingProxyType)):
        if i in seen:
            raise BencodeEncodeError(f"circular reference found {value!r}")
        seen.add(i)
        __encode_mapping(value, r, seen)
        seen.remove(i)
        return

    if isinstance(value, (list, tuple)):
        if i in seen:
            raise BencodeEncodeError(f"circular reference found {value!r}")
        seen.add(i)

        r.write(b"l")
        for item in value:
            __encode(item, r, seen)
        r.write(b"e")

        seen.remove(i)
        return

    if isinstance(value, bytearray):
        __encode_bytes(bytes(value), r)
        return

    if isinstance(value, memoryview):
        r.write(str(len(value)).encode())
        r.write(b":")
        r.write(value)
        return

    if is_dataclass(value) and not isinstance(value, type):
        if i in seen:
            raise BencodeEncodeError(f"circular reference found {value!r}")
        seen.add(i)
        __encode_dataclass(value, r, seen)
        seen.remove(i)
        return

    raise TypeError(f"type '{type(value)!r}' not supported by bencode")


def __encode_bytes(x: bytes, r: io.BytesIO) -> None:
    r.write(str(len(x)).encode())
    r.write(b":")
    r.write(x)


def __encode_mapping(x: Mapping[Any, Any], r: io.BytesIO, seen: set[int]) -> None:
    r.write(b"d")

    # force all keys to bytes, because str and bytes are incomparable
    i_list: list[tuple[bytes, object]] = [(to_binary(k), v) for k, v in x.items()]
    if not i_list:
        r.write(b"e")
        return
    i_list.sort(key=lambda kv: kv[0])
    __check_duplicated_keys(i_list)

    for k, v in i_list:
        __encode_bytes(k, r)
        __encode(v, r, seen)

    r.write(b"e")


def __encode_dataclass(x: Any, r: io.BytesIO, seen: set[int]) -> None:
    keys = fields(x)
    if not keys:
        r.write(b"de")
        return

    r.write(b"d")

    ks = sorted([k.name for k in keys])

    # no need to check duplicated keys, dataclasses will check this.

    for k in ks:
        __encode_bytes(k.encode(), r)
        __encode(getattr(x, k), r, seen)

    r.write(b"e")


def __check_duplicated_keys(s: list[tuple[bytes, object]]) -> None:
    last_key: bytes = s[0][0]
    for current, _ in s[1:]:
        if last_key == current:
            raise BencodeEncodeError(
                f"find duplicated keys {last_key!r} and {current.decode()}"
            )
        last_key = current


def to_binary(s: str | bytes) -> bytes:
    if isinstance(s, bytes):
        return s

    if isinstance(s, str):
        return s.encode("utf-8", "strict")

    raise TypeError(f"expected binary or text (found {type(s)})")
