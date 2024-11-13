#pragma once
#include <fmt/core.h>
#include <gch/small_vector.hpp>

#include <Python.h>

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

class AutoFree {
public:
    PyObject *ptr;

    AutoFree(PyObject *p) { ptr = p; }

    ~AutoFree() { Py_DecRef(ptr); }
};
