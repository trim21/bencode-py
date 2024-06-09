from __future__ import annotations

import bencode2


def pytest_addoption(parser):
    parser.addoption("--assert-pkg-compiled", action="store", default=None)


def pytest_configure(config):
    assert_pkg_compiled: str | None = config.option.assert_pkg_compiled
    if assert_pkg_compiled is None:
        return

    if assert_pkg_compiled == "true":
        assert bencode2.COMPILED
    elif assert_pkg_compiled == "false":
        assert not bencode2.COMPILED
    else:
        raise ValueError(
            f"unexpected --assert-pkg-compiled option, should be true/false,"
            f" got {assert_pkg_compiled!r} instead"
        )
