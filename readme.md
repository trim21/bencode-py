# A fast and correct bencode serialize/deserialize library

[![PyPI](https://img.shields.io/pypi/v/bencode2)](https://pypi.org/project/bencode2/)
[![tests](https://github.com/trim21/bencode-py/actions/workflows/tests.yaml/badge.svg)](https://github.com/trim21/bencode-py/actions/workflows/tests.yaml)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bencode2)](https://pypi.org/project/bencode2/)
[![Codecov branch](https://img.shields.io/codecov/c/github/Trim21/bencode-py/main)](https://codecov.io/gh/Trim21/bencode-py/branch/main)

This library is compiled with mypy on cpython, and pure python on pypy.

## install

```shell
pip install bencode2
```

## basic usage

```python
import bencode2


assert bencode2.bdecode(b"d4:spaml1:a1:bee") == {b"spam": [b"a", b"b"]}

# if you want to decode dict with str keys
assert bencode2.bdecode(b"d4:spaml1:a1:bee", str_key=True) == {"spam": [b"a", b"b"]}

assert bencode2.bencode({'hello': 'world'}) == b'd5:hello5:worlde'
```
