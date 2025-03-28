from __future__ import annotations

import contextlib
import dataclasses
import secrets
import sys
import threading
import time
import tracemalloc
from typing import Any

from bencode2 import BencodeDecodeError, bdecode, bencode


@dataclasses.dataclass(frozen=True, slots=True)
class DC:
    a: int
    b: str
    c: bool
    d: list[Any]


large_binary = b" " * (100 * 1024 * 1024 + 10)


def w() -> None:
    C = type("C", (object,), {})

    bdecode(bencode(1844674407370955161600))
    bencode(large_binary)

    bdecode(bencode(DC(a=1, b="ss", c=True, d=[{"a": 1, "b": b"bb"}, (1, 2, 3)])))

    try:
        bdecode(s)
    except BencodeDecodeError:
        pass

    with contextlib.suppress(TypeError):
        bencode(DC(a=1, b="ss", c=True, d=[None]))

    try:
        bencode([1, 2, "a", b"b", None])
    except TypeError:
        pass

    try:
        bencode([1, 2, "a", b"b", C()])
    except TypeError:
        pass

    try:
        bencode({"0": s, "2": [True, C()], "3": None})
        bencode({"1": C()})
    except TypeError:
        pass


def encode_in_thread() -> None:
    t = threading.Thread(target=w)
    t.start()
    t.join()


tracemalloc.start()
while True:
    s = b"100:" + secrets.token_bytes(10)

    for c in [i for i in range(5000)]:
        encode_in_thread()

    # gc.collect()
    v = tracemalloc.get_tracemalloc_memory()
    print(v)
    if v > 10610992:
        time.sleep(1000)
        sys.exit(1)
