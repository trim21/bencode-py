#include <fmt/core.h>
#include <pybind11/pybind11.h>

namespace py = pybind11;

class EncodeError : public py::value_error {
public:
    EncodeError(std::string msg) { s = msg; }

    const char *what() const throw() { return s.c_str(); }

private:
    std::string s;
};

class DecodeError : public py::value_error {
public:
    DecodeError(std::string msg) { s = msg; }

    const char *what() const throw() { return s.c_str(); }

private:
    std::string s;
};

#define decodeErrF(f, ...)                                                                         \
    do {                                                                                           \
        throw DecodeError(fmt::format(f, ##__VA_ARGS__));                                          \
    } while (0)
