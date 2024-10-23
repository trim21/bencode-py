# A fast and correct bencode serialize/deserialize library

[![PyPI](https://img.shields.io/pypi/v/bencode2)](https://pypi.org/project/bencode2/)
[![tests](https://github.com/trim21/bencode-py/actions/workflows/tests.yaml/badge.svg)](https://github.com/trim21/bencode-py/actions/workflows/tests.yaml)
[![CircleCI](https://dl.circleci.com/status-badge/img/gh/trim21/bencode-py/tree/master.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/trim21/bencode-py/tree/master)
[![PyPI - Python Version](https://img.shields.io/badge/python-%3E%3D3.8%2C%3C4.0-blue)](https://pypi.org/project/bencode2/)
[![Codecov branch](https://img.shields.io/codecov/c/github/Trim21/bencode-py/master)](https://codecov.io/gh/Trim21/bencode-py/branch/master)

## introduction

Why yet another bencode package in python?

because I need a bencode library:

### 1. Correct

It should fully validate its inputs, both encoded bencode bytes, or python object to be
encoded.

And it should not decode bencode bytes to `str` by default.

Bencode doesn't have a utf-8 str type, only bytes,
so many decoder try to decode bytes to str and fallback to bytes,
**this package won't, it parse bencode bytes value as python bytes.**

It may be attempting to parse all dictionary keys as string,
but for BitTorrent v2 torrent, the keys in `pieces root` dictionary is still sha256 hash
instead of ascii/utf-8 string.

If you prefer string as dictionary keys, write a dedicated function to convert parsing
result.

Also be careful! Even file name or torrent name may not be valid utf-8 string.

### 2. Fast enough

this package is written with c++ in CPython.

### 3. still cross implement

This package sill have a pure python wheel `bencode2-${version}-py3-none-any.whl` wheel
on pypi.

Which means you can still use it in non-cpython python with same behavior.

## install

```shell
pip install bencode2
```

## basic usage

```python
import bencode2

assert bencode2.bdecode(b"d4:spaml1:a1:bee") == {b"spam": [b"a", b"b"]}

assert bencode2.bencode({'hello': 'world'}) == b'd5:hello5:worlde'
```

### Decoding

| bencode type | python type |
|:------------:|:-----------:|
|   integer    |    `int`    |
|    string    |   `bytes`   |
|    array     |   `list`    |
|  dictionary  |   `dict`    |

bencode have 4 native types, integer, string, array and dictionary.

This package will decode integer to `int`, array to `list` and
dictionary to `dict`.

Because bencode string is not defined as utf-8 string, and will contain raw bytes
bencode2 will decode bencode string to python `bytes`.

### Encoding

|            python type            | bencode type |
|:---------------------------------:|:------------:|
|              `bool`               | integer 0/1  |
|       `int`, `enum.IntEnum`       |   integer    |
|       `str`, `enum.StrEnum`       |    string    |
| `bytes`, `bytearray`,`memoryview` |    string    |
|   `list`, `tuple`, `NamedTuple`   |    array     |
|       `dict`, `OrderedDict`       |  dictionary  |
|       `types.MaapingProxy`        |  dictionary  |
|            dataclasses            |  dictionary  |

## free threading

bencode2 have a free threading wheel on pypi, build with GIL disabled.

When encoding or decoding, it will not acquire GIL and may call non-thread-safy c-api,
which mean it's the caller's responsibility to ensure thread safety.

When calling `bencode`, it's safe to encode same object in multiple threading,
but it's not safe to encoding a object and change it in another thread at same time.

Also, when decoding, `bytes` objects are immutable so it's safe to be used in multiple
threading,
but `memoryview` and `bytearray` maybe not, please make sure underlay data doesn't
change when decoding.
