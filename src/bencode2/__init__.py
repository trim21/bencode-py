try:  # pragma: no cover
    from .__bencode import BencodeDecodeError, BencodeEncodeError, bdecode, bencode

    COMPILED = True
except ImportError:  # pragma: no cover
    from .__decoder import BencodeDecodeError, bdecode
    from .__encoder import BencodeEncodeError, bencode

    COMPILED = False

__all__ = (
    "BencodeDecodeError",
    "BencodeEncodeError",
    "bencode",
    "bdecode",
    "COMPILED",
)
