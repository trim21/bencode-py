---
name: compiled-extension-workflow
description: 'Build and validate the nanobind C++ extension with meson. Use for changes in src/bencode2/*.cpp or *.hpp, meson.build, native crashes, ABI issues, import failures, or any task that must run with --assert-pkg-compiled=true.'
argument-hint: '[optional changed files or test target]'
---

# Compiled Extension Workflow

## When To Use
- Touching `src/bencode2/bencode.cpp`, `decode.cpp`, `encode.cpp`, headers, `meson.build`, or other files that affect the compiled module.
- Debugging `.pyd` or `.so` import failures, nanobind binding problems, or behavior that only reproduces when `COMPILED` is true.

## Procedure
1. Sync dev dependencies if needed: `uv sync --dev --no-install-project`.
2. Configure or refresh the build directory with `meson setup build`.
3. Compile the extension with `meson compile -C build`.
4. Copy the built module back to `src/bencode2` with `ninja -C build copy`.
5. Run compiled tests with `PYTHONPATH=src pytest --assert-pkg-compiled=true tests`.
6. If the change affects encode or decode semantics, also run the pure-Python path and update the fallback implementation.

## Checks
- After the copied binary exists in `src/bencode2`, `src/bencode2/__init__.py` should import from `.__bencode` and expose `COMPILED = True`.
- If public signatures change, keep `src/bencode2/__bencode.pyi` and `src/bencode2/__init__.pyi` aligned.
- Do not leave behavior changes native-only unless a test explicitly documents that difference.
