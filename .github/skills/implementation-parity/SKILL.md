---
name: implementation-parity
description: 'Keep the C++ extension and pure Python fallback behavior aligned. Use for encode or decode semantic changes, validation rules, security hardening, recursion or overflow fixes, error message updates, and regression tests that must cover both implementations.'
argument-hint: '[behavior change, bug, or touched files]'
---

# Implementation Parity

## When To Use
- Changing parse or encode rules in either implementation.
- Adding security hardening, overflow checks, depth limits, duplicate-key rules, or malformed input validation.
- Updating regression tests that should protect both the compiled module and the fallback path.

## Procedure
1. Locate the paired implementation before editing:
   - decode: `src/bencode2/decode.cpp` and `src/bencode2/__decoder.py`
   - encode: `src/bencode2/encode.cpp` and `src/bencode2/__encoder.py`
2. Make the semantic change in both paths unless the difference is explicitly intended and tested.
3. Add or update focused regression tests in `tests/test_decode.py`, `tests/test_encode.py`, or `tests/test_torrent.py`.
4. Run fallback validation with `PYTHONPATH=src pytest --assert-pkg-compiled=false tests`.
5. Build and run compiled validation with `meson setup build`, `meson compile -C build`, `ninja -C build copy`, and `PYTHONPATH=src pytest --assert-pkg-compiled=true tests`.

## Parity Checklist
- Decoded string values stay as `bytes`.
- Dictionary keys remain sorted and duplicated keys are rejected.
- Malformed integers and byte lengths raise `BencodeDecodeError` instead of being coerced.
- Large values do not overflow, truncate, or silently wrap.
- `--assert-pkg-compiled` continues to distinguish the path under test.
