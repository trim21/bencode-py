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

    @pytest.mark.parametrize("use_memoryview", [False, True])
    def test_bytearray_resize_after_decode_error(self, use_memoryview: bool) -> None:
        ba = bytearray(b"invalid")
        mv = memoryview(ba) if use_memoryview else ba

        with pytest.raises(BencodeDecodeError):
            bdecode(mv)  # type: ignore[arg-type]

        ba.extend(b"ok")  # must not raise BufferError

    @pytest.mark.parametrize("use_memoryview", [False, True])
    def test_bytearray_resize_after_stress(self, use_memoryview: bool) -> None:
        for _ in range(500):
            ba = bytearray(b"bad")
            mv = memoryview(ba) if use_memoryview else ba
            with pytest.raises(BencodeDecodeError):
                bdecode(mv)  # type: ignore[arg-type]
            ba.extend(b"x")
