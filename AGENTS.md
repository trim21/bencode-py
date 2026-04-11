# Project Guidelines

## Architecture
- `src/bencode2/__init__.py` selects the native nanobind module `__bencode` when a copied extension exists in `src/bencode2`; otherwise it falls back to `__decoder.py` and `__encoder.py`.
- Keep the C++ and Python implementations behaviorally aligned. If encode or decode semantics, validation rules, or error behavior change in one path, update the other path and the relevant tests in `tests/`.
- Preserve the core library invariants: decode bencode string values as `bytes`, not `str`; reject malformed integers and byte lengths; keep dictionary keys sorted and reject duplicates.

## Code Style
- Python targets 3.10 and follows the Black, Ruff, and strict mypy configuration in `pyproject.toml`. Keep Python type annotations explicit and match existing exception types.
- Native code is C++20 with nanobind, fmt, and Meson. Follow the existing direct parsing and error handling style instead of introducing parallel code paths for the same rule.
- Keep the public API surface stable unless the task explicitly changes it: `bencode`, `bdecode`, `BencodeEncodeError`, `BencodeDecodeError`, and `COMPILED`.

## Build And Test
- Use the workspace virtual environment and `uv` for Python dependency sync: `uv sync --dev --no-install-project`.
- Pure-Python validation: make sure `src/bencode2` does not contain a copied `__bencode` binary, then run `PYTHONPATH=src pytest --assert-pkg-compiled=false tests`.
- Native validation: run `meson setup build`, `meson compile -C build`, and `ninja -C build copy`, then run `PYTHONPATH=src pytest --assert-pkg-compiled=true tests`.
- When a change touches encoder or decoder semantics, run both the pure-Python and compiled test paths.

## Conventions
- `tests/conftest.py` uses `--assert-pkg-compiled=true|false` to assert which implementation is under test. Keep that signal meaningful.
- `tests/test_decode.py`, `tests/test_encode.py`, and `tests/test_torrent.py` are the primary regression suites. Add focused tests next to the behavior you change.
- `ninja -C build copy` changes import behavior for the whole repo by copying the built extension back into `src/bencode2`.
- Use the workspace skills for repeated workflows: `compiled-extension-workflow`, `pure-python-fallback`, and `implementation-parity`.
