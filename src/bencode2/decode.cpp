#include <cstdlib>
#include <exception>
#include <optional>
#include <string_view>

#include <string>

#include <fmt/core.h>
#include <nanobind/nanobind.h>

#include "common.hpp"
#include "overflow.hpp"

namespace nb = nanobind;

nb::object decodeAny(const char *buf, Py_ssize_t &index, Py_ssize_t size);

#define decoderError(f, ...) throw DecodeError(fmt::format(f, ##__VA_ARGS__))

nb::object decodeInt(const char *buf, Py_ssize_t &index, Py_ssize_t size) {
    Py_ssize_t index_e = 0;
    for (Py_ssize_t i = index + 1; i < size; i++) {
        if (buf[i] == 'e') {
            index_e = i;
            break;
        }
    }

    if (index_e == 0) {
        throw DecodeError(fmt::format("invalid int, missing 'e': %zd", index));
    }

    // malformed 'ie'
    if (index + 1 == index_e) {
        decoderError("invalid int, found 'ie': {}", index_e);
    }

    int64_t sign = 1;

    // i1234e
    // i-1234e
    //  ^ index
    index = index + 1;
    Py_ssize_t num_start = index;

    if (buf[index] == '-') {
        if (buf[index + 1] == '0') {
            decoderError("invalid int, '-0' found at %zd", index);
        }

        num_start = 1 + index;
        sign = -1;
    } else if (buf[index] == '0') {
        if (index + 1 != index_e) {
            decoderError("invalid int, non-zero int should not start with '0'. found at %zd",
                         index);
        }
    }

    for (Py_ssize_t i = num_start; i < index_e; i++) {
        char c = buf[i];
        if (c < '0' || c > '9') {
            decoderError("invalid int, '{:c}' found at {}", c, i);
        }
    }

    // fast path without overflow check for small length string
    if ((index_e - index) < 19) {
        int64_t val = 0;
        for (Py_ssize_t i = num_start; i < index_e; i++) {
            val = val * 10 + (buf[i] - '0');
        }

        index = index_e + 1;
        return nb::cast(sign * val);
    }

    int64_t val = 0;

    for (Py_ssize_t i = num_start; i < index_e; i++) {
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

    debug_print("decode int {} without overflow", val);
    index = index_e + 1;

    return nb::cast(val);

// i1234e
// i-1234e
//  ^ index

// bencode int overflow u64 or i64, build a PyLong object from Str directly.
__OverFlow:;
    std::string s = std::string(buf + index, index_e - index);

    debug_print("decode int {} with overflow", s);

    index = index_e + 1;

    PyObject *i = PyLong_FromString(s.c_str(), NULL, 10);

    if (i == NULL) {
        throw nb::python_error();
    }

    auto o = nb::object(i, nb::detail::steal_t());
    debug_print("{}", s);
    return o;
}

// there is no bytes/Str in bencode, they only have 1 type for both of them.
// TODO: check byte length overflow ssize_t
static std::string_view decodeAsView(const char *buf, Py_ssize_t &index, Py_ssize_t size) {
    Py_ssize_t index_sep = 0;
    for (Py_ssize_t i = index; i < size; i++) {
        if (buf[i] == ':') {
            index_sep = i;
            break;
        }
    }

    if (index_sep == 0) {
        decoderError("invalid string, missing length: index %zd", index);
    }

    if (buf[index] == '0' && index + 1 != index_sep) {
        decoderError("invalid bytes length, found at {}", index);
    }

    Py_ssize_t len = 0;
    for (Py_ssize_t i = index; i < index_sep; i++) {
        if (buf[i] < '0' || buf[i] > '9') {
            decoderError("invalid bytes length, found '%c' at %zd", buf[i], i);
        }
        len = len * 10 + (buf[i] - '0');
    }

    if (index_sep + len >= size) {
        decoderError("bytes length overflow, index {}", index);
    }

    index = index_sep + len + 1;

    return std::string_view(&buf[index_sep + 1], len);
}

// there is no bytes/Str in bencode, they only have 1 type for both of them.
static nb::bytes decodeBytes(const char *buf, Py_ssize_t &index, Py_ssize_t size) {
    auto s = decodeAsView(buf, index, size);
    return nb::bytes(s.data(), s.length());
}

nb::object decodeList(const char *buf, Py_ssize_t &index, Py_ssize_t size) {
    index = index + 1;

    nb::list l = nb::list();

    while (1) {
        if (index >= size) {
            decoderError("buffer overflow when decoding list, index {}", index);
        }

        if (buf[index] == 'e') {
            break;
        }

        nb::object obj = decodeAny(buf, index, size);

        l.append(obj);
    }

    index = index + 1;

    return l;
}

nb::object decodeDict(const char *buf, Py_ssize_t &index, Py_ssize_t size) {
    index = index + 1;
    std::optional<std::string_view> lastKey = std::nullopt;

    auto d = nb::dict();

    while (1) {
        if (index >= size) {
            decoderError("buffer overflow when decoding dict, index {}", index);
        }

        if (buf[index] == 'e') {
            break;
        }

        if (buf[index] < '0' || buf[index] > '9') {
            decoderError("expecting bytes when parsing dict key, found {} instead, index {}",
                         buf[index], index);
        }

        auto key = decodeAsView(buf, index, size);
        auto obj = decodeAny(buf, index, size);

        // skip first key
        if (lastKey.has_value()) {
            if (key < lastKey.value()) {
                decoderError("invalid dict, key not sorted. index {}", index);
            }
            if (key == lastKey.value()) {
                decoderError("invalid dict, find duplicated keys {}. index {}", key, index);
            }
        }
        lastKey = std::make_optional(key);

        d[nb::bytes(key.data(), key.length())] = obj;
    }

    index = index + 1;

    return d;
}

nb::object decodeAny(const char *buf, Py_ssize_t &index, Py_ssize_t size) {
    // int
    if (buf[index] == 'i') {
        return decodeInt(buf, index, size);
    }

    // bytes
    if (buf[index] >= '0' && buf[index] <= '9') {
        return decodeBytes(buf, index, size);
    }

    // list
    if (buf[index] == 'l') {
        return decodeList(buf, index, size);
    }

    // dict
    if (buf[index] == 'd') {
        return decodeDict(buf, index, size);
    }

    decoderError("invalid bencode prefix '{:c}', index {}", buf[index], index);
}

nb::object bdecode(nb::object b) {
    if (!PyObject_CheckBuffer(b.ptr())) {
        throw nb::type_error(
            "bencode.bencode should be called with bytes/memoryview/bytearray/Buffer");
    }

    Py_buffer view;
    PyObject_GetBuffer(b.ptr(), &view, 0);
    if (PyErr_Occurred()) {
        throw nb::python_error();
    }

    Py_ssize_t size = view.len;
    if (size == 0) {
        throw DecodeError("can't decode empty bytes");
    }

    const char *buf = (char *)view.buf;

    Py_ssize_t index = 0;

    nb::object o;
    try {
        o = decodeAny(buf, index, size);
    } catch (std::exception &e) {
        PyBuffer_Release(&view);
        throw e;
    }

    PyBuffer_Release(&view);

    if (index != size) {
        decoderError("invalid bencode data, parse end at index {} but total bytes length {}", index,
                     size);
    }

    return o;
}
