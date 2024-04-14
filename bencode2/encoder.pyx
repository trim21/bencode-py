# cython: language_level=3

from collections.abc import Mapping
from typing import Any

from ._compat import to_binary
from .exceptions import BencodeEncodeError


class BencodeEncoder:
    def __init__(self):
        pass

    def encode(self, value: Any) -> bytes:
        """
        Encode ``value`` into the bencode format.

        :param value: Value
        :type value: object

        :return: Bencode formatted string
        :rtype: str
        """
        r = []  # makes more sense for something with lots of appends

        # Encode provided value
        self.__encode(value, r)
        # self.encode_func[type(value)](value, r)

        # Join parts
        return b"".join(r)

    def __encode(self, value: Any, r: list):
        if isinstance(value, Mapping):
            self.__encode_dict(value, r)
        elif isinstance(value, str):
            self.__encode_str(value, r)
        elif isinstance(value, list):
            self.__encode_list(value, r)
        elif isinstance(value, tuple):
            self.__encode_list(value, r)
        elif isinstance(value, bytes):
            self.__encode_bytes(value, r)
        elif isinstance(value, bool):
            self.__encode_bool(value, r)
        elif isinstance(value, int):
            self.__encode_int(value, r)
        else:
            raise BencodeEncodeError(f"type '{type(value)}' not supported")

    def __encode_int(self, x: int, r: list):
        r.extend((b"i", str(x).encode("utf-8"), b"e"))

    def __encode_bool(self, x: bool, r: list):
        if x:
            self.__encode_int(1, r)
        else:
            self.__encode_int(0, r)

    def __encode_bytes(self, x: bytes, r: list):
        r.extend((str(len(x)).encode("utf-8"), b":", x))

    def __encode_str(self, x: str, r: list):
        return self.__encode_bytes(x.encode("UTF-8"), r)

    def __encode_list(self, x: list | tuple, r: list):
        r.append(b"l")

        for i in x:
            self.__encode(i, r)

        r.append(b"e")

    def __encode_dict(self, x: Mapping, r: list):
        r.append(b"d")

        # force all keys to bytes, because str and bytes are incomparable
        i_list = [(to_binary(k), v) for k, v in x.items()]
        i_list.sort(key=lambda kv: kv[0])

        for k, v in i_list:
            self.__encode(k, r)
            self.__encode(v, r)

        r.append(b"e")
