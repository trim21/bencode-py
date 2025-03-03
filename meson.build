project(
    'bencode2',
    'cpp',
    default_options: [
        'c_std=c11',
        'cpp_std=c++2c',
        'buildtype=release',
        'debug=false',
    ],
    meson_version: '>= 1.3.0',
)

if get_option('b_coverage')
    if meson.get_compiler('cpp').get_id() == 'clang'
        add_project_arguments('-fprofile-instr-generate', language: 'cpp')
        add_project_arguments('-fcoverage-mapping', language: 'cpp')
        add_project_arguments('-fprofile-arcs', language: 'cpp')
        add_global_link_arguments('-fprofile-instr-generate', language: 'c')
    endif
endif

py = import('python').find_installation(pure: false)

py.install_sources(
    'src/bencode2/__init__.py',
    'src/bencode2/__init__.pyi',
    'src/bencode2/__encoder.py',
    'src/bencode2/__decoder.py',
    'src/bencode2/py.typed',
    subdir: 'bencode2',
)

add_project_arguments('-DFMT_HEADER_ONLY', language: 'cpp')

add_project_arguments('-DLIBCXX_HARDENING_MODE=fast', language: 'cpp')

if get_option('be-debug').enabled()
    add_project_arguments('-DBENCODE_CPP_DEBUG', language: 'cpp')
endif

nanobind_dep = dependency('nanobind', static: true)


out = py.extension_module(
    '__bencode',
    'src/bencode2/bencode.cpp',
    'src/bencode2/encode.cpp',
    'src/bencode2/decode.cpp',
    install: true,
    include_directories: include_directories(
        './vendor/small_vector/source/include/',
        './vendor/fmt/include/',
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
