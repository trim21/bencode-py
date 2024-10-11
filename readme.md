# A fast and correct bencode serialize/deserialize library

[![PyPI](https://img.shields.io/pypi/v/bencode2)](https://pypi.org/project/bencode2/)
[![tests](https://github.com/trim21/bencode-py/actions/workflows/tests.yaml/badge.svg)](https://github.com/trim21/bencode-py/actions/workflows/tests.yaml)
[![PyPI - Python Version](https://img.shields.io/badge/python-%3E%3D3.8%2C%3C4.0-blue)](https://pypi.org/project/bencode2/)
[![Codecov branch](https://img.shields.io/codecov/c/github/Trim21/bencode-py/master)](https://codecov.io/gh/Trim21/bencode-py/branch/master)

## introduction

Why yet another bencode package in python?

because I need a bencode library:

1. Correct, which mean it should fully validate its inputs,
   and won't try to decode bencode bytes to `str` by default.
   Bencode doesn't have a utf-8 str type, only bytes,
   so many decoder try to decode bytes to str and fallback to bytes,
   **this package won't, it parse bencode bytes value as python bytes.**
2. Fast enough, that's why this package is written with c++.
3. even cross implement, what's why
   this package sill have a pure python fallback
   and `bencode2-${version}-py3-none-any.whl` wheel on pypi.

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

bencode have 4 native types, integer, string, array and directory.

This package will decode integer to `int`, array to `list` and
directory to `dict`.

Because bencode string is not defined as utf-8 string, and will contain raw bytes
bencode2 will decode bencode string to python `bytes`.

### Encoding

Many python types are supported.

|            python type            | bencode type |
|:---------------------------------:|:------------:|
|              `bool`               | integer 0/1  |
|       `int`, `enum.IntEnum`       |   integer    |
|       `str`, `enum.StrEnum`       |    string    |
| `bytes`, `bytearray`,`memoryview` |    string    |
|   `list`, `tuple`, `NamedTuple`   |    array     |
|       `dict`, `OrderedDict`       |  directory   |
|       `types.MaapingProxy`        |  directory   |
|            dataclasses            |  directory   |
