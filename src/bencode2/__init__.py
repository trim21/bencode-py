try:
    from .__bencode import BencodeDecodeError, BencodeEncodeError, bdecode, bencode

    COMPILED = True
except ModuleNotFoundError:
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
