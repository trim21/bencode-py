from pathlib import Path
from typing import Any

from ._decoder import BencodeDecodeError
from ._decoder import Decoder as _Decoder
from ._encoder import BencodeEncodeError
from ._encoder import encode as _encode

COMPILED = Path(__file__).suffix in (".pyd", ".so")

__all__ = (
    "BencodeDecodeError",
    "BencodeEncodeError",
    "bencode",
    "bdecode",
    "COMPILED",
)


def bencode(value: Any, /) -> bytes:
    """Encode value into the bencode format."""
    return _encode(value)


def bdecode(value: bytes, /, *, str_key: bool = False) -> Any:
    """Decode bencode formatted bytes to python value."""
    if not isinstance(value, bytes):
        raise TypeError("only support decoding bytes")
    return _Decoder(value, str_key).decode()
