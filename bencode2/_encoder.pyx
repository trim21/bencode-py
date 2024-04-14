# cython: language_level=3

from collections.abc import Mapping
from typing import Any, Mapping

from cpython.bytes cimport PyBytes_Check
from cpython.int cimport PyInt_Check
from cpython.list cimport PyList_Check, PyList_Append
from cpython.tuple cimport PyTuple_Check
from cpython.bool cimport PyBool_Check
from cpython.dict cimport PyDict_Check
from cpython.string cimport PyString_Check

from ._exceptions import BencodeEncodeError

cpdef bytes encode(value: Any):
    r: list[bytes] = []  # makes more sense for something with lots of appends

    __encode(value, r)

    # Join parts
    return b"".join(r)

cdef __encode(value, r: list[bytes]):
    if PyDict_Check(value):
        __encode_dict(value, r)
    elif PyString_Check(value):
        __encode_str(value, r)
    elif PyList_Check(value):
        __encode_list(value, r)
    elif PyTuple_Check(value):
        __encode_list(value, r)
    elif PyBytes_Check(value):
        __encode_bytes(value, r)
    elif PyBool_Check(value):
        __encode_bool(value, r)
    elif PyInt_Check(value):
        __encode_int(value, r)
    else:
        raise BencodeEncodeError(f"type '{type(value)}' not supported")

cdef __encode_int(x: int, r: list[bytes]):
    r.extend((b"i", str(x).encode("utf-8"), b"e"))

cdef __encode_bool(x: bool, r: list[bytes]):
    if x:
        __encode_int(1, r)
    else:
        __encode_int(0, r)

cdef __encode_bytes(x: bytes, r: list[bytes]):
    PyList_Append(r, str(len(x)).encode("utf-8"))
    PyList_Append(r, b":")
    PyList_Append(r, x)

cdef __encode_str(x: str, r: list[bytes]):
    __encode_bytes(x.encode("UTF-8"), r)

cdef __encode_list(x: list | tuple, r: list[bytes]):
    PyList_Append(r, b"l")

    for i in x:
        __encode(i, r)

    PyList_Append(r, b"e")

cdef __encode_dict(x: Mapping, r: list[bytes]):
    PyList_Append(r, b"d")

    # force all keys to bytes, because str and bytes are incomparable
    i_list: list[tuple[bytes, Any]] = [(to_binary(k), v) for k, v in x.items()]
    i_list.sort(key=lambda kv: kv[0])
    __check_duplicated_keys(i_list)

    for k, v in i_list:
        __encode(k, r)
        __encode(v, r)

    PyList_Append(r, b"e")

cdef __check_duplicated_keys(s: list[tuple[bytes, Any]]):
    if len(s) == 0:
        return
    last_key: bytes = s[0][0]
    for current, _ in s[1:]:
        if last_key == current:
            raise BencodeEncodeError(
                f'find duplicated keys {last_key} and {current.decode()}'
            )
        last_key = current

cdef to_binary(s: str | bytes):
    if PyBytes_Check(s):
        return s

    if PyString_Check(s):
        return s.encode("utf-8", "strict")

    raise TypeError("expected binary or text (found %s)" % type(s))
