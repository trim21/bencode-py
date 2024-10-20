cmake_minimum_required(VERSION 3.28)
project(bencode_cpp)

set(CMAKE_CXX_STANDARD 17)

add_compile_options("$<$<C_COMPILER_ID:MSVC>:/utf-8>")
add_compile_options("$<$<CXX_COMPILER_ID:MSVC>:/utf-8;/Zc:__cplusplus>")

find_package(Python COMPONENTS Interpreter Development REQUIRED)

# add python includes to find <Python.h>
include_directories(${Python3_INCLUDE_DIRS})

include_directories(./src/bencode2/)

execute_process(
        COMMAND "${Python_EXECUTABLE}" -m pybind11 --cmakedir
        OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE PYBIND11_ROOT)

include_directories(${PYBIND11_ROOT}/../../../include)

execute_process(
        COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
        OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE nanobind_ROOT)

find_package(nanobind CONFIG REQUIRED)

include_directories(./vendor/fmt/include/)
include_directories(./src/bencode2/)

nanobind_add_module(__bencode src/bencode2/bencode.cpp
        src/bencode2/overflow.h
        src/bencode2/decode.h
        src/bencode2/encode.h
        src/bencode2/common.h
        src/bencode2/encode_ctx.h
)
