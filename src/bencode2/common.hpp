#pragma once
#include <string>
#include <string_view>

#include <fmt/core.h>
#include <fmt/ranges.h>
#include <gch/small_vector.hpp>

#include <Python.h>

#ifdef _MSC_VER
#pragma warning(disable : 4996)
#endif

#ifdef BENCODE_CPP_DEBUG

#define debug_print(format, ...)                                                                   \
                                                                                                   \
    do {                                                                                           \
        printf(__FILE__);                                                                          \
        printf(":");                                                                               \
        printf("%d", __LINE__);                                                                    \
        printf("\t%s", __FUNCTION__);                                                              \
        printf("\tDEBUG: ");                                                                       \
        fmt::println(format, ##__VA_ARGS__);                                                       \
    } while (0)

#else

#define debug_print(...)                                                                           \
    do {                                                                                           \
    } while (0)

#endif

struct EncodeError {
public:
    EncodeError(std::string msg) { s = msg; }

    const char *what() const noexcept { return s.c_str(); }

private:
    std::string s;
};

struct DecodeError {
public:
    DecodeError(std::string msg) { s = msg; }

    const char *what() const noexcept { return s.c_str(); }

private:
    std::string s;
};

class AutoFree {
public:
    PyObject *ptr;

    AutoFree(PyObject *p) { ptr = p; }

    ~AutoFree() { Py_DecRef(ptr); }
};

// error messages are turned into python str by nanobind, which decodes them as
// utf-8, so bytes from the input are rendered as hex escapes instead of being
// copied verbatim
inline std::string hexBytes(std::string_view bytes) {
    if (bytes.empty()) {
        return "";
    }

    return fmt::format("\\x{:02x}", fmt::join(bytes, "\\x"));
}
