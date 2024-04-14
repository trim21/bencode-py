# cython: language_level=3

from cpython.bytes cimport PyBytes_Check
from cpython.string cimport PyString_Check

def to_binary(s):
    if PyBytes_Check(s):
        return s

    if PyString_Check(s):
        return s.encode("utf-8", "strict")

    raise TypeError("expected binary or text (found %s)" % type(s))
