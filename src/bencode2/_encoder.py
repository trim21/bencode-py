from __future__ import annotations

from types import MappingProxyType
from typing import Any

from ._exceptions import BencodeEncodeError


def encode(value: Any) -> bytes:
    r: list[bytes] = []  # makes more sense for something with lots of appends

    __encode(value, r, set())

    # Join parts
    return b"".join(r)


def __encode(value: Any, r: list[bytes], seen: set[int]) -> None:
    if isinstance(value, str):
        return __encode_str(value, r)
    if isinstance(value, bytes):
        return __encode_bytes(value, r)
    if isinstance(value, bool):
        if value is True:
            r.append(b"i1e")
        else:
            r.append(b"i0e")
        return
    if isinstance(value, int):
        return __encode_int(value, r)

    i = id(value)
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


def __encode_int(x: int, r: list[bytes]) -> None:
    r.extend((b"i", str(x).encode(), b"e"))


def __encode_bytes(x: bytes, r: list[bytes]) -> None:
    r.extend((str(len(x)).encode(), b":", x))


def __encode_str(x: str, r: list[bytes]) -> None:
    __encode_bytes(x.encode("UTF-8"), r)


def __encode_list(x: list[Any], r: list[bytes], seen: set[int]) -> None:
    r.append(b"l")

    for i in x:
        __encode(i, r, seen)

    r.append(b"e")


def __encode_tuple(x: tuple[Any, ...], r: list[bytes], seen: set[int]) -> None:
    r.append(b"l")

    for i in x:
        __encode(i, r, seen)

    r.append(b"e")


def __encode_mapping_proxy(
    x: MappingProxyType[Any, Any], r: list[bytes], seen: set[int]
) -> None:
    r.append(b"d")

    # force all keys to bytes, because str and bytes are incomparable
    i_list: list[tuple[bytes, object]] = [(to_binary(k), v) for k, v in x.items()]
    if not i_list:
        return r.append(b"e")
    i_list.sort(key=lambda kv: kv[0])
    __check_duplicated_keys(i_list)

    for k, v in i_list:
        __encode_bytes(k, r)
        __encode(v, r, seen)

    r.append(b"e")


def __encode_dict(x: dict[Any, Any], r: list[bytes], seen: set[int]) -> None:
    r.append(b"d")

    # force all keys to bytes, because str and bytes are incomparable
    i_list: list[tuple[bytes, object]] = [(to_binary(k), v) for k, v in x.items()]
    if not i_list:
        return r.append(b"e")
    i_list.sort(key=lambda kv: kv[0])
    __check_duplicated_keys(i_list)

    for k, v in i_list:
        __encode_bytes(k, r)
        __encode(v, r, seen)

    r.append(b"e")


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
