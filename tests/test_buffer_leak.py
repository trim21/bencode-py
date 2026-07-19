"""
Regression test: decoding a malformed input from bytearray/memoryview
must release the underlying buffer so the bytearray can be resized afterwards.
"""

import pytest

from bencode2 import COMPILED, BencodeDecodeError, bdecode


@pytest.mark.skipif(
    not COMPILED,
    reason="only relevant to compiled extension (C++ decoder uses PyObject_GetBuffer)",
)
class TestBufferRelease:
    """Ensure PyBuffer_Release is always called, even on decode errors."""

    def test_bytearray_resize_after_decode_error(self) -> None:
        ba = bytearray(b"invalid")
        with pytest.raises(BencodeDecodeError):
            bdecode(ba)
        ba.extend(b"ok")

    def test_memoryview_of_bytearray(self) -> None:
        """memoryview itself holds a buffer export on the underlying bytearray,
        so it must be released before the bytearray can be resized."""
        ba = bytearray(b"invalid")
        with pytest.raises(BencodeDecodeError):
            bdecode(memoryview(ba))
        # memoryview already out of scope, bdecode's buffer should be released
        ba.extend(b"ok")

    def test_bytearray_resize_after_stress(self) -> None:
        for _ in range(500):
            ba = bytearray(b"bad")
            with pytest.raises(BencodeDecodeError):
                bdecode(ba)
            ba.extend(b"x")

    def test_memoryview_after_stress(self) -> None:
        for _ in range(500):
            ba = bytearray(b"bad")
            with pytest.raises(BencodeDecodeError):
                bdecode(memoryview(ba))
            ba.extend(b"x")
