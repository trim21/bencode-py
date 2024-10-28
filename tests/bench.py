import dataclasses
import sys
from pathlib import Path

import bencode2

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


def test_benchmark_encode_compat_peers_bytes_key(benchmark):
    benchmark(
        bencode2.bencode,
        {key.encode(): value for key, value in compat_peers_py.items()},
    )


def test_benchmark_encode_compat_peers_str_key(benchmark):
    benchmark(bencode2.bencode, compat_peers_py)


def test_benchmark_decode_compat_peers(benchmark):
    benchmark(bencode2.bdecode, bencode2.bencode(compat_peers_py))


def test_benchmark_decode_single_file_torrent(benchmark):
    benchmark(bencode2.bdecode, single_file_torrent)


def test_benchmark_encode_single_file_torrent(benchmark):
    benchmark(bencode2.bencode, bencode2.bdecode(single_file_torrent))


@dataclasses.dataclass(frozen=True, slots=True)
class AnnounceCompatResponse:
    interval: int
    peers: bytes
    peers6: bytes
    # "interval": 3600,
    # 50 peers
    # "peers": b"1" * 6 * 50,
    # "peers6": b"1" * 18 * 50,


def test_benchmark_encode_compact_peers_dataclass(benchmark):
    benchmark(bencode2.bencode, AnnounceCompatResponse(**compat_peers_py))
