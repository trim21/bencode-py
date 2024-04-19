import pathlib

from bencodepy import bencode as bencodepy_bencode, bdecode as bencodepy_bdecode

from bencode2 import bencode
from bencode2 import bdecode

root = pathlib.Path(__file__).parent

torrent_1_raw = root.joinpath("tests/fixtures/56507.torrent.bin").read_bytes()
torrent_1_data = bdecode(torrent_1_raw)

torrent_2_raw = root.joinpath(
    "tests/fixtures/ubuntu-22.04.2-desktop-amd64.iso.torrent.bin"
).read_bytes()
torrent_2_data = bdecode(torrent_2_raw)


def test_decode_1_bencode2(benchmark):
    benchmark(bdecode, torrent_1_raw)


def test_decode_2_bencode2(benchmark):
    benchmark(bdecode, torrent_2_raw)


def test_encode_1_bencode2(benchmark):
    benchmark(bencode, torrent_1_data)


def test_encode_2_bencode2(benchmark):
    benchmark(bencode, torrent_2_data)


def test_decode_1_bencode_py(benchmark):
    benchmark(bencodepy_bdecode, torrent_1_raw)


def test_decode_2_bencode_py(benchmark):
    benchmark(bencodepy_bdecode, torrent_2_raw)


def test_encode_1_bencode_py(benchmark):
    benchmark(bencodepy_bencode, torrent_1_data)


def test_encode_2_bencode_py(benchmark):
    benchmark(bencodepy_bencode, torrent_2_data)
