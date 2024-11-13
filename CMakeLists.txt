cmake_minimum_required(VERSION 3.28)
project(bencode_cpp)

set(CMAKE_CXX_STANDARD 17)

add_compile_options("$<$<CXX_COMPILER_ID:MSVC>:/utf-8;/Zc:__cplusplus>")

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

message("Found Python3 " ${Python3_VERSION})
message("Found Python3 includes " ${Python3_INCLUDE_DIRS})
message("Found PYTHON_LIBRARY " ${Python3_LIBRARIES})

add_definitions(-DFMT_HEADER_ONLY)

# add python includes to find <Python.h>
include_directories(${Python3_INCLUDE_DIRS})

execute_process(
        COMMAND "${Python3_EXECUTABLE}" -c "import pybind11;print(pybind11.get_include())"
        OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE PYBIND11_INCLUDE)

include_directories(./src/bencode2/)
include_directories(${PYBIND11_INCLUDE})
include_directories(./vendor/fmt/include/)
include_directories(./vendor/small_vector/source/include/)

add_library(
        bencode2
        SHARED
        src/bencode2/bencode.cpp
)

target_link_libraries(bencode2 ${Python3_LIBRARIES})
