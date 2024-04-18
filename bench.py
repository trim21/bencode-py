import pathlib

from bencode2 import bencode
from bencode2 import bdecode

root = pathlib.Path(__file__).parent

torrent_1_raw = root.joinpath("tests/fixtures/56507.torrent.bin").read_bytes()
torrent_1_data = bdecode(torrent_1_raw)

torrent_2_raw = root.joinpath(
    "tests/fixtures/ubuntu-22.04.2-desktop-amd64.iso.torrent.bin"
).read_bytes()
torrent_2_data = bdecode(torrent_2_raw)


def decode(b: bytes):
    return bdecode(b)


def test_bdecode_1(benchmark):
    benchmark(decode, torrent_1_raw)


def test_bdecode_2(benchmark):
    benchmark(decode, torrent_2_raw)


def encode(data):
    return bencode(data)


def test_bencode_1(benchmark):
    benchmark(encode, torrent_1_data)


def test_bencode_2(benchmark):
    benchmark(encode, torrent_2_data)
