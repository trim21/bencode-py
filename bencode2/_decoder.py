from __future__ import annotations

from typing import Any, Final

from ._exceptions import BencodeDecodeError

char_l: Final = 108  # ord("l")
char_i: Final = 105  # ord("i")
char_e: Final = 101  # ord("e")
char_d: Final = 100  # ord("d")
char_0: Final = 48  # ord("0")
char_9: Final = 57  # ord("9")
char_dash: Final = 45  # ord("-")
char_colon: Final = 58  # ord(":")


def atoi(b: memoryview) -> int:
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
    value: bytes
    mw: memoryview
    index: int

    __slots__ = ("str_key", "value", "mw", "index")

    def __init__(self, value: bytes, str_key: bool) -> None:
        self.str_key = str_key
        self.value = value
        self.mw = memoryview(value)
        self.index = 0

    def decode(self) -> object:
        try:
            data = self.__decode()
        except (IndexError, KeyError, TypeError, ValueError) as e:
            raise BencodeDecodeError(f"not a valid bencode bytes: {e}") from e

        if self.index != len(self.value):
            raise BencodeDecodeError("invalid bencode value (data after valid prefix)")

        return data

    def __index(self, b: int) -> int:
        i = self.index
        for c in self.mw[i:]:
            if c == b:
                return i
            i += 1
        raise IndexError(f"expected char {chr(b)} not found")

    def __decode(self) -> object:
        if self.value[self.index] == char_l:
            return self.__decode_list()
        if self.value[self.index] == char_i:
            return self.__decode_int()
        if self.value[self.index] == char_d:
            return self.__decode_dict()
        if char_0 <= self.value[self.index] <= char_9:
            return self.__decode_bytes()

        raise BencodeDecodeError(
            f"unexpected token {self.value[self.index:self.index + 1]!r}. "
            f"index {self.index}"
        )

    def __decode_int(self) -> int:
        self.index += 1
        new_f = self.__index(char_e)
        try:
            n = atoi(self.mw[self.index : new_f])
        except ValueError:
            raise BencodeDecodeError(
                f"malformed int {self.value[self.index:new_f]!r}. index {self.index}"
            )

        if self.value[self.index] == char_dash:
            if self.value[self.index + 1] == char_0:
                raise BencodeDecodeError(
                    f"-0 is not allowed in bencoding. index: {self.index}"
                )
        elif self.value[self.index] == char_0 and new_f != self.index + 1:
            raise BencodeDecodeError(
                f"integer with leading zero is not allowed. index: {self.index}"
            )
        self.index = new_f + 1
        return n

    def __decode_list(self) -> list:
        r: list = []
        self.index += 1

        while self.value[self.index] != char_e:
            v = self.__decode()
            r.append(v)

        self.index += 1
        return r

    def __decode_bytes(self) -> bytes:
        # colon = self.value.index(b":", self.index)
        colon = self.__index(char_colon)

        if self.value[self.index] == char_0:
            if colon != self.index + 1:
                raise BencodeDecodeError(
                    f"malformed str/bytes length with leading 0. index {self.index}"
                )

        try:
            n = atoi(self.mw[self.index : colon])
        except ValueError:
            raise BencodeDecodeError(
                f"malformed str/bytes length {self.value[self.index:colon]!r}."
                f" index {self.index}"
            )

        colon += 1
        s = self.value[colon : colon + n]

        self.index = colon + n

        return s

    def __decode_dict(self) -> dict:
        start_index = self.index
        self.index += 1

        items: list[tuple[bytes, Any]] = []
        while self.value[self.index] != char_e:
            k = self.__decode_bytes()
            v = self.__decode()
            items.append((k, v))

        _check_sorted(items, start_index)

        self.index += 1

        if self.str_key:
            return {key.decode(): value for key, value in items}

        return dict(items)


def _check_sorted(s: list[tuple[bytes, Any]], idx: int) -> None:
    i = 1
    while i < len(s):
        if s[i][0] < s[i - 1][0]:
            raise BencodeDecodeError(f"directory keys is not sorted, index {idx}")
        i += 1
