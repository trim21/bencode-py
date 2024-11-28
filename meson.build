project(
    'bencode2',
    'cpp',
    default_options: [
        # 'cpp_std=c++17',
        'c_std=c11',
        'cpp_std=c++17',
        'buildtype=release',
        'debug=false',
    ],
    meson_version: '>= 1.3.0',
)

py_inter = import('python').find_installation()

PY_IMPL = run_command(
    py_inter,
    '-c', 'import sys; print(sys.implementation.name)',
    check: true,
).stdout().strip()

pure_py = (get_option('pure_py').enabled()) or (PY_IMPL != 'cpython')

py = import('python').find_installation(pure: pure_py)

py.install_sources(
    'src/bencode2/__init__.py',
    'src/bencode2/__init__.pyi',
    'src/bencode2/__encoder.py',
    'src/bencode2/__decoder.py',
    'src/bencode2/py.typed',
    subdir: 'bencode2',
)

if not pure_py
    if get_option('buildtype').startswith('debug')
        add_project_arguments('-DBENCODE_CPP_DEBUG', language: 'cpp')
    endif

    add_global_arguments('-DFMT_HEADER_ONLY', language: 'cpp')

    nanobind_dep = dependency('nanobind', static: true)

    out = py.extension_module(
        '__bencode',
        'src/bencode2/bencode.cpp',
        install: true,
        include_directories: include_directories(
            [
                './vendor/fmt/include/',
                './vendor/small_vector/source/include/',
            ],
        ),
        subdir: 'bencode2',
        dependencies: [nanobind_dep, py.dependency()],
    )

    custom_target(
        'copy extension back to file tree',
        input: out,
        output: 'copy',
        depends: out,
        command: [
            'cp',
            out.full_path(),
            join_paths(meson.project_source_root(), 'src/bencode2/'),
        ],
        build_by_default: false,
    )
endif
