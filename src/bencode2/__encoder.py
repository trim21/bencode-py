from __future__ import annotations

import io
from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from types import MappingProxyType
from typing import Any


class BencodeEncodeError(ValueError):
    """Bencode encode error."""


def bencode(value: Any, /) -> bytes:
    """Encode value into the bencode format."""
    with io.BytesIO() as w:
        __encode(w, value, set(), stack_depth=0)
        return w.getvalue()


def __encode(w: io.BytesIO, value: Any, seen: set[int], stack_depth: int) -> None:
    if isinstance(value, str):
        return __encode_bytes(w, value.encode("UTF-8"))

    if isinstance(value, int):
        w.write(b"i")
        # will handle bool and enum.IntEnum
        w.write(str(int(value)).encode())
        w.write(b"e")
        return

    if isinstance(value, bytes):
        return __encode_bytes(w, value)

    stack_depth += 1

    i = id(value)
    if isinstance(value, (dict, OrderedDict, MappingProxyType)):
        if stack_depth >= 100:
            if i in seen:
                raise BencodeEncodeError(f"circular reference found {value!r}")
            seen.add(i)
        __encode_mapping(w, value, seen, stack_depth=stack_depth)
        if stack_depth >= 100:  # pragma: no cover
            seen.remove(i)
        stack_depth -= 1
        return

    if isinstance(value, (list, tuple)):
        if stack_depth >= 100:
            if i in seen:
                raise BencodeEncodeError(f"circular reference found {value!r}")
            seen.add(i)

        w.write(b"l")
        for item in value:
            __encode(w, item, seen, stack_depth=stack_depth)
        w.write(b"e")

        if stack_depth >= 100:  # pragma: no cover
            seen.remove(i)
        stack_depth -= 1

        return

    if isinstance(value, bytearray):
        __encode_bytes(w, bytes(value))
        return

    if isinstance(value, memoryview):
        w.write(str(len(value)).encode())
        w.write(b":")
        w.write(value)
        return

    if is_dataclass(value) and not isinstance(value, type):
        if stack_depth >= 100:
            if i in seen:
                raise BencodeEncodeError(f"circular reference found {value!r}")
            seen.add(i)

        __encode_dataclass(w, value, seen, stack_depth=stack_depth)

        if stack_depth >= 100:  # pragma: no cover
            seen.remove(i)
        stack_depth -= 1

        return

    raise TypeError(f"type '{type(value)!r}' not supported by bencode")


def __encode_bytes(w: io.BytesIO, val: bytes) -> None:
    w.write(str(len(val)).encode())
    w.write(b":")
    w.write(val)


def __encode_mapping(
    w: io.BytesIO,
    val: Mapping[Any, Any],
    seen: set[int],
    stack_depth: int,
) -> None:
    w.write(b"d")

    # force all keys to bytes, because str and bytes are incomparable
    i_list: list[tuple[bytes, object]] = [(to_binary(k), v) for k, v in val.items()]
    if not i_list:
        w.write(b"e")
        return
    i_list.sort(key=lambda kv: kv[0])
    __check_duplicated_keys(i_list)

    for k, v in i_list:
        __encode_bytes(w, k)
        __encode(w, v, seen, stack_depth=stack_depth)

    w.write(b"e")


def __encode_dataclass(w: io.BytesIO, x: Any, seen: set[int], stack_depth: int) -> None:
    keys = fields(x)
    if not keys:
        w.write(b"de")
        return

    w.write(b"d")

    ks = sorted([k.name for k in keys])

    # no need to check duplicated keys, dataclasses will check this.

    for k in ks:
        __encode_bytes(w, k.encode())
        __encode(w, getattr(x, k), seen, stack_depth=stack_depth)

    w.write(b"e")


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
