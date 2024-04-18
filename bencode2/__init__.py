from typing import Any

from .bencode2 import encode, BencodeEncodeError, decode, BencodeDecodeError


def bencode(obj: Any) -> bytes:
    return encode(obj)


def bdecode(obj: bytes, *, str_key: bool = False) -> Any:
    return decode(obj, str_key=str_key)


__all__ = [
    "bencode",
    "BencodeEncodeError",
    "bdecode",
    "BencodeDecodeError",
]
