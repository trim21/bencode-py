#pragma once

#include <Python.h>
#include <pybind11/pybind11.h>
namespace py = pybind11;

#define HPy_ssize_t Py_ssize_t
#define HPy PyObject *

#ifdef _MSC_VER
#pragma warning(disable : 4996)
#endif

#ifdef BENCODE_CPP_DEBUG

#ifdef _MSC_VER
#define debug_print(fmt, ...)                                                  \
                                                                               \
  do {                                                                         \
    printf(__FILE__);                                                          \
    printf(":");                                                               \
    printf("%d", __LINE__);                                                    \
    printf("\t%s", __FUNCTION__);                                              \
    printf("\tDEBUG: ");                                                       \
    printf(fmt, __VA_ARGS__);                                                  \
    printf("\n");                                                              \
  } while (0)

#else

#define debug_print(fmt, ...)                                                  \
  do {                                                                         \
    printf(__FILE__);                                                          \
    printf(":");                                                               \
    printf("%d", __LINE__);                                                    \
    printf("\t%s\tDEBUG: ", __PRETTY_FUNCTION__);                              \
    printf(fmt, ##__VA_ARGS__);                                                \
    printf("\n");                                                              \
  } while (0)

#endif
#else

#define debug_print(fmt, ...)                                                  \
  do {                                                                         \
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
