# cython: language_level=3

from typing import Any

from .decoder import BencodeDecoder
from .encoder import encode
from .exceptions import BencodeDecodeError, BencodeEncodeError

__all__ = (
    "BencodeDecodeError",
    "BencodeEncodeError",
    "bencode",
    "bdecode",
)


def bencode(value: Any) -> bytes:
    """
    Encode ``value`` into the bencode format.

    :param value: Value
    :type value: object

    :return: Bencode formatted string
    """
    return encode(value)


_decoder = BencodeDecoder()


def bdecode(value: bytes) -> Any:
    """
    Decode bencode formatted byte string ``value``.

    :param value: Bencode formatted string
    :type value: bytes

    :return: Decoded value
    :rtype: object
    """
    return _decoder.decode(value)
