# cython: language_level=3

from collections.abc import Callable
from typing import Any

from ._compat import to_binary
from .exceptions import BencodeDecodeError


class BencodeDecoder:
    def __init__(self):
        self.decode_func: dict[bytes, Callable[[Any, int], tuple[list, int]]] = {
            b"l": self.decode_list,
            b"i": self.decode_int,
            b"0": self.decode_string,
            b"1": self.decode_string,
            b"2": self.decode_string,
            b"3": self.decode_string,
            b"4": self.decode_string,
            b"5": self.decode_string,
            b"6": self.decode_string,
            b"7": self.decode_string,
            b"8": self.decode_string,
            b"9": self.decode_string,
            b"d": self.decode_dict,
        }

    def decode(self, value: bytes) -> Any:
        """
        Decode bencode formatted byte string ``value``.

        :param value: Bencode formatted string
        :type value: bytes

        :return: Decoded value
        :rtype: object
        """
        try:
            value = to_binary(value)
            data, length = self.decode_func[value[0:1]](value, 0)
        except (IndexError, KeyError, TypeError, ValueError):
            raise BencodeDecodeError("not a valid bencoded string")

        if length != len(value):
            raise BencodeDecodeError("invalid bencoded value (data after valid prefix)")

        return data

    def decode_int(self, x, index: int):
        index += 1
        new_f = x.index(b"e", index)
        n = int(x[index:new_f])

        if x[index : index + 1] == b"-":
            if x[index + 1 : index + 2] == b"0":
                raise ValueError
        elif x[index : index + 1] == b"0" and new_f != index + 1:
            raise ValueError

        return n, new_f + 1

    def decode_string(self, x, index: int):
        """Decode torrent bencoded 'string' in x starting at f."""
        colon = x.index(b":", index)
        n = int(x[index:colon])

        if x[index : index + 1] == b"0" and colon != index + 1:
            raise ValueError

        colon += 1
        s = x[colon : colon + n]

        return bytes(s), colon + n

    def decode_list(self, x, index: int):
        r, index = [], index + 1

        while x[index : index + 1] != b"e":
            v, index = self.decode_func[x[index : index + 1]](x, index)
            r.append(v)

        return r, index + 1

    def decode_dict(self, x, index: int):
        """Decode bencoded dictionary."""
        index += 1

        r = {}

        while x[index : index + 1] != b"e":
            k, index = self.decode_string(x, index)
            r[k], index = self.decode_func[x[index : index + 1]](x, index)

        return r, index + 1
