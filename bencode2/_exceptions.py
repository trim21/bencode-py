# cython: language_level=3


class BencodeDecodeError(Exception):
    """Bencode decode error."""


class BencodeEncodeError(Exception):
    """Bencode encode error."""
