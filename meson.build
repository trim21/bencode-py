project(
    'bencode2',
    'cpp',
    default_options: ['cpp_std=c++17'],
)

py = import('python').find_installation(pure: false)

PURE_PY = run_command(
    py,
    '-c', 'import os; print(os.environ.get("PY_BENCODE2_PURE_PYTHON", "0"))',
    check: true,
).stdout().strip()

PY_IMPL = run_command(
    py,
    '-c', 'import sys; print(sys.implementation.name)',
    check: true,
).stdout().strip()

py.install_sources(
    'src/bencode2/__init__.py',
    'src/bencode2/__init__.pyi',
    'src/bencode2/__encoder.py',
    'src/bencode2/__decoder.py',
    'src/bencode2/py.typed',
    subdir: 'bencode2',
)

if (PURE_PY != '1') and (PY_IMPL == 'cpython')
    fs = import('fs')

    pybind11_path = run_command(
        py,
        '-c', 'import pybind11; print(pybind11.get_include());',
        check: true,
    ).stdout().strip()

    pybind11_includes = fs.relative_to(pybind11_path, meson.current_source_dir())

    add_global_arguments('-DFMT_HEADER_ONLY', language: 'cpp')
    incdir = include_directories(
        [
            pybind11_includes,
            './vendor/fmt/include',
            './vendor/small_vector/source/include',
        ],
    )
    py.extension_module(
        '__bencode',
        'src/bencode2/bencode.cpp',
        install: true,
        include_directories: incdir,
        subdir: 'bencode2',
        dependencies: py.dependency(),
    )
endif
