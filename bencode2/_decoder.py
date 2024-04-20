from __future__ import annotations

from typing import Any, Final

from ._exceptions import BencodeDecodeError

char_l: Final[int] = 108  # b"l"[0]
char_i: Final[int] = 105  # b"i"[0]
char_e: Final[int] = 101  # b"e"[0]
char_d: Final[int] = 100  # b"d"[0]
char_0: Final[int] = 48  # b"0"[0]
char_9: Final[int] = 57  # b"9"[0]
char_dash: Final[int] = 45  # b"-"[0]


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
            return self.__decode_dict(x, index)
        if char_0 <= x[index] <= char_9:
            return self.__decode_bytes(x, index)

        raise BencodeDecodeError(
            f"unexpected token {x[index:index + 1]!r} at index {index}"
        )

    def __decode_int(self, x: bytes, index: int) -> tuple[int, int]:
        index += 1
        new_f = x.index(b"e", index)
        try:
            n = int(x[index:new_f], 10)
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
            n = int(x[index:colon], 10)
        except ValueError:
            raise BencodeDecodeError(
                f"malformed str/bytes length {x[index:colon]!r}, index {index}"
            )

        colon += 1
        s = x[colon : colon + n]

        return s, colon + n

    def __decode_dict(self, x: bytes, index: int) -> tuple[dict, int]:
        index += 1

        d: dict

        if self.str_key:
            r: dict[str, Any] = {}
            while x[index] != char_e:
                k, index = self.__decode_bytes(x, index)
                kk = k.decode(encoding="utf-8", errors="strict")
                r[kk], index = self.__decode(x, index)
            d = r
        else:
            rr: dict[bytes, Any] = {}
            while x[index] != char_e:
                k, index = self.__decode_bytes(x, index)
                rr[k], index = self.__decode(x, index)
            d = rr

        return d, index + 1
