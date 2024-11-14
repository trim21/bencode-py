#pragma once

#include <string_view>

#include <string>

#include <fmt/core.h>
#include <pybind11/pybind11.h>

#include "common.hpp"
#include "overflow.hpp"

namespace py = pybind11;

static py::object decodeAny(const char *buf, Py_ssize_t *index, Py_ssize_t size);

#define decodeErrF(f, ...)                                                                         \
    do {                                                                                           \
        throw DecodeError(fmt::format(f, ##__VA_ARGS__));                                          \
    } while (0)

static py::object decodeInt(const char *buf, Py_ssize_t *index, Py_ssize_t size) {
    Py_ssize_t index_e = 0;
    for (Py_ssize_t i = *index + 1; i < size; i++) {
        if (buf[i] == 'e') {
            index_e = i;
            break;
        }
    }

    if (index_e == 0) {
        throw DecodeError(fmt::format("invalid int, missing 'e': %zd", *index));
    }

    // malformed 'ie'
    if (*index + 1 == index_e) {
        decodeErrF("invalid int, found 'ie': {}", index_e);
    }

    int64_t sign = 1;

    // i1234e
    // i-1234e
    //  ^ index
    *index = *index + 1;
    Py_ssize_t num_start = *index;

    if (buf[*index] == '-') {
        if (buf[*index + 1] == '0') {
            decodeErrF("invalid int, '-0' found at %zd", *index);
        }

        num_start = 1 + *index;
        sign = -1;
    } else if (buf[*index] == '0') {
        if (*index + 1 != index_e) {
            decodeErrF("invalid int, non-zero int should not start with '0'. found at %zd", *index);
        }
    }

    for (Py_ssize_t i = num_start; i < index_e; i++) {
        char c = buf[i] - '0';
        if (c < 0 || c > 9) {
            decodeErrF("invalid int, '{:c}' found at {}", c, i);
        }
    }

    // fast path without overflow check for small length string
    if ((index_e - *index) < 19) {
        int64_t val = 0;
        for (Py_ssize_t i = num_start; i < index_e; i++) {
            val = val * 10 + (buf[i] - '0');
        }

        *index = index_e + 1;
        return py::cast(sign * val);
    }

    int64_t val = 0;

    for (Py_ssize_t i = *index + 1; i < index_e; i++) {
        char c = buf[i] - '0';

        auto of = _i64_mul_overflow(val, 10, &val);
        of = of || _i64_add_overflow(val, c, &val);

        if (of) {
            goto __OverFlow;
        }
    }

    if (_i64_mul_overflow(val, sign, &val)) {
        goto __OverFlow;
    }

    return py::cast(val);

// i1234e
// i-1234e
//  ^ index

// bencode int overflow u64 or i64, build a PyLong object from Str directly.
__OverFlow:;
    std::string s = std::basic_string(buf + *index, index_e - *index);

    *index = index_e + 1;

    PyObject *i = PyLong_FromString(s.c_str(), NULL, 10);

    auto o = py::handle(i).cast<py::object>();
    o.dec_ref();
    debug_print("{}", s);
    return o;
}

// there is no bytes/Str in bencode, they only have 1 type for both of them.
// TODO: check byte length overflow ssize_t
static std::string_view decodeAsView(const char *buf, Py_ssize_t *index, Py_ssize_t size) {
    Py_ssize_t index_sep = 0;
    for (Py_ssize_t i = *index; i < size; i++) {
        if (buf[i] == ':') {
            index_sep = i;
            break;
        }
    }

    if (index_sep == 0) {
        decodeErrF("invalid string, missing length: index %zd", *index);
    }

    if (buf[*index] == '0' && *index + 1 != index_sep) {
        decodeErrF("invalid bytes length, found at {}", *index);
    }

    Py_ssize_t len = 0;
    for (Py_ssize_t i = *index; i < index_sep; i++) {
        if (buf[i] < '0' || buf[i] > '9') {
            decodeErrF("invalid bytes length, found '%c' at %zd", buf[i], i);
        }
        len = len * 10 + (buf[i] - '0');
    }

    if (index_sep + len >= size) {
        decodeErrF("bytes length overflow, index {}", *index);
    }

    *index = index_sep + len + 1;

    return std::string_view(&buf[index_sep + 1], len);
}

// there is no bytes/Str in bencode, they only have 1 type for both of them.
static py::bytes decodeBytes(const char *buf, Py_ssize_t *index, Py_ssize_t size) {
    auto s = decodeAsView(buf, index, size);
    return py::bytes(s.data(), s.length());
}

static py::object decodeList(const char *buf, Py_ssize_t *index, Py_ssize_t size) {
    *index = *index + 1;

    py::list l = py::list(0);

    while (1) {
        if (*index >= size) {
            decodeErrF("buffer overflow when decoding list, index {}", *index);
        }

        if (buf[*index] == 'e') {
            break;
        }

        py::object obj = decodeAny(buf, index, size);

        l.append(obj);
    }

    *index = *index + 1;

    return l;
}

static py::object decodeDict(const char *buf, Py_ssize_t *index, Py_ssize_t size) {
    *index = *index + 1;
    std::optional<std::string_view> lastKey = std::nullopt;

    auto d = py::dict();

    while (1) {
        if (*index >= size) {
            decodeErrF("buffer overflow when decoding dict, index {}", *index);
        }

        if (buf[*index] == 'e') {
            break;
        }

        auto key = decodeAsView(buf, index, size);
        auto obj = decodeAny(buf, index, size);

        // skip first key
        if (lastKey.has_value()) {
            if (key < lastKey.value()) {
                decodeErrF("invalid dict, key not sorted. index {}", *index);
            }
            if (key == lastKey.value()) {
                decodeErrF("invalid dict, find duplicated keys {}. index {}", key, *index);
            }
        }
        lastKey = std::make_optional(key);

        d[py::bytes(key)] = obj;
    }

    *index = *index + 1;

    return d;
}

static py::object decodeAny(const char *buf, Py_ssize_t *index, Py_ssize_t size) {
    // int
    if (buf[*index] == 'i') {
        return decodeInt(buf, index, size);
    }

    // bytes
    if (buf[*index] >= '0' && buf[*index] <= '9') {
        return decodeBytes(buf, index, size);
    }

    // list
    if (buf[*index] == 'l') {
        return decodeList(buf, index, size);
    }

    // dict
    if (buf[*index] == 'd') {
        return decodeDict(buf, index, size);
    }

    decodeErrF("invalid bencode prefix '{:c}', index {}", buf[*index], *index);
}

static py::object bdecode(py::buffer b) {
    py::buffer_info info = b.request();

    Py_ssize_t size = info.size;
    if (size == 0) {
        throw DecodeError("can't decode empty bytes");
    }

    const char *buf = (char *)info.ptr;

    Py_ssize_t index = 0;
    py::object o = decodeAny(buf, &index, size);

    if (index != size) {
        decodeErrF("invalid bencode data, parse end at index {} but total bytes length {}", index,
                   size);
    }

    return o;
}
