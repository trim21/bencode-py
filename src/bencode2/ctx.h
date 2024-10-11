#pragma once
#define FMT_HEADER_ONLY

#include <stdint.h>
#include <string>
#include <unordered_set>

#include <fmt/compile.h>
#include <fmt/core.h>

#include "common.h"

#define defaultBufferSize 4096

class EncodeContext {
public:
    std::string s;
    size_t stack_depth;
    std::unordered_set<uintptr_t> seen;

    EncodeContext() {
        s = std::string();
        stack_depth = 0;
        s.reserve(defaultBufferSize);
    }

    ~EncodeContext() {
        debug_print("delete context");
        seen.clear();
        s.clear();
    }

    void reset() {
        stack_depth = 0;
        s.clear();
        seen.clear();
    }

    void write(std::string ss) { write(ss.data(), ss.size()); }

    void write(const char *data, Py_ssize_t size) {
        bufferGrow(size);

        s.append(data, size);
    }

    void writeSize_t(size_t val) {
        bufferGrow(20);
        fmt::format_to(std::back_inserter(s), FMT_COMPILE("{}"), val);
    }

    void writeLongLong(int64_t val) {
        bufferGrow(20);
        fmt::format_to(std::back_inserter(s), FMT_COMPILE("{}"), val);
    }

    void writeChar(const char c) {
        bufferGrow(1);
        s.push_back(c);
    }

private:
    void bufferGrow(Py_ssize_t size) {
        if (size + s.length() + 1 >= s.capacity()) {
            s.reserve(s.capacity() * 2 + size);
        }
    }
};
