#include <Python.h>
#include <algorithm> // std::sort
#include <gch/small_vector.hpp>
#include <pybind11/pybind11.h>

#include "common.hpp"
#include "encode_ctx.hpp"

namespace py = pybind11;

// dataclasses.fields
extern py::object dataclasses_fields;

// dataclasses.is_dataclass
extern py::object is_dataclasses;

static void encodeAny(EncodeContext *ctx, py::handle obj);

bool cmp(std::pair<std::string_view, py::handle> &a, std::pair<std::string_view, py::handle> &b) {
    return a.first < b.first;
}

static std::string_view from_py_string(py::handle obj) {
    if (PyBytes_Check(obj.ptr())) {
        Py_ssize_t size = 0;
        char *s;

        if (PyBytes_AsStringAndSize(obj.ptr(), &s, &size)) {
            throw std::runtime_error("failed to get contents of bytes");
        }

        return std::basic_string_view(s, size);
    }

    if (PyUnicode_Check(obj.ptr())) {
        if (PyUnicode_IS_COMPACT_ASCII(obj.ptr())) {
            const char *s = (char *)PyUnicode_DATA(obj.ptr());
            Py_ssize_t size = ((PyASCIIObject *)(obj.ptr()))->length;
            return std::basic_string_view(s, size);
        }

        Py_ssize_t size = 0;
        const char *s = PyUnicode_AsUTF8AndSize(obj.ptr(), &size);
        return std::basic_string_view(s, size);
    }

    throw py::type_error("dict keys must be str or bytes");
}

static void encodeDict(EncodeContext *ctx, py::handle obj) {
    ctx->writeChar('d');
    auto l = PyDict_Size(obj.ptr());
    gch::small_vector<std::pair<std::string_view, py::handle>, 8> vec;

    vec.reserve(l);

    for (auto item : static_cast<py::dict>(py::object(obj, true))) {
        vec.push_back(std::make_pair(from_py_string(item.first), item.second));
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
static void encodeDictLike(EncodeContext *ctx, py::handle h) {
    ctx->writeChar('d');
    auto l = PyObject_Size(h.ptr());
    if (l == 0) {
        ctx->writeChar('e');
        return;
    }

    auto obj = h.cast<py::object>();

    gch::small_vector<std::pair<std::string_view, py::handle>, 10> vec(l);
    size_t index = 0;
    for (auto keyValue : obj.attr("items")()) {
        auto key = PyTuple_GetItem(keyValue.ptr(), 0);
        auto value = PyTuple_GetItem(keyValue.ptr(), 1);

        vec.at(index) = std::make_pair(from_py_string(py::handle(key)), py::handle(value));
        index++;
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

static void encodeDataclasses(EncodeContext *ctx, py::handle h) {
    ctx->writeChar('d');
    auto fields = dataclasses_fields(h);
    auto size = PyTuple_Size(fields.ptr());

    auto obj = h.cast<py::object>();

    gch::small_vector<std::pair<std::string_view, py::handle>, 10> m(size);

    size_t index = 0;
    for (auto field : fields) {
        auto key = field.attr("name").ptr();
        auto value = obj.attr(key);

        debug_print("set items");
        m.at(index) = std::make_pair(from_py_string(py::handle(key)), py::handle(value));
        index++;
    }

    std::sort(m.begin(), m.end(), cmp);

    for (auto pair : m) {
        ctx->writeSize_t(pair.first.length());
        ctx->writeChar(':');
        ctx->write(pair.first);

        encodeAny(ctx, pair.second);
    }

    ctx->writeChar('e');
    return;
}

static void encodeInt_fast(EncodeContext *ctx, long long val) {
    ctx->writeChar('i');
    ctx->writeLongLong(val);
    ctx->writeChar('e');
}

static void encodeInt_slow(EncodeContext *ctx, py::handle obj);

static void encodeInt(EncodeContext *ctx, py::handle obj) {
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

static void encodeInt_slow(EncodeContext *ctx, py::handle obj) {
    ctx->writeChar('i');

    auto i = PyNumber_Long(obj.ptr());
    auto _ = AutoFree(i);

    auto s = py::str(i);
    auto sv = from_py_string(s);
    ctx->write(sv);

    ctx->writeChar('e');
}

static void encodeList(EncodeContext *ctx, const py::handle obj) {
    ctx->writeChar('l');

    for (auto item : obj) {
        encodeAny(ctx, item);
    }

    ctx->writeChar('e');
}

static void encodeTuple(EncodeContext *ctx, py::handle obj) {
    ctx->writeChar('l');

    for (auto item : obj) {
        encodeAny(ctx, item);
    }

    ctx->writeChar('e');
}

template <typename Encode>
void encodeComposeObject(EncodeContext *ctx, py::handle obj, Encode encode) {
    uintptr_t key = (uintptr_t)obj.ptr();
    debug_print("put object %p to seen", key);
    debug_print("after put object %p to seen", key);
    ctx->stack_depth++;
    bool enableCheck = ctx->stack_depth >= 1000;
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
static void encodeStr(EncodeContext *ctx, const py::handle obj) {
    debug_print("encode str");

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

static void encodeAny(EncodeContext *ctx, const py::handle obj) {
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
        Py_buffer view;
        if (PyObject_GetBuffer(obj.ptr(), &view, 0)) {
            return;
        }

        debug_print("write buffer");
        ctx->writeSize_t(view.len);
        debug_print("write char");
        ctx->writeChar(':');
        debug_print("write content");
        ctx->write((const char *)view.buf, view.len);
        PyBuffer_Release(&view);
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
        return encodeComposeObject(ctx, obj, encodeDictLike);
    }

    if (is_dataclasses(obj).ptr() == Py_True) {
        return encodeComposeObject(ctx, obj, encodeDataclasses);
    }

    // Unsupported type, raise TypeError
    std::string repr = py::repr(obj.get_type());

    std::string msg = "unsupported object " + repr;

    throw py::type_error(msg);
}

static std::vector<EncodeContext *> pool;

// only add lock when building in free thread
#if Py_GIL_DISABLED
static std::mutex m;
#endif

std::unique_ptr<EncodeContext> getContext() {
#if Py_GIL_DISABLED
    std::lock_guard<std::mutex> guard(m);
#endif

    if (pool.empty()) {
        debug_print("empty pool, create Context");
        return std::make_unique<EncodeContext>();
    }

    debug_print("get Context from pool");
    auto ctx = pool.back();
    pool.pop_back();

    return std::unique_ptr<EncodeContext>(ctx);
}

// 30 MiB
size_t const ctx_buffer_reuse_cap = 30 * 1024 * 1024u;

void releaseContext(std::unique_ptr<EncodeContext> ctx) {
    if (pool.size() < 5 && ctx->buffer.capacity() <= ctx_buffer_reuse_cap) {
        debug_print("put Context back to pool");

#if Py_GIL_DISABLED
        std::lock_guard<std::mutex> guard(m);
#endif

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
    std::unique_ptr<EncodeContext> ptr;
    CtxMgr() { ptr = getContext(); }

    ~CtxMgr() { releaseContext(std::move(ptr)); }
};

py::bytes bencode(py::object v) {
    debug_print("1");
    auto ctx = CtxMgr();

    encodeAny(ctx.ptr.get(), v);

    auto res = py::bytes(ctx.ptr->buffer.data(), ctx.ptr->buffer.size());

    return res;
}
