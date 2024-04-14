# cython: language_level=3

from typing import Any

from ._exceptions import BencodeDecodeError

cdef class Decoder:
    str_key: bool

    def __init__(self, str_key: bool):
        self.str_key = str_key

    def decode(self, value: bytes)-> Any:
        try:
            data, length = self.__decode(value, 0)
        except (IndexError, KeyError, TypeError, ValueError) as e:
            raise BencodeDecodeError(f"not a valid bencode bytes: {e}") from e

        if length != len(value):
            raise BencodeDecodeError("invalid bencode value (data after valid prefix)")

        return data

    cdef tuple[Any, int] __decode(self, x: bytes, index: int):
        if x[index] == c'l':
            return self.__decode_list(x, index)
        if x[index] == c'i':
            return self.__decode_int(x, index)
        if x[index] == c'd':
            return self.__decode_dict(x, index)
        if c'0' <= x[index] <= c'9':
            return self.__decode_str(x, index)

        raise BencodeDecodeError(
            f"unexpected token {x[index:index + 1]} at index {index}")

    cdef tuple[object, int] __decode_int(self, x: bytes, index: int):
        index += 1
        new_f = x.index(b"e", index)
        n = int(x[index:new_f])

        if x[index] == c'-':
            if x[index + 1: index + 2] == b"0":
                raise ValueError
        elif x[index] == c'0' and new_f != index + 1:
            raise ValueError

        return n, new_f + 1

    cdef tuple[list, int] __decode_list(self, x: bytes, index: int):
        r, index = [], index + 1

        while x[index] != c'e':
            v, index = self.__decode(x, index)
            r.append(v)

        return r, index + 1

    cdef tuple[bytes, int] __decode_str(self, x: bytes, index: int):
        colon = x.index(b":", index)
        n = int(x[index:colon])

        if x[index] == c'0' and colon != index + 1:
            raise ValueError

        colon += 1
        s = x[colon: colon + n]

        return s, colon + n

    cdef tuple[dict, int] __decode_dict(self, x: bytes, index: int):
        index += 1

        r = {}
        while x[index] != c'e':
            k, index = self.__decode_str(x, index)
            if self.str_key:
                k = k.decode(encoding='utf-8', errors='strict')
            r[k], index = self.__decode(x, index)

        return r, index + 1
