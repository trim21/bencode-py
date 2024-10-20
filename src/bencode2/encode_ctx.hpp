#pragma once
#define FMT_HEADER_ONLY

#include <stdint.h>
#include <string>
#include <unordered_set>

#include <fmt/compile.h>
#include <fmt/core.h>

#include "common.hpp"

#define defaultBufferSize 4096

class EncodeContext {
public:
    std::vector<char> buffer;
    size_t stack_depth;
    std::unordered_set<uintptr_t> seen;

    EncodeContext() {
        buffer = std::vector<char>();
        stack_depth = 0;
        buffer.reserve(defaultBufferSize);
    }

    ~EncodeContext() {
        debug_print("delete context");
        seen.clear();
        buffer.clear();
    }

    void reset() {
        stack_depth = 0;
        buffer.clear();
        seen.clear();
    }

    void write(std::string_view val) {
        bufferGrow(val.size());

        buffer.insert(buffer.end(), val.begin(), val.end());
    }

    void write(const char *data, Py_ssize_t size) {
        bufferGrow(size);

        buffer.insert(buffer.end(), data, data + size);
    }

    void writeSize_t(size_t val) {
        bufferGrow(20);
        fmt::format_to(std::back_inserter(buffer), "{}", val);
    }

    void writeLongLong(int64_t val) {
        bufferGrow(20);
        fmt::format_to(std::back_inserter(buffer), "{}", val);
    }

    void writeChar(const char c) {
        bufferGrow(1);
        buffer.push_back(c);
    }

private:
    void bufferGrow(Py_ssize_t size) {
        if (size + buffer.size() + 1 >= buffer.capacity()) {
            buffer.reserve(buffer.capacity() * 2 + size);
        }
    }
};
