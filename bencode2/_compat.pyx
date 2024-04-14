# cython: language_level=3

def to_binary(s):
    if isinstance(s, bytes):
        return s

    if isinstance(s, str):
        return s.encode("utf-8", "strict")

    raise TypeError("expected binary or text (found %s)" % type(s))
