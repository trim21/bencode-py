"""
Regression test: the compiled encoder reuses a thread local context pool.
The pool owns its contexts, so a thread exit must free the buffers it created
instead of leaking them (up to the reuse cap each).
"""

import gc
import sys
import threading

import pytest

from bencode2 import COMPILED, bencode

pytestmark = [
    pytest.mark.skipif(
        not COMPILED,
        reason="only relevant to compiled extension (thread local CtxMgr pool)",
    ),
    pytest.mark.skipif(
        sys.platform != "linux", reason="reads RSS from /proc/self/statm"
    ),
]

PAYLOAD = b"x" * (16 * 1024 * 1024)
THREADS = 8
# THREADS * len(PAYLOAD) would be leaked per round without the fix,
# this leaves room for glibc arena and thread stack noise.
MAX_GROWTH_KB = 64 * 1024


def rss_kb() -> int:
    with open("/proc/self/statm") as f:
        return int(f.read().split()[1]) * 4096 // 1024


def encode_in_threads() -> None:
    threads = [
        threading.Thread(target=bencode, args=(PAYLOAD,)) for _ in range(THREADS)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def test_thread_context_is_freed_on_thread_exit() -> None:
    bencode(PAYLOAD)
    encode_in_threads()
    gc.collect()

    before = rss_kb()
    encode_in_threads()
    gc.collect()

    growth = rss_kb() - before
    assert growth < MAX_GROWTH_KB, f"RSS grew {growth} KiB over {THREADS} threads"
