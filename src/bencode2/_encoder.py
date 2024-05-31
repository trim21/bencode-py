from __future__ import annotations

import io
from collections import OrderedDict
from types import MappingProxyType
from typing import Any


class BencodeEncodeError(Exception):
    """Bencode encode error."""


def encode(value: Any) -> bytes:
    with io.BytesIO() as r:
        __encode(value, r, set())
        return r.getvalue()


def __encode(value: Any, r: io.BytesIO, seen: set[int]) -> None:
    if isinstance(value, str):
        return __encode_str(value, r)
    if isinstance(value, bytes):
        return __encode_bytes(value, r)
    if isinstance(value, bool):
        if value is True:
            r.write(b"i1e")
        else:
            r.write(b"i0e")
        return

    if isinstance(value, int):
        return __encode_int(value, r)

    i = id(value)
    if isinstance(value, OrderedDict):
        if i in seen:
            raise BencodeEncodeError(f"circular reference found {value!r}")
        seen.add(i)
        __encode_mapping(value, r, seen)
        seen.remove(i)
        return

    if isinstance(value, dict):
        if i in seen:
            raise BencodeEncodeError(f"circular reference found {value!r}")
        seen.add(i)
        __encode_dict(value, r, seen)
        seen.remove(i)
        return
    if isinstance(value, list):
        if i in seen:
            raise BencodeEncodeError(f"circular reference found {value!r}")
        seen.add(i)
        __encode_list(value, r, seen)
        seen.remove(i)
        return
    if isinstance(value, tuple):
        if i in seen:
            raise BencodeEncodeError(f"circular reference found {value!r}")
        seen.add(i)
        __encode_tuple(value, r, seen)
        seen.remove(i)
        return

    if isinstance(value, MappingProxyType):
        if i in seen:
            raise BencodeEncodeError(f"circular reference found {value!r}")
        seen.add(i)
        __encode_mapping_proxy(value, r, seen)
        seen.remove(i)
        return

    if isinstance(value, bytearray):
        __encode_bytes(bytes(value), r)
        return

    raise TypeError(f"type '{type(value)!r}' not supported by bencode")


def __encode_int(x: int, r: io.BytesIO) -> None:
    r.write(b"i")
    r.write(str(x).encode())
    r.write(b"e")


def __encode_bytes(x: bytes, r: io.BytesIO) -> None:
    r.write(str(len(x)).encode())
    r.write(b":")
    r.write(x)


def __encode_str(x: str, r: io.BytesIO) -> None:
    __encode_bytes(x.encode("UTF-8"), r)


def __encode_list(x: list[Any], r: io.BytesIO, seen: set[int]) -> None:
    r.write(b"l")

    for i in x:
        __encode(i, r, seen)

    r.write(b"e")


def __encode_tuple(x: tuple[Any, ...], r: io.BytesIO, seen: set[int]) -> None:
    r.write(b"l")

    for i in x:
        __encode(i, r, seen)

    r.write(b"e")


def __encode_mapping_proxy(
    x: MappingProxyType[Any, Any], r: io.BytesIO, seen: set[int]
) -> None:
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


def __encode_mapping(x: OrderedDict[Any, Any], r: io.BytesIO, seen: set[int]) -> None:
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


def __encode_dict(x: dict[Any, Any], r: io.BytesIO, seen: set[int]) -> None:
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
