#pragma once
#include <fmt/core.h>
#include <gch/small_vector.hpp>

#include <Python.h>
#include <pybind11/pybind11.h>
namespace py = pybind11;

#ifdef _MSC_VER
#pragma warning(disable : 4996)
#endif

#ifdef _MSC_VER
#define print_log(format, ...)                                                                     \
                                                                                                   \
    do {                                                                                           \
        printf(__FILE__);                                                                          \
        printf(":");                                                                               \
        printf("%d", __LINE__);                                                                    \
        printf("\t%s", __FUNCTION__);                                                              \
        printf("\tDEBUG: ");                                                                       \
        fmt::println(format, __VA_ARGS__);                                                         \
    } while (0)

#else

#define print_log(format, ...)                                                                     \
    do {                                                                                           \
        printf(__FILE__);                                                                          \
        printf(":");                                                                               \
        printf("%d", __LINE__);                                                                    \
        printf("\t%s\tDEBUG: ", __PRETTY_FUNCTION__);                                              \
        fmt::println(format, ##__VA_ARGS__);                                                       \
    } while (0)

#endif

#ifdef BENCODE_CPP_DEBUG

#ifdef _MSC_VER
#define debug_print(format, ...)                                                                   \
                                                                                                   \
    do {                                                                                           \
        printf(__FILE__);                                                                          \
        printf(":");                                                                               \
        printf("%d", __LINE__);                                                                    \
        printf("\t%s", __FUNCTION__);                                                              \
        printf("\tDEBUG: ");                                                                       \
        fmt::println(format, __VA_ARGS__);                                                         \
    } while (0)

#else

#define debug_print(format, ...)                                                                   \
    do {                                                                                           \
        printf(__FILE__);                                                                          \
        printf(":");                                                                               \
        printf("%d", __LINE__);                                                                    \
        printf("\t%s\tDEBUG: ", __PRETTY_FUNCTION__);                                              \
        fmt::println(format, ##__VA_ARGS__);                                                       \
    } while (0)

#endif
#else

#define debug_print(fmt, ...)                                                                      \
    do {                                                                                           \
    } while (0)

#endif

struct EncodeError : public py::value_error {
public:
    EncodeError(std::string msg) { s = msg; }

    const char *what() const throw() { return s.c_str(); }

private:
    std::string s;
};

struct DecodeError : public py::value_error {
public:
    DecodeError(std::string msg) { s = msg; }

    const char *what() const throw() { return s.c_str(); }

private:
    std::string s;
};

class AutoFree {
public:
    PyObject *ptr;

    AutoFree(PyObject *p) { ptr = p; }

    ~AutoFree() { Py_DecRef(ptr); }
};
