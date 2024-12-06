project(
  'fmt',
  'cpp',
  version: '11.0.2',
  license: 'MIT WITH fmt-exception',
  default_options: ['cpp_std=c++14'],
)

fmt_header_only_dep = declare_dependency(
  include_directories: 'include',
  compile_args: '-DFMT_HEADER_ONLY',
)
