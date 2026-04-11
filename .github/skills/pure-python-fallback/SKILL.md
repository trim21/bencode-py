---
name: pure-python-fallback
description: 'Validate the pure Python decoder and encoder fallback. Use for changes in src/bencode2/__decoder.py or __encoder.py, PyPy compatibility, tests that should pass without the native module, or any task that must run with --assert-pkg-compiled=false.'
argument-hint: '[optional changed files or test target]'
---

# Pure Python Fallback

## When To Use
- Touching `src/bencode2/__decoder.py`, `src/bencode2/__encoder.py`, or tests that should pass when the native module is unavailable.
- Validating fallback behavior on PyPy, free-threading related changes, or local environments where the compiled module has not been copied into `src/bencode2`.

## Procedure
1. Make sure `src/bencode2` does not contain a copied `__bencode` binary from a previous Meson build. Leave `build/` alone unless the build itself is under investigation.
2. Sync dev dependencies if needed: `uv sync --dev --no-install-project`.
3. Run fallback tests with `PYTHONPATH=src pytest --assert-pkg-compiled=false tests`.
4. When semantics change, compare against the compiled path and keep shared tests implementation-agnostic.

## Checks
- `src/bencode2/__init__.py` should reach the fallback import path through `ModuleNotFoundError`.
- Do not coerce decoded bencode strings to `str`; decoded string values must remain `bytes`.
- `tests/test_encode.py::test_free` is compiled-only coverage and should not be used to judge fallback behavior.
