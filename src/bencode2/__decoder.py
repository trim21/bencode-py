from __future__ import annotations

from typing import Any, Final

from typing_extensions import Buffer

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


class BencodeDecodeError(ValueError):
    """Bencode decode error."""


def bdecode(value: Buffer, /) -> Any:
    """Decode bencode formatted bytes to python value."""
    if not isinstance(value, bytes):
        value = memoryview(value).tobytes()
    if not value:
        raise BencodeDecodeError("empty input")
    return Decoder(value).decode()


class Decoder:
    value: bytes
    mw: memoryview
    index: int
    size: int

    __slots__ = ("value", "mw", "index", "size")

    def __init__(self, value: bytes) -> None:
        self.value = value
        self.size = len(value)
        self.mw = memoryview(value)
        self.index = 0

    def decode(self) -> object:
        data = self.__decode()

        if self.index != self.size:  # pragma: no cover
            raise BencodeDecodeError("invalid bencode value (data after valid prefix)")

        return data

    def __decode(self) -> object:
        if char_0 <= self.value[self.index] <= char_9:
            return self.__decode_bytes()
        if self.value[self.index] == char_i:
            return self.__decode_int()
        if self.value[self.index] == char_d:
            return self.__decode_dict()
        if self.value[self.index] == char_l:
            return self.__decode_list()

        raise BencodeDecodeError(
            f"unexpected token {self.value[self.index:self.index + 1]!r}. "
            f"index {self.index}"
        )

    def __decode_int(self) -> int:
        self.index += 1
        try:
            index_end = self.value.index(char_e, self.index)
        except ValueError:
            raise BencodeDecodeError(
                f"invalid int, failed to found end. index {self.index}"
            )

        try:
            n = atoi(self.mw[self.index : index_end])
        except ValueError:
            raise BencodeDecodeError(
                f"malformed int {self.value[self.index:index_end]!r}. index {self.index}"
            )

        if self.value[self.index] == char_dash:
            if self.value[self.index + 1] == char_0:
                raise BencodeDecodeError(
                    f"-0 is not allowed in bencoding. index: {self.index}"
                )
        elif self.value[self.index] == char_0 and index_end != self.index + 1:
            raise BencodeDecodeError(
                f"integer with leading zero is not allowed. index: {self.index}"
            )
        self.index = index_end + 1
        return n

    def __decode_list(self) -> list[Any]:
        r: list[Any] = []
        self.index += 1

        while True:
            if self.index >= self.size:
                raise BencodeDecodeError(
                    f"buffer overflow when decoding array, index {self.index}"
                )

            if self.value[self.index] == char_e:
                break

            v = self.__decode()
            r.append(v)

        self.index += 1
        return r

    def __decode_bytes(self) -> bytes:
        try:
            index_colon = self.value.index(char_colon, self.index)
        except ValueError:
            raise BencodeDecodeError(
                f"invalid bytes, failed find expected char ':'. index {self.index}"
            )

        if self.value[self.index] == char_0:
            if index_colon != self.index + 1:
                raise BencodeDecodeError(
                    f"malformed str/bytes length with leading 0. index {self.index}"
                )

        n: int = 0
        for c in self.value[self.index : index_colon]:
            if not (char_0 <= c <= char_9):
                raise BencodeDecodeError(
                    f"malformed str/bytes length {self.value[self.index:index_colon]!r}."
                    f" index {self.index}"
                )

            n = n * 10 + (c - char_0)

        if index_colon + n >= self.size:
            raise BencodeDecodeError(
                f"malformed str/bytes length, buffer overflow. index {self.index}"
            )

        index_colon += 1

        s = self.value[index_colon : index_colon + n]

        self.index = index_colon + n

        return s

    def __decode_dict(self) -> dict[str | bytes, Any]:
        start_index = self.index
        self.index += 1

        items: list[tuple[bytes, Any]] = []

        while True:
            if self.index >= self.size:
                raise BencodeDecodeError(
                    f"buffer overflow when decoding bytes, index {self.index}"
                )
            if self.value[self.index] == char_e:
                break
            if not (char_0 <= self.value[self.index] <= char_9):
                raise BencodeDecodeError(
                    f"directory only allow str as keys, found unexpected char '{self.value[self.index]:c}', index {self.index}"
                )
            k = self.__decode_bytes()
            v = self.__decode()
            items.append((k, v))

        if not items:
            self.index += 1
            return {}

        _check_sorted(items, start_index)

        self.index += 1

        return dict(items)


def _check_sorted(s: list[tuple[bytes, Any]], idx: int) -> None:
    i = 1
    while i < len(s):
        if s[i][0] < s[i - 1][0]:
            raise BencodeDecodeError(f"directory keys is not sorted, index {idx}")
        if s[i][0] == s[i - 1][0]:
            raise BencodeDecodeError(f"found duplicated keys in directory, index {idx}")
        i += 1
