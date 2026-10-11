from __future__ import annotations

import sys
from typing import Any, Final

from typing_extensions import Buffer

char_l: Final = ord("l")
char_i: Final = ord("i")
char_e: Final = ord("e")
char_d: Final = ord("d")
char_0: Final = ord("0")
char_9: Final = ord("9")
char_dash: Final = ord("-")
char_colon: Final = ord(":")

_MAX_DECODE_DEPTH: Final = 4096


class BencodeDecodeError(ValueError):
    """Bencode decode error."""


def bdecode(value: Buffer, /) -> Any:
    """Decode bencode formatted bytes to python value."""
    return Decoder(value).decode()


class Decoder:
    value: memoryview | bytes
    index: int
    size: int

    __slots__ = ("index", "size", "value")

    def __init__(self, value: Buffer) -> None:
        view = memoryview(value)
        self.size = view.nbytes
        if self.size == 0:
            raise BencodeDecodeError("empty input")

        # Indexing into and slicing a bytes object is much cheaper than doing
        # the same through a memoryview on interpreters where the latter is
        # not optimized, PyPy being the notable one.
        self.value = value if type(value) is bytes else view.cast("B")
        self.index = 0

    def decode(self) -> object:
        data = self.__decode(0)

        if self.index != self.size:  # pragma: no cover
            raise BencodeDecodeError(
                f"invalid bencode data, parse end at index {self.index}"
                f" but total bytes length {self.size}"
            )

        return data

    def __decode(self, depth: int) -> object:
        depth += 1
        if depth > _MAX_DECODE_DEPTH:
            raise BencodeDecodeError("exceeded maximum decode depth")

        if char_0 <= self.value[self.index] <= char_9:
            return self.__decode_bytes()
        if self.value[self.index] == char_i:
            return self.__decode_int()
        if self.value[self.index] == char_d:
            return self.__decode_dict(depth)
        if self.value[self.index] == char_l:
            return self.__decode_list(depth)

        raise BencodeDecodeError(
            f"invalid bencode prefix '\\x{self.value[self.index]:02x}', index {self.index}"
        )

    def __decode_int(self) -> int:
        start_index = self.index
        self.index += 1
        value = self.value
        index_end = self.index
        while index_end < self.size and value[index_end] != char_e:
            index_end += 1
        if index_end == self.size:
            raise BencodeDecodeError(f"invalid int, missing 'e': {start_index}")

        if index_end == self.index:
            raise BencodeDecodeError(f"invalid int, found 'ie': {self.index}")

        n: int = 1
        offset: int = 0

        if value[self.index] == char_dash:
            n = -1
            offset = 1
            if self.index + offset >= index_end:
                raise BencodeDecodeError(
                    f"invalid int, '-' with no digits at {self.index}"
                )
            if value[self.index + offset] == char_0:
                raise BencodeDecodeError(f"invalid int, '-0' found at {self.index}")
        elif value[self.index] == char_0 and index_end != self.index + 1:
            raise BencodeDecodeError(
                f"invalid int, non-zero int should not start with '0'."
                f" found at {self.index}"
            )

        total: int = 0
        for i in range(self.index + offset, index_end):
            c = value[i]
            if not (char_0 <= c <= char_9):
                raise BencodeDecodeError(f"invalid int, '\\x{c:02x}' found at {i}")
            total = total * 10 + (c - char_0)

        self.index = index_end + 1
        return total * n

    def __decode_list(self, depth: int) -> list[Any]:
        r: list[Any] = []
        self.index += 1

        while True:
            if self.index >= self.size:
                raise BencodeDecodeError(
                    f"buffer overflow when decoding list, index {self.index}"
                )

            if self.value[self.index] == char_e:
                break

            v = self.__decode(depth)
            r.append(v)

        self.index += 1
        return r

    def __decode_bytes(self) -> bytes:
        value = self.value
        index_colon = self.index
        while index_colon < self.size and value[index_colon] != char_colon:
            index_colon += 1
        if index_colon == self.size:
            raise BencodeDecodeError(
                f"invalid string, missing length: index {self.index}"
            )

        if value[self.index] == char_0 and index_colon != self.index + 1:
            raise BencodeDecodeError(
                f"invalid bytes length, leading zero. index {self.index}"
            )

        n: int = 0
        for i in range(self.index, index_colon):
            c = value[i]
            if not (char_0 <= c <= char_9):
                raise BencodeDecodeError(
                    f"invalid bytes length, '\\x{c:02x}' found at {i}"
                )
            # the length is accumulated as Py_ssize_t in the c++ decoder, which
            # has to bail out on overflow before reading the whole prefix
            if n > (sys.maxsize - 9) // 10:
                raise BencodeDecodeError(f"bytes length overflow, index {self.index}")

            n = n * 10 + (c - char_0)

        if index_colon + n >= self.size:
            raise BencodeDecodeError(f"bytes length overflow, index {self.index}")

        index_colon += 1

        s = self.value[index_colon : index_colon + n]

        self.index = index_colon + n

        if isinstance(s, memoryview):
            return s.tobytes()
        return s

    def __decode_dict(self, depth: int) -> dict[str | bytes, Any]:
        start_index = self.index
        self.index += 1
        value = self.value

        items: list[tuple[bytes, Any]] = []
        last_key: bytes | None = None

        while True:
            if self.index >= self.size:
                raise BencodeDecodeError(
                    f"buffer overflow when decoding dict, index {self.index}"
                )
            if value[self.index] == char_e:
                break
            if not (char_0 <= value[self.index] <= char_9):
                raise BencodeDecodeError(
                    f"expecting bytes when parsing dict key,"
                    f" found '\\x{value[self.index]:02x}' instead,"
                    f" index {self.index}"
                )
            k = self.__decode_bytes()
            if self.index >= self.size:
                raise BencodeDecodeError(
                    f"buffer overflow when decoding dict, index {self.index}"
                )
            v = self.__decode(depth)
            if last_key is not None:
                if k < last_key:
                    raise BencodeDecodeError(
                        f"invalid dict, key not sorted. index {start_index}"
                    )
                if k == last_key:
                    raise BencodeDecodeError(
                        f"invalid dict, find duplicated keys"
                        f" '{_hex(k)}'. index {start_index}"
                    )
            last_key = k
            items.append((k, v))

        if not items:
            self.index += 1
            return {}

        self.index += 1

        return dict(items)


def _hex(value: bytes) -> str:
    return "".join(f"\\x{byte:02x}" for byte in value)
