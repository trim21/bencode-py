#include <Python.h>
#include <algorithm> // std::sort
#include <iostream>
#include <pybind11/pybind11.h>

#include "common.h"
#include "ctx.h"

namespace py = pybind11;

// dataclasses.fields
extern py::object dataclasses_fields;
// dataclasses.is_dataclass
extern py::object is_dataclasses;

static void encodeAny(Context *ctx, py::handle obj);

bool cmp(std::pair<std::string, py::handle> &a, std::pair<std::string, py::handle> &b) {
    return a.first < b.first;
}

static void encodeDict(Context *ctx, py::handle obj) {
    debug_print("encodeDict");
    ctx->writeChar('d');
    auto l = PyDict_Size(obj.ptr());
    if (l == 0) {
        ctx->writeChar('e');
        return;
    }

    std::vector<std::pair<std::string, py::handle>> m(l);
    auto items = PyDict_Items(obj.ptr());

    // smart pointer to dec_ref when function return
    auto ref = AutoFree(items);

    for (int i = 0; i < l; ++i) {
        auto keyValue = PyList_GetItem(items, i);
        auto key = PyTuple_GetItem(keyValue, 0);
        auto value = PyTuple_GetItem(keyValue, 1);

        if (!(PyUnicode_Check(key) || PyBytes_Check(key))) {
            throw py::type_error("dict keys must be str or bytes");
        }

        debug_print("set items");
        m.at(i) = std::make_pair(py::handle(key).cast<std::string>(), py::handle(value));
    }

    std::sort(m.begin(), m.end(), cmp);
    auto lastKey = m[0].first;
    debug_print("key '%s'\n", lastKey.data());
    for (auto i = 1; i < l; i++) {
        auto currentKey = m[i].first;
        debug_print("key '%s'\n", currentKey.data());
        if (currentKey == lastKey) {
            throw EncodeError(fmt::format("found duplicated keys {}", lastKey));
        }

        lastKey = currentKey;
    }

    for (auto pair : m) {
        ctx->writeSize_t(pair.first.length());
        ctx->writeChar(':');
        ctx->write(pair.first.data(), pair.first.length());

        encodeAny(ctx, pair.second);
    }

    ctx->writeChar('e');
    return;
}

// slow path for types.MappingProxyType
static void encodeDictLike(Context *ctx, py::handle h) {
    debug_print("encodeDictLike");
    ctx->writeChar('d');
    debug_print("get object size");
    auto l = PyObject_Size(h.ptr());
    if (l == 0) {
        ctx->writeChar('e');
        return;
    }

    auto obj = h.cast<py::object>();

    std::vector<std::pair<std::string, py::handle>> m(l);
    debug_print("get items");
    auto items = obj.attr("items")();

    size_t index = 0;
    for (auto keyValue : items) {
        auto key = PyTuple_GetItem(keyValue.ptr(), 0);
        auto value = PyTuple_GetItem(keyValue.ptr(), 1);

        if (!(PyUnicode_Check(key) || PyBytes_Check(key))) {
            throw EncodeError("dict keys must be str or bytes");
        }

        debug_print("set items");
        m.at(index) = std::make_pair(py::handle(key).cast<std::string>(), py::handle(value));
        index++;
    }

    std::sort(m.begin(), m.end(), cmp);
    auto lastKey = m[0].first;
    debug_print("key '%s'\n", lastKey.data());
    for (auto i = 1; i < l; i++) {
        auto currentKey = m[i].first;
        debug_print("key '%s'\n", currentKey.data());
        if (currentKey == lastKey) {
            throw EncodeError(fmt::format("found duplicated keys {}", lastKey));
        }

        lastKey = currentKey;
    }

    for (auto pair : m) {
        ctx->writeSize_t(pair.first.length());
        ctx->writeChar(':');
        ctx->write(pair.first.data(), pair.first.length());

        encodeAny(ctx, pair.second);
    }

    ctx->writeChar('e');
    return;
}

static void encodeDataclasses(Context *ctx, py::handle h) {
    debug_print("encodeDataclasses");

    ctx->writeChar('d');
    debug_print("get object size");
    auto fields = dataclasses_fields(h);
    auto size = PyTuple_Size(fields.ptr());
    if (size == 0) {
        ctx->writeChar('e');
        return;
    }

    auto obj = h.cast<py::object>();

    std::vector<std::pair<std::string, py::handle>> m(size);

    size_t index = 0;
    for (auto field : fields) {
        auto key = field.attr("name").ptr();
        auto value = obj.attr(key);

        debug_print("set items");
        m.at(index) = std::make_pair(py::handle(key).cast<std::string>(), py::handle(value));
        index++;
    }

    std::sort(m.begin(), m.end(), cmp);

    for (auto pair : m) {
        ctx->writeSize_t(pair.first.length());
        ctx->writeChar(':');
        ctx->write(pair.first.data(), pair.first.length());

        encodeAny(ctx, pair.second);
    }

    ctx->writeChar('e');
    return;
}

static void encodeInt_fast(Context *ctx, long long val) {
    ctx->writeChar('i');
    ctx->writeLongLong(val);
    ctx->writeChar('e');
}

static void encodeInt_slow(Context *ctx, py::handle obj);

static void encodeInt(Context *ctx, py::handle obj) {
    int overflow = 0;
    long long val = PyLong_AsLongLongAndOverflow(obj.ptr(), &overflow);
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

static void encodeInt_slow(Context *ctx, py::handle obj) {
    PyObject *fmt = PyUnicode_FromString("%d");
    if (fmt == NULL) {
        return;
    }

    auto _0 = AutoFree(fmt);

    PyObject *s = PyUnicode_Format(fmt, obj.ptr()); // s = '%d" % i
    if (s == NULL) {
        return;
    }
    auto _1 = AutoFree(s);

    PyObject *b = PyUnicode_AsUTF8String(s);
    if (b == NULL) {
        return;
    }
    auto _2 = AutoFree(b);

    Py_ssize_t size;
    char *data;
    if (PyBytes_AsStringAndSize(b, &data, &size)) {
        return;
    }

    ctx->writeChar('i');
    ctx->write(data, size);
    ctx->writeChar('e');
}

//
static void encodeList(Context *ctx, const py::handle obj) {
    ctx->writeChar('l');

    Py_ssize_t len = PyList_Size(obj.ptr());
    for (Py_ssize_t i = 0; i < len; i++) {
        PyObject *o = PyList_GetItem(obj.ptr(), i);
        encodeAny(ctx, o);
    }

    ctx->writeChar('e');
}

static void encodeTuple(Context *ctx, py::handle obj) {
    ctx->writeChar('l');

    Py_ssize_t len = PyTuple_Size(obj.ptr());
    for (Py_ssize_t i = 0; i < len; i++) {
        PyObject *o = PyTuple_GetItem(obj.ptr(), i);
        encodeAny(ctx, o);
    }

    ctx->writeChar('e');
}

#define encodeComposeObject(ctx, obj, encoder)                                                     \
    do {                                                                                           \
        uintptr_t key = (uintptr_t)obj.ptr();                                                      \
        debug_print("put object %p to seen", key);                                                 \
        debug_print("after put object %p to seen", key);                                           \
        if (ctx->seen.find(key) != ctx->seen.end()) {                                              \
            debug_print("circular reference found");                                               \
            throw EncodeError("circular reference found");                                         \
        }                                                                                          \
        ctx->seen.insert(key);                                                                     \
        encoder(ctx, obj);                                                                         \
        ctx->seen.erase(key);                                                                      \
        return;                                                                                    \
    } while (0)

static void encodeAny(Context *ctx, const py::handle obj) {
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
        Py_ssize_t size = 0;
        char *s;

        if (PyBytes_AsStringAndSize(obj.ptr(), &s, &size)) {
            throw std::runtime_error("failed to get contents of bytes");
        }

        debug_print("write buffer");
        ctx->writeSize_t(size);
        debug_print("write char");
        ctx->writeChar(':');
        debug_print("write content");
        ctx->write((const char *)s, size);
        return;
    }

    if (PyUnicode_Check(obj.ptr())) {
        debug_print("encode str");
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

    if (PyLong_Check(obj.ptr())) {
        return encodeInt(ctx, obj);
    }

    if (PyList_Check(obj.ptr())) {
        encodeComposeObject(ctx, obj, encodeList);
    }

    if (PyTuple_Check(obj.ptr())) {
        encodeComposeObject(ctx, obj, encodeTuple);
    }

    if (PyDict_Check(obj.ptr())) {
        encodeComposeObject(ctx, obj, encodeDict);
    }

    if (PyByteArray_Check(obj.ptr())) {
        const char *s = PyByteArray_AsString(obj.ptr());
        size_t size = PyByteArray_Size(obj.ptr());

        ctx->writeSize_t(size);
        ctx->writeChar(':');
        ctx->write(s, size);

        return;
    }

    if (PyMemoryView_Check(obj.ptr())) {
        Py_buffer *buf = PyMemoryView_GET_BUFFER(obj.ptr());
        ctx->writeSize_t(buf->len);
        ctx->writeChar(':');
        ctx->write((char *)buf->buf, buf->len);

        return;
    }

    // types.MappingProxyType
    debug_print("test if mapping proxy");
    if (obj.ptr()->ob_type == &PyDictProxy_Type) {
        debug_print("encode mapping proxy");
        encodeComposeObject(ctx, obj, encodeDictLike);
    }

    if (is_dataclasses(obj).ptr() == Py_True) {
        encodeComposeObject(ctx, obj, encodeDataclasses);
    }

    // Unsupported type, raise TypeError
    std::string repr = py::repr(obj.get_type());

    std::string msg = "unsupported object " + repr;

    throw py::type_error(msg);
}

static std::vector<Context *> pool;

std::unique_ptr<Context> getContext() {
    if (pool.empty()) {
        debug_print("empty pool, create Context");
        return std::make_unique<Context>();
    }

    debug_print("get Context from pool");
    auto ctx = pool.back();
    pool.pop_back();

    return std::unique_ptr<Context>(ctx);
}

// 30 MiB
size_t const ctx_buffer_reuse_cap = 30 * 1024 * 1024u;

void releaseContext(std::unique_ptr<Context> ctx) {
    if (pool.size() < 5 && ctx->s.capacity() <= ctx_buffer_reuse_cap) {
        debug_print("put Context back to pool");
        ctx.get()->reset();
        pool.push_back(ctx.get());
        ctx.release();
        return;
    }

    debug_print("delete Context");
    ctx.reset();
}

class CtxMgr {
public:
    std::unique_ptr<Context> ptr;
    CtxMgr() { ptr = getContext(); }

    ~CtxMgr() { releaseContext(std::move(ptr)); }
};

py::bytes bencode(py::object v) {
    debug_print("1");
    auto ctx = CtxMgr();

    encodeAny(ctx.ptr.get(), v);

    auto res = py::bytes(ctx.ptr->s);

    return res;
}
