# cython: language_level=3

from ._exceptions import BencodeDecodeError

cdef class Decoder:
    str_key: bool

    def __init__(self, str_key: bool):
        self.str_key = str_key

    def decode(self, value: bytes)-> object:
        try:
            data, length = self.__decode(value, 0)
        except (IndexError, KeyError, TypeError, ValueError) as e:
            raise BencodeDecodeError(f"not a valid bencode bytes: {e}") from e

        if length != len(value):
            raise BencodeDecodeError("invalid bencode value (data after valid prefix)")

        return data

    cdef tuple[object, int] __decode(self, x: bytes, index: int):
        if x[index] == c'l':
            return self.__decode_list(x, index)
        if x[index] == c'i':
            return self.__decode_int(x, index)
        if x[index] == c'd':
            return self.__decode_dict(x, index)
        if c'0' <= x[index] <= c'9':
            return self.__decode_str(x, index)

        raise BencodeDecodeError(
            f"unexpected token {x[index:index + 1]} at index {index}"
        )

    cdef tuple[object, int] __decode_int(self, x: bytes, index: int):
        index += 1
        new_f = x.index(b"e", index)
        try:
            n = int(x[index:new_f], 10)
        except ValueError:
            raise BencodeDecodeError(
                f'malformed int {x[index:new_f]}. index {index}'
            )

        if x[index] == c'-':
            if x[index + 1] == c"0":
                raise BencodeDecodeError(
                    f'-0 is not allowed in bencoding. index: {index}'
                )
        elif x[index] == c'0' and new_f != index + 1:
            raise BencodeDecodeError(
                f'integer with leading zero is not allowed. index: {index}'
            )
        return n, new_f + 1

    cdef tuple[list, int] __decode_list(self, x: bytes, index: int):
        r, index = [], index + 1

        while x[index] != c'e':
            v, index = self.__decode(x, index)
            r.append(v)

        return r, index + 1

    cdef tuple[bytes, int] __decode_str(self, x: bytes, index: int):
        colon = x.index(b":", index)

        if x[index] == c'0':
            if colon != index + 1:
                raise BencodeDecodeError(
                    f'malformed str/bytes length with leading 0. index {index}'
                )

        try:
            n = int(x[index:colon], 10)
        except ValueError:
            raise BencodeDecodeError(f'malformed str/bytes length {x[index:colon]}, index {index}')

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
