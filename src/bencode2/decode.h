#include <nanobind/ndarray.h>
#include <string>

#include <fmt/core.h>
#include <optional>

#include "common.h"
#include "overflow.h"

static nb::object decodeAny(const char *buf, Py_ssize_t *index, Py_ssize_t size);

#define decodeErrF(f, ...)                                                                         \
    do {                                                                                           \
        throw DecodeError(fmt::format(f, ##__VA_ARGS__));                                          \
    } while (0)

static nb::object decodeInt(const char *buf, Py_ssize_t *index, Py_ssize_t size) {
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

    int sign = 1;

    // i1234e
    // i-1234e
    //  ^ index
    *index = *index + 1;

    if (buf[*index] == '-') {
        if (buf[*index + 1] == '0') {
            decodeErrF("invalid int, '-0' found at %zd", *index);
        }

        sign = -1;
    } else if (buf[*index] == '0') {
        if (*index + 1 != index_e) {
            decodeErrF("invalid int, non-zero int should not start with '0'. found at %zd", *index);
        }
    }

    if (sign > 0) {
        unsigned long long val = 0;
        for (Py_ssize_t i = *index; i < index_e; i++) {
            char c = buf[i] - '0';
            if (c < 0 || c > 9) {
                decodeErrF("invalid int, '%c' found at %zd", c, i);
            }

            // val = val * 10 + (buf[i] - '0')
            // but with overflow check

            int of = _u64_mul_overflow(val, 10, &val);
            of = of || _u64_add_overflow(val, c, &val);

            if (of) {
                goto __OverFlow;
            }
        }

        *index = index_e + 1;

        return nb::cast(val);
    } else {
        long long val = 0;
        int of;
        for (Py_ssize_t i = *index + 1; i < index_e; i++) {
            char c = buf[i] - '0';
            if (c < 0 || c > 9) {
                decodeErrF("invalid int, '{:c}' found at {}", c, i);
            }

            of = _i64_mul_overflow(val, 10, &val);
            of = of || _i64_add_overflow(val, c, &val);

            if (of) {
                goto __OverFlow;
            }
        }

        if (_i64_mul_overflow(val, sign, &val)) {
            goto __OverFlow;
        }

        *index = index_e + 1;
        return nb::cast(val);
    }

// i1234e
// i-1234e
//  ^ index

// bencode int overflow u64 or i64, build a PyLong object from Str directly.
__OverFlow:;
    std::string s = std::basic_string(buf + *index, index_e - *index);

    *index = index_e + 1;

    PyObject *i = PyLong_FromString(s.c_str(), NULL, 10);

    auto o = nb::object(nb::handle(i), nb::detail::steal_t());
    return o;
}

// there is no bytes/Str in bencode, they only have 1 type for both of them.
static nb::bytes decodeBytes(const char *buf, Py_ssize_t *index, Py_ssize_t size) {
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

    return nb::bytes(&buf[index_sep + 1], len);
}

static nb::object decodeList(const char *buf, Py_ssize_t *index, Py_ssize_t size) {
    *index = *index + 1;

    nb::list l = nb::list();

    while (1) {
        if (*index >= size) {
            decodeErrF("buffer overflow when decoding list, index {}", *index);
        }

        if (buf[*index] == 'e') {
            break;
        }

        nb::object obj = decodeAny(buf, index, size);

        l.append(obj);

        if (*index >= size) {
            decodeErrF("invalid data, buffer overflow when decoding list. index {}", *index);
        }
    }

    *index = *index + 1;

    return l;
}

static nb::object decodeDict(const char *buf, Py_ssize_t *index, Py_ssize_t size) {
    *index = *index + 1;
    std::optional<nb::bytes> lastKey = std::nullopt;

    auto d = nb::dict();

    while (1) {
        if (*index >= size) {
            decodeErrF("buffer overflow when decoding dict, index {}", *index);
        }

        if (buf[*index] == 'e') {
            break;
        }

        auto key = decodeBytes(buf, index, size);
        auto obj = decodeAny(buf, index, size);

        // skip first key
        if (lastKey.has_value()) {
            if (key < lastKey.value()) {
                decodeErrF("invalid dict, key not sorted. index {}", *index);
            }
            if (key.equal(lastKey.value())) {
                decodeErrF("invalid dict, find duplicated keys {}. index {}", nb::repr(key).c_str(),
                           *index);
            }
        }
        lastKey = std::make_optional(key);

        if (*index >= size) {
            decodeErrF("invalid data, buffer overflow end when decoding dict. index {}", *index);
        }

        d[key] = obj;
    }

    *index = *index + 1;

    return d;
}

static nb::object decodeAny(const char *buf, Py_ssize_t *index, Py_ssize_t size) {
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

nb::object bdecode(nb::object b) {
    char *data;
    Py_ssize_t size;
    if (PyBytes_Check(b.ptr())) {
        size = nb::bytes(b.ptr()).size();
        data = (char *)nb::bytes(b.ptr()).data();
    } else if (PyObject_CheckBuffer(b.ptr())) {
        // TODO: release buffer
        Py_buffer view;
        auto ret = PyObject_GetBuffer(b.ptr(), &view, PyBUF_C_CONTIGUOUS);
        if (ret) {
            return nb::object();
        }
        data = (char *)view.buf;
        size = view.len;
    } else {
        throw nb::type_error("");
    }

    Py_ssize_t index = 0;
    nb::object o = decodeAny(data, &index, size);

    if (index != size) {
        decodeErrF("invalid bencode data, parse end at index {} but total bytes length {}", index,
                   size);
    }

    return o;
}
