# cython: language_level=3
# cython: linetrace=True
# distutils: define_macros=CYTHON_TRACE=1

class BencodeDecodeError(Exception):
    """Bencode decode error."""


class BencodeEncodeError(Exception):
    """Bencode encode error."""
