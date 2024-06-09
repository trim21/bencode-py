import bencode2


def pytest_configure():
    if bencode2.COMPILED:
        print("[test] using compiled bencode2")
    else:
        print("[test] using non-compiled bencode2")
