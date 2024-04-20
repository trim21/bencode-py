from typing import Any

from ._exceptions import BencodeDecodeError


char_l = b"l"[0]
char_i = b"i"[0]
char_e = b"e"[0]
char_d = b"d"[0]
char_0 = b"0"[0]
char_9 = b"9"[0]
char_dash = b"-"[0]


def atoi(b: bytes) -> int:
    sign: int = 1
    offset: int = 0

    if b[0] == char_dash:
        sign = -1
        offset = 1

    total: int = 0
    for c in b[offset:]:
        if not (char_0 <= c <= char_9):
            raise ValueError
        total = total * 10 + (c - char_0)

    return total * sign


class Decoder:
    str_key: bool

    def __init__(self, str_key: bool):
        self.str_key = str_key

    def decode(self, value: bytes) -> object:
        try:
            data, length = self.__decode(value, 0)
        except (IndexError, KeyError, TypeError, ValueError) as e:
            raise BencodeDecodeError(f"not a valid bencode bytes: {e}") from e

        if length != len(value):
            raise BencodeDecodeError("invalid bencode value (data after valid prefix)")

        return data

    def __decode(self, x: bytes, index: int) -> tuple[Any, int]:
        if x[index] == char_l:
            return self.__decode_list(x, index)
        if x[index] == char_i:
            return self.__decode_int(x, index)
        if x[index] == char_d:
            if self.str_key:
                return self.__decode_str_dict(x, index)
            else:
                return self.__decode_bytes_dict(x, index)
        if char_0 <= x[index] <= char_9:
            return self.__decode_bytes(x, index)

        raise BencodeDecodeError(
            f"unexpected token {x[index:index + 1]!r} at index {index}"
        )

    def __decode_int(self, x: bytes, index: int) -> tuple[int, int]:
        index += 1
        new_f = x.index(b"e", index)
        try:
            n = atoi(x[index:new_f])
        except ValueError:
            raise BencodeDecodeError(f"malformed int {x[index:new_f]!r}. index {index}")

        if x[index] == char_dash:
            if x[index + 1] == char_0:
                raise BencodeDecodeError(
                    f"-0 is not allowed in bencoding. index: {index}"
                )
        elif x[index] == char_0 and new_f != index + 1:
            raise BencodeDecodeError(
                f"integer with leading zero is not allowed. index: {index}"
            )
        return n, new_f + 1

    def __decode_list(self, x: bytes, index: int) -> tuple[list, int]:
        r, index = [], index + 1

        while x[index] != char_e:
            v, index = self.__decode(x, index)
            r.append(v)

        return r, index + 1

    def __decode_bytes(self, x: bytes, index: int) -> tuple[bytes, int]:
        colon = x.index(b":", index)

        if x[index] == char_0:
            if colon != index + 1:
                raise BencodeDecodeError(
                    f"malformed str/bytes length with leading 0. index {index}"
                )

        try:
            n = atoi(x[index:colon])
        except ValueError:
            raise BencodeDecodeError(
                f"malformed str/bytes length {x[index:colon]!r}, index {index}"
            )

        colon += 1
        s = x[colon : colon + n]

        return s, colon + n

    def __decode_str_dict(self, x: bytes, index: int) -> tuple[dict, int]:
        index += 1

        r: dict[str, Any] = {}
        while x[index] != char_e:
            k, index = self.__decode_bytes(x, index)
            kk = k.decode(encoding="utf-8", errors="strict")
            r[kk], index = self.__decode(x, index)

        return r, index + 1

    def __decode_bytes_dict(self, x: bytes, index: int) -> tuple[dict, int]:
        index += 1

        r: dict[bytes, Any] = {}
        while x[index] != char_e:
            k, index = self.__decode_bytes(x, index)
            r[k], index = self.__decode(x, index)

        return r, index + 1
