cmake_minimum_required(VERSION 3.28)
project(bencode_cpp)

set(CMAKE_CXX_STANDARD 17)

add_compile_options("$<$<C_COMPILER_ID:MSVC>:/utf-8>")
add_compile_options("$<$<CXX_COMPILER_ID:MSVC>:/utf-8;/Zc:__cplusplus>")

find_package(Python3 COMPONENTS Interpreter Development)

# add python includes to find <Python.h>
include_directories(${Python3_INCLUDE_DIRS})

include_directories(./src/bencode2/)

execute_process(
        COMMAND "${Python_EXECUTABLE}" -m pybind11 --cmakedir
        OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE PYBIND11_ROOT)

include_directories(${PYBIND11_ROOT}/../../../include)

include_directories(./vendor/fmt/include/)

add_executable(
        bencode2
        src/bencode2/bencode.cpp
        src/bencode2/encode.hpp
        src/bencode2/decode.hpp
        src/bencode2/overflow.hpp
        src/bencode2/common.hpp
        src/bencode2/encode_ctx.hpp
)
