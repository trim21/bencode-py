import dataclasses
import sys
from pathlib import Path

from bencode2.__bencode import bencode as cpp_bencode
from bencode2.__bencode import decode as cpp_bdecode
from bencode2.__decoder import bdecode as py_bdecode
from bencode2.__encoder import bencode as py_bencode

# a parametrize to make codspeed add python version to benchmark
py = f"{sys.version_info.major}.{sys.version_info.minor}"

compat_peers_py = {
    "interval": 3600,
    # 50 peers
    "peers": b"1" * 6 * 50,
    "peers6": b"1" * 18 * 50,
}

single_file_torrent = (
    Path(__file__)
    .joinpath("../fixtures/ubuntu-22.04.2-desktop-amd64.iso.torrent.bin")
    .resolve()
    .read_bytes()
)

multiple_files_torrent = (
    Path(__file__)
    .joinpath("../fixtures/multiple-files.torrent.bin")
    .resolve()
    .read_bytes()
)


def test_benchmark_cpp_encode_compat_peers_bytes_key(benchmark):
    benchmark(
        cpp_bencode,
        {key.encode(): value for key, value in compat_peers_py.items()},
    )


def test_benchmark_cpp_encode_compat_peers_str_key(benchmark):
    benchmark(cpp_bencode, compat_peers_py)


def test_benchmark_cpp_decode_compat_peers(benchmark):
    benchmark(cpp_bdecode, py_bencode(compat_peers_py))


def test_benchmark_cpp_decode_single_file_torrent(benchmark):
    benchmark(cpp_bdecode, single_file_torrent)


def test_benchmark_cpp_encode_single_file_torrent(benchmark):
    benchmark(cpp_bencode, py_bdecode(single_file_torrent))


def test_benchmark_cpp_decode_multiple_files_torrent(benchmark):
    benchmark(cpp_bdecode, single_file_torrent)


def test_benchmark_cpp_encode_multiple_files_torrent(benchmark):
    benchmark(cpp_bencode, py_bdecode(single_file_torrent))


def test_benchmark_py_decode_single_file_torrent(benchmark):
    benchmark(py_bdecode, single_file_torrent)


def test_benchmark_py_encode_single_file_torrent(benchmark):
    benchmark(py_bencode, py_bdecode(single_file_torrent))


def test_benchmark_py_decode_multiple_files_torrent(benchmark):
    benchmark(py_bdecode, multiple_files_torrent)


def test_benchmark_py_encode_multiple_files_torrent(benchmark):
    benchmark(py_bencode, py_bdecode(multiple_files_torrent))


@dataclasses.dataclass(frozen=True, slots=True)
class AnnounceCompatResponse:
    interval: int
    peers: bytes
    peers6: bytes
    # "interval": 3600,
    # 50 peers
    # "peers": b"1" * 6 * 50,
    # "peers6": b"1" * 18 * 50,


def test_benchmark_cpp_encode_compact_peers_dataclass(benchmark):
    benchmark(cpp_bencode, AnnounceCompatResponse(**compat_peers_py))


def test_benchmark_py_encode_compact_peers_dataclass(benchmark):
    benchmark(py_bencode, AnnounceCompatResponse(**compat_peers_py))
