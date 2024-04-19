# A bencode serialize/deserialize library based on cython

## install

```shell
pip install bencode2
```

## basic usage

```python
import bencode2

assert bencode2.bdecode(b"d4:spaml1:a1:bee") == {b"spam": [b"a", b"b"]}
assert bencode2.bdecode(b"d4:spaml1:a1:bee", str_key=True) == {"spam": [b"a", b"b"]}

assert bencode2.bencode({'hello': 'world'}) == b'd5:hello5:worlde'
```

## notice

This package is not available in pypy and is slower than [bencode-py](https://pypi.org/project/bencode.py/) in pypy.
