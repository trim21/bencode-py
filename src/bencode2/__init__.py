try:  # pragma: no cover
    from ._bencode import BencodeDecodeError, BencodeEncodeError, bdecode, bencode

    COMPILED = True
except ImportError:  # pragma: no cover
    from ._decoder import BencodeDecodeError, bdecode
    from ._encoder import BencodeEncodeError, bencode

    COMPILED = False

__all__ = (
    "BencodeDecodeError",
    "BencodeEncodeError",
    "bencode",
    "bdecode",
    "COMPILED",
)
