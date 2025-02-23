#include <Python.h>
#include <algorithm> // std::sort
#include <gch/small_vector.hpp>
#include <nanobind/nanobind.h>

#include "common.hpp"
#include "encode_ctx.hpp"

namespace nb = nanobind;

// dataclasses.fields
extern nb::object dataclasses_fields;

// dataclasses.is_dataclass
extern nb::object is_dataclasses;

void encodeAny(EncodeContext *ctx, nb::handle obj);

static bool cmp(std::pair<std::string_view, nb::handle> &a,
                std::pair<std::string_view, nb::handle> &b) {
    return a.first < b.first;
}

static std::string_view py_string_view(nb::handle obj) {
    // fast path for pure ascii string
    if (PyUnicode_IS_COMPACT_ASCII(obj.ptr())) {
        const char *s = (char *)PyUnicode_DATA(obj.ptr());
        Py_ssize_t size = ((PyASCIIObject *)(obj.ptr()))->length;
        return std::string_view(s, size);
    }

    Py_ssize_t size = 0;
    const char *s = PyUnicode_AsUTF8AndSize(obj.ptr(), &size);
    return std::string_view(s, size);
}

static std::string_view dict_key_view(nb::handle obj) {
    if (PyBytes_Check(obj.ptr())) {
        Py_ssize_t size = 0;
        char *s;

        if (PyBytes_AsStringAndSize(obj.ptr(), &s, &size)) {
            throw std::runtime_error("failed to get contents of bytes"); // LCOV_EXCL_LINE
        }

        return std::string_view(s, size);
    }

    if (PyUnicode_Check(obj.ptr())) {
        return py_string_view(obj);
    }

    throw nb::type_error("dict keys must be str or bytes");
}

void encodeDict(EncodeContext *ctx, nb::handle obj) {
    ctx->writeChar('d');
    auto l = PyDict_Size(obj.ptr());
    gch::small_vector<std::pair<std::string_view, nb::handle>, 8> vec;

    vec.reserve(l);

    PyObject *key, *value;
    Py_ssize_t pos = 0;
    while (PyDict_Next(obj.ptr(), &pos, &key, &value)) {
        vec.push_back(std::make_pair(dict_key_view(key), value));
    }

    std::sort(vec.begin(), vec.end(), cmp);

    if (vec.size() != 0) {
        for (size_t i = 0; i < vec.size() - 1; i++) {
            if (vec[i].first == vec[i + 1].first) {
                throw EncodeError(fmt::format("found duplicated keys {}", vec[i].first));
            }
        }
    }

    for (auto pair : vec) {
        ctx->writeSize_t(pair.first.length());
        ctx->writeChar(':');
        ctx->write(pair.first);

        encodeAny(ctx, pair.second);
    }

    ctx->writeChar('e');
    return;
}

// slow path for types.MappingProxyType
void encodeDictLike(EncodeContext *ctx, nb::handle h) {
    ctx->writeChar('d');
    auto l = PyObject_Size(h.ptr());
    if (l == 0) {
        ctx->writeChar('e');
        return;
    }

    gch::small_vector<std::pair<std::string_view, nb::handle>, 8> vec;

    vec.reserve(l);

    for (auto keyValue : h.attr("items")()) {
        auto key = PyTuple_GetItem(keyValue.ptr(), 0);
        auto value = PyTuple_GetItem(keyValue.ptr(), 1);

        vec.push_back(std::make_pair(dict_key_view(nb::handle(key)), nb::handle(value)));
    }

    std::sort(vec.begin(), vec.end(), cmp);
    for (size_t i = 0; i < vec.size() - 1; i++) {
        if (vec[i].first == vec[i + 1].first) {
            throw EncodeError(fmt::format("found duplicated keys {}", vec[i].first));
        }
    }

    for (auto pair : vec) {
        ctx->writeSize_t(pair.first.length());
        ctx->writeChar(':');
        ctx->write(pair.first);

        encodeAny(ctx, pair.second);
    }

    ctx->writeChar('e');
    return;
}

void encodeDataclasses(EncodeContext *ctx, nb::handle h) {
    ctx->writeChar('d');
    auto fields = dataclasses_fields(h);
    auto size = PyTuple_Size(fields.ptr());

    gch::small_vector<std::pair<std::string_view, nb::handle>, 8> vec;

    vec.reserve(size);

    for (auto field : fields) {
        auto key = field.attr("name").ptr();
        auto value = h.attr(key);

        vec.push_back(make_pair(py_string_view(key), nb::handle(value)));
    }

    std::sort(vec.begin(), vec.end(), cmp);

    for (auto pair : vec) {
        ctx->writeSize_t(pair.first.length());
        ctx->writeChar(':');
        ctx->write(pair.first);

        encodeAny(ctx, pair.second);
    }

    ctx->writeChar('e');
    return;
}

void encodeInt_fast(EncodeContext *ctx, long long val) {
    ctx->writeChar('i');
    ctx->writeLongLong(val);
    ctx->writeChar('e');
}

void encodeInt_slow(EncodeContext *ctx, nb::handle obj);

void encodeInt(EncodeContext *ctx, nb::handle obj) {
    int overflow = 0;
    int64_t val = PyLong_AsLongLongAndOverflow(obj.ptr(), &overflow);
    if (overflow) {
        PyErr_Clear();
        // slow path for very long int
        return encodeInt_slow(ctx, obj);
    }
    if (val == -1 && PyErr_Occurred()) { // unexpected error
        return;
    }

    return encodeInt_fast(ctx, val);
}

void encodeInt_slow(EncodeContext *ctx, nb::handle obj) {
    ctx->writeChar('i');

    auto i = PyNumber_Long(obj.ptr());
    auto _ = AutoFree(i);

    auto s = nb::str(i);
    auto sv = py_string_view(s);
    ctx->write(sv);

    ctx->writeChar('e');
}

void encodeList(EncodeContext *ctx, const nb::handle obj) {
    ctx->writeChar('l');

    auto size = PyList_Size(obj.ptr());
    for (auto i = 0; i < size; i++) {
        encodeAny(ctx, nb::handle(PyList_GetItem(obj.ptr(), i)));
    }

    ctx->writeChar('e');
}

void encodeTuple(EncodeContext *ctx, nb::handle obj) {
    ctx->writeChar('l');

    auto size = PyTuple_Size(obj.ptr());
    for (auto i = 0; i < size; i++) {
        encodeAny(ctx, nb::handle(PyTuple_GetItem(obj.ptr(), i)));
    }

    ctx->writeChar('e');
}

template <typename Encode>
void encodeComposeObject(EncodeContext *ctx, nb::handle obj, Encode encode) {
    uintptr_t key = (uintptr_t)obj.ptr();
    debug_print("put object {:x} to seen", key);
    debug_print("after put object {:x} to seen", key);
    ctx->stack_depth++;
    bool enableCheck = ctx->stack_depth >= 100;
    if (enableCheck) {
        if (ctx->seen.find(key) != ctx->seen.end()) {
            debug_print("circular reference found");
            throw EncodeError("circular reference found");
        }
        ctx->seen.insert(key);
    }
    encode(ctx, obj);
    if (enableCheck) {
        ctx->seen.erase(key);
    }
    ctx->stack_depth--;
    return;
}

// for internal detail of python string
// https://github.com/python/cpython/blob/850189a64e7f0b920fe48cb12a5da3e648435680/Include/cpython/unicodeobject.h#L81
void encodeStr(EncodeContext *ctx, const nb::handle obj) {
    debug_print("encode str");

    // fast path for pure ascii string
    if (PyUnicode_IS_COMPACT_ASCII(obj.ptr())) {
        const char *s = (char *)PyUnicode_DATA(obj.ptr());
        Py_ssize_t size = ((PyASCIIObject *)(obj.ptr()))->length;
        debug_print("write length");
        ctx->writeSize_t(size);
        debug_print("write char");
        ctx->writeChar(':');
        debug_print("write content");
        ctx->write(s, size);
        return;
    }

    Py_ssize_t size = 0;
    const char *s = PyUnicode_AsUTF8AndSize(obj.ptr(), &size);

    debug_print("write length");
    ctx->writeSize_t(size);
    debug_print("write char");
    ctx->writeChar(':');
    debug_print("write content");
    ctx->write(s, size);
    return;
}

void encodeAny(EncodeContext *ctx, const nb::handle obj) {
    debug_print("encodeAny");

    if (obj.ptr() == Py_True) {
        debug_print("encode true");
        ctx->write("i1e", 3);
        return;
    }

    if (obj.ptr() == Py_False) {
        debug_print("encode false");
        ctx->write("i0e", 3);
        return;
    }

    if (PyBytes_Check(obj.ptr())) {
        debug_print("encode bytes");
        char *s;
        Py_ssize_t length;
        if (PyBytes_AsStringAndSize(obj.ptr(), &s, &length)) {
            throw nb::python_error();
        }

        debug_print("write buffer");
        ctx->writePySize_t(length);
        debug_print("write char");
        ctx->writeChar(':');
        debug_print("write content");
        ctx->write(s, length);
        return;
    }

    if (PyUnicode_Check(obj.ptr())) {
        encodeStr(ctx, obj);
        return;
    }

    if (PyLong_Check(obj.ptr())) {
        return encodeInt(ctx, obj);
    }

    if (PyList_Check(obj.ptr())) {
        return encodeComposeObject(ctx, obj, encodeList);
    }

    if (PyTuple_Check(obj.ptr())) {
        return encodeComposeObject(ctx, obj, encodeTuple);
    }

    if (PyDict_Check(obj.ptr())) {
        return encodeComposeObject(ctx, obj, encodeDict);
    }

    if (PyByteArray_Check(obj.ptr())) {
        const char *s = PyByteArray_AsString(obj.ptr());
        size_t size = PyByteArray_Size(obj.ptr());

        ctx->writeSize_t(size);
        ctx->writeChar(':');
        ctx->write(s, size);

        return;
    }

    // fast path for memoryview
    if (PyMemoryView_Check(obj.ptr())) {
        Py_buffer *buf = PyMemoryView_GET_BUFFER(obj.ptr());
        ctx->writeSize_t(buf->len);
        ctx->writeChar(':');
        ctx->write((char *)buf->buf, buf->len);

        return;
    }

    if (PyObject_CheckBuffer(obj.ptr())) {
        Py_buffer buf;
        PyObject_GetBuffer(obj.ptr(), &buf, 0);
        if (PyErr_Occurred()) {
            throw nb::python_error();
        }

        ctx->writeSize_t(buf.len);
        ctx->writeChar(':');
        ctx->write((char *)buf.buf, buf.len);

        PyBuffer_Release(&buf);
        return;
    }

    // types.MappingProxyType
    debug_print("test if mapping proxy");
    if (obj.ptr()->ob_type == &PyDictProxy_Type) {
        debug_print("encode mapping proxy");
        return encodeComposeObject(ctx, obj, encodeDictLike);
    }

    if (is_dataclasses(obj).ptr() == Py_True) {
        return encodeComposeObject(ctx, obj, encodeDataclasses);
    }

    // Unsupported type, raise TypeError
    auto repr = nb::repr(obj.type());

    std::string msg = "unsupported object ";
    msg.append(repr.c_str());

    throw nb::type_error(msg.c_str());
}

thread_local static std::vector<EncodeContext *> pool;

// 30 MiB. Most torrents is smaller than 20 mib,
// we may alloc more size so set it bigger
size_t const ctx_buffer_reuse_cap = 20 * 1024 * 1024u;

// reuse encoded buffer for average 10% performance gain.
class CtxMgr {
public:
    EncodeContext *ctx;
    CtxMgr() {
        if (pool.empty()) {
            debug_print("empty pool, create Context");
            ctx = new EncodeContext();
            return;
        }

        debug_print("get Context from pool");

        // will there be any race problem here?
        ctx = pool.back();
        pool.pop_back();

        return;
    }

    ~CtxMgr() {
        if (pool.size() <= 2) {
            if (ctx->buffer.capacity() <= ctx_buffer_reuse_cap) {
                debug_print("put Context back to pool");

                ctx->reset();
                pool.push_back(ctx);
                return;
            }
        }

        debug_print("delete Context");
        delete ctx;
    }
};

nb::bytes bencode(nb::object v) {
    debug_print("1");
    auto ctx = CtxMgr();

    encodeAny(ctx.ctx, v);

    auto res = nb::bytes(ctx.ctx->buffer.data(), ctx.ctx->buffer.size());

    return res;
}
