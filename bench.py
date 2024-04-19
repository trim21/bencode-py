import pathlib
import sys

import pytest

from bencode2 import bencode
from bencode2 import bdecode

root = pathlib.Path(__file__).parent

torrent_1_raw = root.joinpath("tests/fixtures/56507.torrent.bin").read_bytes()
torrent_1_data = bdecode(torrent_1_raw)

torrent_2_raw = root.joinpath(
    "tests/fixtures/ubuntu-22.04.2-desktop-amd64.iso.torrent.bin"
).read_bytes()
torrent_2_data = bdecode(torrent_2_raw)

os = sys.platform
py_ver = "{}{}".format(*sys.version_info[:2])


def mark(fn):
    return pytest.mark.parametrize(["os", "ver"], [(os, py_ver)])(fn)


def decode(b: bytes):
    return bdecode(b)


def encode(data):
    return bencode(data)


@mark
def test_decode_1(benchmark, os, ver):
    benchmark(decode, torrent_1_raw)


@mark
def test_decode_2(benchmark, os, ver):
    benchmark(decode, torrent_2_raw)


@mark
def test_encode_1(benchmark, os, ver):
    benchmark(encode, torrent_1_data)


@mark
def test_encode_2(benchmark, os, ver):
    benchmark(encode, torrent_2_data)
